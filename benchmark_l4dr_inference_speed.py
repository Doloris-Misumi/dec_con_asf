#!/usr/bin/env python3
"""Benchmark L4DR single-frame inference latency on the local K-Radar copy."""

import argparse
import gc
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="L4DR inference speed benchmark")
    parser.add_argument("--repo-root", default="/home/hongsheng/L4DR/K-Radar-main-repo")
    parser.add_argument("--config", default="configs/cfg_PP_L4DR_v1.1.yml")
    parser.add_argument("--model", default="/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v1.1-model_34.pt")
    parser.add_argument("--data-root", default="/home/hongsheng/k_radar_dataset")
    parser.add_argument("--gpu", default="3")
    parser.add_argument("--tag", default="l4dr_v1_1_model34_lr_local_sparsecube")
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--iters", type=int, default=100)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--label-version", default="v1_0")
    parser.add_argument("--out-dir", default="/home/hongsheng/dec_con_asf/results/efficiency_260902")
    parser.add_argument("--strict", action="store_true")
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
    sys.path = filtered_path
    sys.path = [str(ops_root), str(repo_root)] + sys.path
    os.chdir(repo_root)


def patch_sparse_radar_loader(data_root):
    import numpy as np
    import datasets.kradar_detection_v2_0 as kradar_v2

    def get_rdr_sparse_local(self, dict_item):
        seq = dict_item["meta"]["seq"]
        rdr_idx = dict_item["meta"]["idx"]["rdr"]
        official_path = Path(self.rdr_sparse.dir) / seq / f"sprdr_{rdr_idx}.npy"
        if official_path.exists():
            path = official_path
            source = "sprdr_symlink_to_sparse_cube" if official_path.is_symlink() else "sprdr"
        else:
            path = Path(data_root) / seq / "sparse_cube" / f"cube_{rdr_idx}.npy"
            source = "sparse_cube"
        rdr_sparse = np.load(path)[:, : self.rdr_sparse.n_used]
        dict_item["rdr_sparse"] = rdr_sparse
        dict_item["meta"]["rdr_sparse_source"] = source
        dict_item["meta"]["rdr_sparse_path"] = str(path)
        return dict_item

    kradar_v2.KRadarDetection_v2_0.get_rdr_sparse = get_rdr_sparse_local


def move_batch_to_cuda(batch, torch):
    for key, value in list(batch.items()):
        if torch.is_tensor(value):
            batch[key] = value.cuda(non_blocking=True)
    return batch


def clear_batch(batch):
    if not isinstance(batch, dict):
        return
    for key in list(batch.keys()):
        batch[key] = None


