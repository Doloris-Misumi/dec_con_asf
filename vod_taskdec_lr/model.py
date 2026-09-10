import torch
import torch.nn as nn

try:
    from vod_taskdec_lr.models.fuser import TaskAwareDecControlledA2Fusion
except ModuleNotFoundError:
    from models.fuser import TaskAwareDecControlledA2Fusion


class SimpleBevEncoder(nn.Module):
    """Scatter point statistics to BEV and project them with small conv blocks."""

    def __init__(self, in_channels, out_channels, point_cloud_range, grid_size):
        super().__init__()
        self.register_buffer("pc_range", torch.tensor(point_cloud_range, dtype=torch.float32), persistent=False)
        self.grid_y, self.grid_x = [int(v) for v in grid_size]
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def _scatter(self, batched_points, batch_size, attr_start, attr_dim):
        device = batched_points.device
        feat = torch.zeros(batch_size, attr_dim + 1, self.grid_y, self.grid_x, device=device)
        if batched_points.numel() == 0:
            return feat

        batch_idx = batched_points[:, 0].long()
        xyz = batched_points[:, 1:4]
        attrs = batched_points[:, attr_start:attr_start + attr_dim]
        x_min, y_min, z_min, x_max, y_max, z_max = self.pc_range
        mask = (
            (xyz[:, 0] >= x_min)
            & (xyz[:, 0] < x_max)
            & (xyz[:, 1] >= y_min)
            & (xyz[:, 1] < y_max)
            & (xyz[:, 2] >= z_min)
            & (xyz[:, 2] < z_max)
        )
        if not mask.any():
            return feat

        batch_idx = batch_idx[mask]
        xyz = xyz[mask]
        attrs = attrs[mask]
        gx = ((xyz[:, 0] - x_min) / (x_max - x_min) * self.grid_x).long().clamp(0, self.grid_x - 1)
        gy = ((xyz[:, 1] - y_min) / (y_max - y_min) * self.grid_y).long().clamp(0, self.grid_y - 1)
        lin = batch_idx * (self.grid_y * self.grid_x) + gy * self.grid_x + gx

        flat = feat.permute(0, 2, 3, 1).reshape(-1, attr_dim + 1)
        values = torch.cat([attrs, torch.ones(attrs.shape[0], 1, device=device)], dim=1)
        flat.index_add_(0, lin, values)
        count = flat[:, -1:].clamp_min(1.0)
        flat[:, :-1] = flat[:, :-1] / count
        flat[:, -1:] = torch.log1p(flat[:, -1:])
        return feat

    def forward(self, batched_points, batch_size, attr_start, attr_dim):
        return self.net(self._scatter(batched_points, batch_size, attr_start, attr_dim))


class VodTaskDecLrSmokeModel(nn.Module):
    """Small VoD L+R model that exercises the copied TaskDec fuser."""

    def __init__(self, cfg):
        super().__init__()
        dataset_cfg = cfg["DATASET"]
        model_cfg = cfg["MODEL"]
        self.patch_dec_weight = float(model_cfg["FUSER"].get("PATCH_DEC_WEIGHT", 0.1))
        self.lidar_encoder = SimpleBevEncoder(
            in_channels=2,
            out_channels=int(model_cfg["LIDAR_CHANNELS"]),
            point_cloud_range=dataset_cfg["POINT_CLOUD_RANGE"],
            grid_size=dataset_cfg["GRID_SIZE"],
        )
        self.radar_encoder = SimpleBevEncoder(
            in_channels=5,
            out_channels=int(model_cfg["RADAR_CHANNELS"]),
            point_cloud_range=dataset_cfg["POINT_CLOUD_RANGE"],
            grid_size=dataset_cfg["GRID_SIZE"],
        )

        grid_x = int(dataset_cfg["GRID_SIZE"][1])
        grid_y = int(dataset_cfg["GRID_SIZE"][0])
        grid_size = [grid_x, grid_y, 1]
        self.fuser = TaskAwareDecControlledA2Fusion(
            model_cfg["FUSER"],
            grid_size,
            point_cloud_range=dataset_cfg["POINT_CLOUD_RANGE"],
            voxel_size=[
                (dataset_cfg["POINT_CLOUD_RANGE"][3] - dataset_cfg["POINT_CLOUD_RANGE"][0]) / grid_x,
                (dataset_cfg["POINT_CLOUD_RANGE"][4] - dataset_cfg["POINT_CLOUD_RANGE"][1]) / grid_y,
                1.0,
            ],
        )
        fused_channels = int(model_cfg["FUSER"]["UCP"]["DIM_PATCH"]) * int(
            model_cfg["FUSER"]["UCP"]["N_QUERY"]
        ) // (
            int(model_cfg["FUSER"]["UCP"]["PATCH_SIZE"][0])
            * int(model_cfg["FUSER"]["UCP"]["PATCH_SIZE"][1])
        )
        self.proxy_head = nn.Conv2d(fused_channels, 1, kernel_size=1)

    def _target_heatmap(self, gt_boxes, height, width, point_cloud_range):
        device = gt_boxes.device
        target = torch.zeros(gt_boxes.shape[0], 1, height, width, device=device)
        x_min, y_min, _, x_max, y_max, _ = [float(v) for v in point_cloud_range]
        for batch_idx in range(gt_boxes.shape[0]):
            boxes = gt_boxes[batch_idx]
            valid = (boxes[:, 3] > 0.0) & (boxes[:, 4] > 0.0) & (boxes[:, 7] > 0.0)
            boxes = boxes[valid]
            if boxes.numel() == 0:
                continue
            gx = ((boxes[:, 0] - x_min) / (x_max - x_min) * width).long().clamp(0, width - 1)
            gy = ((boxes[:, 1] - y_min) / (y_max - y_min) * height).long().clamp(0, height - 1)
            target[batch_idx, 0, gy, gx] = 1.0
        return target

    def forward(self, batch):
        batch_size = len(batch["frame_ids"])
        lidar_points = batch["lidar_points"]
        radar_points = batch["radar_points"]
        batch["spatial_features_2d"] = self.lidar_encoder(lidar_points, batch_size, attr_start=4, attr_dim=1)
        batch["bev_feat"] = self.radar_encoder(radar_points, batch_size, attr_start=4, attr_dim=4)
        batch = self.fuser(batch)
        logits = self.proxy_head(batch["fused_feat"])
        target = self._target_heatmap(
            batch["gt_boxes"],
            logits.shape[-2],
            logits.shape[-1],
            self.fuser.point_cloud_range,
        )
        proxy_loss = nn.functional.binary_cross_entropy_with_logits(logits, target)
        patch_loss = batch.get("patch_dec_loss", logits.new_tensor(0.0))
        loss = proxy_loss + self.patch_dec_weight * patch_loss
        return {
            "loss": loss,
            "proxy_loss": proxy_loss.detach(),
            "patch_dec_loss": patch_loss.detach(),
            "logits_shape": tuple(logits.shape),
            "fused_shape": tuple(batch["fused_feat"].shape),
            "patch_dec_logging": batch.get("patch_dec_logging", {}),
        }


