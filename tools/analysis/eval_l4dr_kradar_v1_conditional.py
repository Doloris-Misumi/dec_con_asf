#!/usr/bin/env python3
"""Run local conditional K-Radar v1.0 evaluation for an L4DR checkpoint."""

import argparse
import json
import os
import random
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default="/home/hongsheng/L4DR/K-Radar-main-repo")
    parser.add_argument("--config", default="configs/cfg_PP_L4DR_v1.1.yml")
    parser.add_argument("--model", default="/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v1.1-model_34.pt")
    parser.add_argument("--data-root", default="/home/hongsheng/k_radar_dataset")
    parser.add_argument("--gpu", default="3")
    parser.add_argument("--tag", default="l4dr_v1_1_model34_local_eval_260910")
    parser.add_argument("--out-dir", default="/home/hongsheng/dec_con_asf/results/l4dr_kradar_v1_local_eval_260910")
    parser.add_argument("--conf-thr", default="0.3", help="Comma-separated confidence thresholds.")
    parser.add_argument("--label-version", default="v1_0")
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--subset", action="store_true")
    parser.add_argument("--num-subset", type=int, default=50)
    parser.add_argument("--epoch", type=int, default=None)
    return parser.parse_args()


def configure_imports(repo_root):
    repo_root = Path(repo_root).resolve()
    ops_root = repo_root / "ops"
    script_dir = Path(__file__).resolve().parent
    filtered_path = []
    for item in sys.path:
        if not item:
            continue
        try:
            if Path(item).resolve() == script_dir:
                continue
        except OSError:
            pass
        filtered_path.append(item)
    sys.path = [str(ops_root), str(repo_root)] + filtered_path
    os.chdir(repo_root)


def patch_sparse_radar_loader(data_root):
    import numpy as np
    import datasets.kradar_detection_v2_0 as kradar_v2

    data_root = Path(data_root)

    def get_rdr_sparse_local(self, dict_item):
        seq = dict_item["meta"]["seq"]
        rdr_idx = dict_item["meta"]["idx"]["rdr"]
        official_path = Path(self.rdr_sparse.dir) / seq / f"sprdr_{rdr_idx}.npy"
        if official_path.exists():
            path = official_path
            source = "sprdr_symlink_to_sparse_cube" if official_path.is_symlink() else "sprdr"
        else:
            path = data_root / seq / "sparse_cube" / f"cube_{rdr_idx}.npy"
            source = "sparse_cube"
        rdr_sparse = np.load(path)[:, : self.rdr_sparse.n_used]
        dict_item["rdr_sparse"] = rdr_sparse
        dict_item["meta"]["rdr_sparse_source"] = source
        dict_item["meta"]["rdr_sparse_path"] = str(path)
        return dict_item

    kradar_v2.KRadarDetection_v2_0.get_rdr_sparse = get_rdr_sparse_local


def patch_empty_condition_eval():
    import pipelines.pipeline_detection_v1_0 as pipeline_mod

    original_eval = pipeline_mod.get_official_eval_result
    class_names = ["sed", "bus", "mot", "bic", "big", "ped", "peg"]

    def safe_get_official_eval_result(gt_annos, dt_annos, idx_cls_val, *args, **kwargs):
        if len(gt_annos) == 0 or len(dt_annos) == 0:
            is_return_with_dict = bool(kwargs.get("is_return_with_dict", False))
            cls_name = class_names[idx_cls_val] if 0 <= idx_cls_val < len(class_names) else str(idx_cls_val)
            metrics = {
                "cls": cls_name,
                "iou": [0.7, 0.5, 0.3],
                "bev": [0.0, 0.0, 0.0],
                "3d": [0.0, 0.0, 0.0],
            }
            text = "Empty condition in local wrapper; AP values are set to 0.0.\n"
            return (metrics, text) if is_return_with_dict else text
        return original_eval(gt_annos, dt_annos, idx_cls_val, *args, **kwargs)

    pipeline_mod.get_official_eval_result = safe_get_official_eval_result