def summarize(values):
    return {
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def write_markdown(path, result):
    lines = [
        f"# Inference Efficiency: {result['tag']}",
        "",
        f"Date: {result['date']}",
        "",
        f"- Repo: `{result['repo_root']}`",
        f"- Config: `{result['config']}`",
        f"- Model: `{result['model']}`",
        f"- Data root: `{result['data_root']}`",
        f"- GPU: `{result['gpu']}`",
        f"- Modality: LiDAR + radar",
        f"- Label version for loader: `{result['label_version']}`",
        f"- Radar source: `{result['radar_source_note']}`",
        f"- Warmup / measured iters: `{result['warmup']}` / `{result['measured_iters']}`",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Parameters (M) | {result['params_m']:.2f} |",
        f"| Trainable parameters (M) | {result['trainable_params_m']:.2f} |",
        f"| Mean forward latency (ms) | {result['forward_ms']['mean']:.2f} |",
        f"| Median forward latency (ms) | {result['forward_ms']['median']:.2f} |",
        f"| Forward FPS | {result['forward_fps']:.2f} |",
        f"| Mean data load latency (ms) | {result['load_ms']['mean']:.2f} |",
        f"| Mean CPU-to-GPU transfer latency (ms) | {result['transfer_ms']['mean']:.2f} |",
        f"| Mean end-to-end latency (ms) | {result['total_ms']['mean']:.2f} |",
        f"| End-to-end FPS | {result['e2e_fps']:.2f} |",
        f"| Model memory after load (GB) | {result['model_allocated_gb']:.2f} |",
        f"| Peak allocated memory (GB) | {result['peak_allocated_gb']:.2f} |",
        f"| Peak reserved memory (GB) | {result['peak_reserved_gb']:.2f} |",
    ]
    path.write_text("\n".join(lines) + "\n")


def main():
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    configure_imports(args.repo_root)
    patch_sparse_radar_loader(args.data_root)

    import torch
    import numpy as np
    from torch.utils.data import DataLoader
    from utils.util_config import cfg, cfg_from_yaml_file
    from models.skeletons import build_skeleton
    from datasets.kradar_detection_v2_0 import KRadarDetection_v2_0

    repo_root = Path(args.repo_root).resolve()
    config_path = Path(args.config)
    model_path = Path(args.model)
    data_root = Path(args.data_root).resolve()
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    random.seed(2023)
    np.random.seed(2023)
    torch.manual_seed(2023)

    cfg_from_yaml_file(str(config_path), cfg)
    cfg.GENERAL.LOGGING.IS_LOGGING = False
    cfg.DATASET.path_data.list_dir_kradar = [str(data_root)]
    cfg.DATASET.label_version = args.label_version
    cfg.DATASET.rdr_sparse.dir = str(data_root)
    cfg.OPTIMIZER.NUM_WORKERS = args.num_workers

    print(f"* Benchmark tag: {args.tag}", flush=True)
    print(f"* Repo root: {repo_root}", flush=True)
    print(f"* Config: {config_path}", flush=True)
    print(f"* Model: {model_path}", flush=True)
    print(f"* Data root: {data_root}", flush=True)
    print(f"* GPU: {args.gpu}", flush=True)

    dataset = KRadarDetection_v2_0(cfg=cfg, split="test")
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=dataset.collate_fn,
        num_workers=args.num_workers,
        drop_last=False,
        pin_memory=False,
    )

    network = build_skeleton(cfg).cuda().eval()
    checkpoint = torch.load(str(model_path), map_location="cpu")
    missing, unexpected = network.load_state_dict(checkpoint, strict=args.strict)
    print(f"* Dataset length: {len(dataset)}", flush=True)
    print(f"* Missing keys: {len(missing)}; unexpected keys: {len(unexpected)}", flush=True)

    params = sum(p.numel() for p in network.parameters())
    trainable_params = sum(p.numel() for p in network.parameters() if p.requires_grad)
    model_allocated_gb = torch.cuda.memory_allocated() / (1024 ** 3)

    total_iters = args.warmup + args.iters
    forward_ms = []
    load_ms = []
    transfer_ms = []
    total_ms = []
    source_counts = {}
    data_iter = iter(loader)

    torch.cuda.synchronize()
    for idx in range(total_iters):
        total_start = time.perf_counter()
        load_start = time.perf_counter()
        try:
            batch = next(data_iter)
        except StopIteration:
            break
        load_elapsed = (time.perf_counter() - load_start) * 1000.0

        for meta in batch.get("meta", []):
            source = meta.get("rdr_sparse_source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

        transfer_start = time.perf_counter()
        move_batch_to_cuda(batch, torch)
        torch.cuda.synchronize()
        transfer_elapsed = (time.perf_counter() - transfer_start) * 1000.0

        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        with torch.no_grad():
            out = network(batch)
        end.record()
        torch.cuda.synchronize()
        forward_elapsed = start.elapsed_time(end)
        total_elapsed = (time.perf_counter() - total_start) * 1000.0

        if idx == args.warmup - 1:
            torch.cuda.reset_peak_memory_stats()
        elif idx >= args.warmup:
            forward_ms.append(forward_elapsed)
            load_ms.append(load_elapsed)
            transfer_ms.append(transfer_elapsed)
            total_ms.append(total_elapsed)
            if len(forward_ms) % 10 == 0:
                print(f"* measured {len(forward_ms)}/{args.iters}", flush=True)

        out = None
        clear_batch(batch)
        batch = None

    torch.cuda.synchronize()
    gc.collect()

    if not forward_ms:
        raise RuntimeError("No measured iterations were completed.")

    radar_source_note = ", ".join(f"{k}:{v}" for k, v in sorted(source_counts.items()))
    result = {
        "tag": args.tag,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo_root": str(repo_root),
        "config": str(config_path),
        "model": str(model_path),
        "data_root": str(data_root),
        "gpu": str(args.gpu),
        "label_version": args.label_version,
        "warmup": args.warmup,
        "measured_iters": len(forward_ms),
        "batch_size": args.batch_size,
        "num_workers": args.num_workers,
        "params_m": params / 1e6,
        "trainable_params_m": trainable_params / 1e6,
        "model_allocated_gb": model_allocated_gb,
        "forward_ms": summarize(forward_ms),
        "load_ms": summarize(load_ms),
        "transfer_ms": summarize(transfer_ms),
        "total_ms": summarize(total_ms),
        "forward_fps": 1000.0 / statistics.fmean(forward_ms),
        "e2e_fps": 1000.0 / statistics.fmean(total_ms),
        "peak_allocated_gb": torch.cuda.max_memory_allocated() / (1024 ** 3),
        "peak_reserved_gb": torch.cuda.max_memory_reserved() / (1024 ** 3),
        "radar_source_counts": source_counts,
        "radar_source_note": radar_source_note,
        "missing_keys": list(missing),
        "unexpected_keys": list(unexpected),
    }

    json_path = out_dir / f"{args.tag}.json"
    md_path = out_dir / f"{args.tag}.md"
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    write_markdown(md_path, result)
    print(f"* JSON: {json_path}", flush=True)
    print(f"* MD: {md_path}", flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
