"""Rivet geometry, rig pivots, and baked animation poses."""

import math

from mathutils import Vector

from foundry import Unit, chamfer, flash, set_pose, tween


HIP = (0, 0.04, 1.39)
KNEE = (0, -0.155, 0.84)
ANKLE = (0, 0.067, 0.285)


def make_rivet():
    unit = Unit("Rivet", "Bipedal combat robot")
    pelvis = unit.bone("pelvis", HIP)
    torso = unit.bone("torso", (0, 0.075, 1.55), pelvis)
    neck = unit.bone("head", (0, -0.025, 2.18), torso)
    x_leg = 0.315

    unit.loft(
        "z",
        [
            (1.28, chamfer(0.67, 0.41, 0.076)),
            (1.38, chamfer(0.83, 0.54, 0.102)),
            (1.54, [(x, y + 0.049) for x, y in chamfer(0.63, 0.51, 0.107)]),
        ],
        "Frame",
        pelvis,
        0.022,
    )
    unit.plate(
        "y",
        -0.273,
        -0.19,
        [
            (-0.237, 1.31),
            (0.237, 1.31),
            (0.328, 1.405),
            (0.209, 1.48),
            (-0.209, 1.48),
            (-0.328, 1.405),
        ],
        "Carbon",
        pelvis,
        0.012,
    )
    unit.plate(
        "y",
        -0.293,
        -0.267,
        [
            (-0.171, 1.332),
            (0.171, 1.332),
            (0.23, 1.398),
            (0.133, 1.435),
            (-0.133, 1.435),
            (-0.23, 1.398),
        ],
        "Ceramic",
        pelvis,
        0.008,
    )
    unit.block((0, 0.044, 1.55), (0.51, 0.43, 0.20), "Carbon", torso, bevel=0.019)
    for sign in (-1, 1):
        for z in (1.503, 1.56, 1.617):
            unit.block(
                (sign * 0.223, -0.092, z),
                (0.139, 0.25, 0.037),
                "Alloy",
                torso,
                bevel=0.006,
            )

    torso_lower = [
        (-0.26, -0.19),
        (0.26, -0.19),
        (0.325, -0.087),
        (0.329, 0.259),
        (0.197, 0.335),
        (-0.197, 0.335),
        (-0.329, 0.259),
        (-0.325, -0.087),
    ]
    torso_middle = [
        (-0.345, -0.365),
        (0.345, -0.365),
        (0.535, -0.197),
        (0.493, 0.26),
        (0.259, 0.388),
        (-0.259, 0.388),
        (-0.493, 0.26),
        (-0.535, -0.197),
    ]
    torso_top = [
        (-0.277, -0.291),
        (0.277, -0.291),
        (0.442, -0.138),
        (0.432, 0.205),
        (0.253, 0.32),
        (-0.253, 0.32),
        (-0.432, 0.205),
        (-0.442, -0.138),
    ]
    unit.loft(
        "z",
        [
            (1.58, torso_lower),
            (1.86, torso_middle),
            (2.079, torso_middle),
            (2.272, torso_top),
        ],
        "Frame",
        torso,
        0.024,
    )
    shape = [
        (-0.348, 1.79),
        (0.348, 1.79),
        (0.466, 1.918),
        (0.453, 2.097),
        (0.281, 2.22),
        (-0.281, 2.22),
        (-0.453, 2.097),
        (-0.466, 1.918),
    ]
    inset = [(x * 0.88, 1.986 + (z - 1.986) * 0.87) for x, z in shape]
    unit.loft(
        "y",
        [(-0.425, inset), (-0.374, shape), (-0.253, shape)],
        "Ceramic",
        torso,
        0.015,
    )
    unit.plate(
        "y",
        -0.446,
        -0.413,
        [
            (-0.213, 1.819),
            (0.209, 1.819),
            (0.318, 1.916),
            (0.215, 1.996),
            (-0.216, 1.996),
            (-0.318, 1.916),
        ],
        "Carbon",
        torso,
        0.007,
    )
    for x in (-0.205, -0.122, -0.039, 0.044, 0.127, 0.210):
        unit.plate(
            "y",
            -0.455,
            -0.444,
            [
                (x - 0.020, 1.861),
                (x + 0.015, 1.861),
                (x + 0.048, 1.946),
                (x + 0.012, 1.946),
            ],
            "Frame",
            torso,
            0.002,
        )
    unit.stamp((0.092, -0.427, 2.077), 0.103, "02", "Carbon", torso, top=False)
    unit.chip("y", -0.426, (0.349, 2.017), 0.066, 0.90, "Alloy", torso)
    unit.chip("y", -0.426, (0.336, 2.02), 0.047, 0.82, "Alloy", torso)
    unit.chip("y", -0.426, (-0.285, 2.126), 0.037, -0.41, "Alloy", torso)
    unit.chip("z", 2.5995, (0.142, -0.178), 0.057, 0.71, "Alloy", neck)
    unit.chip("z", 2.5995, (0.131, -0.187), 0.031, 0.56, "Alloy", neck)
    for i in range(3):
        x = -0.247 + i * 0.036
        unit.plate(
            "y",
            -0.432,
            -0.425,
            [
                (x - 0.035, 2.042),
                (x - 0.014, 2.042),
                (x + 0.017, 2.106),
                (x - 0.004, 2.106),
            ],
            "SafetyAmber",
            torso,
        )
    unit.plate(
        "y",
        -0.457,
        -0.420,
        [
            (-0.139, 1.783),
            (0.139, 1.783),
            (0.191, 1.819),
            (0.147, 1.852),
            (-0.147, 1.852),
            (-0.191, 1.819),
        ],
        "Alloy",
        torso,
        0.007,
    )

    # Rear heat sinks sit between the shoulder silhouettes.
    unit.block(
        (0, 0.34, 2.009),
        (0.73, 0.30, 0.559),
        "Carbon",
        torso,
        corners=0.086,
        bevel=0.024,
    )
    for sign in (-1, 1):
        x = sign * 0.253
        unit.block(
            (x, 0.442, 2.008),
            (0.218, 0.22, 0.468),
            "Ceramic",
            torso,
            corners=0.039,
            bevel=0.015,
        )
        unit.block(
            (x, 0.561, 1.998),
            (0.157, 0.049, 0.339),
            "Frame",
            torso,
            corners=0.022,
            bevel=0.008,
        )
        for i in range(4):
            unit.block(
                (x, 0.594, 1.872 + i * 0.08),
                (0.153, 0.027, 0.032),
                "Carbon",
                torso,
                corners=0.01,
                bevel=0.003,
            )
        unit.block(
            (x, 0.469, 2.257),
            (0.118, 0.133, 0.043),
            "SafetyAmber",
            torso,
            corners=0.017,
            bevel=0.004,
        )
    unit.round((0, -0.002, 2.177), (0, -0.002, 2.312), 0.176, "Carbon", neck, n=12)
    head_bottom = [
        (-0.18, -0.251),
        (0.18, -0.251),
        (0.238, -0.176),
        (0.22, 0.106),
        (0.165, 0.171),
        (-0.165, 0.171),
        (-0.22, 0.106),
        (-0.238, -0.176),
    ]
    head_mid = [
        (-0.209, -0.322),
        (0.209, -0.322),
        (0.279, -0.209),
        (0.268, 0.12),
        (0.174, 0.206),
        (-0.174, 0.206),
        (-0.268, 0.12),
        (-0.279, -0.209),
    ]
    head_top = [
        (-0.171, -0.285),
        (0.171, -0.285),
        (0.222, -0.184),
        (0.205, 0.08),
        (0.149, 0.152),
        (-0.149, 0.152),
        (-0.205, 0.08),
        (-0.222, -0.184),
    ]
    unit.loft(
        "z",
        [(2.245, head_bottom), (2.36, head_mid), (2.486, head_mid), (2.599, head_top)],
        "Ceramic",
        neck,
        0.016,
    )
    unit.plate(
        "y",
        -0.344,
        -0.251,
        [
            (-0.224, 2.339),
            (0.224, 2.339),
            (0.265, 2.401),
            (0.207, 2.481),
            (-0.207, 2.481),
            (-0.265, 2.401),
        ],
        "Carbon",
        neck,
        0.010,
    )
    unit.plate(
        "y",
        -0.355,
        -0.340,
        [
            (-0.194, 2.374),
            (0.194, 2.374),
            (0.233, 2.408),
            (0.180, 2.443),
            (-0.180, 2.443),
            (-0.233, 2.408),
        ],
        "Frame",
        neck,
        0.005,
    )
    for sign in (-1, 1):
        unit.plate(
            "y",
            -0.361,
            -0.354,
            [
                (sign * x, z)
                for x, z in [
                    (0.024, 2.393),
                    (0.175, 2.393),
                    (0.205, 2.408),
                    (0.165, 2.427),
                    (0.024, 2.420),
                ]
            ],
            "Optics",
            neck,
        )
        unit.round(
            (sign * 0.224, -0.022, 2.409),
            (sign * 0.280, -0.022, 2.409),
            0.102,
            "Frame",
            neck,
            n=10,
        )
        unit.round(
            (sign * 0.267, -0.022, 2.409),
            (sign * 0.286, -0.022, 2.409),
            0.056,
            "SafetyAmber",
            neck,
            n=8,
        )
    unit.block(
        (0, -0.100, 2.607),
        (0.091, 0.235, 0.024),
        "SafetyAmber",
        neck,
        corners=0.025,
        bevel=0.004,
    )

    for side, sign in (("L", -1), ("R", 1)):
        hip = (sign * x_leg, *HIP[1:])
        knee = (sign * x_leg, *KNEE[1:])
        ankle = (sign * x_leg, *ANKLE[1:])
        thigh = unit.bone("thigh." + side, hip, pelvis)
        shin = unit.bone("shin." + side, knee, thigh)
        foot = unit.bone("foot." + side, ankle, shin)
        x = hip[0]
        for origin, radius, half, mat, bone in (
            (hip, 0.163, 0.13, "Carbon", thigh),
            (knee, 0.162, 0.153, "Frame", shin),
            (ankle, 0.133, 0.128, "Carbon", foot),
        ):
            _, y, z = origin
            unit.round((x - half, y, z), (x + half, y, z), radius, mat, bone)
            unit.round(
                (x + sign * (half - 0.006), y, z),
                (x + sign * (half + 0.023), y, z),
                radius * 0.58,
                "Alloy",
                bone,
                n=8,
            )
            unit.round(
                (x + sign * (half + 0.018), y, z),
                (x + sign * (half + 0.032), y, z),
                radius * 0.28,
                "Carbon",
                bone,
                n=8,
            )
        unit.rail(
            (x, 0.049, 1.34), (x, -0.157, 0.898), 0.256, 0.24, "Frame", thigh, 0.018
        )
        unit.loft(
            "z",
            [
                (0.925, [(x + a, b - 0.132) for a, b in chamfer(0.234, 0.274, 0.060)]),
                (1.09, [(x + a, b - 0.043) for a, b in chamfer(0.312, 0.315, 0.065)]),
                (1.312, [(x + a, b + 0.009) for a, b in chamfer(0.267, 0.32, 0.065)]),
            ],
            "Ceramic",
            thigh,
            0.014,
        )
        unit.rail(
            (x + sign * 0.076, 0.161, 1.312),
            (x + sign * 0.096, 0.026, 0.914),
            0.082,
            0.072,
            "Carbon",
            thigh,
            0.006,
        )
        unit.round(
            (x + sign * 0.083, 0.125, 1.232),
            (x + sign * 0.1, 0.032, 0.952),
            0.045,
            "Alloy",
            thigh,
            n=8,
        )
        unit.plate(
            "y",
            -0.34,
            -0.222,
            [
                (x + a, z)
                for a, z in [
                    (-0.119, 0.736),
                    (0.095, 0.736),
                    (0.157, 0.819),
                    (0.124, 0.927),
                    (-0.105, 0.927),
                    (-0.157, 0.849),
                ]
            ],
            "PlayerColor",
            shin,
            0.013,
        )
        unit.plate(
            "y",
            -0.35,
            -0.330,
            [
                (x + a, z)
                for a, z in [
                    (-0.053, 0.777),
                    (0.061, 0.777),
                    (0.086, 0.811),
                    (0.063, 0.849),
                    (-0.06, 0.849),
                    (-0.083, 0.807),
                ]
            ],
            "Frame",
            shin,
            0.005,
        )
        unit.loft(
            "z",
            [
                (0.242, [(x + a, b + 0.072) for a, b in chamfer(0.209, 0.226, 0.054)]),
                (0.392, [(x + a, b + 0.047) for a, b in chamfer(0.357, 0.399, 0.074)]),
                (0.721, [(x + a, b - 0.027) for a, b in chamfer(0.323, 0.387, 0.064)]),
                (0.812, [(x + a, b - 0.091) for a, b in chamfer(0.270, 0.305, 0.064)]),
            ],
            "Ceramic",
            shin,
            0.018,
        )
        unit.rail(
            (x + sign * 0.18, 0.048, 0.453),
            (x + sign * 0.159, -0.066, 0.695),
            0.045,
            0.106,
            "Frame",
            shin,
            0.007,
        )
        unit.round(
            (x + sign * 0.08, 0.162, 0.335),
            (x + sign * 0.11, 0.145, 0.667),
            0.035,
            "Frame",
            shin,
            n=8,
        )
        unit.block((x, 0.199, 0.456), (0.149, 0.104, 0.22), "Carbon", shin, bevel=0.012)

        # Wide forked toe pads and an exposed turntable at each ankle.
        unit.loft(
            "z",
            [
                (0.000, [(x + a, b - 0.061) for a, b in chamfer(0.409, 0.626, 0.083)]),
                (0.098, [(x + a, b - 0.061) for a, b in chamfer(0.434, 0.648, 0.083)]),
                (0.163, [(x + a, b - 0.035) for a, b in chamfer(0.404, 0.571, 0.083)]),
            ],
            "Carbon",
            foot,
            0.012,
        )
        unit.loft(
            "z",
            [
                (0.138, [(x + a, b + 0.045) for a, b in chamfer(0.369, 0.404, 0.07)]),
                (0.267, [(x + a, b + 0.075) for a, b in chamfer(0.260, 0.299, 0.06)]),
            ],
            "Frame",
            foot,
            0.012,
        )
        for off in (-0.115, 0.115):
            unit.loft(
                "z",
                [
                    (
                        0.102,
                        [
                            (x + off + a, b - 0.236)
                            for a, b in chamfer(0.204, 0.316, 0.042)
                        ],
                    ),
                    (
                        0.172,
                        [
                            (x + off + a, b - 0.228)
                            for a, b in chamfer(0.194, 0.303, 0.038)
                        ],
                    ),
                    (
                        0.210,
                        [
                            (x + off + a, b - 0.191)
                            for a, b in chamfer(0.173, 0.245, 0.031)
                        ],
                    ),
                ],
                "Ceramic",
                foot,
                0.008,
            )
            unit.block(
                (x + off, -0.259, 0.212),
                (0.115, 0.035, 0.008),
                "SafetyAmber",
                foot,
                corners=0.012,
                bevel=0.002,
            )
        unit.block(
            (x, 0.225, 0.157), (0.223, 0.122, 0.068), "PlayerColor", foot, bevel=0.007
        )

        shoulder = unit.bone("shoulder." + side, (sign * 0.597, 0.027, 2.059), torso)
        elbow = unit.bone("elbow." + side, (sign * 0.805, 0.028, 1.633), shoulder)
        unit.round(
            (sign * 0.419, 0.027, 2.050),
            (sign * 0.789, 0.027, 2.05),
            0.177,
            "Frame",
            shoulder,
            n=12,
        )
        unit.rail(
            (sign * 0.67, 0.019, 2.071),
            (sign * 0.81, 0.035, 1.631),
            0.252,
            0.25,
            "Frame",
            shoulder,
            0.014,
        )
        unit.round(
            (sign * 0.684, 0.034, 1.633),
            (sign * 0.948, 0.034, 1.633),
            0.147,
            "Carbon",
            elbow,
            n=12,
        )
        unit.round(
            (sign * 0.941, 0.034, 1.633),
            (sign * 0.978, 0.034, 1.633),
            0.091,
            "Alloy",
            elbow,
            n=10,
        )
        unit.round(
            (sign * 0.971, 0.034, 1.633),
            (sign * 0.989, 0.034, 1.633),
            0.045,
            "Carbon",
            elbow,
            n=8,
        )
        shoulder_low = [
            (sign * x, y)
            for x, y in [
                (0.479, -0.25),
                (0.843, -0.305),
                (1.002, -0.177),
                (1.013, 0.151),
                (0.928, 0.297),
                (0.574, 0.264),
                (0.436, 0.126),
                (0.437, -0.14),
            ]
        ]
        shoulder_top = [
            (sign * x, y)
            for x, y in [
                (0.533, -0.224),
                (0.811, -0.259),
                (0.949, -0.135),
                (0.931, 0.127),
                (0.852, 0.234),
                (0.601, 0.215),
                (0.500, 0.106),
                (0.502, -0.108),
            ]
        ]
        unit.loft(
            "z",
            [(1.922, shoulder_low), (2.098, shoulder_low), (2.291, shoulder_top)],
            "PlayerColor",
            shoulder,
            0.019,
        )
        shoulder_cap = [
            (sign * x, y)
            for x, y in [
                (0.588, -0.160),
                (0.780, -0.192),
                (0.881, -0.107),
                (0.865, 0.081),
                (0.790, 0.166),
                (0.605, 0.158),
                (0.55, 0.065),
                (0.55, -0.082),
            ]
        ]
        unit.plate("z", 2.288, 2.322, shoulder_cap, "Ceramic", shoulder, 0.009)
        for i in range(3):
            x = sign * (0.645 + i * 0.066)
            unit.block(
                (x, 0.023, 2.325),
                (0.025, 0.154, 0.011),
                "Frame",
                shoulder,
                corners=0.009,
                bevel=0.002,
                rotate=sign * 0.23,
            )
        unit.plate(
            "y",
            -0.289,
            -0.232,
            [
                (sign * x, z)
                for x, z in [
                    (0.548, 2.007),
                    (0.761, 1.995),
                    (0.843, 2.056),
                    (0.789, 2.131),
                    (0.578, 2.131),
                ]
            ],
            "Carbon",
            shoulder,
            0.008,
        )
        unit.plate(
            "y",
            -0.293,
            -0.288,
            [
                (sign * x, z)
                for x, z in [
                    (0.592, 2.043),
                    (0.736, 2.032),
                    (0.774, 2.054),
                    (0.719, 2.084),
                    (0.592, 2.088),
                ]
            ],
            "SafetyAmber",
            shoulder,
            0.003,
        )

        if side == "L":
            claw = unit.bone("claw.L", (-0.849, -0.18, 1.336), elbow)
            unit.rail(
                (-0.812, 0.024, 1.617),
                (-0.847, -0.172, 1.374),
                0.29,
                0.258,
                "Frame",
                elbow,
                0.012,
            )
            unit.loft(
                "z",
                [
                    (
                        1.376,
                        [
                            (-0.846 + a, b - 0.141)
                            for a, b in chamfer(0.275, 0.28, 0.059)
                        ],
                    ),
                    (
                        1.55,
                        [
                            (-0.838 + a, b - 0.092)
                            for a, b in chamfer(0.35, 0.335, 0.072)
                        ],
                    ),
                    (
                        1.651,
                        [
                            (-0.826 + a, b - 0.058)
                            for a, b in chamfer(0.281, 0.26, 0.060)
                        ],
                    ),
                ],
                "Ceramic",
                elbow,
                0.016,
            )
            unit.block(
                (-0.85, -0.173, 1.294),
                (0.211, 0.168, 0.138),
                "Carbon",
                claw,
                bevel=0.012,
            )
            for x in (-0.914, -0.834, -0.754):
                unit.rail(
                    (x, -0.194, 1.296),
                    (x, -0.237, 1.178),
                    0.049,
                    0.061,
                    "Alloy",
                    claw,
                    0.003,
                )
                unit.rail(
                    (x, -0.241, 1.185),
                    (x, -0.306, 1.20),
                    0.049,
                    0.048,
                    "Frame",
                    claw,
                    0.003,
                )
            unit.rail(
                (-0.742, -0.130, 1.309),
                (-0.685, -0.187, 1.228),
                0.057,
                0.062,
                "Frame",
                claw,
                0.004,
            )
        else:
            recoil = unit.bone("recoil", (0.832, -0.141, 1.61), elbow)
            socket = unit.bone("socket_muzzle", (0.831, -0.940, 1.612), recoil)
            pulse = unit.bone("fx_flash", (0.831, -0.940, 1.612), socket)
            unit.block(
                (0.816, -0.058, 1.583),
                (0.373, 0.370, 0.313),
                "Ceramic",
                elbow,
                corners=0.07,
                bevel=0.017,
            )
            rear = [(a + 0.831, b + 1.614) for a, b in chamfer(0.339, 0.310, 0.078)]
            front = [(a + 0.831, b + 1.614) for a, b in chamfer(0.286, 0.226, 0.053)]
            unit.loft(
                "y",
                [(-0.880, front), (-0.727, front), (-0.495, rear), (-0.168, rear)],
                "Frame",
                recoil,
                0.014,
            )
            unit.block(
                (0.831, -0.487, 1.780),
                (0.266, 0.559, 0.097),
                "PlayerColor",
                recoil,
                corners=0.069,
                bevel=0.012,
            )
            unit.block(
                (0.831, -0.540, 1.829),
                (0.104, 0.29, 0.013),
                "Carbon",
                recoil,
                corners=0.018,
                bevel=0.003,
            )
            for x in (0.741, 0.921):
                unit.rail(
                    (x, -0.662, 1.615),
                    (x, -0.935, 1.615),
                    0.115,
                    0.132,
                    "Carbon",
                    recoil,
                    0.008,
                )
                unit.block(
                    (x, -0.822, 1.691),
                    (0.072, 0.152, 0.023),
                    "Alloy",
                    recoil,
                    corners=0.015,
                    bevel=0.004,
                )
            unit.block(
                (0.831, -0.879, 1.614),
                (0.117, 0.104, 0.085),
                "Carbon",
                recoil,
                bevel=0.006,
            )
            unit.block(
                (0.831, -0.934, 1.614),
                (0.056, 0.009, 0.038),
                "SafetyAmber",
                recoil,
                bevel=0.002,
            )
            for i in range(3):
                unit.block(
                    (1.003, -0.291 - i * 0.074, 1.649),
                    (0.018, 0.042, 0.115),
                    "SafetyAmber",
                    recoil,
                    corners=0.006,
                    bevel=0.002,
                )
            flash(unit, (0.831, -0.940, 1.612), 0.138, pulse)

    unit.make_rig()
    return unit


