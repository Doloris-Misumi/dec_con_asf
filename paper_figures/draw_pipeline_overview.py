from __future__ import annotations

import html
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1800, 980
OUT_DIR = Path(__file__).resolve().parent
SVG_PATH = OUT_DIR / "task_dec_asf_pipeline_overview_v1.svg"
PNG_PATH = OUT_DIR / "task_dec_asf_pipeline_overview_v1.png"


PALETTE = {
    "bg": "#fbfbf8",
    "ink": "#17212b",
    "muted": "#607080",
    "line": "#7f8c99",
    "soft_line": "#d9e1e8",
    "asf": "#eaf3ff",
    "asf_stroke": "#4f86c6",
    "asf_deep": "#245f9e",
    "ours": "#eef9f3",
    "ours_stroke": "#2ca878",
    "ours_deep": "#0f7a55",
    "amber": "#fff1c9",
    "amber_stroke": "#d99a14",
    "rose": "#fff0f3",
    "rose_stroke": "#d65f7b",
    "lav": "#f2efff",
    "lav_stroke": "#7d6ad8",
    "gray": "#f2f4f7",
    "gray_stroke": "#a9b4bf",
    "white": "#ffffff",
}


FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def hex_to_rgb(color: str, alpha: int = 255):
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


class Figure:
    def __init__(self, width: int = W, height: int = H, svg_path: Path = SVG_PATH, png_path: Path = PNG_PATH):
        self.w = width
        self.h = height
        self.svg_path = Path(svg_path)
        self.png_path = Path(png_path)
        self.img = Image.new("RGBA", (self.w, self.h), hex_to_rgb(PALETTE["bg"]))
        self.draw = ImageDraw.Draw(self.img)
        self.svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">',
            "<defs>",
            '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
            '<feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#17212b" flood-opacity="0.08"/>',
            "</filter>",
            self._marker("arrow-ink", PALETTE["ink"]),
            self._marker("arrow-blue", PALETTE["asf_deep"]),
            self._marker("arrow-green", PALETTE["ours_deep"]),
            self._marker("arrow-amber", PALETTE["amber_stroke"]),
            self._marker("arrow-rose", PALETTE["rose_stroke"]),
            "</defs>",
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{PALETTE["bg"]}"/>',
        ]

    @staticmethod
    def _marker(marker_id: str, color: str) -> str:
        return (
            f'<marker id="{marker_id}" markerWidth="12" markerHeight="12" refX="10" refY="6" '
            'orient="auto" markerUnits="strokeWidth">'
            f'<path d="M2,2 L10,6 L2,10 Z" fill="{color}"/>'
            "</marker>"
        )

    def finish(self):
        self.svg.append("</svg>")
        self.svg_path.write_text("\n".join(self.svg), encoding="utf-8")
        self.img.convert("RGB").save(self.png_path, quality=95)

    def rect(self, x, y, w, h, fill, outline, width=2, r=18, shadow=False):
        r_int = int(round(r))
        width_int = int(round(width))
        if shadow:
            self.draw.rounded_rectangle(
                [x + 3, y + 4, x + w + 3, y + h + 4],
                radius=r_int,
                fill=hex_to_rgb("#000000", 14),
            )
        self.draw.rounded_rectangle(
            [x, y, x + w, y + h],
            radius=r_int,
            fill=hex_to_rgb(fill),
            outline=hex_to_rgb(outline),
            width=max(width_int, 1),
        )
        filter_attr = ' filter="url(#shadow)"' if shadow else ""
        self.svg.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" '
            f'fill="{fill}" stroke="{outline}" stroke-width="{width}"{filter_attr}/>'
        )

    def line(self, points, color, width=3, arrow=False, dash=None, marker="arrow-ink"):
        width_int = max(int(round(width)), 1)
        for a, b in zip(points[:-1], points[1:]):
            if dash:
                self._dashed_segment(a, b, color, width_int, dash)
            else:
                self.draw.line([a, b], fill=hex_to_rgb(color), width=width_int)
        if arrow:
            self._arrow_head(points[-2], points[-1], color, width_int)
        pts = " ".join(f"{x},{y}" for x, y in points)
        dash_attr = f' stroke-dasharray="{dash[0]} {dash[1]}"' if dash else ""
        marker_attr = f' marker-end="url(#{marker})"' if arrow else ""
        self.svg.append(
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"{dash_attr}{marker_attr}/>'
        )

    def _dashed_segment(self, a, b, color, width, dash):
        x1, y1 = a
        x2, y2 = b
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        ux, uy = dx / dist, dy / dist
        on, off = dash
        t = 0.0
        while t < dist:
            t2 = min(t + on, dist)
            p1 = (x1 + ux * t, y1 + uy * t)
            p2 = (x1 + ux * t2, y1 + uy * t2)
            self.draw.line([p1, p2], fill=hex_to_rgb(color), width=width)
            t += on + off

    def _arrow_head(self, a, b, color, width):
        ax, ay = a
        bx, by = b
        angle = math.atan2(by - ay, bx - ax)
        length = 13 + width
        spread = math.radians(25)
        p1 = (
            bx - length * math.cos(angle - spread),
            by - length * math.sin(angle - spread),
        )
        p2 = (
            bx - length * math.cos(angle + spread),
            by - length * math.sin(angle + spread),
        )
        self.draw.polygon([b, p1, p2], fill=hex_to_rgb(color))

    def text(
        self,
        x,
        y,
        value,
        size=18,
        fill=None,
        bold=False,
        anchor="la",
        align="left",
        line_spacing=1.15,
    ):
        fill = fill or PALETTE["ink"]
        fnt = font(size, bold=bold)
        lines = value.split("\n")
        line_h = int(size * line_spacing)
        total_h = line_h * (len(lines) - 1)
        start_y = y
        if "m" in anchor:
            start_y = y - total_h / 2
        for i, line in enumerate(lines):
            yy = start_y + i * line_h
            self.draw.text((x, yy), line, fill=hex_to_rgb(fill), font=fnt, anchor=anchor)
        if anchor.startswith("m"):
            text_anchor = "middle"
        elif anchor.startswith("r"):
            text_anchor = "end"
        else:
            text_anchor = "start"
        dominant = "middle" if len(anchor) > 1 and anchor[1] == "m" else "hanging"
        escaped = [html.escape(line) for line in lines]
        self.svg.append(
            f'<text x="{x}" y="{y}" fill="{fill}" font-family="DejaVu Sans, Arial, sans-serif" '
            f'font-size="{size}" font-weight="{"700" if bold else "400"}" '
            f'text-anchor="{text_anchor}" dominant-baseline="{dominant}">'
        )
        for i, line in enumerate(escaped):
            dy = "0" if i == 0 else f"{line_h}"
            self.svg.append(f'<tspan x="{x}" dy="{dy}">{line}</tspan>')
        self.svg.append("</text>")

    def pill(self, x, y, w, h, label, fill, outline, color=None, size=15, bold=False):
        self.rect(x, y, w, h, fill, outline, width=1.5, r=h / 2)
        self.text(x + w / 2, y + h / 2, label, size=size, fill=color or outline, bold=bold, anchor="mm")

    def circle(self, x, y, r, fill, outline=None, width=2):
        self.draw.ellipse(
            [x - r, y - r, x + r, y + r],
            fill=hex_to_rgb(fill),
            outline=hex_to_rgb(outline or fill),
            width=width,
        )
        self.svg.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" '
            f'stroke="{outline or fill}" stroke-width="{width}"/>'
        )

    def small_token_grid(self, x, y, cols, rows, cell, gap, fill, outline):
        for r in range(rows):
            for c in range(cols):
                xx = x + c * (cell + gap)
                yy = y + r * (cell + gap)
                self.rect(xx, yy, cell, cell, fill, outline, width=1, r=4)

    def mini_input(self, x, y, w, h, kind):
        self.rect(x, y, w, h, PALETTE["white"], PALETTE["soft_line"], width=1.5, r=12)
        if kind == "camera":
            self.draw.rectangle([x + 16, y + 14, x + w - 16, y + h - 16], fill=hex_to_rgb("#dceeff"))
            self.draw.polygon(
                [(x + 16, y + h - 16), (x + w - 16, y + h - 16), (x + w * 0.62, y + 45), (x + w * 0.38, y + 45)],
                fill=hex_to_rgb("#5f6974"),
            )
            self.draw.line([(x + w * 0.50, y + 45), (x + w * 0.50, y + h - 16)], fill=hex_to_rgb("#f7d05c"), width=4)
            self.draw.rectangle([x + 170, y + 39, x + 208, y + 66], outline=hex_to_rgb("#d99a14"), width=3)
            self.svg.append(f'<rect x="{x + 16}" y="{y + 14}" width="{w - 32}" height="{h - 30}" fill="#dceeff"/>')
            self.svg.append(
                f'<polygon points="{x + 16},{y + h - 16} {x + w - 16},{y + h - 16} {x + w * 0.62},{y + 45} {x + w * 0.38},{y + 45}" fill="#5f6974"/>'
            )
            self.svg.append(f'<line x1="{x + w * 0.50}" y1="{y + 45}" x2="{x + w * 0.50}" y2="{y + h - 16}" stroke="#f7d05c" stroke-width="4"/>')
            self.svg.append(f'<rect x="{x + 170}" y="{y + 39}" width="38" height="27" fill="none" stroke="#d99a14" stroke-width="3"/>')
        elif kind == "lidar":
            cx, cy = x + w / 2, y + h / 2
            for i in range(58):
                angle = i * 0.57
                rr = 12 + (i * 7) % 75
                px = cx + math.cos(angle) * rr
                py = cy + math.sin(angle) * rr * 0.55
                color = "#69a98d" if i % 3 else "#d99a14"
                self.circle(px, py, 2.4, color, color, width=1)
            self.draw.line([x + 24, y + h - 20, x + w - 24, y + h - 20], fill=hex_to_rgb("#8aa1b2"), width=2)
            self.svg.append(f'<line x1="{x + 24}" y1="{y + h - 20}" x2="{x + w - 24}" y2="{y + h - 20}" stroke="#8aa1b2" stroke-width="2"/>')
        elif kind == "radar":
            cx, cy = x + w / 2, y + h - 5
            for i, r in enumerate(range(28, 92, 8)):
                color = "#174f89" if i % 2 else "#1f9bd1"
                ry = r * 0.48
                self.draw.arc([cx - r, cy - ry, cx + r, cy + ry], 198, 342, fill=hex_to_rgb(color), width=3)
                start = math.radians(198)
                end = math.radians(342)
                sx, sy = cx + r * math.cos(start), cy + ry * math.sin(start)
                ex, ey = cx + r * math.cos(end), cy + ry * math.sin(end)
                self.svg.append(
                    f'<path d="M {sx:.1f},{sy:.1f} A {r},{ry:.1f} 0 0 1 {ex:.1f},{ey:.1f}" '
                    f'fill="none" stroke="{color}" stroke-width="3"/>'
                )
            for bx, by, bw, bh, col in [(x + 60, y + 32, 48, 24, "#ffd34d"), (x + 155, y + 41, 34, 18, "#f06275")]:
                self.draw.rectangle([bx, by, bx + bw, by + bh], outline=hex_to_rgb(col), width=3)
                self.svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="none" stroke="{col}" stroke-width="3"/>')
        else:
            raise ValueError(kind)


