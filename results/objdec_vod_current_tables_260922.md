# VoD 当前结果表：锚框适配完成后

整理日期：2026-09-22。适配锚框实验已于13:21完成80轮；按每5轮完整验证的EAA选模，最佳为第80轮，EAA/DC=72.03/83.76。

## 官方 VoD 3D AP

下面各行为 **LiDAR＋4D Radar**，无额外人工雾，使用官方区域/类别过滤和11点AP，Car/Pedestrian/Cyclist的3D IoU阈值为0.5/0.25/0.25。EAA是Entire Annotated Area，DC是Driving Corridor；不是3D与BEV两种指标。

本地验证集1,296帧。每一行EAA与DC来自同一个权重，不能把不同轮次最高值拼接。论文报告与本地训练分别标注，训练预算及选模方式并不完全相同。

### EAA：整体标注区域

| 方法 | 权重轮次 | Car | Pedestrian | Cyclist | mAP |
|---|---:|---:|---:|---:|---:|
| PP-Concat，历史本地基线 | 80 | 66.88 | 63.38 | 79.39 | 69.88 |
| 旧ObjDec，warm-start＋mild | 79 | 67.50 | 63.66 | 79.38 | 70.18 |
| ObjDec，2×2 patch＋局部编码 | 75 | 68.72 | 65.59 | 79.38 | 71.23 |
| ObjDec，上述配置＋适配锚框 | 80 | 66.93 | 65.28 | 83.89 | 72.03 |
| L4DR，本地复现 | 99 | 68.69 | 65.35 | 78.98 | 71.00 |
| InterFusion，论文报告 | — | 66.50 | 64.50 | 78.50 | 69.83 |
| L4DR，论文报告 | — | 69.10 | 66.20 | 82.80 | 72.70 |

### DC：检测走廊

| 方法 | 权重轮次 | Car | Pedestrian | Cyclist | mAP |
|---|---:|---:|---:|---:|---:|
| PP-Concat，历史本地基线 | 80 | 90.77 | 71.09 | 89.53 | 83.80 |
| 旧ObjDec，warm-start＋mild | 79 | 90.59 | 71.02 | 89.76 | 83.79 |
| ObjDec，2×2 patch＋局部编码 | 75 | 90.74 | 73.23 | 90.09 | 84.69 |
| ObjDec，上述配置＋适配锚框 | 80 | 89.44 | 73.02 | 88.83 | 83.76 |
| L4DR，本地复现 | 99 | 90.51 | 75.13 | 88.90 | 84.84 |
| InterFusion，论文报告 | — | 90.70 | 72.00 | 88.70 | 83.80 |
| L4DR，论文报告 | — | 90.80 | 76.10 | 95.50 | 87.47 |

论文两行已核对 [L4DR AAAI 2025 正式论文 Table 3](https://ojs.aaai.org/index.php/AAAI/article/view/32397/34552)。其表只给三类AP，此处mAP为三类公开数值的算术平均；本地mAP保留原始评分输出，因此与已四舍五入类别数值的重新平均可能差0.01。

## 锚框适配带来什么变化

相对2×2 patch＋局部编码版本的EAA最佳第75轮：

| 区域 | ΔCar | ΔPedestrian | ΔCyclist | ΔmAP |
|---|---:|---:|---:|---:|
| EAA | −1.79 | −0.31 | +4.51 | +0.80 |
| DC | −1.30 | −0.21 | −1.26 | −0.93 |

整体区域的骑行者是主要增益来源；EAA骑行者83.89也高于L4DR论文82.80，但其余类别和DC并未同步提升。不能据此确定收益来自更远距离，或某一个具体定位误差，需要另做分距离与误差分析。

- 对本地L4DR第99轮：EAA +1.03，DC −1.08。
- 对L4DR论文：EAA −0.67，DC −3.71。DC差距以骑行者最大（−6.67），其次为行人（−3.08）与车辆（−1.36）。
- 对历史PP-Concat：EAA +2.15，DC −0.04。但历史Concat没有同步增加局部编码等变化，因此不能把这2.15全部视为单一解耦设计的收益。

新旧两组均为80轮预算、每5轮验证。若严格同第80轮比较，旧版70.83/84.66，新版72.03/83.76，差值为EAA +1.20、DC −0.90。新旧最佳候选比较和同轮比较方向一致。

## 补充：相同选中权重的 KITTI AP_R40

这里是另一套评测汇总：IoU仍为Car0.5、Pedestrian/Cyclist0.25，但采用KITTI难度过滤与AP_R40。不得直接与EAA/DC数值互换。

| 版本 | 指标 | Easy均值 | Moderate均值 | Hard均值 |
|---|---|---:|---:|---:|
| 2×2＋局部编码，第75轮 | 3D | 83.43 | 78.64 | 72.23 |
| ＋适配锚框，第80轮 | 3D | 83.06 | 78.35 | 72.02 |
| 2×2＋局部编码，第75轮 | BEV | 85.47 | 80.55 | 74.56 |
| ＋适配锚框，第80轮 | BEV | 85.33 | 80.92 | 75.02 |

适配锚框的KITTI Moderate 3D均值反而下降0.29，而BEV上升0.37。这进一步表明该改动是指标与类别间的取舍，不能表述为全面增强。

## 选模和训练差异

- 两个近期ObjDec版本均从头训练80轮，FP32，微批次8×累积2，有效batch16；每5轮验证，按官方EAA选模。本次锚框适配只改三类尺寸和底部高度，使用训练集统计。
- 历史PP-Concat为AMP、实际batch16、末轮80；旧ObjDec warm版本从Concat初始化。它们是历史参照，不是对近期组合改动的严格独立消融。
- 本地L4DR训练100轮、双GPU、总batch16、SyncBN；此处第99轮是已评估末期候选中较优者，不宣称扫描所有100轮后的最优。
- 后处理诊断中，旧第75轮放宽NMS至0.1得到71.24/84.81，属于固定权重后处理对照，未作为统一原设置的主表结果。本表两组新训练均保留score0.1、NMS0.01。
- 本文VoD表可以报告跨数据集训练适配能力及明确的指标收益；现有结果不支持“VoD全面超过L4DR”或“VoD SOTA”。

## 结果来源

- [新锚框版本第80轮](../analysis_exports/objdec_vod_adapted_anchors_260921/validation/epoch_080/metrics.json)、[KITTI原始段落](../analysis_exports/objdec_vod_adapted_anchors_260921/validation/epoch_080/kitti.txt)、[完成状态](../analysis_exports/objdec_vod_adapted_anchors_260921/status.json)。
- [2×2＋局部编码第75轮](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075/metrics.json)、[KITTI原始段落](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075/kitti.txt)。
- [历史PP-Concat及warm版本官方评分记录](paper_vod_main_table_draft_260909.md)。
- [L4DR本地复现记录](l4dr_vod_local_repro_results_260910.md)。
- [后处理诊断](objdec_vod_postprocess_diagnostic_260921.md)。
