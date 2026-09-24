# ObjDec 0.16m：第10轮验证与同轮次对照

采集：2026-09-18T22:15:32+08:00。读取既有验证文件，没有修改训练设置或进程。工程目录仍使用TaskDec。

统一协议：去重val 1,487帧，Moderate，AP_R40，严格IoU=0.7/0.5/0.5（Vehicle/Pedestrian/Cyclist）。以下全部为第10轮验证，不混入test或不同轮次。

| 方法 | Vehicle | Pedestrian | Cyclist | 平均3D AP | 平均BEV AP |
|---|---:|---:|---:|---:|---:|
| Concat 0.4m | 40.33 | 29.69 | 57.08 | 42.36 | 60.02 |
| ASF-style patch 0.4m | 43.81 | 19.94 | 48.11 | 37.29 | 52.10 |
| ObjDec 4×4 / 0.4m | 42.28 | 22.50 | 48.66 | 37.81 | 51.60 |
| ObjDec 2×2 / 0.4m | 44.70 | 29.21 | 57.15 | 43.69 | 58.38 |
| L4DR / 0.16m | 60.67 | 49.08 | 60.40 | 56.72 | 66.74 |
| Concat 0.16m | 58.59 | 51.34 | 67.28 | 59.07 | 70.40 |
| ObjDec 2×2 / 0.16m | 59.32 | 45.65 | 63.50 | 56.16 | 67.83 |

## ObjDec第5→10轮变化

| 指标 | 第5轮 | 第10轮 | Δ |
|---|---:|---:|---:|
| Vehicle | 50.41 | 59.32 | +8.91 |
| Pedestrian | 35.93 | 45.65 | +9.72 |
| Cyclist | 46.31 | 63.50 | +17.19 |
| 平均3D | 44.22 | 56.16 | +11.94 |
| 平均BEV | 60.21 | 67.83 | +7.62 |

## 与参照方法的平均3D差距

差值=ObjDec 0.16m−参照，正值表示领先。

| 参照 | 第5轮差值 | 第10轮差值 | 差值变化 |
|---|---:|---:|---:|
| Concat 0.16m | -4.01 | -2.91 | +1.10 |
| L4DR / 0.16m | -0.52 | -0.56 | -0.04 |
| ObjDec 2×2 / 0.4m | +16.52 | +12.47 | -4.05 |

## 第10轮分类别差值

| ObjDec 0.16m−参照 | Vehicle | Pedestrian | Cyclist | 平均3D | 平均BEV |
|---|---:|---:|---:|---:|---:|
| Concat 0.16m | +0.74 | -5.70 | -3.78 | -2.91 | -2.58 |
| L4DR / 0.16m | -1.34 | -3.43 | +3.10 | -0.56 | +1.09 |
| ObjDec 2×2 / 0.4m | +14.62 | +16.44 | +6.35 | +12.47 | +9.45 |

## 当前运行状态

| GPU | 方法 | 当前轮 | batch | 最近状态更新时间 | failure_count |
|---|---|---:|---|---|---:|
| 1 | L4DR / 0.16m | 78/80 | 1900/4196 | 2026-09-18T22:15:28.997914+08:00 | 0 |
| 2 | Concat 0.16m | 21/80 | 2200/4196 | 2026-09-18T22:15:09.828705+08:00 | 0 |
| 3 | ObjDec 2×2 / 0.16m | 11/80 | 100/4196 | 2026-09-18T22:14:18.287459+08:00 | 0 |

## 解读

- ObjDec平均3D由44.22提升至56.16（+11.94）；行人35.93→45.65，骑行者46.31→63.50，三类均提升。
- 与同分辨率Concat差距4.01→2.91，缩小1.10点；第10轮Vehicle高0.74，但行人低5.70、骑行者低3.78，后两类仍是追赶重点。
- 与L4DR平均差距0.52→0.56，基本持平，不能说已经追平或稳定超越；第10轮ObjDec骑行者高3.10，车辆和行人低1.34/3.43。
- 相对旧0.4m、2×2版本，同第10轮平均3D提高12.47，行人提高16.44；细网格的早期收益仍明显。
- 只有早期少数验证点，尚不足以判断80轮后的排名。保持既定预算与验证频次。L4DR为L+R原生架构，其余为C+L+R；同轮同网格不代表同模型或同计算量。ASF-style patch未启用SCL。

## 原始第10轮文件

- [Concat 0.4m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/controlled_80ep/concat/val_epoch_010.json)
- [ASF-style patch 0.4m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/controlled_80ep/patch/val_epoch_010.json)
- [ObjDec 4×4 / 0.4m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/controlled_80ep/taskdec/val_epoch_010.json)
- [ObjDec 2×2 / 0.4m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/taskdec_patch2_80ep/taskdec/val_epoch_010.json)
- [L4DR / 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_010.json)
- [Concat 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_010.json)
- [ObjDec 2×2 / 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_010.json)
