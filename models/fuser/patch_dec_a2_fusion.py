import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import repeat

from .a2_fusion import A2Fusion


class PatchDecA2Fusion(A2Fusion):
    """A2Fusion with patch-level common/unique decomposition.

    The module keeps ASF's patch-wise CASAP/PFT pipeline intact. Before
    cross-attention, each modality patch token is decomposed into a common
    component and a modality-unique component. During training the auxiliary
    losses can be computed only on GT foreground BEV patches, so the
    regularizer focuses on real objects instead of empty background. Inference
    does not need GT boxes.
    """

    def __init__(self, model_cfg, grid_size, **kwargs):
        super().__init__(model_cfg, grid_size, **kwargs)
        self.patch_dec_enabled = model_cfg.get("PATCH_DEC_ENABLED", True)
        self.patch_dec_selection = model_cfg.get("PATCH_DEC_SELECTION", "gt_foreground")
        self.patch_dec_topk_ratio = model_cfg.get("PATCH_DEC_TOPK_RATIO", 0.25)
        self.patch_dec_min_patches = model_cfg.get("PATCH_DEC_MIN_PATCHES", 512)
        self.patch_dec_fg_margin = float(model_cfg.get("PATCH_DEC_FG_MARGIN", 0.8))
        self.patch_dec_fg_fallback_to_energy = model_cfg.get("PATCH_DEC_FG_FALLBACK_TO_ENERGY", False)
        self.patch_dec_lambda_decouple = model_cfg.get("PATCH_DEC_LAMBDA_DECOUPLE", 0.1)
        self.patch_dec_lambda_common = model_cfg.get("PATCH_DEC_LAMBDA_COMMON", 0.1)
        self.patch_dec_lambda_unique = model_cfg.get("PATCH_DEC_LAMBDA_UNIQUE", 0.03)
        self.patch_dec_unique_margin = model_cfg.get("PATCH_DEC_UNIQUE_MARGIN", 0.1)

        x_shape, y_shape, _ = [int(v) for v in grid_size]
        self.patch_y, self.patch_x = [int(v) for v in model_cfg.UCP.PATCH_SIZE]
        self.patch_grid_y = int(y_shape / self.patch_y)
        self.patch_grid_x = int(x_shape / self.patch_x)

        def to_float_list(value):
            if isinstance(value, torch.Tensor):
                value = value.detach().cpu().tolist()
            elif hasattr(value, "tolist"):
                value = value.tolist()
            return [float(v) for v in value]

        default_range = [0.0, -16.0, -2.0, 72.0, 16.0, 7.6]
        default_voxel = [0.4, 0.4, 0.4]
        self.point_cloud_range = to_float_list(
            kwargs.get("point_cloud_range", model_cfg.get("PATCH_DEC_POINT_CLOUD_RANGE", default_range))
        )
        self.voxel_size = to_float_list(
            kwargs.get("voxel_size", model_cfg.get("PATCH_DEC_VOXEL_SIZE", default_voxel))
        )

        dim_patch = model_cfg.UCP.DIM_PATCH
        hidden_dim = model_cfg.get("PATCH_DEC_HIDDEN_DIM", dim_patch)
        res_scale = model_cfg.get("PATCH_DEC_RES_SCALE", 0.1)
        self.patch_dec_res_scale = nn.Parameter(torch.tensor(float(res_scale)))
        self.patch_dec_res_scale.requires_grad_(bool(model_cfg.get("PATCH_DEC_RES_SCALE_LEARNABLE", True)))

        def make_encoder():
            return nn.Sequential(
                nn.LayerNorm(dim_patch),
                nn.Linear(dim_patch, hidden_dim, bias=False),
                nn.GELU(),
                nn.Linear(hidden_dim, dim_patch, bias=False),
                nn.LayerNorm(dim_patch),
            )

        self.patch_common = nn.ModuleDict({key: make_encoder() for key in self.key_feats})
        self.patch_unique = nn.ModuleDict({key: make_encoder() for key in self.key_feats})

    def _select_energy_patch_indices(self, base_tokens):
        num_patch = base_tokens[0].shape[0]
        if num_patch == 0:
            return None

        ratio = float(self.patch_dec_topk_ratio)
        if ratio <= 0.0 or ratio >= 1.0:
            return torch.arange(num_patch, device=base_tokens[0].device)

        num_keep = max(int(num_patch * ratio), int(self.patch_dec_min_patches))
        num_keep = min(num_keep, num_patch)
        energy = torch.stack([tok.detach().norm(dim=-1) for tok in base_tokens], dim=0).mean(dim=0)
        return torch.topk(energy, k=num_keep, largest=True).indices

    def _patch_centers_xy(self, device, dtype):
        x_min, y_min = self.point_cloud_range[0], self.point_cloud_range[1]
        step_x = self.patch_x * self.voxel_size[0]
        step_y = self.patch_y * self.voxel_size[1]

        xs = torch.arange(self.patch_grid_x, device=device, dtype=dtype)
        ys = torch.arange(self.patch_grid_y, device=device, dtype=dtype)
        center_x = x_min + (xs + 0.5) * step_x
        center_y = y_min + (ys + 0.5) * step_y
        try:
            mesh_y, mesh_x = torch.meshgrid(center_y, center_x, indexing="ij")
        except TypeError:
            mesh_y, mesh_x = torch.meshgrid(center_y, center_x)
        return mesh_x.reshape(-1), mesh_y.reshape(-1)

    def _gt_foreground_patch_mask(self, batch_dict, num_patch, device):
        fg_mask, _, num_fg, fg_ratio = self._gt_patch_targets(batch_dict, num_patch, device)
        return fg_mask, num_fg, fg_ratio

    def _gt_patch_targets(self, batch_dict, num_patch, device, num_classes=2):
        gt_boxes = batch_dict.get("gt_boxes", None)
        if gt_boxes is None or gt_boxes.numel() == 0:
            return None, None, 0, 0.0

        gt_boxes = gt_boxes.to(device)
        batch_size = gt_boxes.shape[0]
        num_patch_per_sample = self.patch_grid_y * self.patch_grid_x
        if batch_size * num_patch_per_sample != num_patch:
            return None, None, 0, 0.0

        dtype = gt_boxes.dtype
        patch_x, patch_y = self._patch_centers_xy(device, dtype)
        fg_mask = torch.zeros(num_patch, dtype=torch.bool, device=device)
        class_targets = torch.full((num_patch,), -1, dtype=torch.long, device=device)
        margin = torch.tensor(self.patch_dec_fg_margin, device=device, dtype=dtype)

        for batch_idx in range(batch_size):
            boxes = gt_boxes[batch_idx]
            if boxes.shape[-1] < 8:
                valid = (boxes[:, 3] > 0.0) & (boxes[:, 4] > 0.0)
            else:
                valid = (boxes[:, 3] > 0.0) & (boxes[:, 4] > 0.0) & (boxes[:, 7] > 0.0)
            boxes = boxes[valid]
            if boxes.numel() == 0:
                continue

            sample_mask = torch.zeros(num_patch_per_sample, dtype=torch.bool, device=device)
            sample_classes = torch.full((num_patch_per_sample,), -1, dtype=torch.long, device=device)
            for box in boxes:
                x, y, _, length, width, _, theta = box[:7]
                dx = patch_x - x
                dy = patch_y - y
                cos_t = torch.cos(theta)
                sin_t = torch.sin(theta)
                local_x = dx * cos_t + dy * sin_t
                local_y = -dx * sin_t + dy * cos_t
                in_box = (
                    (local_x.abs() <= length * 0.5 + margin)
                    & (local_y.abs() <= width * 0.5 + margin)
                )
                sample_mask |= in_box
                if boxes.shape[-1] >= 8:
                    cls_idx = int(torch.round(box[7]).clamp(min=1, max=num_classes).item()) - 1
                else:
                    cls_idx = 0
                sample_classes[in_box] = cls_idx

            start = batch_idx * num_patch_per_sample
            fg_mask[start:start + num_patch_per_sample] = sample_mask
            class_targets[start:start + num_patch_per_sample] = sample_classes

        return fg_mask, class_targets, int(fg_mask.sum().item()), float(fg_mask.float().mean().item())

    def _select_gt_foreground_patch_indices(self, batch_dict, num_patch, device):
        fg_mask, num_fg, fg_ratio = self._gt_foreground_patch_mask(batch_dict, num_patch, device)
        if fg_mask is None:
            return None, num_fg, fg_ratio

        indices = fg_mask.nonzero(as_tuple=False).flatten()
        return indices, num_fg, fg_ratio

    def _select_patch_indices(self, base_tokens, batch_dict):
        num_patch = base_tokens[0].shape[0]
        if num_patch == 0:
            return None, "empty", 0, 0.0

        if self.patch_dec_selection == "gt_foreground":
            indices, num_fg, fg_ratio = self._select_gt_foreground_patch_indices(
                batch_dict, num_patch, base_tokens[0].device
            )
            if indices is not None and indices.numel() > 0:
                return indices, "gt_foreground", num_fg, fg_ratio
            if not self.patch_dec_fg_fallback_to_energy:
                return None, "gt_foreground_empty", num_fg, fg_ratio

        indices = self._select_energy_patch_indices(base_tokens)
        num_selected = 0 if indices is None else int(indices.numel())
        fg_ratio = float(num_selected) / float(num_patch)
        return indices, "energy", num_selected, fg_ratio

    def _apply_patch_dec(self, keys, tokens, batch_dict):
        if (not self.patch_dec_enabled) or len(tokens) == 0:
            return tokens

        base_tokens = [tok.squeeze(1) for tok in tokens]
        common_tokens = []
        unique_tokens = []
        dec_tokens = []

        for key, base in zip(keys, base_tokens):
            common = self.patch_common[key](base)
            unique = self.patch_unique[key](base)
            common_tokens.append(common)
            unique_tokens.append(unique)
            dec = base + self.patch_dec_res_scale * (common + unique)
            dec_tokens.append(dec.unsqueeze(1))

        if self.training and len(tokens) >= 2:
            idx, selection, num_fg, fg_ratio = self._select_patch_indices(base_tokens, batch_dict)
            if idx is not None and idx.numel() > 0:
                common_sel = [tok.index_select(0, idx) for tok in common_tokens]
                unique_sel = [tok.index_select(0, idx) for tok in unique_tokens]

                decouple_loss = torch.stack([
                    F.cosine_similarity(c, u, dim=-1).abs().mean()
                    for c, u in zip(common_sel, unique_sel)
                ]).mean()

                common_loss = 0.0
                unique_loss = 0.0
                n_pair = 0
                for i in range(len(common_sel)):
                    for j in range(i + 1, len(common_sel)):
                        ci = F.normalize(common_sel[i], dim=-1)
                        cj = F.normalize(common_sel[j], dim=-1)
                        ui = F.normalize(unique_sel[i], dim=-1)
                        uj = F.normalize(unique_sel[j], dim=-1)
                        common_loss = common_loss + (1.0 - (ci * cj).sum(dim=-1)).mean()
                        unique_cos = (ui * uj).sum(dim=-1)
                        unique_loss = unique_loss + F.relu(unique_cos - self.patch_dec_unique_margin).mean()
                        n_pair += 1

                if n_pair > 0:
                    common_loss = common_loss / n_pair
                    unique_loss = unique_loss / n_pair

                patch_dec_loss = (
                    self.patch_dec_lambda_decouple * decouple_loss
                    + self.patch_dec_lambda_common * common_loss
                    + self.patch_dec_lambda_unique * unique_loss
                )
                batch_dict["patch_dec_loss"] = patch_dec_loss
                batch_dict["patch_dec_logging"] = {
                    "patch_dec_loss_raw": patch_dec_loss.detach().item(),
                    "patch_dec_decouple": decouple_loss.detach().item(),
                    "patch_dec_common": common_loss.detach().item()
                    if isinstance(common_loss, torch.Tensor) else float(common_loss),
                    "patch_dec_unique": unique_loss.detach().item()
                    if isinstance(unique_loss, torch.Tensor) else float(unique_loss),
                    "patch_dec_res_scale": self.patch_dec_res_scale.detach().item(),
                    "patch_dec_num_patches": float(idx.numel()),
                    "patch_dec_fg_patches": float(num_fg),
                    "patch_dec_fg_ratio": float(fg_ratio),
                    "patch_dec_selection_code": 1.0 if selection == "gt_foreground" else 0.0,
                }

        return dec_tokens

    def _modify_query_with_patch_dec(self, q_feat, batch_dict):
        return q_feat

    def _modify_fused_tokens_with_patch_dec(self, fused_feat, batch_dict):
        return fused_feat

    def forward(self, batch_dict):
        list_feats = []
        list_keys = []

        is_get_feats_to_vis = False
        if not self.training:
            if "get_feats_to_vis" in batch_dict.keys():
                is_get_feats_to_vis = batch_dict["get_feats_to_vis"]
                batch_dict["feat_b4_fusion"] = []

        for temp_key in self.key_feats:
            if not self.training:
                if "avail_feats" in batch_dict.keys():
                    if temp_key not in batch_dict["avail_feats"]:
                        continue

            temp_feat = getattr(self, f"to_embed_{temp_key}")(batch_dict[temp_key])

            if is_get_feats_to_vis:
                batch_dict["feat_b4_fusion"].append(temp_feat)

            temp_feat = torch.unsqueeze(getattr(self, f"to_patch_{temp_key}")(temp_feat), dim=1)
            temp_feat = getattr(self, f"to_patch_embed_{temp_key}")(temp_feat)
            list_feats.append(temp_feat)
            list_keys.append(temp_key)

        list_feats = self._apply_patch_dec(list_keys, list_feats, batch_dict)

        kv_feats = torch.cat(list_feats, dim=1)
        b_patch, _, _ = kv_feats.shape
        q_feat = repeat(self.aware_query, "b n c -> (b b_repeat) n c", b_repeat=b_patch)
        q_feat = self._modify_query_with_patch_dec(q_feat, batch_dict)

        if self.training:
            if self.is_scl:
                list_individual_feat = []
                for temp_kv_feat in list_feats:
                    list_individual_feat.append(
                        self.to_fused_feat(self.pft(self.fuser(q_feat, temp_kv_feat, temp_kv_feat)[0]))
                    )
                temp_n = len(list_feats)
                for temp_i in range(temp_n):
                    for temp_j in range(temp_i + 1, temp_n):
                        temp_kv_feat = torch.cat([list_feats[temp_i], list_feats[temp_j]], dim=1)
                        list_individual_feat.append(
                            self.to_fused_feat(self.pft(self.fuser(q_feat, temp_kv_feat, temp_kv_feat)[0]))
                        )
                batch_dict["list_individual_feat"] = list_individual_feat
        else:
            if "feat_indiv" in batch_dict.keys():
                list_individual_feat = []
                for temp_kv_feat in list_feats:
                    list_individual_feat.append(
                        self.to_fused_feat(self.pft(self.fuser(q_feat, temp_kv_feat, temp_kv_feat)[0]))
                    )
                batch_dict["feat_indiv"] = list_individual_feat

        if "get_att_maps" in batch_dict.keys():
            fused_feat, att_maps = self.fuser(q_feat, kv_feats, kv_feats)
            batch_dict["get_att_maps"] = self.get_feat_w_channel(att_maps)
        else:
            fused_feat = self.fuser(q_feat, kv_feats, kv_feats)[0]

        if is_get_feats_to_vis:
            batch_dict["pre_fused_feat"] = self.to_fused_feat(fused_feat)

        fused_feat = self._modify_fused_tokens_with_patch_dec(fused_feat, batch_dict)
        fused_feat = self.pft(fused_feat)
        fused_feat = self.to_fused_feat(fused_feat)
        batch_dict["fused_feat"] = fused_feat

        return batch_dict


