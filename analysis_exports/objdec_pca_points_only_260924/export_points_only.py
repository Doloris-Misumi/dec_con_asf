#!/usr/bin/env python3
"""Export existing architecture PCA insets as larger, opaque points only."""
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / "tools/analysis"))
from plot_objdec_pca_260919 import selected_pairs, limits, MODALITIES, MARKERS
from objdec_plot_palette import MODALITY_COLORS

SOURCE = ROOT / "analysis_exports/taskdec_patch_pca_weather_260909/taskdec_patch_states_pca.npz"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    before = digest(SOURCE)
    fields = ["weather", "foreground", "modality", "frame_idx", "patch_idx"]
    with np.load(SOURCE) as archive:
        data = {"raw_" + field: archive["raw_" + field] for field in fields}
        for feature in ["common", "unique"]:
            for field in fields + ["pca"]:
                data[feature + "_" + field] = archive[feature + "_" + field]
    chosen = selected_pairs(data, "normal", 20260919)
    panels = {}
    plt.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42})
    for feature, label in [("common", "shared"), ("unique", "specific")]:
        xy = data[feature + "_pca"]
        mask = ((data[feature + "_foreground"] == 1)
                & (data[feature + "_weather"] == "normal"))
        lo, hi = limits(xy[mask])
        fig = plt.figure(figsize=(2.65, 2.1), facecolor="none")
        ax = fig.add_axes([0, 0, 1, 1], facecolor="none")
        selections = {}
        for modality, color, marker in zip(MODALITIES, MODALITY_COLORS, MARKERS):
            available = np.flatnonzero(mask & (data[feature + "_modality"] == modality))
            ids = np.array([int(k) for k in available if
                (int(data[feature + "_frame_idx"][k]),
                 int(data[feature + "_patch_idx"][k])) in chosen], dtype=np.int64)
            ax.scatter(*xy[ids].T, s=54, alpha=0.95, c=color, marker=marker,
                       edgecolors="white", linewidths=0.2)
            selections[modality] = {
                "count": len(ids),
                "source_indices": ids.tolist(),
                "coordinates_sha256": hashlib.sha256(xy[ids].tobytes()).hexdigest(),
            }
        ax.set(xlim=(lo[0], hi[0]), ylim=(lo[1], hi[1]))
        ax.set_aspect("equal", adjustable="box")
        ax.set_axis_off()
        fig.canvas.draw()
        bounds = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        stem = f"objdec_{label}_pca_normal_points_only"
        for suffix in ["png", "svg", "pdf"]:
            fig.savefig(OUT / f"{stem}.{suffix}", dpi=600, transparent=True,
                        bbox_inches=bounds, pad_inches=0.0)
        plt.close(fig)
        panels[label] = {"stem": stem, "selection": selections,
                         "xlim": [float(lo[0]), float(hi[0])],
                         "ylim": [float(lo[1]), float(hi[1])]}
    assert digest(SOURCE) == before
    record = {
        "source": str(SOURCE), "source_sha256": before,
        "source_unchanged": True, "pca_refitted": False,
        "scope": "Same selected local foreground patches as the normal-weather architecture insets, not full-test frame means.",
        "style": {"old_marker_area_pt2": 18, "marker_area_pt2": 54,
                  "old_alpha": 0.72, "alpha": 0.95,
                  "background": "transparent", "axes": False,
                  "text": False, "legend": False, "png_dpi": 600,
                  "colors": dict(zip(MODALITIES, MODALITY_COLORS))},
        "panels": panels,
    }
    (OUT / "manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    (OUT / "README.md").write_text(
        "# ObjDec：架构图用纯散点PCA素材\n\n"
        "沿用正常天气的局部前景patch PCA坐标与原有固定抽样，未重新拟合或移动点。\n"
        "点面积由18增至54 pt²（3倍），不透明度由0.72增至0.95。\n"
        "Camera蓝圆点、LiDAR绿三角、4D Radar紫方块；无坐标轴、文字、边框或图例。\n"
        "每张提供600 dpi透明PNG及矢量SVG/PDF；PPT优先使用SVG。\n\n"
        "- Shared：`objdec_shared_pca_normal_points_only.*`\n"
        "- Specific：`objdec_specific_pca_normal_points_only.*`\n\n"
        "两分支沿用各自的PCA基及显示范围，不据跨图视觉距离计算对齐幅度。\n"
        "重跑：用rl_3dod环境Python执行本目录export_points_only.py，仅CPU绘图。\n"
    )
    print(json.dumps({"output": str(OUT), "source_unchanged": True,
                      "points_per_panel": {k: {m: v["count"] for m, v in p["selection"].items()}
                                           for k, p in panels.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
