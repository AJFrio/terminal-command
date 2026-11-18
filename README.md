# Terminal Command

Terminal Command is an original large-scale 3D RTS in development. The first milestone is a synthetic cross-platform benchmark with a Linux desktop executable, a browser build, and a WebRTC command exchange.

See the [benchmark results](docs/benchmark.md) and [game design](docs/README.md).

## Build and run

Use Rust 1.95 or later. Run the commands from the repository root.

```sh
cargo build --locked --release -p terminal-command -p tc-session -p tc-rtc
target/release/terminal-command
target/release/terminal-command --units 4000 --rigs 64 --ticks 400 > desktop.json
target/release/terminal-command --inspect
```

The timed executable writes a JSON report and exits. The default window and timed presets use a 1920 × 1080 client area. Rivet inspection accepts `1` for idle, `2` for movement, `3` for firing, and `4` to cycle. Run `--verify-rig` to print the two player-color counts and pose-change evidence for all three clips.

Build the browser edition and serve it on loopback for local WebGPU development.

```sh
rustup target add wasm32-unknown-unknown
cargo install wasm-bindgen-cli --version 0.2.130 --locked
tools/build-web.sh
python3 -m http.server 8069 --bind 127.0.0.1 --directory dist/web
```

Open [the benchmark](http://127.0.0.1:8069/), [4,000 units with 64 rigs](http://127.0.0.1:8069/?units=4000&rigs=64), or [Rivet inspection](http://127.0.0.1:8069/?mode=inspect). Use HTTPS when serving the browser build off loopback. A 400-tick browser run offers a JSON download when it completes.

## Compare replay hashes

```sh
target/release/tc-replay 4000 400 21041 > native-replay.json
```

Download the JSON from the matching [headless browser replay](http://127.0.0.1:8069/?mode=replay&units=4000&ticks=400&seed=21041). Compare the complete deterministic traces with `jq`, including the initial, periodic, and final hashes.

```sh
jq -e -s 'length == 2 and (.[0].trace == .[1].trace)' native-replay.json browser-replay.json
cargo test --locked --release -p tc-session
```

## Verify native-to-browser WebRTC

Start `target/release/tc-rtc` and open the complete one-time URL it prints. The process exits with a JSON report after verifying the ordered command batches, counts, and selected ICE candidate types. Start a fresh process per pass.

The default pass uses host candidates. Set `TC_ICE_URL` to a STUN URL to try a direct path across networks. To require TURN at both endpoints, set `TC_ICE_URL` to a TURN URL, along with `TC_TURN_USER` and `TC_TURN_CREDENTIAL`. Both peers must be able to reach the TURN service. Keep the signal listener on loopback and serve it through authenticated HTTPS signaling when a browser is on another network. The session token goes in the URL fragment.