def leg_pose(rig, side, pelvis, ankle_y, ankle_z, pitch):
    # Solve the hinge in the sagittal plane and bake it into the three bone transforms.
    hip = Vector((HIP[1] + pelvis[1], HIP[2] + pelvis[2]))
    target = Vector((ankle_y, ankle_z))
    upper_rest = Vector((KNEE[1] - HIP[1], KNEE[2] - HIP[2]))
    lower_rest = Vector((ANKLE[1] - KNEE[1], ANKLE[2] - KNEE[2]))
    reach = target - hip
    distance = min(reach.length, upper_rest.length + lower_rest.length - 0.0002)
    direction = reach.normalized()
    across = Vector((direction[1], -direction[0]))
    along = (
        upper_rest.length_squared - lower_rest.length_squared + distance * distance
    ) / (2 * distance)
    upper = direction * along + across * math.sqrt(
        max(0, upper_rest.length_squared - along * along)
    )
    lower = direction * distance - upper

    def angle(v):
        return math.atan2(v[1], v[0])

    thigh = angle(upper) - angle(upper_rest)
    shin = angle(lower) - angle(lower_rest) - thigh
    set_pose(rig, "thigh." + side, x=thigh)
    set_pose(rig, "shin." + side, x=shin)
    set_pose(rig, "foot." + side, x=pitch - thigh - shin)


