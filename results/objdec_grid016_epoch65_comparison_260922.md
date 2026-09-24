# V2X-Radar-V：ObjDec 第65轮结果与对比

整理时间：2026-09-22T01:51:31+08:00。本轮仅收集结果，没有启动或修改实验。

采用当前本地统一协议：0.16m 网格、去重验证集 1,487 帧、AP_R40；主比较为 Moderate 严格 IoU（Vehicle 0.7、Pedestrian/Cyclist 0.5）。Vehicle 合并 Car/Truck/Bus。不是直接与公开论文不同划分的汇总值比较。

第65轮达到 3D **81.095092**、BEV **85.542294**，是三模态 ObjDec 当前已验证候选中的最佳。相对第60轮提高 0.658216 / 0.465175 个百分点，三类两项指标均上升。

## 第65轮 3D

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
|---|---:|---:|---:|---:|
| ObjDec C+L+R | 84.37 | 74.56 | 84.35 | 81.10 |
| Concat C+L+R | 84.26 | 75.11 | 82.82 | 80.73 |
| L4DR L+R | 82.63 | 70.74 | 77.51 | 76.96 |
| ObjDec−Concat | +0.12 | -0.55 | +1.53 | +0.36 |

## 第65轮 BEV

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
|---|---:|---:|---:|---:|
| ObjDec C+L+R | 91.27 | 78.72 | 86.64 | 85.54 |
| Concat C+L+R | 90.90 | 79.24 | 85.43 | 85.19 |
| L4DR L+R | 89.51 | 74.20 | 79.86 | 81.19 |
| ObjDec−Concat | +0.37 | -0.52 | +1.21 | +0.36 |

L4DR 同轮 3D/BEV 为 76.960004/81.192409，ObjDec CLR 高 4.135088/4.349885；两者模态不同，不能将全部差距归因于融合架构。

## 后半程同轮趋势

| 轮次 | ObjDec 3D | Concat 3D | 差值 | ObjDec BEV | Concat BEV | 差值 |
|---|---:|---:|---:|---:|---:|---:|
| 45 | 77.48 | 76.22 | +1.26 | 83.58 | 82.93 | +0.65 |
| 50 | 78.38 | 77.90 | +0.48 | 84.11 | 83.69 | +0.42 |
| 55 | 80.44 | 79.09 | +1.36 | 85.12 | 84.46 | +0.66 |
| 60 | 80.44 | 80.26 | +0.18 | 85.08 | 84.66 | +0.42 |
| 65 | 81.10 | 80.73 | +0.36 | 85.54 | 85.19 | +0.36 |

第60→65轮，ObjDec 的3D优势从 +0.18 扩到 +0.36，但BEV优势从 +0.42 缩至 +0.36，因此不能说所有指标的领先都在逐轮扩大。第65轮对Concat的优势主要由骑行者贡献：3D +1.53、BEV +1.21；车辆小幅领先，行人仍低 0.55/0.52。

## 与完成80轮的Concat最佳候选比较

Concat按严格Moderate 3D选出的最佳为第75轮：81.458458 / 85.754368。同一权重与ObjDec第65轮比较，当前仍差 **0.36 / 0.21**；该差距相比第60轮的1.02/0.68缩小，但双方轮次不同，不构成同轮胜负。

相对Concat第75轮，ObjDec第65轮车辆3D −0.26、行人 −1.61、骑行者 +0.78；BEV为 −0.03/−1.31/+0.71。行人是目前追上Concat最佳候选最明显的缺口；这一观察本身不能确定缺口来自定位、分类还是训练波动。

## ASF-style及双模态：最新共同验证为第55轮

| 方法（第55轮） | 3D Mean | BEV Mean |
|---|---:|---:|
| ObjDec C+L+R | 80.44 | 85.12 |
| Concat C+L+R | 79.09 | 84.46 |
| L4DR L+R | 75.31 | 81.08 |
| ASF-style C+L+R | 79.14 | 84.02 |
| ObjDec L+R | 77.19 | 82.14 |

同模态比较：ObjDec CLR 对 ASF-style CLR 为 +1.30 3D / +1.10 BEV；ObjDec LR 对 L4DR LR 为 +1.88 / +1.06。ASF-style 与 ObjDec LR 目前没有第65轮验证，不混入第65轮同轮主表。ASF-style是统一底座的本地适配，不能标为完整官方配方复现。

