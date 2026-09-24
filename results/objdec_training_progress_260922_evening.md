# ObjDec 当前训练进度与最新结果

核查时间：2026-09-22 20:47–20:50（北京时间）。只读核对宿主机 nvidia-smi、进程、状态与原始评测 JSON，未修改运行中的任务。

## 当前任务

| GPU | 任务 | 状态（最新日志） | 最近完成的验证 | 预计剩余纯训练时间 |
|---|---|---|---|---|
| 0 | V2X ASF-style C+L+R，0.16m | 第76/80轮，700/4196步 | 第75轮 | 约5小时 |
| 1 | V2X ObjDec L+R，0.16m | 第76/80轮，2500/4196步 | 第75轮 | 约4.5小时 |
| 2 | VoD ObjDec：2×2 patch＋局部编码＋适配锚框 | 已完成80轮，13:21结束；GPU空闲 | 第80轮 | 已结束 |
| 3 | V2X ObjDec C+L+R，0.16m | 第80/80轮，1600/4196步 | 第75轮 | 约49分钟 |

预计时间按当前轮耗时线性估算，未包含第80轮验证和训练后的 best/last 全量评测；训练完成不等于GPU立即空闲。三个V2X训练的failure_count均为0，进程存活，状态文件持续更新。GPU0/1另外各有一个既有π0.5服务（约8.4/8.3 GiB）；不是新增训练。整卡显存分别约29.2/32.5/0.025/30.0 GiB，GPU0/1/3利用率97–100%。

Concat与L4DR的80轮训练和最终评测此前均已完成。

## V2X 第75轮同轮对比

本地统一去重验证集1487帧，AP_R40、Moderate、严格IoU：Vehicle 0.7，Pedestrian/Cyclist 0.5。这里不是不同公开划分之间的论文表值比较。

| 方法 | 3D mean | BEV mean |
|---|---:|---:|
| Concat C+L+R | 81.458458 | 85.754368 |
| ObjDec C+L+R | 81.136563 | 85.578819 |
| ASF-style C+L+R | 80.944855 | 85.210492 |
| ObjDec L+R | 79.123113 | 83.149933 |
| L4DR L+R | 77.149994 | 81.812077 |

- 第75轮ObjDec CLR对Concat：−0.321896 3D / −0.175549 BEV；对ASF-style：+0.191708 / +0.368327。
- ObjDec LR对同轮L4DR：+1.973119 / +1.337856；对L4DR按3D选出的最佳第80轮（77.193341 / 81.691623）：+1.929772 / +1.458310。
- CLR与LR模态不同，不能把二者差距直接解释为架构收益。ASF-style为统一底座上的本地适配，不等于完整官方配方复现。

### 第75轮分类结果

| 方法 | Vehicle 3D | Pedestrian 3D | Cyclist 3D | Vehicle BEV | Pedestrian BEV | Cyclist BEV |
|---|---:|---:|---:|---:|---:|---:|
| Concat CLR | 84.64 | 76.17 | 83.57 | 91.30 | 80.03 | 85.93 |
| ObjDec CLR | 84.05 | 74.92 | 84.44 | 91.08 | 79.19 | 86.47 |
| ASF-style CLR | 84.25 | 75.16 | 83.42 | 91.08 | 78.43 | 86.12 |
| ObjDec LR | 84.11 | 72.72 | 80.54 | 90.02 | 76.33 | 83.10 |
| L4DR LR | 81.76 | 71.13 | 78.56 | 89.67 | 74.91 | 80.85 |

### 后半程趋势（3D / BEV）

| 方法 | 第65轮 | 第70轮 | 第75轮 |
|---|---:|---:|---:|
| ObjDec CLR | 81.10 / 85.54 | 81.41 / 85.62 | 81.14 / 85.58 |
| Concat CLR | 80.73 / 85.19 | 80.92 / 85.39 | 81.46 / 85.75 |
| ASF-style CLR | 80.04 / 84.74 | 80.55 / 84.94 | 80.94 / 85.21 |
| ObjDec LR | 78.37 / 82.60 | 78.33 / 82.46 | 79.12 / 83.15 |
| L4DR LR | 76.96 / 81.19 | 77.16 / 81.62 | 77.15 / 81.81 |

三模态ObjDec当前按3D选出的最佳仍是第70轮：81.405431 / 85.620082。相对Concat最佳第75轮差0.053028 / 0.134286，接近但尚未超过；第75轮小幅回落，不能说性能持续逐轮上升。第80轮尚未出验证结果。

## VoD 适配锚框实验已完成

两版均按官方EAA选择权重，同一个权重报告DC；不能分别拼接各项最高值。

| 配置 | 按EAA选出的轮次 | EAA | DC |
|---|---:|---:|---:|
| ObjDec 2×2 patch＋局部编码 | 75 | 71.23 | 84.69 |
| 上述配置＋训练集适配锚框 | 80 | 72.03 | 83.76 |
| 差值 | — | +0.80 | −0.93 |

原版第80轮为70.83 / 84.66，因此同80轮比较为EAA +1.20、DC −0.90。适配锚框带来整体区域收益，但检测走廊表现下降，不能称为全面提升。

| 类别 | 原最佳EAA | 新最佳EAA | 差值 | 原最佳DC | 新最佳DC | 差值 |
|---|---:|---:|---:|---:|---:|---:|
| Car | 68.72 | 66.93 | −1.79 | 90.74 | 89.44 | −1.30 |
| Pedestrian | 65.59 | 65.28 | −0.31 | 73.23 | 73.02 | −0.21 |
| Cyclist | 79.38 | 83.89 | +4.51 | 90.09 | 88.83 | −1.26 |

EAA增益主要来自Cyclist。本次训练中位数锚框同时调整尺寸和底部高度，不能仅凭此结果归因到某一个具体参数。

## 原始记录

- [ObjDec CLR状态](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/status.json)、[第70轮](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_070.json)、[第75轮](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_075.json)。
- [ASF-style状态](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/status.json)、[第75轮](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_075.json)。
- [ObjDec LR状态](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/status.json)、[第75轮](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_075.json)。
- [Concat第75轮](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_075.json)。
- [L4DR第75轮](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_075.json)、[第80轮](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_080.json)。
- [VoD适配锚框状态](../analysis_exports/objdec_vod_adapted_anchors_260921/status.json)、[最终第80轮指标](../analysis_exports/objdec_vod_adapted_anchors_260921/validation/epoch_080/metrics.json)、[原版第75轮指标](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075/metrics.json)。
