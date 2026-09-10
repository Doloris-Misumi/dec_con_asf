from __future__ import annotations

from pathlib import Path

from draw_pipeline_overview import Figure, PALETTE


OUT_DIR = Path(__file__).resolve().parent


def sensor_row(fig: Figure, x: int, y: int, name: str, fill: str, stroke: str):
    fig.rect(x, y, 168, 54, PALETTE["white"], PALETTE["soft_line"], width=1.3, r=12)
    fig.circle(x + 25, y + 27, 13, fill, stroke, width=2)
    fig.text(x + 52, y + 19, name, size=14, bold=True)
    fig.text(x + 52, y + 38, "frozen", size=11, fill=PALETTE["muted"])
    fig.rect(x + 208, y, 150, 54, PALETTE["gray"], PALETTE["gray_stroke"], width=1.2, r=12)
    fig.text(x + 283, y + 22, "BEV feature", size=13, bold=True, anchor="mm")
    fig.text(x + 283, y + 40, "C x H x W", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.line([(x + 168, y + 27), (x + 208, y + 27)], PALETTE["line"], width=2.4, arrow=True)


def token_grid(fig: Figure, x: int, y: int, fill: str, stroke: str):
    fig.small_token_grid(x, y, cols=5, rows=3, cell=14, gap=5, fill=fill, outline=stroke)


def control_lane(fig: Figure, x: int, y1: int, y2: int, color: str, label: str, label_y: int):
    fig.circle(x, y1, 5, PALETTE["white"], color, width=2)
    fig.circle(x, y2, 5, PALETTE["white"], color, width=2)
    fig.line([(x, y1), (x, y2)], color, width=2.4, dash=(8, 7), arrow=True, marker="arrow-green" if color == PALETTE["ours_deep"] else "arrow-amber" if color == PALETTE["amber_stroke"] else "arrow-rose")
    fig.text(x + 10, label_y, label, size=11, bold=True, fill=color)


def draw_clean_main():
    svg_path = OUT_DIR / "task_dec_asf_pipeline_overview_v3_clean.svg"
    png_path = OUT_DIR / "task_dec_asf_pipeline_overview_v3_clean.png"
    fig = Figure(width=1800, height=900, svg_path=svg_path, png_path=png_path)

    # Inputs stay compact and quiet.
    fig.pill(70, 62, 150, 30, "multi-modal input", PALETTE["gray"], PALETTE["gray_stroke"], color=PALETTE["muted"], size=12)
    rows = [
        (70, 132, "Camera", "#d9ebff", PALETTE["asf_stroke"]),
        (70, 222, "LiDAR", "#def5ea", PALETTE["ours_stroke"]),
        (70, 312, "4D Radar", "#fff0c7", PALETTE["amber_stroke"]),
    ]
    for x, y, name, fill, stroke in rows:
        sensor_row(fig, x, y, name, fill, stroke)

    # ASF becomes a clean substrate with only the essential forward path.
    asf_x, asf_y, asf_w, asf_h = 485, 72, 900, 292
    fig.rect(asf_x, asf_y, asf_w, asf_h, PALETTE["asf"], PALETTE["asf_stroke"], width=2.0, r=22, shadow=True)
    fig.pill(asf_x + 30, asf_y + 28, 160, 30, "ASF substrate", PALETTE["white"], PALETTE["asf_stroke"], color=PALETTE["asf_deep"], size=13, bold=True)
    fig.text(asf_x + 215, asf_y + 34, "canonical patch projection -> patch-level attention -> fused BEV", size=14, fill=PALETTE["muted"])

    token_specs = [
        (530, 135, "#d9ebff", PALETTE["asf_stroke"], 132),
        (530, 202, "#def5ea", PALETTE["ours_stroke"], 222),
        (530, 269, "#fff0c7", PALETTE["amber_stroke"], 312),
    ]
    for tx, ty, fill, stroke, src_y in token_specs:
        fig.line([(428, src_y + 27), (475, src_y + 27), (505, ty + 22), (530, ty + 22)], PALETTE["line"], width=2.0, arrow=True)
        token_grid(fig, tx, ty, fill, stroke)
    fig.text(575, 330, "canonical patches z_m,p", size=11, fill=PALETTE["muted"], anchor="mm")

    fig.rect(695, 164, 140, 92, PALETTE["white"], PALETTE["soft_line"], width=1.4, r=15)
    fig.text(765, 190, "To-Embed", size=13, bold=True, anchor="mm")
    fig.text(765, 214, "+ UCP", size=15, bold=True, anchor="mm")
    fig.text(765, 236, "dim 256", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.line([(628, 210), (695, 210)], PALETTE["asf_deep"], width=2.5, arrow=True, marker="arrow-blue")

    fig.rect(915, 146, 160, 125, PALETTE["white"], PALETTE["asf_stroke"], width=1.7, r=16)
    fig.text(995, 177, "Aware-query", size=13, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(995, 204, "MHA", size=24, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(995, 232, "patch K/V", size=12, fill=PALETTE["muted"], anchor="mm")
    fig.line([(835, 210), (915, 208)], PALETTE["asf_deep"], width=2.5, arrow=True, marker="arrow-blue")

    fig.rect(1128, 164, 88, 92, PALETTE["white"], PALETTE["asf_stroke"], width=1.5, r=14)
    fig.text(1172, 194, "PFT", size=15, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(1172, 219, "reshape", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1075, 208), (1128, 210)], PALETTE["asf_deep"], width=2.5, arrow=True, marker="arrow-blue")

    fig.rect(1262, 166, 82, 90, PALETTE["white"], PALETTE["soft_line"], width=1.3, r=14)
    fig.text(1303, 195, "fused", size=12, bold=True, fill=PALETTE["muted"], anchor="mm")
    fig.text(1303, 218, "BEV", size=15, bold=True, anchor="mm")
    fig.line([(1216, 210), (1262, 211)], PALETTE["asf_deep"], width=2.5, arrow=True, marker="arrow-blue")

    # Injection ports align vertically with the controller heads.
    ports = [
        (610, "patch residual", PALETTE["rose_stroke"]),
        (945, "K/V scale", PALETTE["amber_stroke"]),
        (1165, "query bias", PALETTE["ours_deep"]),
        (1260, "fused residual", PALETTE["ours_deep"]),
    ]
    for px, label, color in ports:
        fig.circle(px, asf_y + asf_h - 18, 5, PALETTE["white"], color, width=2)
        fig.text(px, asf_y + asf_h - 38, label, size=10, bold=True, fill=color, anchor="mm")

    # Detection path stays outside the method block.
    fig.line([(1344, 211), (1490, 211), (1490, 312)], PALETTE["asf_deep"], width=2.8, arrow=True, marker="arrow-blue")
    fig.rect(1488, 312, 242, 90, PALETTE["gray"], PALETTE["gray_stroke"], width=1.5, r=15)
    fig.text(1609, 343, "Detection head", size=17, bold=True, anchor="mm")
    fig.text(1609, 368, "3D object boxes", size=12, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1609, 402), (1609, 458)], PALETTE["line"], width=2.5, arrow=True)
    fig.rect(1488, 458, 242, 112, PALETTE["white"], PALETTE["soft_line"], width=1.3, r=15)
    box_lines = [
        [(1528, 510), (1587, 492), (1610, 514), (1550, 534), (1528, 510)],
        [(1604, 498), (1670, 490), (1690, 512), (1622, 522), (1604, 498)],
    ]
    for pts in box_lines:
        fig.line(pts, PALETTE["amber_stroke"], width=2.4)
    fig.text(1609, 552, "BEV / 3D AP", size=12, bold=True, fill=PALETTE["muted"], anchor="mm")

    # Ours is the visual anchor.
    ctl_x, ctl_y, ctl_w, ctl_h = 360, 448, 1035, 330
    fig.rect(ctl_x, ctl_y, ctl_w, ctl_h, PALETTE["ours"], PALETTE["ours_stroke"], width=2.6, r=24, shadow=True)
    fig.pill(ctl_x + 28, ctl_y + 28, 104, 32, "Ours", PALETTE["white"], PALETTE["ours_stroke"], color=PALETTE["ours_deep"], size=13, bold=True)
    fig.text(ctl_x + 160, ctl_y + 27, "Task-aware Decoupled Fusion Controller", size=25, bold=True, fill=PALETTE["ours_deep"])
    fig.text(ctl_x + 162, ctl_y + 60, "Common/unique patch factors are converted into clean, aligned control channels.", size=14, fill=PALETTE["muted"])

    fig.rect(410, 548, 150, 84, PALETTE["white"], PALETTE["ours_stroke"], width=1.5, r=15)
    fig.text(485, 574, "canonical", size=14, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(485, 596, "patch tokens", size=13, fill=PALETTE["muted"], anchor="mm")
    fig.text(485, 616, "z_m,p", size=12, fill=PALETTE["muted"], anchor="mm")
    fig.line([(540, asf_y + asf_h - 18), (540, 420), (485, 420), (485, 548)], PALETTE["ours_deep"], width=2.2, dash=(8, 7), arrow=True, marker="arrow-green")

    fig.line([(560, 590), (610, 590)], PALETTE["ours_deep"], width=2.6, arrow=True, marker="arrow-green")
    fig.rect(612, 516, 225, 148, PALETTE["white"], PALETTE["ours_stroke"], width=1.7, r=18)
    fig.text(724, 546, "Patch Decoupling", size=17, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.rect(650, 572, 72, 54, "#e2f6ec", PALETTE["ours_stroke"], width=1.2, r=12)
    fig.text(686, 594, "common", size=11, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(686, 612, "c_m,p", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.rect(732, 572, 72, 54, "#fff5d8", PALETTE["amber_stroke"], width=1.2, r=12)
    fig.text(768, 594, "unique", size=11, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.text(768, 612, "u_m,p", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.text(724, 647, "foreground-only decoupling losses", size=10, fill=PALETTE["muted"], anchor="mm")

    fig.line([(837, 590), (890, 590)], PALETTE["ours_deep"], width=2.5, arrow=True, marker="arrow-green")
    fig.rect(892, 548, 150, 84, PALETTE["white"], PALETTE["soft_line"], width=1.3, r=15)
    fig.text(967, 574, "task summary", size=13, bold=True, anchor="mm")
    fig.text(967, 596, "c_bar, |u|_bar", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.text(967, 616, "per patch p", size=11, fill=PALETTE["muted"], anchor="mm")

    fig.rect(500, 682, 855, 74, "#f7fbf9", PALETTE["soft_line"], width=1.1, r=17)
    fig.text(520, 701, "aligned control channels", size=12, bold=True, fill=PALETTE["muted"])
    fig.rect(535, 709, 150, 38, PALETTE["rose"], PALETTE["rose_stroke"], width=1.3, r=12)
    fig.text(610, 728, "Foreground gate", size=12, bold=True, fill=PALETTE["rose_stroke"], anchor="mm")
    fig.rect(860, 709, 170, 38, PALETTE["amber"], PALETTE["amber_stroke"], width=1.3, r=12)
    fig.text(945, 728, "Sensor reliability", size=12, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.rect(1120, 698, 215, 52, PALETTE["lav"], PALETTE["lav_stroke"], width=1.3, r=13)
    fig.text(1228, 718, "Task context adapter", size=12, bold=True, fill=PALETTE["lav_stroke"], anchor="mm")
    fig.text(1228, 738, "query + fused deltas", size=10, fill=PALETTE["muted"], anchor="mm")

    fig.line([(967, 632), (967, 682)], PALETTE["line"], width=2.2, arrow=True)
    fig.line([(967, 682), (610, 709)], PALETTE["line"], width=1.7, arrow=True)
    fig.line([(967, 682), (945, 709)], PALETTE["line"], width=1.7, arrow=True)
    fig.line([(967, 682), (1228, 698)], PALETTE["line"], width=1.7, arrow=True)

    # Straight, non-crossing control lanes. They live only in the gap between
    # the controller and ASF, so the method block stays visually clean.
    fig.text(505, ctl_y - 17, "output ports", size=10, bold=True, fill=PALETTE["muted"])
    control_lane(fig, 610, ctl_y, asf_y + asf_h - 18, PALETTE["rose_stroke"], "gate", 418)
    control_lane(fig, 945, ctl_y, asf_y + asf_h - 18, PALETTE["amber_stroke"], "reliability", 418)
    control_lane(fig, 1165, ctl_y, asf_y + asf_h - 18, PALETTE["ours_deep"], "query", 418)
    control_lane(fig, 1260, ctl_y, asf_y + asf_h - 18, PALETTE["ours_deep"], "fused", 418)

    # Small textual footer.
    fig.rect(70, 828, 1660, 1, PALETTE["soft_line"], PALETTE["soft_line"], width=1, r=0)
    fig.text(80, 849, "ASF is compact:", size=13, bold=True, fill=PALETTE["asf_deep"])
    fig.text(205, 849, "it supplies canonical patch fusion.", size=13, fill=PALETTE["muted"])
    fig.text(560, 849, "Main idea:", size=13, bold=True, fill=PALETTE["ours_deep"])
    fig.text(650, 849, "decoupled patch semantics drive sensor availability and task-aware fusion.", size=13, fill=PALETTE["muted"])

    fig.finish()
    print(f"Wrote {svg_path}")
    print(f"Wrote {png_path}")


def draw_clean_detail():
    svg_path = OUT_DIR / "task_dec_controller_detail_v2_clean.svg"
    png_path = OUT_DIR / "task_dec_controller_detail_v2_clean.png"
    fig = Figure(width=1700, height=820, svg_path=svg_path, png_path=png_path)

    fig.text(70, 52, "Task-aware Decoupled Controller", size=26, bold=True, fill=PALETTE["ours_deep"])
    fig.text(72, 86, "A clean two-stream view: common semantics and unique evidence are summarized into patch-wise controls.", size=14, fill=PALETTE["muted"])

    # Left: input and decoupling.
    fig.rect(70, 165, 210, 430, PALETTE["white"], PALETTE["soft_line"], width=1.4, r=18)
    fig.text(95, 200, "Canonical tokens", size=17, bold=True)
    for y, fill, stroke, label in [
        (245, "#d9ebff", PALETTE["asf_stroke"], "camera"),
        (355, "#def5ea", PALETTE["ours_stroke"], "lidar"),
        (465, "#fff0c7", PALETTE["amber_stroke"], "radar"),
    ]:
        token_grid(fig, 105, y, fill, stroke)
        fig.text(150, y + 64, label, size=11, fill=PALETTE["muted"], anchor="mm")
    fig.rect(340, 305, 190, 150, PALETTE["ours"], PALETTE["ours_stroke"], width=1.9, r=18)
    fig.text(435, 342, "Patch", size=17, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(435, 369, "Decoupling", size=19, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.rect(380, 395, 62, 42, "#e2f6ec", PALETTE["ours_stroke"], width=1.1, r=11)
    fig.text(411, 416, "E_com", size=10, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.rect(452, 395, 62, 42, "#fff5d8", PALETTE["amber_stroke"], width=1.1, r=11)
    fig.text(483, 416, "E_uni", size=10, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.line([(280, 380), (340, 380)], PALETTE["line"], width=2.3, arrow=True)

    # Common stream.
    fig.rect(610, 145, 650, 250, PALETTE["ours"], PALETTE["ours_stroke"], width=1.9, r=20)
    fig.pill(640, 174, 155, 30, "Common stream", PALETTE["white"], PALETTE["ours_stroke"], color=PALETTE["ours_deep"], size=13, bold=True)
    fig.text(820, 180, "shared target information", size=13, fill=PALETTE["muted"])
    for y, label in [(230, "c_cam,p"), (280, "c_lid,p"), (330, "c_rad,p")]:
        fig.rect(655, y, 120, 34, "#e2f6ec", PALETTE["ours_stroke"], width=1.1, r=9)
        fig.text(715, y + 17, label, size=11, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.rect(850, 248, 140, 64, PALETTE["white"], PALETTE["soft_line"], width=1.2, r=13)
    fig.text(920, 272, "aggregate", size=12, bold=True, anchor="mm")
    fig.text(920, 294, "c_bar", size=12, fill=PALETTE["muted"], anchor="mm")
    fig.rect(1060, 220, 150, 54, PALETTE["white"], PALETTE["ours_stroke"], width=1.2, r=12)
    fig.text(1135, 241, "common align", size=12, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(1135, 260, "cross-modal", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.rect(1060, 300, 150, 54, PALETTE["white"], PALETTE["rose_stroke"], width=1.2, r=12)
    fig.text(1135, 321, "orthogonal", size=12, bold=True, fill=PALETTE["rose_stroke"], anchor="mm")
    fig.text(1135, 340, "c vs u", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.line([(530, 350), (610, 270)], PALETTE["ours_deep"], width=2.2, arrow=True, marker="arrow-green")
    fig.line([(775, 247), (850, 280)], PALETTE["line"], width=1.8, arrow=True)
    fig.line([(775, 297), (850, 280)], PALETTE["line"], width=1.8, arrow=True)
    fig.line([(775, 347), (850, 280)], PALETTE["line"], width=1.8, arrow=True)
    fig.line([(990, 280), (1060, 247)], PALETTE["ours_deep"], width=1.8, arrow=True, marker="arrow-green")
    fig.line([(990, 280), (1060, 327)], PALETTE["rose_stroke"], width=1.8, arrow=True, marker="arrow-rose")

    # Unique stream.
    fig.rect(610, 455, 650, 250, PALETTE["amber"], PALETTE["amber_stroke"], width=1.9, r=20)
    fig.pill(640, 484, 150, 30, "Unique stream", PALETTE["white"], PALETTE["amber_stroke"], color=PALETTE["amber_stroke"], size=13, bold=True)
    fig.text(815, 490, "sensor-specific evidence", size=13, fill=PALETTE["muted"])
    for y, label in [(540, "u_cam,p"), (590, "u_lid,p"), (640, "u_rad,p")]:
        fig.rect(655, y, 120, 34, "#fff8e4", PALETTE["amber_stroke"], width=1.1, r=9)
        fig.text(715, y + 17, label, size=11, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.rect(850, 558, 140, 64, PALETTE["white"], PALETTE["soft_line"], width=1.2, r=13)
    fig.text(920, 582, "aggregate", size=12, bold=True, anchor="mm")
    fig.text(920, 604, "|u|_bar", size=12, fill=PALETTE["muted"], anchor="mm")
    fig.rect(1060, 535, 150, 54, PALETTE["white"], PALETTE["amber_stroke"], width=1.2, r=12)
    fig.text(1135, 556, "unique split", size=12, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.text(1135, 575, "margin", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.rect(1060, 615, 150, 54, PALETTE["white"], PALETTE["gray_stroke"], width=1.2, r=12)
    fig.text(1135, 636, "sensor cue", size=12, bold=True, fill=PALETTE["ink"], anchor="mm")
    fig.text(1135, 655, "|c_m - c_bar|", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.line([(530, 410), (610, 580)], PALETTE["amber_stroke"], width=2.2, arrow=True, marker="arrow-amber")
    fig.line([(775, 557), (850, 590)], PALETTE["line"], width=1.8, arrow=True)
    fig.line([(775, 607), (850, 590)], PALETTE["line"], width=1.8, arrow=True)
    fig.line([(775, 657), (850, 590)], PALETTE["line"], width=1.8, arrow=True)
    fig.line([(990, 590), (1060, 562)], PALETTE["amber_stroke"], width=1.8, arrow=True, marker="arrow-amber")
    fig.line([(990, 590), (1060, 642)], PALETTE["line"], width=1.8, arrow=True)

    # Clean summary and heads.
    fig.rect(1310, 310, 145, 86, PALETTE["white"], PALETTE["soft_line"], width=1.3, r=15)
    fig.text(1382, 337, "patch task", size=13, bold=True, anchor="mm")
    fig.text(1382, 359, "summary", size=13, bold=True, anchor="mm")
    fig.text(1382, 381, "[c_bar, |u|_bar]", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1210, 247), (1310, 353)], PALETTE["ours_deep"], width=2.0, arrow=True, marker="arrow-green")
    fig.line([(1210, 590), (1310, 353)], PALETTE["amber_stroke"], width=2.0, arrow=True, marker="arrow-amber")

    fig.rect(1500, 205, 160, 60, PALETTE["rose"], PALETTE["rose_stroke"], width=1.3, r=13)
    fig.text(1580, 229, "g_p", size=14, bold=True, fill=PALETTE["rose_stroke"], anchor="mm")
    fig.text(1580, 249, "foreground", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.rect(1500, 320, 160, 60, PALETTE["amber"], PALETTE["amber_stroke"], width=1.3, r=13)
    fig.text(1580, 344, "alpha_m,p", size=13, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.text(1580, 364, "reliability", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.rect(1500, 435, 160, 60, PALETTE["lav"], PALETTE["lav_stroke"], width=1.3, r=13)
    fig.text(1580, 459, "t_p", size=14, bold=True, fill=PALETTE["lav_stroke"], anchor="mm")
    fig.text(1580, 479, "task context", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1455, 353), (1500, 235)], PALETTE["line"], width=1.8, arrow=True)
    fig.line([(1455, 353), (1500, 350)], PALETTE["line"], width=1.8, arrow=True)
    fig.line([(1455, 353), (1500, 465)], PALETTE["line"], width=1.8, arrow=True)

    fig.rect(1500, 615, 160, 64, PALETTE["asf"], PALETTE["asf_stroke"], width=1.3, r=13)
    fig.text(1580, 638, "ASF modulation", size=12, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(1580, 659, "K/V, query, fused", size=10, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1580, 495), (1580, 615)], PALETTE["asf_deep"], width=2.2, arrow=True, marker="arrow-blue")

    fig.rect(70, 750, 1140, 1, PALETTE["soft_line"], PALETTE["soft_line"], width=1, r=0)
    fig.text(78, 772, "Difference from DecAlign:", size=13, bold=True, fill=PALETTE["ours_deep"])
    fig.text(276, 772, "decoupling is used to control ASF patch fusion, not only to form the final representation.", size=13, fill=PALETTE["muted"])

    fig.finish()
    print(f"Wrote {svg_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    draw_clean_main()
    draw_clean_detail()
