"""Siltback geometry, rig pivots, and baked animation poses."""

import math

from mathutils import Euler, Vector

from foundry import Unit, chamfer, flash, set_pose, tween


TRACK_H = 0.78
TRACK_R = 0.286
TRACK_Z = 0.325
TRACK_LENGTH = TRACK_H * 4 + TRACK_R * math.tau
LINKS = 16


def track_circle(s):
    s %= TRACK_LENGTH
    if s < 2 * TRACK_H:
        return -TRACK_H + s, TRACK_Z + TRACK_R, 0
    s -= 2 * TRACK_H
    if s < math.pi * TRACK_R:
        a = s / TRACK_R
        return TRACK_H + TRACK_R * math.sin(a), TRACK_Z + TRACK_R * math.cos(a), -a
    s -= math.pi * TRACK_R
    if s < 2 * TRACK_H:
        return TRACK_H - s, TRACK_Z - TRACK_R, -math.pi
    a = (s - 2 * TRACK_H) / TRACK_R
    return (
        -TRACK_H - TRACK_R * math.sin(a),
        TRACK_Z - TRACK_R * math.cos(a),
        -math.pi - a,
    )


def track_pose(s):
    y, z, angle = track_circle(s)
    slope, up = abs(math.sin(angle)), math.cos(angle)
    lower_pad = slope * (TRACK_LENGTH / LINKS * 0.43) - min(-0.034 * up, 0.026 * up)
    lower_ridge = slope * 0.087 - min(0.023 * up, 0.039 * up)
    return y, max(z, lower_pad, lower_ridge), angle


