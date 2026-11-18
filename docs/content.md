# Units and content

The unit definition is the extension point for new vehicles, robots, and structures. Each definition combines reusable capabilities such as movement, vision, weapons, construction, and production. Most roster additions should require a definition and art assets. A new mechanic can add a reusable simulation system with explicit rules, performance costs, and a native/Wasm replay case.

## Authoring and loading

1. Author a unit definition with a stable, namespaced ID, a footprint, durability, build cost, and references to reusable capabilities. Give each faction its own names, shapes, and visual identity.
2. Model, rig, and animate the unit in Blender. Keep its editable `.blend` source and provenance, and reference the exported GLB, icon, effects, and audio from its visual definition. [Blender glTF exporter documentation](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html)
3. Run a content compiler that checks schema version, ID uniqueness, numeric bounds, references, asset availability, and cross-platform asset budgets. Compile rules and gameplay map data into a bundle with stable ordering and a digest. Emit a separate manifest for visual assets.
4. Load definitions once per match and assign compact runtime IDs. Each unit instance holds its definition handle and changing state. Load the selected map and roster assets as needed. Expanding the catalog should mainly affect the content built or loaded. The simulation cost should follow the units present and the work their capabilities do.

## Unit rigs and animation

The first Foundry units have Blender Python recipes for regenerating their editable sources and GLB exports. [Foundry unit build instructions](../models/README.md)

Export the mesh, armature, and named clips together as a GLB. Rigid robot parts such as armor plates and turrets can follow individual bones. Use weighted skinning where a part needs to deform. Author clips for the states each unit uses, such as `idle`, `move`, `fire`, and `destroyed`. Bake constraint-driven motion into exportable keyframes and validate the clip names and playback in both builds. [Khronos Blender exporter documentation](https://github.com/KhronosGroup/glTF-Blender-IO/blob/main/docs/blender_docs/scene_gltf2.rst) · [Bevy animated GLB example](https://bevy.org/examples/animation/animated-mesh/)

Map simulation states and events to clips through the unit's visual definition. Keep movement cycles in place and let the simulation position the unit and set weapon timing. Share rig and clip assets across instances. For large armies, profile full rigs up close, less frequent pose updates at distance, and tactical icons at wide zoom.

## Player colors

Each unit has a fully styled base design, including its own painted surfaces, materials, and wear. In Blender, artists designate areas such as armor panels, stripes, or markings for the owning player's color. Keep the rest of the authored finish visible. Check each design at normal play and wide zoom so ownership remains easy to identify across the roster.

Use a player-color mask or a clearly designated material slot in the exported asset. The visual definition identifies the colorable regions, and the renderer applies the owning player's color while preserving the underlying surface detail. Prototype the material on desktop and browser and verify that it survives the Blender-to-GLB export. Share meshes, textures, and materials across units, and pass the player color as instance data where the rendering path supports it. Measure batching and rendering cost with mixed units and colors at the target army scale.

Assign distinct colors in the match lobby and associate them with player slots for all clients. When ownership changes, the displayed color follows the new owner. Carry the same identification into tactical icons and selection feedback. Test colors against varied terrain and lighting, including color-vision-friendly choices and additional ownership cues such as icons or outlines.

## Terrain and environments

- **Blender-authored maps.** Sculpt or model the terrain and dress it with props in Blender. Export terrain meshes and props for rendering. Bake gameplay height and traversal data from the terrain and tag gameplay markers such as spawn points, blockers, and resource sites.
- **Procedural maps.** Generate terrain, traversal data, and gameplay markers from a seed and versioned settings. Use Blender-authored props wherever they fit. Bake generated maps through the content compiler first and retain the seed, generator version, and parameters for reproduction.

Both workflows produce the same map bundle. The simulation reads canonical heights, traversal data, blockers, spawns, and resource sites. The client loads the corresponding terrain chunks, materials, and props. Validate gameplay markers and their alignment with the rendered terrain. Include the compiled gameplay map digest in multiplayer and replay checks so desktop and browser use the same battlefield.

## Example unit

This proposed TOML definition adds a ground scout by combining existing capabilities. Values are illustrative. Units of measure belong in the schema so the compiler can convert authored numbers consistently.

```toml
schema_version = 1
id = "foundry:siltback"
footprint_cells = [2, 2]
hit_points = 180
build_ticks = 200

[cost]
alloy = 35

[capabilities]
movement = "core:light_tracks"
vision = "core:short_range_optics"
weapons = ["core:burst_cannon"]
```

The visual manifest uses the same ID to associate the scout with its GLB, portrait, and sound sets. Hit volumes, weapon range, and movement restrictions come from the rules bundle. The model, animation timing, and render level of detail affect what players see.

## Compatibility and expansion

- Include the rules and map digest in the multiplayer handshake and replay header. Version the schema and preserve the rule bundle needed to replay a match. Tuning changes can produce a new bundle while keeping unit IDs stable.
- Reuse meshes, materials, and textures where they fit the design. Set budgets for materials per unit, distant representations, and effect density. Benchmark a mixed roster as well as a single repeated unit so render batching benefits are measured realistically.
- Start with first-party content and validate every pack through the compiler. Data-only mod packs can use the same format if public mod support becomes a goal. Decide pack discovery, distribution, and scripting after the core format and multiplayer compatibility checks are proven.
