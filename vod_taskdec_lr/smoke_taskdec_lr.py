#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

import torch
import yaml
from easydict import EasyDict
from torch.utils.data import DataLoader

from model import VodTaskDecLrSmokeModel
from vod_dataset import VodLrDataset


def load_cfg(path):
    with open(path, "r") as f:
        return EasyDict(yaml.safe_load(f))


def to_device(batch, device):
    out = {}
    for key, value in batch.items():
        if torch.is_tensor(value):
            out[key] = value.to(device)
        else:
            out[key] = value
    return out


def main():
    parser = argparse.ArgumentParser(description="Smoke-test VoD TaskDec L+R adaptation")
    parser.add_argument("--config", default="configs/taskdec_lr_smoke.yml")
    parser.add_argument("--gpu", default=None)
    parser.add_argument("--out", default="logs/taskdec_lr_smoke_result.json")
    args = parser.parse_args()

    cfg = load_cfg(args.config)
    gpu = args.gpu if args.gpu is not None else str(cfg.get("SMOKE", {}).get("GPU", 3))
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    torch.manual_seed(20250215)
    dataset = VodLrDataset(cfg["DATASET"])
    loader = DataLoader(
        dataset,
        batch_size=int(cfg["SMOKE"].get("BATCH_SIZE", 2)),
        shuffle=False,
        num_workers=0,
        collate_fn=dataset.collate_fn,
    )
    model = VodTaskDecLrSmokeModel(cfg).to(device)
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(cfg["SMOKE"].get("LR", 5e-4)))

    steps = int(cfg["SMOKE"].get("STEPS", 2))
    records = []
    for step_idx, batch in enumerate(loader):
        if step_idx >= steps:
            break
        batch = to_device(batch, device)
        optimizer.zero_grad(set_to_none=True)
        output = model(batch)
        output["loss"].backward()
        optimizer.step()
        logging = output["patch_dec_logging"]
        records.append(
            {
                "step": step_idx,
                "frames": batch["frame_ids"],
                "loss": float(output["loss"].detach().cpu()),
                "proxy_loss": float(output["proxy_loss"].cpu()),
                "patch_dec_loss": float(output["patch_dec_loss"].cpu()),
                "fused_shape": list(output["fused_shape"]),
                "logits_shape": list(output["logits_shape"]),
                "fg_patches": logging.get("patch_dec_fg_patches"),
                "fg_ratio": logging.get("patch_dec_fg_ratio"),
                "gate_mean": logging.get("dec_control_fg_gate_mean"),
                "w_lidar": logging.get("dec_control_w_spatial_features_2d"),
                "w_radar": logging.get("dec_control_w_bev_feat"),
            }
        )
        print(json.dumps(records[-1], indent=2))

    result = {
        "ok": len(records) == steps,
        "device": str(device),
        "gpu": gpu,
        "num_dataset_samples": len(dataset),
        "records": records,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