class VodTaskDecLrAnchorModel(nn.Module):
    """VoD L+R TaskDec model with the original ASF/OpenPCDet anchor head."""

    def __init__(self, cfg):
        super().__init__()
        from models.head.anchor_head_integrated import AnchorHeadSingleIntegrated

        dataset_cfg = cfg["DATASET"]
        model_cfg = cfg["MODEL"]
        self.patch_dec_weight = float(model_cfg["FUSER"].get("PATCH_DEC_WEIGHT", 0.1))
        self.lidar_encoder = SimpleBevEncoder(
            in_channels=2,
            out_channels=int(model_cfg["LIDAR_CHANNELS"]),
            point_cloud_range=dataset_cfg["POINT_CLOUD_RANGE"],
            grid_size=dataset_cfg["GRID_SIZE"],
        )
        self.radar_encoder = SimpleBevEncoder(
            in_channels=5,
            out_channels=int(model_cfg["RADAR_CHANNELS"]),
            point_cloud_range=dataset_cfg["POINT_CLOUD_RANGE"],
            grid_size=dataset_cfg["GRID_SIZE"],
        )

        grid_x = int(dataset_cfg["GRID_SIZE"][1])
        grid_y = int(dataset_cfg["GRID_SIZE"][0])
        self.fuser = TaskAwareDecControlledA2Fusion(
            model_cfg["FUSER"],
            [grid_x, grid_y, 1],
            point_cloud_range=dataset_cfg["POINT_CLOUD_RANGE"],
            voxel_size=[
                (dataset_cfg["POINT_CLOUD_RANGE"][3] - dataset_cfg["POINT_CLOUD_RANGE"][0]) / grid_x,
                (dataset_cfg["POINT_CLOUD_RANGE"][4] - dataset_cfg["POINT_CLOUD_RANGE"][1]) / grid_y,
                1.0,
            ],
        )
        self.head = AnchorHeadSingleIntegrated(cfg)

    def forward(self, batch):
        batch_size = len(batch["frame_ids"])
        lidar_points = batch["lidar_points"]
        radar_points = batch["radar_points"]
        batch["batch_size"] = batch_size
        batch["spatial_features_2d"] = self.lidar_encoder(lidar_points, batch_size, attr_start=4, attr_dim=1)
        batch["bev_feat"] = self.radar_encoder(radar_points, batch_size, attr_start=4, attr_dim=4)
        batch = self.fuser(batch)
        batch = self.head(batch)

        if not self.training:
            return batch

        det_loss = self.head.loss(batch)
        patch_loss = batch.get("patch_dec_loss", det_loss.new_tensor(0.0))
        loss = det_loss + self.patch_dec_weight * patch_loss
        logging = {}
        logging.update(batch.get("logging", {}))
        logging.update(batch.get("patch_dec_logging", {}))
        logging["det_loss"] = float(det_loss.detach().cpu())
        logging["patch_dec_loss"] = float(patch_loss.detach().cpu())
        logging["total_loss"] = float(loss.detach().cpu())
        return {
            "loss": loss,
            "det_loss": det_loss.detach(),
            "patch_dec_loss": patch_loss.detach(),
            "fused_shape": tuple(batch["fused_feat"].shape),
            "logging": logging,
        }