def make_siltback():
    unit = Unit("Siltback", "Tracked scout")
    hull = unit.bone("hull", (0, 0, 0.52))
    turret = unit.bone("turret", (0.29, 0.12, 0.94), hull)
    recoil = unit.bone("recoil", (0.29, -0.05, 1.01), turret)
    mast = unit.bone("antenna", (-0.43, 0.67, 0.94), hull)
    hatch = unit.bone("rear_hatch", (0.01, 0.85, 0.85), hull)
    unit.bone("socket_muzzle", (0.29, -0.89, 1.005), recoil)
    pulse = unit.bone("fx_flash", (0.29, -0.89, 1.005), "socket_muzzle")

    # A low wedge with an offset gun and a broad, uninterrupted sensor brow.
    lower = [
        (-0.50, -1.08),
        (0.50, -1.08),
        (0.69, -0.84),
        (0.72, 0.70),
        (0.53, 0.94),
        (-0.53, 0.94),
        (-0.72, 0.70),
        (-0.69, -0.84),
    ]
    mid = [
        (-0.55, -1.18),
        (0.55, -1.18),
        (0.74, -0.94),
        (0.76, 0.76),
        (0.54, 1.00),
        (-0.54, 1.00),
        (-0.76, 0.76),
        (-0.74, -0.94),
    ]
    top = [
        (-0.36, -1.035),
        (0.36, -1.035),
        (0.58, -0.75),
        (0.65, 0.64),
        (0.49, 0.83),
        (-0.49, 0.83),
        (-0.65, 0.64),
        (-0.58, -0.75),
    ]
    unit.loft("z", [(0.19, lower), (0.32, mid), (0.67, mid)], "Frame", hull, 0.026)
    unit.loft("z", [(0.53, mid), (0.64, mid), (0.90, top)], "Ceramic", hull, 0.023)
    unit.plate(
        "y",
        -1.191,
        -1.126,
        [
            (-0.42, 0.36),
            (0.42, 0.36),
            (0.49, 0.43),
            (0.38, 0.56),
            (-0.38, 0.56),
            (-0.49, 0.43),
        ],
        "Carbon",
        hull,
        0.01,
    )
    unit.plate(
        "y",
        -1.221,
        -1.188,
        [
            (-0.33, 0.418),
            (0.33, 0.418),
            (0.40, 0.464),
            (0.30, 0.506),
            (-0.30, 0.506),
            (-0.40, 0.464),
        ],
        "Frame",
        hull,
        0.007,
    )
    unit.plate(
        "y",
        -1.228,
        -1.222,
        [
            (-0.24, 0.442),
            (0.24, 0.442),
            (0.29, 0.468),
            (0.22, 0.487),
            (-0.22, 0.487),
            (-0.29, 0.468),
        ],
        "Optics",
        hull,
    )
    for x in (-0.32, 0.32):
        unit.block(
            (x, -1.229, 0.468), (0.045, 0.01, 0.050), "SafetyAmber", hull, bevel=0.003
        )
    unit.block((0, -1.012, 0.27), (0.69, 0.29, 0.14), "Frame", hull, bevel=0.017)

    # Port-side access panel, seam and octagonal fasteners.
    unit.plate(
        "z",
        0.894,
        0.933,
        [
            (-0.45, -0.67),
            (-0.17, -0.67),
            (-0.035, -0.45),
            (-0.035, 0.48),
            (-0.17, 0.65),
            (-0.45, 0.65),
            (-0.53, 0.50),
            (-0.53, -0.46),
        ],
        "Carbon",
        hull,
        0.01,
    )
    unit.plate(
        "z",
        0.922,
        0.954,
        [
            (-0.44, -0.60),
            (-0.184, -0.60),
            (-0.07, -0.414),
            (-0.07, 0.38),
            (-0.20, 0.56),
            (-0.45, 0.56),
            (-0.50, 0.45),
            (-0.50, -0.432),
        ],
        "PlayerColor",
        hull,
        0.008,
    )
    unit.stamp((-0.304, -0.29, 0.956), 0.17, "01", "Ceramic", hull)
    unit.chip("z", 0.955, (-0.456, 0.355), 0.048, 0.36, "Frame", hull)
    unit.chip("z", 0.956, (-0.469, 0.327), 0.023, 0.43, "Frame", hull)
    unit.chip("z", 0.901, (0.253, -0.858), 0.055, 0.55, "Alloy", hull)
    unit.chip("z", 0.901, (0.215, -0.877), 0.028, 0.67, "Alloy", hull)
    unit.chip("z", 0.901, (-0.357, -0.945), 0.097, -0.18, "Alloy", hull)
    unit.chip("z", 0.901, (-0.364, -0.928), 0.046, -0.07, "Alloy", hull)
    for y in (0.105, 0.20, 0.295):
        unit.block(
            (-0.29, y, 0.958),
            (0.25, 0.039, 0.009),
            "Carbon",
            hull,
            corners=0.013,
            bevel=0.002,
            rotate=-0.19,
        )
    for x, y in (
        (-0.43, -0.47),
        (-0.44, 0.445),
        (0.45, 0.62),
        (0.36, -0.79),
        (0.02, -0.89),
    ):
        unit.round(
            (x, y, 0.899 if x > 0 else 0.950),
            (x, y, 0.917 if x > 0 else 0.963),
            0.024,
            "Alloy",
            hull,
            n=6,
        )
    unit.block((0.08, 0.729, 0.887), (0.49, 0.25, 0.083), "Carbon", hatch, bevel=0.012)
    unit.block((0.08, 0.748, 0.923), (0.405, 0.155, 0.028), "Frame", hatch, bevel=0.006)
    for index in range(4):
        unit.block(
            (-0.06 + index * 0.09, 0.758, 0.942),
            (0.035, 0.109, 0.023),
            "Alloy",
            hatch,
            corners=0.012,
            bevel=0.003,
        )
    for x in (-0.54, 0.54):
        unit.block((x, 0.857, 0.69), (0.19, 0.23, 0.17), "Carbon", hull, bevel=0.01)
        unit.plate(
            "y",
            0.971,
            0.989,
            [
                (x - 0.056, 0.648),
                (x + 0.068, 0.648),
                (x + 0.068, 0.718),
                (x - 0.034, 0.718),
                (x - 0.056, 0.70),
            ],
            "SafetyAmber",
            hull,
            0.004,
        )

    unit.round((0.29, 0.11, 0.884), (0.29, 0.11, 0.96), 0.285, "Carbon", turret, n=16)
    unit.loft(
        "z",
        [
            (
                0.942,
                [
                    (0.076, -0.22),
                    (0.52, -0.22),
                    (0.62, -0.03),
                    (0.58, 0.31),
                    (0.47, 0.44),
                    (0.12, 0.44),
                    (0.02, 0.28),
                    (0.01, -0.03),
                ],
            ),
            (
                1.12,
                [
                    (0.12, -0.20),
                    (0.48, -0.20),
                    (0.57, -0.035),
                    (0.54, 0.28),
                    (0.44, 0.38),
                    (0.15, 0.38),
                    (0.072, 0.253),
                    (0.065, -0.04),
                ],
            ),
        ],
        "Ceramic",
        turret,
        0.017,
    )
    unit.block(
        (0.298, 0.12, 1.137),
        (0.29, 0.36, 0.042),
        "PlayerColor",
        turret,
        corners=0.055,
        bevel=0.008,
    )
    unit.block(
        (0.31, 0.194, 1.164),
        (0.146, 0.074, 0.017),
        "SafetyAmber",
        turret,
        corners=0.018,
        bevel=0.004,
    )
    for x in (0.098, 0.50):
        unit.block((x, -0.13, 1.045), (0.11, 0.29, 0.16), "Frame", turret, bevel=0.012)
    unit.loft(
        "y",
        [
            (
                -0.71,
                [
                    (0.145, 0.938),
                    (0.436, 0.938),
                    (0.466, 0.975),
                    (0.466, 1.041),
                    (0.434, 1.081),
                    (0.145, 1.081),
                    (0.115, 1.041),
                    (0.115, 0.975),
                ],
            ),
            (
                -0.21,
                [
                    (0.11, 0.924),
                    (0.47, 0.924),
                    (0.501, 0.963),
                    (0.501, 1.065),
                    (0.471, 1.104),
                    (0.11, 1.104),
                    (0.080, 1.065),
                    (0.080, 0.963),
                ],
            ),
        ],
        "Frame",
        recoil,
        0.012,
    )
    unit.block(
        (0.29, -0.475, 1.09),
        (0.174, 0.34, 0.032),
        "Alloy",
        recoil,
        corners=0.035,
        bevel=0.006,
    )
    for x in (0.186, 0.394):
        unit.rail(
            (x, -0.60, 1.007), (x, -0.864, 1.007), 0.10, 0.115, "Carbon", recoil, 0.008
        )
        unit.block(
            (x, -0.785, 1.074),
            (0.072, 0.122, 0.021),
            "Ceramic",
            recoil,
            corners=0.013,
            bevel=0.004,
        )
    unit.block(
        (0.29, -0.791, 1.011), (0.098, 0.12, 0.076), "Carbon", recoil, bevel=0.007
    )
    unit.block(
        (0.29, -0.854, 1.011), (0.043, 0.006, 0.036), "SafetyAmber", recoil, bevel=0.002
    )
    flash(unit, (0.29, -0.89, 1.005), 0.102, pulse)

    unit.round((-0.43, 0.67, 0.90), (-0.43, 0.67, 0.984), 0.090, "Carbon", mast)
    unit.round(
        (-0.43, 0.67, 0.968), (-0.49, 0.801, 1.29), 0.021, "Frame", mast, tip=0.013, n=8
    )
    unit.round(
        (-0.49, 0.801, 1.272), (-0.502, 0.825, 1.328), 0.024, "SafetyAmber", mast, n=8
    )
    unit.block((-0.35, 0.69, 1.00), (0.088, 0.068, 0.07), "Ceramic", mast, bevel=0.008)

    # Two independently visible treads share the same straight-line cycle.
    for index, y in enumerate((-0.78, 0, 0.78)):
        axle = unit.bone("axle.%02d" % index, (0, y, TRACK_Z))
        for side in (-1, 1):
            x = side * 0.935
            r = 0.242 if index in (0, 2) else 0.216
            unit.round(
                (x - side * 0.155, y, TRACK_Z),
                (x + side * 0.183, y, TRACK_Z),
                r,
                "Carbon",
                axle,
            )
            unit.round(
                (x + side * 0.164, y, TRACK_Z),
                (x + side * 0.212, y, TRACK_Z),
                r * 0.82,
                "Frame",
                axle,
            )
            unit.round(
                (x + side * 0.207, y, TRACK_Z),
                (x + side * 0.222, y, TRACK_Z),
                r * 0.47,
                "Alloy",
                axle,
                n=10,
            )
            unit.round(
                (x + side * 0.220, y, TRACK_Z),
                (x + side * 0.238, y, TRACK_Z),
                r * 0.25,
                "Carbon",
                axle,
                n=8,
            )
            for i in range(5):
                a = math.tau * i / 5
                yy, zz = y + r * 0.63 * math.cos(a), TRACK_Z + r * 0.63 * math.sin(a)
                unit.round(
                    (x + side * 0.209, yy, zz),
                    (x + side * 0.226, yy, zz),
                    0.021,
                    "SafetyAmber" if i == 0 else "Alloy",
                    axle,
                    n=6,
                )
    for side in (-1, 1):
        x = side * 0.935
        unit.plate(
            "x",
            x - 0.148,
            x + 0.148,
            [(y, z + TRACK_Z) for y, z in chamfer(1.77, 0.34, 0.15)],
            "Frame",
            "root",
            0.019,
        )
        unit.loft(
            "z",
            [
                (0.607, [(x + a, b) for a, b in chamfer(0.54, 1.89, 0.145)]),
                (0.757, [(x + a, b) for a, b in chamfer(0.47, 1.67, 0.15)]),
            ],
            "Carbon",
            "root",
            0.021,
        )
        unit.plate(
            "z",
            0.742,
            0.790,
            [(x + a, b - 0.08) for a, b in chamfer(0.43, 1.34, 0.125)],
            "PlayerColor",
            "root",
            0.014,
        )
        unit.plate(
            "z",
            0.784,
            0.806,
            [(x + a, b - 0.31) for a, b in chamfer(0.277, 0.525, 0.073)],
            "Ceramic",
            "root",
            0.009,
        )
        for index in range(3):
            unit.block(
                (x, 0.198 + index * 0.095, 0.795),
                (0.242, 0.025, 0.021),
                "Frame",
                "root",
                corners=0.009,
                bevel=0.003,
                rotate=side * 0.34,
            )
        y0 = -0.717
        unit.plate(
            "x",
            x + side * 0.249,
            x + side * 0.260,
            [(y0, 0.575), (y0 + 0.22, 0.575), (y0 + 0.34, 0.655), (y0 + 0.107, 0.655)],
            "SafetyAmber",
            "root",
            0.004,
        )
        for i in range(2):
            yy = y0 + 0.104 + i * 0.092
            unit.plate(
                "x",
                x + side * 0.261,
                x + side * 0.266,
                [
                    (yy, 0.577),
                    (yy + 0.033, 0.577),
                    (yy + 0.127, 0.653),
                    (yy + 0.092, 0.653),
                ],
                "Carbon",
                "root",
            )

    for i in range(LINKS):
        y, z, angle = track_pose(i * TRACK_LENGTH / LINKS)
        bone = unit.bone("tread.%02d" % i, (0, y, z), length=0.09)
        rot = Euler((angle, 0, 0)).to_matrix()
        for side in (-1, 1):
            x = side * 0.935
            half = TRACK_LENGTH / LINKS * 0.43
            pts = [
                (-0.192, -half),
                (0.192, -half),
                (0.245, -half + 0.037),
                (0.245, half - 0.037),
                (0.192, half),
                (-0.192, half),
                (-0.245, half - 0.037),
                (-0.245, -half + 0.037),
            ]
            verts = [
                tuple(Vector((x, y, z)) + rot @ Vector((xx, yy, zz)))
                for zz in (-0.034, 0.026)
                for xx, yy in pts
            ]
            unit.shape(
                verts,
                [tuple(range(8))[::-1], tuple(range(8, 16))]
                + [(j, (j + 1) % 8, (j + 1) % 8 + 8, j + 8) for j in range(8)],
                "Carbon",
                bone,
            )
            for offset in (-0.122, 0.122):
                ridge = [
                    (offset + xx, yy)
                    for xx, yy in [
                        (-0.103, -0.041),
                        (0.103, -0.031),
                        (0.103, 0.031),
                        (-0.103, 0.041),
                    ]
                ]
                ridge = [(a, b + side * a * 0.19) for a, b in ridge]
                verts = [
                    tuple(Vector((x, y, z)) + rot @ Vector((xx, yy, zz)))
                    for zz in (0.023, 0.039)
                    for xx, yy in ridge
                ]
                unit.shape(
                    verts,
                    [(3, 2, 1, 0), (4, 5, 6, 7)]
                    + [(j, (j + 1) % 4, (j + 1) % 4 + 4, j + 4) for j in range(4)],
                    "Frame",
                    bone,
                )
    unit.make_rig()
    return unit


