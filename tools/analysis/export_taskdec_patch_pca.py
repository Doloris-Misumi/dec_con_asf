#!/usr/bin/env python3
"""Export TaskDec patch states and draw lightweight PCA visualizations.

The script samples canonical patch tokens from a trained TaskDec model without
changing the model code. It records raw canonical tokens, common factors, and
unique factors, then produces PCA scatter plots as SVG files.
"""

import argparse
import csv
import json
import os
import random
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ops"))


DEFAULT_EXP = ROOT / "logs" / (
    "exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_"
    "rlc_l1d256_l2p2t32d256g_l2g_scl_mha16"
)


MODALITY_NAMES = {
    "cam_bev_feat": "Camera",
    "spatial_features_2d": "LiDAR",
    "bev_feat": "4D Radar",
}

MODALITY_SHORT = {
    "cam_bev_feat": "C",
    "spatial_features_2d": "L",
    "bev_feat": "R",
}

MODALITY_COLORS = {
    "cam_bev_feat": "#d65f5f",
    "spatial_features_2d": "#3f9b72",
    "bev_feat": "#5276d7",
}

FEATURE_TITLES = {
    "raw": "Raw Canonical",
    "common": "Common State",
    "unique": "Unique State",
}

WEATHER_ORDER = [
    "normal",
    "overcast",
    "fog",
    "rain",
    "sleet",
    "lightsnow",
    "heavysnow",
]

DESC_WEATHER_CACHE = {}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_EXP / "config.yml"))
    parser.add_argument("--model", default=str(DEFAULT_EXP / "models" / "model_0.pt"))
    parser.add_argument("--gpu", default="3")
    parser.add_argument("--infer-mode", default="rlc")
    parser.add_argument("--num-frames", type=int, default=80)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-fg-per-frame", type=int, default=48)
    parser.add_argument("--max-bg-per-frame", type=int, default=24)
    parser.add_argument("--max-svg-points", type=int, default=3600)
    parser.add_argument("--frames-per-weather", type=int, default=0)
    parser.add_argument("--weather-list", default=",".join(WEATHER_ORDER))
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "analysis_exports" / "taskdec_patch_pca_260904"),
    )
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def get_meta_value(meta, key, default="unknown"):
    if not meta:
        return default
    value = meta.get(key, default)
    if isinstance(value, (list, tuple)):
        return value[0] if value else default
    return value


def normalize_condition_name(value):
    text = str(value).strip().lower()
    text = text.replace(" ", "").replace("-", "").replace("_", "")
    aliases = {
        "light_snow": "lightsnow",
        "lightsnow": "lightsnow",
        "lightingsnow": "lightsnow",
        "heavysnow": "heavysnow",
        "heavy_snow": "heavysnow",
        "snow": "sleet",
    }
    return aliases.get(text, text)


def read_weather_from_desc_file(path_desc):
    if not path_desc:
        return None
    path_desc = str(path_desc)
    if path_desc in DESC_WEATHER_CACHE:
        return DESC_WEATHER_CACHE[path_desc]
    try:
        with open(path_desc, "r") as f:
            line = f.readline().strip()
        parts = [item.strip() for item in line.split(",")]
        value = normalize_condition_name(parts[2]) if len(parts) >= 3 else None
    except OSError:
        value = None
    DESC_WEATHER_CACHE[path_desc] = value
    return value


def infer_weather(meta):
    desc = meta.get("desc", {}) if isinstance(meta, dict) else {}
    for key in ("climate", "weather", "condition"):
        if isinstance(desc, dict) and key in desc:
            return normalize_condition_name(desc[key])
    for key in ("weather", "condition"):
        if isinstance(meta, dict) and key in meta:
            return normalize_condition_name(meta[key])
    path_info = meta.get("path", {}) if isinstance(meta, dict) else {}
    if isinstance(path_info, dict):
        for key in ("desc", "path_desc"):
            value = read_weather_from_desc_file(path_info.get(key))
            if value:
                return value
    return "unknown"


def infer_batch_weather(batch_dict):
    meta_list = batch_dict.get("meta", [])
    sample_meta = meta_list[0] if isinstance(meta_list, list) and meta_list else {}
    return infer_weather(sample_meta)


def normalize_np(x, eps=1.0e-8):
    denom = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(denom, eps)


