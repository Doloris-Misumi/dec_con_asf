#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
import pickle
import random
import sys
import time
import types
from pathlib import Path

import numpy as np
import torch
import yaml
from easydict import EasyDict
from torch.utils.data import DataLoader
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
OPS_ROOT = PROJECT_ROOT / "ops"
if str(OPS_ROOT) not in sys.path:
    sys.path.insert(0, str(OPS_ROOT))

from vod_taskdec_lr.model import VodTaskDecLrAnchorModel
from vod_taskdec_lr.vod_dataset import VodLrDataset


CLASS_NAMES = ["Car", "Pedestrian", "Cyclist"]


def to_easydict(value):
    if isinstance(value, dict):
        return EasyDict({key: to_easydict(val) for key, val in value.items()})
    if isinstance(value, list):
        return [to_easydict(item) for item in value]
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


class Calibration:
    def __init__(self, calib_file):
        self.P2 = self._read_matrix(calib_file, "P2", 12).reshape(3, 4)
        self.R0 = self._read_matrix(calib_file, "R0_rect", 9).reshape(3, 3)
        self.V2C = self._read_matrix(calib_file, "Tr_velo_to_cam", 12).reshape(3, 4)

    @staticmethod
    def _read_matrix(calib_file, key, size):
        for raw in Path(calib_file).read_text().splitlines():
            if raw.startswith(f"{key}:"):
                values = np.asarray([float(v) for v in raw.split(":", 1)[1].split()], dtype=np.float32)
                if values.size != size:
                    raise ValueError(f"{key} in {calib_file} has {values.size} values, expected {size}")
                return values
        raise KeyError(f"{key} not found in {calib_file}")

    @staticmethod
    def cart_to_hom(points):
        return np.hstack([points, np.ones((points.shape[0], 1), dtype=np.float32)])

    def lidar_to_rect(self, points_lidar):
        points_lidar_hom = self.cart_to_hom(points_lidar)
        return points_lidar_hom @ self.V2C.T @ self.R0.T

    def rect_to_img(self, points_rect):
        points_rect_hom = self.cart_to_hom(points_rect)
        points_img_hom = points_rect_hom @ self.P2.T
        denom = np.maximum(points_img_hom[:, 2:3], 1e-6)
        points_img = points_img_hom[:, :2] / denom
        points_depth = points_img_hom[:, 2] - self.P2.T[3, 2]
        return points_img, points_depth


def boxes3d_lidar_to_kitti_camera(boxes_lidar, calib):
    boxes = boxes_lidar.copy()
    xyz_lidar = boxes[:, 0:3].copy()
    length = boxes[:, 3:4]
    width = boxes[:, 4:5]
    height = boxes[:, 5:6]
    heading = boxes[:, 6:7]
    xyz_lidar[:, 2] -= height[:, 0] / 2.0
    xyz_camera = calib.lidar_to_rect(xyz_lidar)
    rotation_y = -heading - np.pi / 2.0
    return np.concatenate([xyz_camera, length, height, width, rotation_y], axis=1)


def boxes3d_to_corners3d_kitti_camera(boxes_camera):
    num_boxes = boxes_camera.shape[0]
    length = boxes_camera[:, 3]
    height = boxes_camera[:, 4]
    width = boxes_camera[:, 5]
    x_corners = np.stack(
        [length / 2, length / 2, -length / 2, -length / 2, length / 2, length / 2, -length / 2, -length / 2],
        axis=1,
    )
    y_corners = np.zeros((num_boxes, 8), dtype=np.float32)
    y_corners[:, 4:8] = -height[:, None]
    z_corners = np.stack(
        [width / 2, -width / 2, -width / 2, width / 2, width / 2, -width / 2, -width / 2, width / 2],
        axis=1,
    )
    corners = np.stack([x_corners, y_corners, z_corners], axis=2).astype(np.float32)
    rotation_y = boxes_camera[:, 6]
    cos_yaw = np.cos(rotation_y)
    sin_yaw = np.sin(rotation_y)
    rot = np.zeros((num_boxes, 3, 3), dtype=np.float32)
    rot[:, 0, 0] = cos_yaw
    rot[:, 0, 2] = -sin_yaw
    rot[:, 1, 1] = 1.0
    rot[:, 2, 0] = sin_yaw
    rot[:, 2, 2] = cos_yaw
    corners = corners @ rot
    corners += boxes_camera[:, None, 0:3]
    return corners


