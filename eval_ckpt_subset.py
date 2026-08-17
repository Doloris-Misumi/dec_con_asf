#!/usr/bin/env python3
"""Evaluate saved checkpoints on a fixed small validation subset."""

import argparse
import contextlib
import json
import os
import random
import re
import sys
from pathlib import Path


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


def parse_args():
    parser = argparse.ArgumentParser(description="Subset validation for PatchDec checkpoints")
    parser.add_argument("--config", default="./configs/ASF_patch_dec_v1.yml")
    parser.add_argument(
        "--exp-dir",
        default="./logs/exp_260726_144405_PatchDec_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16",
    )
    parser.add_argument("--gpu", default="2")
    parser.add_argument("--num-subset", type=int, default=1000)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20250215)
    parser.add_argument("--confs", default="0.3", help="Comma-separated confidence thresholds")
    parser.add_argument("--epochs", default="all", help="Comma-separated epoch ids, or all")
    parser.add_argument("--strict", action="store_true", help="Load checkpoints with strict=True")
    parser.add_argument("--pin-memory", action="store_true")
    parser.add_argument("--persistent-workers", action="store_true")
    parser.add_argument("--prefetch-factor", type=int, default=None)
    return parser.parse_args()


def checkpoint_epoch(path):
    match = re.search(r"model_(\d+)\.pt$", path.name)
    if match is None:
        return None
    return int(match.group(1))


def reset_seed(seed):
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def parse_stdout_blocks(text):
    results = {}
    current_conf = None
    current_cls = None
    current_iou = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = re.match(r"-+conf([\d.]+)-+", line)
        if match:
            current_conf = match.group(1)
            results.setdefault(current_conf, {})
            current_cls = None
            current_iou = None
            continue

        match = re.match(r"(\S+)\s+AP\(Average Precision\)@([\d.]+),", line)
        if match and current_conf is not None:
            current_cls = match.group(1)
            current_iou = f"{float(match.group(2)):g}"
            results[current_conf].setdefault(current_cls, {"BEV": {}, "3D": {}})
            continue

        if current_conf is None or current_cls is None or current_iou is None:
            continue

        match = re.match(r"bev\s+AP:\s*([\d.e+\-]+)", line)
        if match:
            results[current_conf][current_cls]["BEV"][current_iou] = float(match.group(1))
            continue

        match = re.match(r"3d\s+AP:\s*([\d.e+\-]+)", line)
        if match:
            results[current_conf][current_cls]["3D"][current_iou] = float(match.group(1))
            continue

    return results


def metric(results, conf, cls_name, metric_name, iou):
    return results.get(conf, {}).get(cls_name, {}).get(metric_name, {}).get(iou)


def mean_available(values):
    values = [v for v in values if isinstance(v, float)]
    if not values:
        return None
    return sum(values) / len(values)


def format_metric(value):
    return f"{value:.2f}" if value is not None else "-"


def append_top_epochs(lines, rows, conf, cls_name, metric_name, iou, title):
    scored = []
    for row in rows:
        value = metric(row["results"], conf, cls_name, metric_name, iou)
        if value is not None:
            scored.append((value, row["epoch"]))
    scored.sort(reverse=True)
    if scored:
        best = ", ".join([f"epoch {epoch}: {score:.2f}" for score, epoch in scored[:3]])
        lines.append(f"{title}: {best}")
        lines.append("")