def draw_feature_map(fig: Figure, x, y, w, h, label, color):
    fig.rect(x, y, w, h, PALETTE["white"], PALETTE["soft_line"], width=1.5, r=10)
    for i in range(5):
        xx = x + 18 + i * 21
        fig.draw.line([(xx, y + 18), (xx + 50, y + h - 20)], fill=hex_to_rgb(color, 95), width=2)
        fig.svg.append(f'<line x1="{xx}" y1="{y + 18}" x2="{xx + 50}" y2="{y + h - 20}" stroke="{color}" stroke-opacity="0.37" stroke-width="2"/>')
    fig.text(x + w / 2, y + h - 18, label, size=13, fill=PALETTE["muted"], bold=True, anchor="mm")


def draw_detection_output(fig: Figure, x, y):
    fig.rect(x, y, 250, 112, PALETTE["white"], PALETTE["soft_line"], width=1.5, r=12)
    for gx in range(7):
        xx = x + 22 + gx * 28
        fig.draw.line([(xx, y + 18), (xx, y + 91)], fill=hex_to_rgb("#d9e1e8"), width=1)
        fig.svg.append(f'<line x1="{xx}" y1="{y + 18}" x2="{xx}" y2="{y + 91}" stroke="#d9e1e8" stroke-width="1"/>')
    for gy in range(4):
        yy = y + 22 + gy * 18
        fig.draw.line([(x + 18, yy), (x + 232, yy)], fill=hex_to_rgb("#d9e1e8"), width=1)
        fig.svg.append(f'<line x1="{x + 18}" y1="{yy}" x2="{x + 232}" y2="{yy}" stroke="#d9e1e8" stroke-width="1"/>')
    boxes = [
        [(x + 82, y + 54), (x + 132, y + 44), (x + 148, y + 64), (x + 98, y + 75)],
        [(x + 156, y + 30), (x + 200, y + 37), (x + 193, y + 58), (x + 149, y + 51)],
        [(x + 42, y + 74), (x + 78, y + 66), (x + 88, y + 82), (x + 52, y + 91)],
    ]
    for pts in boxes:
        fig.draw.line(pts + [pts[0]], fill=hex_to_rgb(PALETTE["amber_stroke"]), width=3)
        fig.svg.append(
            '<polyline points="{}" fill="none" stroke="{}" stroke-width="3"/>'.format(
                " ".join(f"{px},{py}" for px, py in pts + [pts[0]]),
                PALETTE["amber_stroke"],
            )
        )
    fig.text(x + 125, y + 100, "3D boxes", size=13, fill=PALETTE["muted"], bold=True, anchor="mm")


