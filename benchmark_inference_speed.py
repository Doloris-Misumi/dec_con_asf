#!/usr/bin/env python3
"""Benchmark single-frame inference latency for K-Radar fusion models."""

import argparse
import gc
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="K-Radar inference speed benchmark")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--gpu", default="0")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--infer-mode", default="rlc")
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--iters", type=int, default=100)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--out-dir", default="/home/hongsheng/dec_con_asf/results/efficiency_260902")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def configure_imports(repo_root):
    repo_root = Path(repo_root).resolve()
    ops_root = repo_root / "ops"
    script_dir = Path(__file__).resolve().parent
    new_path = []
    for item in sys.path:
        if not item:
            new_path.append(item)
            continue
        try:
            if Path(item).resolve() == script_dir and script_dir != repo_root:
                continue
        except OSError:
            pass
        new_path.append(item)
    sys.path = [str(ops_root), str(repo_root)] + new_path
    os.chdir(repo_root)


def infer_mode_to_avail_feats(infer_mode):
    infer_mode = str(infer_mode).lower()
    avail = []
    if "c" in infer_mode:
        avail.append("cam_bev_feat")
    if "l" in infer_mode:
        avail.append("spatial_features_2d")
    if "r" in infer_mode:
        avail.append("bev_feat")
    if not avail:
        raise ValueError(f"Invalid infer mode: {infer_mode}")
    return avail


def clear_batch(batch):
    if not isinstance(batch, dict):
        return
    if "pointer" in batch:
        for item in batch["pointer"]:
            for key in list(item.keys()):
                if key != "meta":
                    item[key] = None
    for key in list(batch.keys()):
        batch[key] = None


def build_test_loader(pline, torch):
    if hasattr(pline, "build_dataloader"):
        return pline.build_dataloader(
            pline.dataset_test,
            batch_size=1,
            shuffle=False,
            collate_fn=pline.dataset_test.collate_fn,
            drop_last=False,
        )
    return torch.utils.data.DataLoader(
        pline.dataset_test,
        batch_size=1,
        shuffle=False,
        collate_fn=pline.dataset_test.collate_fn,
        num_workers=int(pline.cfg.OPTIMIZER.get("NUM_WORKERS", 0)),
        drop_last=False,
    )


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
        f"- GPU: `{result['gpu']}`",
        f"- Infer mode: `{result['infer_mode']}`",
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

    import torch
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0

    repo_root = Path(args.repo_root).resolve()
    config_path = Path(args.config)
    model_path = Path(args.model)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    if not model_path.is_absolute():
        model_path = repo_root / model_path
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"* Benchmark tag: {args.tag}", flush=True)
    print(f"* Repo root: {repo_root}", flush=True)
    print(f"* Config: {config_path}", flush=True)
    print(f"* Model: {model_path}", flush=True)
    print(f"* GPU: {args.gpu}", flush=True)

    pline = PipelineDetection_v1_0(path_cfg=str(config_path), mode="test")
    pline.cfg.OPTIMIZER.NUM_WORKERS = args.num_workers
    pline.load_dict_model(str(model_path), is_strict=args.strict)
    pline.network.eval()

    params = sum(p.numel() for p in pline.network.parameters())
    trainable_params = sum(p.numel() for p in pline.network.parameters() if p.requires_grad)
    model_allocated_gb = torch.cuda.memory_allocated() / (1024 ** 3)
    avail_feats = (
        pline.infer_mode_to_avail_feats(args.infer_mode)
        if hasattr(pline, "infer_mode_to_avail_feats")
        else infer_mode_to_avail_feats(args.infer_mode)
    )

    loader = build_test_loader(pline, torch)

    total_iters = args.warmup + args.iters
    forward_ms = []
    load_ms = []
    total_ms = []
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
        batch["avail_feats"] = avail_feats

        torch.cuda.synchronize()
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        with torch.no_grad():
            out = pline.network(batch)
        end.record()
        torch.cuda.synchronize()
        forward_elapsed = start.elapsed_time(end)
        total_elapsed = (time.perf_counter() - total_start) * 1000.0

        if idx == args.warmup - 1:
            torch.cuda.reset_peak_memory_stats()
        elif idx >= args.warmup:
            forward_ms.append(forward_elapsed)
            load_ms.append(load_elapsed)
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

    result = {
        "tag": args.tag,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo_root": str(repo_root),
        "config": str(config_path),
        "model": str(model_path),
        "gpu": str(args.gpu),
        "infer_mode": args.infer_mode,
        "warmup": args.warmup,
        "measured_iters": len(forward_ms),
        "params_m": params / 1e6,
        "trainable_params_m": trainable_params / 1e6,
        "model_allocated_gb": model_allocated_gb,
        "forward_ms": summarize(forward_ms),
        "load_ms": summarize(load_ms),
        "total_ms": summarize(total_ms),
        "forward_fps": 1000.0 / statistics.fmean(forward_ms),
        "e2e_fps": 1000.0 / statistics.fmean(total_ms),
        "peak_allocated_gb": torch.cuda.max_memory_allocated() / (1024 ** 3),
        "peak_reserved_gb": torch.cuda.max_memory_reserved() / (1024 ** 3),
    }

    json_path = out_dir / f"{args.tag}.json"
    md_path = out_dir / f"{args.tag}.md"
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    write_markdown(md_path, result)
    print(f"* JSON: {json_path}", flush=True)
    print(f"* MD: {md_path}", flush=True)


if __name__ == "__main__":
    main()
