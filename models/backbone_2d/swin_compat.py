from functools import partial
from typing import Callable, List, Optional

import torch
import torch.nn.functional as F
from torch import Tensor, nn
from torchvision.ops import StochasticDepth


class Permute(nn.Module):
    def __init__(self, dims):
        super().__init__()
        self.dims = dims

    def forward(self, x):
        return torch.permute(x, self.dims)


class MLP(nn.Sequential):
    def __init__(self, in_channels, hidden_channels, activation_layer=nn.GELU, dropout=0.0):
        layers = []
        in_dim = in_channels
        for idx, hidden_dim in enumerate(hidden_channels):
            layers.append(nn.Linear(in_dim, hidden_dim))
            if idx < len(hidden_channels) - 1:
                layers.append(activation_layer())
                layers.append(nn.Dropout(dropout))
            in_dim = hidden_dim
        layers.append(nn.Dropout(dropout))
        super().__init__(*layers)


def _patch_merging_pad(x):
    h, w, _ = x.shape[-3:]
    return F.pad(x, (0, 0, 0, w % 2, 0, h % 2))


class PatchMerging(nn.Module):
    def __init__(self, dim: int, norm_layer: Callable[..., nn.Module] = nn.LayerNorm):
        super().__init__()
        self.dim = dim
        self.reduction = nn.Linear(4 * dim, 2 * dim, bias=False)
        self.norm = norm_layer(4 * dim)

    def forward(self, x: Tensor):
        x = _patch_merging_pad(x)
        x0 = x[..., 0::2, 0::2, :]
        x1 = x[..., 1::2, 0::2, :]
        x2 = x[..., 0::2, 1::2, :]
        x3 = x[..., 1::2, 1::2, :]
        x = torch.cat([x0, x1, x2, x3], -1)
        x = self.norm(x)
        x = self.reduction(x)
        return x


def _meshgrid_ij(coords_h, coords_w):
    try:
        return torch.meshgrid(coords_h, coords_w, indexing="ij")
    except TypeError:
        return torch.meshgrid(coords_h, coords_w)


