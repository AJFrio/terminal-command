"""Kiln production building for the Foundry roster."""

import math


from foundry import Unit, chamfer, set_pose, tween


CLIPS = (("idle", 61, 1), ("produce", 91, 1), ("deploy", 133, 1), ("destroyed", 61, 1))
DECK_Z = 0.22
RAMP_START = -5.20
RAMP_TOP = -3.47
GATE_TRAVEL = 1.87
GATE_OPEN_FRAME = 25
GATE_CLOSE_FRAME = 107
SPAWN = (0, -1.20, DECK_Z)
EXIT = (0, -5.48, 0)


def deck_and_bay(unit):
    """Prepare a continuous floor from the fabrication bay to the terrain."""
    outline = chamfer(8.62, 7.32, 0.52)
    brim = [(x, y + 0.19) for x, y in outline]
    foot = [(x * 0.96, y + 0.19) for x, y in outline]
    unit.loft("z", [(0, foot), (0.12, brim), (DECK_Z, brim)], "Carbon", "root", 0.028)
    unit.plate("z", 0.12, DECK_Z, chamfer(7.92, 6.53, 0.47), "Frame", "root")
    unit.plate(
        "x",
        -1.76,
        1.76,
        [(RAMP_START, 0), (RAMP_TOP, 0), (RAMP_TOP, DECK_Z)],
        "Frame",
        "root",
    )
    for side in (-1, 1):
        # The low curbs keep the traversable lane clear for both mobile units.
        unit.plate(
            "x",
            min(side * 1.63, side * 1.81),
            max(side * 1.63, side * 1.81),
            [
                (RAMP_START + 0.03, 0),
                (RAMP_TOP + 0.03, DECK_Z - 0.04),
                (RAMP_TOP + 0.03, DECK_Z + 0.08),
                (RAMP_START + 0.17, 0.027),
            ],
            "Alloy",
            "root",
        )
        for index in range(5):
            y = RAMP_START + 0.30 + index * 0.26
            x = side * 1.40
            points = [
                (px, py, DECK_Z * (py - RAMP_START) / (RAMP_TOP - RAMP_START) + 0.005)
                for px, py in (
                    (x - 0.10, y),
                    (x + 0.073, y + 0.046),
                    (x + 0.073, y + 0.139),
                    (x - 0.10, y + 0.09),
                )
            ]
            unit.shape(points, [(0, 1, 2, 3)], "SafetyAmber", "root")
    for y in (-3.38, -2.83, -2.08, -1.30, -0.51, 0.28, 1.06, 1.84):
        unit.block(
            (0, y, DECK_Z + 0.007), (2.64, 0.024, 0.012), "Carbon", "root", bevel=0
        )
    for x in (-1.46, 1.46):
        unit.block(
            (x, -0.46, DECK_Z + 0.01), (0.045, 5.67, 0.017), "Alloy", "root", bevel=0
        )
        for y in (-2.44, -0.68, 1.10):
            unit.block(
                (x, y, DECK_Z + 0.020), (0.11, 0.38, 0.018), "Optics", "root", bevel=0
            )
    unit.block(
        (0, 3.04, 1.80), (3.98, 1.10, 3.26), "Carbon", "root", corners=0.28, bevel=0.045
    )
    unit.block(
        (0, 2.478, 1.78),
        (2.90, 0.18, 2.53),
        "Frame",
        "root",
        corners=0.075,
        bevel=0.045,
    )
    for x in (-1.16, -0.58, 0, 0.58, 1.16):
        unit.block((x, 2.36, 1.94), (0.11, 0.097, 1.81), "Alloy", "root", bevel=0.017)
    for x in (-1.32, 1.32):
        unit.rail((x, 2.30, 2.67), (x, 2.30, 3.10), 0.075, 0.06, "Optics", "root", 0)


