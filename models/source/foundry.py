"""Shared geometry, materials, skinning, and pose helpers for the Foundry units."""

import math

import bmesh
import bpy
from mathutils import Vector


PALETTE = {
    "Ceramic": ("CFC6AB", 0.38, 0.18, 0),
    "PlayerColor": ("15BDAF", 0.32, 0.30, 0),
    "Frame": ("3C4B51", 0.44, 0.54, 0),
    "Carbon": ("1C252B", 0.60, 0.16, 0),
    "Alloy": ("859597", 0.35, 0.62, 0),
    "SafetyAmber": ("F29243", 0.38, 0.24, 0),
    "Optics": ("94F9EB", 0.22, 0.16, 1.9),
    "Pulse": ("FFBB67", 0.25, 0.02, 4.0),
}


def linear_rgb(value):
    result = tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(
        c / 12.92 if c < 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in result
    )


def material(name, color, roughness, metal=0, emission=0):
    rgba = (*linear_rgb(color), 1)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = rgba
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Emission Color"].default_value = rgba
    shader.inputs["Emission Strength"].default_value = emission
    return mat


def chamfer(w, d, k):
    x, y = w / 2, d / 2
    return [
        (-x + k, -y),
        (x - k, -y),
        (x, -y + k),
        (x, y - k),
        (x - k, y),
        (-x + k, y),
        (-x, y - k),
        (-x, -y + k),
    ]


