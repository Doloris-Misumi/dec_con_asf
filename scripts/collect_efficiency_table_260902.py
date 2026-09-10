#!/usr/bin/env python3
"""Collect TaskDec/ASF inference efficiency benchmark results."""

import json
from datetime import datetime
from pathlib import Path


ROOT = Path("/home/hongsheng/dec_con_asf")
OUT_DIR = ROOT / "results/efficiency_260902"


def load(name):
    path = OUT_DIR / f"{name}.json"
    if not path.exists():
        return None, path
    return json.loads(path.read_text()), path


def fmt(result, key, subkey=None, scale=1.0):
    if result is None:
        return "-"
    value = result[key][subkey] if subkey else result[key]
    return f"{value * scale:.2f}"


def delta_fmt(taskdec, asf, key, subkey=None):
    if taskdec is None or asf is None:
        return "-"
    td_value = taskdec[key][subkey] if subkey else taskdec[key]
    asf_value = asf[key][subkey] if subkey else asf[key]
    delta = td_value - asf_value
    pct = 100.0 * delta / asf_value if asf_value else 0.0
    return f"{delta:+.2f} ({pct:+.1f}%)"


def main():
    rows = []
    loaded = {}
    for label, name in [
        ("Official ASF v1 ckpt (C+L+R)", "official_asf_v1_model10_rlc"),
        ("TaskDec Robust model_0 (C+L+R)", "taskdec_robust_v1_model0_rlc"),
        ("L4DR model_34 (L+R, local run)", "l4dr_v1_1_model34_lr_local_sparsecube"),
    ]:
        result, path = load(name)
        loaded[name] = result
        rows.append(
            "| {label} | {params} | {lat} | {fps} | {e2e} | {mem} | `{source}` |".format(
                label=label,
                params=fmt(result, "params_m"),
                lat=fmt(result, "forward_ms", "mean"),
                fps=fmt(result, "forward_fps"),
                e2e=fmt(result, "total_ms", "mean"),
                mem=fmt(result, "peak_allocated_gb"),
                source=path,
            )
        )

    asf = loaded.get("official_asf_v1_model10_rlc")
    taskdec = loaded.get("taskdec_robust_v1_model0_rlc")
    rows.append(
        "| TaskDec - ASF | {params} | {lat} | {fps} | {e2e} | {mem} | - |".format(
            params=delta_fmt(taskdec, asf, "params_m"),
            lat=delta_fmt(taskdec, asf, "forward_ms", "mean"),
            fps=delta_fmt(taskdec, asf, "forward_fps"),
            e2e=delta_fmt(taskdec, asf, "total_ms", "mean"),
            mem=delta_fmt(taskdec, asf, "peak_allocated_gb"),
        )
    )

    lines = [
        "# K-Radar v1.0 Inference Efficiency",
        "",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Protocol: batch size 1, same local machine, warmup + measured forward timing.",
        "",
        "| Method | Params (M) | Forward latency (ms) | Forward FPS | End-to-end latency (ms) | Peak memory (GB) | Source |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    lines.extend(rows)
    lines.extend(
        [
            "",
            "Notes:",
            "",
            "- Forward latency is timed around `network(batch)` only, after 20 warmup iterations and over 100 measured iterations.",
            "- End-to-end latency includes dataset loading/collation and is therefore more IO-sensitive.",
            "- L4DR is an L+R model. This local run uses the released `model_34.pt` with the v1.1 config and reads local `sprdr_*.npy` symlinks that point to `sparse_cube/cube_*.npy`.",
        ]
    )
    out_path = ROOT / "results/paper_efficiency_table_260902.md"
    out_path.write_text("\n".join(lines) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
