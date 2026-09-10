#!/usr/bin/env python3
"""Create paper-ready TaskDec visualization figures from exported patch states.

This script is deliberately diagnostic: it visualizes representation separation,
foreground gating, and conservative reliability readouts without implying that
the reliability head switches dominant sensors across weather.
"""

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WEATHER_ORDER = [
    "normal",
    "overcast",
    "fog",
    "rain",
    "sleet",
    "lightsnow",
    "heavysnow",
]
REP_WEATHERS = ["normal", "fog", "rain", "heavysnow"]
FEATURE_ORDER = ["raw", "common", "unique"]
FEATURE_TITLES = {
    "raw": "Canonical patch",
    "common": "Shared target state",
    "unique": "Sensor-specific state",
}
MODALITIES = ["Camera", "LiDAR", "4D Radar"]
COLORS = {
    "Camera": "#c5524f",
    "LiDAR": "#2f8f6b",
    "4D Radar": "#456cc2",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--npz", required=True, help="Path to taskdec_patch_states_pca.npz")
    parser.add_argument("--out-dir", required=True, help="Output figure directory")
    parser.add_argument("--max-per-modality", type=int, default=190)
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def ensure_out_dir(path):
    out_dir = Path(path)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def finite_limits(coords, qlo=1, qhi=99):
    lo = np.percentile(coords, qlo, axis=0)
    hi = np.percentile(coords, qhi, axis=0)
    span = np.maximum(hi - lo, 1e-6)
    pad = span * 0.08
    return lo - pad, hi + pad


def sample_indices(rng, mask, limit):
    indices = np.flatnonzero(mask)
    if indices.size <= limit:
        return indices
    return np.asarray(rng.choice(indices, size=limit, replace=False), dtype=np.int64)


def save_all(fig, out_dir, stem):
    paths = []
    for suffix, kwargs in [
        ("png", {"dpi": 320}),
        ("svg", {}),
        ("pdf", {}),
    ]:
        path = out_dir / f"{stem}.{suffix}"
        fig.savefig(path, bbox_inches="tight", **kwargs)
        paths.append(path)
    plt.close(fig)
    return paths


def plot_pca_grid(data, out_dir, stem, weathers, max_per_modality, seed):
    rng = np.random.default_rng(seed)
    fig, axes = plt.subplots(
        len(weathers),
        len(FEATURE_ORDER),
        figsize=(9.4, 2.15 * len(weathers) + 0.5),
        sharex=False,
        sharey=False,
    )
    if len(weathers) == 1:
        axes = np.asarray([axes])

    for col, feature in enumerate(FEATURE_ORDER):
        coords = data[f"{feature}_pca"]
        lo, hi = finite_limits(coords)
        weather_arr = data[f"{feature}_weather"].astype(str)
        modality_arr = data[f"{feature}_modality"].astype(str)
        fg_arr = data[f"{feature}_foreground"].astype(np.int64) == 1

        for row, weather in enumerate(weathers):
            ax = axes[row, col]
            for modality in MODALITIES:
                mask = (weather_arr == weather) & (modality_arr == modality) & fg_arr
                idx = sample_indices(rng, mask, max_per_modality)
                ax.scatter(
                    coords[idx, 0],
                    coords[idx, 1],
                    s=5,
                    c=COLORS[modality],
                    alpha=0.56,
                    linewidths=0,
                    label=modality if row == 0 and col == 0 else None,
                )
            ax.set_xlim(lo[0], hi[0])
            ax.set_ylim(lo[1], hi[1])
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(FEATURE_TITLES[feature], fontsize=10.8, fontweight="bold")
            if col == 0:
                ax.set_ylabel(weather, fontsize=9.5, rotation=0, labelpad=30, va="center")
            for spine in ax.spines.values():
                spine.set_color("#d7dce4")
                spine.set_linewidth(0.75)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, loc="upper center", frameon=False, bbox_to_anchor=(0.5, 1.025))
    fig.tight_layout(rect=(0.02, 0.0, 1.0, 0.985))
    return save_all(fig, out_dir, stem)


def read_distance_table(path):
    rows = []
    with Path(path).open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "weather": row["weather"],
                "feature": row["feature"],
                "mean_pair_distance": float(row["mean_pair_distance"]),
            })
    return rows


def read_reliability_table(path):
    rows = []
    with Path(path).open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = row.get("group", row.get("foreground_group"))
            gate = row.get("mean_gate", row.get("mean_fg_gate"))
            rows.append({
                "weather": row["weather"],
                "group": group,
                "modality": row["modality"],
                "mean_reliability": float(row["mean_reliability"]),
                "mean_gate": float(gate),
                "count": int(row["count"]),
            })
    return rows


