from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


class VodLrDataset(Dataset):
    """Minimal VoD LiDAR+Radar reader for TaskDec L+R smoke tests.

    The dataset uses real VoD point clouds and labels, but it deliberately keeps
    the interface local to this sandbox instead of registering itself into the
    K-Radar data factory.
    """

    def __init__(self, cfg):
        self.root = Path(cfg["ROOT"])
        self.split = cfg.get("SPLIT", "val")
        self.radar_folder = cfg.get("RADAR_FOLDER", "radar_5frames")
        self.classes = list(cfg.get("CLASSES", ["Car", "Pedestrian", "Cyclist"]))
        self.class_to_id = {name: idx + 1 for idx, name in enumerate(self.classes)}
        self.max_gt = int(cfg.get("MAX_GT", 128))
        self.point_cloud_range = np.asarray(cfg["POINT_CLOUD_RANGE"], dtype=np.float32)
        self.grid_size = tuple(int(v) for v in cfg.get("GRID_SIZE", [128, 128]))
        self.radar_mean = np.asarray(cfg.get("RADAR_MEAN", [0, 0, 0, 0, 0, 0, 0]), dtype=np.float32)
        self.radar_std = np.asarray(cfg.get("RADAR_STD", [1, 1, 1, 1, 1, 1, 1]), dtype=np.float32)

        split_path = self.root / "lidar" / "ImageSets" / f"{self.split}.txt"
        if not split_path.exists():
            raise FileNotFoundError(split_path)
        self.frame_ids = [line.strip() for line in split_path.read_text().splitlines() if line.strip()]
        num_samples = cfg.get("NUM_SAMPLES", None)
        if num_samples is not None:
            self.frame_ids = self.frame_ids[: int(num_samples)]

    def __len__(self):
        return len(self.frame_ids)

    def _lidar_path(self, frame_id):
        return self.root / "lidar" / "training" / "velodyne" / f"{frame_id}.bin"

    def _radar_path(self, frame_id):
        return self.root / self.radar_folder / "training" / "velodyne" / f"{frame_id}.bin"

    def _label_path(self, frame_id):
        return self.root / "lidar" / "training" / "label_2" / f"{frame_id}.txt"

    def _calib_path(self, frame_id):
        return self.root / "lidar" / "training" / "calib" / f"{frame_id}.txt"

    @staticmethod
    def _read_calib_matrix(path, key):
        for raw in Path(path).read_text().splitlines():
            if raw.startswith(f"{key}:"):
                values = [float(v) for v in raw.split(":", 1)[1].split()]
                if len(values) == 12:
                    mat = np.eye(4, dtype=np.float32)
                    mat[:3, :4] = np.asarray(values, dtype=np.float32).reshape(3, 4)
                    return mat
                if len(values) == 9:
                    mat = np.eye(4, dtype=np.float32)
                    mat[:3, :3] = np.asarray(values, dtype=np.float32).reshape(3, 3)
                    return mat
        raise KeyError(f"{key} not found in {path}")

    def _camera_to_lidar(self, xyz_cam, calib_path):
        tr_velo_to_cam = self._read_calib_matrix(calib_path, "Tr_velo_to_cam")
        rect = self._read_calib_matrix(calib_path, "R0_rect")
        cam_to_lidar = np.linalg.inv(rect @ tr_velo_to_cam)
        xyz_h = np.concatenate([xyz_cam, np.ones((xyz_cam.shape[0], 1), dtype=np.float32)], axis=1)
        return (xyz_h @ cam_to_lidar.T)[:, :3]

    def _read_labels(self, frame_id):
        label_path = self._label_path(frame_id)
        if not label_path.exists():
            return np.zeros((0, 8), dtype=np.float32)

        rows = []
        xyz_cam = []
        boxes_cam_meta = []
        for raw in label_path.read_text().splitlines():
            parts = raw.split()
            if len(parts) < 15:
                continue
            cls_name = parts[0]
            if cls_name not in self.class_to_id:
                continue
            values = [float(v) for v in parts[1:15]]
            h, w, length = values[7], values[8], values[9]
            x, y, z = values[10], values[11], values[12]
            ry = values[13]
            xyz_cam.append([x, y, z])
            boxes_cam_meta.append((length, w, h, ry, self.class_to_id[cls_name]))

        if not xyz_cam:
            return np.zeros((0, 8), dtype=np.float32)

        centers_lidar = self._camera_to_lidar(np.asarray(xyz_cam, dtype=np.float32), self._calib_path(frame_id))
        for center, meta in zip(centers_lidar, boxes_cam_meta):
            length, width, height, ry, cls_id = meta
            center[2] += height / 2.0
            # KITTI camera ry to LiDAR yaw. This follows the common OpenPCDet
            # convention used by the VoD/L4DR data pipeline.
            yaw = -(np.pi / 2.0 + ry)
            rows.append([center[0], center[1], center[2], length, width, height, yaw, cls_id])

        boxes = np.asarray(rows, dtype=np.float32)
        boxes = self._filter_boxes_in_range(boxes)
        return boxes

    def _filter_boxes_in_range(self, boxes):
        if boxes.size == 0:
            return boxes
        x_min, y_min, z_min, x_max, y_max, z_max = self.point_cloud_range
        mask = (
            (boxes[:, 0] >= x_min)
            & (boxes[:, 0] <= x_max)
            & (boxes[:, 1] >= y_min)
            & (boxes[:, 1] <= y_max)
            & (boxes[:, 2] >= z_min - 2.0)
            & (boxes[:, 2] <= z_max + 2.0)
        )
        return boxes[mask]

    def __getitem__(self, index):
        frame_id = self.frame_ids[index]
        lidar_path = self._lidar_path(frame_id)
        radar_path = self._radar_path(frame_id)
        if not lidar_path.exists():
            raise FileNotFoundError(lidar_path)
        if not radar_path.exists():
            raise FileNotFoundError(radar_path)

        lidar = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        radar = np.fromfile(radar_path, dtype=np.float32).reshape(-1, 7)
        radar = (radar - self.radar_mean) / self.radar_std
        gt_boxes = self._read_labels(frame_id)

        return {
            "frame_id": frame_id,
            "lidar_points": torch.from_numpy(lidar),
            "radar_points": torch.from_numpy(radar.astype(np.float32)),
            "gt_boxes": torch.from_numpy(gt_boxes),
        }

    def collate_fn(self, batch):
        lidar_points = []
        radar_points = []
        gt_boxes = []
        frame_ids = []

        for batch_idx, item in enumerate(batch):
            frame_ids.append(item["frame_id"])
            lidar_batch = torch.cat(
                [torch.full((item["lidar_points"].shape[0], 1), batch_idx), item["lidar_points"]],
                dim=1,
            )
            radar_batch = torch.cat(
                [torch.full((item["radar_points"].shape[0], 1), batch_idx), item["radar_points"]],
                dim=1,
            )
            lidar_points.append(lidar_batch)
            radar_points.append(radar_batch)

            cur_gt = item["gt_boxes"]
            padded = torch.zeros(self.max_gt, 8, dtype=torch.float32)
            num = min(cur_gt.shape[0], self.max_gt)
            if num > 0:
                padded[:num] = cur_gt[:num]
            gt_boxes.append(padded)

        return {
            "frame_ids": frame_ids,
            "lidar_points": torch.cat(lidar_points, dim=0),
            "radar_points": torch.cat(radar_points, dim=0),
            "gt_boxes": torch.stack(gt_boxes, dim=0),
        }
