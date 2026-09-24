# TaskDec Related Work：结构安排与中英文初稿（近期文献补充版）

日期：2026-09-17。已补充 2025–2026 年相关文献，与 [Introduction 初稿](taskdec_introduction_bilingual_initial_260917.md) 配套。修改前版本保存在 [draft_history](draft_history/before_recent_literature_taskdec_related_work_bilingual_initial_260917.md)。中文、英文分别构成完整版本；链接在正式稿中替换为文献引用。

## 一、建议结构

保留两个小节，每节三段。第一节介绍空间融合、近期的模态贡献控制、K-Radar 直接近邻；第二节介绍共享/特有学习基础、近期分解与使用方式，以及 TaskDec 的具体联系。不单独增加恶劣天气小节。

| 正式小节 | 段落安排 | 收束点 |
| --- | --- | --- |
| **2.1 Multi-Sensor Fusion for 3D Object Detection** | 公共空间/查询交互 → 输入质量与模态贡献 → LiDAR–radar 和三传感器融合 | 在 ASF 的局部融合基础上联系表征组织与目标相关控制 |
| **2.2 Shared and Modality-Specific Representation Learning** | 基础思想 → 近期的筛选/对齐/检测使用及事后分析 → TaskDec | 对应 BEV 区域、目标区域训练约束、输入/query/output 控制 |

当前英文正文约 440 词，23 篇方法文献，其中 14 篇来自 2025–2026 年。通过合并方法介绍控制篇幅；正式占页以模板排版为准。shared / modality-specific 是本文统一术语，介绍他人方法时保留其 common / unique / private 用语。

## 二、中文正文

### 2.1 多传感器融合三维目标检测

