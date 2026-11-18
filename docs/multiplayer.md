# Multiplayer

## Private peer-hosted matches

Start with invite-only 1v1 and a player-hosted coordinator. The coordinator orders commands and sends each committed batch to the other players. Every player, including the coordinator, runs the same simulation. Start with two peers, then extend the same star topology to a four-player room. A four-player room has three WebRTC links to the host. The host's upload and connection quality matter as the room grows.

Use a reliable, ordered WebRTC data channel for committed turns. On the browser use `RTCPeerConnection`. Evaluate a native WebRTC implementation behind the same transport interface and choose it by testing browser interoperability, direct and relayed connections, and desktop packaging. [W3C WebRTC specification](https://www.w3.org/TR/webrtc/) · [WebRTC.rs](https://github.com/webrtc-rs/webrtc) · [libdatachannel](https://github.com/paullouisageneau/libdatachannel)

## How a turn works

1. Agree on protocol and simulation compatibility, rules and map digests, seed, match settings, and player slots before tick zero. Establish the starting input lead with empty warm-up turns.
2. For each input tick, every active player submits one envelope with a tick number and their orders, including an empty envelope when idle. Start with a fixed input lead of two to four ticks at 20 Hz and queue new orders for the next eligible unsent tick. Show immediately that the order is queued, then measure the time until the unit starts responding, including time spent waiting for a route. [Simulation tick contract](simulation.md#tick-contract)
3. The coordinator binds each envelope to its authenticated slot, enforces message and tick-window limits, and commits one sorted batch per tick in player-slot and within-player order. Peers execute batches in tick order. The simulation validates unit ownership, capabilities, visibility, and costs against the execution tick. Record that same batch in the replay.
4. Encode a bulk command as one intent with a compact set of stable unit IDs. Bound payloads and test a 2,000-unit order from each player in the same turn. If an order requires multiple transport chunks, assemble it before committing the tick so all its units receive it together. Keep control and command queues bounded and monitor send-buffer pressure.
5. Compare a canonical state hash at a fixed tick interval. On divergence, stop and record the match manifest, last agreed hash, and command history for replay-based diagnosis. Replaying the same log on both platforms should identify the first divergent tick.

Wait for a missing batch and show a waiting state. Give unavailable peers a short grace period, then end the private prototype match if a required peer or the host cannot recover. Backgrounded browser tabs can throttle timers or suspend work. Treat bounded catch-up after brief interruptions, clear timeout messages, and browser sleep as test cases. Mid-match rejoin and host migration can follow once the basic protocol is stable. [Chrome background timer behavior](https://developer.chrome.com/blog/timer-throttling-in-chrome-88/)

## Hosting and operating cost

| Service | What it does | Cost driver |
| --- | --- | --- |
| Static HTTPS hosting and CDN | Serves browser files, asset packs, and desktop downloads. | Download bytes, asset size, and cache hits. |
| Small room and signaling service | Issues expiring invite tokens, assigns slots, and exchanges SDP and ICE messages. Room state can expire when a match starts or the room closes. | Room creation, active lobby connections, and signaling traffic. |
| STUN | Helps peers discover candidates for direct connections. | Connection setup requests. |
| TURN | Relays encrypted match traffic when a direct connection fails. Use short-lived credentials and usage limits. | Relayed connection time, billable bytes per link, and any provider fees. |

Match simulation runs on player devices. Direct links carry commands, with TURN as a fallback for restrictive networks. For a local proof of concept, peers can exchange offers and answers manually. Use the signaling service and force a TURN path before inviting remote testers. Download maps and content over HTTPS so their bytes stay off the match data channel. [WebRTC peer connections](https://webrtc.org/getting-started/peer-connections) · [TURN setup](https://webrtc.org/getting-started/turn-server)

Estimate TURN volume from relayed link-hours multiplied by measured billable bytes per hour per link. Count links individually because only part of a room may use TURN. Measure join success, direct versus relayed connections, per-link traffic, and stalled turns before choosing a provider or estimating a monthly bill. TURN-only rooms could be offered later if players want to conceal their IP addresses from peers, with the added relay cost reflected in the operating budget.

## Trust model and future options

Peer-hosted lockstep fits private casual matches. Every peer holds enough state to simulate hidden units, so a modified client can reveal the map. The coordinator can withhold or skew command delivery, and a slow peer can stall the match. State checksums expose disagreements but cannot enforce fair play. If ranked play or stronger trust guarantees become a priority, reuse the headless simulation on an authoritative server and send each client only its permitted view. Budget for server simulation and state replication in that mode.
