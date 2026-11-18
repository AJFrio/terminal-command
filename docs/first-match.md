# First playable match

This brief defines a starting point for a private 1v1 ground battle. Its rules and presentation are playtest assumptions that can change as the game develops. The central experience is **army maneuver**. A player should be able to split a large force, send groups along different routes, and understand where each group is headed.

## Match loop

Each player starts with an HQ and a mobile builder. The builder constructs resource collectors and a factory. Collectors provide one resource used to build structures and units. The factory produces a fast scout and a combat unit. Players expand their economy, scout, assemble forces, and attack the opposing base. A player wins when the opposing HQ is destroyed.

Start with one map that offers a chokepoint and a second, more open route. Place starting resources and routes so each player has room to build and can contest the space between bases. Fog of war makes scouting useful and keeps the enemy's current movements hidden until observed. Use one robot and one vehicle design for the initial roster and give them distinct silhouettes and roles.

## Army control

Support box selection, control groups, move, attack-move, and queued orders. Show the current selection, destination, and queued route clearly enough for players to divide an army and follow both groups. A click should receive immediate visual acknowledgement, with units beginning to act as soon as the simulation and route are ready.

Playtest a group of 2,000 mixed-speed units receiving one attack-move order through a choke. As a starting behavior, assign stable formation positions, let the group spread into available space, and have units engage enemies encountered along the route. Test whether faster units should wait for slower units or advance, how the formation reforms after the choke, and how to show congestion and unreachable destinations. Use the results to settle the behavior.

## Battlefield readability

Build one rigged robot and one vehicle in Blender and view them in a representative battle. At normal play zoom, players should recognize each unit's class, owner, and current action. At wide zoom, tactical icons should preserve unit and player identification while terrain, routes, and impassable areas remain legible. Test player colors on the units, icons, and selection feedback against both light and dark terrain. [Player colors](content.md#player-colors)

## Prototype evaluation

Choose and record a reference desktop, browser, resolution, and graphics settings before comparing builds. Run a repeatable 4,000-unit battle with 2,000 units per player, simultaneous army orders, active factories, fog, and a moving camera. Measure frame and simulation times, missed ticks, and time from a click until units begin moving, including route waiting time. Record the workload and results against the [initial benchmark gates](simulation.md#initial-benchmark-gates).

Playtest whether players can scout, expand, split their army, choose a route, and destroy the opposing HQ. Capture observations about control clarity and responsiveness alongside the performance numbers. Use those findings to revise the rules and decide what to build next.
