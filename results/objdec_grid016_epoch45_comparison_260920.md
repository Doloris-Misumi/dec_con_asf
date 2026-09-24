# ObjDec 0.16m：第45轮3D、BEV结果与同轮比较

核查时间：2026-09-20T22:39:37+08:00。只读收集既有结果，未启动或修改训练。

统一口径：V2X-Radar-V、0.16m网格、去重val 1,487帧、AP_R40；Vehicle/Pedestrian/Cyclist严格IoU=0.7/0.5/0.5。主比较为Moderate；补表列Easy/Hard。不将验证分数与最终test混排。

## 第45轮 3D AP：Moderate

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- |
| ObjDec C+L+R | 80.94 | 69.98 | 81.53 | 77.48 |
| Concat C+L+R | 78.54 | 70.36 | 79.76 | 76.22 |
| L4DR L+R | 75.31 | 66.05 | 74.63 | 72.00 |
| ObjDec − Concat C+L+R | +2.40 | -0.38 | +1.76 | +1.26 |
| ObjDec − L4DR L+R | +5.63 | +3.93 | +6.90 | +5.49 |

## 第45轮 BEV AP：Moderate

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- |
| ObjDec C+L+R | 90.60 | 74.94 | 85.20 | 83.58 |
| Concat C+L+R | 90.87 | 74.75 | 83.17 | 82.93 |
| L4DR L+R | 89.15 | 70.42 | 78.12 | 79.23 |
| ObjDec − Concat C+L+R | -0.28 | +0.19 | +2.04 | +0.65 |
| ObjDec − L4DR L+R | +1.45 | +4.52 | +7.08 | +4.35 |

## ObjDec第40→45轮变化

| 指标 | 类别 | 第40轮 | 第45轮 | 变化 |
| --- | --- | --- | --- | --- |
| 3D | Vehicle | 81.24 | 80.94 | -0.30 |
| 3D | Pedestrian | 68.50 | 69.98 | +1.48 |
| 3D | Cyclist | 79.92 | 81.53 | +1.61 |
| 3D | Mean | 76.55 | 77.48 | +0.93 |
| BEV | Vehicle | 90.51 | 90.60 | +0.08 |
| BEV | Pedestrian | 73.77 | 74.94 | +1.17 |
| BEV | Cyclist | 83.61 | 85.20 | +1.59 |
| BEV | Mean | 82.63 | 83.58 | +0.95 |

## 最近均值趋势

### 3D

| 轮次 | ObjDec CLR | Concat CLR | L4DR LR | ObjDec−Concat | ObjDec−L4DR |
| --- | --- | --- | --- | --- | --- |
| 25 | 66.80 | 68.04 | 62.97 | -1.24 | +3.83 |
| 30 | 69.92 | 69.30 | 68.42 | +0.61 | +1.50 |
| 35 | 73.80 | 74.27 | 71.09 | -0.47 | +2.71 |
| 40 | 76.55 | 74.67 | 73.33 | +1.89 | +3.22 |
| 45 | 77.48 | 76.22 | 72.00 | +1.26 | +5.49 |

### BEV

| 轮次 | ObjDec CLR | Concat CLR | L4DR LR | ObjDec−Concat | ObjDec−L4DR |
| --- | --- | --- | --- | --- | --- |
| 25 | 76.83 | 75.75 | 73.87 | +1.08 | +2.97 |
| 30 | 78.38 | 79.77 | 75.33 | -1.40 | +3.05 |
| 35 | 80.90 | 80.99 | 77.38 | -0.09 | +3.52 |
| 40 | 82.63 | 82.00 | 79.20 | +0.63 | +3.43 |
| 45 | 83.58 | 82.93 | 79.23 | +0.65 | +4.35 |

## 解读

- ObjDec当前best更新为第45轮：Mean 3D 77.48、Mean BEV 83.58，相对第40轮分别提高0.93/0.95点。三维车辆小幅回落0.30点，行人和骑行者各提高1.48/1.61点；BEV三类均提高。

- 同轮Concat对照下，Mean 3D/BEV分别领先1.26/0.65点。3D车辆和骑行者更高，行人仍低0.38点；BEV车辆低0.28点，行人和骑行者高0.19/2.04点。不能概括为所有类别、所有指标都领先。

- 对Concat的Mean 3D领先由第40轮1.89缩至第45轮1.26，因为Concat同期增长1.55点，ObjDec增长0.93点；Mean BEV领先由0.63变为0.65。

- 对同轮L4DR，ObjDec的Mean 3D/BEV分别高5.49/4.35点，三类均更高。L4DR的Mean 3D本轮从73.33回落至72.00，主要为车辆回落；差距扩大既包含ObjDec改善，也包含对方波动。两者使用不同模态与架构。

- 第45轮仍是训练期val节点；不能据此提前认定最终80轮test排名。

## 其他组：最新第30轮（单独列出）

### 第30轮 3D

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- |
| ObjDec C+L+R | 72.44 | 61.76 | 75.56 | 69.92 |
| Concat C+L+R | 67.87 | 63.46 | 76.59 | 69.30 |
| L4DR L+R | 74.40 | 59.43 | 71.41 | 68.42 |
| ASF-style C+L+R | 75.28 | 63.93 | 75.87 | 71.69 |
| ObjDec L+R | 68.13 | 58.87 | 72.54 | 66.51 |

