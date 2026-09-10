#!/usr/bin/env python3
"""Plot weather-aware TaskDec PCA summaries from exported patch states."""

import argparse
import csv
from collections import defaultdict
from itertools import combinations
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

FEATURE_ORDER = ["raw", "common", "unique"]
FEATURE_TITLES = {
    "raw": "Raw canonical",
    "common": "Common state",
    "unique": "Unique state",
}
MODALITIES = ["Camera", "LiDAR", "4D Radar"]
COLORS = {
    "Camera": "#d65f5f",
    "LiDAR": "#3f9b72",
    "4D Radar": "#5276d7",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--npz", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-per-modality", type=int, default=220)
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def ensure_out_dir(path):
    out_dir = Path(path)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def finite_limits(coords):
    lo = np.percentile(coords, 1, axis=0)
    hi = np.percentile(coords, 99, axis=0)
    span = np.maximum(hi - lo, 1.0e-6)
    pad = span * 0.08
    return lo - pad, hi + pad


def sample_indices(rng, mask, limit):
    indices = np.flatnonzero(mask)
    if indices.size <= limit:
        return indices
    return np.asarray(rng.choice(indices, size=limit, replace=False), dtype=np.int64)


def savefig(fig, out_dir, stem):
    png_path = out_dir / f"{stem}.png"
    svg_path = out_dir / f"{stem}.svg"
    fig.savefig(png_path, dpi=240, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, svg_path


def plot_pca_grid(data, out_dir, max_per_modality, seed):
    rng = np.random.default_rng(seed)
    fig, axes = plt.subplots(
        len(WEATHER_ORDER),
        len(FEATURE_ORDER),
        figsize=(12.2, 16.4),
        sharex=False,
        sharey=False,
    )
    for col, feature in enumerate(FEATURE_ORDER):
        coords = data[f"{feature}_pca"]
        lo, hi = finite_limits(coords)
        for row, weather in enumerate(WEATHER_ORDER):
            ax = axes[row, col]
            weather_arr = data[f"{feature}_weather"].astype(str)
            modality_arr = data[f"{feature}_modality"].astype(str)
            fg_arr = data[f"{feature}_foreground"].astype(np.int64) == 1
            for modality in MODALITIES:
                mask = (weather_arr == weather) & (modality_arr == modality) & fg_arr
                idx = sample_indices(rng, mask, max_per_modality)
                ax.scatter(
                    coords[idx, 0],
                    coords[idx, 1],
                    s=4,
                    c=COLORS[modality],
                    alpha=0.58,
                    linewidths=0,
                    label=modality if row == 0 and col == 0 else None,
                )
            ax.set_xlim(lo[0], hi[0])
            ax.set_ylim(lo[1], hi[1])
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(FEATURE_TITLES[feature], fontsize=12, fontweight="bold")
            if col == 0:
                ax.set_ylabel(weather, fontsize=10, rotation=0, labelpad=33, va="center")
            for spine in ax.spines.values():
                spine.set_color("#d5dae3")
                spine.set_linewidth(0.8)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, loc="upper center", frameon=False, bbox_to_anchor=(0.5, 0.996))
    fig.suptitle("TaskDec patch-state PCA by weather, foreground patches", y=1.014, fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0.02, 0.0, 1.0, 0.985))
    return savefig(fig, out_dir, "taskdec_weather_pca_foreground_grid")


def reliability_rows(data):
    meta = {
        "weather": data["raw_weather"].astype(str),
        "modality": data["raw_modality"].astype(str),
        "fg": data["raw_foreground"].astype(np.int64) == 1,
        "gate": data["raw_fg_gate"].astype(float),
        "rel": data["raw_sensor_reliability"].astype(float),
    }
    rows = {}
    for weather in WEATHER_ORDER:
        for fg_name, fg_mask in [
            ("fg", meta["fg"]),
            ("bg", ~meta["fg"]),
            ("all", np.ones_like(meta["fg"], dtype=bool)),
        ]:
            for modality in MODALITIES:
                mask = (meta["weather"] == weather) & (meta["modality"] == modality) & fg_mask
                if mask.sum() == 0:
                    continue
                rows[(weather, fg_name, modality)] = {
                    "rel": float(np.mean(meta["rel"][mask])),
                    "gate": float(np.mean(meta["gate"][mask])),
                    "count": int(mask.sum()),
                }
    return rows


