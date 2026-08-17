import json
import os


def add_runtime_args(parser):
    parser.add_argument("--num-workers", type=int, default=None,
                        help="Override OPTIMIZER.NUM_WORKERS for dataloaders")
    parser.add_argument("--pin-memory", action="store_true",
                        help="Enable DataLoader pin_memory")
    parser.add_argument("--persistent-workers", action="store_true",
                        help="Keep DataLoader workers alive between epochs")
    parser.add_argument("--prefetch-factor", type=int, default=None,
                        help="DataLoader prefetch_factor when num_workers > 0")
    parser.add_argument("--fast-cudnn", action="store_true",
                        help="Use cudnn.benchmark=True and deterministic=False")
    parser.add_argument("--allow-tf32", action="store_true",
                        help="Allow TF32 matmul/convolution for exploratory speed runs")
    parser.add_argument("--disable-train-val", action="store_true",
                        help="Disable validation inside train_network for quick runs")
    parser.add_argument("--max-epoch", type=int, default=None,
                        help="Override OPTIMIZER.MAX_EPOCH")
    parser.add_argument("--val-subset", type=int, default=None,
                        help="Override VAL.NUM_SUBSET")
    parser.add_argument("--val-subset-every", type=int, default=None,
                        help="Override VAL.VAL_PER_EPOCH_SUBSET")
    parser.add_argument("--val-full-every", type=int, default=None,
                        help="Override VAL.VAL_PER_EPOCH_FULL")
    return parser


def apply_runtime_overrides(pline, args):
    overrides = {}
    should_rebuild_scheduler = False

    num_workers = getattr(args, "num_workers", None)
    pin_memory = getattr(args, "pin_memory", False)
    persistent_workers = getattr(args, "persistent_workers", False)
    prefetch_factor = getattr(args, "prefetch_factor", None)
    max_epoch = getattr(args, "max_epoch", None)
    disable_train_val = getattr(args, "disable_train_val", False)
    val_subset = getattr(args, "val_subset", None)
    val_subset_every = getattr(args, "val_subset_every", None)
    val_full_every = getattr(args, "val_full_every", None)
    fast_cudnn = getattr(args, "fast_cudnn", False)
    allow_tf32 = getattr(args, "allow_tf32", False)

    if num_workers is not None:
        pline.cfg.OPTIMIZER.NUM_WORKERS = num_workers
        overrides["OPTIMIZER.NUM_WORKERS"] = num_workers
    if pin_memory:
        pline.cfg.OPTIMIZER.PIN_MEMORY = True
        overrides["OPTIMIZER.PIN_MEMORY"] = True
    if persistent_workers:
        pline.cfg.OPTIMIZER.PERSISTENT_WORKERS = True
        overrides["OPTIMIZER.PERSISTENT_WORKERS"] = True
    if prefetch_factor is not None:
        pline.cfg.OPTIMIZER.PREFETCH_FACTOR = prefetch_factor
        overrides["OPTIMIZER.PREFETCH_FACTOR"] = prefetch_factor
    if max_epoch is not None:
        pline.cfg.OPTIMIZER.MAX_EPOCH = max_epoch
        overrides["OPTIMIZER.MAX_EPOCH"] = max_epoch
        should_rebuild_scheduler = True

    if disable_train_val:
        pline.cfg.VAL.IS_VALIDATE = False
        pline.is_validate = False
        overrides["VAL.IS_VALIDATE"] = False
    if val_subset is not None:
        pline.cfg.VAL.NUM_SUBSET = val_subset
        pline.val_num_subset = val_subset
        overrides["VAL.NUM_SUBSET"] = val_subset
    if val_subset_every is not None:
        pline.cfg.VAL.VAL_PER_EPOCH_SUBSET = val_subset_every
        pline.val_per_epoch_subset = val_subset_every
        overrides["VAL.VAL_PER_EPOCH_SUBSET"] = val_subset_every
    if val_full_every is not None:
        pline.cfg.VAL.VAL_PER_EPOCH_FULL = val_full_every
        pline.val_per_epoch_full = val_full_every
        overrides["VAL.VAL_PER_EPOCH_FULL"] = val_full_every

    if fast_cudnn or allow_tf32:
        import torch

        if fast_cudnn:
            pline.cfg.GENERAL.IS_DETERMINISTIC = False
            torch.backends.cudnn.deterministic = False
            torch.backends.cudnn.benchmark = True
            overrides["GENERAL.IS_DETERMINISTIC"] = False
            overrides["torch.backends.cudnn.benchmark"] = True

        if allow_tf32:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            if hasattr(torch, "set_float32_matmul_precision"):
                torch.set_float32_matmul_precision("high")
            overrides["torch.backends.cuda.matmul.allow_tf32"] = True
            overrides["torch.backends.cudnn.allow_tf32"] = True

    if should_rebuild_scheduler and getattr(pline, "scheduler", None) is not None:
        from utils.util_pipeline import build_scheduler

        pline.scheduler = build_scheduler(pline, pline.optimizer)
        overrides["scheduler"] = "rebuilt_after_runtime_override"

    if overrides:
        print(f"* Runtime overrides: {overrides}")
        if hasattr(pline, "path_log"):
            os.makedirs(pline.path_log, exist_ok=True)
            with open(os.path.join(pline.path_log, "runtime_overrides.json"), "w") as f:
                json.dump(overrides, f, indent=2)

    return overrides
