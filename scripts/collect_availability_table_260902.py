#!/usr/bin/env python3
"""Collect K-Radar v1.0 missing-modality availability results."""

import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path("/home/hongsheng/dec_con_asf")
ASF_ROOT = Path("/home/hongsheng/K-Radar-main")

TASKDEC_RLC = ROOT / "logs/exp_260812_232650_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.json"
ASF_RLC = ASF_ROOT / "results/official_asf_v1_exp250303/summary_conf0.3.json"

TASKDEC_LR_SOURCE = "results/full_eval_metric_audit_260821.md recompute"
ASF_LR_SOURCE = "results/full_eval_metric_audit_260821.md recompute"


def empty_metrics():
    return {
        "bev_07": None,
        "bev_05": None,
        "bev_03": None,
        "d3_07": None,
        "d3_05": None,
        "d3_03": None,
    }


def metrics_from_json(path, conf="0.3"):
    data = json.loads(path.read_text())
    sed = data[conf]["all"]["sed"]
    return {
        "bev_07": sed["BEV"].get("0.7"),
        "bev_05": sed["BEV"].get("0.5"),
        "bev_03": sed["BEV"].get("0.3"),
        "d3_07": sed["3D"].get("0.7"),
        "d3_05": sed["3D"].get("0.5"),
        "d3_03": sed["3D"].get("0.3"),
    }


def metrics_from_conditional_log(path, conf="0.3", condition="all"):
    text = path.read_text(errors="ignore")
    pattern = re.compile(
        rf"Conf thr:\s*{re.escape(conf)}\s*,\s*Condition:\s*{re.escape(condition)}.*?"
        r"Cls:\s*sed.*?"
        r"IoU:\s*\[([^\]]+)\].*?"
        r"BEV:\s*\[([^\]]+)\].*?"
        r"3D:\s*\[([^\]]+)\]",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        return None
    ious = [float(x.strip()) for x in match.group(1).split(",")]
    bevs = [float(x.strip()) for x in match.group(2).split(",")]
    d3s = [float(x.strip()) for x in match.group(3).split(",")]
    by_iou = {f"{iou:g}": (bev, d3) for iou, bev, d3 in zip(ious, bevs, d3s)}
    return {
        "bev_07": by_iou.get("0.7", (None, None))[0],
        "bev_05": by_iou.get("0.5", (None, None))[0],
        "bev_03": by_iou.get("0.3", (None, None))[0],
        "d3_07": by_iou.get("0.7", (None, None))[1],
        "d3_05": by_iou.get("0.5", (None, None))[1],
        "d3_03": by_iou.get("0.3", (None, None))[1],
    }


def find_taskdec_eval(mode):
    candidates = []
    for log_path in sorted((ROOT / "logs/launcher").glob(f"availability_taskdec_robust_v1_model0_{mode}_gpu*_260902.log")):
        text = log_path.read_text(errors="ignore")
        match = re.search(r"Full summary JSON:\s*(\S+)", text)
        if match:
            path = Path(match.group(1))
            if path.exists():
                candidates.append(path)
    for path in sorted((ROOT / "logs").glob("exp_*TaskDecControlRobust_v1_0_A2FUSION*/full_eval_summary.json")):
        stdout = path.with_name("full_eval_stdout.log")
        if not stdout.exists():
            continue
        head = stdout.read_text(errors="ignore")[:2000]
        if f"* Infer mode: {mode}" in head:
            candidates.append(path)
    return candidates[-1] if candidates else None


def find_official_asf_log(mode):
    candidates = []
    for path in sorted((ASF_ROOT / "logs_avail_eval").glob(f"availability_official_asf_v1_model10_{mode}_gpu*_260902.log")):
        if metrics_from_conditional_log(path) is not None:
            candidates.append(path)
    return candidates[-1] if candidates else None


def fmt(value):
    return "-" if value is None else f"{value:.2f}"


def row(method, mode, metrics, source):
    return (
        f"| {method} | {mode.upper()} | {fmt(metrics['bev_05'])} | {fmt(metrics['d3_05'])} | "
        f"{fmt(metrics['bev_03'])} | {fmt(metrics['d3_03'])} | {fmt(metrics['d3_07'])} | `{source}` |"
    )


def delta(a, b, key):
    if a.get(key) is None or b.get(key) is None:
        return None
    return a[key] - b[key]


def main():
    rows = []
    sources = []

    taskdec = {
        "rlc": (metrics_from_json(TASKDEC_RLC), str(TASKDEC_RLC)),
        "lr": ({"bev_07": None, "bev_05": 85.45, "bev_03": 88.45, "d3_07": None, "d3_05": 71.68, "d3_03": 88.06}, TASKDEC_LR_SOURCE),
    }
    asf = {
        "rlc": (metrics_from_json(ASF_RLC), str(ASF_RLC)),
        "lr": ({"bev_07": None, "bev_05": 85.75, "bev_03": 86.35, "d3_07": None, "d3_05": 71.98, "d3_03": 86.02}, ASF_LR_SOURCE),
    }

    for mode in ["rc", "lc"]:
        taskdec_path = find_taskdec_eval(mode)
        if taskdec_path is not None:
            taskdec[mode] = (metrics_from_json(taskdec_path), str(taskdec_path))
        else:
            taskdec[mode] = (empty_metrics(), "pending")

        asf_path = find_official_asf_log(mode)
        if asf_path is not None:
            metrics = metrics_from_conditional_log(asf_path)
            asf[mode] = (metrics if metrics is not None else empty_metrics(), str(asf_path))
        else:
            asf[mode] = (empty_metrics(), "pending")

    lines = [
        "# K-Radar v1.0 Missing-Modality Availability Table",
        "",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Scope: K-Radar v1.0 narrow RoI, Sedan class, C=front camera, L=LiDAR, R=4D radar. "
        "All rows use C+L+R-trained checkpoints evaluated with controlled available sensors at inference. "
        "Main protocol is `conf_thr=0.3`.",
        "",
        "| Method | Available sensors | APBEV@0.5 | AP3D@0.5 | APBEV@0.3 | AP3D@0.3 | AP3D@0.7 | Source |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]

    for mode in ["rlc", "lr", "rc", "lc"]:
        lines.append(row("TaskDec Robust `model_0`", mode, taskdec[mode][0], taskdec[mode][1]))
        lines.append(row("Official ASF v1 ckpt", mode, asf[mode][0], asf[mode][1]))

    lines += [
        "",
        "## Delta: TaskDec - Official ASF",
        "",
        "| Available sensors | Delta APBEV@0.5 | Delta AP3D@0.5 | Delta APBEV@0.3 | Delta AP3D@0.3 |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode in ["rlc", "lr", "rc", "lc"]:
        td, base = taskdec[mode][0], asf[mode][0]
        lines.append(
            f"| {mode.upper()} | {fmt(delta(td, base, 'bev_05'))} | {fmt(delta(td, base, 'd3_05'))} | "
            f"{fmt(delta(td, base, 'bev_03'))} | {fmt(delta(td, base, 'd3_03'))} |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- `LR` uses the saved-prediction recompute values from the prior audit because the historical conditional-all LR block is inconsistent.",
        "- `RC` is accepted because the metric block was written before the post-run native `free(): invalid pointer` exit.",
        "- `LC` did not start because the launcher stopped after the RC post-run exit.",
    ]

    out_path = ROOT / "results/paper_availability_missing_modalities_260902.md"
    out_path.write_text("\n".join(lines) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