def wing(unit, side):
    """Build a tapered side bay and its layered roof."""
    suffix = "L" if side < 0 else "R"
    shell = unit.bone("wing." + suffix, (side * 2.56, 0.15, 0.36), length=0.29)
    x = side * 2.95

    def profile(width, depth, corner, x_shift=0.0, y=0.13):
        return [
            (x + side * x_shift + dx, y + dy)
            for dx, dy in chamfer(width, depth, corner)
        ]

    unit.loft(
        "z",
        [
            (0.21, profile(2.32, 6.66, 0.43)),
            (0.56, profile(2.37, 6.70, 0.43)),
            (1.16, profile(2.10, 6.22, 0.40, -0.07)),
        ],
        "Frame",
        "root",
        0.05,
    )
    unit.loft(
        "z",
        [
            (0.59, profile(2.23, 6.40, 0.47)),
            (1.20, profile(2.47, 6.60, 0.57, 0.01)),
            (2.76, profile(2.32, 6.38, 0.57, -0.07)),
            (3.71, profile(2.10, 5.70, 0.51, -0.16, 0.36)),
            (4.25, profile(1.96, 5.16, 0.44, -0.26, 0.45)),
        ],
        "Ceramic",
        shell,
        0.060,
    )
    unit.loft(
        "z",
        [
            (4.205, profile(2.02, 5.10, 0.44, -0.26, 0.45)),
            (4.33, profile(2.00, 5.11, 0.42, -0.26, 0.45)),
            (4.46, profile(1.85, 4.93, 0.38, -0.26, 0.45)),
        ],
        "Carbon",
        shell,
        0.034,
    )

    # Teal panels stay visible at the overhead camera angle.
    unit.loft(
        "z",
        [
            (4.445, profile(1.74, 4.02, 0.55, -0.25, 0.17)),
            (4.57, profile(1.62, 3.93, 0.52, -0.25, 0.17)),
        ],
        "PlayerColor",
        shell,
        0.028,
    )
    unit.block(
        (x - side * 0.25, -1.10, 4.602),
        (1.06, 1.17, 0.099),
        "Ceramic",
        shell,
        corners=0.22,
        bevel=0.025,
    )
    if side > 0:
        unit.stamp((x - 0.24, -1.09, 4.655), 0.62, "03", "Carbon", shell)
        unit.chip("z", 4.654, (x + 0.05, -1.39), 0.21, 0.61, "Alloy", shell)
        unit.chip("z", 4.572, (x - 0.79, -0.36), 0.25, 0.89, "Frame", shell)
    else:
        for i in range(3):
            unit.block(
                (x + 0.03, -1.39 + 0.27 * i, 4.656),
                (0.71, 0.125, 0.027),
                "Frame",
                shell,
                corners=0.055,
                bevel=0.009,
                rotate=-0.21,
            )
        unit.chip("z", 4.573, (x + 0.66, -0.41), 0.30, -0.92, "Frame", shell)
    for y in (-1.47, 1.53):
        unit.round(
            (x + side * 0.31, y, 4.532),
            (x + side * 0.31, y, 4.599),
            0.099,
            "Alloy",
            shell,
            n=8,
        )

    # Broad inset radiator on each outside wall, behind a beveled louver frame.
    grille = [
        (-0.80, 1.46),
        (1.95, 1.46),
        (2.24, 1.77),
        (2.13, 2.48),
        (1.75, 2.80),
        (-0.75, 2.80),
        (-1.12, 2.44),
        (-1.15, 1.78),
    ]
    unit.plate("x", side * 3.95, side * 4.106, grille, "Carbon", shell, 0.047)
    for i in range(6):
        y = -0.66 + i * 0.465
        unit.plate(
            "x",
            side * 4.092,
            side * 4.147,
            [(y - 0.17, 1.62), (y + 0.06, 1.62), (y + 0.37, 2.59), (y + 0.13, 2.59)],
            "Frame",
            shell,
            0.016,
        )
    unit.block(
        (side * 4.079, 0.37, 1.54),
        (0.165, 2.22, 0.100),
        "SafetyAmber",
        shell,
        corners=0.03,
        bevel=0.012,
    )
    unit.round(
        (side * 4.018, -2.63, 0.99),
        (side * 4.018, -0.71, 0.99),
        0.102,
        "Frame",
        shell,
        n=10,
    )
    for y in (-2.48, -1.03):
        unit.round(
            (side * 4.018, y - 0.069, 0.99),
            (side * 4.018, y + 0.069, 0.99),
            0.147,
            "Alloy",
            shell,
            n=10,
        )

    # Keep the service covers behind the shutters' travel across the facade.
    y = -2.81
    unit.loft(
        "y",
        [
            (
                y - 0.28,
                [
                    (side * px, z)
                    for px, z in [
                        (2.28, 0.76),
                        (3.43, 0.76),
                        (3.74, 1.08),
                        (3.60, 1.81),
                        (3.26, 2.13),
                        (2.39, 2.13),
                        (2.16, 1.86),
                        (2.15, 0.97),
                    ]
                ],
            ),
            (
                y + 0.05,
                [
                    (side * px, z)
                    for px, z in [
                        (2.21, 0.69),
                        (3.47, 0.69),
                        (3.80, 1.07),
                        (3.67, 1.89),
                        (3.31, 2.25),
                        (2.29, 2.25),
                        (2.08, 1.86),
                        (2.07, 0.96),
                    ]
                ],
            ),
        ],
        "Frame",
        shell,
        0.044,
    )
    unit.block(
        (side * 2.92, y - 0.307, 1.43),
        (0.98, 0.089, 0.48),
        "Carbon",
        shell,
        bevel=0.024,
    )
    unit.block(
        (side * 2.92, y - 0.353, 1.46),
        (0.67, 0.035, 0.116),
        "Optics",
        shell,
        corners=0.019,
        bevel=0,
    )
    for dx in (-0.43, 0.43):
        unit.round(
            (side * 2.92 + dx, y - 0.36, 1.12),
            (side * 2.92 + dx, y - 0.29, 1.12),
            0.060,
            "Alloy",
            shell,
            n=8,
        )

    for at_y in (-2.15, -0.41, 1.33):
        unit.block(
            (side * 1.75, at_y, 2.77),
            (0.10, 0.66, 0.16),
            "Frame",
            shell,
            corners=0.025,
            bevel=0.01,
        )
        unit.block(
            (side * 1.69, at_y, 2.77),
            (0.054, 0.45, 0.068),
            "Optics",
            shell,
            corners=0.012,
            bevel=0,
        )
    return shell


