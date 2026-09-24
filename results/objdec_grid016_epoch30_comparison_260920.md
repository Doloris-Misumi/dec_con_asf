# ObjDec 0.16m 第30轮验证与同轮比较

核查时间：2026-09-20T01:51:11+08:00。只读收集状态与结果；没有改变训练。

统一口径：V2X-Radar-V 去重 val 1,487 帧；Moderate；AP_R40；严格 IoU（Vehicle/Pedestrian/Cyclist）=0.7/0.5/0.5。以下同轮表及趋势均为验证集结果，差值按未舍入数值计算。

## 同第30轮结果

| 方法 | Vehicle | Pedestrian | Cyclist | 平均3D | 平均BEV |
|---|---:|---:|---:|---:|---:|
| ObjDec C+L+R / 0.16m | 72.44 | 61.76 | 75.56 | 69.92 | 78.38 |
| Concat C+L+R / 0.16m | 67.87 | 63.46 | 76.59 | 69.30 | 79.77 |
| L4DR L+R / 0.16m | 74.40 | 59.43 | 71.41 | 68.42 | 75.33 |
| 旧 ObjDec 2×2 / 0.4m | 68.25 | 44.60 | 67.88 | 60.24 | 70.28 |

## ObjDec 第25→30轮

| 指标 | 第25轮 | 第30轮 | 变化 |
|---|---:|---:|---:|
| Vehicle | 68.42 | 72.44 | +4.01 |
| Pedestrian | 59.49 | 61.76 | +2.27 |
| Cyclist | 72.49 | 75.56 | +3.07 |
| 平均3D | 66.80 | 69.92 | +3.12 |
| 平均BEV | 76.83 | 78.38 | +1.55 |

## 平均3D趋势

| 轮次 | ObjDec | Concat | L4DR | ObjDec−Concat | ObjDec−L4DR |
|---|---:|---:|---:|---:|---:|
| 5 | 44.22 | 48.23 | 44.74 | -4.01 | -0.52 |
| 10 | 56.16 | 59.07 | 56.72 | -2.91 | -0.56 |
| 15 | 64.67 | 64.74 | 60.40 | -0.07 | +4.27 |
| 20 | 67.37 | 68.95 | 63.09 | -1.58 | +4.28 |
| 25 | 66.80 | 68.04 | 62.97 | -1.24 | +3.83 |
| 30 | 69.92 | 69.30 | 68.42 | +0.61 | +1.50 |

## 解读

- ObjDec 第30轮平均3D达到69.92，比第25轮提高3.12点，比此前最佳第20轮提高2.55点；当前best已更新为第30轮。三类均比第25轮提高。
- 与同轮Concat的平均3D差值由第25轮−1.24转为第30轮+0.61。ObjDec相对Concat的车辆/行人/骑行者分别为+4.57/−1.70/−1.03点，平均BEV仍低1.40点。当前优势主要来自车辆，不能表述为所有类别或所有指标均领先。
- Concat同期平均3D也提高1.26点，因此平均3D的反超并非来自Concat总体回落；但Concat车辆AP同期降低2.76点，车辆单项差距受双方波动影响。
- 与同轮L4DR相比，ObjDec平均3D高1.50点、平均BEV高3.05点；车辆低1.97点，行人和骑行者高2.33/4.15点。L4DR第25→30轮增长5.45点，ObjDec对它的领先从3.83缩至1.50点。两者输入模态和网络结构不同。
- 与旧0.4m、2×2 ObjDec相比，同第30轮平均3D高9.68点，行人高17.16点。该比较体现网格细化后的配置收益，不能全部归因于解耦架构。
- 第30轮是训练期验证节点；尚不能推出ObjDec最终80轮能保持领先，也不将其与最终test分数直接比较。

## 当前运行状态

| GPU | 方法 | 状态 | 最新完整验证 | 最新平均3D | failure_count |
|---|---|---|---:|---:|---:|
| 3 | ObjDec C+L+R / 0.16m | 第31/80轮，1100/4196 batch | 30 | 69.92 | 0 |
| 2 | Concat C+L+R / 0.16m | 80轮及最终复评完成 | 80 | 81.31 | 0 |
| 0 | ASF-style C+L+R / 0.16m | 第13/80轮，2900/4196 batch | 10 | 53.16 | 0 |
| 1 | ObjDec L+R / 0.16m | 第13/80轮，3100/4196 batch | 10 | 51.99 | 0 |

ASF-style与ObjDec-LR尚未到第30轮；两者最新完整验证均为第10轮。GPU2已空闲；GPU0/1另有原驻留服务进程。

## 已完成Concat的最终结果（单列）

- best去重val（1,487帧）：平均3D 81.46，平均BEV 85.75；best由val选择，为第75轮。
- best去重test（1,486帧）：平均3D 81.90，平均BEV 86.47；best由val选择，为第75轮。

该test结果仅记录Concat训练完成后的终点，不与上面的ObjDec第30轮val作直接优劣比较。

## 原始结果与来源

- [ObjDec C+L+R / 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_030.json)；SHA256 `afb88697e07cf1ec6b9e75d7ba5299b4ddb7aa2e4e05e22e7a800c7bcf3fc1d4`。
- [Concat C+L+R / 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_030.json)；SHA256 `6a676bc8554394324716343d1b2a9937a061716fc4c7ae7fba6a47d75e0f915c`。
- [L4DR L+R / 0.16m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_030.json)；SHA256 `a1ebcfec0ad2f665f4e800f8842472744827f8db8cfd7808caf5063ce63a9ecd`。
- [旧 ObjDec 2×2 / 0.4m](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/taskdec_patch2_80ep/taskdec/val_epoch_030.json)；SHA256 `0d8038839479c0a3391d3998c59821eca4464d38441994644fac85cc737b72de`。
- [ASF-style C+L+R / 0.16m，第10轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_010.json)。
- [ObjDec L+R / 0.16m，第10轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_010.json)。
- [Concat最终best完整复评](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/concat/final_best.json)。
