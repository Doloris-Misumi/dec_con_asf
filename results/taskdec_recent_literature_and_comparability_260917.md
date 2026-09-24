# TaskDec 2025–2026 年文献补充与结果可比性核查

核查日期：2026-09-17。用途：更新 Introduction / Related Work 的方法覆盖和年份，并回应新工作的性能是否可能影响现有叙述。仅整理公开论文和本地已归档结果，没有启动训练或推理。

## 1. 已完成的正文更新

- [Related Work 中英文稿](taskdec_related_work_bilingual_initial_260917.md)：新增 10 篇，原有 13 篇保留，共 **23 篇**，其中 **14 篇为 2025–2026 年发表或公开版本**。英文正文约 440 词，保持两节。
- [Introduction 中英文稿](taskdec_introduction_bilingual_initial_260917.md)：方法引用由 4 篇扩展为 **12 篇**，其中 9 篇来自 2025–2026 年。保留原有研究问题、方法和实验结果。
- [新增文献 BibTeX](taskdec_recent_references_2025_2026_260917.bib)：仅收录本轮实际加入正文的 10 篇。正式发表与预印本区分登记；未编造 DOI、页码或未确认的会议。
- 修改前版本保存在 [Related Work 备份](draft_history/before_recent_literature_taskdec_related_work_bilingual_initial_260917.md) 和 [Introduction 备份](draft_history/before_recent_literature_taskdec_introduction_bilingual_initial_260917.md)。

文献按方法相关性选取。不同任务的分数不用于高低筛选；同数据集结果也先登记协议。本文没有建立“所有新方法均已被 TaskDec 同协议击败”的结论。

## 2. 本轮纳入的 10 篇

下表链接均为论文、正式论文集或作者页面。

