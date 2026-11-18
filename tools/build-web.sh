#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ "$(wasm-bindgen --version)" != "wasm-bindgen 0.2.130" ]]; then
    printf '%s\n' 'Install wasm-bindgen-cli 0.2.130 with cargo install wasm-bindgen-cli --version 0.2.130 --locked.' >&2
    exit 1
fi
build_dir="${CARGO_TARGET_DIR:-target}"
cargo build --locked --release --target wasm32-unknown-unknown -p tc-web -p tc-worker
mkdir -p dist/web/{pkg,assets}
cp apps/web/site/* dist/web/
cp models/rivet.glb dist/web/assets/
wasm-bindgen --target web --no-typescript --remove-name-section --remove-producers-section --out-dir dist/web/pkg --out-name client \
    "$build_dir/wasm32-unknown-unknown/release/tc_web.wasm"
wasm-bindgen --target web --no-typescript --remove-name-section --remove-producers-section --out-dir dist/web/pkg --out-name worker \
    "$build_dir/wasm32-unknown-unknown/release/tc_worker.wasm"