def cosine_mean(a, b):
    a_np = a.detach().float().cpu().numpy()
    b_np = b.detach().float().cpu().numpy()
    if a_np.shape[0] == 0:
        return None
    cos = (normalize_np(a_np) * normalize_np(b_np)).sum(axis=1)
    return float(np.mean(cos))


def choose_indices(rng, indices, limit):
    indices = np.asarray(indices, dtype=np.int64)
    if limit <= 0 or indices.size == 0:
        return np.empty((0,), dtype=np.int64)
    if indices.size <= limit:
        return indices
    return np.asarray(rng.sample(indices.tolist(), limit), dtype=np.int64)


def choose_evenly(indices, limit):
    indices = list(indices)
    if limit <= 0 or len(indices) <= limit:
        return indices
    positions = np.linspace(0, len(indices) - 1, limit)
    chosen = []
    seen = set()
    for pos in positions:
        idx = indices[int(round(float(pos)))]
        if idx not in seen:
            chosen.append(idx)
            seen.add(idx)
    if len(chosen) < limit:
        for idx in indices:
            if idx in seen:
                continue
            chosen.append(idx)
            seen.add(idx)
            if len(chosen) >= limit:
                break
    return chosen


def build_weather_balanced_indices(dataset, weather_targets, frames_per_weather):
    by_weather = defaultdict(list)
    list_items = getattr(dataset, "list_dict_item", None)
    if list_items is None:
        return None, {}
    for idx, item in enumerate(list_items):
        meta = item.get("meta", {}) if isinstance(item, dict) else {}
        weather = infer_weather(meta)
        by_weather[weather].append(idx)

    selected = []
    available = {}
    for weather in weather_targets:
        indices = by_weather.get(weather, [])
        available[weather] = len(indices)
        selected.extend(choose_evenly(indices, frames_per_weather))
    return selected, available