多传感器融合检测通过空间对应和特征交互，将不同传感器的观测用于联合预测。[BEVFusion](https://arxiv.org/abs/2205.13542) 将相机和 LiDAR 特征汇聚到统一的鸟瞰图（BEV）空间；[TransFusion](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf) 与 [CMT](https://openaccess.thecvf.com/content/ICCV2023/papers/Yan_Cross_Modal_Transformer_Towards_Fast_and_Robust_3D_Object_Detection_ICCV_2023_paper.pdf) 则分别通过 LiDAR 引导的查询和三维位置编码建立跨模态交互。对于相机–雷达融合，[RCBEVDet](https://openaccess.thecvf.com/content/CVPR2024/html/Lin_RCBEVDet_Radar-camera_Fusion_in_Birds_Eye_View_for_3D_Object_CVPR_2024_paper.html) 结合雷达 BEV 编码与可变形跨注意力完成特征对齐。这些设计为跨传感器特征的对应与整合提供了不同途径。

近期研究进一步关注模态贡献与输入质量变化。[MoME（2025）](https://arxiv.org/abs/2503.19776) 为相机、LiDAR 及联合特征设置专家解码器，并根据查询选择专家；[CCF（2026）](https://arxiv.org/abs/2603.23276) 结合独立查询监督、几何先验和互补遮蔽，缓解跨域检测中的模态失衡。[RobuRCDet（2025）](https://proceedings.iclr.cc/paper_files/paper/2025/hash/21dabaacda3edba8bb281da45d7cbc17-Abstract-Conference.html) 则利用雷达高斯扩展和图像置信度引导的融合，处理相机与雷达受到不同扰动的情况。

在 K-Radar 相关研究中，[3D-LRF](https://openaccess.thecvf.com/content/CVPR2024/papers/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.pdf) 与 [L4DR](https://arxiv.org/abs/2408.03677) 分别研究三维空间交互、前景去噪及门控融合；[DLRFusion（2025）](https://openaccess.thecvf.com/content/ICCV2025/html/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.html) 将 Doppler、雷达功率和 LiDAR 特征分开编码并迭代交互。[WCBR](https://arxiv.org/abs/2604.05405) 根据环境条件调节分支贡献，[SRF（2026）](https://ave.kaist.ac.kr/2026/02/12/srf-stereo-radar-fusion-for-3d-object-detection-in-adverse-weather-conditions/) 在三维体素空间融合双目图像与雷达。对于三传感器融合，[ASF](https://arxiv.org/abs/2503.07029) 采用统一空间投影与对应 patch 内的跨传感器注意力，[RAF（2026）](https://arxiv.org/abs/2607.04587) 则利用显式监督的图像可靠性图调制相机特征。TaskDec 沿用 ASF 的投影和局部交互机制，进一步将共享/特有表征学习与目标相关融合控制联系起来。

### 2.2 共享与模态特有表征学习

共享与特有信息的显式组织已有研究基础。[Domain Separation Networks](https://papers.nips.cc/paper_files/paper/2016/hash/45fbc6d3e05ebd93369ce542e8f2322d-Abstract.html) 在域适应中区分共享与域特有表示；[MISA](https://arxiv.org/abs/2005.03545) 通过相似性、差异性与重建约束，学习用于情感分析的模态不变及模态特有表示。[FactorCL](https://papers.neurips.cc/paper_files/paper/2023/hash/6818dcc65fdf3cbd4b05770fb957803e-Abstract-Conference.html) 关注同时保留任务相关的共享与独有信息，[DeCUR](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/04236.pdf) 则通过跨模态和模态内相关性目标实现 common/unique 自监督学习。这些工作支持在学习一致性的同时保留有用差异。

近期工作进一步研究两类信息的筛选、对齐与使用。[Liu 等（2025）](https://proceedings.nips.cc/paper_files/paper/2025/hash/55123f38c9f4acf417335cff41be6e27-Abstract-Conference.html) 从因果建模角度将模态特有部分进一步区分为独有与冗余信息；[MultiLoReFT（2026）](https://arxiv.org/abs/2607.16789) 通过低秩表示微调学习共享及模态特有子空间。[DecAlign（2026）](https://proceedings.iclr.cc/paper_files/paper/2026/file/f7f5f501282771c96bb3fedcc96bedfe-Paper-Conference.pdf) 分别利用原型引导的最优传输和分布匹配处理特有与共同表示。面向检测，[SPFD（2026）](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Beyond_Duality_A_Hybrid_Framework_of_Leveraging_Shared_and_Private_CVPR_2026_paper.html) 基于频域一致性分离 RGB–Event 的共享/私有特征，并在编码器和解码器中分别使用；[LMD（2025）](https://proceedings.neurips.cc/paper_files/paper/2025/hash/d3e0aaa57c0d639f32a520cda39aec6d-Abstract-Conference.html) 则对已训练的融合网络进行事后模态贡献分解。

TaskDec 关注相机、LiDAR 与四维雷达在对应 BEV 区域中的表征学习和融合计算。在训练时，目标区域约束用于组织共享与特有表示的一致性和差异性；在前向计算中，这些表示参与前景门控、模态贡献权重和目标上下文的预测，进而调节融合输入、注意力查询及融合输出。其具体设计在于将局部目标监督与三处融合控制相结合。

## 三、English draft

### 2.1 Multi-Sensor Fusion for 3D Object Detection

Multi-sensor detectors combine observations through spatial correspondence and feature interaction. [BEVFusion](https://arxiv.org/abs/2205.13542) brings camera and LiDAR features into a unified bird's-eye-view (BEV) space, while [TransFusion](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf) and [CMT](https://openaccess.thecvf.com/content/ICCV2023/papers/Yan_Cross_Modal_Transformer_Towards_Fast_and_Robust_3D_Object_Detection_ICCV_2023_paper.pdf) establish cross-modal interactions through LiDAR-guided queries and 3D positional encoding, respectively. For radar–camera fusion, [RCBEVDet](https://openaccess.thecvf.com/content/CVPR2024/html/Lin_RCBEVDet_Radar-camera_Fusion_in_Birds_Eye_View_for_3D_Object_CVPR_2024_paper.html) combines radar BEV encoding with deformable cross-attention for feature alignment. These designs offer different ways to establish correspondence and integrate sensor features.

Recent studies further address modality contributions and varying input quality. [MoME (2025)](https://arxiv.org/abs/2503.19776) routes queries among camera, LiDAR, and joint expert decoders. [CCF (2026)](https://arxiv.org/abs/2603.23276) combines separate query supervision, geometric priors, and complementary masking to address modality imbalance in cross-domain detection. [RobuRCDet (2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/21dabaacda3edba8bb281da45d7cbc17-Abstract-Conference.html) uses Gaussian expansion of radar points and camera-confidence-guided fusion to accommodate different sensor disturbances.

On K-Radar, [3D-LRF](https://openaccess.thecvf.com/content/CVPR2024/papers/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.pdf) and [L4DR](https://arxiv.org/abs/2408.03677) investigate spatial interaction, foreground denoising, and gated fusion. [DLRFusion (2025)](https://openaccess.thecvf.com/content/ICCV2025/html/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.html) separately encodes Doppler, radar power, and LiDAR features for iterative interaction. [WCBR](https://arxiv.org/abs/2604.05405) adjusts branch contributions according to environmental conditions, while [SRF (2026)](https://ave.kaist.ac.kr/2026/02/12/srf-stereo-radar-fusion-for-3d-object-detection-in-adverse-weather-conditions/) fuses stereo images and radar in 3D voxel space. For three-sensor fusion, [ASF](https://arxiv.org/abs/2503.07029) uses unified canonical projection and cross-sensor attention within corresponding patches, whereas [RAF (2026)](https://arxiv.org/abs/2607.04587) modulates camera features using explicitly supervised image reliability maps. Building on ASF's projection and local interaction mechanisms, TaskDec connects shared and modality-specific representation learning with object-related fusion control.

### 2.2 Shared and Modality-Specific Representation Learning

Explicitly organizing shared and specific information has an established foundation. [Domain Separation Networks](https://papers.nips.cc/paper_files/paper/2016/hash/45fbc6d3e05ebd93369ce542e8f2322d-Abstract.html) distinguish shared and domain-specific representations for domain adaptation. [MISA](https://arxiv.org/abs/2005.03545) learns modality-invariant and modality-specific representations through similarity, difference, and reconstruction constraints for affect analysis. [FactorCL](https://papers.neurips.cc/paper_files/paper/2023/hash/6818dcc65fdf3cbd4b05770fb957803e-Abstract-Conference.html) retains task-relevant shared and unique information, while [DeCUR](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/04236.pdf) learns common and unique representations through cross-modal and intra-modal correlation objectives. These studies support learning consistency while preserving useful differences.

Recent work further explores how these representations are selected, aligned, and used. [Liu et al. (2025)](https://proceedings.nips.cc/paper_files/paper/2025/hash/55123f38c9f4acf417335cff41be6e27-Abstract-Conference.html) use a causal formulation to further separate modality-specific information into unique and redundant components. [MultiLoReFT (2026)](https://arxiv.org/abs/2607.16789) learns shared and modality-specific subspaces through low-rank representation fine-tuning. [DecAlign (2026)](https://proceedings.iclr.cc/paper_files/paper/2026/file/f7f5f501282771c96bb3fedcc96bedfe-Paper-Conference.pdf) uses prototype-guided optimal transport and distribution matching for modality-specific and common representations, respectively. For detection, [SPFD (2026)](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Beyond_Duality_A_Hybrid_Framework_of_Leveraging_Shared_and_Private_CVPR_2026_paper.html) separates RGB–event shared and private features through frequency-domain coherence and uses them in both its encoder and decoder. [LMD (2025)](https://proceedings.neurips.cc/paper_files/paper/2025/hash/d3e0aaa57c0d639f32a520cda39aec6d-Abstract-Conference.html) instead provides post-hoc decomposition of modality contributions in pretrained fusion networks.

TaskDec studies representation learning and fusion computation within corresponding BEV regions of camera, LiDAR, and 4D radar features. During training, constraints within object regions organize consistency and differences between shared and modality-specific representations. In the forward computation, these representations help predict foreground gates, modality contribution weights, and object context, which regulate fusion inputs, attention queries, and fused outputs. The design connects local object supervision to control at these three fusion stages.

## 四、参考组织方式与引用核查（不进入正文）

### 4.1 借鉴什么，不照搬什么

- **ASF §2** 按 deeply coupled fusion 和 sensor-wise cross-attention fusion 展开。本文借鉴其“融合方式—具体架构—近邻关系”的顺序，但不沿用其二分法作为一级标题，因为 TaskDec 的另一条主线是表征学习。也不把拼接、空间投影或注意力方法笼统写成无法适应环境变化。
- **L4DR Related Work** 分别讨论 LiDAR 检测、恶劣天气检测、LiDAR–radar 融合。本文保留最后一条中的直接相关方法，把天气适应作为部分方法的特点，不扩展成全文主问题。
- **DecAlign §2 与 Appendix A** 按 multimodal representation learning 和 cross-modal alignment 组织。本文借鉴“共享/特有学习—不同对齐机制”的联系，但不展开与 TaskDec 关系较远的模态翻译和蒸馏分支。
- 逐方法描述以各论文原文核查。特别是 MISA 的相似性项采用 central moment discrepancy，不能因其他 Related Work 的概括而写成使用 InfoNCE 对比损失；3D-LRF 已考虑天气条件门控，不能写为不考虑恶劣天气。

对应原文：[ASF §2](https://arxiv.org/html/2503.07029v2#S2)、[L4DR](https://arxiv.org/html/2408.03677v6)、[DecAlign 全文](https://proceedings.iclr.cc/paper_files/paper/2026/file/f7f5f501282771c96bb3fedcc96bedfe-Paper-Conference.pdf)、[MISA 原文](https://arxiv.org/pdf/2005.03545v1)。

### 4.2 文献在本文中的作用

| 文献 | 出版信息 | 引用目的与范围 |
| --- | --- | --- |
| BEVFusion: Multi-Task Multi-Sensor Fusion with Unified Bird's-Eye View Representation | ICRA 2023 | Liu 等的统一 BEV 版本；不要和同名的另一篇 BEVFusion 混淆 |
| TransFusion: Robust LiDAR-Camera Fusion for 3D Object Detection with Transformers | CVPR 2022 | 由 LiDAR 查询引导图像特征交互 |
| Cross Modal Transformer: Towards Fast and Robust 3D Object Detection | ICCV 2023 | 图像/点云 token 的位置关联与跨模态交互 |
| RCBEVDet: Radar-camera Fusion in Bird's Eye View for 3D Object Detection | CVPR 2024 | 补齐相机–雷达融合路线；不是 K-Radar 实验对照 |
| Towards Robust 3D Object Detection with LiDAR and 4D Radar Fusion in Various Weather Conditions | CVPR 2024 | 3D-LRF；三维交互及天气条件适应 |
| L4DR: LiDAR-4DRadar Fusion for Weather-Robust 3D Object Detection | AAAI 2025 | 前景去噪、多模态编码、多尺度门控的直接近邻 |
| Weather-Conditioned Branch Routing for Robust LiDAR-Radar 3D Object Detection | arXiv:2604.05405，2026 | 本稿仅概括公开 v1 的条件路由；不混入尚未公开的 ICRA 修订细节 |
| Availability-aware Sensor Fusion via Unified Canonical Space | NeurIPS 2025 | 明确 TaskDec 的空间投影和 patch 交互来源 |
| Domain Separation Networks | NeurIPS 2016 | 共享/私有表示的相关早期思路；其对象是域，不直接等同于模态 |
| MISA: Modality-Invariant and -Specific Representations for Multimodal Sentiment Analysis | ACM MM 2020 | 共享/特有学习约束及融合预测的直接概念近邻 |
| Factorized Contrastive Learning: Going Beyond Multi-view Redundancy | NeurIPS 2023 | 已明确研究任务相关的 shared/unique 信息，需要在新颖性定位中交代 |
| Decoupling Common and Unique Representations for Multimodal Self-supervised Learning | ECCV 2024 | DeCUR；通过模态内与跨模态相关性学习 common/unique；引用正式 ECCV 版本 |
| DecAlign: Hierarchical Cross-Modal Alignment for Decoupled Multimodal Representation Learning | ICLR 2026 | 分别处理共同与特有表示的对齐，并用于预测 |

### 4.3 后续修改时保留的区别

1. **不将 common/unique 分支本身写成首次提出。** FactorCL 也已明确联系任务相关信息，SPFD 已在检测架构中使用共享/私有表示；TaskDec 的具体定位是对应 BEV 区域、目标区域训练约束，以及表示到三处融合控制的计算联系。
2. **不把既有方法概括为“只做辅助损失”或“只做全局对齐”。** MISA 和 DecAlign 的表示会进入下游预测；DecAlign 还包含局部 token / 原型层面的交互，DeCUR 也考虑空间信息选择。
3. **明确 ASF 的继承关系。** 架构创新需要通过新增的表征组织和计算路径说明，不把已有 UCP、patch attention 或传感器组合训练改称原创。
4. **方法引用与结果表选项分开。** L4DR 是方法上直接相关的工作，应在 Related Work 中交代；某个新数据集上的对比是否进入主表，是实验设置和证据报告的问题。
5. **本文不单列天气小节。** 天气适应出现在近邻方法的介绍中；TaskDec 的主问题是局部信息组织和目标相关融合，正常场景同样存在。

若后续篇幅不足，先删 DSN 的历史引入，再合并 TransFusion/CMT 的介绍；保留 ASF、L4DR、DLRFusion、RAF，以及 FactorCL、DecAlign、SPFD 的直接关系；其余新文献可用合并句保留引用。无需在 Related Work 中重复 Introduction 的贡献列表和数值结果。


### 4.4 本轮补充（2025–2026）

本轮新增 10 篇进入正文，原有 13 篇保留，共 23 篇，其中 14 篇为 2025–2026 年发表或公开版本。新增条目的年份、原始来源、性能与协议核对详见 [近期文献核查表](taskdec_recent_literature_and_comparability_260917.md)。在排版时统一改成 author–year 引用，正文中的年份无需重复。

| 新增文献 | 年份与状态 | 本文使用位置 |
| --- | --- | --- |
| DLRFusion | ICCV 2025 | §2.1：Doppler / power / LiDAR 的显式分路交互 |
| MoME | CVPR 2025 | §2.1：按查询选择模态专家 |
| RobuRCDet | ICLR 2025 | §2.1：输入扰动与图像置信度引导融合 |
| CCF | CVPR 2026 | §2.1：跨域模态失衡和独立查询监督 |
| SRF | IV 2026，作者实验室页面确认 | §2.1：K-Radar 上的双目–雷达三维体融合 |
| RAF | 2026，作者 arXiv 标注 ECCV 2026 | §2.1：三模态融合中的图像可靠性监督 |
| Plug-and-play Feature Causality Decomposition | NeurIPS 2025 | §2.2：区分有用特有信息与冗余；不将 TaskDec 称为因果方法 |
| MultiLoReFT | arXiv 2026；本轮未确认正式会议接收 | §2.2：共享/特有子空间与低秩微调 |
| SPFD / Beyond Duality | CVPR 2026 | §2.2：shared/private 表示参与检测编码与解码 |
| LMD | NeurIPS 2025 | §2.2：自动驾驶融合网络的事后模态贡献分析 |

相关工作中的方法介绍不构成同协议性能排名。新文献中公开的 K-Radar 数字与本地 TaskDec 数字分别保留来源；没有因性能高低删除相关方法。SPFD 和特征因果分解的存在进一步要求把创新描述限定到 TaskDec 的具体学习约束与计算连接。
