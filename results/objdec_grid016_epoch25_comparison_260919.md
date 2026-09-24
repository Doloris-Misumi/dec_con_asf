**ObjDec 0.16m 第25轮验证结果与同轮比较**

核查时间：2026-09-19T19:34:30.660418+08:00。仅收集状态与结果，没有改变训练。

统一口径：V2X-Radar-V 去重 val 1,487 帧；Moderate；AP_R40；严格 IoU=0.7/0.5/0.5。以下全部为验证集结果。

| 第25轮方法 | Vehicle | Pedestrian | Cyclist | 平均3D | 平均BEV |
|---|---:|---:|---:|---:|---:|
| ObjDec C+L+R / 0.16m | 68.42 | 59.49 | 72.49 | 66.80 | 76.83 |
| Concat C+L+R / 0.16m | 70.63 | 61.58 | 71.92 | 68.04 | 75.75 |
| L4DR L+R / 0.16m | 64.63 | 57.22 | 67.06 | 62.97 | 73.87 |
| 旧 ObjDec 2×2 / 0.4m | 62.46 | 40.31 | 67.03 | 56.60 | 68.41 |

**ObjDec 第20→25轮变化**

| 指标 | 第20轮 | 第25轮 | 差值 |
|---|---:|---:|---:|
| Vehicle | 72.53 | 68.42 | -4.10 |
| Pedestrian | 56.38 | 59.49 | +3.10 |
| Cyclist | 73.20 | 72.49 | -0.71 |
| 平均3D | 67.37 | 66.80 | -0.57 |
| 平均BEV | 75.48 | 76.83 | +1.35 |

**平均3D趋势**

| 轮次 | ObjDec | Concat | L4DR | ObjDec−Concat | ObjDec−L4DR |
|---|---:|---:|---:|---:|---:|
| 5 | 44.22 | 48.23 | 44.74 | -4.01 | -0.52 |
| 10 | 56.16 | 59.07 | 56.72 | -2.91 | -0.56 |
| 15 | 64.67 | 64.74 | 60.40 | -0.07 | +4.27 |
| 20 | 67.37 | 68.95 | 63.09 | -1.58 | +4.28 |
| 25 | 66.80 | 68.04 | 62.97 | -1.24 | +3.83 |

**解释**

- 第25轮平均3D 66.80，低于第20轮67.37；best仍为第20轮。行人提高3.10点，车辆降低4.10点，骑行者降低0.71点。
- Concat同期平均3D也由68.95降至68.04；ObjDec与Concat差距由1.58缩至1.24点。这个缩小部分来自Concat回落，不能表述为ObjDec持续增长。
- 第25轮ObjDec相对Concat的车辆/行人/骑行者为-2.21/-2.09/+0.57点。行人差距从3.55缩至2.09点；车辆差距扩大。
- 第25轮ObjDec平均BEV为76.83，高于Concat的75.75，差值+1.08点。
- 第25轮ObjDec平均3D高于同轮L4DR 3.83点；相比旧0.4m的2×2版本提高10.20点。C+L+R与L+R的输入不同，不能视为全条件对齐。
- ObjDec车辆严格BEV由86.35升至86.91，宽松IoU的3D由89.45升至91.05，但严格3D从72.53降至68.42。这提示应优先分析严格三维框匹配（包括z/高度/尺寸等），而不是直接认定目标识别整体退化；仅凭AP不能确认具体原因。
- ObjDec、Concat与L4DR在该阶段的车辆严格3D均回落，但这不足以认定存在同一个训练或评测问题。当前failure_count均为0。

**当前状态与新对照**

| GPU | 方法 | 状态 | 最新完整验证 | 最新平均3D |
|---|---|---|---:|---:|
| 0 | ASF-style C+L+R / 0.16m | 第7/80轮，batch 3300/4196 | 5 | 43.54 |
| 1 | ObjDec L+R / 0.16m | 第7/80轮，batch 3300/4196 | 5 | 45.87 |
| 2 | Concat C+L+R / 0.16m | 第74/80轮，batch 3000/4196 | 70 | 80.92 |
| 3 | ObjDec C+L+R / 0.16m | 第26/80轮，batch 2800/4196 | 25 | 66.80 |

新对照第5轮平均3D：ASF-style C+L+R 43.54；ObjDec L+R 45.87；原ObjDec C+L+R 44.22；L4DR L+R 44.74。ObjDec-LR同轮高于L4DR 1.13点，但仍属于早期结果。ASF-style为no-SCL本地适配。

**原始第25轮结果**

- [ObjDec C+L+R / 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_025.json)；SHA256 `9a3788f8cac3361029535c8b54d0681ca81acb669e3702194d040e0bd5f330e0`。
- [Concat C+L+R / 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_025.json)；SHA256 `39bd52e4150b0325212a7fe8d75a568d82cfd681b50b774f9094529424506511`。
- [L4DR L+R / 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_025.json)；SHA256 `5aa098d0e9def454b09f96ec4d99e85026718f0ab23039bff4de807519b32bfe`。
- [旧 ObjDec 2×2 / 0.4m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/taskdec_patch2_80ep/taskdec/val_epoch_025.json)；SHA256 `4a372b1681010503382e43db15b700cf8909686a9eb88c4455a1eb9c1b2ed4a8`。