class PatchStateCollector:
    def __init__(self, args):
        self.args = args
        self.rng = random.Random(args.seed)
        self.features = defaultdict(list)
        self.meta = defaultdict(lambda: defaultdict(list))
        self.metrics = defaultdict(list)
        self.weather_frame_counts = Counter()
        self.frames_seen = 0
        self.frames_collected = 0
        self.records_collected = 0

    def collect(self, fuser, keys, tokens, batch_dict):
        base_tokens = [tok.squeeze(1) for tok in tokens]
        if not base_tokens:
            return

        common_tokens = [fuser.patch_common[key](base) for key, base in zip(keys, base_tokens)]
        unique_tokens = [fuser.patch_unique[key](base) for key, base in zip(keys, base_tokens)]

        num_patch = base_tokens[0].shape[0]
        num_classes = int(getattr(fuser, "dec_control_num_classes", 2))
        fg_mask, _, num_fg, fg_ratio = fuser._gt_patch_targets(
            batch_dict,
            num_patch,
            base_tokens[0].device,
            num_classes=num_classes,
        )
        if fg_mask is None:
            fg_np = np.zeros((num_patch,), dtype=bool)
        else:
            fg_np = fg_mask.detach().cpu().numpy().astype(bool)

        fg_idx = choose_indices(self.rng, np.flatnonzero(fg_np), self.args.max_fg_per_frame)
        bg_idx = choose_indices(self.rng, np.flatnonzero(~fg_np), self.args.max_bg_per_frame)
        selected = np.concatenate([fg_idx, bg_idx])
        if selected.size == 0:
            return

        control_factor = fuser._dec_control_schedule_factor(batch_dict)
        gate_logits, gate_prob, _, _, sensor_prob, _ = fuser._dec_control_scores(
            keys,
            base_tokens,
            common_tokens,
            unique_tokens,
            control_factor=control_factor,
        )
        del gate_logits

        meta_list = batch_dict.get("meta", [])
        sample_meta = meta_list[0] if isinstance(meta_list, list) and meta_list else {}
        seq = str(get_meta_value(sample_meta, "seq"))
        idx = sample_meta.get("idx", {}) if isinstance(sample_meta, dict) else {}
        frame_id = str(idx.get("rdr", idx.get("camf", self.frames_seen))) if isinstance(idx, dict) else str(self.frames_seen)
        weather = infer_weather(sample_meta)

        self._record_similarity_metrics(keys, base_tokens, common_tokens, unique_tokens, fg_np)

        selected_t = np.asarray(selected, dtype=np.int64)
        fg_selected = fg_np[selected_t].astype(np.int8)
        gate_np = gate_prob.detach().float().cpu().numpy()[selected_t]
        sensor_prob_np = sensor_prob.detach().float().cpu().numpy()[selected_t]

        for sensor_idx, key in enumerate(keys):
            modality = MODALITY_NAMES.get(key, key)
            modality_short = MODALITY_SHORT.get(key, key)
            reliability = sensor_prob_np[:, sensor_idx]
            tensors = {
                "raw": base_tokens[sensor_idx],
                "common": common_tokens[sensor_idx],
                "unique": unique_tokens[sensor_idx],
            }
            for feature_type, tensor in tensors.items():
                values = tensor.detach().float().cpu().numpy()[selected_t]
                self.features[feature_type].append(values)
                store = self.meta[feature_type]
                n = values.shape[0]
                store["modality"].extend([modality] * n)
                store["modality_key"].extend([key] * n)
                store["modality_short"].extend([modality_short] * n)
                store["foreground"].extend(fg_selected.tolist())
                store["patch_idx"].extend(selected_t.tolist())
                store["frame_idx"].extend([self.frames_seen] * n)
                store["seq"].extend([seq] * n)
                store["sample_id"].extend([frame_id] * n)
                store["weather"].extend([weather] * n)
                store["fg_gate"].extend(gate_np.tolist())
                store["sensor_reliability"].extend(reliability.tolist())
                self.records_collected += n

        self.frames_collected += 1
        self.weather_frame_counts[weather] += 1
        self.metrics["num_fg_patches"].append(float(num_fg))
        self.metrics["fg_ratio"].append(float(fg_ratio))

    def _record_similarity_metrics(self, keys, base_tokens, common_tokens, unique_tokens, fg_np):
        masks = {
            "fg": fg_np,
            "bg": ~fg_np,
        }
        for mask_name, mask_np in masks.items():
            if int(mask_np.sum()) == 0:
                continue
            idx = np.flatnonzero(mask_np)
            if idx.size > 512:
                idx = np.asarray(self.rng.sample(idx.tolist(), 512), dtype=np.int64)
            idx_t = base_tokens[0].new_tensor(idx).long()
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    suffix = f"{mask_name}_{MODALITY_SHORT.get(keys[i], keys[i])}{MODALITY_SHORT.get(keys[j], keys[j])}"
                    self._append_metric(f"raw_cos_{suffix}", cosine_mean(
                        base_tokens[i].index_select(0, idx_t),
                        base_tokens[j].index_select(0, idx_t),
                    ))
                    self._append_metric(f"common_cos_{suffix}", cosine_mean(
                        common_tokens[i].index_select(0, idx_t),
                        common_tokens[j].index_select(0, idx_t),
                    ))
                    self._append_metric(f"unique_cos_{suffix}", cosine_mean(
                        unique_tokens[i].index_select(0, idx_t),
                        unique_tokens[j].index_select(0, idx_t),
                    ))
            for i, key in enumerate(keys):
                suffix = f"{mask_name}_{MODALITY_SHORT.get(key, key)}"
                self._append_metric(f"common_unique_abs_cos_{suffix}", abs(cosine_mean(
                    common_tokens[i].index_select(0, idx_t),
                    unique_tokens[i].index_select(0, idx_t),
                )))

    def _append_metric(self, key, value):
        if value is not None and np.isfinite(value):
            self.metrics[key].append(float(value))

    def arrays(self):
        output = {}
        for feature_type, chunks in self.features.items():
            if chunks:
                output[feature_type] = np.concatenate(chunks, axis=0)
            else:
                output[feature_type] = np.empty((0, 0), dtype=np.float32)
        return output

    def metadata_arrays(self, feature_type):
        return {key: np.asarray(value) for key, value in self.meta[feature_type].items()}

    def metric_summary(self):
        summary = {
            "frames_seen": self.frames_seen,
            "frames_collected": self.frames_collected,
            "records_collected": self.records_collected,
            "weather_frame_counts": dict(sorted(self.weather_frame_counts.items())),
        }
        for key, values in sorted(self.metrics.items()):
            arr = np.asarray(values, dtype=np.float64)
            if arr.size == 0:
                continue
            summary[key] = {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "n": int(arr.size),
            }
        return summary


