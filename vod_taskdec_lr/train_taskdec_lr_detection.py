#!/usr/bin/env python3
import argparse
import copy
import json
import os
import random
import shutil
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
OPS_ROOT = PROJECT_ROOT / "ops"
if str(OPS_ROOT) not in sys.path:
    sys.path.insert(0, str(OPS_ROOT))

import numpy as np
import torch
import yaml
from easydict import EasyDict
from torch.utils.data import DataLoader

from vod_taskdec_lr.model import VodTaskDecLrAnchorModel
from vod_taskdec_lr.vod_dataset import VodLrDataset


def to_easydict(value):
    if isinstance(value, dict):
        return EasyDict({key: to_easydict(val) for key, val in value.items()})
    if isinstance(value, list):
        return [to_easydict(item) for item in value]
    return value


def to_plain(value):
    if isinstance(value, dict):
        return {key: to_plain(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    return value


def load_cfg(path):
    with open(path, "r") as f:
        return to_easydict(yaml.safe_load(f))


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def to_device(batch, device):
    output = {}
    for key, value in batch.items():
        output[key] = value.to(device, non_blocking=True) if torch.is_tensor(value) else value
    return output


def mean_dict(records):
    total = {}
    counts = {}
    for record in records:
        for key, value in record.items():
            if isinstance(value, (int, float)) and np.isfinite(value):
                total[key] = total.get(key, 0.0) + float(value)
                counts[key] = counts.get(key, 0) + 1
    return {key: total[key] / counts[key] for key in sorted(total)}


def save_checkpoint(path, model, optimizer, scheduler, cfg, epoch):
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict() if scheduler is not None else None,
            "cfg": to_plain(cfg),
        },
        path,
    )


def build_run_dir(args, cfg):
    timestamp = time.strftime("%y%m%d_%H%M%S")
    run_name = args.run_name or f"exp_{timestamp}_VoDTaskDecLRAnchor_ep{args.epochs or cfg.TRAIN.EPOCHS}_gpu{args.gpu}"
    run_dir = PROJECT_ROOT / "vod_taskdec_lr" / "runs" / run_name
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(args.config, run_dir / "config.yml")
    return run_dir


def main():
    parser = argparse.ArgumentParser(description="Train VoD TaskDec L+R with ASF-style anchor head")
    parser.add_argument("--config", default="vod_taskdec_lr/configs/taskdec_lr_anchor_train.yml")
    parser.add_argument("--gpu", default="3")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--num-workers", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    cfg = load_cfg(args.config)
    if args.epochs is not None:
        cfg.TRAIN.EPOCHS = args.epochs
    if args.batch_size is not None:
        cfg.TRAIN.BATCH_SIZE = args.batch_size
    if args.num_workers is not None:
        cfg.TRAIN.NUM_WORKERS = args.num_workers

    set_seed(int(cfg.GENERAL.SEED))
    torch.backends.cudnn.benchmark = True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run_dir = build_run_dir(args, cfg)
    metrics_path = run_dir / "metrics.jsonl"
    print(f"[run_dir] {run_dir}", flush=True)
    print(f"[device] {device} cuda_visible={os.environ.get('CUDA_VISIBLE_DEVICES')}", flush=True)

    dataset = VodLrDataset(cfg.DATASET)
    loader = DataLoader(
        dataset,
        batch_size=int(cfg.TRAIN.BATCH_SIZE),
        shuffle=True,
        num_workers=int(cfg.TRAIN.NUM_WORKERS),
        pin_memory=True,
        drop_last=True,
        collate_fn=dataset.collate_fn,
    )
    model = VodTaskDecLrAnchorModel(cfg).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(cfg.TRAIN.LR),
        weight_decay=float(cfg.TRAIN.WEIGHT_DECAY),
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=max(int(cfg.TRAIN.EPOCHS), 1),
        eta_min=float(cfg.TRAIN.MIN_LR),
    )

    num_params = sum(param.numel() for param in model.parameters() if param.requires_grad)
    print(f"[data] split={cfg.DATASET.SPLIT} samples={len(dataset)} batch_size={cfg.TRAIN.BATCH_SIZE}", flush=True)
    print(f"[model] trainable_params={num_params:,}", flush=True)

    for epoch in range(int(cfg.TRAIN.EPOCHS)):
        model.train()
        epoch_records = []
        start_time = time.time()
        for step, batch in enumerate(loader):
            if args.max_steps is not None and step >= args.max_steps:
                break
            batch = to_device(batch, device)
            optimizer.zero_grad(set_to_none=True)
            output = model(batch)
            loss = output["loss"]
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), float(cfg.TRAIN.GRAD_NORM_CLIP))
            optimizer.step()

            logging = dict(output["logging"])
            logging["epoch"] = epoch
            logging["step"] = step
            logging["lr"] = optimizer.param_groups[0]["lr"]
            logging["grad_norm"] = float(grad_norm)
            epoch_records.append(logging)

            if step % int(cfg.TRAIN.LOG_INTERVAL) == 0:
                print(json.dumps(logging, sort_keys=True), flush=True)

        scheduler.step()
        summary = mean_dict(epoch_records)
        summary.update(
            {
                "epoch": epoch,
                "num_steps": len(epoch_records),
                "seconds": round(time.time() - start_time, 2),
                "lr_after_epoch": optimizer.param_groups[0]["lr"],
            }
        )
        with metrics_path.open("a") as f:
            f.write(json.dumps(summary, sort_keys=True) + "\n")
        print("[epoch_summary] " + json.dumps(summary, sort_keys=True), flush=True)

        if (epoch + 1) % int(cfg.TRAIN.SAVE_EVERY) == 0:
            ckpt_path = run_dir / "checkpoints" / f"model_{epoch}.pt"
            save_checkpoint(ckpt_path, model, optimizer, scheduler, cfg, epoch)
            print(f"[checkpoint] {ckpt_path}", flush=True)

    print(f"[done] metrics={metrics_path}", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
