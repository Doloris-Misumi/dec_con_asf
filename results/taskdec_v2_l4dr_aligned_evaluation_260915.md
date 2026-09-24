# K-Radar v2：L4DR 统一评测与 Strong / ASF 对照

完成时间：2026-09-15T21:21:27.500426+08:00

本次已完成 L4DR 双类别官方权重在 **v2.0、13,727 帧、与 Strong 完全相同 GT 和 revised evaluator** 下的全量评测。两类平均 AP3D@0.3 / @0.5：L4DR 为 69.48 / 48.23，Strong 为 66.91 / 43.05；Strong 相对 L4DR 的差值为 **-2.57 / -5.18 AP 点**。

本次结果不支持“统一评测后 Strong 的 Total 领先 L4DR”。Strong 相对官方 ASF 归档的均值收益仍是 +0.36 / +1.48 点（AP3D@0.3 / @0.5）；v2 写作可继续聚焦 Dec 家族在宽 ROI、双类别设置下相对 ASF 的扩展收益，同时保留 L4DR 的更高 Total 和天气上的完整正负结果。

**来源边界：** L4DR 为本次本地推理，Strong 为原有预测的本次复算；ASF 保留官方结果归档，本次没有其逐帧预测可供重新评分。L4DR 与 Strong 已核实逐帧 GT 完全相同，ASF 的配置口径一致但本轮未逐帧核验。表中三行均明确来源，不能把 ASF 行写成“三方法本次同时复测”。

## 1. 对齐了哪些项目

| 项目 | 本次设置 / 核验 |
| --- | --- |
| 评测标签 | K-Radar v2_0；Sedan + Bus or Truck；onlyR=False |
| ROI | [0, −16, −2, 72, 16, 7.6]；标定 z_offset=0.7 |
| 测试帧 | 13,727 帧；与 Strong 保存的 GT 和天气元数据逐帧、逐行完全一致 |
| GT 数量 | Sedan 29,613；Bus/Truck 5,843 |
| 前处理置信度 | NMS 前 SCORE_THRESH=0.1；最终导出 score > 0.3 |
| NMS | 原生 class-agnostic rotated NMS；IoU=0.01；pre=4096 / post=500；两仓库 NMS 源码相同 |
| KITTI 导出 | 直接调用 TaskDec 原始导出函数；GT 四舍五入到 2 位，坐标/尺寸顺序一致 |
| 评测器 | TaskDec revised evaluator：41 个 precision 值平均、z_center=0.5；不是标准 KITTI R40 |
| Strong 归档复核 | 全部 18 条件 × 2 类 × 6 指标 = 216 项；与原归档差值全部为 0 |
| L4DR 输入与结构 | 原生 LiDAR + 正式恢复的稀疏雷达张量；MGF backbone；DENOISE_T=0.1 |
| 权重加载 | 双类别 572 项参数 strict=True；无 missing/unexpected keys，无舍弃权重 |

未统一训练过程、模态或模型自身输入编码：L4DR 使用 L+R，Strong/ASF 使用 C+L+R。本次统一测试协议，不声称三者经过相同训练。L4DR 当前公开配置的有效 `MODEL.POST_PROCESSING.NMS_CONFIG.NMS_THRESH` 是 0.7，另一个 `DENSE_HEAD.POST_PROCESSING` 中的 0.01 不被其最终后处理读取。本次明确将有效阈值对齐到 Strong/ASF 的 0.01；该设置在推理前确定，未依据测试 AP 调参。因此本次是包括后处理在内的统一协议实验，不能当成仅替换 evaluator 的原生 L4DR 结果。

## 2. Total：完整六项指标

AP 单位为百分数；Mean 为两类 AP 的等权平均。Total 直接汇总全测试集计算，不是天气 AP 的平均。

