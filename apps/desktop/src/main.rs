use std::{
    error::Error,
    path::PathBuf,
    thread,
    time::{Duration, Instant},
};
use tc_client::{Bridge, Options};
use tc_session::{Replay, SimulationReport, TICK_MS, Timing};

fn main() -> Result<(), Box<dyn Error>> {
    let mut options = Options::default();
    let mut assets = PathBuf::from("models");
    let mut verify_rig = false;
    let mut args = std::env::args().skip(1);
    while let Some(flag) = args.next() {
        let mut value = || {
            args.next()
                .ok_or_else(|| format!("missing value for {flag}"))
        };
        match flag.as_str() {
            "--units" => options.units = value()?.parse()?,
            "--rigs" => options.rigs = value()?.parse()?,
            "--seed" => options.seed = value()?.parse()?,
            "--ticks" => options.ticks = value()?.parse()?,
            "--warmup" => options.warmup = value()?.parse()?,
            "--width" => options.width = value()?.parse()?,
            "--height" => options.height = value()?.parse()?,
            "--assets" => assets = PathBuf::from(value()?),
            "--fullscreen" => options.fullscreen = true,
            "--inspect" => options.inspect = true,
            "--verify-rig" => {
                options.inspect = true;
                verify_rig = true;
            }
            "--help" | "-h" => {
                println!(
                    "Terminal Command benchmark\n\
                     --units 500|4000   --rigs <even count>   --seed <u32>\n\
                     --ticks <count>    --warmup <ticks>      --fullscreen\n\
                     --width <px>       --height <px>         --assets <directory>\n\
                     --inspect          --verify-rig"
                );
                return Ok(());
            }
            _ => return Err(format!("unknown argument {flag}").into()),
        }
    }
    options.validate()?;

    let bridge = Bridge::new(options.units);
    let timed = options.ticks > 0 && !options.inspect;
    if !options.inspect {
        let worker_options = options.clone();
        let worker_bridge = bridge.clone();
        thread::Builder::new()
            .name("terminal-command-sim".to_owned())
            .spawn(move || simulate(worker_options, worker_bridge))?;
    }
    tc_client::run(
        options,
        bridge.clone(),
        std::path::absolute(assets)?.to_string_lossy().into_owned(),
        timed || verify_rig,
    );

    if let Some(error) = bridge.status().error {
        return Err(error.into());
    }
    if timed || verify_rig {
        let mut report: serde_json::Value = serde_json::from_str(
            &bridge
                .report()
                .ok_or("benchmark exited before completion")?,
        )?;
        report["native_peak_rss_bytes"] = serde_json::json!(peak_rss_bytes());
        println!("{report}");
    }
    Ok(())
}

fn simulate(options: Options, bridge: Bridge) {
    while !bridge.status().ready {
        if bridge.status().error.is_some() {
            return;
        }
        thread::sleep(Duration::from_millis(10));
    }
    let mut replay = Replay::new(options.units, options.seed).expect("validated workload");
    let mut steps = Vec::new();
    let mut snapshots = Vec::new();
    let mut skipped = 0;
    let mut missed = 0;
    let interval = Duration::from_millis(u64::from(TICK_MS));
    let mut deadline = Instant::now();
    loop {
        thread::sleep(deadline.saturating_duration_since(Instant::now()));
        deadline += interval;
        let start = Instant::now();
        replay.step();
        let step_ms = start.elapsed().as_secs_f64() * 1000.0;
        let tick = replay.tick();
        let final_tick = tick == options.ticks;
        if options.ticks > 0 {
            replay.record(final_tick);
        }
        let mut snapshot_ms = 0.0;
        let sent = bridge.publish(tick, |bytes| {
            let start = Instant::now();
            replay.write_view(bytes);
            snapshot_ms = start.elapsed().as_secs_f64() * 1000.0;
        });
        if options.ticks > 0 && tick > options.warmup {
            steps.push(step_ms);
            if sent {
                snapshots.push(snapshot_ms);
            } else {
                skipped += 1;
            }
            missed += u32::from(Instant::now() > deadline);
        }
        if final_tick {
            bridge.finish(SimulationReport {
                snapshot_bytes: replay.view_len(),
                trace: replay.finish(),
                missed_deadlines: missed,
                skipped_transfers: skipped,
                step: Timing::from_samples(&mut steps),
                snapshot: Timing::from_samples(&mut snapshots),
                worker_copy: None,
                worker_memory_bytes: None,
            });
            break;
        }
    }
}

fn peak_rss_bytes() -> Option<u64> {
    let status = std::fs::read_to_string("/proc/self/status").ok()?;
    status
        .lines()
        .find_map(|line| line.strip_prefix("VmHWM:"))?
        .split_whitespace()
        .next()?
        .parse::<u64>()
        .ok()
        .map(|kb| kb * 1024)
}