def compute_distance_rows(data):
    from itertools import combinations

    rows = []
    for feature in FEATURE_ORDER:
        coords = data[f"{feature}_pca"]
        weather_arr = data[f"{feature}_weather"].astype(str)
        modality_arr = data[f"{feature}_modality"].astype(str)
        fg_arr = data[f"{feature}_foreground"].astype(np.int64) == 1
        for weather in WEATHER_ORDER:
            centroids = {}
            for modality in MODALITIES:
                mask = (weather_arr == weather) & (modality_arr == modality) & fg_arr
                if mask.sum() > 0:
                    centroids[modality] = coords[mask].mean(axis=0)
            distances = [
                float(np.linalg.norm(centroids[a] - centroids[b]))
                for a, b in combinations(MODALITIES, 2)
                if a in centroids and b in centroids
            ]
            if distances:
                rows.append({
                    "weather": weather,
                    "feature": feature,
                    "mean_pair_distance": float(np.mean(distances)),
                })
    return rows


def compute_reliability_rows(data):
    weather_arr = data["raw_weather"].astype(str)
    modality_arr = data["raw_modality"].astype(str)
    fg_arr = data["raw_foreground"].astype(np.int64) == 1
    rel_arr = data["raw_sensor_reliability"].astype(float)
    gate_arr = data["raw_fg_gate"].astype(float)
    rows = []
    for weather in WEATHER_ORDER:
        for group, mask_fg in [("fg", fg_arr), ("bg", ~fg_arr), ("all", np.ones_like(fg_arr, dtype=bool))]:
            for modality in MODALITIES:
                mask = (weather_arr == weather) & (modality_arr == modality) & mask_fg
                if mask.sum() == 0:
                    continue
                rows.append({
                    "weather": weather,
                    "group": group,
                    "modality": modality,
                    "mean_reliability": float(rel_arr[mask].mean()),
                    "mean_gate": float(gate_arr[mask].mean()),
                    "count": int(mask.sum()),
                })
    return rows


def plot_distance_and_gate(distance_rows, reliability_rows, out_dir):
    x = np.arange(len(WEATHER_ORDER))
    width = 0.24
    dist_map = {(row["feature"], row["weather"]): row["mean_pair_distance"] for row in distance_rows}
    rel_map = {
        (row["weather"], row["group"], row["modality"]): row
        for row in reliability_rows
    }

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.05))

    ax = axes[0]
    bar_colors = {"raw": "#777f8c", "common": "#2f8f6b", "unique": "#456cc2"}
    handles = []
    labels = []
    for idx, feature in enumerate(FEATURE_ORDER):
        values = [dist_map.get((feature, weather), np.nan) for weather in WEATHER_ORDER]
        handle = ax.bar(
            x + (idx - 1) * width,
            values,
            width=width,
            color=bar_colors[feature],
            label=FEATURE_TITLES[feature],
        )
        handles.append(handle)
        labels.append(FEATURE_TITLES[feature])
    ax.set_ylabel("Modality-centroid distance")
    ax.set_xticks(x)
    ax.set_xticklabels(WEATHER_ORDER, rotation=25, ha="right")
    ax.set_title("Representation decoupling", fontsize=10.8, fontweight="bold")
    ax.grid(axis="y", color="#e6e9ef", linewidth=0.8)

    ax = axes[1]
    fg_values = []
    bg_values = []
    for weather in WEATHER_ORDER:
        fg_mod = [rel_map[(weather, "fg", m)]["mean_gate"] for m in MODALITIES if (weather, "fg", m) in rel_map]
        bg_mod = [rel_map[(weather, "bg", m)]["mean_gate"] for m in MODALITIES if (weather, "bg", m) in rel_map]
        fg_values.append(float(np.mean(fg_mod)))
        bg_values.append(float(np.mean(bg_mod)))
    ax.plot(x, fg_values, marker="o", linewidth=2.0, color="#111827", label="foreground patches")
    ax.plot(x, bg_values, marker="o", linewidth=2.0, color="#9aa3af", label="background patches")
    ax.fill_between(x, bg_values, fg_values, color="#d8dee9", alpha=0.45, linewidth=0)
    ax.set_ylabel("Mean gate value")
    ax.set_xticks(x)
    ax.set_xticklabels(WEATHER_ORDER, rotation=25, ha="right")
    ax.set_title("Task-aware foreground gating", fontsize=10.8, fontweight="bold")
    ax.grid(axis="y", color="#e6e9ef", linewidth=0.8)
    ax.legend(frameon=False, fontsize=8.7)

    fig.legend(
        handles,
        labels,
        frameon=False,
        ncol=3,
        fontsize=8.8,
        loc="lower center",
        bbox_to_anchor=(0.29, -0.015),
    )
    fig.tight_layout(rect=(0.0, 0.08, 1.0, 1.0))
    return save_all(fig, out_dir, "paper_fig_taskdec_decoupling_and_gate")