| 方法 | 类别 | 3D@0.3 | 3D@0.5 | 3D@0.7 | BEV@0.3 | BEV@0.5 | BEV@0.7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L4DR local aligned | Sedan | 76.79 | 54.68 | 11.23 | 79.90 | 73.61 | 49.16 |
| L4DR local aligned | Bus/Truck | 62.17 | 41.78 | 10.49 | 67.12 | 56.86 | 29.65 |
| L4DR local aligned | Mean | 69.48 | 48.23 | 10.86 | 73.51 | 65.23 | 39.41 |
| ASF official archive | Sedan | 74.98 | 52.09 | 11.85 | 77.85 | 71.70 | 43.21 |
| ASF official archive | Bus/Truck | 58.13 | 31.06 | 7.93 | 67.85 | 53.21 | 20.85 |
| ASF official archive | Mean | 66.55 | 41.57 | 9.89 | 72.85 | 62.45 | 32.03 |
| DecControlled Strong | Sedan | 74.58 | 52.14 | 12.31 | 77.32 | 71.27 | 44.26 |
| DecControlled Strong | Bus/Truck | 59.24 | 33.97 | 9.92 | 65.14 | 50.59 | 23.13 |
| DecControlled Strong | Mean | 66.91 | 43.05 | 11.11 | 71.23 | 60.93 | 33.69 |

## 3. 天气表（参考 L4DR Table 10 的组织）

天气仅改变评测分组，不改变模型或阈值。Fog 的 Bus/Truck GT 数为 0，显示“—”；CSV 保留 evaluator 原始 0 并设置 has_gt=False，不能将它算作有效收益。

### AP3D@0.3

| 类别 | 方法 | Total | Normal | Light snow | Heavy snow | Rain | Sleet | Overcast | Fog |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sedan | L4DR local aligned | 76.79 | 75.52 | 87.71 | 58.49 | 78.25 | 67.17 | 83.57 | 93.60 |
| Sedan | ASF official archive | 74.98 | 74.14 | 88.24 | 63.61 | 66.37 | 70.43 | 82.35 | 92.26 |
| Sedan | DecControlled Strong | 74.58 | 73.51 | 89.56 | 63.57 | 68.11 | 72.52 | 84.30 | 94.46 |
| Bus/Truck | L4DR local aligned | 62.17 | 56.27 | 80.47 | 63.76 | 2.96 | 74.75 | 87.43 | — |
| Bus/Truck | ASF official archive | 58.13 | 53.28 | 88.26 | 68.20 | 7.89 | 59.55 | 75.33 | — |
| Bus/Truck | DecControlled Strong | 59.24 | 51.63 | 89.56 | 72.34 | 10.08 | 57.47 | 73.82 | — |

### AP3D@0.5

| 类别 | 方法 | Total | Normal | Light snow | Heavy snow | Rain | Sleet | Overcast | Fog |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sedan | L4DR local aligned | 54.68 | 50.21 | 62.32 | 53.33 | 53.03 | 47.42 | 56.53 | 83.81 |
| Sedan | ASF official archive | 52.09 | 49.63 | 59.25 | 49.52 | 46.85 | 44.05 | 53.38 | 80.55 |
| Sedan | DecControlled Strong | 52.14 | 49.39 | 60.75 | 50.49 | 48.30 | 49.13 | 59.62 | 80.30 |
| Bus/Truck | L4DR local aligned | 41.78 | 36.60 | 53.30 | 41.11 | 0.68 | 62.92 | 76.06 | — |
| Bus/Truck | ASF official archive | 31.06 | 23.93 | 70.81 | 32.55 | 2.48 | 38.83 | 47.04 | — |
| Bus/Truck | DecControlled Strong | 33.97 | 23.94 | 75.09 | 39.37 | 5.05 | 38.48 | 49.65 | — |

所有 18 条件、两类、3D/BEV 三个 IoU 阈值及正负差值见 [paper_kradar_v2_l4dr_asf_strong_aligned_260915.csv](paper_kradar_v2_l4dr_asf_strong_aligned_260915.csv)。

## 4. 固定预测后的评测协议交叉检查

下表只改变 AP 的 11/41 点汇总方式和 IoU 的高度中心；GT、预测、NMS 与置信度固定。这能量化 evaluator 的影响，不能把本次本地结果与论文 Table 10 的差值全部归因于 evaluator。

