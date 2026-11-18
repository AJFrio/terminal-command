use axum::{
    Json, Router,
    extract::State,
    http::{HeaderMap, StatusCode, header},
    response::{Html, IntoResponse},
    routing::{get, post},
};
use rtc::ice::mdns::MulticastDnsMode;
use serde::{Deserialize, Serialize};
use std::{
    collections::VecDeque,
    error::Error,
    net::SocketAddr,
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};
use tc_session::{CommandBatch, Timing};
use tokio::{
    net::TcpListener,
    sync::{Notify, oneshot},
    time::timeout,
};
use webrtc::{
    data_channel::{DataChannel, DataChannelEvent},
    peer_connection::{
        PeerConnection, PeerConnectionBuilder, PeerConnectionEventHandler, RTCConfigurationBuilder,
        RTCIceGatheringState, RTCIceServer, RTCIceTransportPolicy, RTCSessionDescription,
        SettingEngine,
    },
};

const BATCHES: u32 = 128;
const IN_FLIGHT: u32 = 8;
const CHANNEL: &str = "terminal-command-bench-v1";
const WIRE_DONE: &str = "batches-verified";
type TestError = Box<dyn Error + Send + Sync>;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct IceServer {
    urls: Vec<String>,
    username: String,
    credential: String,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct BrowserConfig {
    ice_servers: Vec<IceServer>,
    ice_transport_policy: &'static str,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct BrowserStats {
    local_candidate: String,
    remote_candidate: String,
    protocol: String,
    connection_ms: f64,
    ice_rtt_ms: Option<f64>,
    inbound_bytes: usize,
    outbound_bytes: usize,
    batches: u32,
    browser: String,
}

#[derive(Serialize)]
struct NativeStats {
    batches: u32,
    sent_bytes: usize,
    received_bytes: usize,
    command_round_trip: Timing,
}

struct Signal {
    authorization: String,
    config: BrowserConfig,
    peer: tokio::sync::Mutex<Option<Box<dyn PeerConnection>>>,
    exchange: Arc<Exchange>,
    completion: Mutex<Option<oneshot::Sender<(NativeStats, BrowserStats)>>>,
}

#[derive(Default)]
struct Exchange {
    gathered: Notify,
    result: Arc<Mutex<Option<Result<NativeStats, String>>>>,
}

#[async_trait::async_trait]
impl PeerConnectionEventHandler for Exchange {
    async fn on_ice_gathering_state_change(&self, state: RTCIceGatheringState) {
        if state == RTCIceGatheringState::Complete {
            self.gathered.notify_one();
        }
    }

    async fn on_data_channel(&self, channel: Arc<dyn DataChannel>) {
        let result_slot = self.result.clone();
        tokio::spawn(async move {
            let result = timeout(Duration::from_secs(24), round_trips(&*channel))
                .await
                .map_err(|_| "data channel timed out".to_owned())
                .and_then(|result| result.map_err(|error| error.to_string()));
            if let Err(error) = &result {
                eprintln!("Data channel error: {error}");
            }
            // Store the result before acknowledging it so the browser can confirm it via HTTP.
            let clean = result.is_ok();
            *result_slot.lock().unwrap() = Some(result);
            let ack = if clean {
                WIRE_DONE
            } else {
                "batch-verification-failed"
            };
            let _ = channel.send_text(ack).await;
        });
    }
}

async fn round_trips(channel: &dyn DataChannel) -> Result<NativeStats, TestError> {
    if channel.label().await? != CHANNEL {
        return Err("unexpected data channel label".into());
    }
    loop {
        match channel.poll().await {
            Some(DataChannelEvent::OnOpen) => break,
            Some(DataChannelEvent::OnClose) | None => {
                return Err("channel closed before opening".into());
            }
            _ => {}
        }
    }

    let mut sent_bytes = 0;
    let mut received_bytes = 0;
    let mut rtt = Vec::with_capacity(BATCHES as usize);
    let mut pending = VecDeque::with_capacity(IN_FLIGHT as usize);
    for index in 0..IN_FLIGHT {
        sent_bytes += send_batch(channel, index, &mut pending).await?;
    }
    for index in 0..BATCHES {
        loop {
            match channel.poll().await {
                Some(DataChannelEvent::OnMessage(inbound)) => {
                    let browser_batch = serde_json::from_slice::<CommandBatch>(&inbound.data)?;
                    if browser_batch != batch(1, index) {
                        return Err(format!("invalid browser batch at index {index}").into());
                    }
                    received_bytes += inbound.data.len();
                    break;
                }
                Some(DataChannelEvent::OnClose) | None => {
                    return Err(format!("channel closed at batch {index}").into());
                }
                _ => {}
            }
        }
        let start = pending.pop_front().expect("sent batch");
        rtt.push(start.elapsed().as_secs_f64() * 1000.0);
        if index + IN_FLIGHT < BATCHES {
            sent_bytes += send_batch(channel, index + IN_FLIGHT, &mut pending).await?;
        }
    }
    Ok(NativeStats {
        batches: BATCHES,
        sent_bytes,
        received_bytes,
        command_round_trip: Timing::from_samples(&mut rtt),
    })
}

async fn send_batch(
    channel: &dyn DataChannel,
    index: u32,
    pending: &mut VecDeque<Instant>,
) -> Result<usize, TestError> {
    let outbound = serde_json::to_string(&batch(0, index))?;
    pending.push_back(Instant::now());
    channel.send_text(&outbound).await?;
    Ok(outbound.len())
}

fn batch(player: u8, index: u32) -> CommandBatch {
    CommandBatch {
        version: CommandBatch::VERSION,
        tick: 1 + index * 4,
        player,
        advance: index % 3 != u32::from(player),
        lane_mm: (index as i32 * 127 + i32::from(player) * 759) % 12_001 - 6_000,
    }
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), TestError> {
    let mut args = std::env::args().skip(1);
    let bind = args.next().unwrap_or_else(|| "127.0.0.1:8091".into());
    if matches!(bind.as_str(), "--help" | "-h") {
        println!(
            "tc-rtc [listen socket]\nOptional ICE server via TC_ICE_URL. For TURN set TC_TURN_USER and TC_TURN_CREDENTIAL."
        );
        return Ok(());
    }
    let bind: SocketAddr = bind.parse()?;
    let seconds = args
        .next()
        .map(|value| value.parse())
        .transpose()?
        .unwrap_or(120);
    if args.next().is_some() || !(30..=900).contains(&seconds) {
        return Err("usage: tc-rtc [listen socket] [timeout seconds 30..900]".into());
    }

    let config = browser_config()?;
    let mut nonce = [0; 24];
    getrandom::fill(&mut nonce).map_err(|error| error.to_string())?;
    let token = nonce
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    let (sender, receiver) = oneshot::channel();
    let signal = Arc::new(Signal {
        authorization: format!("Bearer {token}"),
        config,
        peer: tokio::sync::Mutex::new(None),
        exchange: Arc::new(Exchange::default()),
        completion: Mutex::new(Some(sender)),
    });
    let router = Router::new()
        .route("/", get(|| async { Html(include_str!("rtc.html")) }))
        .route(
            "/rtc.js",
            get(|| async {
                (
                    [(header::CONTENT_TYPE, "text/javascript")],
                    include_str!("rtc.js"),
                )
            }),
        )
        .route("/api/config", get(config_for_browser))
        .route("/api/offer", post(answer))
        .route("/api/confirm", post(confirm))
        .with_state(signal.clone());

    let listener = TcpListener::bind(bind).await?;
    eprintln!(
        "Open http://{}/#{token} in the benchmark browser.",
        listener.local_addr()?
    );

    let report = Arc::new(Mutex::new(None));
    let result = report.clone();
    axum::serve(listener, router)
        .with_graceful_shutdown(async move {
            let received = timeout(Duration::from_secs(seconds), receiver)
                .await
                .ok()
                .and_then(Result::ok);
            *result.lock().unwrap() = received;
        })
        .await?;
    if let Some(peer) = signal.peer.lock().await.take() {
        peer.close().await?;
    }
    let (native, browser) = report
        .lock()
        .unwrap()
        .take()
        .ok_or("WebRTC benchmark timed out awaiting a verified exchange")?;
    println!(
        "{}",
        serde_json::json!({
            "mode": if signal.config.ice_transport_policy == "relay" { "turn" } else { "direct" },
            "native_transport": "webrtc-rs 0.20.0",
        "max_in_flight": IN_FLIGHT,
            "native": native,
            "browser": browser,
        })
    );
    Ok(())
}

fn browser_config() -> Result<BrowserConfig, TestError> {
    let url = std::env::var("TC_ICE_URL").unwrap_or_default();
    let (ice_servers, relay) = if url.is_empty() {
        (Vec::new(), false)
    } else {
        let relay = url.starts_with("turn:") || url.starts_with("turns:");
        if !relay && !url.starts_with("stun:") {
            return Err("TC_ICE_URL must be a stun:, turn: or turns: URL".into());
        }
        let (username, credential) = if relay {
            (
                std::env::var("TC_TURN_USER")?,
                std::env::var("TC_TURN_CREDENTIAL")?,
            )
        } else {
            (String::new(), String::new())
        };
        (
            vec![IceServer {
                urls: vec![url],
                username,
                credential,
            }],
            relay,
        )
    };
    Ok(BrowserConfig {
        ice_servers,
        ice_transport_policy: if relay { "relay" } else { "all" },
    })
}

fn authorized(signal: &Signal, headers: &HeaderMap) -> Result<(), StatusCode> {
    if headers
        .get(header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        == Some(&signal.authorization)
    {
        Ok(())
    } else {
        Err(StatusCode::UNAUTHORIZED)
    }
}

async fn config_for_browser(
    State(signal): State<Arc<Signal>>,
    headers: HeaderMap,
) -> Result<impl IntoResponse, StatusCode> {
    authorized(&signal, &headers)?;
    Ok((
        [(header::CACHE_CONTROL, "no-store")],
        Json(signal.config.clone()),
    ))
}

async fn answer(
    State(signal): State<Arc<Signal>>,
    headers: HeaderMap,
    Json(offer): Json<RTCSessionDescription>,
) -> Result<Json<RTCSessionDescription>, (StatusCode, String)> {
    authorized(&signal, &headers).map_err(|status| (status, String::new()))?;
    let mut slot = signal.peer.lock().await;
    if slot.is_some() {
        return Err((
            StatusCode::CONFLICT,
            "the single benchmark peer is already connected".into(),
        ));
    }

    let config = RTCConfigurationBuilder::new()
        .with_ice_servers(
            signal
                .config
                .ice_servers
                .iter()
                .map(|ice| RTCIceServer {
                    urls: ice.urls.clone(),
                    username: ice.username.clone(),
                    credential: ice.credential.clone(),
                })
                .collect(),
        )
        .with_ice_transport_policy(if signal.config.ice_transport_policy == "relay" {
            RTCIceTransportPolicy::Relay
        } else {
            RTCIceTransportPolicy::All
        })
        .build();

    // Chrome can advertise LAN host candidates as temporary mDNS names.
    let mut settings = SettingEngine::default();
    settings.set_multicast_dns_mode(MulticastDnsMode::QueryOnly);
    let peer = PeerConnectionBuilder::new()
        .with_configuration(config)
        .with_setting_engine(settings)
        .with_handler(signal.exchange.clone())
        .with_udp_addrs(vec!["0.0.0.0:0".to_owned()])
        .build()
        .await
        .map_err(|error| internal(&error))?;

    let result: Result<_, TestError> = async {
        peer.set_remote_description(offer).await?;
        let answer = peer.create_answer(None).await?;
        peer.set_local_description(answer).await?;
        timeout(Duration::from_secs(15), signal.exchange.gathered.notified()).await?;
        peer.local_description()
            .await
            .ok_or_else(|| "missing local SDP answer".into())
    }
    .await;

    match result {
        Ok(description) => {
            *slot = Some(Box::new(peer));
            Ok(Json(description))
        }
        Err(error) => {
            let _ = peer.close().await;
            Err(internal(&*error))
        }
    }
}

fn internal(error: &dyn std::fmt::Display) -> (StatusCode, String) {
    eprintln!("Signaling error: {error}");
    (
        StatusCode::INTERNAL_SERVER_ERROR,
        "native signaling failed; see the native log".into(),
    )
}

async fn confirm(
    State(signal): State<Arc<Signal>>,
    headers: HeaderMap,
    Json(browser): Json<BrowserStats>,
) -> Result<StatusCode, (StatusCode, &'static str)> {
    authorized(&signal, &headers).map_err(|status| (status, ""))?;
    let path_matches = if signal.config.ice_transport_policy == "relay" {
        browser.local_candidate == "relay" && browser.remote_candidate == "relay"
    } else {
        let direct = |candidate: &str| matches!(candidate, "host" | "srflx" | "prflx");
        direct(&browser.local_candidate) && direct(&browser.remote_candidate)
    };
    let mut result = signal.exchange.result.lock().unwrap();
    let Some(Ok(native)) = result.as_ref() else {
        return Err((StatusCode::CONFLICT, "native did not verify the batches"));
    };
    if !path_matches
        || browser.batches != native.batches
        || browser.outbound_bytes != native.received_bytes
        || browser.inbound_bytes != native.sent_bytes
    {
        return Err((
            StatusCode::UNPROCESSABLE_ENTITY,
            "ICE path or byte counts did not match the benchmark",
        ));
    }
    let Some(sender) = signal.completion.lock().unwrap().take() else {
        return Err((StatusCode::CONFLICT, "benchmark already completed"));
    };
    let native = result.take().unwrap().unwrap();
    let _ = sender.send((native, browser));
    Ok(StatusCode::NO_CONTENT)
}