def pose(unit, clip, frame, t):
    rig = unit.rig
    wave = t * math.tau
    if clip == "idle":
        pelvis = (0, 0, -0.018 * (1 - math.cos(wave)))
        set_pose(rig, "pelvis", location=pelvis)
        set_pose(rig, "torso", x=0.017 * math.sin(wave), z=0.02 * math.sin(wave))
        set_pose(rig, "head", x=0.032 * math.sin(wave * 2), z=0.17 * math.sin(wave))
        set_pose(rig, "shoulder.L", x=-0.034 * math.sin(wave + 0.55))
        set_pose(rig, "shoulder.R", x=0.029 * math.sin(wave + 0.55))
        for side in ("L", "R"):
            leg_pose(rig, side, pelvis, ANKLE[1], ANKLE[2], 0)
    if clip == "move":
        pelvis = (0, 0.013 * math.sin(wave * 2), -0.071 + 0.025 * math.cos(wave * 2))
        set_pose(rig, "pelvis", location=pelvis)
        set_pose(
            rig,
            "torso",
            x=0.072 + 0.028 * math.sin(wave * 2),
            y=0.062 * math.cos(wave),
            z=-0.095 * math.sin(wave),
        )
        set_pose(
            rig,
            "head",
            x=-0.05 - 0.014 * math.sin(wave * 2),
            y=-0.042 * math.cos(wave),
            z=0.054 * math.sin(wave),
        )
        for side, offset in (("L", 0), ("R", 0.5)):
            phase = (t + offset) % 1
            if phase < 0.56:
                y = -0.31 + 0.62 * phase / 0.56
                lift = pitch = 0
            else:
                swing = (phase - 0.56) / 0.44
                y = 0.31 - 0.62 * (swing * swing * (3 - 2 * swing))
                lift = 0.236 * math.sin(swing * math.pi) ** 1.3
                pitch = -0.38 * math.sin(math.tau * swing) * math.sin(math.pi * swing)
            leg_pose(rig, side, pelvis, ANKLE[1] + y, ANKLE[2] + lift, pitch)
            arm = math.sin(math.tau * (phase - 0.26))
            set_pose(
                rig,
                "shoulder." + side,
                x=arm * (0.22 if side == "L" else 0.12),
                y=(0.11 if side == "L" else -0.06),
            )
            set_pose(rig, "elbow." + side, x=-0.085 + arm * 0.035)
        set_pose(rig, "claw.L", x=0.13 * math.sin(wave + 0.4))
    if clip == "fire":
        brace = tween(frame, [(1, 0), (4, 1), (11, 0.77), (20, 0)])
        kick = tween(
            frame, [(1, 0), (4, -0.022), (5, 0.167), (7, 0.105), (12, -0.018), (20, 0)]
        )
        size = tween(frame, [(1, 1), (4, 1), (5, 476), (6, 268), (8, 1)])
        pelvis = (0, 0.038 * brace, -0.056 * brace)
        set_pose(rig, "pelvis", location=pelvis)
        set_pose(
            rig, "torso", x=0.04 * brace - 1.02 * kick, z=-0.074 * brace + kick * 0.53
        )
        set_pose(rig, "head", x=-0.06 * brace + kick * 0.61, z=0.085 * brace)
        set_pose(rig, "shoulder.R", x=-0.112 * brace + kick * 0.9)
        set_pose(rig, "elbow.R", x=-0.038 * brace)
        set_pose(rig, "shoulder.L", x=0.13 * brace)
        set_pose(rig, "recoil", location=(0, kick, 0))
        set_pose(rig, "fx_flash", y=frame * 0.43, scale=size)
        for side in ("L", "R"):
            leg_pose(rig, side, pelvis, ANKLE[1], ANKLE[2], 0)
    if clip == "destroyed":
        drop = tween(frame, [(1, 0), (9, 0.11), (27, 1), (34, 0.91), (46, 0.96)])
        skid = tween(frame, [(1, 0), (11, 0), (20, 1), (46, 1)])
        pelvis = (0, -0.11 * drop, -0.595 * drop)
        set_pose(rig, "pelvis", location=pelvis)
        set_pose(rig, "torso", x=0.97 * drop, y=-0.12 * drop, z=0.15 * drop)
        set_pose(rig, "head", x=0.20 * drop, y=-0.24 * drop, z=-0.27 * drop)
        set_pose(rig, "shoulder.L", x=-0.56 * drop, y=0.31 * drop)
        set_pose(rig, "elbow.L", x=-0.24 * drop)
        set_pose(rig, "claw.L", x=0.39 * drop)
        set_pose(rig, "shoulder.R", x=-0.38 * drop, y=-0.10 * drop)
        set_pose(rig, "elbow.R", x=0.06 * drop)
        leg_pose(rig, "L", pelvis, ANKLE[1] - 0.26 * skid, ANKLE[2], 0)
        leg_pose(
            rig,
            "R",
            pelvis,
            ANKLE[1] + 0.36 * skid,
            ANKLE[2] + 0.164 * drop,
            0.38 * drop,
        )