def boxes3d_kitti_camera_to_imageboxes(boxes_camera, calib, image_shape):
    if boxes_camera.shape[0] == 0:
        return np.zeros((0, 4), dtype=np.float32)
    corners = boxes3d_to_corners3d_kitti_camera(boxes_camera)
    points_img, _ = calib.rect_to_img(corners.reshape(-1, 3))
    corners_img = points_img.reshape(-1, 8, 2)
    min_uv = corners_img.min(axis=1)
    max_uv = corners_img.max(axis=1)
    boxes2d = np.concatenate([min_uv, max_uv], axis=1)
    boxes2d[:, 0] = np.clip(boxes2d[:, 0], 0, image_shape[1] - 1)
    boxes2d[:, 1] = np.clip(boxes2d[:, 1], 0, image_shape[0] - 1)
    boxes2d[:, 2] = np.clip(boxes2d[:, 2], 0, image_shape[1] - 1)
    boxes2d[:, 3] = np.clip(boxes2d[:, 3], 0, image_shape[0] - 1)
    return boxes2d


def read_image_shape(root, frame_id):
    image_path = Path(root) / "lidar" / "training" / "image_2" / f"{frame_id}.jpg"
    try:
        from PIL import Image

        with Image.open(image_path) as image:
            width, height = image.size
        return np.asarray([height, width], dtype=np.int32)
    except Exception:
        return np.asarray([1216, 1936], dtype=np.int32)


def empty_annotation(with_score):
    anno = {
        "name": np.asarray([], dtype=object),
        "truncated": np.zeros((0,), dtype=np.float64),
        "occluded": np.zeros((0,), dtype=np.int64),
        "alpha": np.zeros((0,), dtype=np.float64),
        "bbox": np.zeros((0, 4), dtype=np.float64),
        "dimensions": np.zeros((0, 3), dtype=np.float64),
        "location": np.zeros((0, 3), dtype=np.float64),
        "rotation_y": np.zeros((0,), dtype=np.float64),
    }
    if with_score:
        anno["score"] = np.zeros((0,), dtype=np.float64)
    return anno


def read_label_annotation(label_path):
    content = [line.strip().split() for line in Path(label_path).read_text().splitlines() if line.strip()]
    if not content:
        return empty_annotation(with_score=True)

    anno = {}
    anno["name"] = np.asarray([line[0] for line in content])
    anno["truncated"] = np.asarray([float(line[1]) for line in content], dtype=np.float64)
    anno["occluded"] = np.asarray([int(float(line[2])) for line in content], dtype=np.int64)
    anno["alpha"] = np.asarray([float(line[3]) for line in content], dtype=np.float64)
    anno["bbox"] = np.asarray([[float(v) for v in line[4:8]] for line in content], dtype=np.float64)
    dims_hwl = np.asarray([[float(v) for v in line[8:11]] for line in content], dtype=np.float64)
    anno["dimensions"] = dims_hwl[:, [2, 0, 1]]
    anno["location"] = np.asarray([[float(v) for v in line[11:14]] for line in content], dtype=np.float64)
    anno["rotation_y"] = np.asarray([float(line[14]) for line in content], dtype=np.float64)
    if len(content[0]) >= 16:
        anno["score"] = np.asarray([float(line[15]) for line in content], dtype=np.float64)
    else:
        anno["score"] = np.zeros((len(content),), dtype=np.float64)
    return anno


def prediction_to_annotation(frame_id, pred_dict, root, class_names):
    scores = pred_dict["pred_scores"].detach().cpu().numpy()
    boxes_lidar = pred_dict["pred_boxes"].detach().cpu().numpy()
    labels = pred_dict["pred_labels"].detach().cpu().numpy().astype(np.int64)
    if scores.shape[0] == 0:
        anno = empty_annotation(with_score=True)
        anno["frame_id"] = frame_id
        anno["boxes_lidar"] = np.zeros((0, 7), dtype=np.float32)
        return anno

    calib = Calibration(Path(root) / "lidar" / "training" / "calib" / f"{frame_id}.txt")
    image_shape = read_image_shape(root, frame_id)
    boxes_camera = boxes3d_lidar_to_kitti_camera(boxes_lidar, calib)
    boxes_img = boxes3d_kitti_camera_to_imageboxes(boxes_camera, calib, image_shape)
    names = np.asarray(class_names, dtype=object)[labels - 1]

    anno = {
        "name": names,
        "truncated": -np.ones((scores.shape[0],), dtype=np.float64),
        "occluded": -np.ones((scores.shape[0],), dtype=np.int64),
        "alpha": -np.arctan2(-boxes_lidar[:, 1], boxes_lidar[:, 0]) + boxes_camera[:, 6],
        "bbox": boxes_img.astype(np.float64),
        "dimensions": boxes_camera[:, 3:6].astype(np.float64),
        "location": boxes_camera[:, 0:3].astype(np.float64),
        "rotation_y": boxes_camera[:, 6].astype(np.float64),
        "score": scores.astype(np.float64),
        "boxes_lidar": boxes_lidar.astype(np.float32),
        "frame_id": frame_id,
    }
    return anno


