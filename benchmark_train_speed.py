#!/usr/bin/env python3
import argparse
import os
import time


def parse_args():
    parser = argparse.ArgumentParser(description="Short train-iteration speed benchmark")
    parser.add_argument("--config", default="./configs/ASF_dec_controlled_gentle.yml")
    parser.add_argument("--gpu", default="0")
    parser.add_argument("--iters", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--num-workers", type=int, default=None)
    parser.add_argument("--pin-memory", action="store_true")
    parser.add_argument("--persistent-workers", action="store_true")
    parser.add_argument("--prefetch-factor", type=int, default=None)
    parser.add_argument("--fast-cudnn", action="store_true")
    parser.add_argument("--allow-tf32", action="store_true")
    return parser.parse_args()


def clear_batch(batch):
    if "pointer" in batch:
        for item in batch["pointer"]:
            for key in item.keys():
                if key != "meta":
                    item[key] = None
    for key in list(batch.keys()):
        batch[key] = None


def main():
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

    import numpy as np
    import torch
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0
    from utils.runtime_utils import apply_runtime_overrides

    pline = PipelineDetection_v1_0(path_cfg=args.config, mode="train")
    apply_runtime_overrides(pline, args)

    pline.network.train()
    data_loader = pline.build_dataloader(
        pline.dataset_train,
        batch_size=pline.cfg.OPTIMIZER.BATCH_SIZE,
        shuffle=True,
        collate_fn=pline.dataset_train.collate_fn,
        drop_last=True,
    )

    total_iters = args.warmup + args.iters
    measured_load = []
    measured_train = []
    measured_total = []
    torch.cuda.reset_peak_memory_stats()

    print("* Train speed benchmark")
    print(f"* GPU: {args.gpu}")
    print(f"* Config: {args.config}")
    print(f"* Batch size: {pline.cfg.OPTIMIZER.BATCH_SIZE}")
    print(f"* Num workers: {pline.cfg.OPTIMIZER.NUM_WORKERS}")
    print(f"* Warmup/measure iters: {args.warmup}/{args.iters}")

    data_iter = iter(data_loader)
    for idx_iter in range(total_iters):
        torch.cuda.synchronize()
        total_start = time.perf_counter()
        load_start = time.perf_counter()
        batch = next(data_iter)
        load_elapsed = time.perf_counter() - load_start

        torch.cuda.synchronize()
        train_start = time.perf_counter()

        if pline.distil:
            with torch.no_grad():
                batch = pline.distil_model(batch)
                batch["ldr_bev_feat"] = batch["spatial_features_2d"]

        pline.optimizer.zero_grad(set_to_none=True)
        out = pline.network(batch)
        if pline.get_loss_from == "head":
            loss = pline.network.head.loss(out)
        else:
            loss = pline.network.loss(out)
        loss.backward()
        pline.optimizer.step()
        if pline.scheduler is not None:
            pline.scheduler.step()

        torch.cuda.synchronize()
        train_elapsed = time.perf_counter() - train_start
        total_elapsed = time.perf_counter() - total_start
        if idx_iter >= args.warmup:
            measured_load.append(load_elapsed)
            measured_train.append(train_elapsed)
            measured_total.append(total_elapsed)
            print(
                f"iter {idx_iter - args.warmup + 1:03d}/{args.iters}: "
                f"load={load_elapsed:.3f}s train={train_elapsed:.3f}s "
                f"total={total_elapsed:.3f}s loss={float(loss.detach().cpu()):.4f}"
            )
        else:
            print(
                f"warmup {idx_iter + 1:03d}/{args.warmup}: "
                f"load={load_elapsed:.3f}s train={train_elapsed:.3f}s total={total_elapsed:.3f}s"
            )

        clear_batch(batch)

    if measured_total:
        peak_gb = torch.cuda.max_memory_allocated() / (1024 ** 3)
        print("* Summary")
        print(f"mean_load_s: {np.mean(measured_load):.4f}")
        print(f"mean_train_s: {np.mean(measured_train):.4f}")
        print(f"mean_total_s: {np.mean(measured_total):.4f}")
        print(f"median_total_s: {np.median(measured_total):.4f}")
        print(f"min_total_s: {np.min(measured_total):.4f}")
        print(f"max_total_s: {np.max(measured_total):.4f}")
        print(f"iters_per_hour: {3600.0 / np.mean(measured_total):.1f}")
        print(f"peak_allocated_gb: {peak_gb:.2f}")


if __name__ == "__main__":
    main()