def gate_and_lintel(unit):
    lintel = unit.bone("lintel", (0, -2.14, 4.07), length=0.32)
    unit.loft(
        "z",
        [
            (3.48, [(x, y - 2.63) for x, y in chamfer(4.36, 1.50, 0.31)]),
            (3.82, [(x, y - 2.70) for x, y in chamfer(4.36, 1.63, 0.31)]),
            (4.47, [(x, y - 2.57) for x, y in chamfer(3.90, 1.55, 0.28)]),
            (4.66, [(x, y - 2.45) for x, y in chamfer(3.48, 1.17, 0.24)]),
        ],
        "Ceramic",
        lintel,
        0.055,
    )
    band = [
        (-1.56, 3.69),
        (1.56, 3.69),
        (1.76, 3.86),
        (1.56, 4.10),
        (-1.56, 4.10),
        (-1.76, 3.86),
    ]
    unit.plate("y", -3.532, -3.36, band, "Carbon", lintel, 0.028)
    unit.block(
        (0, -3.554, 3.89), (2.40, 0.05, 0.22), "PlayerColor", lintel, bevel=0.015
    )
    for x in (-0.85, -0.44, 0, 0.44, 0.85):
        unit.block(
            (x, -3.583, 3.891),
            (0.258, 0.023, 0.088),
            "Optics",
            lintel,
            corners=0.025,
            bevel=0,
        )
    for sign in (-1, 1):
        unit.plate(
            "y",
            -3.56,
            -3.48,
            [
                (sign * x, z)
                for x, z in [
                    (1.32, 3.78),
                    (1.54, 3.78),
                    (1.63, 3.89),
                    (1.54, 3.98),
                    (1.32, 3.98),
                ]
            ],
            "SafetyAmber",
            lintel,
            0.013,
        )
    unit.plate(
        "z",
        4.643,
        4.71,
        [(x, y - 2.43) for x, y in chamfer(2.21, 0.67, 0.20)],
        "Frame",
        lintel,
        0.021,
    )
    for x in (-0.65, -0.22, 0.22, 0.65):
        unit.block(
            (x, -2.39, 4.722),
            (0.20, 0.27, 0.033),
            "Alloy",
            lintel,
            corners=0.048,
            bevel=0,
        )

    for side, suffix in ((-1, "L"), (1, "R")):
        x = side * 1.91
        unit.plate(
            "y",
            -3.46,
            -2.68,
            [
                (side * px, z)
                for px, z in [
                    (1.70, 0.22),
                    (2.08, 0.22),
                    (2.23, 0.53),
                    (2.13, 3.51),
                    (1.97, 3.68),
                    (1.70, 3.53),
                ]
            ],
            "Carbon",
            "root",
            0.034,
        )
        unit.block(
            (x, -3.465, 2.11),
            (0.13, 0.064, 2.14),
            "Alloy",
            "root",
            corners=0.031,
            bevel=0.014,
        )
        unit.block(
            (x, -3.507, 2.46),
            (0.058, 0.029, 1.18),
            "SafetyAmber",
            "root",
            corners=0.02,
            bevel=0,
        )
        unit.block(
            (x, -3.509, 3.16),
            (0.061, 0.026, 0.143),
            "Optics",
            "root",
            corners=0.017,
            bevel=0,
        )
        gate = unit.bone("shutter." + suffix, (side * 0.91, -3.15, 1.86), length=0.24)
        side_outline = [
            (0.035, 0.24),
            (1.68, 0.24),
            (1.79, 0.40),
            (1.79, 3.23),
            (1.61, 3.51),
            (0.13, 3.51),
            (0.035, 3.39),
        ]
        unit.plate(
            "y",
            -3.225,
            -2.89,
            [(side * px, z) for px, z in side_outline],
            "Carbon",
            gate,
            0.022,
        )
        unit.plate(
            "y",
            -3.285,
            -3.205,
            [
                (side * px, z)
                for px, z in [
                    (0.08, 0.41),
                    (1.53, 0.41),
                    (1.68, 0.61),
                    (1.68, 3.04),
                    (1.50, 3.28),
                    (0.09, 3.28),
                    (0.08, 3.19),
                ]
            ],
            "Frame",
            gate,
            0.024,
        )
        for index in range(5):
            z = 0.60 + index * 0.43
            unit.plate(
                "y",
                -3.325,
                -3.28,
                [
                    (side * px, zz)
                    for px, zz in [
                        (0.128, z),
                        (1.51, z + 0.058),
                        (1.64, z + 0.16),
                        (1.64, z + 0.269),
                        (0.128, z + 0.252),
                    ]
                ],
                "Alloy",
                gate,
                0.010,
            )
        unit.plate(
            "y",
            -3.352,
            -3.316,
            [
                (side * px, z)
                for px, z in [
                    (0.14, 1.06),
                    (0.46, 1.32),
                    (0.46, 2.38),
                    (0.14, 2.67),
                    (0.14, 2.37),
                    (0.28, 2.21),
                    (0.28, 1.51),
                    (0.14, 1.39),
                ]
            ],
            "SafetyAmber",
            gate,
            0.012,
        )
        unit.block(
            (side * 0.89, -3.333, 0.51),
            (1.31, 0.06, 0.11),
            "Carbon",
            gate,
            corners=0.026,
            bevel=0.009,
        )


