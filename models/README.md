# Foundry units

The Foundry roster is generated with Blender Python. Each unit has an editable
`.blend` file and a matching animated `.glb` export.

- [Siltback recipe](source/siltback.py) defines the scout’s armor, tread mechanism, and clips.
- [Rivet recipe](source/rivet.py) defines the robot’s armor, joints, and clips.
- [Kiln recipe](source/kiln.py) defines the factory’s production bay, shutters, and clips.
- [Shared helpers](source/foundry.py) define the palette, geometry, and rigid skinning.

## Regenerate the assets

Run from the repository root with Blender 5.2.2, the version used to build these
assets. The script uses Blender’s bundled glTF exporter and Python modules.

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python models/source/build_units.py -- --output-dir /tmp/terminal-command-models
```

The command builds the roster. Use `--unit siltback`, `--unit rivet`, or
`--unit kiln` to rebuild one asset. Omit `--output-dir` and pass `--overwrite`
to replace the generated files in `models/`. Regeneration replaces any hand
edits to those files with the recipe’s version.

Open a `.blend` and press Space to preview its marked clips. Each `.glb`
contains the rig and the `PlayerColor` material. Siltback and Rivet use `idle`,
`move`, `fire`, and `destroyed`. Keep the move cycle in place and the origin at
ground level when editing the recipes.

## Kiln factory

`foundry:kiln` is the ground-unit factory for Siltback and Rivet. The model is
8.62 m wide, 9.05 m deep including the ramp, and 5.80 m tall at rest. The origin
is at ground level. The factory faces Blender `-Y` / glTF `+Z`.

| Clip | Motion |
| --- | --- |
| `idle` | Cooling fan turns and the carriage indicator pulses. |
| `produce` | The carriage traverses the rail, lowers its press, and returns in a 3-second loop. |
| `deploy` | The shutters open, hold fully open from 0.80 to 3.53 seconds, and close. |
| `destroyed` | The carriage drops, the exhaust stacks buckle, and the shutters jam. |

`socket_unit_spawn` is on the bay floor inside the building.
`socket_unit_exit` is on the ground past the ramp. Use these joints as position
markers, with deployed units facing the same direction as the factory.
