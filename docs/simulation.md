# Simulation and performance

## Tick contract

Start with a **20 Hz fixed simulation tick** and let the client render at its own frame rate. Ground units navigate on a 2D grid with terrain height and traversal data, presented as a 3D battlefield. A tick consumes an ordered batch of intents and updates the world in an explicit sequence. Start with orders and economy, then movement, visibility, combat, and cleanup. Define when a newly created unit or projectile becomes eligible to act. Record the order and timing of any rules that can change match outcomes.

- Use integer or fixed-point simulation coordinates, velocities, ranges, timers, and resource quantities. Define rounding and overflow rules. Presentation can use floating point for interpolation and animation.
- Use stable match-scoped unit IDs and seeded random streams with explicit ownership. Resolve equivalent choices with stable keys, including nearest-target ties and equal-cost path choices. Keep gameplay iteration independent of hash-map order, platform clocks, and job completion timing.
- Replay a versioned initial match manifest and ordered command log on native and Wasm. Compare canonical tick hashes that cover live entities, resources, RNG state, and pending simulation work. Derived caches can be omitted when rebuilding them produces equivalent future ticks. Hash fields in a specified order and byte encoding so padding and platform representation cannot affect the result.
- Run the first simulation single-threaded. Parallelize a measured bottleneck only when results can be merged in a stable order and become visible on the same ticks across platforms. Budget incremental work in expansions or records processed per tick.

## Scaling systems

Thousands of units per player make memory layout, navigation, and neighborhood queries early design choices.

| System | Starting design |
| --- | --- |
| Active state | Keep hot fields such as positions, orders, movement, and cooldowns in dense arrays with compact handles. Store static definition data once per unit type. Allocate feature-specific state only for units that use it, and reuse working buffers. |
| Group movement | Use a shared hierarchical route for a group order, with local steering and deterministic formation slots. Cache routes by movement class and navigation revision where useful. Resolve chokepoints with stable priorities and bounded local neighbor checks. Budget route searches across ticks and track both queue depth and how long a unit waits to move. |
| Targeting, collision, and fog | Share a spatial grid for bounded nearby queries. Stagger target acquisition while updating movement, weapon timers, and due events each tick. Update fog using an explicit grid and cadence. Profile dense engagements where one grid cell contains many units and navigation changes when buildings are placed or destroyed. |
| Weapons and effects | Use compact simulation records for projectiles that affect combat. Express trails, tracers, sound, and particles as presentation effects. Set a replayable stress workload for projectile and splash damage counts independently of unit count. |
| Orders, production, and bots | Use the same validated commands for players and scripted opponents. Schedule expensive decisions at a lower deterministic cadence. Exercise bulk orders, economy, and factory queues in the benchmark so they compete with pathing and combat for tick time. |

## Initial benchmark gates

Use seeded scenarios and release builds. The 2,000-per-player figure is a test point for the requested per-player scale. Increase it once the reference builds show headroom.

| Scenario | Active controllable units | Purpose |
| --- | ---: | --- |
| Prototype | 500 total | Compare native and Wasm replays and measure worker, render, and network boundaries early. |
| Cross-play 1v1 | 4,000 total | Exercise two 2,000-unit armies on both platforms, including a single order to a full army. |
| Small team match | 8,000 total | Exercise four 2,000-unit armies, simultaneous fights, and stacked production. |
| Capacity exploration | 16,000 total | Measure the next scale step before committing to eight-player rooms. |

For the 1v1 and team gates, target **p95 simulation steps ≤12 ms and p99 ≤25 ms** with a 50 ms tick interval. At 1080p, target 60 FPS desktop and 30 FPS browser as initial floors on recorded reference hardware. Track p95 frame times, missed ticks, worker handoff cost, peak memory, path queue age, and command-to-action delay. Choose and record representative hardware, browser versions, graphics settings, and OS before treating results as release criteria. Use the slowest supported client as the cross-play reference.

Measure a quiet economy, army movement through a choke and a newly blocked route, sustained combat with fog and projectile churn, and mass construction and destruction. Run each gate headless and with a moving camera and visible battle. Compare the canonical replay hash on native and running browser Wasm throughout. Record independent counts for units, buildings, and projectiles so performance gains can be compared against the same workload.
