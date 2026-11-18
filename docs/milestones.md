# Development milestones

## 1. Cross-platform benchmark

Completed November 18, 2026. [Reference runs, measurements, and engineering decisions](benchmark.md).

- Build one headless Rust simulation and run the same seeded movement and combat trace natively and in browser Wasm. Verify the periodic state hashes agree.
- Render a ground map with 500 moving units in Bevy. Prove the browser Worker handoff and native desktop executable. Jump to a synthetic 4,000-unit render and simulation load early to expose poor scaling before building the roster.
- Export one rigged Blender unit with idle, movement, and firing clips and player-color regions. Play all three clips and check multiple player colors on desktop and browser. Measure the cost of many animated instances. [Unit rigs and animation](content.md#unit-rigs-and-animation) · [Player colors](content.md#player-colors)
- Exchange command batches between a native process and a browser tab via WebRTC, first on a direct path and then with TURN forced. Test another physical network before choosing the native transport library.
- Record the reference OS, browser, CPU, GPU, resolution, frame and tick percentiles, and transfer cost. Use the results to decide whether Bevy's built-in instancing or a specialized rendering path meets the budget. [Benchmark design](simulation.md#initial-benchmark-gates)

## 2. First playable 1v1

Build the [first playable match](first-match.md) with an HQ, builder, resource income, factory, scout, combat unit, and one map with a choke and an open route. Compile the map from either a Blender scene or a seeded generator and check that the rendered terrain matches the simulation grid. Add selection, control groups, queued orders, camera, move and attack-move orders, and basic fog. Run it offline against a scripted enemy. Prove that a new unit using existing capabilities can be added through the content pipeline. Exercise 4,000 active units with representative systems and record deterministic replays before fleshing out more factions.

## 3. Private online playtest

Add room links, the compatibility handshake, turn buffering, TURN fallback, and mismatch diagnostics. Verify native-to-browser and browser-to-browser 1v1 on ordinary home networks and a relay-only run. Exercise simultaneous full-army commands, added latency and packet loss, briefly hidden tabs, host exit, and incompatible content. Track join success, relay volume, and delays between a click and game response. Ship this milestone to testers once both builds meet the agreed 1v1 performance gates.

## 4. Team scale

Prove the 8,000-active-unit workload in a four-player match with mixed desktop and browser clients. Stress choke congestion, projectile storms, simultaneous production, and a slower supported machine. Measure the coordinator's upload, relay usage, stalled turns, and sim headroom. Use the results to set team-room and unit caps. Keep 16,000 active units as a capacity experiment until the smaller team workload meets the targets.

## Decisions before wider release

- Choose supported native operating systems and browser/GPU baselines after the benchmark. Decide whether WebGL2 coverage is worth maintaining.
- Choose how large a typical team room should be and whether the per-player cap should exceed the provisional 2,000-unit benchmark.
- Decide whether reconnect, public rooms, ranked matches, and public mod packs belong in the first wider release. The private playtest makes those decisions easier to price.
