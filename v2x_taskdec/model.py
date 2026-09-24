"""Three controlled fusion architectures on shared LSS + PointPillars encoders.

Native PointPillars components are read from the existing local OpenPCDet tree.
TaskDec is the sole fusion path in that variant; no preceding ConvFuser exists.
"""
from pathlib import Path
import sys
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from easydict import EasyDict
import yaml

ROOT = Path(__file__).resolve().parents[1]
PCDET = ROOT / 'vod_taskdec_native/L4DR_taskdec'
if str(PCDET) not in sys.path:
    sys.path.insert(0, str(PCDET))
from pcdet.models.backbones_3d.vfe.pillar_vfe import PillarVFE
from pcdet.models.backbones_2d.base_bev_backbone import BaseBEVBackbone
from pcdet.models.dense_heads.anchor_head_single import AnchorHeadSingle
from pcdet.ops.iou3d_nms import iou3d_nms_utils
from ops.bev_pool import bev_pool
from .fuser import A2Fusion, TaskAwareDecControlledA2Fusion


def conv_block(cin, cout, stride=1):
    return nn.Sequential(nn.Conv2d(cin, cout, 3, stride, 1, bias=False),
                         nn.BatchNorm2d(cout, eps=1e-3, momentum=.01), nn.ReLU(inplace=True))


class LssCamera(nn.Module):
    """ResNet-50/FPN + learned depth lifting, following the existing CamBase path.

    Geometry uses augmented projection matrices, floor voxelization, and explicit
    x/y conversion to the standard [batch, channels, y, x] point-pillar layout.
    """
    def __init__(self, cfg):
        super().__init__()
        from torchvision.models import resnet50
        net = resnet50(pretrained=False)
        if cfg.get('image_pretrained'):
            state = torch.load(cfg['image_pretrained'], map_location='cpu')
            net.load_state_dict(state, strict=True)
        self.stem = nn.Sequential(net.conv1, net.bn1, net.relu, net.maxpool)
        self.layer1, self.layer2, self.layer3, self.layer4 = net.layer1, net.layer2, net.layer3, net.layer4
        self.neck = nn.Sequential(nn.Conv2d(1024 + 2048, 256, 1, bias=False),
                                  nn.BatchNorm2d(256), nn.ReLU(), conv_block(256, 128))
        self.channels = 64
        depths = torch.arange(*cfg['depth_bound'])
        self.register_buffer('depth_bins', depths)
        self.depthnet = nn.Conv2d(128, len(depths) + self.channels, 1)
        self.register_buffer('range_min', torch.tensor(cfg['point_cloud_range'][:3]))
        self.register_buffer('voxel_size', torch.tensor(cfg['voxel_size']))
        self.grid = np.rint((np.array(cfg['point_cloud_range'][3:]) - np.array(cfg['point_cloud_range'][:3])) /
                            np.array(cfg['voxel_size'])).astype(int).tolist()
        assert self.grid[2] == 1
        self.bev_stem = nn.Sequential(conv_block(64, 64), conv_block(64, 64))

    def forward(self, image, lidar_to_image, world_aug):
        b, _, ih, iw = image.shape
        x = self.layer2(self.layer1(self.stem(image)))
        x3 = self.layer3(x)
        x4 = self.layer4(x3)
        x = self.neck(torch.cat([x3, F.interpolate(x4, size=x3.shape[-2:], mode='bilinear', align_corners=False)], 1))
        prediction = self.depthnet(x)
        d = len(self.depth_bins)
        depth = prediction[:, :d].softmax(dim=1)
        context = prediction[:, d:]
        fh, fw = x.shape[-2:]
        # Match CamBase's feature-grid endpoint convention, explicitly audited.
        ys, xs = torch.meshgrid(torch.linspace(0, ih - 1, fh, device=x.device),
                                torch.linspace(0, iw - 1, fw, device=x.device))
        z = self.depth_bins[:, None, None].expand(-1, fh, fw)
        frustum = torch.stack([xs[None] * z, ys[None] * z, z, torch.ones_like(z)], -1)
        lifted = torch.einsum('bij,dhwj->bdhwi', torch.inverse(lidar_to_image.float()), frustum)
        geom = torch.einsum('bij,bdhwj->bdhwi', world_aug.float(), lifted)[..., :3]
        coords = torch.floor((geom - self.range_min) / self.voxel_size).long().reshape(-1, 3)
        batch_ids = torch.arange(b, device=x.device)[:, None].expand(b, d * fh * fw).reshape(-1, 1)
        coords = torch.cat([coords, batch_ids], 1)
        values = (depth[:, None] * context[:, :, None]).permute(0, 2, 3, 4, 1).reshape(-1, self.channels)
        keep = ((coords[:, :3] >= 0) & (coords[:, :3] < coords.new_tensor(self.grid))).all(1)
        if keep.any():
            # CUDA op spatial indices are [x,y,z,b]; result is B,C,Z,X,Y.
            bev = bev_pool(values[keep].contiguous(), coords[keep].contiguous(), b, 1, self.grid[0], self.grid[1])
            bev = bev[:, :, 0].transpose(-1, -2).contiguous()
        else:
            bev = values.sum() * 0 + values.new_zeros((b, self.channels, self.grid[1], self.grid[0]))
        return self.bev_stem(bev), depth


