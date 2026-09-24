# VoD ObjDec第75轮：固定权重后处理诊断

2026-09-21。已完成1,296帧验证；本轮没有训练新模型，未修改既有训练配置、权重或论文结果表。

## 结论

降低置信度阈值没有提高整体AP，放宽NMS只带来很小的行人收益，未找回更多骑行者真阳性。当前证据不支持指望这两项后处理调整补齐骑行者差距。下一项训练更值得独立验证训练集适配锚框，之后再考虑更细网格；本轮尚未启动这些训练。

## 固定条件与复现核对

- ObjDec 2×2 patch＋局部编码，第75轮 `best_eaa.pth`。权重SHA256及源文件校验见[manifest](../analysis_exports/objdec_vod_postprocess_diagnostic_260921/manifest.json)。
- 同一批1,296帧共享网络前向，只切换score或NMS阈值。GT未传入网络，只用于离线评价。
- 原生VoD EAA（Entire Annotated Area）/DC（Driving Corridor）；Car/Pedestrian/Cyclist的3D IoU阈值为0.5/0.25/0.25，沿用官方过滤、匹配和11点AP汇总，不混入KITTI AP_R40。
- 原设置每帧类别、分数和框与历史epoch75缓存完全相同；EAA/DC完整复现71.23/84.69。见[预测核对](../analysis_exports/objdec_vod_postprocess_diagnostic_260921/baseline_prediction_check.json)。
- GPU2完成共享前向后转CPU评分；GPU峰值张量分配约2.04 GiB，新增结果目录约31.55 MiB，无特征图和权重副本。

## 官方3D AP

AP以百分数表示，Δ为相对原设置的百分点差。NMS仍为原实现的跨类别BEV NMS。

### EAA

| 设置 | Score | NMS IoU | Car | Pedestrian | Cyclist | Mean | ΔMean |
|---|---:|---:|---:|---:|---:|---:|---:|
| 原设置 | 0.10 | 0.01 | 68.72 | 65.59 | 79.38 | 71.23 | — |
| 只降低score | 0.01 | 0.01 | 67.03 | 65.78 | 79.38 | 70.73 | −0.50 |
| 只放宽NMS | 0.10 | 0.10 | 68.56 | 65.80 | 79.36 | 71.24 | +0.01 |

### DC

| 设置 | Car | Pedestrian | Cyclist | Mean | ΔMean |
|---|---:|---:|---:|---:|---:|
| 原设置 | 90.74 | 73.23 | 90.09 | 84.69 | — |
| 只降低score | 90.74 | 73.23 | 90.09 | 84.69 | 0.00 |
| 只放宽NMS | 90.74 | 73.60 | 90.09 | 84.81 | +0.12 |

放宽NMS的收益集中在行人：EAA +0.21、DC +0.37；骑行者EAA −0.02、DC不变。0.01点的整体EAA变化不构成明显改善。

## 召回与误检

在各设置自己的保留分数阈值处，使用官方过滤与一对一匹配统计。诊断Recall=TP/有效GT，Precision=TP/(TP+FP)，不是AP。DC的忽略项可能使TP+FN不等于有效GT；保留原匹配行为，没有人为修正。

| 区域/类别 | 设置 | TP | FP | Recall (%) | Precision (%) |
|---|---|---:|---:|---:|---:|
| EAA / Cyclist | 原设置 | 1,229 | 989 | 85.70 | 55.41 |
| EAA / Cyclist | 只降低score | 1,251 | 32,445 | 87.24 | 3.71 |
| EAA / Cyclist | 只放宽NMS | 1,229 | 1,054 | 85.70 | 53.83 |
| DC / Cyclist | 原设置 | 553 | 209 | 94.05 | 72.57 |
| DC / Cyclist | 只降低score | 553 | 2,319 | 94.05 | 19.25 |
| DC / Cyclist | 只放宽NMS | 553 | 218 | 94.05 | 71.73 |
| EAA / Pedestrian | 原设置 | 2,791 | 4,719 | 74.45 | 37.16 |
| EAA / Pedestrian | 只降低score | 2,945 | 138,446 | 78.55 | 2.08 |
| EAA / Pedestrian | 只放宽NMS | 2,826 | 5,192 | 75.38 | 35.25 |
| DC / Pedestrian | 原设置 | 1,413 | 1,869 | 82.83 | 43.05 |
| DC / Pedestrian | 只降低score | 1,470 | 25,052 | 86.17 | 5.54 |
| DC / Pedestrian | 只放宽NMS | 1,432 | 2,069 | 83.94 | 40.90 |

