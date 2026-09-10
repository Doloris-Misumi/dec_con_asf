from __future__ import annotations

from pathlib import Path

from draw_pipeline_overview import Figure, PALETTE


OUT_DIR = Path(__file__).resolve().parent


def token_stack(fig: Figure, x: int, y: int, label: str, fill: str, stroke: str):
    fig.small_token_grid(x, y, cols=5, rows=3, cell=15, gap=5, fill=fill, outline=stroke)
    fig.text(x + 48, y + 70, label, size=12, fill=PALETTE["muted"], anchor="mm")


def tiny_sensor(fig: Figure, x: int, y: int, name: str, fill: str, stroke: str):
    fig.rect(x, y, 178, 54, PALETTE["white"], PALETTE["soft_line"], width=1.4, r=12)
    fig.circle(x + 26, y + 27, 13, fill, stroke, width=2)
    fig.text(x + 52, y + 18, name, size=14, bold=True)
    fig.text(x + 52, y + 36, "frozen encoder", size=11, fill=PALETTE["muted"])


def draw_main():
    svg_path = OUT_DIR / "task_dec_asf_pipeline_overview_v2_main.svg"
    png_path = OUT_DIR / "task_dec_asf_pipeline_overview_v2_main.png"
    fig = Figure(width=1800, height=920, svg_path=svg_path, png_path=png_path)

    # Compact inputs.
    fig.pill(70, 62, 164, 32, "inputs", PALETTE["gray"], PALETTE["gray_stroke"], color=PALETTE["muted"], size=13)
    sensor_rows = [
        (70, 125, "Camera", "#d9ebff", PALETTE["asf_stroke"]),
        (70, 215, "LiDAR", "#def5ea", PALETTE["ours_stroke"]),
        (70, 305, "4D Radar", "#fff0c7", PALETTE["amber_stroke"]),
    ]
    for x, y, name, fill, stroke in sensor_rows:
        tiny_sensor(fig, x, y, name, fill, stroke)
        fig.rect(282, y, 156, 54, PALETTE["gray"], PALETTE["gray_stroke"], width=1.4, r=12)
        fig.text(360, y + 21, "BEV feature", size=13, bold=True, anchor="mm")
        fig.text(360, y + 39, "C x H x W", size=11, fill=PALETTE["muted"], anchor="mm")
        fig.line([(248, y + 27), (282, y + 27)], PALETTE["line"], width=2.6, arrow=True)

    # ASF is now a compact supporting substrate.
    fig.rect(510, 62, 865, 260, PALETTE["asf"], PALETTE["asf_stroke"], width=2.0, r=20, shadow=True)
    fig.pill(540, 88, 208, 30, "ASF substrate", PALETTE["white"], PALETTE["asf_stroke"], color=PALETTE["asf_deep"], size=13, bold=True)
    fig.text(770, 93, "canonical patch projection and patch-level attention", size=14, fill=PALETTE["muted"])

    token_specs = [
        (575, 145, "cam z_c,p", "#d9ebff", PALETTE["asf_stroke"], 125),
        (575, 210, "lidar z_l,p", "#def5ea", PALETTE["ours_stroke"], 215),
        (575, 275, "radar z_r,p", "#fff0c7", PALETTE["amber_stroke"], 305),
    ]
    for x, y, label, fill, stroke, source_y in token_specs:
        fig.line([(438, source_y + 27), (496, source_y + 27), (530, y + 23), (575, y + 23)], PALETTE["line"], width=2.2, arrow=True)
        token_stack(fig, x, y, label, fill, stroke)

    fig.rect(765, 150, 118, 108, PALETTE["white"], PALETTE["soft_line"], width=1.5, r=15)
    fig.text(824, 181, "To-Embed", size=13, bold=True, anchor="mm")
    fig.text(824, 204, "+ UCP", size=13, bold=True, anchor="mm")
    fig.text(824, 228, "dim 256", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.line([(675, 205), (765, 205)], PALETTE["asf_deep"], width=2.4, arrow=True, marker="arrow-blue")

    fig.rect(945, 133, 150, 120, PALETTE["white"], PALETTE["asf_stroke"], width=1.8, r=16)
    fig.text(1020, 169, "Aware-query", size=14, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(1020, 193, "MHA", size=23, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(1020, 220, "K/V patches", size=12, fill=PALETTE["muted"], anchor="mm")
    fig.line([(883, 205), (945, 193)], PALETTE["asf_deep"], width=2.5, arrow=True, marker="arrow-blue")

    fig.rect(1145, 154, 86, 78, PALETTE["white"], PALETTE["asf_stroke"], width=1.6, r=14)
    fig.text(1188, 182, "PFT", size=15, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(1188, 205, "reshape", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1095, 193), (1145, 193)], PALETTE["asf_deep"], width=2.5, arrow=True, marker="arrow-blue")

    fig.rect(1260, 147, 82, 92, PALETTE["white"], PALETTE["soft_line"], width=1.4, r=13)
    fig.text(1301, 178, "fused", size=12, bold=True, fill=PALETTE["muted"], anchor="mm")
    fig.text(1301, 199, "BEV", size=14, bold=True, fill=PALETTE["ink"], anchor="mm")
    fig.line([(1231, 193), (1260, 193)], PALETTE["asf_deep"], width=2.4, arrow=True, marker="arrow-blue")

    # Ours is the visual center.
    fig.rect(368, 385, 1075, 405, PALETTE["ours"], PALETTE["ours_stroke"], width=2.6, r=24, shadow=True)
    fig.pill(398, 414, 110, 34, "Ours", PALETTE["white"], PALETTE["ours_stroke"], color=PALETTE["ours_deep"], size=14, bold=True)
    fig.text(530, 418, "Task-aware Decoupled Fusion Controller", size=27, bold=True, fill=PALETTE["ours_deep"])
    fig.text(532, 452, "Decouple canonical patch tokens, infer patch semantics, and control ASF fusion dynamically.", size=15, fill=PALETTE["muted"])

    fig.rect(420, 515, 155, 86, PALETTE["white"], PALETTE["ours_stroke"], width=1.6, r=15)
    fig.text(498, 543, "canonical", size=14, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(498, 564, "patch tokens", size=13, fill=PALETTE["muted"], anchor="mm")
    fig.text(498, 584, "z_m,p", size=13, fill=PALETTE["muted"], anchor="mm")
    fig.line([(625, 322), (625, 350), (390, 350), (390, 558), (420, 558)], PALETTE["ours_deep"], width=2.3, dash=(9, 7), arrow=True, marker="arrow-green")

    fig.line([(575, 558), (638, 558)], PALETTE["ours_deep"], width=2.6, arrow=True, marker="arrow-green")
    fig.rect(640, 488, 230, 155, PALETTE["white"], PALETTE["ours_stroke"], width=1.8, r=18)
    fig.text(755, 518, "Patch Decoupling", size=17, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.rect(672, 548, 78, 54, "#e2f6ec", PALETTE["ours_stroke"], width=1.3, r=12)
    fig.text(711, 570, "common", size=12, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(711, 589, "c_m,p", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.rect(760, 548, 78, 54, "#fff5d8", PALETTE["amber_stroke"], width=1.3, r=12)
    fig.text(799, 570, "unique", size=12, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.text(799, 589, "u_m,p", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.text(755, 623, "common/unique losses on foreground patches", size=11, fill=PALETTE["muted"], anchor="mm")

    fig.line([(870, 545), (930, 500)], PALETTE["ours_deep"], width=2.4, arrow=True, marker="arrow-green")
    fig.line([(870, 575), (930, 575)], PALETTE["ours_deep"], width=2.4, arrow=True, marker="arrow-green")
    fig.line([(870, 605), (930, 650)], PALETTE["ours_deep"], width=2.4, arrow=True, marker="arrow-green")

    head_specs = [
        (930, 460, 214, 74, "Foreground gate", "g_p", PALETTE["rose"], PALETTE["rose_stroke"]),
        (930, 548, 214, 74, "Sensor reliability", "alpha_m,p", PALETTE["amber"], PALETTE["amber_stroke"]),
        (930, 636, 214, 74, "Class context", "t_p", PALETTE["lav"], PALETTE["lav_stroke"]),
    ]
    for x, y, w, h, title, sym, fill, stroke in head_specs:
        fig.rect(x, y, w, h, fill, stroke, width=1.7, r=15)
        fig.text(x + w / 2, y + 26, title, size=15, bold=True, fill=stroke, anchor="mm")
        fig.text(x + w / 2, y + 51, sym, size=15, fill=PALETTE["muted"], anchor="mm")

    fig.rect(1190, 480, 192, 70, PALETTE["white"], PALETTE["gray_stroke"], width=1.4, r=15)
    fig.text(1286, 507, "control vector", size=15, bold=True, anchor="mm")
    fig.text(1286, 530, "[g_p, alpha_m,p, t_p]", size=13, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1144, 497), (1190, 510)], PALETTE["line"], width=2.2, arrow=True)
    fig.line([(1144, 585), (1190, 515)], PALETTE["line"], width=2.2, arrow=True)
    fig.line([(1144, 673), (1190, 523)], PALETTE["line"], width=2.2, arrow=True)

    fig.rect(426, 690, 370, 58, PALETTE["white"], PALETTE["soft_line"], width=1.3, r=14)
    fig.text(446, 708, "Training signals", size=13, bold=True, fill=PALETTE["ink"])
    fig.text(446, 729, "foreground patch mask + class target + decoupling regularizers", size=12, fill=PALETTE["muted"])
    fig.line([(610, 690), (695, 630)], PALETTE["line"], width=1.8, dash=(6, 5), arrow=True)

    # Feedback controls from our module to ASF.
    fig.line([(1286, 480), (1286, 335), (1055, 250)], PALETTE["amber_stroke"], width=2.6, dash=(9, 7), arrow=True, marker="arrow-amber")
    fig.text(1218, 345, "scale K/V", size=12, bold=True, fill=PALETTE["amber_stroke"], anchor="rm")
    fig.line([(1240, 550), (1188, 335), (1019, 133)], PALETTE["ours_deep"], width=2.6, dash=(9, 7), arrow=True, marker="arrow-green")
    fig.text(1168, 338, "query bias", size=12, bold=True, fill=PALETTE["ours_deep"], anchor="rm")
    fig.line([(1330, 550), (1368, 362), (1265, 215)], PALETTE["ours_deep"], width=2.6, dash=(9, 7), arrow=True, marker="arrow-green")
    fig.text(1375, 360, "fused residual", size=12, bold=True, fill=PALETTE["ours_deep"])
    fig.line([(1160, 498), (1160, 360), (760, 360), (690, 227)], PALETTE["rose_stroke"], width=2.2, dash=(8, 7), arrow=True, marker="arrow-rose")
    fig.text(910, 350, "foreground-aware residual", size=12, bold=True, fill=PALETTE["rose_stroke"], anchor="mm")

    # Detection output.
    fig.line([(1342, 193), (1490, 193), (1490, 305)], PALETTE["asf_deep"], width=2.7, arrow=True, marker="arrow-blue")
    fig.rect(1480, 305, 250, 92, PALETTE["gray"], PALETTE["gray_stroke"], width=1.6, r=15)
    fig.text(1605, 336, "Detection head", size=17, bold=True, anchor="mm")
    fig.text(1605, 362, "3D object boxes", size=13, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1605, 397), (1605, 455)], PALETTE["line"], width=2.7, arrow=True)
    fig.rect(1480, 455, 250, 120, PALETTE["white"], PALETTE["soft_line"], width=1.4, r=15)
    for x0, y0, x1, y1 in [(1518, 510, 1585, 490), (1590, 498, 1658, 512), (1535, 543, 1598, 531)]:
        fig.line([(x0, y0), (x1, y0 - 13), (x1 + 24, y1 + 10), (x0 + 20, y0 + 23), (x0, y0)], PALETTE["amber_stroke"], width=2.4)
    fig.text(1605, 560, "BEV / 3D AP", size=12, bold=True, fill=PALETTE["muted"], anchor="mm")

    # Minimal notation footer, not a large title.
    fig.rect(70, 835, 1660, 1, PALETTE["soft_line"], PALETTE["soft_line"], width=1, r=0)
    fig.text(82, 856, "Compact ASF view:", size=13, bold=True, fill=PALETTE["asf_deep"])
    fig.text(238, 856, "canonical patch fusion is retained as a substrate.", size=13, fill=PALETTE["muted"])
    fig.text(620, 856, "Main contribution:", size=13, bold=True, fill=PALETTE["ours_deep"])
    fig.text(780, 856, "task-aware common/unique decomposition controls patch-level sensor fusion.", size=13, fill=PALETTE["muted"])

    fig.finish()
    print(f"Wrote {svg_path}")
    print(f"Wrote {png_path}")


def draw_detail():
    svg_path = OUT_DIR / "task_dec_controller_detail_v1.svg"
    png_path = OUT_DIR / "task_dec_controller_detail_v1.png"
    fig = Figure(width=1700, height=850, svg_path=svg_path, png_path=png_path)

    fig.text(72, 56, "Task-aware Decoupled Controller", size=28, bold=True, fill=PALETTE["ours_deep"])
    fig.text(74, 92, "A DecAlign-inspired common/unique split adapted from representation alignment to patch-level fusion control.", size=15, fill=PALETTE["muted"])

    # Left canonical inputs.
    fig.rect(70, 170, 250, 470, PALETTE["white"], PALETTE["soft_line"], width=1.5, r=18)
    fig.text(95, 205, "Canonical patch tokens", size=18, bold=True)
    inputs = [
        (100, 250, "Camera", "#d9ebff", PALETTE["asf_stroke"]),
        (100, 365, "LiDAR", "#def5ea", PALETTE["ours_stroke"]),
        (100, 480, "4D Radar", "#fff0c7", PALETTE["amber_stroke"]),
    ]
    for x, y, name, fill, stroke in inputs:
        token_stack(fig, x, y, f"{name} z_m,p", fill, stroke)
        fig.line([(195, y + 25), (320, 405)], PALETTE["line"], width=2.0, arrow=True)

    # Central decoupling block.
    fig.rect(360, 300, 190, 210, PALETTE["ours"], PALETTE["ours_stroke"], width=2.0, r=18)
    fig.text(455, 336, "Modality-wise", size=15, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(455, 361, "Patch Decoupling", size=19, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.rect(395, 390, 56, 58, "#e2f6ec", PALETTE["ours_stroke"], width=1.2, r=12)
    fig.text(423, 414, "E_com", size=11, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.rect(460, 390, 56, 58, "#fff5d8", PALETTE["amber_stroke"], width=1.2, r=12)
    fig.text(488, 414, "E_uni", size=11, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")

    # Common stream.
    fig.rect(610, 150, 650, 245, PALETTE["ours"], PALETTE["ours_stroke"], width=1.9, r=20)
    fig.pill(635, 178, 160, 30, "Common stream", PALETTE["white"], PALETTE["ours_stroke"], color=PALETTE["ours_deep"], size=13, bold=True)
    fig.text(820, 184, "shared target semantics across modalities", size=13, fill=PALETTE["muted"])
    common_positions = [(650, 235), (650, 285), (650, 335)]
    for i, (x, y) in enumerate(common_positions):
        fig.rect(x, y, 120, 34, "#e2f6ec", PALETTE["ours_stroke"], width=1.1, r=9)
        fig.text(x + 60, y + 17, f"c_{i + 1},p", size=12, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
        fig.line([(550, 388), (650, y + 17)], PALETTE["ours_deep"], width=2.0, arrow=True, marker="arrow-green")
    fig.rect(845, 250, 145, 82, PALETTE["white"], PALETTE["soft_line"], width=1.4, r=14)
    fig.text(918, 276, "aggregate", size=13, bold=True, anchor="mm")
    fig.text(918, 300, "mean(c_m,p)", size=12, fill=PALETTE["muted"], anchor="mm")
    for _, y in common_positions:
        fig.line([(770, y + 17), (845, 291)], PALETTE["line"], width=1.8, arrow=True)
    fig.rect(1055, 223, 160, 60, PALETTE["white"], PALETTE["ours_stroke"], width=1.3, r=13)
    fig.text(1135, 246, "common align", size=12, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(1135, 266, "cross-modal", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.rect(1055, 305, 160, 60, PALETTE["white"], PALETTE["rose_stroke"], width=1.3, r=13)
    fig.text(1135, 328, "orthogonality", size=12, bold=True, fill=PALETTE["rose_stroke"], anchor="mm")
    fig.text(1135, 348, "common vs unique", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.line([(990, 291), (1055, 253)], PALETTE["ours_deep"], width=1.8, arrow=True, marker="arrow-green")
    fig.line([(990, 291), (1055, 335)], PALETTE["rose_stroke"], width=1.8, arrow=True, marker="arrow-rose")

    # Unique stream.
    fig.rect(610, 455, 650, 245, PALETTE["amber"], PALETTE["amber_stroke"], width=1.9, r=20)
    fig.pill(635, 483, 155, 30, "Unique stream", PALETTE["white"], PALETTE["amber_stroke"], color=PALETTE["amber_stroke"], size=13, bold=True)
    fig.text(815, 489, "sensor-specific evidence and reliability cues", size=13, fill=PALETTE["muted"])
    unique_positions = [(650, 540), (650, 590), (650, 640)]
    for i, (x, y) in enumerate(unique_positions):
        fig.rect(x, y, 120, 34, "#fff8e4", PALETTE["amber_stroke"], width=1.1, r=9)
        fig.text(x + 60, y + 17, f"u_{i + 1},p", size=12, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
        fig.line([(550, 428), (650, y + 17)], PALETTE["amber_stroke"], width=2.0, arrow=True, marker="arrow-amber")
    fig.rect(845, 555, 145, 82, PALETTE["white"], PALETTE["soft_line"], width=1.4, r=14)
    fig.text(918, 581, "aggregate", size=13, bold=True, anchor="mm")
    fig.text(918, 605, "mean(|u_m,p|)", size=12, fill=PALETTE["muted"], anchor="mm")
    for _, y in unique_positions:
        fig.line([(770, y + 17), (845, 596)], PALETTE["line"], width=1.8, arrow=True)
    fig.rect(1055, 545, 160, 60, PALETTE["white"], PALETTE["amber_stroke"], width=1.3, r=13)
    fig.text(1135, 568, "unique separate", size=12, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.text(1135, 588, "margin loss", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.rect(1055, 625, 160, 60, PALETTE["white"], PALETTE["gray_stroke"], width=1.3, r=13)
    fig.text(1135, 648, "sensor evidence", size=12, bold=True, fill=PALETTE["ink"], anchor="mm")
    fig.text(1135, 668, "|c_m,p - c_bar|", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.line([(990, 596), (1055, 575)], PALETTE["amber_stroke"], width=1.8, arrow=True, marker="arrow-amber")
    fig.line([(990, 596), (1055, 655)], PALETTE["line"], width=1.8, arrow=True)

    # Control heads.
    fig.rect(1320, 235, 285, 385, PALETTE["white"], PALETTE["soft_line"], width=1.6, r=20, shadow=True)
    fig.text(1345, 270, "Patch-wise control heads", size=18, bold=True)
    control_heads = [
        (1350, 315, "Foreground gate", "from [c_bar, |u|_bar]", "g_p", PALETTE["rose"], PALETTE["rose_stroke"]),
        (1350, 415, "Sensor reliability", "from [z, c, u, |c-c_bar|]", "alpha_m,p", PALETTE["amber"], PALETTE["amber_stroke"]),
        (1350, 515, "Class context", "from [c_bar, |u|_bar]", "t_p", PALETTE["lav"], PALETTE["lav_stroke"]),
    ]
    for x, y, title, source, sym, fill, stroke in control_heads:
        fig.rect(x, y, 220, 72, fill, stroke, width=1.5, r=14)
        fig.text(x + 110, y + 21, title, size=14, bold=True, fill=stroke, anchor="mm")
        fig.text(x + 110, y + 43, source, size=10, fill=PALETTE["muted"], anchor="mm")
        fig.text(x + 110, y + 61, sym, size=12, bold=True, fill=PALETTE["ink"], anchor="mm")

    fig.rect(1035, 398, 190, 46, PALETTE["white"], PALETTE["soft_line"], width=1.3, r=13)
    fig.text(1130, 416, "task summary", size=12, bold=True, fill=PALETTE["ink"], anchor="mm")
    fig.text(1130, 434, "[c_bar, |u|_bar]", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.line([(990, 291), (1035, 421)], PALETTE["ours_deep"], width=1.8, arrow=True, marker="arrow-green")
    fig.line([(990, 596), (1035, 421)], PALETTE["amber_stroke"], width=1.8, arrow=True, marker="arrow-amber")
    fig.line([(1225, 421), (1320, 350)], PALETTE["line"], width=2.0, arrow=True)
    fig.line([(1225, 421), (1320, 450)], PALETTE["line"], width=2.0, arrow=True)
    fig.line([(1225, 421), (1320, 550)], PALETTE["line"], width=2.0, arrow=True)

    fig.rect(1320, 675, 285, 92, PALETTE["asf"], PALETTE["asf_stroke"], width=1.5, r=16)
    fig.text(1345, 704, "Modulate ASF patch fusion", size=15, bold=True, fill=PALETTE["asf_deep"])
    fig.text(1345, 728, "K/V token scale, query delta,\nand fused-token residual", size=12, fill=PALETTE["muted"], line_spacing=1.25)
    fig.line([(1460, 587), (1460, 675)], PALETTE["asf_deep"], width=2.2, arrow=True, marker="arrow-blue")

    fig.rect(74, 740, 1130, 1, PALETTE["soft_line"], PALETTE["soft_line"], width=1, r=0)
    fig.text(78, 764, "Difference from DecAlign:", size=13, bold=True, fill=PALETTE["ours_deep"])
    fig.text(
        276,
        764,
        "we do not use decoupling only for final representation fusion; we use it to control availability-aware patch fusion.",
        size=13,
        fill=PALETTE["muted"],
    )

    fig.finish()
    print(f"Wrote {svg_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    draw_main()
    draw_detail()
