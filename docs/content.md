# Units and content

The unit definition is the extension point for new vehicles, robots, and structures. Each definition combines reusable capabilities such as movement, vision, weapons, construction, and production. Most roster additions should require a definition and art assets. A new mechanic can add a reusable simulation system with explicit rules, performance costs, and a native/Wasm replay case.

## Authoring and loading

1. Author a unit definition with a stable, namespaced ID, a footprint, durability, build cost, and references to reusable capabilities. Give each faction its own names, shapes, and visual identity.
2. Add its visual definition with a model, icon, effects, and audio. Use GLB for runtime models and keep editable source art and its provenance. [Khronos glTF specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)
3. Run a content compiler that checks schema version, ID uniqueness, numeric bounds, references, asset availability, and cross-platform asset budgets. Compile rules and gameplay map data into a bundle with stable ordering and a digest. Emit a separate manifest for visual assets.
4. Load definitions once per match and assign compact runtime IDs. Each unit instance holds its definition handle and changing state. Load the selected map and roster assets as needed. Expanding the catalog should mainly affect the content built or loaded. The simulation cost should follow the units present and the work their capabilities do.

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