def write_local_config(args, out_dir, conf_thrs):
    import yaml

    repo_root = Path(args.repo_root).resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    with config_path.open() as f:
        cfg_obj = yaml.safe_load(f)

    log_root = out_dir / "l4dr_logs"
    cfg_obj["GENERAL"]["NAME"] = "cfg_PP_L4DR_v1.1_local_eval"
    cfg_obj["GENERAL"]["LOGGING"]["IS_LOGGING"] = True
    cfg_obj["GENERAL"]["LOGGING"]["PATH_LOGGING"] = str(log_root)
    cfg_obj["GENERAL"]["LOGGING"]["IS_SAVE_MODEL"] = False
    cfg_obj["GENERAL"]["RESUME"]["IS_RESUME"] = False
    cfg_obj["DATASET"]["path_data"]["list_dir_kradar"] = [str(Path(args.data_root).resolve())]
    cfg_obj["DATASET"]["label_version"] = args.label_version
    cfg_obj["DATASET"]["rdr_sparse"]["dir"] = str(Path(args.data_root).resolve())
    cfg_obj["OPTIMIZER"]["NUM_WORKERS"] = args.num_workers
    cfg_obj["VAL"]["IS_CONSIDER_VAL_SUBSET"] = bool(args.subset)
    cfg_obj["VAL"]["NUM_SUBSET"] = int(args.num_subset)
    cfg_obj["VAL"]["LIST_VAL_CONF_THR"] = conf_thrs

    local_config = out_dir / "cfg_PP_L4DR_v1.1_local_eval.yml"
    with local_config.open("w") as f:
        yaml.safe_dump(cfg_obj, f, sort_keys=False)
    return local_config, log_root


def parse_complete_results(path):
    text = Path(path).read_text(errors="replace")
    blocks = []
    current = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                blocks.append(current)
                current = {}
            continue
        if line.startswith("Conf thr:"):
            if current:
                blocks.append(current)
                current = {}
            match = re.match(r"Conf thr:\s*([^,]+),\s*Condition:\s*(.+)", line)
            if match:
                current["conf_thr"] = match.group(1).strip()
                current["condition"] = match.group(2).strip()
        elif line.startswith("cls:"):
            current["cls"] = line.split(":", 1)[1].strip()
        elif line.startswith("iou:"):
            current["iou"] = [float(x) for x in line.split(":", 1)[1].split()]
        elif line.startswith("bev:"):
            current["bev"] = [float(x) for x in line.split(":", 1)[1].split()]
        elif line.startswith("3d"):
            current["3d"] = [float(x) for x in line.split(":", 1)[1].split()]
    if current:
        blocks.append(current)
    return blocks