def plot_reliability_gate(data, out_dir):
    rows = reliability_rows(data)
    x = np.arange(len(WEATHER_ORDER))
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.2))

    ax = axes[0]
    for modality in MODALITIES:
        y = [rows.get((w, "fg", modality), {}).get("rel", np.nan) for w in WEATHER_ORDER]
        ax.plot(x, y, marker="o", linewidth=1.7, color=COLORS[modality], label=modality)
    ax.set_xticks(x)
    ax.set_xticklabels(WEATHER_ORDER, rotation=25, ha="right")
    ax.set_ylim(-0.02, 1.03)
    ax.set_ylabel("Mean reliability")
    ax.set_title("Foreground sensor reliability")
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.legend(frameon=False)

    ax = axes[1]
    for fg_name, color, label in [("fg", "#111827", "foreground"), ("bg", "#9ca3af", "background")]:
        values = []
        for weather in WEATHER_ORDER:
            weather_values = [
                rows.get((weather, fg_name, modality), {}).get("gate", np.nan)
                for modality in MODALITIES
            ]
            values.append(np.nanmean(weather_values))
        ax.plot(x, values, marker="o", linewidth=1.9, color=color, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels(WEATHER_ORDER, rotation=25, ha="right")
    ax.set_ylabel("Mean foreground gate")
    ax.set_title("Gate response by weather")
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.legend(frameon=False)

    fig.tight_layout()
    return savefig(fig, out_dir, "taskdec_weather_reliability_gate")


def centroid_distance_rows(data):
    rows = []
    for feature in FEATURE_ORDER:
        coords = data[f"{feature}_pca"]
        weather_arr = data[f"{feature}_weather"].astype(str)
        modality_arr = data[f"{feature}_modality"].astype(str)
        fg_arr = data[f"{feature}_foreground"].astype(np.int64) == 1
        for weather in WEATHER_ORDER:
            centroids = {}
            counts = {}
            for modality in MODALITIES:
                mask = (weather_arr == weather) & (modality_arr == modality) & fg_arr
                if mask.sum() == 0:
                    continue
                centroids[modality] = coords[mask].mean(axis=0)
                counts[modality] = int(mask.sum())
            distances = {}
            for a, b in combinations(MODALITIES, 2):
                if a in centroids and b in centroids:
                    distances[f"{a}-{b}"] = float(np.linalg.norm(centroids[a] - centroids[b]))
            if distances:
                rows.append({
                    "feature": feature,
                    "weather": weather,
                    "mean_pair_distance": float(np.mean(list(distances.values()))),
                    "max_pair_distance": float(np.max(list(distances.values()))),
                    "counts": counts,
                    **distances,
                })
    return rows


def plot_centroid_distances(rows, out_dir):
    x = np.arange(len(WEATHER_ORDER))
    width = 0.24
    fig, ax = plt.subplots(figsize=(10.2, 4.3))
    colors = {"raw": "#6b7280", "common": "#10b981", "unique": "#6366f1"}
    row_map = {(row["feature"], row["weather"]): row for row in rows}
    for i, feature in enumerate(FEATURE_ORDER):
        y = [row_map[(feature, w)]["mean_pair_distance"] for w in WEATHER_ORDER]
        ax.bar(x + (i - 1) * width, y, width=width, color=colors[feature], label=FEATURE_TITLES[feature])
    ax.set_xticks(x)
    ax.set_xticklabels(WEATHER_ORDER, rotation=25, ha="right")
    ax.set_ylabel("Mean modality-centroid distance in PCA")
    ax.set_title("Common states align sensors; unique states preserve sensor-specific variation")
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.legend(frameon=False, ncol=3)
    fig.tight_layout()
    return savefig(fig, out_dir, "taskdec_weather_modality_centroid_distance")


def write_tables(data, out_dir):
    rel = reliability_rows(data)
    dist = centroid_distance_rows(data)

    dist_csv = out_dir / "weather_pca_modality_distances.csv"
    fieldnames = [
        "weather",
        "feature",
        "mean_pair_distance",
        "max_pair_distance",
        "Camera-LiDAR",
        "Camera-4D Radar",
        "LiDAR-4D Radar",
    ]
    with dist_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in dist:
            writer.writerow({
                key: f"{row[key]:.7g}" if isinstance(row.get(key), float) else row.get(key, "")
                for key in fieldnames
            })

    md_path = out_dir / "pca_weather_analysis.md"
    lines = [
        "# TaskDec Weather PCA Analysis",
        "",
        "Export: weather-balanced foreground/background patch sample.",
        "",
        "## PCA Explained Variance",
        "",
        "| Feature | PC1 | PC2 |",
        "|---|---:|---:|",
    ]
    for feature in FEATURE_ORDER:
        ratio = data[f"{feature}_pca_explained"] * 100.0
        lines.append(f"| {feature} | {ratio[0]:.2f}% | {ratio[1]:.2f}% |")

    lines.extend([
        "",
        "## Foreground Gate By Weather",
        "",
        "| Weather | Gate fg | Gate bg | Delta |",
        "|---|---:|---:|---:|",
    ])
    for weather in WEATHER_ORDER:
        fg_values = [rel.get((weather, "fg", m), {}).get("gate", np.nan) for m in MODALITIES]
        bg_values = [rel.get((weather, "bg", m), {}).get("gate", np.nan) for m in MODALITIES]
        fg_mean = float(np.nanmean(fg_values))
        bg_mean = float(np.nanmean(bg_values))
        lines.append(f"| {weather} | {fg_mean:.4f} | {bg_mean:.4f} | {fg_mean - bg_mean:.4f} |")

    lines.extend([
        "",
        "## Mean Modality-Centroid Distance",
        "",
        "| Weather | Raw | Common | Unique |",
        "|---|---:|---:|---:|",
    ])
    row_map = {(row["feature"], row["weather"]): row for row in dist}
    for weather in WEATHER_ORDER:
        vals = [row_map[(feature, weather)]["mean_pair_distance"] for feature in FEATURE_ORDER]
        lines.append(f"| {weather} | {vals[0]:.2f} | {vals[1]:.2f} | {vals[2]:.2f} |")

    ranked_common = sorted(
        [row for row in dist if row["feature"] == "common"],
        key=lambda row: row["mean_pair_distance"],
        reverse=True,
    )
    ranked_unique = sorted(
        [row for row in dist if row["feature"] == "unique"],
        key=lambda row: row["mean_pair_distance"],
        reverse=True,
    )
    lines.extend([
        "",
        "## Suggested Figure Choices",
        "",
        f"- Largest common-state sensor spread: `{ranked_common[0]['weather']}` ({ranked_common[0]['mean_pair_distance']:.2f}).",
        f"- Largest unique-state sensor spread: `{ranked_unique[0]['weather']}` ({ranked_unique[0]['mean_pair_distance']:.2f}).",
        "- In this checkpoint, the learned reliability is strongly LiDAR-dominant across all weather groups, so PCA/centroid-distance plots are more informative than reliability bars for showing sensor-specific structure.",
    ])
    md_path.write_text("\n".join(lines))
    return md_path, dist_csv


def main():
    args = parse_args()
    out_dir = ensure_out_dir(args.out_dir)
    data = np.load(args.npz)

    pca_png, pca_svg = plot_pca_grid(data, out_dir, args.max_per_modality, args.seed)
    rel_png, rel_svg = plot_reliability_gate(data, out_dir)
    dist_rows = centroid_distance_rows(data)
    dist_png, dist_svg = plot_centroid_distances(dist_rows, out_dir)
    md_path, dist_csv = write_tables(data, out_dir)

    print(f"PCA grid PNG: {pca_png}")
    print(f"PCA grid SVG: {pca_svg}")
    print(f"Reliability/gate PNG: {rel_png}")
    print(f"Reliability/gate SVG: {rel_svg}")
    print(f"Centroid distance PNG: {dist_png}")
    print(f"Centroid distance SVG: {dist_svg}")
    print(f"Analysis MD: {md_path}")
    print(f"Distance CSV: {dist_csv}")


if __name__ == "__main__":
    main()