def pca_2d(x):
    x = np.asarray(x, dtype=np.float64)
    if x.shape[0] < 3:
        return np.zeros((x.shape[0], 2), dtype=np.float32), np.zeros((2,), dtype=np.float32)
    x_centered = x - np.mean(x, axis=0, keepdims=True)
    _, s, vh = np.linalg.svd(x_centered, full_matrices=False)
    coords = x_centered @ vh[:2].T
    var = (s ** 2) / max(x.shape[0] - 1, 1)
    total = float(np.sum(var))
    ratio = var[:2] / total if total > 0 else np.zeros((2,), dtype=np.float64)
    return coords.astype(np.float32), ratio.astype(np.float32)


def xml_escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def sample_for_svg(rng, coords, meta, foreground_only, max_points, weather_filter=None):
    mask = np.ones((coords.shape[0],), dtype=bool)
    if foreground_only:
        mask &= meta["foreground"].astype(np.int64) == 1
    if weather_filter is not None:
        weather_arr = np.asarray([normalize_condition_name(v) for v in meta["weather"]])
        mask &= weather_arr == normalize_condition_name(weather_filter)
    indices = np.flatnonzero(mask)
    if indices.size > max_points:
        fg = indices[meta["foreground"][indices].astype(np.int64) == 1]
        bg = indices[meta["foreground"][indices].astype(np.int64) == 0]
        keep_fg = min(fg.size, int(max_points * 0.72))
        keep_bg = max_points - keep_fg
        chosen = []
        if keep_fg > 0:
            chosen.extend(rng.sample(fg.tolist(), keep_fg))
        if keep_bg > 0 and bg.size > 0:
            chosen.extend(rng.sample(bg.tolist(), min(keep_bg, bg.size)))
        indices = np.asarray(chosen, dtype=np.int64)
    return indices


def panel_transform(coords, x0, y0, width, height):
    if coords.shape[0] == 0:
        return np.empty((0,), dtype=np.float32), np.empty((0,), dtype=np.float32)
    lo = np.percentile(coords, 1, axis=0)
    hi = np.percentile(coords, 99, axis=0)
    span = np.maximum(hi - lo, 1.0e-6)
    pad = 0.08 * span
    lo = lo - pad
    hi = hi + pad
    span = np.maximum(hi - lo, 1.0e-6)
    clipped = np.minimum(np.maximum(coords, lo), hi)
    xs = x0 + (clipped[:, 0] - lo[0]) / span[0] * width
    ys = y0 + height - (clipped[:, 1] - lo[1]) / span[1] * height
    return xs, ys