def plot_controller_readout(reliability_rows, out_dir):
    rel_map = {
        (row["weather"], row["group"], row["modality"]): row["mean_reliability"]
        for row in reliability_rows
    }
    x = np.arange(len(WEATHER_ORDER))
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 3.65))

    lidar_values = np.asarray([rel_map.get((weather, "fg", "LiDAR"), np.nan) for weather in WEATHER_ORDER])
    ax = axes[0]
    ax.plot(x, lidar_values, marker="o", linewidth=2.0, color=COLORS["LiDAR"])
    ax.set_ylim(max(0.985, float(np.nanmin(lidar_values)) - 0.001), min(1.0, float(np.nanmax(lidar_values)) + 0.001))
    ax.set_ylabel("Mean reliability")
    ax.set_xticks(x)
    ax.set_xticklabels(WEATHER_ORDER, rotation=25, ha="right")
    ax.set_title("LiDAR readout", fontsize=10.6, fontweight="bold")
    ax.grid(axis="y", color="#e6e9ef", linewidth=0.8)

    ax = axes[1]
    for modality in ["Camera", "4D Radar"]:
        values = np.asarray([rel_map.get((weather, "fg", modality), np.nan) for weather in WEATHER_ORDER])
        ax.plot(x, values, marker="o", linewidth=2.0, color=COLORS[modality], label=modality)
    ax.set_ylabel("Mean reliability")
    ax.set_xticks(x)
    ax.set_xticklabels(WEATHER_ORDER, rotation=25, ha="right")
    ax.set_title("Auxiliary sensor readouts, zoomed", fontsize=10.6, fontweight="bold")
    ax.grid(axis="y", color="#e6e9ef", linewidth=0.8)
    ax.legend(frameon=False, ncol=2, fontsize=8.8)
    fig.suptitle("Controller reliability diagnostics", fontsize=12.0, fontweight="bold", y=1.03)
    fig.tight_layout()
    return save_all(fig, out_dir, "paper_fig_taskdec_reliability_readout")


def write_caption_note(out_dir):
    path = out_dir / "paper_visual_caption_notes.md"
    path.write_text(
        "\n".join([
            "# TaskDec Paper Visualization Notes",
            "",
            "Recommended main-text figure:",
            "",
            "- `paper_fig_taskdec_pca_representative.*`: compact PCA evidence that the shared target state aligns modalities while the sensor-specific state preserves modality-dependent variation.",
            "- `paper_fig_taskdec_decoupling_and_gate.*`: quantitative companion figure for modality-centroid distance and foreground gate response.",
            "",
            "Recommended appendix figure:",
            "",
            "- `paper_fig_taskdec_pca_all_weather_appendix.*`: all-weather PCA grid.",
            "- `paper_fig_taskdec_reliability_readout.*`: auxiliary controller readout. The reliability head is LiDAR-dominant in this checkpoint, so use this as a diagnostic rather than evidence of sensor switching.",
            "",
            "Safe wording:",
            "",
            "> The learned controller produces a compact modality-shared state and a separated modality-specific state across weather conditions. Foreground gates increase on task-relevant patches, while the reliability readout remains conservative and LiDAR-dominant in this checkpoint.",
            "",
        ]),
        encoding="utf-8",
    )
    return path


def main():
    args = parse_args()
    out_dir = ensure_out_dir(args.out_dir)
    data = np.load(args.npz, allow_pickle=True)
    export_dir = Path(args.npz).resolve().parent

    distance_csv = export_dir / "weather_pca_modality_distances.csv"
    reliability_csv = export_dir / "weather_sensor_reliability.csv"
    distance_rows = read_distance_table(distance_csv) if distance_csv.exists() else compute_distance_rows(data)
    reliability_rows = read_reliability_table(reliability_csv) if reliability_csv.exists() else compute_reliability_rows(data)

    outputs = []
    outputs.extend(plot_pca_grid(data, out_dir, "paper_fig_taskdec_pca_representative", REP_WEATHERS, args.max_per_modality, args.seed))
    outputs.extend(plot_pca_grid(data, out_dir, "paper_fig_taskdec_pca_all_weather_appendix", WEATHER_ORDER, args.max_per_modality, args.seed))
    outputs.extend(plot_distance_and_gate(distance_rows, reliability_rows, out_dir))
    outputs.extend(plot_controller_readout(reliability_rows, out_dir))
    outputs.append(write_caption_note(out_dir))

    print("Generated files:")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