ObjDec LR 第55轮3D为77.193290，与L4DR第80轮最佳77.193341几乎相同，差 −0.000051；两位小数均77.19。对应BEV 82.143089对81.691623高0.45。轮次不同，仅作为阶段性参考，不写成双模态3D已超过L4DR最终最佳。

## 第65轮补充难度与宽松阈值

| 指标／IoU | 难度 | Vehicle | Pedestrian | Cyclist | Mean |
|---|---|---:|---:|---:|---:|
| 3D / strict | easy | 89.72 | 76.57 | 86.36 | 84.22 |
| 3D / strict | moderate | 84.37 | 74.56 | 84.35 | 81.10 |
| 3D / strict | hard | 81.96 | 74.47 | 84.08 | 80.17 |
| 3D / loose | easy | 94.03 | 86.89 | 92.53 | 91.15 |
| 3D / loose | moderate | 93.73 | 85.27 | 91.17 | 90.06 |
| 3D / loose | hard | 93.54 | 85.20 | 91.10 | 89.95 |
| BEV / strict | easy | 93.40 | 80.34 | 88.50 | 87.41 |
| BEV / strict | moderate | 91.27 | 78.72 | 86.64 | 85.54 |
| BEV / strict | hard | 90.86 | 78.65 | 86.33 | 85.28 |
| BEV / loose | easy | 95.24 | 87.26 | 92.83 | 91.77 |
| BEV / loose | moderate | 94.33 | 85.61 | 91.32 | 90.42 |
| BEV / loose | hard | 93.86 | 85.53 | 91.27 | 90.22 |

strict为0.7/0.5/0.5，loose为0.5/0.25/0.25；不把两者混为同一个mAP口径。

## 状态文件记录

截至读取时，ObjDec CLR状态文件记录第66轮1400/4196步；ASF-style和ObjDec LR均记录第58轮。该信息来自status.json；本会话nvidia-smi无法访问驱动，因此未据此确认实时GPU占用或进程存活。

## 原始结果来源（SHA256）

- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_065.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_065.json)：`8a28bb61d556933fa6e17e5f3fb938fe2285f2697ed138f4076e57edd880f9fe`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_065.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_065.json)：`7013d422f7e1d9788d2ea9d866aaad7ecb27284583380db48dee0ed950624074`。
- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_065.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_065.json)：`d6ec5067d92d51e5855180f3a6b970b1839fd2d72070fa90f3c1be0be1e31e54`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_045.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_045.json)：`31d1968e9252da5ed8b6e334fceaf57429e481bbfd5ef8ef214227224eb09279`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_045.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_045.json)：`9e5cffe74664b005a93b7053524e224f6b083bbfe2e132a9167fbf85d3660a0a`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_050.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_050.json)：`5761b241cfd9fdabb6334615cce6ca073cde30ea45093adbb7a71b5273a23416`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_050.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_050.json)：`bb718d072304d66c7f2ee0fda9a95a6a3e1edfec929441c7d02596fd1a5f9951`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_055.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_055.json)：`ed1d8e10e6ae0ba136fa60ff5a4f2b56af22a7cf7b189ce03b6cd1d36ef0ab29`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_055.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_055.json)：`ac3e77374f9b91305383c45c106fa88c7c4f5c0984afaa36e23488c8ed3a81f9`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_060.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_060.json)：`c3e85ebd7d04cbad418689e24ea9bdb241ef2c171dc9f21463f8f7aedd58b25c`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_060.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_060.json)：`208c5f1d448faa05fdf940e7532c5998bd17f7d9bf2916b480079cdcf52824ba`。
- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_055.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_055.json)：`89e9b64b9e31b760af5832d6b4194854cc8fb9d6cacdce2825d13939b140ab41`。
- [analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_055.json](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_055.json)：`cdf66805620f94cc8f9f85231a5bda5d964fca501429edcef04a5bdb49f17e7f`。
- [analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_055.json](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_055.json)：`6400f29a0418673e04b9e649d258e7f3aa5a729e7f3c19f3de3558c39c02f090`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_075.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_075.json)：`16886ba43a31e1ae2aecb1c6e4efd35a670a4108a2e3ae1d49182cb622dcd5bf`。
- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_080.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_080.json)：`5b09f09ba0d3b986d5f985cfeff41fa792f770bd031d865d7eabebf2fed33dc4`。