class PillarEncoder(nn.Module):
    def __init__(self, cfg, n_features):
        super().__init__()
        vfe_cfg = EasyDict(USE_NORM=True, WITH_DISTANCE=False, USE_ABSLOTE_XYZ=True, NUM_FILTERS=[64])
        self.vfe = PillarVFE(vfe_cfg, n_features, cfg['voxel_size'], cfg['point_cloud_range'])
        self.grid = np.rint((np.array(cfg['point_cloud_range'][3:]) - np.array(cfg['point_cloud_range'][:3])) /
                            np.array(cfg['voxel_size'])).astype(int).tolist()
        assert self.grid[2] == 1
        self.stem = nn.Sequential(conv_block(64, 64), conv_block(64, 64))

    def forward(self, tensors, batch_size):
        features, coords, counts = tensors
        nx, ny, _ = self.grid
        if len(features):
            result = self.vfe(dict(voxels=features, voxel_coords=coords, voxel_num_points=counts))
            pillars = result['pillar_features'].reshape(-1, 64)
            flat = features.new_zeros((batch_size * ny * nx, 64))
            ids = coords[:, 0].long() * ny * nx + coords[:, 2].long() * nx + coords[:, 3].long()
            flat = flat.index_copy(0, ids, pillars)
            bev = flat.reshape(batch_size, ny, nx, 64).permute(0, 3, 1, 2).contiguous()
        else:
            bev = features.new_zeros((batch_size, 64, ny, nx))
        return self.stem(bev)


def fuser_config(cfg):
    if 'resolved_fuser' in cfg:
        return EasyDict(cfg['resolved_fuser'])
    base = yaml.safe_load((ROOT / 'configs/v1_0/cfg_A2F_scl_final.yml').read_text())['MODEL']['FUSER']
    base.update(yaml.safe_load((ROOT / 'configs/ASF_task_dec_controlled_robust_v1_0.yml').read_text())['MODEL']['FUSER'])
    keys = cfg['modalities']
    base.update(KEY_FEATS=keys, DIM_FEATS=[64] * len(keys), DEC_CONTROL_NUM_CLASSES=len(cfg['class_names']),
                DEC_CONTROL_CONTEXT_MODE='class', PATCH_DEC_HIDDEN_DIM=128)
    base['TO_EMBED'].update(DIM_COMMON=64)
    base['UCP'].update(DIM_PATCH=128, N_QUERY=16, PATCH_SIZE=[4, 4])
    base['N_HEADS_MHA'] = 8
    return EasyDict(base)


class V2XDetector(nn.Module):
    def __init__(self, cfg, variant):
        super().__init__()
        if variant not in ('concat', 'patch', 'taskdec'):
            raise ValueError(variant)
        self.cfg, self.variant = cfg, variant
        self.encoders = nn.ModuleDict()
        for key in cfg['modalities']:
            self.encoders[key] = LssCamera(cfg) if key == 'camera' else PillarEncoder(cfg, cfg['point_features'][key])
        grid = np.rint((np.array(cfg['point_cloud_range'][3:]) - np.array(cfg['point_cloud_range'][:3])) /
                       np.array(cfg['voxel_size'])).astype(int)
        if variant == 'concat':
            self.fuser = nn.Sequential(nn.Conv2d(64 * len(cfg['modalities']), 128, 3, padding=1, bias=False),
                                        nn.BatchNorm2d(128), nn.ReLU())
        else:
            cls = TaskAwareDecControlledA2Fusion if variant == 'taskdec' else A2Fusion
            self.fuser = cls(fuser_config(cfg), grid, point_cloud_range=cfg['point_cloud_range'],
                            voxel_size=cfg['voxel_size'], scl=False)
        neck_cfg = EasyDict(LAYER_NUMS=[3, 5, 5], LAYER_STRIDES=[2, 2, 2], NUM_FILTERS=[128, 256, 256],
                            UPSAMPLE_STRIDES=[1, 2, 4], NUM_UPSAMPLE_FILTERS=[128, 128, 128])
        self.neck = BaseBEVBackbone(neck_cfg, 128)
        self.head = AnchorHeadSingle(EasyDict(cfg['head']), 384, len(cfg['class_names']), cfg['class_names'],
                                    grid, cfg['point_cloud_range'], predict_boxes_when_training=False)

    def forward(self, batch):
        state = {'batch_size': len(batch['frame_ids'])}
        if self.training:
            state['gt_boxes'] = batch['gt_boxes']
        for key in self.cfg['modalities']:
            if key == 'camera':
                state[key], _ = self.encoders[key](batch['image'], batch['lidar_to_image'], batch['world_aug'])
            else:
                state[key] = self.encoders[key](batch[key], state['batch_size'])
        if self.variant == 'concat':
            state['fused_feat'] = self.fuser(torch.cat([state[k] for k in self.cfg['modalities']], 1))
        else:
            state = self.fuser(state)
        state['spatial_features'] = state['fused_feat']
        state = self.neck(state)
        state = self.head(state)
        if self.training:
            det_loss, log = self.head.get_loss()
            aux = state.get('patch_dec_loss', det_loss.new_tensor(0.))
            log.update(state.get('patch_dec_logging', {}))
            return dict(loss=det_loss + self.cfg['patch_dec_weight'] * aux, det_loss=det_loss,
                        aux_loss=aux, logging=log)
        return self.decode(state)

    def decode(self, state):
        results = []
        for scores, boxes in zip(state['batch_cls_preds'].sigmoid(), state['batch_box_preds']):
            entries = []
            for cls in range(len(self.cfg['class_names'])):
                cls_scores = scores[:, cls]
                valid = torch.isfinite(boxes).all(1) & (cls_scores >= self.cfg['score_threshold'])
                bs, ss = boxes[valid], cls_scores[valid]
                if not len(ss):
                    continue
                keep, _ = iou3d_nms_utils.nms_gpu(bs, ss, self.cfg['nms_threshold'], pre_maxsize=4096)
                keep = keep[:self.cfg['max_detections']]
                entries.append(torch.cat([bs[keep], ss[keep, None], ss.new_full((len(keep), 1), cls + 1)], 1))
            results.append(torch.cat(entries) if entries else boxes.new_zeros((0, 9)))
        return results