def shifted_window_attention(
    input: Tensor,
    qkv_weight: Tensor,
    proj_weight: Tensor,
    relative_position_bias: Tensor,
    window_size: List[int],
    num_heads: int,
    shift_size: List[int],
    attention_dropout: float = 0.0,
    dropout: float = 0.0,
    qkv_bias: Optional[Tensor] = None,
    proj_bias: Optional[Tensor] = None,
):
    b, h, w, c = input.shape
    pad_r = (window_size[1] - w % window_size[1]) % window_size[1]
    pad_b = (window_size[0] - h % window_size[0]) % window_size[0]
    x = F.pad(input, (0, 0, 0, pad_r, 0, pad_b))
    _, pad_h, pad_w, _ = x.shape

    shift_size = shift_size.copy()
    if window_size[0] >= pad_h:
        shift_size[0] = 0
    if window_size[1] >= pad_w:
        shift_size[1] = 0

    if sum(shift_size) > 0:
        x = torch.roll(x, shifts=(-shift_size[0], -shift_size[1]), dims=(1, 2))

    num_windows = (pad_h // window_size[0]) * (pad_w // window_size[1])
    x = x.view(b, pad_h // window_size[0], window_size[0], pad_w // window_size[1], window_size[1], c)
    x = x.permute(0, 1, 3, 2, 4, 5).reshape(b * num_windows, window_size[0] * window_size[1], c)

    qkv = F.linear(x, qkv_weight, qkv_bias)
    qkv = qkv.reshape(x.size(0), x.size(1), 3, num_heads, c // num_heads).permute(2, 0, 3, 1, 4)
    q, k, v = qkv[0], qkv[1], qkv[2]
    q = q * (c // num_heads) ** -0.5
    attn = q.matmul(k.transpose(-2, -1))
    attn = attn + relative_position_bias

    if sum(shift_size) > 0:
        attn_mask = x.new_zeros((pad_h, pad_w))
        h_slices = ((0, -window_size[0]), (-window_size[0], -shift_size[0]), (-shift_size[0], None))
        w_slices = ((0, -window_size[1]), (-window_size[1], -shift_size[1]), (-shift_size[1], None))
        count = 0
        for h_slice in h_slices:
            for w_slice in w_slices:
                attn_mask[h_slice[0]:h_slice[1], w_slice[0]:w_slice[1]] = count
                count += 1
        attn_mask = attn_mask.view(
            pad_h // window_size[0], window_size[0], pad_w // window_size[1], window_size[1]
        )
        attn_mask = attn_mask.permute(0, 2, 1, 3).reshape(num_windows, window_size[0] * window_size[1])
        attn_mask = attn_mask.unsqueeze(1) - attn_mask.unsqueeze(2)
        attn_mask = attn_mask.masked_fill(attn_mask != 0, float(-100.0)).masked_fill(
            attn_mask == 0, float(0.0)
        )
        attn = attn.view(x.size(0) // num_windows, num_windows, num_heads, x.size(1), x.size(1))
        attn = attn + attn_mask.unsqueeze(1).unsqueeze(0)
        attn = attn.view(-1, num_heads, x.size(1), x.size(1))

    attn = F.softmax(attn, dim=-1)
    attn = F.dropout(attn, p=attention_dropout, training=True)

    x = attn.matmul(v).transpose(1, 2).reshape(x.size(0), x.size(1), c)
    x = F.linear(x, proj_weight, proj_bias)
    x = F.dropout(x, p=dropout, training=True)

    x = x.view(b, pad_h // window_size[0], pad_w // window_size[1], window_size[0], window_size[1], c)
    x = x.permute(0, 1, 3, 2, 4, 5).reshape(b, pad_h, pad_w, c)

    if sum(shift_size) > 0:
        x = torch.roll(x, shifts=(shift_size[0], shift_size[1]), dims=(1, 2))

    return x[:, :h, :w, :].contiguous()


class ShiftedWindowAttention(nn.Module):
    def __init__(
        self,
        dim: int,
        window_size: List[int],
        shift_size: List[int],
        num_heads: int,
        qkv_bias: bool = True,
        proj_bias: bool = True,
        attention_dropout: float = 0.0,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.window_size = window_size
        self.shift_size = shift_size
        self.num_heads = num_heads
        self.attention_dropout = attention_dropout
        self.dropout = dropout
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.proj = nn.Linear(dim, dim, bias=proj_bias)
        self.relative_position_bias_table = nn.Parameter(
            torch.zeros((2 * window_size[0] - 1) * (2 * window_size[1] - 1), num_heads)
        )

        coords_h = torch.arange(self.window_size[0])
        coords_w = torch.arange(self.window_size[1])
        coords = torch.stack(_meshgrid_ij(coords_h, coords_w))
        coords_flatten = torch.flatten(coords, 1)
        relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]
        relative_coords = relative_coords.permute(1, 2, 0).contiguous()
        relative_coords[:, :, 0] += self.window_size[0] - 1
        relative_coords[:, :, 1] += self.window_size[1] - 1
        relative_coords[:, :, 0] *= 2 * self.window_size[1] - 1
        relative_position_index = relative_coords.sum(-1).view(-1)
        self.register_buffer("relative_position_index", relative_position_index)
        nn.init.trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, x: Tensor):
        n = self.window_size[0] * self.window_size[1]
        relative_position_bias = self.relative_position_bias_table[self.relative_position_index]
        relative_position_bias = relative_position_bias.view(n, n, -1)
        relative_position_bias = relative_position_bias.permute(2, 0, 1).contiguous().unsqueeze(0)
        return shifted_window_attention(
            x,
            self.qkv.weight,
            self.proj.weight,
            relative_position_bias,
            self.window_size,
            self.num_heads,
            self.shift_size,
            attention_dropout=self.attention_dropout,
            dropout=self.dropout,
            qkv_bias=self.qkv.bias,
            proj_bias=self.proj.bias,
        )


class SwinTransformerBlock(nn.Module):
    def __init__(
        self,
        dim: int,
        num_heads: int,
        window_size: List[int],
        shift_size: List[int],
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
        attention_dropout: float = 0.0,
        stochastic_depth_prob: float = 0.0,
        norm_layer: Callable[..., nn.Module] = nn.LayerNorm,
        attn_layer: Callable[..., nn.Module] = ShiftedWindowAttention,
    ):
        super().__init__()
        self.norm1 = norm_layer(dim)
        self.attn = attn_layer(
            dim,
            window_size,
            shift_size,
            num_heads,
            attention_dropout=attention_dropout,
            dropout=dropout,
        )
        self.stochastic_depth = StochasticDepth(stochastic_depth_prob, "row")
        self.norm2 = norm_layer(dim)
        self.mlp = MLP(dim, [int(dim * mlp_ratio), dim], activation_layer=nn.GELU, dropout=dropout)

        for m in self.mlp.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.normal_(m.bias, std=1e-6)

    def forward(self, x: Tensor):
        x = x + self.stochastic_depth(self.attn(self.norm1(x)))
        x = x + self.stochastic_depth(self.mlp(self.norm2(x)))
        return x


class SwinTransformer(nn.Module):
    def __init__(
        self,
        patch_size: List[int],
        embed_dim: int,
        depths: List[int],
        num_heads: List[int],
        window_size: List[int],
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
        attention_dropout: float = 0.0,
        stochastic_depth_prob: float = 0.0,
        num_classes: int = 1000,
        norm_layer: Optional[Callable[..., nn.Module]] = None,
        block: Optional[Callable[..., nn.Module]] = None,
    ):
        super().__init__()
        if block is None:
            block = SwinTransformerBlock
        if norm_layer is None:
            norm_layer = partial(nn.LayerNorm, eps=1e-5)

        layers: List[nn.Module] = []
        layers.append(
            nn.Sequential(
                nn.Conv2d(3, embed_dim, kernel_size=(patch_size[0], patch_size[1]), stride=(patch_size[0], patch_size[1])),
                Permute([0, 2, 3, 1]),
                norm_layer(embed_dim),
            )
        )

        total_stage_blocks = sum(depths)
        stage_block_id = 0
        for i_stage, depth in enumerate(depths):
            stage: List[nn.Module] = []
            dim = embed_dim * 2 ** i_stage
            for i_layer in range(depth):
                sd_prob = stochastic_depth_prob * float(stage_block_id) / (total_stage_blocks - 1)
                stage.append(
                    block(
                        dim,
                        num_heads[i_stage],
                        window_size=window_size,
                        shift_size=[0 if i_layer % 2 == 0 else w // 2 for w in window_size],
                        mlp_ratio=mlp_ratio,
                        dropout=dropout,
                        attention_dropout=attention_dropout,
                        stochastic_depth_prob=sd_prob,
                        norm_layer=norm_layer,
                    )
                )
                stage_block_id += 1
            layers.append(nn.Sequential(*stage))
            if i_stage < len(depths) - 1:
                layers.append(PatchMerging(dim, norm_layer))

        self.features = nn.Sequential(*layers)
        num_features = embed_dim * 2 ** (len(depths) - 1)
        self.norm = norm_layer(num_features)
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Linear(num_features, num_classes)

        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x):
        x = self.features(x)
        x = self.norm(x)
        x = x.permute(0, 3, 1, 2)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.head(x)


def _swin_transformer(patch_size, embed_dim, depths, num_heads, window_size, stochastic_depth_prob, **kwargs):
    return SwinTransformer(
        patch_size=patch_size,
        embed_dim=embed_dim,
        depths=depths,
        num_heads=num_heads,
        window_size=window_size,
        stochastic_depth_prob=stochastic_depth_prob,
        **kwargs,
    )


def swin_t(pretrained=False, progress=True, **kwargs):
    return _swin_transformer([4, 4], 96, [2, 2, 6, 2], [3, 6, 12, 24], [7, 7], 0.2, **kwargs)


def swin_s(pretrained=False, progress=True, **kwargs):
    return _swin_transformer([4, 4], 96, [2, 2, 18, 2], [3, 6, 12, 24], [7, 7], 0.3, **kwargs)


def swin_b(pretrained=False, progress=True, **kwargs):
    return _swin_transformer([4, 4], 128, [2, 2, 18, 2], [4, 8, 16, 32], [7, 7], 0.5, **kwargs)
