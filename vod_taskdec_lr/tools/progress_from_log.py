#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
from pathlib import Path


def parse_start_time(log_path):
    match = re.search(r"_(\d{6})_(\d{6})\.log$", log_path.name)
    if not match:
        return None
    date_part, time_part = match.groups()
    return dt.datetime.strptime(date_part + time_part, "%y%m%d%H%M%S")


def fmt_seconds(seconds):
    seconds = max(int(seconds), 0)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    if days:
        return f"{days}d {hours:02d}h {minutes:02d}m"
    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    if minutes:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s"


def load_records(log_path):
    latest = None
    summaries = []
    run_dir = None
    for raw in log_path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if line.startswith("[run_dir]"):
            run_dir = line.split(" ", 1)[1]
        elif line.startswith("{"):
            try:
                latest = json.loads(line)
            except json.JSONDecodeError:
                pass
        elif line.startswith("[epoch_summary]"):
            try:
                summaries.append(json.loads(line.split(" ", 1)[1]))
            except (IndexError, json.JSONDecodeError):
                pass
    return run_dir, latest, summaries


def main():
    parser = argparse.ArgumentParser(description="Summarize VoD TaskDec training progress from launcher log")
    parser.add_argument("log")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--steps-per-epoch", type=int, default=2569)
    args = parser.parse_args()

    log_path = Path(args.log)
    run_dir, latest, summaries = load_records(log_path)
    if latest is None and not summaries:
        raise SystemExit(f"No training records found in {log_path}")

    now = dt.datetime.now()
    start = parse_start_time(log_path) or now
    elapsed = max((now - start).total_seconds(), 1.0)

    if summaries:
        completed_epochs = int(summaries[-1].get("epoch", -1)) + 1
        seconds_per_epoch = sum(float(item.get("seconds", 0.0)) for item in summaries) / len(summaries)
        eta = seconds_per_epoch * max(args.epochs - completed_epochs, 0)
        speed_text = f"{args.steps_per_epoch / seconds_per_epoch:.2f} it/s"
        cur_epoch = completed_epochs
        cur_step = 0
        progress = completed_epochs / args.epochs
        source = "epoch summaries"
    else:
        cur_epoch = int(latest.get("epoch", 0))
        cur_step = int(latest.get("step", 0)) + 1
        done_steps = cur_epoch * args.steps_per_epoch + cur_step
        total_steps = args.epochs * args.steps_per_epoch
        speed = done_steps / elapsed
        eta = (total_steps - done_steps) / max(speed, 1e-9)
        speed_text = f"{speed:.2f} it/s ({1.0 / max(speed, 1e-9):.3f}s/it)"
        progress = done_steps / total_steps
        source = "wall-time estimate"

    print(f"log: {log_path}")
    if run_dir:
        print(f"run: {run_dir}")
    print(f"source: {source}")
    print(f"progress: epoch {cur_epoch}/{args.epochs - 1}, step {cur_step}/{args.steps_per_epoch}, total {progress * 100:.2f}%")
    print(f"elapsed: {fmt_seconds(elapsed)}")
    print(f"speed: {speed_text}")
    print(f"eta: {fmt_seconds(eta)}")
    record = latest or summaries[-1]
    keys = ["total_loss", "det_loss", "rpn_loss_cls", "rpn_loss_loc", "rpn_loss_dir", "patch_dec_loss", "lr"]
    loss_text = ", ".join(f"{key}={record[key]:.4g}" for key in keys if key in record)
    if loss_text:
        print(f"latest: {loss_text}")


if __name__ == "__main__":
    main()