| 方法 | AP 汇总点数 | z_center | Mean AP3D@0.3 | Mean AP3D@0.5 |
| --- | --- | --- | --- | --- |
| Strong | 11 | 1.0 | 62.01 | 39.46 |
| Strong | 11 | 0.5 | 63.26 | 43.66 |
| Strong | 41 | 1.0 | 63.93 | 40.04 |
| Strong | 41 | 0.5 | 66.91 | 43.05 |
| L4DR | 11 | 1.0 | 66.44 | 46.37 |
| L4DR | 11 | 0.5 | 70.86 | 47.75 |
| L4DR | 41 | 1.0 | 67.43 | 45.27 |
| L4DR | 41 | 0.5 | 69.48 | 48.23 |

11 点 + z_center=1.0 与原始 legacy API 数值一致；41 点 + z_center=0.5 与本次 revised 全量结果一致。改变高度中心不影响 BEV 的几何 IoU；更换 AP 汇总点数仍会改变 BEV AP。

## 5. 权重身份、论文引用与写作建议

原本地 `L4DR-KRadar-v1.1-model_34.pt` 是 Sedan 单类别，不能装成双类别用。本次采用作者发布的 [L4DR_KRadar2.1 双类别权重](https://huggingface.co/hx24/L4DR_KRadar2.1)，固定 revision `4f65460867a61a704a2290ff0ca2e8d05b463312` 的 `model_30.pt`。同目录 `model.pt` 的 LFS SHA 相同，只下载一份，没有比较多个 checkpoint 后挑选最优。

checkpoint SHA-256：`ccdc151a0c16185be8ab1801affed1f71fd6f63ae6f3c2fbf94c30346a0d8180`。发布名称为 v2.1；本次评测强制使用并核验 v2.0 标签。不能据此宣称重现了论文 Table 10 的 checkpoint、训练标签和完整运行环境。

表行建议写 `L4DR (official checkpoint, locally evaluated)`；Strong 继续写 `DecControlled Strong (ours)`，并说明它不含 task-context 分支。ASF 继续写 `ASF (official archived results)`。如需保留 Table 10 原始引用，另列 `L4DR (paper)` 并指向旧表，不用新数值覆盖文献原值。

English table note: L4DR is evaluated locally from the author-released dual-class checkpoint on the exact v2.0 frames and ground-truth boxes used by DecControlled Strong. Both local rows use the revised evaluator, a score threshold of 0.3, and class-agnostic rotated NMS at 0.01. The ASF row contains archived official results under the corresponding configuration and is not rescored in this run. L4DR uses L+R; ASF and Strong use C+L+R. Strong is a Dec-family variant without task-context modulation.

## 6. 文件与复现

- [本次运行目录与命令](../analysis_exports/l4dr_v2_aligned_260915/README.md)
- [逐帧核验与协议](../analysis_exports/l4dr_v2_aligned_260915/preflight.json)
- [L4DR 原始全量指标](../analysis_exports/l4dr_v2_aligned_260915/l4dr_evaluation.json)
- [Strong 复算全量指标](../analysis_exports/l4dr_v2_aligned_260915/strong_evaluation.json)
- [Strong 归档 216 项核验](../analysis_exports/l4dr_v2_aligned_260915/strong_archive_verification.json)
- [原论文天气对照与历史协议审计](taskdec_v2_l4dr_weather_total_and_eval_protocol_audit_260912.md)
- [LaTeX 紧凑 Total + 天气表](paper_kradar_v2_l4dr_asf_strong_aligned_260915.tex)

只保存一份预测文本，天气/道路/昼夜按索引分组评测，不复制 GT、点云或完整特征。下载权重约 237 MiB；原始雷达输入复用此前 WCBR 已完成的恢复目录。原生 Dataset 会累计缓存已读点云，本次仅在独立 runner 中修正其内存保留行为；修正前的短暂未完成运行另存为 partial，未纳入 AP。