def fabrication_line(unit):
    # The roof well makes carriage movement legible even with the gate closed.
    for x in (-1.39, 1.39):
        unit.block(
            (x, 0.16, 3.68),
            (0.71, 4.45, 0.42),
            "Carbon",
            "root",
            corners=0.17,
            bevel=0.040,
        )
        unit.block(
            (x, 0.13, 3.917),
            (0.33, 4.03, 0.14),
            "Alloy",
            "root",
            corners=0.058,
            bevel=0.021,
        )
        unit.block(
            (x, 0.13, 4.009),
            (0.075, 3.87, 0.053),
            "SafetyAmber",
            "root",
            corners=0.017,
            bevel=0.010,
        )
        for y in (-1.48, 0.03, 1.51):
            unit.block(
                (x + 0.19, y, 3.864),
                (0.23, 0.33, 0.15),
                "Frame",
                "root",
                corners=0.043,
                bevel=0.015,
            )
    unit.loft(
        "z",
        [
            (3.31, [(x, y + 2.74) for x, y in chamfer(3.95, 1.69, 0.31)]),
            (3.96, [(x, y + 2.76) for x, y in chamfer(3.90, 1.78, 0.33)]),
            (4.33, [(x, y + 2.75) for x, y in chamfer(3.47, 1.56, 0.32)]),
        ],
        "Ceramic",
        "root",
        0.056,
    )
    unit.block(
        (0, 2.68, 4.364), (1.89, 0.84, 0.11), "Frame", "root", corners=0.24, bevel=0.026
    )
    for x in (-0.47, 0.47):
        unit.block(
            (x, 2.66, 4.434),
            (0.67, 0.56, 0.061),
            "PlayerColor",
            "root",
            corners=0.094,
            bevel=0.016,
        )
        for index in range(3):
            unit.block(
                (x, 2.49 + 0.14 * index, 4.478),
                (0.39, 0.050, 0.027),
                "Carbon",
                "root",
                corners=0.019,
                bevel=0,
            )

    carriage = unit.bone("carriage", (0, 1.04, 4.10), length=0.34)
    unit.block(
        (0, 1.04, 4.203),
        (3.13, 0.92, 0.34),
        "Frame",
        carriage,
        corners=0.19,
        bevel=0.044,
    )
    unit.loft(
        "z",
        [
            (4.30, [(x, y + 1.04) for x, y in chamfer(2.03, 1.37, 0.27)]),
            (4.53, [(x, y + 1.04) for x, y in chamfer(1.98, 1.26, 0.24)]),
            (4.82, [(x, y + 1.11) for x, y in chamfer(1.61, 1.09, 0.26)]),
        ],
        "Ceramic",
        carriage,
        0.041,
    )
    unit.block(
        (0, 1.15, 4.847),
        (1.22, 0.73, 0.095),
        "PlayerColor",
        carriage,
        corners=0.20,
        bevel=0.023,
    )
    unit.block(
        (0, 1.15, 4.91),
        (0.66, 0.37, 0.043),
        "Carbon",
        carriage,
        corners=0.082,
        bevel=0.012,
    )
    for x in (-1.31, 1.31):
        unit.block(
            (x, 1.04, 4.15),
            (0.54, 0.95, 0.29),
            "Carbon",
            carriage,
            corners=0.117,
            bevel=0.033,
        )
        unit.block(
            (x, 0.66, 4.30),
            (0.39, 0.23, 0.107),
            "SafetyAmber",
            carriage,
            corners=0.044,
            bevel=0.019,
        )
    for i in range(3):
        unit.block(
            (-0.47 + 0.47 * i, 0.337, 4.407),
            (0.268, 0.049, 0.117),
            "SafetyAmber",
            carriage,
            corners=0.033,
            bevel=0.009,
        )

    press = unit.bone("press", (0, 1.04, 3.75), carriage, length=0.21)
    unit.round((0, 1.04, 3.53), (0, 1.04, 4.10), 0.33, "Alloy", press, n=12)
    unit.block(
        (0, 1.04, 3.43), (1.05, 0.83, 0.26), "Carbon", press, corners=0.16, bevel=0.030
    )
    unit.block(
        (0, 1.04, 3.286),
        (0.71, 0.55, 0.064),
        "SafetyAmber",
        press,
        corners=0.11,
        bevel=0.015,
    )

    light = unit.bone("process_light", (0, 1.15, 4.948), carriage)
    unit.block(
        (0, 1.15, 4.948),
        (0.004, 0.0018, 0.0006),
        "Pulse",
        light,
        corners=0.0003,
        bevel=0,
    )
    unit.bone("socket_fabrication", (0, 1.04, 3.25), press)


