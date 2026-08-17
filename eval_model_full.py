#!/usr/bin/env python3
"""Run full K-Radar validation for one saved checkpoint."""

import argparse
import contextlib
import json
import os
import re
import shutil
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Full validation for one PatchDec checkpoint")
    parser.add_argument("--config", default="./configs/ASF_patch_dec_v1.yml")
    parser.add_argument("--model", required=True)
    parser.add_argument("--gpu", default="2")
    parser.add_argument("--epoch", type=int, default=None)
    parser.add_argument("--confs", default="0.0,0.3", help="Comma-separated confidence thresholds")
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--conditional", action="store_true", help="Also run conditional/weather validation")
    parser.add_argument("--pin-memory", action="store_true")
    parser.add_argument("--persistent-workers", action="store_true")
    parser.add_argument("--prefetch-factor", type=int, default=None)
    return parser.parse_args()


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


def normalize_conf(value):
    return f"{float(value):g}"


def parse_stdout_eval_results(text):
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
            current_conf = normalize_conf(match.group(1))
            results.setdefault(current_conf, {"all": {}})
            current_cls = None
            current_iou = None
            continue

        match = re.match(r"(\S+)\s+AP\(Average Precision\)@([\d.]+),", line)
        if match and current_conf is not None:
            current_cls = match.group(1)
            current_iou = f"{float(match.group(2)):g}"
            results[current_conf]["all"].setdefault(current_cls, {"BEV": {}, "3D": {}})
            continue

        if current_conf is None or current_cls is None or current_iou is None:
            continue

        match = re.match(r"bev\s+AP:\s*([\d.e+\-]+)", line)
        if match:
            results[current_conf]["all"][current_cls]["BEV"][current_iou] = float(match.group(1))
            continue

        match = re.match(r"3d\s+AP:\s*([\d.e+\-]+)", line)
        if match:
            results[current_conf]["all"][current_cls]["3D"][current_iou] = float(match.group(1))
            continue

    return results


def write_summary(path_log, results):
    summary_json = path_log / "full_eval_summary.json"
    summary_md = path_log / "full_eval_summary.md"
    with open(summary_json, "w") as f:
        json.dump(results, f, indent=2)

    lines = ["# Full Validation Summary", ""]
    for conf in sorted(results.keys(), key=float):
        lines.append(f"## conf={conf}")
        lines.append("")
        lines.append("| Class | BEV@0.7 | BEV@0.5 | BEV@0.3 | 3D@0.7 | 3D@0.5 | 3D@0.3 |")
        lines.append("|-------|---------|---------|---------|--------|--------|--------|")
        all_data = results[conf].get("all", {})
        for cls_name in ["sed", "bus"]:
            cls_data = all_data.get(cls_name, {})
            bev = cls_data.get("BEV", {})
            td = cls_data.get("3D", {})
            lines.append(
                f"| {cls_name} | {bev.get('0.7', 0):.2f} | {bev.get('0.5', 0):.2f} | {bev.get('0.3', 0):.2f} | "
                f"{td.get('0.7', 0):.2f} | {td.get('0.5', 0):.2f} | {td.get('0.3', 0):.2f} |"
            )
        lines.append("")

    with open(summary_md, "w") as f:
        f.write("\n".join(lines))

    print(f"* Full summary JSON: {summary_json}")
    print(f"* Full summary MD: {summary_md}")


def main():
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0

    confs = [float(item.strip()) for item in args.confs.split(",") if item.strip()]
    model_path = Path(args.model).resolve()
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    print("* PatchDec full checkpoint evaluation")
    print(f"* CUDA_VISIBLE_DEVICES={args.gpu}")
    print(f"* Config: {args.config}")
    print(f"* Model: {model_path}")
    print(f"* Epoch tag: {args.epoch}")
    print(f"* Full conf thresholds: {[normalize_conf(c) for c in confs]}")
    print(f"* Conditional: {args.conditional}")

    pline = PipelineDetection_v1_0(path_cfg=args.config, mode="test")
    pline.cfg.OPTIMIZER.NUM_WORKERS = args.num_workers
    if args.pin_memory:
        pline.cfg.OPTIMIZER.PIN_MEMORY = True
    if args.persistent_workers:
        pline.cfg.OPTIMIZER.PERSISTENT_WORKERS = True
    if args.prefetch_factor is not None:
        pline.cfg.OPTIMIZER.PREFETCH_FACTOR = args.prefetch_factor
    pline.load_dict_model(str(model_path), is_strict=args.strict)
    pline.network.eval()

    path_log = Path(pline.path_log).resolve()
    shutil.copy2(os.path.realpath(__file__), path_log / "executed_code.txt")
    print(f"* Eval log dir: {path_log}")

    stdout_log = path_log / "full_eval_stdout.log"
    with open(stdout_log, "w") as log_file:
        tee = Tee(sys.stdout, log_file)
        with contextlib.redirect_stdout(tee):
            pline.validate_kitti(epoch=args.epoch, list_conf_thr=confs, is_subset=False)

    print(f"* Full stdout log: {stdout_log}")
    results = parse_stdout_eval_results(stdout_log.read_text(errors="ignore"))
    write_summary(path_log, results)

    if args.conditional:
        cond_confs = [conf for conf in confs if normalize_conf(conf) == "0.3"] or confs
        cond_stdout_log = path_log / "conditional_eval_stdout.log"
        with open(cond_stdout_log, "w") as log_file:
            tee = Tee(sys.stdout, log_file)
            with contextlib.redirect_stdout(tee):
                pline.validate_kitti_conditional(
                    epoch=args.epoch,
                    list_conf_thr=cond_confs,
                    is_subset=False,
                    is_print_memory=False,
                )
        print(f"* Conditional stdout log: {cond_stdout_log}")

    print("* Done.")


if __name__ == "__main__":
    main()