def draw_svg(path, pca_data, foreground_only, max_points, seed, weather_filter=None, title_suffix=None):
    rng = random.Random(seed)
    width = 1500
    height = 520
    margin_x = 70
    panel_w = 395
    panel_h = 330
    gap = 55
    panel_y = 92
    legend_y = 462
    bg = "#fbfbfd"
    axis = "#d6dbe5"
    text = "#1f2937"
    muted = "#687386"

    title = "TaskDec Patch-State PCA"
    if title_suffix:
        title += f" - {title_suffix}"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{bg}"/>',
        (
            f'<text x="{margin_x}" y="42" font-family="Arial, sans-serif" '
            f'font-size="24" font-weight="700" fill="{text}">'
            f'{xml_escape(title)}'
            f'</text>'
        ),
        (
            f'<text x="{margin_x}" y="67" font-family="Arial, sans-serif" '
            f'font-size="14" fill="{muted}">'
            f'{"foreground patches only" if foreground_only else "foreground patches with sampled background"}'
            f'</text>'
        ),
    ]

    for panel_idx, feature_type in enumerate(["raw", "common", "unique"]):
        x0 = margin_x + panel_idx * (panel_w + gap)
        coords = pca_data[feature_type]["coords"]
        meta = pca_data[feature_type]["meta"]
        ratio = pca_data[feature_type]["ratio"]
        indices = sample_for_svg(rng, coords, meta, foreground_only, max_points, weather_filter=weather_filter)
        xs, ys = panel_transform(coords[indices], x0, panel_y, panel_w, panel_h)

        parts.extend([
            f'<rect x="{x0}" y="{panel_y}" width="{panel_w}" height="{panel_h}" fill="white" stroke="#dfe3eb" stroke-width="1"/>',
            f'<line x1="{x0}" y1="{panel_y + panel_h}" x2="{x0 + panel_w}" y2="{panel_y + panel_h}" stroke="{axis}"/>',
            f'<line x1="{x0}" y1="{panel_y}" x2="{x0}" y2="{panel_y + panel_h}" stroke="{axis}"/>',
            (
                f'<text x="{x0}" y="{panel_y - 18}" font-family="Arial, sans-serif" '
                f'font-size="18" font-weight="700" fill="{text}">'
                f'{FEATURE_TITLES[feature_type]}'
                f'</text>'
            ),
            (
                f'<text x="{x0 + panel_w - 4}" y="{panel_y - 18}" text-anchor="end" '
                f'font-family="Arial, sans-serif" font-size="12" fill="{muted}">'
                f'PC1 {ratio[0] * 100:.1f}%, PC2 {ratio[1] * 100:.1f}%'
                f'</text>'
            ),
            (
                f'<text x="{x0 + panel_w / 2}" y="{panel_y + panel_h + 34}" '
                f'text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="{muted}">PC1</text>'
            ),
            (
                f'<text x="{x0 - 42}" y="{panel_y + panel_h / 2}" '
                f'transform="rotate(-90 {x0 - 42} {panel_y + panel_h / 2})" '
                f'text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="{muted}">PC2</text>'
            ),
        ])

        if indices.size == 0:
            parts.append(
                f'<text x="{x0 + panel_w / 2}" y="{panel_y + panel_h / 2}" '
                f'text-anchor="middle" font-family="Arial, sans-serif" '
                f'font-size="16" fill="{muted}">no sampled patches</text>'
            )
            continue

        order = np.argsort(meta["foreground"][indices].astype(np.int64))
        for out_idx in order:
            row = indices[out_idx]
            key = str(meta["modality_key"][row])
            color = MODALITY_COLORS.get(key, "#6b7280")
            is_fg = int(meta["foreground"][row]) == 1
            radius = 2.4 if is_fg else 1.25
            opacity = 0.72 if is_fg else 0.18
            stroke = "#222222" if is_fg else "none"
            stroke_width = "0.25" if is_fg else "0"
            parts.append(
                f'<circle cx="{xs[out_idx]:.2f}" cy="{ys[out_idx]:.2f}" r="{radius}" '
                f'fill="{color}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
            )

    legend_x = margin_x
    for i, (key, name) in enumerate(MODALITY_NAMES.items()):
        lx = legend_x + i * 170
        color = MODALITY_COLORS[key]
        parts.append(f'<circle cx="{lx}" cy="{legend_y}" r="6" fill="{color}" fill-opacity="0.78"/>')
        parts.append(
            f'<text x="{lx + 14}" y="{legend_y + 5}" font-family="Arial, sans-serif" '
            f'font-size="14" fill="{text}">{xml_escape(name)}</text>'
        )
    parts.append(f'<circle cx="{legend_x + 560}" cy="{legend_y}" r="6" fill="#111827" fill-opacity="0.72"/>')
    parts.append(
        f'<text x="{legend_x + 574}" y="{legend_y + 5}" font-family="Arial, sans-serif" '
        f'font-size="14" fill="{text}">foreground</text>'
    )
    parts.append(f'<circle cx="{legend_x + 700}" cy="{legend_y}" r="4" fill="#111827" fill-opacity="0.18"/>')
    parts.append(
        f'<text x="{legend_x + 714}" y="{legend_y + 5}" font-family="Arial, sans-serif" '
        f'font-size="14" fill="{text}">sampled background</text>'
    )
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def summarize_weather_reliability(out_dir, pca_data):
    meta = pca_data["raw"]["meta"]
    fields = [
        "weather",
        "foreground_group",
        "modality",
        "count",
        "mean_reliability",
        "std_reliability",
        "mean_fg_gate",
        "std_fg_gate",
    ]
    groups = defaultdict(lambda: {"rel": [], "gate": []})
    for i in range(len(meta["weather"])):
        weather = normalize_condition_name(meta["weather"][i])
        modality = str(meta["modality"][i])
        is_fg = int(meta["foreground"][i]) == 1
        rel = float(meta["sensor_reliability"][i])
        gate = float(meta["fg_gate"][i])
        for fg_group in ("all", "fg" if is_fg else "bg"):
            key = (weather, fg_group, modality)
            groups[key]["rel"].append(rel)
            groups[key]["gate"].append(gate)

    weather_rank = {name: i for i, name in enumerate(WEATHER_ORDER)}
    modality_rank = {name: i for i, name in enumerate(MODALITY_NAMES.values())}
    rows = []
    for (weather, fg_group, modality), values in groups.items():
        rel = np.asarray(values["rel"], dtype=np.float64)
        gate = np.asarray(values["gate"], dtype=np.float64)
        rows.append({
            "weather": weather,
            "foreground_group": fg_group,
            "modality": modality,
            "count": int(rel.size),
            "mean_reliability": float(np.mean(rel)),
            "std_reliability": float(np.std(rel)),
            "mean_fg_gate": float(np.mean(gate)),
            "std_fg_gate": float(np.std(gate)),
        })
    rows.sort(key=lambda r: (
        weather_rank.get(r["weather"], 999),
        {"fg": 0, "all": 1, "bg": 2}.get(r["foreground_group"], 9),
        modality_rank.get(r["modality"], 999),
    ))

    csv_path = out_dir / "weather_sensor_reliability.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "weather": row["weather"],
                "foreground_group": row["foreground_group"],
                "modality": row["modality"],
                "count": row["count"],
                "mean_reliability": f"{row['mean_reliability']:.7g}",
                "std_reliability": f"{row['std_reliability']:.7g}",
                "mean_fg_gate": f"{row['mean_fg_gate']:.7g}",
                "std_fg_gate": f"{row['std_fg_gate']:.7g}",
            })

    md_lines = [
        "# Weather Sensor Reliability",
        "",
        "Values are computed from sampled raw canonical patch records. `fg` and `bg` are selected by the GT foreground patch mask used by TaskDec.",
        "",
        "| Weather | Group | Camera | LiDAR | 4D Radar | Gate mean | Sensor spread |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    row_map = {(r["weather"], r["foreground_group"], r["modality"]): r for r in rows}
    weather_values = sorted({r["weather"] for r in rows}, key=lambda x: weather_rank.get(x, 999))
    for weather in weather_values:
        for fg_group in ("fg", "all", "bg"):
            vals = []
            gates = []
            for modality in MODALITY_NAMES.values():
                row = row_map.get((weather, fg_group, modality))
                vals.append(row["mean_reliability"] if row else np.nan)
                if row:
                    gates.append(row["mean_fg_gate"])
            if not any(np.isfinite(vals)):
                continue
            finite = [v for v in vals if np.isfinite(v)]
            spread = max(finite) - min(finite) if finite else np.nan
            gate_mean = float(np.mean(gates)) if gates else np.nan
            md_lines.append(
                f"| {weather} | {fg_group} | "
                f"{vals[0]:.4f} | {vals[1]:.4f} | {vals[2]:.4f} | "
                f"{gate_mean:.4f} | {spread:.4f} |"
            )

    md_lines.extend([
        "",
        "## Most Sensor-Differentiated Weather Groups",
        "",
        "| Weather | Group | Dominant sensor | Mean reliability | Runner-up | Margin |",
        "|---|---|---|---:|---|---:|",
    ])
    rank_rows = []
    for weather in weather_values:
        for fg_group in ("fg", "all", "bg"):
            vals = []
            for modality in MODALITY_NAMES.values():
                row = row_map.get((weather, fg_group, modality))
                if row:
                    vals.append((modality, row["mean_reliability"]))
            if len(vals) < 2:
                continue
            vals.sort(key=lambda item: item[1], reverse=True)
            rank_rows.append((vals[0][1] - vals[1][1], weather, fg_group, vals))
    for margin, weather, fg_group, vals in sorted(rank_rows, reverse=True)[:12]:
        md_lines.append(
            f"| {weather} | {fg_group} | {vals[0][0]} | {vals[0][1]:.4f} | "
            f"{vals[1][0]} ({vals[1][1]:.4f}) | {margin:.4f} |"
        )

    md_path = out_dir / "weather_sensor_reliability.md"
    md_path.write_text("\n".join(md_lines))
    return csv_path, md_path


def save_csv(path, pca_data):
    fields = [
        "feature_type",
        "pc1",
        "pc2",
        "modality",
        "modality_key",
        "foreground",
        "patch_idx",
        "frame_idx",
        "seq",
        "sample_id",
        "weather",
        "fg_gate",
        "sensor_reliability",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for feature_type in ["raw", "common", "unique"]:
            coords = pca_data[feature_type]["coords"]
            meta = pca_data[feature_type]["meta"]
            for i in range(coords.shape[0]):
                writer.writerow({
                    "feature_type": feature_type,
                    "pc1": f"{coords[i, 0]:.7g}",
                    "pc2": f"{coords[i, 1]:.7g}",
                    "modality": meta["modality"][i],
                    "modality_key": meta["modality_key"][i],
                    "foreground": int(meta["foreground"][i]),
                    "patch_idx": int(meta["patch_idx"][i]),
                    "frame_idx": int(meta["frame_idx"][i]),
                    "seq": meta["seq"][i],
                    "sample_id": meta["sample_id"][i],
                    "weather": meta["weather"][i],
                    "fg_gate": f"{float(meta['fg_gate'][i]):.7g}",
                    "sensor_reliability": f"{float(meta['sensor_reliability'][i]):.7g}",
                })


def save_npz(path, arrays, pca_data, collector):
    payload = {}
    for feature_type in ["raw", "common", "unique"]:
        payload[f"{feature_type}_features"] = arrays[feature_type].astype(np.float32)
        payload[f"{feature_type}_pca"] = pca_data[feature_type]["coords"].astype(np.float32)
        payload[f"{feature_type}_pca_explained"] = pca_data[feature_type]["ratio"].astype(np.float32)
        for key, value in collector.metadata_arrays(feature_type).items():
            payload[f"{feature_type}_{key}"] = value
    np.savez_compressed(path, **payload)


def write_summary(path, args, collector, pca_data):
    summary = collector.metric_summary()
    lines = [
        "# TaskDec Patch-State PCA Export",
        "",
        f"- Config: `{args.config}`",
        f"- Model: `{args.model}`",
        f"- Inference mode: `{args.infer_mode}`",
        f"- Frames collected: {summary['frames_collected']} / seen {summary['frames_seen']}",
        f"- Feature records: {summary['records_collected']}",
        f"- Frames per weather target: {args.frames_per_weather}",
        "",
        "## PCA Explained Variance",
        "",
        "| Feature | PC1 | PC2 |",
        "|---|---:|---:|",
    ]
    for feature_type in ["raw", "common", "unique"]:
        ratio = pca_data[feature_type]["ratio"]
        lines.append(f"| {feature_type} | {ratio[0] * 100:.2f}% | {ratio[1] * 100:.2f}% |")

    lines.extend([
        "",
        "## Weather Frame Counts",
        "",
        "| Weather | Frames |",
        "|---|---:|",
    ])
    for weather, count in sorted(
        summary.get("weather_frame_counts", {}).items(),
        key=lambda item: (WEATHER_ORDER.index(item[0]) if item[0] in WEATHER_ORDER else 999, item[0]),
    ):
        lines.append(f"| {weather} | {count} |")

    lines.extend([
        "",
        "## Cosine Sanity Checks",
        "",
        "| Metric | Mean | Std | N |",
        "|---|---:|---:|---:|",
    ])
    for key, value in sorted(summary.items()):
        if not isinstance(value, dict) or "mean" not in value:
            continue
        lines.append(f"| {key} | {value['mean']:.4f} | {value['std']:.4f} | {value['n']} |")

    path.write_text("\n".join(lines))


def main():
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    random.seed(args.seed)
    np.random.seed(args.seed)
    weather_targets = [
        normalize_condition_name(item)
        for item in str(args.weather_list).split(",")
        if normalize_condition_name(item)
    ]
    weather_target_set = set(weather_targets)

    import torch
    from tqdm import tqdm
    from torch.utils.data import Subset
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("* TaskDec patch PCA export")
    print(f"* CUDA_VISIBLE_DEVICES={args.gpu}")
    print(f"* Config: {args.config}")
    print(f"* Model: {args.model}")
    print(f"* Output: {out_dir}")

    pline = PipelineDetection_v1_0(path_cfg=args.config, mode="test")
    pline.cfg.OPTIMIZER.NUM_WORKERS = args.num_workers
    pline.load_dict_model(args.model, is_strict=args.strict)
    pline.network.eval()

    fuser = getattr(pline.network, "fuser", None)
    if fuser is None or not hasattr(fuser, "patch_common") or not hasattr(fuser, "_apply_patch_dec"):
        raise RuntimeError("The loaded network does not expose a TaskDec fuser.")

    collector = PatchStateCollector(args)
    original_apply = fuser._apply_patch_dec

    def patched_apply(self, keys, tokens, batch_dict):
        with torch.no_grad():
            collector.collect(self, keys, tokens, batch_dict)
        return original_apply(keys, tokens, batch_dict)

    fuser._apply_patch_dec = types.MethodType(patched_apply, fuser)

    dataset_for_loader = pline.dataset_test
    selected_dataset_indices = None
    weather_availability = {}
    if args.frames_per_weather > 0:
        selected_dataset_indices, weather_availability = build_weather_balanced_indices(
            pline.dataset_test,
            weather_targets,
            args.frames_per_weather,
        )
        if selected_dataset_indices:
            dataset_for_loader = Subset(pline.dataset_test, selected_dataset_indices)
            print("* Weather-balanced dataset indices:")
            for weather in weather_targets:
                chosen = sum(
                    1
                    for idx in selected_dataset_indices
                    if infer_weather(pline.dataset_test.list_dict_item[idx]["meta"]) == weather
                )
                print(f"  - {weather}: selected {chosen} / available {weather_availability.get(weather, 0)}")
        else:
            selected_dataset_indices = None
            print("* Weather-balanced index preselection unavailable; falling back to sequential scan.")

    data_loader = pline.build_dataloader(
        dataset_for_loader,
        batch_size=1,
        shuffle=False,
        collate_fn=pline.dataset_test.collate_fn,
    )
    list_avail_feats = pline.infer_mode_to_avail_feats(args.infer_mode)

    with torch.no_grad():
        pbar = tqdm(data_loader, desc="export patches", total=len(dataset_for_loader))
        for idx_datum, dict_datum in enumerate(pbar):
            if idx_datum % max(args.stride, 1) != 0:
                continue
            weather = infer_batch_weather(dict_datum)
            if args.frames_per_weather > 0 and selected_dataset_indices is None:
                if weather not in weather_target_set:
                    continue
                if collector.weather_frame_counts[weather] >= args.frames_per_weather:
                    if all(collector.weather_frame_counts[w] >= args.frames_per_weather for w in weather_targets):
                        break
                    continue
            if args.num_frames > 0 and collector.frames_collected >= args.num_frames:
                break
            collector.frames_seen = idx_datum
            dict_datum["avail_feats"] = list_avail_feats
            _ = pline.network(dict_datum)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            pbar.set_postfix(
                frames=collector.frames_collected,
                records=collector.records_collected,
                weather=weather,
            )
            if (
                args.frames_per_weather > 0
                and all(collector.weather_frame_counts[w] >= args.frames_per_weather for w in weather_targets)
            ):
                break

    arrays = collector.arrays()
    pca_data = {}
    for feature_type in ["raw", "common", "unique"]:
        coords, ratio = pca_2d(arrays[feature_type])
        pca_data[feature_type] = {
            "coords": coords,
            "ratio": ratio,
            "meta": collector.metadata_arrays(feature_type),
        }

    save_npz(out_dir / "taskdec_patch_states_pca.npz", arrays, pca_data, collector)
    save_csv(out_dir / "taskdec_patch_states_pca.csv", pca_data)
    draw_svg(
        out_dir / "taskdec_patch_pca_foreground.svg",
        pca_data,
        foreground_only=True,
        max_points=args.max_svg_points,
        seed=args.seed,
    )
    draw_svg(
        out_dir / "taskdec_patch_pca_all.svg",
        pca_data,
        foreground_only=False,
        max_points=args.max_svg_points,
        seed=args.seed + 1,
    )
    present_weathers = sorted(
        set(str(v) for v in pca_data["raw"]["meta"].get("weather", [])),
        key=lambda item: (WEATHER_ORDER.index(item) if item in WEATHER_ORDER else 999, item),
    )
    for idx_weather, weather in enumerate(present_weathers):
        draw_svg(
            out_dir / f"taskdec_patch_pca_foreground_{weather}.svg",
            pca_data,
            foreground_only=True,
            max_points=args.max_svg_points,
            seed=args.seed + 100 + idx_weather,
            weather_filter=weather,
            title_suffix=f"{weather} foreground",
        )
        draw_svg(
            out_dir / f"taskdec_patch_pca_all_{weather}.svg",
            pca_data,
            foreground_only=False,
            max_points=args.max_svg_points,
            seed=args.seed + 200 + idx_weather,
            weather_filter=weather,
            title_suffix=f"{weather} fg+bg",
        )
    summary = collector.metric_summary()
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2))
    summarize_weather_reliability(out_dir, pca_data)
    write_summary(out_dir / "summary.md", args, collector, pca_data)

    print("* Done.")
    print(f"* Foreground PCA SVG: {out_dir / 'taskdec_patch_pca_foreground.svg'}")
    print(f"* All PCA SVG: {out_dir / 'taskdec_patch_pca_all.svg'}")
    print(f"* Summary: {out_dir / 'summary.md'}")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
