import numpy as np
import torch
import torch.nn as nn

from ..model_utils.taskdec_fuser import TaskAwareDecControlledA2Fusion


def _make_conv_block(in_channels, out_channels, stride, layer_num):
    layers = [
        nn.ZeroPad2d(1),
        nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=0, bias=False),
        nn.BatchNorm2d(out_channels, eps=1e-3, momentum=0.01),
        nn.ReLU(),
    ]
    for _ in range(layer_num):
        layers.extend([
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        ])
    return nn.Sequential(*layers)


def _make_deblock(in_channels, out_channels, stride, use_conv_for_no_stride=False):
    if stride > 1 or (stride == 1 and not use_conv_for_no_stride):
        return nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, stride, stride=stride, bias=False),
            nn.BatchNorm2d(out_channels, eps=1e-3, momentum=0.01),
            nn.ReLU(),
        )

    stride = int(np.round(1 / stride))
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, stride, stride=stride, bias=False),
        nn.BatchNorm2d(out_channels, eps=1e-3, momentum=0.01),
        nn.ReLU(),
    )


class BaseBEVBackbone_TaskDecPP(nn.Module):
    """PointPillar-style VoD BEV backbone with TaskDec L+R fusion.

    The native VoD VFE/scatter keeps separate LiDAR and radar BEV maps. This
    backbone aligns their resolution/channels, fuses them with TaskDec, then
    uses the same FPN-style 2D neck/head interface as PP-Concat.
    """

    def __init__(self, model_cfg, input_channels):
        super().__init__()
        self.model_cfg = model_cfg

        modal_in_channels = model_cfg.get('MODAL_IN_CHANNELS', None)
        if modal_in_channels is None:
            modal_in_channels = [input_channels // 2, input_channels // 2]
        self.lidar_key = model_cfg.get('LIDAR_KEY', 'taskdec_lidar_bev')
        self.radar_key = model_cfg.get('RADAR_KEY', 'taskdec_radar_bev')

        stem_cfg = model_cfg.get('STEM', None)
        self.use_stem = stem_cfg is not None and bool(stem_cfg.get('ENABLED', True))
        if self.use_stem:
            stem_out_channels = int(stem_cfg.OUT_CHANNELS)
            stem_stride = int(stem_cfg.get('STRIDE', 2))
            stem_layers = int(stem_cfg.get('LAYER_NUM', 3))
            self.lidar_stem = _make_conv_block(
                int(modal_in_channels[0]), stem_out_channels, stem_stride, stem_layers
            )
            self.radar_stem = _make_conv_block(
                int(modal_in_channels[1]), stem_out_channels, stem_stride, stem_layers
            )
        else:
            self.lidar_stem = nn.Identity()
            self.radar_stem = nn.Identity()

        fusion_grid_size = model_cfg.TASKDEC_GRID_SIZE
        self.taskdec_fuser = TaskAwareDecControlledA2Fusion(
            model_cfg.TASKDEC,
            grid_size=fusion_grid_size,
            point_cloud_range=model_cfg.get('TASKDEC_POINT_CLOUD_RANGE', [0, -25.6, -3, 51.2, 25.6, 2]),
            voxel_size=model_cfg.get('TASKDEC_VOXEL_SIZE', [0.32, 0.32, 4.0]),
            scl=model_cfg.get('SCL', False),
        )

        taskdec_cfg = model_cfg.TASKDEC
        patch_y, patch_x = taskdec_cfg.UCP.PATCH_SIZE
        n_repeat_channel = int(round(taskdec_cfg.UCP.N_QUERY / (patch_x * patch_y)))
        fused_channels = int(taskdec_cfg.UCP.DIM_PATCH * n_repeat_channel)

        assert len(model_cfg.LAYER_NUMS) == len(model_cfg.LAYER_STRIDES) == len(model_cfg.NUM_FILTERS)
        assert len(model_cfg.UPSAMPLE_STRIDES) == len(model_cfg.NUM_UPSAMPLE_FILTERS)
        layer_nums = model_cfg.LAYER_NUMS
        layer_strides = model_cfg.LAYER_STRIDES
        num_filters = model_cfg.NUM_FILTERS
        upsample_strides = model_cfg.UPSAMPLE_STRIDES
        num_upsample_filters = model_cfg.NUM_UPSAMPLE_FILTERS

        num_levels = len(layer_nums)
        c_in_list = [fused_channels, *num_filters[:-1]]
        self.blocks = nn.ModuleList()
        self.deblocks = nn.ModuleList()
        for idx in range(num_levels):
            self.blocks.append(
                _make_conv_block(c_in_list[idx], num_filters[idx], layer_strides[idx], layer_nums[idx])
            )
            self.deblocks.append(
                _make_deblock(
                    num_filters[idx],
                    num_upsample_filters[idx],
                    upsample_strides[idx],
                    model_cfg.get('USE_CONV_FOR_NO_STRIDE', False),
                )
            )

        c_in = sum(num_upsample_filters)
        if len(upsample_strides) > num_levels:
            self.deblocks.append(
                nn.Sequential(
                    nn.ConvTranspose2d(c_in, c_in, upsample_strides[-1], stride=upsample_strides[-1], bias=False),
                    nn.BatchNorm2d(c_in, eps=1e-3, momentum=0.01),
                    nn.ReLU(),
                )
            )
        self.num_bev_features = c_in

    def forward(self, data_dict):
        lidar_x = self.lidar_stem(data_dict['lidar_spatial_features'])
        radar_x = self.radar_stem(data_dict['radar_spatial_features'])

        data_dict[self.lidar_key] = lidar_x
        data_dict[self.radar_key] = radar_x
        data_dict = self.taskdec_fuser(data_dict)

        x = data_dict['fused_feat']
        ups = []
        ret_dict = {}
        for i, block in enumerate(self.blocks):
            x = block(x)
            stride = int(data_dict['fused_feat'].shape[2] / x.shape[2])
            ret_dict['spatial_features_%dx' % stride] = x
            ups.append(self.deblocks[i](x))

        if len(ups) > 1:
            x = torch.cat(ups, dim=1)
        elif len(ups) == 1:
            x = ups[0]

        if len(self.deblocks) > len(self.blocks):
            x = self.deblocks[-1](x)

        data_dict['spatial_features_2d'] = x
        return data_dict
