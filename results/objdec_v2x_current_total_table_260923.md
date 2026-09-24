# V2X-Radar-V 当前总表与训练进度

核查时间：2026-09-23T07:55:24+08:00。

## 1. 完成情况

| 方法 | 模态 | 训练进度 | 当前best轮次 | 最终best/last测试 |
| --- | --- | --- | --- | --- |
| Concat | C+L+R | 80/80，已完成 | 75 | 已完成 |
| ASF-style | C+L+R | 80/80，已完成 | 80 | 已完成 |
| ObjDec | C+L+R | 80/80，已完成 | 70 | 已完成 |
| L4DR | L+R | 80/80，已完成 | 80 | 已完成 |
| ObjDec-LR | L+R | 80/80，已完成 | 75 | 已完成 |

上述五组训练及best/last最终评测均已完成。此汇表脚本不查询其他项目的实时GPU占用。

## 2. 统一协议与最终测试表

以下均为0.16 m网格、80轮训练预算，按去重验证集平均strict Moderate 3D AP选择best，再在1,486帧去重test评测。AP_R40，Vehicle/Pedestrian/Cyclist的IoU依次为0.7/0.5/0.5，Mean为三类等权平均。训练集8,391帧、去重val 1,487帧，有效batch为8。数值为百分数，差值为百分点。

前三行为共同编码器和检测头下的C+L+R融合比较；后两行为保留原生网络差异的L+R架构比较。ASF-style是本地no-SCL适配。本地划分与ROI不同于公开论文基准，不据此直接声称超过公开榜单。

### 3D AP_R40（best，test）

| 方法 | 模态 | 选中轮次 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- | --- | --- |
| Concat | C+L+R | 75 | 84.81 | 76.84 | 84.05 | 81.90 |
| ASF-style | C+L+R | 80 | 84.54 | 76.17 | 83.18 | 81.30 |
| ObjDec | C+L+R | 70 | 84.06 | 75.94 | 84.13 | 81.38 |
| L4DR | L+R | 80 | 83.17 | 73.25 | 78.31 | 78.24 |
| ObjDec-LR | L+R | 75 | 83.87 | 74.84 | 80.24 | 79.65 |

### BEV AP_R40（best，test）

| 方法 | 模态 | 选中轮次 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- | --- | --- |
| Concat | C+L+R | 75 | 92.12 | 80.66 | 86.64 | 86.47 |
| ASF-style | C+L+R | 80 | 90.95 | 80.41 | 85.80 | 85.72 |
| ObjDec | C+L+R | 70 | 90.91 | 80.88 | 87.02 | 86.27 |
| L4DR | L+R | 80 | 89.74 | 76.60 | 81.35 | 82.56 |
| ObjDec-LR | L+R | 75 | 90.02 | 78.34 | 83.08 | 83.81 |

## 3. 末轮补充（test，不用于重新选模）

| 方法 | 轮次 | Mean 3D | Mean BEV |
| --- | --- | --- | --- |
| Concat | 80 | 81.97 | 86.47 |
| ASF-style | 80 | 81.30 | 85.72 |
| ObjDec | 80 | 81.55 | 86.35 |
| L4DR | 80 | 78.24 | 82.56 |
| ObjDec-LR | 80 | 79.75 | 83.80 |

## 4. 当前验证集候选（val，不能填入上述test表）

| 方法 | 当前best轮次 | Val mean 3D | Val mean BEV |
| --- | --- | --- | --- |
| Concat | 75 | 81.46 | 85.75 |
| ASF-style | 80 | 81.03 | 85.17 |
| ObjDec | 70 | 81.41 | 85.62 |
| L4DR | 80 | 77.19 | 81.69 |
| ObjDec-LR | 75 | 79.12 | 83.15 |

验证分数来自训练期val_epoch文件。最终重评的最后几位可能有数值波动；选模仍以训练期记录为准。

## 5. 目前可得出的结论

- ObjDec三模态最终best为第70轮，test平均3D/BEV为81.38/86.27；相对Concat第75轮分别为-0.52/-0.20点，整体尚未超过Concat。
- 分类别看，ObjDec的Cyclist 3D为+0.08点，Pedestrian/Cyclist BEV分别为+0.22/+0.38点；主要差距在Vehicle，以及Pedestrian 3D。
- 验证集best对比，ObjDec-LR比L4DR高1.93点3D、1.46点BEV。此行为val结果。
- 最终test同模态比较：ObjDec-LR（第75轮）为79.65/83.81，相对L4DR（第80轮）分别为+1.41/+1.25点3D/BEV。
- 最终test同模态比较：ObjDec（第70轮）为81.38/86.27，相对ASF-style（第80轮）分别为+0.08/+0.55点3D/BEV。
- 第80轮结果作为附录补充；不能因其test略高而替换预先按val选择的best。

## 6. 来源与复查

[原始精度CSV](../analysis_exports/objdec_v2x_table_snapshot_260923/metrics.csv)；[状态、结果与来源SHA-256快照](../analysis_exports/objdec_v2x_table_snapshot_260923/snapshot.json)。汇总仅读取已有JSON，未启动模型或修改训练。

- Concat：[运行目录](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/concat)；[status](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/concat/status.json)；[final_best](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/concat/final_best.json)
- ASF-style：[运行目录](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch)；[status](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/status.json)；[final_best](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/final_best.json)
- ObjDec：[运行目录](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/taskdec)；[status](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/status.json)；[final_best](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/final_best.json)
- L4DR：[运行目录](/home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr)；[status](/home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/status.json)；[final_best](/home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/final_best.json)
- ObjDec-LR：[运行目录](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec)；[status](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/status.json)；[final_best](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/final_best.json)