def pose(unit, clip, frame, t):
    rig = unit.rig
    if clip == "idle":
        set_pose(
            rig,
            "hull",
            x=0.011 * math.sin(t * math.tau),
            location=(0, 0, 0.006 * (1 - math.cos(t * math.tau))),
        )
        set_pose(rig, "turret", z=0.085 * math.sin(t * math.tau))
        set_pose(rig, "antenna", x=0.045 * math.sin(t * math.tau + 0.6))
    if clip == "move":
        set_pose(
            rig,
            "hull",
            x=0.025 * math.sin(t * math.tau),
            y=0.015 * math.sin(t * math.tau * 2),
            location=(0, 0, 0.014 + 0.012 * math.cos(t * math.tau * 2)),
        )
        set_pose(
            rig,
            "turret",
            x=0.014 * math.sin(t * math.tau * 2),
            z=0.03 * math.sin(t * math.tau),
        )
        set_pose(rig, "antenna", x=-0.13 + 0.095 * math.sin(t * math.tau * 2 + 0.6))
        for i in range(3):
            set_pose(rig, "axle.%02d" % i, x=math.tau * t)
        for i in range(LINKS):
            start = i * TRACK_LENGTH / LINKS
            traveled = start - TRACK_LENGTH / LINKS * 5 * t
            y0, z0, a0 = track_pose(start)
            y, z, a = track_pose(traveled)
            a -= math.tau * math.floor(traveled / TRACK_LENGTH)
            set_pose(rig, "tread.%02d" % i, x=a - a0, location=(0, y - y0, z - z0))
    if clip == "fire":
        jolt = tween(
            frame, [(1, 0), (3, -0.018), (4, 0.14), (7, 0.068), (11, -0.018), (20, 0)]
        )
        size = tween(frame, [(1, 1), (3, 1), (4, 428), (5, 272), (7, 1)])
        set_pose(rig, "hull", x=-0.22 * jolt, location=(0, 0, -0.16 * jolt))
        set_pose(rig, "recoil", location=(0, jolt, 0))
        set_pose(
            rig,
            "antenna",
            x=tween(frame, [(1, 0), (5, -0.19), (10, 0.08), (14, -0.03), (20, 0)]),
        )
        set_pose(rig, "fx_flash", y=0.35 * frame, scale=size)
    if clip == "destroyed":
        slump = tween(
            frame, [(1, 0), (8, -0.15), (21, 1.0), (29, 0.82), (38, 0.91), (46, 0.91)]
        )
        set_pose(
            rig,
            "hull",
            x=0.091 * slump,
            y=0.106 * slump,
            location=(0.025 * slump, 0.034 * slump, -0.014 * slump),
        )
        set_pose(rig, "turret", x=0.23 * slump, z=-0.34 * slump)
        set_pose(
            rig,
            "rear_hatch",
            x=tween(frame, [(1, 0), (7, 0), (17, -1.59), (26, -0.98), (36, -1.13)]),
        )
        set_pose(
            rig,
            "antenna",
            x=tween(frame, [(1, 0), (11, 0.35), (23, -0.9), (32, -0.68), (46, -0.73)]),
            y=0.24 * slump,
        )