class ForegroundGatedPatchDecA2Fusion(PatchDecA2Fusion):
    """PatchDec fusion with a learned foreground gate.

    GT boxes supervise which BEV patches are object-related during training,
    but inference uses only the learned patch gate. The gate scales the Dec
    residual before ASF's original cross-attention, so background patches keep
    closer to the baseline ASF representation.
    """

    def __init__(self, model_cfg, grid_size, **kwargs):
        super().__init__(model_cfg, grid_size, **kwargs)
        dim_patch = model_cfg.UCP.DIM_PATCH
        gate_hidden_dim = int(model_cfg.get("PATCH_DEC_GATE_HIDDEN_DIM", max(dim_patch // 2, 1)))
        self.patch_dec_gate_min = float(model_cfg.get("PATCH_DEC_GATE_MIN", 0.0))
        self.patch_dec_gate_max = float(model_cfg.get("PATCH_DEC_GATE_MAX", 1.0))
        self.patch_dec_gate_loss_weight = float(model_cfg.get("PATCH_DEC_GATE_LOSS_WEIGHT", 0.05))
        self.patch_dec_gate_pos_weight_max = float(model_cfg.get("PATCH_DEC_GATE_POS_WEIGHT_MAX", 20.0))

        self.patch_fg_gate = nn.Sequential(
            nn.LayerNorm(dim_patch),
            nn.Linear(dim_patch, gate_hidden_dim, bias=True),
            nn.GELU(),
            nn.Linear(gate_hidden_dim, 1, bias=True),
        )

    def _foreground_gate(self, base_tokens):
        gate_base = torch.stack(base_tokens, dim=0).mean(dim=0)
        gate_logits = self.patch_fg_gate(gate_base).squeeze(-1)
        gate_prob = torch.sigmoid(gate_logits)
        gate = self.patch_dec_gate_min + (self.patch_dec_gate_max - self.patch_dec_gate_min) * gate_prob
        return gate_logits, gate_prob, gate

    def _gate_loss(self, gate_logits, fg_mask):
        target = fg_mask.float()
        num_pos = target.sum()
        if num_pos <= 0:
            return None

        num_neg = target.numel() - num_pos
        pos_weight = (num_neg / num_pos.clamp_min(1.0)).clamp(
            min=1.0,
            max=self.patch_dec_gate_pos_weight_max,
        )
        return F.binary_cross_entropy_with_logits(gate_logits, target, pos_weight=pos_weight)

    def _apply_patch_dec(self, keys, tokens, batch_dict):
        if (not self.patch_dec_enabled) or len(tokens) == 0:
            return tokens

        base_tokens = [tok.squeeze(1) for tok in tokens]
        gate_logits, gate_prob, gate = self._foreground_gate(base_tokens)
        gate = gate.unsqueeze(-1)

        common_tokens = []
        unique_tokens = []
        dec_tokens = []

        for key, base in zip(keys, base_tokens):
            common = self.patch_common[key](base)
            unique = self.patch_unique[key](base)
            common_tokens.append(common)
            unique_tokens.append(unique)
            dec = base + self.patch_dec_res_scale * gate * (common + unique)
            dec_tokens.append(dec.unsqueeze(1))

        if self.training and len(tokens) >= 2:
            num_patch = base_tokens[0].shape[0]
            fg_mask, num_fg, fg_ratio = self._gt_foreground_patch_mask(
                batch_dict, num_patch, base_tokens[0].device
            )
            idx = None if fg_mask is None else fg_mask.nonzero(as_tuple=False).flatten()

            if idx is not None and idx.numel() > 0:
                common_sel = [tok.index_select(0, idx) for tok in common_tokens]
                unique_sel = [tok.index_select(0, idx) for tok in unique_tokens]

                decouple_loss = torch.stack([
                    F.cosine_similarity(c, u, dim=-1).abs().mean()
                    for c, u in zip(common_sel, unique_sel)
                ]).mean()

                common_loss = 0.0
                unique_loss = 0.0
                n_pair = 0
                for i in range(len(common_sel)):
                    for j in range(i + 1, len(common_sel)):
                        ci = F.normalize(common_sel[i], dim=-1)
                        cj = F.normalize(common_sel[j], dim=-1)
                        ui = F.normalize(unique_sel[i], dim=-1)
                        uj = F.normalize(unique_sel[j], dim=-1)
                        common_loss = common_loss + (1.0 - (ci * cj).sum(dim=-1)).mean()
                        unique_cos = (ui * uj).sum(dim=-1)
                        unique_loss = unique_loss + F.relu(unique_cos - self.patch_dec_unique_margin).mean()
                        n_pair += 1

                if n_pair > 0:
                    common_loss = common_loss / n_pair
                    unique_loss = unique_loss / n_pair

                gate_loss = self._gate_loss(gate_logits, fg_mask)
                if gate_loss is None:
                    gate_loss = base_tokens[0].new_tensor(0.0)

                patch_dec_loss = (
                    self.patch_dec_lambda_decouple * decouple_loss
                    + self.patch_dec_lambda_common * common_loss
                    + self.patch_dec_lambda_unique * unique_loss
                    + self.patch_dec_gate_loss_weight * gate_loss
                )
                batch_dict["patch_dec_loss"] = patch_dec_loss

                bg_mask = ~fg_mask
                batch_dict["patch_dec_logging"] = {
                    "patch_dec_loss_raw": patch_dec_loss.detach().item(),
                    "patch_dec_decouple": decouple_loss.detach().item(),
                    "patch_dec_common": common_loss.detach().item()
                    if isinstance(common_loss, torch.Tensor) else float(common_loss),
                    "patch_dec_unique": unique_loss.detach().item()
                    if isinstance(unique_loss, torch.Tensor) else float(unique_loss),
                    "patch_dec_gate_loss": gate_loss.detach().item(),
                    "patch_dec_gate_mean": gate_prob.detach().mean().item(),
                    "patch_dec_gate_fg_mean": gate_prob.detach()[fg_mask].mean().item(),
                    "patch_dec_gate_bg_mean": gate_prob.detach()[bg_mask].mean().item()
                    if bg_mask.any() else 0.0,
                    "patch_dec_gate_max": gate_prob.detach().max().item(),
                    "patch_dec_gate_min": gate_prob.detach().min().item(),
                    "patch_dec_res_scale": self.patch_dec_res_scale.detach().item(),
                    "patch_dec_num_patches": float(idx.numel()),
                    "patch_dec_fg_patches": float(num_fg),
                    "patch_dec_fg_ratio": float(fg_ratio),
                    "patch_dec_selection_code": 1.0,
                }

        return dec_tokens


class DecControlledA2Fusion(PatchDecA2Fusion):
    """A2Fusion whose sensor fusion is controlled by patch decomposition.

    PatchDec no longer only adds an auxiliary residual. It decomposes each
    sensor patch token into common and unique parts, predicts a foreground gate,
    then uses sensor-wise Dec scores to scale ASF's K/V tokens before
    multi-head attention. Uniform scores keep the module equivalent to ASF.
    """

    def __init__(self, model_cfg, grid_size, **kwargs):
        super().__init__(model_cfg, grid_size, **kwargs)
        dim_patch = model_cfg.UCP.DIM_PATCH
        hidden_dim = int(model_cfg.get("DEC_CONTROL_HIDDEN_DIM", max(dim_patch // 2, 1)))
        gate_hidden_dim = int(model_cfg.get("DEC_CONTROL_GATE_HIDDEN_DIM", hidden_dim))

        self.dec_control_strength = float(model_cfg.get("DEC_CONTROL_STRENGTH", 0.45))
        self.dec_control_temperature = float(model_cfg.get("DEC_CONTROL_TEMPERATURE", 1.0))
        self.dec_control_scale_min = float(model_cfg.get("DEC_CONTROL_SCALE_MIN", 0.5))
        self.dec_control_scale_max = float(model_cfg.get("DEC_CONTROL_SCALE_MAX", 1.8))
        self.dec_control_gate_min = float(model_cfg.get("DEC_CONTROL_GATE_MIN", 0.0))
        self.dec_control_gate_max = float(model_cfg.get("DEC_CONTROL_GATE_MAX", 1.0))
        self.dec_control_gate_loss_weight = float(model_cfg.get("DEC_CONTROL_GATE_LOSS_WEIGHT", 0.08))
        self.dec_control_gate_pos_weight_max = float(model_cfg.get("DEC_CONTROL_GATE_POS_WEIGHT_MAX", 30.0))
        self.dec_control_entropy_weight = float(model_cfg.get("DEC_CONTROL_ENTROPY_WEIGHT", 0.0))
        self.dec_control_balance_weight = float(model_cfg.get("DEC_CONTROL_BALANCE_WEIGHT", 0.0))
        self.dec_control_use_dec_token = bool(model_cfg.get("DEC_CONTROL_USE_DEC_TOKEN", True))
        self.dec_control_dec_res_scale = float(model_cfg.get("DEC_CONTROL_DEC_RES_SCALE", 0.05))

        def make_score_head():
            return nn.Sequential(
                nn.LayerNorm(dim_patch * 4),
                nn.Linear(dim_patch * 4, hidden_dim, bias=True),
                nn.GELU(),
                nn.Linear(hidden_dim, 1, bias=True),
            )

        self.dec_control_score = nn.ModuleDict({key: make_score_head() for key in self.key_feats})
        for head in self.dec_control_score.values():
            nn.init.zeros_(head[-1].weight)
            nn.init.zeros_(head[-1].bias)

        self.dec_control_fg_gate = nn.Sequential(
            nn.LayerNorm(dim_patch * 2),
            nn.Linear(dim_patch * 2, gate_hidden_dim, bias=True),
            nn.GELU(),
            nn.Linear(gate_hidden_dim, 1, bias=True),
        )
        nn.init.zeros_(self.dec_control_fg_gate[-1].weight)
        nn.init.constant_(
            self.dec_control_fg_gate[-1].bias,
            float(model_cfg.get("DEC_CONTROL_GATE_INIT_BIAS", -2.0)),
        )

    def _dec_control_gate_loss(self, gate_logits, fg_mask):
        target = fg_mask.float()
        num_pos = target.sum()
        if num_pos <= 0:
            return None

        num_neg = target.numel() - num_pos
        pos_weight = (num_neg / num_pos.clamp_min(1.0)).clamp(
            min=1.0,
            max=self.dec_control_gate_pos_weight_max,
        )
        return F.binary_cross_entropy_with_logits(gate_logits, target, pos_weight=pos_weight)

    def _dec_control_scores(self, keys, base_tokens, common_tokens, unique_tokens):
        common_mean = torch.stack(common_tokens, dim=0).mean(dim=0)
        unique_abs_mean = torch.stack([tok.abs() for tok in unique_tokens], dim=0).mean(dim=0)

        gate_input = torch.cat([common_mean, unique_abs_mean], dim=-1)
        gate_logits = self.dec_control_fg_gate(gate_input).squeeze(-1)
        gate_prob = torch.sigmoid(gate_logits)
        gate = self.dec_control_gate_min + (
            self.dec_control_gate_max - self.dec_control_gate_min
        ) * gate_prob

        score_logits = []
        for key, base, common, unique in zip(keys, base_tokens, common_tokens, unique_tokens):
            score_input = torch.cat([base, common, unique, (common - common_mean).abs()], dim=-1)
            score_logits.append(self.dec_control_score[key](score_input).squeeze(-1))
        score_logits = torch.stack(score_logits, dim=1)

        if score_logits.shape[1] == 1:
            sensor_prob = torch.ones_like(score_logits)
        else:
            temperature = max(self.dec_control_temperature, 1.0e-4)
            sensor_prob = torch.softmax(score_logits / temperature, dim=1)

        num_sensor = float(score_logits.shape[1])
        token_scale = 1.0 + self.dec_control_strength * gate.unsqueeze(1) * (
            num_sensor * sensor_prob - 1.0
        )
        token_scale = token_scale.clamp(min=self.dec_control_scale_min, max=self.dec_control_scale_max)

        return gate_logits, gate_prob, gate, score_logits, sensor_prob, token_scale

    def _control_regularizers(self, sensor_prob):
        entropy_loss = sensor_prob.new_tensor(0.0)
        balance_loss = sensor_prob.new_tensor(0.0)

        if self.dec_control_entropy_weight > 0.0 and sensor_prob.shape[1] > 1:
            entropy = -(sensor_prob * sensor_prob.clamp_min(1.0e-6).log()).sum(dim=1)
            entropy_loss = entropy.mean()

        if self.dec_control_balance_weight > 0.0 and sensor_prob.shape[1] > 1:
            target = sensor_prob.new_full((sensor_prob.shape[1],), 1.0 / sensor_prob.shape[1])
            balance_loss = (sensor_prob.mean(dim=0) - target).pow(2).mean()

        return entropy_loss, balance_loss

    def _apply_patch_dec(self, keys, tokens, batch_dict):
        if (not self.patch_dec_enabled) or len(tokens) == 0:
            return tokens

        base_tokens = [tok.squeeze(1) for tok in tokens]
        common_tokens = []
        unique_tokens = []

        for key, base in zip(keys, base_tokens):
            common_tokens.append(self.patch_common[key](base))
            unique_tokens.append(self.patch_unique[key](base))

        gate_logits, gate_prob, gate, _, sensor_prob, token_scale = self._dec_control_scores(
            keys,
            base_tokens,
            common_tokens,
            unique_tokens,
        )

        controlled_tokens = []
        for sensor_idx, (base, common, unique) in enumerate(zip(base_tokens, common_tokens, unique_tokens)):
            controlled = base
            if self.dec_control_use_dec_token:
                controlled = controlled + self.dec_control_dec_res_scale * gate.unsqueeze(-1) * (common + unique)
            controlled = controlled * token_scale[:, sensor_idx].unsqueeze(-1)
            controlled_tokens.append(controlled.unsqueeze(1))

        if self.training and len(tokens) >= 2:
            num_patch = base_tokens[0].shape[0]
            fg_mask, num_fg, fg_ratio = self._gt_foreground_patch_mask(
                batch_dict,
                num_patch,
                base_tokens[0].device,
            )
            idx = None if fg_mask is None else fg_mask.nonzero(as_tuple=False).flatten()

            if idx is not None and idx.numel() > 0:
                common_sel = [tok.index_select(0, idx) for tok in common_tokens]
                unique_sel = [tok.index_select(0, idx) for tok in unique_tokens]

                decouple_loss = torch.stack([
                    F.cosine_similarity(c, u, dim=-1).abs().mean()
                    for c, u in zip(common_sel, unique_sel)
                ]).mean()

                common_loss = 0.0
                unique_loss = 0.0
                n_pair = 0
                for i in range(len(common_sel)):
                    for j in range(i + 1, len(common_sel)):
                        ci = F.normalize(common_sel[i], dim=-1)
                        cj = F.normalize(common_sel[j], dim=-1)
                        ui = F.normalize(unique_sel[i], dim=-1)
                        uj = F.normalize(unique_sel[j], dim=-1)
                        common_loss = common_loss + (1.0 - (ci * cj).sum(dim=-1)).mean()
                        unique_cos = (ui * uj).sum(dim=-1)
                        unique_loss = unique_loss + F.relu(unique_cos - self.patch_dec_unique_margin).mean()
                        n_pair += 1

                if n_pair > 0:
                    common_loss = common_loss / n_pair
                    unique_loss = unique_loss / n_pair

                gate_loss = self._dec_control_gate_loss(gate_logits, fg_mask)
                if gate_loss is None:
                    gate_loss = base_tokens[0].new_tensor(0.0)
                entropy_loss, balance_loss = self._control_regularizers(sensor_prob)

                patch_dec_loss = (
                    self.patch_dec_lambda_decouple * decouple_loss
                    + self.patch_dec_lambda_common * common_loss
                    + self.patch_dec_lambda_unique * unique_loss
                    + self.dec_control_gate_loss_weight * gate_loss
                    + self.dec_control_entropy_weight * entropy_loss
                    + self.dec_control_balance_weight * balance_loss
                )
                batch_dict["patch_dec_loss"] = patch_dec_loss

                bg_mask = ~fg_mask
                logging = {
                    "patch_dec_loss_raw": patch_dec_loss.detach().item(),
                    "patch_dec_decouple": decouple_loss.detach().item(),
                    "patch_dec_common": common_loss.detach().item()
                    if isinstance(common_loss, torch.Tensor) else float(common_loss),
                    "patch_dec_unique": unique_loss.detach().item()
                    if isinstance(unique_loss, torch.Tensor) else float(unique_loss),
                    "dec_control_gate_loss": gate_loss.detach().item(),
                    "dec_control_entropy": entropy_loss.detach().item(),
                    "dec_control_balance": balance_loss.detach().item(),
                    "dec_control_fg_gate_mean": gate_prob.detach().mean().item(),
                    "dec_control_fg_gate_fg_mean": gate_prob.detach()[fg_mask].mean().item(),
                    "dec_control_fg_gate_bg_mean": gate_prob.detach()[bg_mask].mean().item()
                    if bg_mask.any() else 0.0,
                    "dec_control_scale_mean": token_scale.detach().mean().item(),
                    "dec_control_scale_min": token_scale.detach().min().item(),
                    "dec_control_scale_max": token_scale.detach().max().item(),
                    "patch_dec_num_patches": float(idx.numel()),
                    "patch_dec_fg_patches": float(num_fg),
                    "patch_dec_fg_ratio": float(fg_ratio),
                    "patch_dec_selection_code": 1.0,
                }
                for sensor_idx, key in enumerate(keys):
                    prob = sensor_prob.detach()[:, sensor_idx]
                    logging[f"dec_control_w_{key}"] = prob.mean().item()
                    logging[f"dec_control_w_fg_{key}"] = prob[fg_mask].mean().item()
                    logging[f"dec_control_w_bg_{key}"] = prob[bg_mask].mean().item() if bg_mask.any() else 0.0
                batch_dict["patch_dec_logging"] = logging

        return controlled_tokens


class TaskAwareDecControlledA2Fusion(DecControlledA2Fusion):
    """Dec-controlled ASF with foreground class-aware query modulation.

    The Dec branch predicts object-class hints for foreground patches. The hints
    supervise the Dec representation directly with GT boxes and modulate ASF's
    query/output tokens, so the control signal is tied to detection semantics
    instead of only sensor preference.
    """

    def __init__(self, model_cfg, grid_size, **kwargs):
        super().__init__(model_cfg, grid_size, **kwargs)
        dim_patch = model_cfg.UCP.DIM_PATCH
        hidden_dim = int(model_cfg.get("DEC_CONTROL_CLASS_HIDDEN_DIM", max(dim_patch // 2, 1)))

        self.dec_control_num_classes = int(model_cfg.get("DEC_CONTROL_NUM_CLASSES", 2))
        self.dec_control_class_loss_weight = float(model_cfg.get("DEC_CONTROL_CLASS_LOSS_WEIGHT", 0.2))
        self.dec_control_class_pos_weight_max = float(model_cfg.get("DEC_CONTROL_CLASS_POS_WEIGHT_MAX", 8.0))
        self.dec_control_query_strength = float(model_cfg.get("DEC_CONTROL_QUERY_STRENGTH", 0.08))
        self.dec_control_fused_res_strength = float(model_cfg.get("DEC_CONTROL_FUSED_RES_STRENGTH", 0.03))

        self.dec_control_class_head = nn.Sequential(
            nn.LayerNorm(dim_patch * 2),
            nn.Linear(dim_patch * 2, hidden_dim, bias=True),
            nn.GELU(),
            nn.Linear(hidden_dim, self.dec_control_num_classes, bias=True),
        )
        nn.init.zeros_(self.dec_control_class_head[-1].weight)
        nn.init.zeros_(self.dec_control_class_head[-1].bias)

        self.dec_control_class_context = nn.Linear(self.dec_control_num_classes, dim_patch, bias=False)
        nn.init.normal_(
            self.dec_control_class_context.weight,
            mean=0.0,
            std=float(model_cfg.get("DEC_CONTROL_CLASS_CONTEXT_INIT_STD", 0.01)),
        )

    def _class_loss(self, class_logits, class_targets, idx):
        if idx is None or idx.numel() == 0 or class_targets is None:
            return class_logits.new_tensor(0.0)

        target = class_targets.index_select(0, idx).long()
        valid = (target >= 0) & (target < self.dec_control_num_classes)
        if not valid.any():
            return class_logits.new_tensor(0.0)

        target = target[valid]
        logits = class_logits.index_select(0, idx)[valid]
        counts = torch.bincount(target, minlength=self.dec_control_num_classes).float().to(logits.device)
        weights = torch.ones(self.dec_control_num_classes, dtype=logits.dtype, device=logits.device)
        present = counts > 0
        weights[present] = (counts.sum() / counts[present].clamp_min(1.0)).clamp(
            min=1.0,
            max=self.dec_control_class_pos_weight_max,
        )
        return F.cross_entropy(logits, target, weight=weights)

    def _task_context(self, common_tokens, unique_tokens):
        common_mean = torch.stack(common_tokens, dim=0).mean(dim=0)
        unique_abs_mean = torch.stack([tok.abs() for tok in unique_tokens], dim=0).mean(dim=0)
        class_input = torch.cat([common_mean, unique_abs_mean], dim=-1)
        class_logits = self.dec_control_class_head(class_input)
        class_prob = torch.softmax(class_logits, dim=-1)
        class_context = torch.tanh(self.dec_control_class_context(class_prob))
        return class_logits, class_prob, class_context

    def _modify_query_with_patch_dec(self, q_feat, batch_dict):
        query_delta = batch_dict.get("_dec_control_query_delta", None)
        if query_delta is None:
            return q_feat
        return q_feat + query_delta.unsqueeze(1)

    def _modify_fused_tokens_with_patch_dec(self, fused_feat, batch_dict):
        fused_delta = batch_dict.get("_dec_control_fused_delta", None)
        if fused_delta is None:
            return fused_feat
        return fused_feat + fused_delta.unsqueeze(1)

    def _apply_patch_dec(self, keys, tokens, batch_dict):
        if (not self.patch_dec_enabled) or len(tokens) == 0:
            return tokens

        base_tokens = [tok.squeeze(1) for tok in tokens]
        common_tokens = []
        unique_tokens = []

        for key, base in zip(keys, base_tokens):
            common_tokens.append(self.patch_common[key](base))
            unique_tokens.append(self.patch_unique[key](base))

        gate_logits, gate_prob, gate, _, sensor_prob, token_scale = self._dec_control_scores(
            keys,
            base_tokens,
            common_tokens,
            unique_tokens,
        )
        class_logits, class_prob, class_context = self._task_context(common_tokens, unique_tokens)

        gated_context = gate.unsqueeze(-1) * class_context
        batch_dict["_dec_control_query_delta"] = self.dec_control_query_strength * gated_context
        batch_dict["_dec_control_fused_delta"] = self.dec_control_fused_res_strength * gated_context

        controlled_tokens = []
        for sensor_idx, (base, common, unique) in enumerate(zip(base_tokens, common_tokens, unique_tokens)):
            controlled = base
            if self.dec_control_use_dec_token:
                controlled = controlled + self.dec_control_dec_res_scale * gate.unsqueeze(-1) * (common + unique)
            controlled = controlled * token_scale[:, sensor_idx].unsqueeze(-1)
            controlled_tokens.append(controlled.unsqueeze(1))

        if self.training and len(tokens) >= 2:
            num_patch = base_tokens[0].shape[0]
            fg_mask, class_targets, num_fg, fg_ratio = self._gt_patch_targets(
                batch_dict,
                num_patch,
                base_tokens[0].device,
                self.dec_control_num_classes,
            )
            idx = None if fg_mask is None else fg_mask.nonzero(as_tuple=False).flatten()

            if idx is not None and idx.numel() > 0:
                common_sel = [tok.index_select(0, idx) for tok in common_tokens]
                unique_sel = [tok.index_select(0, idx) for tok in unique_tokens]

                decouple_loss = torch.stack([
                    F.cosine_similarity(c, u, dim=-1).abs().mean()
                    for c, u in zip(common_sel, unique_sel)
                ]).mean()

                common_loss = 0.0
                unique_loss = 0.0
                n_pair = 0
                for i in range(len(common_sel)):
                    for j in range(i + 1, len(common_sel)):
                        ci = F.normalize(common_sel[i], dim=-1)
                        cj = F.normalize(common_sel[j], dim=-1)
                        ui = F.normalize(unique_sel[i], dim=-1)
                        uj = F.normalize(unique_sel[j], dim=-1)
                        common_loss = common_loss + (1.0 - (ci * cj).sum(dim=-1)).mean()
                        unique_cos = (ui * uj).sum(dim=-1)
                        unique_loss = unique_loss + F.relu(unique_cos - self.patch_dec_unique_margin).mean()
                        n_pair += 1

                if n_pair > 0:
                    common_loss = common_loss / n_pair
                    unique_loss = unique_loss / n_pair

                gate_loss = self._dec_control_gate_loss(gate_logits, fg_mask)
                if gate_loss is None:
                    gate_loss = base_tokens[0].new_tensor(0.0)
                class_loss = self._class_loss(class_logits, class_targets, idx)
                entropy_loss, balance_loss = self._control_regularizers(sensor_prob)

                patch_dec_loss = (
                    self.patch_dec_lambda_decouple * decouple_loss
                    + self.patch_dec_lambda_common * common_loss
                    + self.patch_dec_lambda_unique * unique_loss
                    + self.dec_control_gate_loss_weight * gate_loss
                    + self.dec_control_class_loss_weight * class_loss
                    + self.dec_control_entropy_weight * entropy_loss
                    + self.dec_control_balance_weight * balance_loss
                )
                batch_dict["patch_dec_loss"] = patch_dec_loss

                bg_mask = ~fg_mask
                logging = {
                    "patch_dec_loss_raw": patch_dec_loss.detach().item(),
                    "patch_dec_decouple": decouple_loss.detach().item(),
                    "patch_dec_common": common_loss.detach().item()
                    if isinstance(common_loss, torch.Tensor) else float(common_loss),
                    "patch_dec_unique": unique_loss.detach().item()
                    if isinstance(unique_loss, torch.Tensor) else float(unique_loss),
                    "dec_control_gate_loss": gate_loss.detach().item(),
                    "dec_control_class_loss": class_loss.detach().item(),
                    "dec_control_entropy": entropy_loss.detach().item(),
                    "dec_control_balance": balance_loss.detach().item(),
                    "dec_control_fg_gate_mean": gate_prob.detach().mean().item(),
                    "dec_control_fg_gate_fg_mean": gate_prob.detach()[fg_mask].mean().item(),
                    "dec_control_fg_gate_bg_mean": gate_prob.detach()[bg_mask].mean().item()
                    if bg_mask.any() else 0.0,
                    "dec_control_scale_mean": token_scale.detach().mean().item(),
                    "dec_control_scale_min": token_scale.detach().min().item(),
                    "dec_control_scale_max": token_scale.detach().max().item(),
                    "dec_control_query_delta_norm": batch_dict["_dec_control_query_delta"].detach().norm(dim=-1).mean().item(),
                    "dec_control_fused_delta_norm": batch_dict["_dec_control_fused_delta"].detach().norm(dim=-1).mean().item(),
                    "patch_dec_num_patches": float(idx.numel()),
                    "patch_dec_fg_patches": float(num_fg),
                    "patch_dec_fg_ratio": float(fg_ratio),
                    "patch_dec_selection_code": 1.0,
                }
                class_prob_detached = class_prob.detach()
                for cls_idx in range(self.dec_control_num_classes):
                    logging[f"dec_control_cls_prob_{cls_idx + 1}"] = class_prob_detached[:, cls_idx].mean().item()
                    logging[f"dec_control_cls_fg_prob_{cls_idx + 1}"] = class_prob_detached[fg_mask, cls_idx].mean().item()
                for sensor_idx, key in enumerate(keys):
                    prob = sensor_prob.detach()[:, sensor_idx]
                    logging[f"dec_control_w_{key}"] = prob.mean().item()
                    logging[f"dec_control_w_fg_{key}"] = prob[fg_mask].mean().item()
                    logging[f"dec_control_w_bg_{key}"] = prob[bg_mask].mean().item() if bg_mask.any() else 0.0
                batch_dict["patch_dec_logging"] = logging

        return controlled_tokens
