#!/usr/bin/env python3
"""Editable concept diagrams for ObjDec; no experimental/PCA data are plotted."""
import json
from pathlib import Path
from xml.sax.saxutils import quoteattr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch, Polygon
from matplotlib.path import Path as MplPath

OUT = Path(__file__).resolve().parent
WIDTH_MM, HEIGHT_MM = 41.7, 32.0
COLORS = ["#4A9EEB", "#58B77A", "#9672D0"]
ARROW = "#667085"
STROKE_MM = 0.28


def circle(x, y, radius, color, role):
    return dict(kind="circle", x=x, y=y, r=radius, fill=color,
                stroke="#FFFFFF", stroke_width=STROKE_MM, role=role)


def triplet(cx, cy, radius, color, role, spread_x=1.9, spread_y=2.1):
    return [circle(cx, cy-spread_y, radius, color, role),
            circle(cx-spread_x, cy+spread_y/2, radius, color, role),
            circle(cx+spread_x, cy+spread_y/2, radius, color, role)]


def shared_scene():
    scene = [
        dict(kind="path", points=[(10.9, 6.4), (14.6, 6.4), (14.8, 14.2), (19.7, 16.0)],
             codes=[MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4],
             d="M 10.9 6.4 C 14.6 6.4 14.8 14.2 19.7 16", role="converging_arrow"),
        dict(kind="path", points=[(10.9, 25.6), (14.6, 25.6), (14.8, 17.8), (19.7, 16.0)],
             codes=[MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4],
             d="M 10.9 25.6 C 14.6 25.6 14.8 17.8 19.7 16", role="converging_arrow"),
        dict(kind="path", points=[(10.9, 16.0), (19.7, 16.0)],
             codes=[MplPath.MOVETO, MplPath.LINETO],
             d="M 10.9 16 L 19.7 16", role="converging_arrow"),
        dict(kind="polygon", points=[(22.0, 16), (18.85, 14.05), (18.85, 17.95)],
             fill=ARROW, role="arrowhead"),
    ]
    for y, color in zip([6.4, 16.0, 25.6], COLORS):
        scene += triplet(6.4, y, 1.92, color, "input_cluster", 1.75, 1.9)
    # Equal counts of all three modalities, interspersed in one compact cluster.
    arrangement = [[0, 1, 2], [2, 0, 1], [1, 2, 0]]
    for row in range(3):
        for col in range(3):
            scene.append(circle(30.1+(col-1)*4.10, 16+(row-1)*4.10,
                                2.44, COLORS[arrangement[row][col]], "aligned_cluster"))
    return scene


def specific_scene():
    scene = []
    # The three clouds are separated spatially, rather than connected by a curve.
    for (cx, cy), color in zip([(7.1, 10.0), (20.85, 23.0), (34.6, 10.0)], COLORS):
        scene += triplet(cx, cy, 2.62, color, "separated_cluster", 1.9, 2.05)
    return scene


def svg_fragment(scene, dx=0, dy=0):
    lines = [f'<g transform="translate({dx} {dy})">']
    for item in scene:
        role = quoteattr(item["role"])
        if item["kind"] == "circle":
            lines.append(f'<circle cx="{item["x"]:.4f}" cy="{item["y"]:.4f}" '
                         f'r="{item["r"]:.4f}" fill="{item["fill"]}" stroke="{item["stroke"]}" '
                         f'stroke-width="{item["stroke_width"]}" data-role={role}/>')
        elif item["kind"] == "path":
            lines.append(f'<path d="{item["d"]}" fill="none" stroke="{ARROW}" '
                         f'stroke-width="0.78" stroke-linecap="round" data-role={role}/>')
        else:
            xy = " ".join(f'{x},{y}' for x, y in item["points"])
            lines.append(f'<polygon points="{xy}" fill="{item["fill"]}" data-role={role}/>')
    return "\n".join(lines+["</g>"])


def draw(ax, scene, dx=0, dy=0):
    # Axes coordinates are millimeters; linewidths in Matplotlib are points.
    to_pt = 72/25.4
    for item in scene:
        if item["kind"] == "circle":
            ax.add_patch(Circle((item["x"]+dx, item["y"]+dy), item["r"],
                                facecolor=item["fill"], edgecolor=item["stroke"],
                                linewidth=item["stroke_width"]*to_pt))
        elif item["kind"] == "path":
            path = MplPath([(x+dx, y+dy) for x, y in item["points"]], item["codes"])
            ax.add_patch(PathPatch(path, facecolor="none", edgecolor=ARROW,
                                   linewidth=0.78*to_pt, capstyle="round"))
        else:
            ax.add_patch(Polygon([(x+dx, y+dy) for x, y in item["points"]],
                                 closed=True, facecolor=item["fill"], edgecolor="none"))


def export(stem, panels, width_mm, height_mm):
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" '
           f'height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}">\n')
    svg += "\n".join(svg_fragment(scene, dx, dy) for scene, dx, dy in panels)
    (OUT/f"{stem}.svg").write_text(svg+"\n</svg>\n")
    fig = plt.figure(figsize=(width_mm/25.4, height_mm/25.4), facecolor="none")
    ax = fig.add_axes([0, 0, 1, 1], facecolor="none")
    ax.set(xlim=(0, width_mm), ylim=(height_mm, 0))
    ax.set_aspect("equal")
    ax.set_axis_off()
    for scene, dx, dy in panels:
        draw(ax, scene, dx, dy)
    for suffix in ["pdf", "png"]:
        fig.savefig(OUT/f"{stem}.{suffix}", dpi=600, transparent=True,
                    pad_inches=0, bbox_inches=None)
    plt.close(fig)


def main():
    shared, specific = shared_scene(), specific_scene()
    for item in shared:
        if "codes" in item:
            item["codes"] = [int(code) for code in item["codes"]]
    export("objdec_shared_aligned_no_text", [(shared, 0, 0)], WIDTH_MM, HEIGHT_MM)
    export("objdec_specific_separated_no_text", [(specific, 0, 0)], WIDTH_MM, HEIGHT_MM)
    export("objdec_shared_specific_side_by_side_no_text",
           [(shared, 0, 0), (specific, WIDTH_MM+4, 0)], WIDTH_MM*2+4, HEIGHT_MM)
    manifest = {
        "type": "conceptual architecture illustration, not empirical PCA",
        "individual_canvas_cm": [WIDTH_MM/10, HEIGHT_MM/10],
        "visible_text": False, "axes": False, "legend": False,
        "background": "transparent", "opacity": 1.0,
        "colors": dict(zip(["Camera", "LiDAR", "4D Radar"], COLORS)),
        "shared": {"input_points_per_modality": 3, "output_points_per_modality": 3,
                   "output_marker_outer_diameter_mm": 2*2.44+STROKE_MM,
                   "scene": shared},
        "specific": {"points_per_modality": 3,
                     "marker_outer_diameter_mm": 2*2.62+STROKE_MM,
                     "scene": specific},
        "reference_full_artboard_width_cm": 56,
        "example_17_8cm_print_width": {
            "scale_factor": 17.8/56,
            "inset_width_cm": WIDTH_MM/10*17.8/56,
            "shared_output_marker_mm": (2*2.44+STROKE_MM)*17.8/56,
            "specific_marker_mm": (2*2.62+STROKE_MM)*17.8/56},
    }
    (OUT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({k:v for k,v in manifest.items() if k not in ["shared", "specific"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