### 第30轮 BEV

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- |
| ObjDec C+L+R | 87.59 | 68.09 | 79.46 | 78.38 |
| Concat C+L+R | 88.66 | 69.71 | 80.96 | 79.77 |
| L4DR L+R | 86.91 | 63.88 | 75.20 | 75.33 |
| ASF-style C+L+R | 89.41 | 68.72 | 80.32 | 79.48 |
| ObjDec L+R | 85.98 | 65.66 | 76.37 | 76.00 |

ASF-style与ObjDec-LR尚未到第45轮，因此不加入第45轮表。第30轮ASF-style的Mean 3D/BEV为71.69/79.48，高于ObjDec CLR同期69.92/78.38；ObjDec-LR为66.51/76.00，对照L4DR同期68.42/75.33。

## 第45轮Easy/Hard补表

### 3D

| 难度 | 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- | --- |
| easy | ObjDec C+L+R | 86.73 | 72.48 | 84.34 | 81.18 |
| easy | Concat C+L+R | 87.16 | 73.02 | 83.36 | 81.18 |
| easy | L4DR L+R | 85.92 | 69.16 | 79.13 | 78.07 |
| hard | ObjDec C+L+R | 79.72 | 69.77 | 81.17 | 76.89 |
| hard | Concat C+L+R | 78.07 | 70.11 | 79.44 | 75.87 |
| hard | L4DR L+R | 73.24 | 65.74 | 74.32 | 71.10 |

### BEV

| 难度 | 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- | --- |
| easy | ObjDec C+L+R | 92.84 | 77.58 | 87.09 | 85.84 |
| easy | Concat C+L+R | 93.28 | 76.75 | 86.14 | 85.39 |
| easy | L4DR L+R | 92.22 | 73.08 | 80.90 | 82.07 |
| hard | ObjDec C+L+R | 90.24 | 74.84 | 84.96 | 83.34 |
| hard | Concat C+L+R | 90.32 | 74.60 | 83.01 | 82.64 |
| hard | L4DR L+R | 88.47 | 70.24 | 77.57 | 78.76 |

## 状态文件快照

| 方法 | 状态 | 当前轮 | batch | best轮 | best val Mean3D | failure_count | 状态时间 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ObjDec C+L+R | training | 46 | 2200/4196 | 45 | 77.48 | 0 | 2026-09-20T22:38:54.976876+08:00 |
| Concat C+L+R | complete | 80 | 4196/4196 | 75 | 81.46 | 0 | 2026-09-19T22:15:39.411604+08:00 |
| L4DR L+R | complete | 80 | 4196/4196 | 80 | 77.19 | 0 | 2026-09-18T23:47:11.252655+08:00 |
| ASF-style C+L+R | training | 33 | 700/4196 | 30 | 71.69 | 0 | 2026-09-20T22:38:39.630260+08:00 |
| ObjDec L+R | training | 33 | 1300/4196 | 30 | 66.51 | 0 | 2026-09-20T22:38:12.474275+08:00 |

## 原始结果来源

- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_025.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_025.json)；SHA256 `9a3788f8cac3361029535c8b54d0681ca81acb669e3702194d040e0bd5f330e0`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_030.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_030.json)；SHA256 `afb88697e07cf1ec6b9e75d7ba5299b4ddb7aa2e4e05e22e7a800c7bcf3fc1d4`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_035.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_035.json)；SHA256 `e00987bf520a119828cfcfdfed2aa4b5664ddccdd43af814ab217251633bb12b`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_040.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_040.json)；SHA256 `c8031c54424d107e1f5b861fd2f1c9c7f0a201fcaf9c04becb7a804a2cdbb8cb`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_045.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_045.json)；SHA256 `31d1968e9252da5ed8b6e334fceaf57429e481bbfd5ef8ef214227224eb09279`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_025.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_025.json)；SHA256 `39bd52e4150b0325212a7fe8d75a568d82cfd681b50b774f9094529424506511`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_030.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_030.json)；SHA256 `6a676bc8554394324716343d1b2a9937a061716fc4c7ae7fba6a47d75e0f915c`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_035.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_035.json)；SHA256 `6ed53d8f82034ac2d8280c6c06b53e340dc9b3adc45e80d1da3225dcc7ac4404`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_040.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_040.json)；SHA256 `8633dc202ce4760fac7d4bb2a19856a982ae6ecea8469f2b24b4afe35eb833cb`。

- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_045.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_045.json)；SHA256 `9e5cffe74664b005a93b7053524e224f6b083bbfe2e132a9167fbf85d3660a0a`。

- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_025.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_025.json)；SHA256 `5aa098d0e9def454b09f96ec4d99e85026718f0ab23039bff4de807519b32bfe`。

- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_030.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_030.json)；SHA256 `a1ebcfec0ad2f665f4e800f8842472744827f8db8cfd7808caf5063ce63a9ecd`。

- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_035.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_035.json)；SHA256 `6ac75ed778faccd6e6e18e1a720080d05be6d3b1dd04fa4c43692a81d3359c71`。

- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_040.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_040.json)；SHA256 `f5f8c9908f73de5b5d8ac1f97b3b3ad7635184d63bea2aa9c22b710b8fabe2b1`。

- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_045.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_045.json)；SHA256 `d43087c42a9ae37d56e233d9f28533ad03d3d5787c22745ee10fec1dbfe05983`。

- [analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_030.json](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_030.json)；SHA256 `2ec2f392d645689916fc89b58e5767b6249639ddef184801a29df7c3c30986bc`。

- [analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_030.json](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_030.json)；SHA256 `78db8c90b0d933b5fe23e65d0d565f76ab4af64b0a9daaad8e373992e4a6c8ec`。