class Unit:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.bones = {}
        self.vertices = []
        self.faces = []
        self.face_materials = []
        self.smooth_faces = []
        self.weights = {}
        self.mats = {key: material(key, *props) for key, props in PALETTE.items()}
        self.bone("root", (0, 0, 0), length=0.24)

    def bone(self, name, origin, parent="root", length=0.14):
        self.bones[name] = (Vector(origin), parent, length)
        return name

    def shape(self, verts, faces, mat, bone, bevel=0, smooth=()):
        bm = bmesh.new()
        bvs = [bm.verts.new(v) for v in verts]
        for i, face in enumerate(faces):
            f = bm.faces.new([bvs[j] for j in face])
            if i in smooth:
                f.smooth = True
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        if bevel >= 0.009:
            bmesh.ops.bevel(
                bm,
                geom=list(bm.edges),
                offset=bevel,
                segments=1,
                affect="EDGES",
                clamp_overlap=True,
            )
        bm.verts.index_update()
        start = len(self.vertices)
        self.vertices.extend(tuple(v.co) for v in bm.verts)
        self.weights.setdefault(bone, []).extend(range(start, len(self.vertices)))
        for face in bm.faces:
            self.faces.append(tuple(start + v.index for v in face.verts))
            self.face_materials.append(mat)
            self.smooth_faces.append(face.smooth)
        bm.free()

    def loft(self, axis, rings, mat, bone, bevel=0):
        def unpack(a, b, h):
            if axis == "z":
                return a, b, h
            if axis == "y":
                return a, h, b
            return h, a, b

        n = len(rings[0][1])
        verts = [unpack(a, b, h) for h, pts in rings for a, b in pts]
        faces = [tuple(range(n))[::-1]]
        for k in range(len(rings) - 1):
            for i in range(n):
                j = (i + 1) % n
                faces.append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
        faces.append(tuple(range(len(verts) - n, len(verts))))
        self.shape(verts, faces, mat, bone, bevel)

    def plate(self, axis, start, end, outline, mat, bone, bevel=0):
        self.loft(axis, [(start, outline), (end, outline)], mat, bone, bevel)

    def block(self, center, size, mat, bone, *, corners=0.05, bevel=0.009, rotate=0):
        x, y, z = center
        w, d, h = size
        c, s = math.cos(rotate), math.sin(rotate)
        pts = [
            (x + a * c - b * s, y + a * s + b * c)
            for a, b in chamfer(w, d, min(corners, w * 0.24, d * 0.24))
        ]
        self.plate("z", z - h / 2, z + h / 2, pts, mat, bone, bevel)

    def round(self, start, end, radius, mat, bone, *, tip=None, n=12):
        # Ring profiles generate both cylindrical and tapered mechanical parts.
        origin, target = Vector(start), Vector(end)
        direction = target - origin
        rotation = direction.to_track_quat("Z", "Y")
        verts = [
            tuple(
                center
                + rotation
                @ Vector(
                    (
                        r * math.cos(2 * math.pi * i / n),
                        r * math.sin(2 * math.pi * i / n),
                        0,
                    )
                )
            )
            for center, r in (
                (origin, radius),
                (target, radius if tip is None else tip),
            )
            for i in range(n)
        ]
        faces = [tuple(range(n))[::-1]]
        faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        faces += [tuple(range(n, 2 * n))]
        self.shape(verts, faces, mat, bone, smooth=range(1, n + 1))

    def rail(self, start, end, width, depth, mat, bone, bevel=0.012):
        start, end = Vector(start), Vector(end)
        delta = end - start
        rot = delta.to_track_quat("Z", "Y")
        verts = [
            tuple(center + rot @ Vector((x, y, 0)))
            for center in (start, end)
            for x, y in chamfer(width, depth, min(width, depth) * 0.20)
        ]
        faces = [(7, 6, 5, 4, 3, 2, 1, 0), tuple(range(8, 16))]
        faces += [(i, (i + 1) % 8, 8 + (i + 1) % 8, 8 + i) for i in range(8)]
        self.shape(verts, faces, mat, bone, bevel)

    def chip(self, axis, level, center, length, angle, mat, bone):
        ring = [
            (-0.5, 0.02),
            (-0.13, -0.09),
            (0.27, -0.045),
            (0.50, 0),
            (0.11, 0.055),
            (-0.21, 0.095),
        ]
        c, s = math.cos(angle), math.sin(angle)
        self.plate(
            axis,
            level - 0.00035,
            level + 0.00035,
            [
                (
                    center[0] + length * (x * c - y * s),
                    center[1] + length * (x * s + y * c),
                )
                for x, y in ring
            ],
            mat,
            bone,
        )

    def stamp(self, center, height, digits, mat, bone, top=True):
        # Monoline industrial stencils formed directly from the surface geometry.
        strokes = {
            "0": ("a", "b", "c", "d", "e", "f"),
            "1": ("b", "c"),
            "2": ("a", "b", "g", "e", "d"),
            "3": ("a", "b", "g", "c", "d"),
        }
        sections = {
            "a": (0, 0.50, 0.55, 0.09),
            "g": (0, 0, 0.50, 0.09),
            "d": (0, -0.50, 0.55, 0.09),
            "f": (-0.275, 0.25, 0.085, 0.45),
            "b": (0.275, 0.25, 0.085, 0.45),
            "e": (-0.275, -0.25, 0.085, 0.45),
            "c": (0.275, -0.25, 0.085, 0.45),
        }
        ox, oy, oz = center
        for index, digit in enumerate(digits):
            for stroke in strokes[digit]:
                x, y, w, h = sections[stroke]
                x = ox + (x + (index - (len(digits) - 1) / 2) * 0.79) * height
                if top:
                    self.block(
                        (x, oy + y * height, oz),
                        (w * height, h * height, 0.0025),
                        mat,
                        bone,
                        corners=0.001,
                        bevel=0,
                    )
                else:
                    self.block(
                        (x, oy, oz + y * height),
                        (w * height, 0.0025, h * height),
                        mat,
                        bone,
                        corners=0.001,
                        bevel=0,
                    )

    def make_rig(self):
        scene = bpy.context.scene
        scene.name = self.name
        scene.unit_settings.system = "METRIC"
        collection = bpy.data.collections.new(self.name + " | Unit")
        scene.collection.children.link(collection)
        armature = bpy.data.armatures.new(self.name + " Skeleton")
        self.rig = bpy.data.objects.new(self.name + " Rig", armature)
        collection.objects.link(self.rig)
        self.rig["unit_id"] = "foundry:" + self.name.lower()
        self.rig["role"] = self.role
        self.rig["player_color_material"] = "PlayerColor"
        self.rig["source"] = "Original hard-surface design for Terminal Command"
        self.rig["facing_blender"] = "-Y"
        self.rig["facing_gltf"] = "+Z"
        self.rig["in_place"] = True
        self.rig.show_in_front = True
        armature.display_type = "STICK"
        bpy.context.view_layer.objects.active = self.rig
        self.rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        for name, (point, parent, length) in self.bones.items():
            bone = armature.edit_bones.new(name)
            bone.head = point
            bone.tail = point + Vector((0, length, 0))
            if name != "root":
                bone.parent = armature.edit_bones[parent]
            bone.use_deform = name in self.weights
        bpy.ops.object.mode_set(mode="OBJECT")

        mesh = bpy.data.meshes.new(self.name + " Armor and Mechanics")
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.validate()
        self.skin = bpy.data.objects.new(self.name + " Geometry", mesh)
        collection.objects.link(self.skin)
        self.skin.parent = self.rig
        for mat in self.mats.values():
            mesh.materials.append(mat)
        indices = {key: index for index, key in enumerate(self.mats)}
        for poly, mat, smooth in zip(
            mesh.polygons, self.face_materials, self.smooth_faces, strict=True
        ):
            poly.material_index = indices[mat]
            poly.use_smooth = smooth
        for bone, vertices in self.weights.items():
            group = self.skin.vertex_groups.new(name=bone)
            group.add(vertices, 1.0, "REPLACE")
        deform = self.skin.modifiers.new("Rigid part skinning", "ARMATURE")
        deform.object = self.rig
        self.skin.select_set(True)
        mesh.calc_loop_triangles()
        print(
            self.name,
            len(mesh.loop_triangles),
            "triangles,",
            len(armature.bones),
            "bones",
            flush=True,
        )


def flash(unit, at, width, bone):
    x, y, z = at
    width /= 400  # The inactive flash is sub-millimeter in the bind pose.
    ring = [
        (
            x + width * math.cos(i * math.pi / 8) * (1 if i % 2 == 0 else 0.40),
            z + width * math.sin(i * math.pi / 8) * (1 if i % 2 == 0 else 0.40),
        )
        for i in range(16)
    ]
    outer = [
        (
            x + width * 0.13 * math.cos(i * math.pi / 8),
            z + width * 0.13 * math.sin(i * math.pi / 8),
        )
        for i in range(16)
    ]
    unit.loft(
        "y",
        [(y - width * 2.6, outer), (y - width * 0.32, ring), (y + width * 0.45, outer)],
        "Pulse",
        bone,
    )


def tween(frame, stops):
    if frame <= stops[0][0]:
        return stops[0][1]
    for (left, a), (right, b) in zip(stops, stops[1:]):
        if frame <= right:
            t = (frame - left) / (right - left)
            t = t * t * (3 - 2 * t)
            return a + (b - a) * t
    return stops[-1][1]


def set_pose(rig, name, *, x=0, y=0, z=0, location=(0, 0, 0), scale=1):
    b = rig.pose.bones[name]
    b.rotation_euler = x, y, z
    b.location = location
    b.scale = (scale,) * 3
