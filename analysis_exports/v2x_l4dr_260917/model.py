"""Full L4DR path: PointNet foreground filter -> MME -> MGF -> detection head.

Native trainable modules are preserved. Dataset-specific voxelization/scatter,
empty inputs and inference without ground truth are handled by this adapter.
"""
import copy
import numpy as np
import torch
from torch import nn
from easydict import EasyDict
from spconv.utils import Point2VoxelCPU3d
from cumm import tensorview as tv
from v2x_taskdec.model import V2XDetector  # Establish the existing PCDet path.
from pcdet.models.backbones_3d.pointnet2_backbone import PointNet2MSG
from pcdet.models.dense_heads.point_head_box import PointHeadPreMask
from pcdet.models.backbones_2d.base_bev_backbone import BaseBEVBackbone_MGF
from pcdet.models.dense_heads.anchor_head_single import AnchorHeadSingle
from native_mme import MME_PillarVFE


class PointHeadWithoutEvalGT(PointHeadPreMask):
    def forward(self, batch):
        preds = self.cls_layers(batch['point_features'])
        batch['point_cls_scores'] = preds.max(dim=-1)[0].sigmoid()
        self.forward_ret_dict = {'point_cls_preds': preds}
        if self.training:
            labels = self.assign_targets(batch)['point_cls_labels']
            labels = labels.masked_fill(~batch['radar_valid'], -1)
            self.forward_ret_dict['point_cls_labels'] = labels
            batch['point_cls_labels'] = labels
        return batch


class L4DRDetector(nn.Module):
    decode = V2XDetector.decode

    def __init__(self, cfg, variant='l4dr'):
        super().__init__()
        assert variant == 'l4dr'
        self.cfg = cfg
        native = EasyDict(copy.deepcopy(cfg['l4dr']['native_model']))
        self.backbone_3d = PointNet2MSG(native.BACKBONE_3D, input_channels=7)
        self.point_head = PointHeadWithoutEvalGT(3, self.backbone_3d.num_point_features,
                                               native.POINT_HEAD, predict_boxes_when_training=False)
        self.vfe = MME_PillarVFE(native.VFE, [4, 7], cfg['voxel_size'], cfg['point_cloud_range'])
        self.backbone_2d = BaseBEVBackbone_MGF(native.BACKBONE_2D, 128)
        self.grid = np.rint((np.array(cfg['point_cloud_range'][3:]) - np.array(cfg['point_cloud_range'][:3])) /
                            np.array(cfg['voxel_size'])).astype(int)
        assert self.grid[2] == 1
        self.head = AnchorHeadSingle(EasyDict(cfg['head']), self.backbone_2d.num_bev_features,
            3, cfg['class_names'], self.grid, cfg['point_cloud_range'], predict_boxes_when_training=False)
        self.radar_voxelizer = Point2VoxelCPU3d(vsize_xyz=cfg['voxel_size'],
            coors_range_xyz=cfg['point_cloud_range'], num_point_features=8,
            max_num_voxels=cfg['max_voxels'], max_num_points_per_voxel=32)
        self.last_counts = {}

    def voxelize_filtered_radar(self, batch):
        # Native foreground threshold and CPU detach of scores are unchanged.
        keep = (batch['point_cls_scores'] > self.cfg['l4dr']['denoise_threshold']) & batch['radar_valid']
        filtered = torch.cat([batch['radar_points'][keep], batch['point_cls_scores'][keep, None]], 1)
        points = filtered.detach().cpu().numpy()
        vox, coords, nums = [], [], []
        for i in range(batch['batch_size']):
            v, c, n = self.radar_voxelizer.point_to_voxel(tv.from_numpy(np.ascontiguousarray(points[points[:, 0] == i, 1:])))
            vox.append(v.numpy().copy()); coords.append(np.pad(c.numpy().copy(), ((0, 0), (1, 0)), constant_values=i))
            nums.append(n.numpy().copy())
        device = batch['radar_points'].device
        for name, values in [('radar_voxels', vox), ('radar_voxel_coords', coords), ('radar_voxel_num_points', nums)]:
            batch[name] = torch.from_numpy(np.concatenate(values)).to(device)
        self.last_counts = dict(valid_radar_points=int(batch['radar_valid'].sum()),
            kept_radar_points=int(keep.sum()), radar_voxels=len(batch['radar_voxel_coords']),
            lidar_voxels=len(batch['lidar_voxel_coords']))
        return batch

    def scatter(self, batch):
        nx, ny, _ = self.grid
        for key in ['lidar', 'radar']:
            features = batch[key + '_pillar_features'].reshape(-1, 64)
            coords = batch[key + '_voxel_coords'].long()
            flat = features.new_zeros((batch['batch_size'] * ny * nx, 64))
            ids = coords[:, 0] * ny * nx + coords[:, 2] * nx + coords[:, 3]
            flat = flat.index_copy(0, ids, features)
            batch[key + '_spatial_features'] = flat.reshape(batch['batch_size'], ny, nx, 64).permute(0, 3, 1, 2).contiguous()
        return batch

    def forward(self, inputs):
        state = dict(batch_size=len(inputs['frame_ids']), radar_points=inputs['radar_points'],
                     radar_valid=inputs['radar_valid'])
        state['lidar_voxels'], state['lidar_voxel_coords'], state['lidar_voxel_num_points'] = inputs['lidar']
        if self.training:
            state['gt_boxes'] = inputs['gt_boxes']
        state = self.backbone_3d(state)
        state = self.point_head(state)
        state = self.voxelize_filtered_radar(state)
        # BatchNorm needs at least two entries on its reduction axes. Only the
        # degenerate one-voxel/one-point radar case uses existing running stats.
        norms = []
        if self.training and len(state['radar_voxel_num_points']) == 1 and int(state['radar_voxel_num_points'][0]) == 1:
            norms = [m for m in self.vfe.r_pfn_layers.modules() if isinstance(m, nn.BatchNorm1d) and m.training]
            for m in norms: m.eval()
        try:
            state = self.vfe(state)
        finally:
            for m in norms: m.train()
        state = self.scatter(state)
        state = self.backbone_2d(state)
        state = self.head(state)
        if self.training:
            det, log = self.head.get_loss()
            point, point_log = self.point_head.get_loss()
            log.update(point_log)
            return dict(loss=det + point, det_loss=det, aux_loss=point, logging=log)
        return self.decode(state)