def save_kitti_prediction(anno, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        bbox = anno["bbox"]
        dims_lhw = anno["dimensions"]
        loc = anno["location"]
        for idx in range(len(anno["name"])):
            h, w, length = dims_lhw[idx, 1], dims_lhw[idx, 2], dims_lhw[idx, 0]
            f.write(
                "%s -1 -1 %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.8f\n"
                % (
                    anno["name"][idx],
                    anno["alpha"][idx],
                    bbox[idx, 0],
                    bbox[idx, 1],
                    bbox[idx, 2],
                    bbox[idx, 3],
                    h,
                    w,
                    length,
                    loc[idx, 0],
                    loc[idx, 1],
                    loc[idx, 2],
                    anno["rotation_y"][idx],
                    anno["score"][idx],
                )
            )


def load_vod_official_evaluator(eval_root):
    eval_root = Path(eval_root)
    package_name = "_l4dr_vod_eval"
    package = types.ModuleType(package_name)
    package.__path__ = [str(eval_root)]
    sys.modules[package_name] = package

    for module_name in ["rotate_iou_cpu", "kitti_official_evaluate"]:
        spec = importlib.util.spec_from_file_location(
            f"{package_name}.{module_name}", eval_root / f"{module_name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"{package_name}.{module_name}"] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.kitti_official_evaluate"].get_official_eval_result


def summarize_official_results(results):
    summary = {}
    for area_name in ["entire_area", "roi"]:
        area = results[area_name]
        class_scores = {}
        for class_name in CLASS_NAMES:
            class_scores[class_name] = float(area[f"{class_name}_3d_all"])
        class_scores["mAP"] = sum(class_scores.values()) / len(CLASS_NAMES)
        summary[area_name] = class_scores
    return summary


def write_summary(output_dir, ckpt_path, split, num_samples, elapsed, summary, raw_results):
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "checkpoint": str(ckpt_path),
        "split": split,
        "num_samples": num_samples,
        "seconds": elapsed,
        "score_thresh": raw_results.get("_score_thresh"),
        "pred_per_sample": raw_results.get("_pred_per_sample"),
        "official_vod_3d": summary,
        "raw_results": raw_results,
    }
    with (output_dir / "metrics.json").open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    lines = [
        "# VoD TaskDec L+R Evaluation",
        "",
        f"Checkpoint: `{ckpt_path}`",
        "",
        f"Split: `{split}`",
        "",
        f"Samples: {num_samples}",
        "",
        f"Elapsed seconds: {elapsed:.2f}",
        "",
        f"Score threshold: {raw_results.get('_score_thresh')}",
        "",
        f"Predictions per sample: {raw_results.get('_pred_per_sample'):.3f}",
        "",
        "Metric: L4DR/VoD official 3D AP. Entire area uses `custom_method=0`; driving corridor uses `custom_method=3`.",
        "",
        "| Area | Car | Pedestrian | Cyclist | mAP |",
        "|---|---:|---:|---:|---:|",
    ]
    for area_name, label in [("entire_area", "Entire annotated area"), ("roi", "Driving corridor")]:
        values = summary[area_name]
        lines.append(
            f"| {label} | {values['Car']:.2f} | {values['Pedestrian']:.2f} | "
            f"{values['Cyclist']:.2f} | {values['mAP']:.2f} |"
        )
    lines.append("")
    (output_dir / "summary.md").write_text("\n".join(lines))