| 工作及原始来源 | 年份 / 发表状态 | 与本文相关的内容 | 实验关系及使用位置 |
| --- | --- | --- | --- |
| [DLRFusion: Doppler-Aware LiDAR-RADAR Fusion for Weather-Robust 3D Detection](https://openaccess.thecvf.com/content/ICCV2025/html/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.html) | ICCV 2025，CVF 确认 | Doppler、雷达功率、LiDAR 分路编码与迭代交互 | K-Radar；引言 §2、Related Work §2.1 |
| [MoME: Resilient Sensor Fusion under Adverse Sensor Failures via Multi-Modal Expert Fusion](https://arxiv.org/abs/2503.19776) | CVPR 2025，作者 arXiv 标明接收 | 相机 / LiDAR / 联合专家及按查询路由 | nuScenes-R 传感器失效设置；引言背景、§2.1 |
| [RobuRCDet: Enhancing Robustness of Radar-Camera Fusion in Bird's Eye View for 3D Object Detection](https://proceedings.iclr.cc/paper_files/paper/2025/hash/21dabaacda3edba8bb281da45d7cbc17-Abstract-Conference.html) | ICLR 2025，正式论文集确认 | 雷达高斯扩展、相机置信度引导融合 | 原论文 nuScenes；引言背景、§2.1 |
| [CCF: Complementary Collaborative Fusion for Domain Generalized Multi-Modal 3D Object Detection](https://arxiv.org/abs/2603.23276) | CVPR 2026，作者 arXiv 标明接收 | 独立查询监督、几何深度先验、互补遮蔽 | nuScenes 跨域设置；§2.1。其 query decoupling 不等同于 common/unique 分支 |
| [SRF: Stereo-Radar Fusion for 3D Object Detection in Adverse Weather Conditions](https://ave.kaist.ac.kr/2026/02/12/srf-stereo-radar-fusion-for-3d-object-detection-in-adverse-weather-conditions/) | IV 2026，作者实验室当前页面确认 | 双目三维体与雷达多尺度三维体融合 | K-Radar v1/v2；§2.1。使用双目且不含 LiDAR |
| [RAF: Reliability-Aware Fusion of Camera, LiDAR, and 4D RADAR for Robust 3D Object Detection in Adverse Weather](https://arxiv.org/abs/2607.04587) | 2026；作者 arXiv 注明 ECCV 2026 | 显式监督相机可靠性，接入冻结的 LiDAR–radar 骨干 | K-Radar / VoD；引言 §2、§2.1。此次阅读的是 arXiv v1，不冒称核查了最终会议版 |
| [Plug-and-play Feature Causality Decomposition for Multimodal Representation Learning](https://proceedings.nips.cc/paper_files/paper/2025/hash/55123f38c9f4acf417335cff41be6e27-Abstract-Conference.html) | NeurIPS 2025，正式论文集确认 | 在模态特有部分进一步区分有用独有信息与冗余 | 通用多模态表征学习；引言动机、§2.2。正文写 Liu 等，未自行创造缩写 |
| [MultiLoReFT: Decoupling Shared and Modality-Specific Subspaces in Multimodal Learning via Low-Rank Representation Fine-Tuning](https://arxiv.org/abs/2607.16789) | arXiv 2026，7 月 18 日公开；未确认会议接收 | 预训练单模态模型之上的共享/特有低秩子空间 | 模拟与多模态表征任务；§2.2，不标成 ICLR 已发表 |
| [SPFD / Beyond Duality: A Hybrid Framework of Leveraging Shared and Private Features for RGB-Event Object Detection](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Beyond_Duality_A_Hybrid_Framework_of_Leveraging_Shared_and_Private_CVPR_2026_paper.html) | CVPR 2026，CVF 确认 | 频域共享/私有分解及编码器、解码器中的使用 | DSEC-Det / PKU-DAVIS-SOD 的 RGB–Event 检测；引言 §2、§2.2 |
| [Layer-Wise Modality Decomposition for Interpretable Multimodal Sensor Fusion](https://proceedings.neurips.cc/paper_files/paper/2025/hash/d3e0aaa57c0d639f32a520cda39aec6d-Abstract-Conference.html) | NeurIPS 2025，正式论文集确认 | 对已训练融合模型进行逐层模态贡献解释 | 含 camera–radar–LiDAR 设置；§2.2，明确为事后解释 |

保留的 MISA、FactorCL、DeCUR 等基础文献用于交代设计来源。新旧文献共同组织成“空间融合—模态贡献”和“共享/特有学习—近期的选择及使用”，不是单纯按年份排列。

## 3. 与现有 TaskDec 数字的关系

### 3.1 已核实的 K-Radar 原文主表

**本表是来源并列，不是统一评测排行榜。** 单位为 AP 百分数；“—”表示本轮读取的主表未列出该项。TaskDec 为本地 v1、Sedan、conf=0.3；新论文行使用各自公开设置。

| 来源 / 方法 | 模态 | BEV@0.3 | 3D@0.3 | BEV@0.5 | 3D@0.5 |
| --- | --- | ---: | ---: | ---: | ---: |
| TaskDec，本地归档 | C+L+R | 88.84 | 88.36 | 88.10 | 67.50 |
| DLRFusion，ICCV 2025 Tables 1–2 | L+R，含 Doppler | 82.9 | 74.8 | 73.2 | 45.7 |
| RAF on L4DR，arXiv v1 Table 1 | C+L+R | — | — | 82.0 | 57.4 |
| RAF on 3D-LRF，arXiv v1 Table 1 | C+L+R | — | — | 71.0 | 43.2 |

来源：[DLRFusion 原文 Tables 1–2](https://openaccess.thecvf.com/content/ICCV2025/papers/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.pdf)、[RAF §4 / Table 1](https://arxiv.org/html/2607.04587v1#S4)、[TaskDec 归档与协议说明](taskdec_full_paper_evidence_motivation_contributions_260917.md)。

核查结果与限制：

- DLRFusion 和 RAF 原文给出的驾驶走廊为 x=[0,72]、y=[−6.4,6.4]、z=[−2,6] m，并评测 Sedan。上述数值低于本地 TaskDec 对应显示值；尚未统一标签修订、置信度预过滤和 evaluator 细节，也未使用官方权重本地复评。
- DLRFusion 使用 Doppler，而当前 TaskDec v1 雷达输入不含 Doppler；传感器组合与训练配置也不同。不能将该行称为等输入、等训练预算比较。
- RAF 表中 3D-LRF 带有复现值标记；其 L4DR-RAF 默认主表值为 82.0 / 57.4。不能把它复现的其他模型行直接替换我们的官方结果行。其超参数消融存在不同结果，主表不按列挑选最高值。
- 因此可说“已查到的新工作公开结果没有在这些对应数值上超过我们”，但不能据此写“同协议全面领先全部 2026 年方法”，也不应直接把差值写进摘要。

### 3.2 SRF 的结果需单独理解

作者页面报告 K-Radar v1 / v2 的 3D mAP 为 **55.6 / 54.3**。本轮可访问的摘要没有充分说明对应 IoU 和类别汇总口径；加上它使用 stereo+radar，没有 LiDAR，因此不将这两个数塞入上面的 AP@0.3/@0.5 列，也不直接减去 TaskDec 或 Strong 的数值。它适合先作为相关方法引用。来源：[作者实验室 SRF 页面](https://ave.kaist.ac.kr/2026/02/12/srf-stereo-radar-fusion-for-3d-object-detection-in-adverse-weather-conditions/)。

### 3.3 其他新文献没有直接可用的 TaskDec 排名

- MoME、RobuRCDet、CCF 的原始评测主要属于 nuScenes 及相关扰动/跨域设置，与 K-Radar 的 IoU AP 不同。
- RAF 论文包含对 RobuRCDet 等方法的 K-Radar 迁移复现，但这些是 RAF 作者的实现结果，不是 RobuRCDet 原论文的官方 K-Radar 基准。
- SPFD 是 RGB–Event 检测，其 2D AP 不能与 TaskDec 的 3D AP 数字排序。
- Liu 等、MultiLoReFT 研究表征学习；LMD 研究贡献解释，均不构成一条与 TaskDec 同协议的 K-Radar 检测结果。

## 4. 对动机和贡献措辞的影响

1. **共享/特有信息与噪声不是新问题。** FactorCL、Liu 等和 DecAlign 已有直接研究；引言现已补上对应来源。
2. **解耦表示进入检测架构也已有先例。** SPFD 在编码与解码阶段使用共享/私有特征，因此不能写“此前解耦都只是辅助损失”或“首次将 shared/private 用于目标检测”。
3. **TaskDec 应明确自己的结构条件。** 对应的三传感器 BEV patch、目标区域约束，以及表示到 token / query / output 控制的连接，是本文应论证的具体设计。SPFD 使用频域分离的 RGB–Event 特征，RAF 主要处理相机观测可靠性，LMD 是已训练模型的事后分析；这些区别不需要以统一性能排名来成立。
4. **不沿用他人较强的语义承诺。** 引用因果分解不代表 TaskDec 具有因果保证；引用可靠性监督不代表当前模态权重已经校准为可靠性概率。

## 5. 另外检索到但未扩写进本轮正文的工作

[CIML: Towards Comprehensive Information-theoretic Multi-view Learning](https://arxiv.org/abs/2509.02084)（2025 年公开版本）也研究任务相关的共同/特有信息及信息瓶颈，可作为 FactorCL 附近的后续备选。本轮已优先加入更贴近检测的 SPFD、LMD，以及有正式 NeurIPS 2025 论文集的 Liu 等工作，控制篇幅。本轮未依据二手数据库将 CIML 的后续期刊信息写入 BibTeX。

本轮检索不是完整文献穷尽；正式投稿前应再次检查与主表直接相关的新增结果和协议。