def write_summary(out_dir, args, conf_thrs, pline_path_log, copied_files):
    summaries = {}
    for conf in conf_thrs:
        raw_path = out_dir / "raw" / f"complete_results_none_{conf}.txt"
        if not raw_path.exists():
            continue
        for block in parse_complete_results(raw_path):
            summaries[(str(conf), block["condition"], block["cls"])] = block

    json_ready = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tag": args.tag,
        "repo_root": str(Path(args.repo_root).resolve()),
        "config": str(Path(args.config).resolve()) if Path(args.config).is_absolute() else str(Path(args.repo_root).resolve() / args.config),
        "local_config": str(out_dir / "cfg_PP_L4DR_v1.1_local_eval.yml"),
        "model": str(Path(args.model).resolve()),
        "data_root": str(Path(args.data_root).resolve()),
        "gpu": str(args.gpu),
        "label_version": args.label_version,
        "subset": bool(args.subset),
        "num_subset": int(args.num_subset),
        "conf_thrs": [str(x) for x in conf_thrs],
        "pipeline_log_dir": str(pline_path_log),
        "copied_files": [str(path) for path in copied_files],
        "metrics": [
            {
                "conf_thr": key[0],
                "condition": key[1],
                "cls": key[2],
                "iou": value.get("iou", []),
                "bev": value.get("bev", []),
                "3d": value.get("3d", []),
            }
            for key, value in sorted(summaries.items())
        ],
    }
    json_path = out_dir / "summary.json"
    json_path.write_text(json.dumps(json_ready, indent=2) + "\n")

    lines = [
        "# L4DR K-Radar v1.0 Local Evaluation",
        "",
        f"Date: {json_ready['date']}",
        "",
        f"- Tag: `{args.tag}`",
        f"- Repo: `{json_ready['repo_root']}`",
        f"- Config: `{json_ready['config']}`",
        f"- Local config: `{json_ready['local_config']}`",
        f"- Model: `{json_ready['model']}`",
        f"- Data root: `{json_ready['data_root']}`",
        f"- Label version: `{args.label_version}`",
        f"- Subset: `{args.subset}`",
        f"- Pipeline log dir: `{pline_path_log}`",
        "",
    ]

    for conf in conf_thrs:
        all_key = (str(conf), "all", "sed")
        if all_key in summaries:
            block = summaries[all_key]
            iou = block["iou"]
            bev = block["bev"]
            ap3d = block["3d"]
            lines.extend([
                f"## Overall, conf={conf}",
                "",
                "| Metric | IoU=0.7 | IoU=0.5 | IoU=0.3 |",
                "|---|---:|---:|---:|",
                f"| APBEV | {bev[0]:.2f} | {bev[1]:.2f} | {bev[2]:.2f} |",
                f"| AP3D | {ap3d[0]:.2f} | {ap3d[1]:.2f} | {ap3d[2]:.2f} |",
                "",
            ])

        weather_order = ["normal", "overcast", "fog", "rain", "sleet", "lightsnow", "heavysnow", "unnormal"]
        present = [w for w in weather_order if (str(conf), w, "sed") in summaries]
        if present:
            lines.extend([
                f"## Weather AP3D, conf={conf}",
                "",
                "| Condition | AP3D@0.7 | AP3D@0.5 | AP3D@0.3 | APBEV@0.7 | APBEV@0.5 | APBEV@0.3 |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ])
            for condition in present:
                block = summaries[(str(conf), condition, "sed")]
                bev = block["bev"]
                ap3d = block["3d"]
                lines.append(
                    f"| {condition} | {ap3d[0]:.2f} | {ap3d[1]:.2f} | {ap3d[2]:.2f} | "
                    f"{bev[0]:.2f} | {bev[1]:.2f} | {bev[2]:.2f} |"
                )
            lines.append("")

    if copied_files:
        lines.extend(["## Raw Files", ""])
        for path in copied_files:
            lines.append(f"- `{path}`")
        lines.append("")

    md_path = out_dir / "summary.md"
    md_path.write_text("\n".join(lines) + "\n")
    return md_path, json_path


def main():
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw").mkdir(exist_ok=True)
    conf_thrs = [float(x.strip()) for x in args.conf_thr.split(",") if x.strip()]

    configure_imports(args.repo_root)
    patch_sparse_radar_loader(args.data_root)
    patch_empty_condition_eval()

    import numpy as np
    import torch
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0

    random.seed(2023)
    np.random.seed(2023)
    torch.manual_seed(2023)

    local_config, _ = write_local_config(args, out_dir, conf_thrs)
    print(f"* Local config: {local_config}", flush=True)
    print(f"* Model: {args.model}", flush=True)
    print(f"* Data root: {args.data_root}", flush=True)
    print(f"* GPU: {args.gpu}", flush=True)

    pline = PipelineDetection_v1_0(path_cfg=str(local_config), mode="test", rank=-1, tag=args.tag)
    print(f"* Dataset length: {len(pline.dataset_test)}", flush=True)
    print(f"* Pipeline log dir: {pline.path_log}", flush=True)
    pline.load_dict_model(args.model)
    print("* Model loaded.", flush=True)
    pline.network.eval()
    with torch.no_grad():
        pline.validate_kitti_conditional(
            epoch=args.epoch,
            list_conf_thr=conf_thrs,
            is_subset=args.subset,
            is_print_memory=False,
            savevis=False,
        )

    copied_files = []
    dir_epoch = "none" if args.epoch is None else (f"epoch_{args.epoch}_subset" if args.subset else f"epoch_{args.epoch}_total")
    for conf in conf_thrs:
        src = Path(pline.path_log) / "test_kitti" / dir_epoch / str(conf) / "complete_results.txt"
        dst = out_dir / "raw" / f"complete_results_{dir_epoch}_{conf}.txt"
        if src.exists():
            shutil.copy2(src, dst)
            copied_files.append(dst)
        else:
            print(f"* Warning: missing expected result file: {src}", flush=True)

    md_path, json_path = write_summary(out_dir, args, conf_thrs, pline.path_log, copied_files)
    print(f"* Summary MD: {md_path}", flush=True)
    print(f"* Summary JSON: {json_path}", flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