def exhaust(unit, left, right):
    stack = unit.bone("exhaust", (-2.70, 1.83, 4.54), left, length=0.22)
    for index, (x, y, top) in enumerate(((-2.99, 1.78, 5.79), (-2.35, 2.15, 5.41))):
        unit.round(
            (x, y, 4.45), (x, y, 4.76), 0.368 - 0.06 * index, "Carbon", stack, n=10
        )
        unit.round(
            (x, y, 4.59),
            (x, y, top - 0.16),
            0.270 - 0.036 * index,
            "Alloy",
            stack,
            n=10,
        )
        unit.round(
            (x, y, top - 0.36),
            (x, y, top - 0.19),
            0.318 - 0.052 * index,
            "SafetyAmber",
            stack,
            n=10,
        )
        unit.round(
            (x, y, top - 0.22), (x, y, top), 0.32 - 0.044 * index, "Frame", stack, n=12
        )
        unit.round(
            (x, y, top - 0.016),
            (x, y, top + 0.005),
            0.215 - 0.025 * index,
            "Carbon",
            stack,
            n=10,
        )
        unit.round(
            (x, y, top + 0.005),
            (x, y, top + 0.010),
            0.123 - 0.010 * index,
            "Alloy",
            stack,
            n=10,
        )
        for sign in (-1, 1):
            unit.plate(
                "x",
                x + sign * 0.169,
                x + sign * 0.242,
                [
                    (y - 0.135, 4.68),
                    (y + 0.135, 4.68),
                    (y + 0.072, top - 0.39),
                    (y - 0.072, top - 0.39),
                ],
                "Frame",
                stack,
                0.014,
            )

    x, y = 2.67, 1.94
    unit.round((x, y, 4.49), (x, y, 4.747), 0.744, "Carbon", right, n=16)
    unit.round((x, y, 4.73), (x, y, 4.803), 0.678, "Frame", right, n=16)
    unit.round((x, y, 4.799), (x, y, 4.829), 0.591, "Carbon", right, n=16)
    rotor = unit.bone("fan", (x, y, 4.85), right, length=0.22)
    blade = [
        (0.15, -0.046),
        (0.49, -0.136),
        (0.558, -0.051),
        (0.497, 0.101),
        (0.231, 0.145),
        (0.126, 0.067),
    ]
    for index in range(6):
        angle = index * math.tau / 6
        cos, sin = math.cos(angle), math.sin(angle)
        unit.plate(
            "z",
            4.836,
            4.899,
            [(x + px * cos - py * sin, y + px * sin + py * cos) for px, py in blade],
            "Alloy",
            rotor,
            0.012,
        )
    unit.round((x, y, 4.841), (x, y, 4.926), 0.155, "SafetyAmber", rotor, n=10)
    unit.round((x, y, 4.924), (x, y, 4.942), 0.093, "Carbon", rotor, n=8)
    # Two fixed ribs span the rotor face without obscuring its broad blades.
    for offset in (-0.235, 0.235):
        unit.rail(
            (x - 0.43, y + offset, 4.953),
            (x + 0.43, y + offset, 4.953),
            0.079,
            0.067,
            "Frame",
            right,
            0.012,
        )


