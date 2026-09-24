# V2X-Radar-V：公开方法规模、性能水平与 SOTA 表述核查

核查日期：2026-09-20。范围是车端单车三维检测 V2X-Radar-V；不把协同感知 V2X-Radar-C、路侧 V2X-Radar-I 或另一个数据集 V2X-R 混为同一排行榜。本轮仅检索和整理，没有修改或启动训练。

## 结论

公开车端结果目前能够明确核实的主体是原数据集论文的 12 种完整基准方法，另外有车端恶劣天气子集的 M2-Fusion 对照，以及至少一篇 2026 年明确使用 V2X-Radar-V 的新方法 PhD-DETR。这个数量是本轮可核实的下界，不是穷尽统计，也不代表有 14 篇专门针对该数据集的新方法论文。

ObjDec 当前第45轮的本地验证集 Mean 3D AP 为 77.48，数值上处于较高水平。不过，本地协议与公开主表尚未完全对应，且本地同预算训练尚未全部完成，因此目前不能据此声称 V2X-Radar-V 公开基准 SOTA。

## 1. 官方完整车端主表

来源：[NeurIPS 2025 数据集论文 Table 4](https://papers.nips.cc/paper_files/paper/2025/file/a501f3238029713afdad57ce7924667a-Paper-Datasets_and_Benchmarks_Track.pdf)。下面只提取 Moderate、严格 IoU 的 3D AP；Vehicle/Pedestrian/Cyclist 的 IoU 分别为 0.7/0.5/0.5。Mean 是这里用三个类别 AP 计算的算术平均，不是原表另行报告的指标。

| 方法 | 模态 | Vehicle | Pedestrian | Cyclist | Mean（计算） |
|---|---|---:|---:|---:|---:|
| PointPillars | L | 68.80 | 38.16 | 65.24 | 57.40 |
| SECOND | L | 71.31 | 39.07 | 68.27 | 59.55 |
| CenterPoint | L | 72.19 | 50.59 | 75.26 | 66.01 |
| PV-RCNN | L | 79.38 | 58.83 | 78.01 | 72.07 |
| SQDNet | L | 79.65 | 58.79 | 79.46 | 72.63 |
| Fade3D | L | 70.64 | 51.88 | 69.93 | 64.15 |
| SMOKE | C | 8.61 | 0.29 | 0.37 | 3.09 |
| BEVDepth | C | 15.47 | 8.51 | 9.46 | 11.15 |
| BEVHeight | C | 15.32 | 8.48 | 7.35 | 10.38 |
| BEVHeight++ | C | 15.53 | 9.36 | 9.91 | 11.60 |
| RDIoU | R | 29.03 | 9.97 | 10.81 | 16.60 |
| RPFA-Net | R | 30.44 | 10.37 | 11.98 | 17.60 |

共 6 种 LiDAR、4 种相机、2 种雷达方法。SQDNet 是这张表中上述三类均值最高的方法，不能因此称为截至今日整个数据集的已确认 SOTA。

原表每格的斜杠表示严格/宽松两种 IoU，**不是 3D/BEV**。本轮没有从这张表得到公开 BEV 排名。

## 2. 官方还有融合实验，需补充此前“主要为单模态”的说明

同一论文 §5.2 与 Table 6 在车端恶劣天气子集上报告 M2-Fusion（LiDAR + 4D Radar），与 LiDAR-only、Radar-only 对照。这是融合实验，但不是 Table 4 完整车端划分的同口径结果。

M2-Fusion 的 Moderate Vehicle/Pedestrian/Cyclist 分别为 50.18/20.53/28.24，采用较宽松 IoU 0.5/0.25/0.25。这些值不能与上表的严格 IoU 或本地全量验证结果比较。原文 Table 6 的名称按表保留；本轮未进一步确认它对应的独立方法版本或可直接运行的官方车端配置。

因此，应表述为“官方完整车端主表以单模态方法为主，另有恶劣天气子集融合实验”，不能说该数据集没有公开融合方法。

## 3. 核实到的新增直接相关方法

**PhD-DETR: Physics-guided depth-aware transformer for monocular 3D object detection under adverse weather conditions**，Applied Soft Computing，出版商页面显示 2026-07-31 online，文章号 116147，Journal Pre-proof。

出版商摘要明确列出 KITTI、KITTI-C、V2X-Radar-V，因而可以确认它在车端数据上实验。它属于单目三维检测，使用物理先验引导特征融合、注意力与训练约束。[出版商原始页面](https://www.sciencedirect.com/science/article/pii/S1568494626015954)，[DOI](https://doi.org/10.1016/j.asoc.2026.116147)。

检索可读取摘要与部分正文索引，但本轮未取得其完整 V2X-Radar-V 数值表和划分细节；不能填入猜测的 AP，也不能因其使用单目输入便断言性能低于 ObjDec。它是后续需要补齐全文表格的明确线索。

## 4. 新论文存在，但有些不属于当前任务

| 工作 | 公开状态 | 任务核查 | 对当前表格的用途 |
|---|---|---|---|
| HRCP：Hybrid Robust Collaborative Perception with LiDAR-4D Radar Fusion under Adverse Weather Conditions | CVPR 2026 | 明确在 V2X-Radar-C 与 V2X-R 上做协同感知 | 可用于相关工作，不直接加入 V 端三类 AP 排名 |
| RC-GeoCP：Geometric Consensus for 4D Radar-Camera Collaborative Perception | 2026 arXiv；v4 于9月5日更新 | 多智能体雷达-相机协同感知，报告 BEV AP，包含 V2X-Radar 协同设置 | 输入、协同设定及指标不同，不直接比较本地 V 端 Mean 3D AP |
| LiDAR-Free 3D Auto-Labeling via Radar–Visual Spatio-Temporal Consistency | 公开期刊文章 | 下游实验使用 V2X-Radar-I 路侧数据 | 不算车端新方法；表中的其他检测器也不能据此算入 V 端清单 |

原始来源：[HRCP 的 CVPR 2026 论文](https://openaccess.thecvf.com/content/CVPR2026/papers/Yang_Hybrid_Robust_Collaborative_Perception_with_LiDAR-4D_Radar_Fusion_under_Adverse_CVPR_2026_paper.pdf)、[RC-GeoCP v4 全文](https://arxiv.org/html/2603.00654v4)、[LiDAR-Free Auto-Labeling 全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC13210705/)。

本轮未找到能够核实、并与当前本地设置直接对应的新增 C+L+R 完整车端排行榜。这个结论仅描述检索结果，不等于证明不存在其他方法，也不构成“首个三模态方法”的证据。

## 5. 与我们当前结果的关系

本地数据依据：[第45轮结果核查](objdec_grid016_epoch45_comparison_260920.md)。下表均为 0.16m、去重 val 1,487 帧、Moderate AP_R40、严格 IoU 0.7/0.5/0.5。

| 方法 | 训练节点 | Mean 3D | Mean BEV |
|---|---|---:|---:|
| ObjDec C+L+R | 第45轮 | 77.48 | 83.58 |
| Concat C+L+R | 第45轮 | 76.22 | 82.93 |
| L4DR L+R | 第45轮 | 72.00 | 79.23 |

这支持第45轮 ObjDec 相对 Concat 的 Mean 3D/BEV 提高 1.26/0.65 个百分点。不同模态的 L4DR 对照需要明确输入差异。

另需区分训练节点与最终模型：Concat 完成80轮后的最佳 checkpoint 是第75轮，去重 val Mean 3D 为 81.46、Mean BEV 为 85.75；ObjDec 尚在训练中，不能把第45轮同轮优势写成最终优势。ASF-style 与 ObjDec-LR 也尚未全部完成；第30轮 ASF-style 的 Mean 3D 71.69 高于 ObjDec CLR 同期69.92。

Concat 最终验证数据源：[final_best.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/final_best.json)，字段 `results.val_deduplicated`。这里没有用 test 分数与 val 混排。

## 6. 为什么目前不能直接声称公开基准 SOTA

完整证据在[公开协议可比性核查](objdec_v2x_public_protocol_comparability_260919.md)。主要问题包括：

- 原论文写 train/val/test=7000/1500/1500；当前本地下载包 train=8391，去重 val/test=1487/1486，尚未建立完整样本ID对应。
- 原论文单车范围写 x=[0,100]、y=[-100,100]m，本地为 x=[0,102.4)、y=[-51.2,51.2)。官方后来公开的一个相机配置也使用后一范围，因此需要锁定版本，不能简单认为某一方必然错误。
- 公开原表报告 validation，本地最终结果另有 test；需明确使用哪个集合。
- 本地评测器虽源自官方代码，但包含 ROI、投影难度过滤及交面积数值处理适配。相同 IoU 不足以证明目标集合和评测过程完全一致。

不同模态、骨干或训练轮数本身不必然使标准基准排名无效；核心是测试集合与评测协议可比，并如实披露各自资源。若要证明融合架构本身的收益，则还需要本地同底座对照。

即使未来本地数值超过所有已查到的公开数值，也不能自动跨越上述协议差异。检索尚未发现更高的方法，同样不能替代同协议证据。

## 7. 当前适合的论文表述及后续最小工作

当前可写：

> Experiments on V2X-Radar-V further evaluate the applicability of ObjDec through controlled comparisons under a unified local evaluation protocol.

中文：在 V2X-Radar-V 上，我们进一步通过统一本地评测协议下的受控对照，评估 ObjDec 架构在另一数据集上的适用性。

当前内部进展可写第45轮的 1.26/0.65 点提升，并明确属于中间验证节点。最终论文应等待各方法完成预定预算，以相同选模规则报告最终结果。

如果最终胜过本地所列对照，可写“best performance among the evaluated methods under our protocol”，同时说明方法适配与输入。现在不建议写“state-of-the-art on V2X-Radar-V”或“state-of-the-art on both datasets”。K-Radar 的 SOTA 主张需依据其自身完整对比证据独立判断。

后续优先级：完成现有本地训练和最终验证；补齐 PhD-DETR 全文数值与协议；若仍需公开基准 SOTA 主张，再确认数据版本和样本ID、ROI及过滤规则，并对接代表性强方法（例如 SQDNet/PV-RCNN）或对齐我们自己的评测。不能默认一次补评就能解决训练数据版本差异。

检索覆盖包含 V2X-Radar-V 的完整名称及别名、2025/2026、fusion、detection、AP，核查数据集论文、官方仓库、CVF、arXiv 与出版商页面；排除了仅引用数据集、做 C/I 子任务、以及名称相近但不同的数据集。公开索引不保证穷尽，故本文不提供绝对论文总数。