def main():
    fig = Figure()

    # Header
    fig.text(70, 42, "Task-aware Decoupled Control for ASF Sensor Fusion", size=34, bold=True)
    fig.text(
        72,
        86,
        "Shared target cues and modality-specific cues dynamically steer canonical patch-level fusion.",
        size=18,
        fill=PALETTE["muted"],
    )
    fig.pill(1395, 48, 250, 36, "Pipeline overview", PALETTE["white"], PALETTE["gray_stroke"], color=PALETTE["muted"], size=15)
    fig.pill(1660, 48, 78, 36, "ICLR", PALETTE["white"], PALETTE["gray_stroke"], color=PALETTE["muted"], size=15, bold=True)

    # Section labels
    fig.pill(70, 128, 250, 34, "1 Frozen sensor encoders", PALETTE["gray"], PALETTE["gray_stroke"], color=PALETTE["muted"], size=14)
    fig.pill(620, 128, 270, 34, "2 ASF canonical patch space", PALETTE["asf"], PALETTE["asf_stroke"], color=PALETTE["asf_deep"], size=14, bold=True)
    fig.pill(610, 628, 332, 34, "3 Ours: decoupled fusion control", PALETTE["ours"], PALETTE["ours_stroke"], color=PALETTE["ours_deep"], size=14, bold=True)
    fig.pill(1420, 128, 190, 34, "4 3D detection", PALETTE["gray"], PALETTE["gray_stroke"], color=PALETTE["muted"], size=14)

    # Inputs and frozen encoders
    rows = [
        ("Camera", "camera", 190, "#4f86c6"),
        ("LiDAR", "lidar", 330, "#2ca878"),
        ("4D Radar", "radar", 470, "#d99a14"),
    ]
    for name, kind, y, color in rows:
        fig.mini_input(70, y, 230, 94, kind)
        fig.text(185, y - 18, name, size=17, bold=True, anchor="mm")
        fig.line([(304, y + 47), (345, y + 47)], PALETTE["line"], width=3, arrow=True, marker="arrow-ink")
        fig.rect(352, y + 8, 205, 78, PALETTE["gray"], PALETTE["gray_stroke"], width=1.8, r=14)
        fig.text(454, y + 35, f"Frozen {name}", size=15, bold=True, anchor="mm")
        fig.text(454, y + 58, "backbone", size=13, fill=PALETTE["muted"], anchor="mm")

    # ASF container
    fig.rect(620, 170, 735, 425, PALETTE["asf"], PALETTE["asf_stroke"], width=2.2, r=22, shadow=True)
    fig.text(650, 197, "ASF Canonical Patch Fusion", size=22, bold=True, fill=PALETTE["asf_deep"])
    fig.text(650, 226, "To-Embed -> unified canonical projection -> aware-query MHA -> PFT", size=15, fill=PALETTE["muted"])
    fig.pill(1136, 190, 170, 34, "ASF baseline path", PALETTE["white"], PALETTE["asf_stroke"], color=PALETTE["asf_deep"], size=13, bold=True)

    token_y = [260, 365, 470]
    token_labels = ["cam patches", "lidar patches", "radar patches"]
    token_colors = ["#d9ebff", "#def5ea", "#fff0c7"]
    token_strokes = [PALETTE["asf_stroke"], PALETTE["ours_stroke"], PALETTE["amber_stroke"]]
    for idx, y in enumerate(token_y):
        fig.line([(558, rows[idx][2] + 47), (600, rows[idx][2] + 47), (705, y + 28), (740, y + 28)], PALETTE["line"], width=2.4, arrow=True, marker="arrow-ink")
        fig.rect(740, y, 104, 56, PALETTE["white"], PALETTE["soft_line"], width=1.6, r=12)
        fig.text(792, y + 20, "To-Embed", size=13, bold=True, anchor="mm")
        fig.text(792, y + 39, "dim 256", size=12, fill=PALETTE["muted"], anchor="mm")
        fig.line([(844, y + 28), (873, y + 28)], PALETTE["line"], width=2.4, arrow=True, marker="arrow-ink")
        fig.rect(875, y, 88, 56, PALETTE["white"], PALETTE["soft_line"], width=1.6, r=12)
        fig.text(919, y + 20, "UCP", size=13, bold=True, anchor="mm")
        fig.text(919, y + 39, "2x2", size=12, fill=PALETTE["muted"], anchor="mm")
        fig.line([(963, y + 28), (996, y + 28)], PALETTE["line"], width=2.4, arrow=True, marker="arrow-ink")
        fig.small_token_grid(1002, y - 3, cols=5, rows=3, cell=17, gap=5, fill=token_colors[idx], outline=token_strokes[idx])
        fig.text(1058, y + 64, token_labels[idx], size=12, fill=PALETTE["muted"], anchor="mm")
        fig.line([(1117, y + 25), (1158, 372)], PALETTE["asf_deep"], width=2.3, arrow=True, marker="arrow-blue")

    fig.rect(1030, 528, 208, 44, PALETTE["white"], PALETTE["asf_stroke"], width=1.7, r=22)
    fig.text(1134, 550, "learned aware query q_p", size=14, fill=PALETTE["asf_deep"], bold=True, anchor="mm")
    fig.line([(1134, 528), (1165, 430)], PALETTE["asf_deep"], width=2.2, arrow=True, marker="arrow-blue")

    fig.rect(1160, 328, 112, 86, PALETTE["white"], PALETTE["asf_stroke"], width=2, r=15)
    fig.text(1216, 359, "MHA", size=20, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(1216, 386, "patch K/V", size=13, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1272, 371), (1306, 371)], PALETTE["asf_deep"], width=2.6, arrow=True, marker="arrow-blue")
    fig.rect(1308, 333, 58, 76, PALETTE["white"], PALETTE["asf_stroke"], width=1.7, r=12)
    fig.text(1337, 359, "PFT", size=15, bold=True, fill=PALETTE["asf_deep"], anchor="mm")
    fig.text(1337, 384, "reshape", size=11, fill=PALETTE["muted"], anchor="mm")

    # Detection side
    fig.line([(1366, 371), (1420, 315)], PALETTE["asf_deep"], width=3, arrow=True, marker="arrow-blue")
    fig.rect(1420, 240, 280, 130, PALETTE["white"], PALETTE["gray_stroke"], width=1.8, r=16, shadow=True)
    fig.text(1560, 266, "Fused BEV feature", size=18, bold=True, anchor="mm")
    for i in range(6):
        fig.draw.line([(1447 + i * 36, 294), (1490 + i * 23, 342)], fill=hex_to_rgb("#4f86c6", 95), width=2)
        fig.svg.append(f'<line x1="{1447 + i * 36}" y1="294" x2="{1490 + i * 23}" y2="342" stroke="#4f86c6" stroke-opacity="0.37" stroke-width="2"/>')
    fig.line([(1560, 370), (1560, 423)], PALETTE["line"], width=3, arrow=True, marker="arrow-ink")
    fig.rect(1420, 424, 280, 100, PALETTE["gray"], PALETTE["gray_stroke"], width=1.8, r=16)
    fig.text(1560, 454, "Detection head", size=18, bold=True, anchor="mm")
    fig.text(1560, 482, "classification + 3D boxes", size=14, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1560, 524), (1560, 578)], PALETTE["line"], width=3, arrow=True, marker="arrow-ink")
    draw_detection_output(fig, 1435, 580)

    # Ours container
    fig.rect(610, 670, 795, 235, PALETTE["ours"], PALETTE["ours_stroke"], width=2.4, r=22, shadow=True)
    fig.text(640, 699, "Task-aware Decoupled Controller", size=22, bold=True, fill=PALETTE["ours_deep"])
    fig.text(640, 728, "Common target information and modality-specific evidence are used as control signals.", size=15, fill=PALETTE["muted"])

    fig.rect(645, 770, 150, 64, PALETTE["white"], PALETTE["ours_stroke"], width=1.6, r=14)
    fig.text(720, 792, "canonical patch", size=13, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(720, 813, "tokens z_m,p", size=13, fill=PALETTE["muted"], anchor="mm")
    fig.line([(720, 595), (720, 770)], PALETTE["ours_deep"], width=2.2, arrow=True, dash=(9, 7), marker="arrow-green")

    fig.line([(795, 802), (835, 802)], PALETTE["ours_deep"], width=2.6, arrow=True, marker="arrow-green")
    fig.rect(838, 742, 180, 120, PALETTE["white"], PALETTE["ours_stroke"], width=1.8, r=16)
    fig.text(928, 768, "Decouple", size=17, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.rect(860, 790, 64, 44, "#e2f6ec", PALETTE["ours_stroke"], width=1.3, r=11)
    fig.text(892, 807, "common", size=11, bold=True, fill=PALETTE["ours_deep"], anchor="mm")
    fig.text(892, 824, "c_m,p", size=11, fill=PALETTE["muted"], anchor="mm")
    fig.rect(934, 790, 64, 44, "#fff5d8", PALETTE["amber_stroke"], width=1.3, r=11)
    fig.text(966, 807, "unique", size=11, bold=True, fill=PALETTE["amber_stroke"], anchor="mm")
    fig.text(966, 824, "u_m,p", size=11, fill=PALETTE["muted"], anchor="mm")

    head_specs = [
        (1062, 742, "Foreground gate", "g_p", PALETTE["rose"], PALETTE["rose_stroke"], "arrow-rose"),
        (1062, 812, "Sensor reliability", "alpha_m,p", PALETTE["amber"], PALETTE["amber_stroke"], "arrow-amber"),
        (1240, 777, "Class context", "t_p", PALETTE["lav"], PALETTE["lav_stroke"], "arrow-green"),
    ]
    for x, y, title, sym, fill, stroke, marker in head_specs:
        fig.line([(1018, 802), (x, y + 28)], PALETTE["ours_deep"], width=2.3, arrow=True, marker="arrow-green")
        fig.rect(x, y, 150, 56, fill, stroke, width=1.6, r=14)
        fig.text(x + 75, y + 20, title, size=12, bold=True, fill=stroke, anchor="mm")
        fig.text(x + 75, y + 40, sym, size=13, fill=PALETTE["muted"], anchor="mm")

    fig.rect(1240, 840, 128, 38, PALETTE["white"], PALETTE["ours_stroke"], width=1.2, r=12)
    fig.text(1304, 859, "train-only GT loss", size=12, fill=PALETTE["muted"], anchor="mm")
    fig.line([(1304, 840), (1304, 812)], PALETTE["line"], width=1.6, arrow=True, dash=(6, 5), marker="arrow-ink")

    # Control feedback arrows
    fig.line([(1137, 812), (1137, 635), (1173, 421)], PALETTE["amber_stroke"], width=2.4, arrow=True, dash=(9, 7), marker="arrow-amber")
    fig.text(1122, 625, "scale K/V tokens", size=12, fill=PALETTE["amber_stroke"], bold=True, anchor="rm")
    fig.line([(1137, 742), (1088, 620), (1006, 486)], PALETTE["rose_stroke"], width=2.2, arrow=True, dash=(8, 7), marker="arrow-rose")
    fig.text(1000, 620, "gate residual", size=12, fill=PALETTE["rose_stroke"], bold=True, anchor="mm")
    fig.line([(1315, 777), (1315, 630), (1162, 528)], PALETTE["ours_deep"], width=2.4, arrow=True, dash=(9, 7), marker="arrow-green")
    fig.text(1330, 627, "query delta", size=12, fill=PALETTE["ours_deep"], bold=True, anchor="la")
    fig.line([(1315, 833), (1376, 803), (1376, 392), (1366, 392)], PALETTE["ours_deep"], width=2.4, arrow=True, dash=(9, 7), marker="arrow-green")
    fig.text(1385, 793, "fused delta", size=12, fill=PALETTE["ours_deep"], bold=True, anchor="la")

    # Short formula callout
    fig.rect(72, 690, 445, 190, PALETTE["white"], PALETTE["soft_line"], width=1.5, r=18)
    fig.text(98, 720, "Core idea", size=19, bold=True)
    fig.text(
        98,
        754,
        "Decompose each modality patch token,\nthen predict task-conditioned controls\nthat modulate ASF instead of replacing it.",
        size=15,
        fill=PALETTE["muted"],
        line_spacing=1.35,
    )
    fig.text(98, 842, "z'_m,p = scale(g_p, alpha_m,p) * (z_m,p + Delta(c_m,p, u_m,p))", size=13, fill=PALETTE["ink"])
    fig.text(98, 866, "q'_p = q_p + Delta q(t_p)", size=13, fill=PALETTE["ink"])

    # Legend
    fig.rect(72, 906, 1565, 1, PALETTE["soft_line"], PALETTE["soft_line"], width=0, r=0)
    fig.pill(84, 925, 112, 28, "ASF", PALETTE["asf"], PALETTE["asf_stroke"], color=PALETTE["asf_deep"], size=12, bold=True)
    fig.text(208, 930, "frozen encoders and canonical patch fusion are inherited from ASF", size=13, fill=PALETTE["muted"])
    fig.pill(610, 925, 112, 28, "Ours", PALETTE["ours"], PALETTE["ours_stroke"], color=PALETTE["ours_deep"], size=12, bold=True)
    fig.text(734, 930, "decoupled controller provides patch-wise gate, reliability, and task context", size=13, fill=PALETTE["muted"])
    fig.line([(1230, 940), (1320, 940)], PALETTE["ours_deep"], width=2.5, arrow=True, dash=(9, 7), marker="arrow-green")
    fig.text(1332, 930, "control signal", size=13, fill=PALETTE["muted"])

    fig.finish()
    print(f"Wrote {SVG_PATH}")
    print(f"Wrote {PNG_PATH}")


if __name__ == "__main__":
    main()