def evaluate_checkpoint(args, cfg, ckpt_path, dataset, loader, device, evaluator):
    tag = args.tag or f"{Path(ckpt_path).stem}_{cfg.DATASET.VAL_SPLIT}"
    output_dir = Path(args.output_dir) / tag
    prediction_dir = output_dir / "final_result" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_dir.mkdir(parents=True, exist_ok=True)

    model = VodTaskDecLrAnchorModel(cfg).to(device)
    checkpoint = torch.load(ckpt_path, map_location=device)
    state_dict = checkpoint.get("model_state", checkpoint)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    det_annos = []
    gt_annos = []
    total_pred = 0
    start = time.time()
    with torch.no_grad():
        for batch in tqdm(loader, desc=f"eval {Path(ckpt_path).stem}", dynamic_ncols=True):
            batch = to_device(batch, device)
            output = model(batch)
            pred_dicts = output["pred_dicts"]
            for frame_id, pred_dict in zip(batch["frame_ids"], pred_dicts):
                anno = prediction_to_annotation(frame_id, pred_dict, cfg.DATASET.ROOT, CLASS_NAMES)
                save_kitti_prediction(anno, prediction_dir / f"{frame_id}.txt")
                det_annos.append(anno)
                gt_annos.append(
                    read_label_annotation(
                        Path(cfg.DATASET.ROOT) / "lidar" / "training" / "label_2" / f"{frame_id}.txt"
                    )
                )
                total_pred += len(anno["name"])

    elapsed = time.time() - start
    raw_results = {}
    raw_results.update(evaluator(gt_annos, det_annos, [0, 1, 2], custom_method=0))
    raw_results.update(evaluator(gt_annos, det_annos, [0, 1, 2], custom_method=3))
    raw_results["_score_thresh"] = float(cfg.MODEL.HEAD.POST_PROCESSING.SCORE_THRESH)
    raw_results["_pred_per_sample"] = total_pred / max(len(dataset), 1)
    summary = summarize_official_results(raw_results)

    with (output_dir / "det_annos.pkl").open("wb") as f:
        pickle.dump(det_annos, f)
    with (output_dir / "gt_annos.pkl").open("wb") as f:
        pickle.dump(gt_annos, f)
    write_summary(output_dir, ckpt_path, cfg.DATASET.VAL_SPLIT, len(dataset), elapsed, summary, raw_results)

    print(f"[done] ckpt={ckpt_path}")
    print(f"[output] {output_dir}")
    print(f"[pred_per_sample] {total_pred / max(len(dataset), 1):.3f}")
    print(json.dumps(summary, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="Evaluate VoD TaskDec L+R checkpoints with L4DR VoD mAP")
    parser.add_argument("--config", default="vod_taskdec_lr/configs/taskdec_lr_anchor_train.yml")
    parser.add_argument("--ckpt", nargs="+", required=True)
    parser.add_argument("--gpu", default="3")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--score-thresh", type=float, default=None)
    parser.add_argument("--output-dir", default="vod_taskdec_lr/evals")
    parser.add_argument("--tag", default=None, help="Only use with a single checkpoint.")
    parser.add_argument(
        "--eval-root",
        default="/home/hongsheng/L4DR/pcdet/datasets/vod_evaluation",
        help="Directory containing L4DR VoD evaluator files.",
    )
    args = parser.parse_args()
    if args.tag is not None and len(args.ckpt) != 1:
        raise ValueError("--tag can only be used with a single checkpoint")

    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    cfg = load_cfg(args.config)
    cfg.DATASET.SPLIT = cfg.DATASET.VAL_SPLIT
    cfg.DATASET.NUM_SAMPLES = args.max_samples
    cfg.TRAIN.BATCH_SIZE = args.batch_size
    cfg.TRAIN.NUM_WORKERS = args.num_workers
    if args.score_thresh is not None:
        cfg.MODEL.HEAD.POST_PROCESSING.SCORE_THRESH = args.score_thresh
    set_seed(int(cfg.GENERAL.SEED))
    torch.backends.cudnn.benchmark = True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[device] {device} cuda_visible={os.environ.get('CUDA_VISIBLE_DEVICES')}")
    print(f"[data] split={cfg.DATASET.SPLIT} max_samples={cfg.DATASET.NUM_SAMPLES}")

    dataset = VodLrDataset(cfg.DATASET)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
        drop_last=False,
        collate_fn=dataset.collate_fn,
    )
    print(f"[data] samples={len(dataset)} batch_size={args.batch_size}")

    evaluator = load_vod_official_evaluator(args.eval_root)
    for ckpt in args.ckpt:
        evaluate_checkpoint(args, cfg, Path(ckpt), dataset, loader, device, evaluator)


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