def make_kiln():
    unit = Unit("Kiln", "Ground-unit factory")
    deck_and_bay(unit)
    left = wing(unit, -1)
    right = wing(unit, 1)
    gate_and_lintel(unit)
    fabrication_line(unit)
    exhaust(unit, left, right)
    unit.bone("socket_unit_spawn", SPAWN, length=0.30)
    unit.bone("socket_unit_exit", EXIT, length=0.30)
    unit.make_rig()
    unit.rig["production_units"] = "foundry:siltback,foundry:rivet"
    unit.rig["deploy_open_start_frame"] = GATE_OPEN_FRAME
    unit.rig["deploy_open_end_frame"] = GATE_CLOSE_FRAME
    unit.rig["animation_fps"] = 30
    return unit


def slide_shutters(rig, fraction):
    for side, suffix in ((-1, "L"), (1, "R")):
        set_pose(
            rig, "shutter." + suffix, location=(side * GATE_TRAVEL * fraction, 0, 0)
        )


def pose(unit, clip, frame, t):
    rig = unit.rig

    if clip == "idle":
        set_pose(rig, "fan", z=math.tau * t)
        light = 1 + 14 * (1 - math.cos(math.tau * t))
        set_pose(rig, "process_light", scale=light)
    elif clip == "produce":
        set_pose(rig, "fan", z=2 * math.tau * t)
        travel = tween(
            frame, [(1, 0), (11, 0), (36, -1.85), (61, -1.85), (85, 0), (91, 0)]
        )
        stroke = tween(
            frame, [(1, 0), (33, 0), (40, -0.74), (50, -0.74), (61, 0), (91, 0)]
        )
        glow = tween(
            frame,
            [
                (1, 1),
                (20, 1),
                (38, 156),
                (42, 184),
                (48, 121),
                (53, 159),
                (61, 84),
                (73, 24),
                (91, 1),
            ],
        )
        set_pose(rig, "carriage", location=(0, travel, 0))
        set_pose(rig, "press", location=(0, 0, stroke))
        set_pose(rig, "process_light", scale=glow)
    elif clip == "deploy":
        set_pose(rig, "fan", z=2 * math.tau * t)
        slide = tween(
            frame,
            [
                (1, 0),
                (5, 0),
                (GATE_OPEN_FRAME, 1),
                (GATE_CLOSE_FRAME, 1),
                (129, 0),
                (133, 0),
            ],
        )
        slide_shutters(rig, slide)
    elif clip == "destroyed":
        twist = tween(
            frame, [(1, 0), (12, -0.17), (25, 1), (33, 0.82), (47, 0.96), (61, 0.96)]
        )
        set_pose(
            rig,
            "fan",
            z=tween(frame, [(1, 0), (8, 1.43), (22, 2.78), (41, 3.49), (61, 3.49)]),
        )
        set_pose(
            rig,
            "wing.L",
            y=-0.046 * twist,
            z=-0.025 * twist,
            location=(-0.07 * twist, 0, -0.075 * twist),
        )
        set_pose(
            rig,
            "wing.R",
            y=0.070 * twist,
            z=-0.038 * twist,
            location=(0.094 * twist, 0.03 * twist, -0.19 * twist),
        )
        set_pose(
            rig,
            "lintel",
            x=0.11 * twist,
            y=-0.11 * twist,
            location=(0.08 * twist, -0.09 * twist, -0.27 * twist),
        )
        set_pose(
            rig,
            "carriage",
            x=-0.21 * twist,
            z=0.19 * twist,
            location=(0.12 * twist, -0.59 * twist, -0.61 * twist),
        )
        set_pose(rig, "press", location=(0, 0, -0.39 * twist))
        set_pose(
            rig,
            "exhaust",
            x=0.41 * twist,
            y=0.18 * twist,
            location=(0, 0, -0.16 * twist),
        )
        set_pose(
            rig,
            "shutter.L",
            x=-0.10 * twist,
            y=-0.046 * twist,
            location=(-0.24 * twist, 0.295 * twist, 0.11 * twist),
        )
        set_pose(
            rig,
            "shutter.R",
            x=0.17 * twist,
            y=0.086 * twist,
            z=0.13 * twist,
            location=(0.42 * twist, -0.068 * twist, 0.12 * twist),
        )
        set_pose(
            rig,
            "process_light",
            scale=tween(
                frame,
                [
                    (1, 1),
                    (7, 1),
                    (14, 221),
                    (18, 43),
                    (23, 152),
                    (28, 9),
                    (41, 1),
                    (61, 1),
                ],
            ),
        )
