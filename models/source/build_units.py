"""Build the Foundry units in a background Blender session."""

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import bpy
from mathutils import Vector

SOURCE_DIR = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SOURCE_DIR))

from foundry import set_pose  # noqa: E402
import kiln  # noqa: E402
import rivet  # noqa: E402
import siltback  # noqa: E402

MOBILE_CLIPS = (("idle", 61, 1), ("move", 31, 2), ("fire", 20, 1), ("destroyed", 46, 1))
UNITS = {
    "siltback": (siltback.make_siltback, siltback.pose, MOBILE_CLIPS, 0.60, 4.9),
    "rivet": (rivet.make_rivet, rivet.pose, MOBILE_CLIPS, 1.30, 4.45),
    "kiln": (kiln.make_kiln, kiln.pose, kiln.CLIPS, 2.10, 15.2),
}


def make_actions(unit, pose, clips):
    rig = unit.rig
    ad = rig.animation_data_create()
    actions = []
    for name, frames, repeat in clips:
        action = bpy.data.actions.new(name)
        action.use_fake_user = True
        slot = action.slots.new(id_type="OBJECT", name=rig.name)
        ad.action = action
        ad.action_slot = slot
        for frame in range(1, frames + 1):
            for b in rig.pose.bones:
                b.rotation_mode = "XYZ"
                set_pose(rig, b.name)
            pose(unit, name, frame, (frame - 1) / (frames - 1))
            for b in rig.pose.bones:
                for path in ("location", "rotation_euler", "scale"):
                    b.keyframe_insert(path, frame=frame, group=b.name)
        actions.append((action, slot, frames, repeat))
        ad.action = None
    return actions


def configure_preview(scene, rig, actions):
    ad = rig.animation_data
    ad.action = None
    for track in list(ad.nla_tracks):
        ad.nla_tracks.remove(track)
    frame = 1
    for action, slot, frames, repeat in actions:
        track = ad.nla_tracks.new()
        track.name = action.name
        strip = track.strips.new(action.name, frame, action)
        strip.action_slot = slot
        strip.repeat = repeat
        strip.extrapolation = "NOTHING"
        scene.timeline_markers.new(action.name, frame=frame)
        frame += (frames - 1) * repeat
    scene.frame_start = 1
    scene.frame_end = frame
    scene.frame_set(1)


def view_settings(height, distance, direction):
    rotation = Vector(direction).to_track_quat("Z", "Y")
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.region_3d.view_perspective = "ORTHO"
                space.region_3d.view_rotation = rotation
                space.region_3d.view_distance = distance
                space.region_3d.view_location = (0, 0, height)
                space.overlay.show_overlays = False
                space.shading.type = "SOLID"
                space.shading.color_type = "MATERIAL"
                space.shading.light = "STUDIO"
                space.shading.studiolight_rotate_z = 0.35
                space.shading.show_cavity = True
                space.shading.cavity_type = "BOTH"
                space.shading.curvature_ridge_factor = 1.23
                space.shading.curvature_valley_factor = 1.17


def save_unit(output_dir, unit_name):
    builder, pose, clips, view_height, view_distance = UNITS[unit_name]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    unit = builder()
    actions = make_actions(unit, pose, clips)
    scene.frame_set(1)
    for action, slot, _, _ in actions:
        track = unit.rig.animation_data.nla_tracks.new()
        track.name = action.name
        strip = track.strips.new(action.name, 1, action)
        strip.action_slot = slot
        track.mute = True

    stem = output_dir / unit_name
    # Export the skin and skeleton as separate glTF scene roots. The armature
    # modifier still binds the mesh to this scene’s single rig.
    unit.skin.parent = None
    status = bpy.ops.export_scene.gltf(
        filepath=str(stem.with_suffix(".glb")),
        use_selection=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_anim_slide_to_zero=True,
        export_reset_pose_bones=True,
        export_optimize_animation_size=True,
        export_optimize_animation_keep_anim_armature=False,
        export_optimize_animation_keep_anim_object=False,
        export_extras=True,
        export_yup=True,
        export_apply=False,
    )
    if status != {"FINISHED"} or not stem.with_suffix(".glb").is_file():
        raise RuntimeError(f"GLB export failed for {unit_name}")
    unit.skin.parent = unit.rig
    configure_preview(scene, unit.rig, actions)
    scene["Animation preview"] = "Press Space to play the marked animation timeline."
    scene["Coordinates"] = (
        "Meters. Blender -Y forward and Z up. GLB +Z forward and Y up."
    )
    view_settings(view_height, view_distance, (3, -5, 3.8))
    bpy.context.preferences.filepaths.save_version = 0
    status = bpy.ops.wm.save_as_mainfile(
        filepath=str(stem.with_suffix(".blend")), compress=True
    )
    if status != {"FINISHED"} or not stem.with_suffix(".blend").is_file():
        raise RuntimeError(f"Blender save failed for {unit_name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--unit", choices=UNITS, help="Build a single unit. Defaults to all units."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=SOURCE_DIR.parent,
        help="Directory for the .blend and .glb files. Defaults to models/.",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Replace existing unit files."
    )
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )
    if not bpy.app.background:
        parser.error("Run this script with blender --background.")

    units = (args.unit,) if args.unit else tuple(UNITS)
    output_dir = args.output_dir.resolve()
    filenames = [f"{unit}.{suffix}" for unit in units for suffix in ("blend", "glb")]
    existing = [name for name in filenames if (output_dir / name).exists()]
    if existing and not args.overwrite:
        parser.error(
            f"Output files already exist: {', '.join(existing)}. "
            "Use --overwrite or choose a new --output-dir."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".build-units-", dir=output_dir) as staging:
        staging = Path(staging)
        for unit in units:
            save_unit(staging, unit)
        for name in filenames:
            target = output_dir / name
            if args.overwrite:
                (staging / name).replace(target)
            else:
                target.hardlink_to(staging / name)
            print(f"Wrote {target}")


if __name__ == "__main__":
    main()
