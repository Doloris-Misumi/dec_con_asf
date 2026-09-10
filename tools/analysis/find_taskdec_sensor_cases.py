#!/usr/bin/env python3
"""Find TaskDec samples with non-default sensor reliability patterns.

The PCA export stores one record per sampled patch and modality. This script
reconstructs C/L/R reliability triplets for each patch, then ranks patch-level
and frame-level candidates such as radar-heavy, camera-heavy, balanced, and
large foreground-gate-response samples.
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

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

MODS = ["C", "L", "R"]
MOD_NAMES = {
    "C": "Camera",
    "L": "LiDAR",
    "R": "4D Radar",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--npz",
        default="analysis_exports/taskdec_patch_pca_weather_260909/taskdec_patch_states_pca.npz",
    )
    parser.add_argument(
        "--out-dir",
        default="analysis_exports/taskdec_patch_pca_weather_260909",
    )
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def entropy_score(values):
    values = np.asarray(values, dtype=np.float64)
    values = values / max(float(np.sum(values)), 1.0e-12)
    return float(-(values * np.log(values + 1.0e-12)).sum() / np.log(values.size))


def balance_score(values):
    values = np.asarray(values, dtype=np.float64)
    return float(1.0 - (np.max(values) - np.min(values)))


def finite_mean(values):
    values = [float(value) for value in values if np.isfinite(float(value))]
    return float(np.mean(values)) if values else np.nan


def finite_max(values):
    values = [float(value) for value in values if np.isfinite(float(value))]
    return float(np.max(values)) if values else np.nan


def float_fmt(value):
    return f"{float(value):.6f}"


def load_patch_triplets(npz_path):
    data = np.load(npz_path, allow_pickle=True)
    frame_idx = data["raw_frame_idx"]
    seq = data["raw_seq"]
    sample_id = data["raw_sample_id"]
    weather = data["raw_weather"]
    patch_idx = data["raw_patch_idx"]
    fg = data["raw_foreground"]
    modality = data["raw_modality_short"]
    rel = data["raw_sensor_reliability"]
    gate = data["raw_fg_gate"]
    available_mods = [mod for mod in MODS if np.any(modality == mod)]

    grouped = defaultdict(dict)
    gate_values = defaultdict(list)
    for i in range(rel.shape[0]):
        key = (
            int(frame_idx[i]),
            str(seq[i]),
            str(sample_id[i]),
            str(weather[i]),
            int(patch_idx[i]),
            int(fg[i]),
        )
        grouped[key][str(modality[i])] = float(rel[i])
        gate_values[key].append(float(gate[i]))

    rows = []
    for key, values in grouped.items():
        if not all(mod in values for mod in available_mods):
            continue
        rel_values = np.asarray([values[mod] for mod in available_mods], dtype=np.float64)
        dominant_idx = int(np.argmax(rel_values))
        top2 = np.sort(rel_values)[-2:]
        margin = float(top2[-1] - top2[-2]) if top2.shape[0] >= 2 else 0.0
        rows.append({
            "frame_idx": key[0],
            "seq": key[1],
            "sample_id": key[2],
            "weather": key[3],
            "patch_idx": key[4],
            "foreground": key[5],
            "camera": values.get("C", np.nan),
            "lidar": values.get("L", np.nan),
            "radar": values.get("R", np.nan),
            "dominant": available_mods[dominant_idx],
            "dominant_name": MOD_NAMES[available_mods[dominant_idx]],
            "dominant_value": float(rel_values[dominant_idx]),
            "dominance_margin": margin,
            "entropy": entropy_score(rel_values),
            "balance_score": balance_score(rel_values),
            "fg_gate": float(np.mean(gate_values[key])),
        })
    return rows


def summarize_frames(patch_rows):
    grouped = defaultdict(list)
    for row in patch_rows:
        key = (
            row["frame_idx"],
            row["seq"],
            row["sample_id"],
            row["weather"],
        )
        grouped[key].append(row)

    rows = []
    for key, patches in grouped.items():
        fg_patches = [row for row in patches if row["foreground"] == 1]
        bg_patches = [row for row in patches if row["foreground"] == 0]
        main = fg_patches if fg_patches else patches
        means = {
            "camera_mean": finite_mean([row["camera"] for row in main]),
            "lidar_mean": finite_mean([row["lidar"] for row in main]),
            "radar_mean": finite_mean([row["radar"] for row in main]),
            "entropy_mean": finite_mean([row["entropy"] for row in main]),
            "balance_score_mean": finite_mean([row["balance_score"] for row in main]),
            "fg_gate_mean": finite_mean([row["fg_gate"] for row in fg_patches]) if fg_patches else np.nan,
            "bg_gate_mean": finite_mean([row["fg_gate"] for row in bg_patches]) if bg_patches else np.nan,
        }
        finite_rel = [
            (mod, means[f"{MOD_NAMES[mod].lower().replace('4d ', '').replace(' ', '_')}_mean"])
            for mod in MODS
            if np.isfinite(means[f"{MOD_NAMES[mod].lower().replace('4d ', '').replace(' ', '_')}_mean"])
        ]
        finite_rel.sort(key=lambda item: item[1], reverse=True)
        dominant = finite_rel[0][0] if finite_rel else "unknown"
        dominant_value = finite_rel[0][1] if finite_rel else np.nan
        dominance_margin = finite_rel[0][1] - finite_rel[1][1] if len(finite_rel) >= 2 else 0.0
        fg_gate_delta = (
            means["fg_gate_mean"] - means["bg_gate_mean"]
            if np.isfinite(means["fg_gate_mean"]) and np.isfinite(means["bg_gate_mean"])
            else np.nan
        )
        rows.append({
            "frame_idx": key[0],
            "seq": key[1],
            "sample_id": key[2],
            "weather": key[3],
            "num_fg_patches": len(fg_patches),
            "num_bg_patches": len(bg_patches),
            "dominant": dominant,
            "dominant_name": MOD_NAMES.get(dominant, dominant),
            "dominant_value": float(dominant_value),
            "dominance_margin": float(dominance_margin),
            "fg_gate_delta": float(fg_gate_delta) if np.isfinite(fg_gate_delta) else np.nan,
            **means,
        })
    return rows


def write_csv(path, rows, fields):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            formatted = {}
            for field in fields:
                value = row.get(field, "")
                if isinstance(value, float):
                    formatted[field] = float_fmt(value) if np.isfinite(value) else ""
                else:
                    formatted[field] = value
            writer.writerow(formatted)


def top_by(rows, key, top_k, reverse=True, foreground_only=False, weather=None):
    selected = rows
    if foreground_only:
        selected = [row for row in selected if row.get("foreground", 1) == 1]
    if weather is not None:
        selected = [row for row in selected if row["weather"] == weather]
    selected = [row for row in selected if np.isfinite(float(row[key]))]
    return sorted(selected, key=lambda row: row[key], reverse=reverse)[:top_k]


def markdown_table(rows, fields):
    if not rows:
        return "_No candidates found._\n"
    lines = []
    lines.append("| " + " | ".join(fields) + " |")
    lines.append("|" + "|".join(["---"] * len(fields)) + "|")
    for row in rows:
        values = []
        for field in fields:
            value = row.get(field, "")
            if isinstance(value, float):
                value = float_fmt(value) if np.isfinite(value) else ""
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_summary(path, patch_rows, frame_rows, top_k):
    patch_fields = [
        "seq",
        "sample_id",
        "weather",
        "patch_idx",
        "foreground",
        "camera",
        "lidar",
        "radar",
        "dominant",
        "dominance_margin",
        "entropy",
        "fg_gate",
    ]
    frame_fields = [
        "seq",
        "sample_id",
        "weather",
        "num_fg_patches",
        "camera_mean",
        "lidar_mean",
        "radar_mean",
        "dominant",
        "dominance_margin",
        "entropy_mean",
        "fg_gate_delta",
    ]

    num_all_radar_patch = sum(1 for row in patch_rows if row["dominant"] == "R")
    num_all_camera_patch = sum(1 for row in patch_rows if row["dominant"] == "C")
    num_all_lidar_patch = sum(1 for row in patch_rows if row["dominant"] == "L")
    num_radar_patch = sum(1 for row in patch_rows if row["foreground"] == 1 and row["dominant"] == "R")
    num_camera_patch = sum(1 for row in patch_rows if row["foreground"] == 1 and row["dominant"] == "C")
    num_lidar_patch = sum(1 for row in patch_rows if row["foreground"] == 1 and row["dominant"] == "L")
    fg_rows = [row for row in patch_rows if row["foreground"] == 1]
    max_radar = finite_max([row["radar"] for row in fg_rows])
    max_camera = finite_max([row["camera"] for row in fg_rows])
    max_entropy = finite_max([row["entropy"] for row in fg_rows])

    lines = [
        "# TaskDec Sensor Case Search",
        "",
        "This file searches the weather-balanced PCA export for local samples whose controller outputs are less LiDAR-default than the weather averages.",
        "",
        "## Quick Counts",
        "",
        f"- All sampled patch groups: {len(patch_rows)}",
        f"- LiDAR-dominant all sampled patches: {num_all_lidar_patch}",
        f"- Radar-dominant all sampled patches: {num_all_radar_patch}",
        f"- Camera-dominant all sampled patches: {num_all_camera_patch}",
        f"- Foreground patch triplets: {num_lidar_patch + num_camera_patch + num_radar_patch}",
        f"- LiDAR-dominant foreground patches: {num_lidar_patch}",
        f"- Radar-dominant foreground patches: {num_radar_patch}",
        f"- Camera-dominant foreground patches: {num_camera_patch}",
        f"- Max foreground radar reliability: {max_radar:.6f}",
        f"- Max foreground camera reliability: {max_camera:.6f}",
        f"- Max foreground entropy: {max_entropy:.6f}",
        "",
        "## Top All Sampled Patches By Radar Reliability",
        "",
        markdown_table(top_by(patch_rows, "radar", top_k), patch_fields),
        "## Top All Sampled Patches By Camera Reliability",
        "",
        markdown_table(top_by(patch_rows, "camera", top_k), patch_fields),
        "## Most Balanced All Sampled Patches",
        "",
        markdown_table(top_by(patch_rows, "entropy", top_k), patch_fields),
        "## Top Foreground Patches By Radar Reliability",
        "",
        markdown_table(top_by(patch_rows, "radar", top_k, foreground_only=True), patch_fields),
        "## Top Foreground Patches By Camera Reliability",
        "",
        markdown_table(top_by(patch_rows, "camera", top_k, foreground_only=True), patch_fields),
        "## Most Balanced Foreground Patches",
        "",
        markdown_table(top_by(patch_rows, "entropy", top_k, foreground_only=True), patch_fields),
        "## Frame-Level Radar-Heavy Candidates",
        "",
        markdown_table(top_by(frame_rows, "radar_mean", top_k), frame_fields),
        "## Frame-Level Camera-Heavy Candidates",
        "",
        markdown_table(top_by(frame_rows, "camera_mean", top_k), frame_fields),
        "## Frame-Level Balanced Candidates",
        "",
        markdown_table(top_by(frame_rows, "entropy_mean", top_k), frame_fields),
        "## Frame-Level Gate-Response Candidates",
        "",
        markdown_table(top_by(frame_rows, "fg_gate_delta", top_k), frame_fields),
        "## Per-Weather Best Radar/Balance Candidates",
        "",
    ]

    for weather in WEATHER_ORDER:
        lines.extend([
            f"### {weather}",
            "",
            "Radar-heavy foreground patches:",
            "",
            markdown_table(top_by(patch_rows, "radar", min(5, top_k), foreground_only=True, weather=weather), patch_fields),
            "Most balanced foreground patches:",
            "",
            markdown_table(top_by(patch_rows, "entropy", min(5, top_k), foreground_only=True, weather=weather), patch_fields),
        ])

    path.write_text("\n".join(lines))


def main():
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    patch_rows = load_patch_triplets(args.npz)
    frame_rows = summarize_frames(patch_rows)

    patch_fields = [
        "frame_idx",
        "seq",
        "sample_id",
        "weather",
        "patch_idx",
        "foreground",
        "camera",
        "lidar",
        "radar",
        "dominant",
        "dominant_value",
        "dominance_margin",
        "entropy",
        "balance_score",
        "fg_gate",
    ]
    frame_fields = [
        "frame_idx",
        "seq",
        "sample_id",
        "weather",
        "num_fg_patches",
        "num_bg_patches",
        "camera_mean",
        "lidar_mean",
        "radar_mean",
        "dominant",
        "dominant_value",
        "dominance_margin",
        "entropy_mean",
        "balance_score_mean",
        "fg_gate_mean",
        "bg_gate_mean",
        "fg_gate_delta",
    ]
    write_csv(out_dir / "taskdec_sensor_patch_cases.csv", patch_rows, patch_fields)
    write_csv(out_dir / "taskdec_sensor_frame_cases.csv", frame_rows, frame_fields)
    write_summary(out_dir / "taskdec_sensor_case_search.md", patch_rows, frame_rows, args.top_k)

    print(f"Patch cases: {out_dir / 'taskdec_sensor_patch_cases.csv'}")
    print(f"Frame cases: {out_dir / 'taskdec_sensor_frame_cases.csv'}")
    print(f"Summary: {out_dir / 'taskdec_sensor_case_search.md'}")


if __name__ == "__main__":
    main()
