# Terminal Command

Terminal Command is a large-scale 3D RTS with original robotic infantry, armored vehicles, and industrial bases. Players can download a native desktop build or open the game in a desktop browser, then play together in the same match. Beyond All Reason and Total Annihilation are references for scale, army control, and the feel of mechanized warfare. Terminal Command will have its own factions, unit designs, maps, and presentation.

## Proposed direction

| Design choice | Starting point |
| --- | --- |
| Desktop and browser | One Rust simulation compiled to native code and WebAssembly, with Bevy as the first candidate for rendering, UI, and input. |
| Army scale | Budget for **2,000 active units per player** as a working number. Prove 4,000 total in 1v1, then 8,000 total in a four-player match. |
| Content authoring | Combine reusable unit definitions with rigged, animated Blender exports. Build maps in Blender or generate them procedurally. |
| Online play | Start with invite-only WebRTC matches. Each player simulates the match locally from the same ordered commands. A small service handles invites and connection setup, with TURN relay when required. |

## Design documents

- [Architecture](architecture.md) covers platform choices, code boundaries, and how the simulation and client fit together.
- [First playable match](first-match.md) describes the starting 1v1 rules, army controls, visual goals, and playtest.
- [Simulation and performance](simulation.md) covers deterministic ticks, pathfinding, and the benchmark workloads and budgets.
- [Units and content](content.md) describes unit definitions, Blender rigs and animation exports, and both terrain workflows.
- [Multiplayer](multiplayer.md) covers the command protocol, connection failures, hosting costs, and fairness tradeoffs.
- [Development milestones](milestones.md) gives the order of work and the evidence needed before expanding scope.

These are first-pass design decisions. The per-player scale is a product goal. The exact count, tick rate, graphics baselines, and technology choices are hypotheses to test. The first playable assumes keyboard and mouse, ground combat, one map, and private 1v1 across desktop and browser. Team-game size, launch platforms, and support for public mods are open decisions.