- 降低score：总检测框由14,444增至200,985。EAA骑行者增加22个TP、31,456个FP；DC骑行者没有增加TP，骑行者AP没有收益。
- 放宽NMS：总检测框为15,162。EAA/DC行人分别增加35/19个TP和473/200个FP；骑行者TP不变。
- 低score组中所有score≥0.1的预测与原设置逐帧完全一致，见[高分框核对](../analysis_exports/objdec_vod_postprocess_diagnostic_260921/low_score_high_confidence_check.json)。Car AP下降不代表高分框被网络改坏；官方实现按候选匹配结果重新选择离散阈值并进行11点汇总。保留该原始评分结果，不把AP变化简单等同于某个阈值的FP变化。

## NMS影响对象

检查有效GT是否至少有同类预测达到评测3D IoU。这是候选覆盖诊断，不等同于一对一召回。

| 类别 | 新增覆盖GT | 失去覆盖GT | 新增项中同类抑制候选 | 新增项中跨类抑制候选 |
|---|---:|---:|---:|---:|
| Car | 5 | 0 | 1 | 4 |
| Pedestrian | 36 | 1 | 34 | 2 |
| Cyclist | 0 | 0 | 0 | 0 |

例如帧00141中一个行人候选score=0.161、3D IoU=0.486，与原设置保留的另一行人框BEV IoU约0.041，可在NMS=0.1时保留。多数新增行人覆盖对应同类近邻，单纯改按类别NMS不会解除这类同类抑制。上述证据来自高分保留框和重叠关系，不是完整逐步NMS轨迹。

本轮没有继续增加按类别NMS实验：尚未发现宽松NMS恢复骑行者覆盖，跨类现象主要在少量汽车。这仅覆盖本次阈值范围，不能排除重叠更大的骑行者候选仍被抑制。完整实例见[nms_recovered_coverage.json](../analysis_exports/objdec_vod_postprocess_diagnostic_260921/nms_recovered_coverage.json)。

## 下一步

1. 原score=0.1/NMS=0.01继续作为既有基准；NMS=0.1仅作为诊断记录，暂不替换正式结果。以后若换后处理，本地对照也应使用一致设置。
2. 优先独立验证0.16m下训练集适配锚框。先按实际训练过滤核对统计、冻结先验，再从头训练。骑行者默认长宽1.76/0.60m，而训练ROI内中位数约1.94/0.78m，是值得检验的先验差异，并非已经证明的瓶颈。不能只改解码锚框套用旧权重。
3. 后续再独立测试0.10m或0.128m网格。本轮尚未区分分类、排序、定位和点云稀疏性各自的误差占比，不承诺细网格收益。

详细分析见[后续计划](objdec_vod_next_steps_260921.md)。本轮没有证据支持继续大范围搜索这两个阈值。

## 评分加速与索引

CPU评分仅将官方重叠计算分块改成一帧一块，避免计算后续丢弃的跨帧组合；过滤、IoU、匹配、阈值和AP规则未变。12帧2D/BEV/3D重叠矩阵逐位相同，完整基线AP与默认分块及历史结果一致，见[分块核对](../analysis_exports/objdec_vod_postprocess_diagnostic_260921/partition_verification.json)。基线评分由约141秒降至17秒，属于评分加速，不是网络推理速度提升。未修改共享评测源码。

- [完整三组指标](../analysis_exports/objdec_vod_postprocess_diagnostic_260921/summary.json)
- [完成状态](../analysis_exports/objdec_vod_postprocess_diagnostic_260921/status.json)
- [推理与诊断脚本](../scripts/diagnose_objdec_vod_postprocess_260921.py)
- [CPU缓存评分脚本](../scripts/score_objdec_vod_postprocess_260921.py)
- [评分日志](../vod_taskdec_native/logs/objdec_vod_postprocess_scoring_260921.log)

三组预测缓存在结果目录的 `baseline/`、`score001/`、`nms010/` 下，全部评分完成。
