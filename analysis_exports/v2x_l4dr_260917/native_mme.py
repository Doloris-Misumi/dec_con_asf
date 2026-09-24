"""Native L4DR MME_PillarVFE with exact memory-bounded coordinate join and empty-input support.
See native_mme.diff for the complete changes. Native source is kept untouched.
"""
import torch
from torch import nn
from pcdet.models.backbones_3d.vfe.pillar_vfe import PFNLayer
from pcdet.models.backbones_3d.vfe.vfe_template import VFETemplate


def match_coords(left, right):
    if not len(left) or not len(right):
        empty = left.new_empty((0,), dtype=torch.long)
        return empty, empty
    # Coordinate columns are nonnegative [batch,z,y,x], each below 65536.
    def encode(c):
        c = c.long()
        return ((c[:,0] * 65536 + c[:,1]) * 65536 + c[:,2]) * 65536 + c[:,3]
    lk, rk = encode(left), encode(right)
    sorted_r, order = torch.sort(rk)
    pos = torch.searchsorted(sorted_r, lk)
    safe = pos.clamp(max=len(right)-1)
    keep = (pos < len(right)) & (sorted_r[safe] == lk)
    return torch.where(keep)[0], order[safe[keep]]


class MME_PillarVFE(VFETemplate):
    def __init__(self, model_cfg, num_point_features, voxel_size, point_cloud_range, **kwargs):
        super().__init__(model_cfg=model_cfg)
        self.use_norm = self.model_cfg.USE_NORM
        self.with_distance = self.model_cfg.WITH_DISTANCE
        self.use_absolute_xyz = self.model_cfg.USE_ABSLOTE_XYZ
        self.use_preground_score = self.model_cfg.USE_RadarSCORE
        num_point_features_l = num_point_features[0]
        num_point_features_r = num_point_features[1]
        num_point_features_l += 6 if self.use_absolute_xyz else 3
        num_point_features_r += 6 if self.use_absolute_xyz else 3
        # center_x, center_y, center_z, mean_x, mean_y, mean_z we need 6 new
        if self.with_distance:
            num_point_features_l += 1
            num_point_features_r += 1
        if self.use_preground_score:
            num_point_features_r += 1
        # LiDAR : x y z cx cy cz dx dy dz I
        # Radar : x y z cx cy cz dx dy dz V R t
        # Fusion : x y z Lcx Lcy Lcz mx my mz Rcx Rcy Rcz I V R t
        ex_point_features = num_point_features_l + num_point_features_r - 6
        num_point_features_r = ex_point_features
        num_point_features_l = ex_point_features
        self.num_point_features_r = num_point_features_r
        self.num_point_features_l = num_point_features_l
        print("common feature dim (use preground_score) = ", num_point_features_r)


        self.num_filters = self.model_cfg.NUM_FILTERS
        assert len(self.num_filters) > 0
        num_filters = [num_point_features_l] + list(self.num_filters)

        l_pfn_layers = []
        for i in range(len(num_filters) - 1):
            in_filters = num_filters[i]
            out_filters = num_filters[i + 1]
            l_pfn_layers.append(
                PFNLayer(in_filters, out_filters, self.use_norm, last_layer=(i >= len(num_filters) - 2))
            )
        self.l_pfn_layers = nn.ModuleList(l_pfn_layers)

        self.num_filters = self.model_cfg.NUM_FILTERS_Radar
        assert len(self.num_filters) > 0
        num_filters = [num_point_features_r] + list(self.num_filters)

        r_pfn_layers = []
        for i in range(len(num_filters) - 1):
            in_filters = num_filters[i]
            out_filters = num_filters[i + 1]
            r_pfn_layers.append(
                PFNLayer(in_filters, out_filters, self.use_norm, last_layer=(i >= len(num_filters) - 2))
            )
        self.r_pfn_layers = nn.ModuleList(r_pfn_layers)

        self.voxel_x = voxel_size[0]
        self.voxel_y = voxel_size[1]
        self.voxel_z = voxel_size[2]
        self.x_offset = self.voxel_x / 2 + point_cloud_range[0]
        self.y_offset = self.voxel_y / 2 + point_cloud_range[1]
        self.z_offset = self.voxel_z / 2 + point_cloud_range[2]
        
    def get_output_feature_dim(self):
        return self.num_filters[-1]

    def get_paddings_indicator(self, actual_num, max_num, axis=0):
        actual_num = torch.unsqueeze(actual_num, axis + 1)
        max_num_shape = [1] * len(actual_num.shape)
        max_num_shape[axis + 1] = -1
        max_num = torch.arange(max_num, dtype=torch.int, device=actual_num.device).view(max_num_shape)
        paddings_indicator = actual_num.int() > max_num
        return paddings_indicator

    def forward(self, batch_dict, **kwargs):
  
        lidar_voxel_features, lidar_voxel_num_points, lidar_coords = batch_dict['lidar_voxels'], batch_dict['lidar_voxel_num_points'], batch_dict['lidar_voxel_coords']
        radar_voxel_features, radar_voxel_num_points, radar_coords = batch_dict['radar_voxels'], batch_dict['radar_voxel_num_points'], batch_dict['radar_voxel_coords']
        L_coords = lidar_coords[:,:]
        R_coords = radar_coords[:,:]

        lidar_points_mean = lidar_voxel_features[:, :, :3].sum(dim=1, keepdim=True) / lidar_voxel_num_points.type_as(lidar_voxel_features).view(-1, 1, 1)
        radar_points_mean = radar_voxel_features[:, :, :3].sum(dim=1, keepdim=True) / radar_voxel_num_points.type_as(radar_voxel_features).view(-1, 1, 1)
        lidar_f_cluster = lidar_voxel_features[:, :, :3] - lidar_points_mean
        radar_f_cluster = radar_voxel_features[:, :, :3] - radar_points_mean

        lidar_f_center = torch.zeros_like(lidar_voxel_features[:, :, :3])
        radar_f_center = torch.zeros_like(radar_voxel_features[:, :, :3])
        lidar_f_center[:, :, 0] = lidar_voxel_features[:, :, 0] - (lidar_coords[:, 3].to(lidar_voxel_features.dtype).unsqueeze(1) * self.voxel_x + self.x_offset)
        lidar_f_center[:, :, 1] = lidar_voxel_features[:, :, 1] - (lidar_coords[:, 2].to(lidar_voxel_features.dtype).unsqueeze(1) * self.voxel_y + self.y_offset)
        lidar_f_center[:, :, 2] = lidar_voxel_features[:, :, 2] - (lidar_coords[:, 1].to(lidar_voxel_features.dtype).unsqueeze(1) * self.voxel_z + self.z_offset)
        radar_f_center[:, :, 0] = radar_voxel_features[:, :, 0] - (radar_coords[:, 3].to(radar_voxel_features.dtype).unsqueeze(1) * self.voxel_x + self.x_offset)
        radar_f_center[:, :, 1] = radar_voxel_features[:, :, 1] - (radar_coords[:, 2].to(radar_voxel_features.dtype).unsqueeze(1) * self.voxel_y + self.y_offset)
        radar_f_center[:, :, 2] = radar_voxel_features[:, :, 2] - (radar_coords[:, 1].to(radar_voxel_features.dtype).unsqueeze(1) * self.voxel_z + self.z_offset)

        # Exact coordinate equality join, without an O(N_lidar*N_radar) matrix.
        common_L, common_R = match_coords(L_coords, R_coords)

        # mask = torch.ones(len(L_coords)).bool() 
        # mask[common_L] = False
        # only_L = torch.where(mask)[0].long()
        # # 找到R中独有的点
        # mask = torch.ones(len(R_coords)).bool()
        # mask[common_R] = False
        # only_R = torch.where(mask)[0].long()

        
        
        #print(len(L_coords), len(R_coords), len(only_L), len(only_R), len(common_L), len(common_R))
        #接下来把Lidar合并到radar voxel（包括特征合并）
        len_radar = 1
        if len(radar_voxel_num_points) > 0:
            len_radar = int(radar_voxel_num_points.max())

        com_features = torch.zeros((len(radar_voxel_num_points), len_radar, self.num_point_features_r)).cuda()
        
        #用radar的部分覆盖（radar点比较少，一般1~5，最多5个点，一次次来）  
        for i in range(len_radar):
            now_feature_idx = 0
            valid_mask = radar_voxel_num_points[common_R] >= i+1 #只覆盖非空的点
            valid_common_R = common_R[valid_mask]
            valid_common_L = common_L[valid_mask]
            #print(radar_voxel_features[valid_common_R[0], i, :3])

            
            com_features[:, i, now_feature_idx : now_feature_idx + 3] = radar_voxel_features[:, i, :3] #3
            now_feature_idx += 3

            #Intensity 覆盖为均值（radar部分的lidar特征设置为0）
            extraF_L = lidar_voxel_features[valid_common_L, :, 3:].sum(dim=1) / lidar_voxel_num_points[valid_common_L].type_as(lidar_voxel_features).view(-1, 1)
            com_features[valid_common_R, i, now_feature_idx : now_feature_idx + 1] = extraF_L #1
            now_feature_idx += 1
            
            # com_features[valid_common_L, replaced_idx, now_feature_idx : now_feature_idx + 1] = 0 #1
            # now_feature_idx += 1


            #radar to lidar偏移
            common_lidar_points_mean = lidar_voxel_features[valid_common_L, :, :3].sum(dim=1) / lidar_voxel_num_points[valid_common_L].type_as(lidar_voxel_features).view(-1, 1)
            radartolidar_f_cluster = radar_voxel_features[valid_common_R, i, :3] - common_lidar_points_mean
            com_features[valid_common_R, i, now_feature_idx : now_feature_idx + radartolidar_f_cluster.shape[-1]] = radartolidar_f_cluster #3
            now_feature_idx += radartolidar_f_cluster.shape[-1]
            
            com_features[:, i, now_feature_idx : now_feature_idx + radar_f_center.shape[-1]] = radar_f_center[:, i] #3
            now_feature_idx += radar_f_center.shape[-1]

            com_features[:, i, now_feature_idx : now_feature_idx + radar_f_cluster.shape[-1]] = radar_f_cluster[:, i] #3
            now_feature_idx += radar_f_cluster.shape[-1]

            
            #radar特征部分修改
            com_features[:, i, now_feature_idx : now_feature_idx + radar_voxel_features.shape[-1] - 3] = radar_voxel_features[:, i, 3:]
            now_feature_idx += radartolidar_f_cluster.shape[-1]
        
        len_lidar = int(lidar_voxel_num_points.max()) if len(lidar_voxel_num_points) else 0
        l_ex_features = torch.zeros((len(lidar_voxel_num_points), 32, self.num_point_features_l)).cuda()
        now_feature_idx = 0
        l_ex_features[:, :, now_feature_idx : now_feature_idx + lidar_voxel_features.shape[-1]] = lidar_voxel_features #4
        now_feature_idx += lidar_voxel_features.shape[-1]
        #print(now_feature_idx)

        l_ex_features[:, :, now_feature_idx : now_feature_idx + lidar_f_cluster.shape[-1]] = lidar_f_cluster #3
        now_feature_idx += lidar_f_cluster.shape[-1]
        #print(now_feature_idx)

        l_ex_features[:, :, now_feature_idx : now_feature_idx + lidar_f_center.shape[-1]] = lidar_f_center #3
        now_feature_idx += lidar_f_center.shape[-1]
        #print(now_feature_idx)

        #计算lidar to radar共同部分中radar0时刻的cluster和feature均值用于特征传播
        #(N,3); (N,feature_dim-1) t=0
        mask = self.get_paddings_indicator(radar_voxel_num_points[common_R], 32, axis=0)
        mask = mask & (radar_voxel_features[common_R, :, -2] == 0) 
        # 求valid且t=0的mask并求和算有多少个，t在-2维度
        num_valid = mask.sum(dim=1)
        l2r_mask = (num_valid > 0)
        l2r_com_L = common_L[l2r_mask]
        l2r_com_R = common_R[l2r_mask]
        num_valid = num_valid[l2r_mask]
        mask = mask[l2r_mask].unsqueeze(-1)
        #计算lidar to radar共同部分的cluster(注意只有common(L，R)的部分才有)
        com_radar = radar_voxel_features[common_R, :, :3]
        com_radar = com_radar[com_radar[...,-2] == 0]
        common_radar_points_mean = (radar_voxel_features[l2r_com_R, :, :3] * mask).sum(dim=1, keepdim=True) / num_valid.type_as(radar_voxel_features).view(-1, 1, 1)
        lidartoradar_f_cluster = lidar_voxel_features[l2r_com_L, :, :3] - common_radar_points_mean

        l_ex_features[l2r_com_L, :, now_feature_idx : now_feature_idx + lidartoradar_f_cluster.shape[-1]] = lidartoradar_f_cluster #3
        now_feature_idx += lidartoradar_f_cluster.shape[-1]
        #radar特征部分先填充均值后面是radar的话会覆盖
        extraFea_R = (radar_voxel_features[l2r_com_R, :, 3:] * mask).sum(dim=1, keepdim=True) / num_valid.type_as(radar_voxel_features).view(-1, 1, 1)
        l_ex_features[l2r_com_L, :, now_feature_idx :] = extraFea_R #4
        now_feature_idx += extraFea_R.shape[-1]

        lidar_features = l_ex_features
        final_voxel_count = lidar_features.shape[1]
        mask = self.get_paddings_indicator(lidar_voxel_num_points, final_voxel_count, axis=0)
        mask = torch.unsqueeze(mask, -1).type_as(lidar_features)
        lidar_features *= mask
        if len(lidar_voxel_num_points):
            for pfn in self.l_pfn_layers:
                lidar_features = pfn(lidar_features)
            lidar_features = lidar_features.reshape(-1, self.num_filters[-1])
        else:
            lidar_features = lidar_features.new_zeros((0, self.num_filters[-1]))

        radar_features = com_features
        final_voxel_count = radar_features.shape[1]
        mask = self.get_paddings_indicator(radar_voxel_num_points, final_voxel_count, axis=0)
        mask = torch.unsqueeze(mask, -1).type_as(radar_features)
        radar_features *= mask
        if len(radar_voxel_num_points):
            for pfn in self.r_pfn_layers:
                radar_features = pfn(radar_features)
            radar_features = radar_features.reshape(-1, self.num_filters[-1])
        else:
            radar_features = radar_features.new_zeros((0, self.num_filters[-1]))
        # T = 10
        # LR_pillar_weight = F.softmax(torch.cat([lidar_voxel_num_points[common_L, None], radar_voxel_num_points[common_R, None]],dim = 1) / T)
        # min_pillar_num = torch.min(lidar_voxel_num_points[common_L], radar_voxel_num_points[common_R])
        # dif_pillar_num = torch.abs(lidar_voxel_num_points[common_L] - radar_voxel_num_points[common_R])
        # eps = 1e-6
        # com_weight = torch.tanh(min_pillar_num / (dif_pillar_num + eps)).reshape(-1).cuda()
        # print(min_pillar_num.shape, dif_pillar_num.shape, com_weight.shape)
        # for i in range(len(common_L)):
        #     print(lidar_voxel_num_points[common_L[i]].item(), radar_voxel_num_points[common_R[i]].item(),LR_pillar_weight[i][0].item(),LR_pillar_weight[i][1].item(), com_weight[i].item())
        # com_features = com_features * com_weight
        # lidar_features[common_L] = lidar_features[common_L] * LR_pillar_weight[i][0]
        # radar_features[common_R] = radar_features[common_R] * LR_pillar_weight[i][1]
        batch_dict['lidar_pillar_features'] = lidar_features
        batch_dict['radar_pillar_features'] = radar_features
        return batch_dict