def write_summary(path_log, rows, confs):
    json_path = path_log / "subset_eval_summary.json"
    md_path = path_log / "subset_eval_summary.md"

    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    lines = []
    lines.append("# PatchDec Checkpoint Subset Evaluation")
    lines.append("")
    lines.append(f"Log dir: `{path_log}`")
    lines.append("")
    for conf in confs:
        lines.append(f"## conf={conf}")
        lines.append("")
        lines.append("### Sedan All IoU Metrics")
        lines.append("")
        lines.append(
            "| Epoch | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |"
        )
        lines.append("|-------|---------|--------|---------|--------|---------|--------|")
        for row in rows:
            if conf not in row["results"]:
                continue
            lines.append(
                "| {epoch} | {bev07} | {d307} | {bev05} | {d305} | {bev03} | {d303} |".format(
                    epoch=row["epoch"],
                    bev07=format_metric(metric(row["results"], conf, "sed", "BEV", "0.7")),
                    d307=format_metric(metric(row["results"], conf, "sed", "3D", "0.7")),
                    bev05=format_metric(metric(row["results"], conf, "sed", "BEV", "0.5")),
                    d305=format_metric(metric(row["results"], conf, "sed", "3D", "0.5")),
                    bev03=format_metric(metric(row["results"], conf, "sed", "BEV", "0.3")),
                    d303=format_metric(metric(row["results"], conf, "sed", "3D", "0.3")),
                )
            )
        lines.append("")
        append_top_epochs(lines, rows, conf, "sed", "3D", "0.3", "Top by sed 3D@0.3")
        append_top_epochs(lines, rows, conf, "sed", "BEV", "0.5", "Top by sed BEV@0.5")

        lines.append("### Legacy Mean Table")
        lines.append("")
        lines.append(
            "| Epoch | sed BEV@0.3 | sed 3D@0.3 | bus BEV@0.3 | bus 3D@0.3 | mean 3D@0.3 |"
        )
        lines.append("|-------|-------------|------------|-------------|------------|-------------|")
        for row in rows:
            if conf not in row["results"]:
                continue
            vals = {
                "sed_bev": metric(row["results"], conf, "sed", "BEV", "0.3"),
                "sed_3d": metric(row["results"], conf, "sed", "3D", "0.3"),
                "bus_bev": metric(row["results"], conf, "bus", "BEV", "0.3"),
                "bus_3d": metric(row["results"], conf, "bus", "3D", "0.3"),
            }
            mean_3d = mean_available([vals["sed_3d"], vals["bus_3d"]])
            lines.append(
                "| {epoch} | {sed_bev} | {sed_3d} | {bus_bev} | {bus_3d} | {mean_3d} |".format(
                    epoch=row["epoch"],
                    sed_bev=format_metric(vals["sed_bev"]),
                    sed_3d=format_metric(vals["sed_3d"]),
                    bus_bev=format_metric(vals["bus_bev"]),
                    bus_3d=format_metric(vals["bus_3d"]),
                    mean_3d=format_metric(mean_3d),
                )
            )
        lines.append("")

        scored = []
        for row in rows:
            mean_3d = mean_available([
                metric(row["results"], conf, "sed", "3D", "0.3"),
                metric(row["results"], conf, "bus", "3D", "0.3"),
            ])
            if mean_3d is not None:
                scored.append((mean_3d, row["epoch"]))
        scored.sort(reverse=True)
        if scored:
            best = ", ".join([f"epoch {epoch}: {score:.2f}" for score, epoch in scored[:3]])
            lines.append(f"Top by mean 3D@0.3: {best}")
            lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    print(f"* Summary JSON: {json_path}")
    print(f"* Summary MD: {md_path}")


def main():
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

    import torch
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0

    confs = [float(item.strip()) for item in args.confs.split(",") if item.strip()]
    conf_keys = [f"{conf:g}" for conf in confs]
    exp_dir = Path(args.exp_dir).resolve()
    ckpt_dir = exp_dir / "models"
    all_ckpts = sorted(ckpt_dir.glob("model_*.pt"), key=checkpoint_epoch)
    if args.epochs != "all":
        wanted = {int(item.strip()) for item in args.epochs.split(",") if item.strip()}
        all_ckpts = [path for path in all_ckpts if checkpoint_epoch(path) in wanted]

    if not all_ckpts:
        raise FileNotFoundError(f"No checkpoints found under {ckpt_dir}")

    print("* PatchDec subset checkpoint evaluation")
    print(f"* CUDA_VISIBLE_DEVICES={args.gpu}")
    print(f"* Source exp: {exp_dir}")
    print(f"* Checkpoints: {[path.name for path in all_ckpts]}")
    print(f"* Subset frames: {args.num_subset}")
    print(f"* Conf thresholds: {conf_keys}")

    pline = PipelineDetection_v1_0(path_cfg=args.config, mode="test")
    pline.cfg.OPTIMIZER.NUM_WORKERS = args.num_workers
    if args.pin_memory:
        pline.cfg.OPTIMIZER.PIN_MEMORY = True
    if args.persistent_workers:
        pline.cfg.OPTIMIZER.PERSISTENT_WORKERS = True
    if args.prefetch_factor is not None:
        pline.cfg.OPTIMIZER.PREFETCH_FACTOR = args.prefetch_factor
    pline.cfg.VAL.NUM_SUBSET = args.num_subset
    pline.val_num_subset = args.num_subset

    path_log = Path(pline.path_log).resolve()
    eval_log_dir = path_log / "subset_eval_stdout"
    eval_log_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for ckpt_path in all_ckpts:
        epoch = checkpoint_epoch(ckpt_path)
        print("")
        print(f"* Evaluating {ckpt_path.name} as epoch {epoch}")
        pline.load_dict_model(str(ckpt_path), is_strict=args.strict)
        reset_seed(args.seed)

        per_epoch_log = eval_log_dir / f"epoch_{epoch}_subset_stdout.log"
        with open(per_epoch_log, "w") as log_file:
            tee = Tee(sys.stdout, log_file)
            with contextlib.redirect_stdout(tee):
                with torch.no_grad():
                    pline.validate_kitti(epoch=epoch, list_conf_thr=confs, is_subset=True)

        text = per_epoch_log.read_text()
        parsed = parse_stdout_blocks(text)
        rows.append({
            "epoch": epoch,
            "checkpoint": str(ckpt_path),
            "stdout_log": str(per_epoch_log),
            "results": parsed,
        })
        write_summary(path_log, rows, conf_keys)

    print("")
    print("* Done.")
    print(f"* Evaluation log dir: {path_log}")


if __name__ == "__main__":
    main()
