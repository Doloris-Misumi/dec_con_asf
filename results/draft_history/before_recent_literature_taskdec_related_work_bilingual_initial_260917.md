# TaskDec Related Work：结构安排与中英文初稿

日期：2026-09-17。与 [Introduction 初稿](taskdec_introduction_bilingual_initial_260917.md) 配套；以下中文、英文分别构成完整版本，不在论文中同时放入。链接在正式 LaTeX 稿中替换为文献引用。

## 一、建议结构

建议保留两个小节，每节两段，不单独增加“恶劣天气感知”小节。两条线分别回答：已有检测架构如何融合不同传感器，以及已有表征学习方法如何组织共同信息和特有信息。TaskDec 的定位落在二者的结合处。

| 正式小节 | 段落安排 | 代表工作 | 末段如何连接 TaskDec |
| --- | --- | --- | --- |
| **2.1 Multi-Sensor Fusion for 3D Object Detection**（多传感器融合三维目标检测） | 第 1 段：公共空间与注意力交互；第 2 段：LiDAR–4D radar 与三传感器融合，重点交代 K-Radar 上的近邻 | BEVFusion、TransFusion、CMT、RCBEVDet；3D-LRF、L4DR、WCBR、ASF | 在 ASF 的空间投影和局部交互基础上，进一步研究表征组成与目标相关性如何共同调节融合 |
| **2.2 Shared and Modality-Specific Representation Learning**（共享与模态特有表征学习） | 第 1 段：共享/私有思想及任务相关的 common/unique 学习；第 2 段：DecAlign 的分解与对齐，以及 TaskDec 的检测场景与计算联系 | DSN、MISA、FactorCL、DeCUR、DecAlign | 在对应 BEV patch 内施加目标区域约束，并让表征参与融合输入、查询与输出的控制 |

第二节使用 shared / modality-specific 作为统一术语；介绍 DeCUR 等具体方法时保留其 common / unique 用语。不把这些术语解释为已经证明的统计独立性。

当前英文正文约 380 词（不含标题和引用），最终占页以 ICLR 模板实际排版为准。这里有意不罗列单模态检测骨干、数据集规模和 AP 数字；骨干放实现细节，基准介绍与性能比较放实验部分。

## 二、中文正文

### 2.1 多传感器融合三维目标检测

多传感器融合检测通过空间对应和特征交互，将不同传感器的观测用于联合预测。在相机–LiDAR 融合中，BEVFusion 将两类特征汇聚到统一的鸟瞰图（BEV）空间；TransFusion 使用由 LiDAR 特征生成的查询与图像特征交互；CMT 则利用三维位置编码关联图像与点云 token，通过跨模态注意力完成检测。这些方法展示了公共空间和查询交互在融合中的不同作用。在相机–雷达融合中，RCBEVDet 结合雷达 BEV 编码与可变形跨注意力，实现两类特征的对齐和融合。[BEVFusion](https://arxiv.org/abs/2205.13542)、[TransFusion](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf)、[CMT](https://openaccess.thecvf.com/content/ICCV2023/papers/Yan_Cross_Modal_Transformer_Towards_Fast_and_Robust_3D_Object_Detection_ICCV_2023_paper.pdf)、[RCBEVDet](https://openaccess.thecvf.com/content/CVPR2024/html/Lin_RCBEVDet_Radar-camera_Fusion_in_Birds_Eye_View_for_3D_Object_CVPR_2024_paper.html)

与本文更接近的研究关注 LiDAR、四维雷达及相机的融合。3D-LRF 结合三维空间交互与天气条件门控；L4DR 采用前景感知去噪、多模态特征编码和多尺度门控融合；WCBR 根据环境条件调节 LiDAR、雷达及融合分支的贡献。ASF 进一步通过统一空间投影与对应 patch 内的跨传感器注意力，处理不同传感器组合。这些工作为条件自适应和局部融合提供了基础。TaskDec 沿用 ASF 的空间投影与局部交互机制，重点研究局部共享/特有表征及目标相关信息如何共同调节融合过程。[3D-LRF](https://openaccess.thecvf.com/content/CVPR2024/papers/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.pdf)、[L4DR](https://arxiv.org/abs/2408.03677)、[WCBR](https://arxiv.org/abs/2604.05405)、[ASF](https://arxiv.org/abs/2503.07029)

### 2.2 共享与模态特有表征学习

显式区分共同信息与特有信息，是多模态表征学习的一条重要思路。早期的 Domain Separation Networks 在域适应中区分共享与域特有表示；MISA 将模态不变与模态特有表示相结合，通过相似性、差异性及重建约束学习用于情感分析的融合表示。FactorCL 从任务相关信息出发，利用因子化对比学习同时保留模态间共享和模态独有的信息。DeCUR 则在多模态自监督学习中，通过跨模态与模态内相关性目标学习 common/unique 表示。这些研究表明，促进共同信息的一致性与保留有用差异可以作为相互配合的学习目标。[DSN](https://papers.nips.cc/paper_files/paper/2016/hash/45fbc6d3e05ebd93369ce542e8f2322d-Abstract.html)、[MISA](https://arxiv.org/abs/2005.03545)、[FactorCL](https://papers.neurips.cc/paper_files/paper/2023/hash/6818dcc65fdf3cbd4b05770fb957803e-Abstract-Conference.html)、[DeCUR](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/04236.pdf)

DecAlign 进一步为两类表示设计不同的对齐机制：通过原型引导的最优传输处理模态特有表示，利用分布匹配约束共同表示，并结合跨模态交互形成预测所需的融合表示。TaskDec 将共享/特有表征学习与密集三维检测中的局部目标相关性联系起来：在空间对应的 BEV patch 内学习两类表示，并在训练时利用目标区域约束组织其一致性与差异性。学习到的表示同时用于预测前景门控、模态贡献权重与目标上下文，进而调节融合输入、注意力查询和融合输出。这一设计将局部表征的学习目标与检测架构中的融合计算直接联系起来。[DecAlign](https://proceedings.iclr.cc/paper_files/paper/2026/file/f7f5f501282771c96bb3fedcc96bedfe-Paper-Conference.pdf)

## 三、English draft

### 2.1 Multi-Sensor Fusion for 3D Object Detection

Multi-sensor detectors combine observations through spatial correspondence and feature interaction. For camera–LiDAR fusion, BEVFusion brings sensor features into a unified bird's-eye-view (BEV) space, whereas TransFusion uses LiDAR-derived queries to interact with image features. CMT associates image and point-cloud tokens through 3D positional encoding and performs detection with cross-modal attention. These approaches illustrate different roles of common feature spaces and query-based interaction in fusion. For radar–camera detection, RCBEVDet combines radar BEV encoding with deformable cross-attention to align and fuse sensor features. [BEVFusion](https://arxiv.org/abs/2205.13542), [TransFusion](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf), [CMT](https://openaccess.thecvf.com/content/ICCV2023/papers/Yan_Cross_Modal_Transformer_Towards_Fast_and_Robust_3D_Object_Detection_ICCV_2023_paper.pdf), [RCBEVDet](https://openaccess.thecvf.com/content/CVPR2024/html/Lin_RCBEVDet_Radar-camera_Fusion_in_Birds_Eye_View_for_3D_Object_CVPR_2024_paper.html)

Closely related work investigates fusion involving LiDAR, 4D radar, and cameras. 3D-LRF combines three-dimensional spatial interaction with weather-conditioned gating. L4DR employs foreground-aware denoising, multimodal feature encoding, and multi-scale gated fusion, while WCBR adjusts the contributions of LiDAR, radar, and fused branches according to environmental conditions. ASF accommodates different sensor combinations through unified canonical projection and cross-sensor attention within corresponding patches. These studies provide foundations for condition-dependent adaptation and local fusion. Building on ASF's projection and local interaction mechanisms, TaskDec investigates how shared and modality-specific local representations, together with object-related information, can regulate fusion. [3D-LRF](https://openaccess.thecvf.com/content/CVPR2024/papers/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.pdf), [L4DR](https://arxiv.org/abs/2408.03677), [WCBR](https://arxiv.org/abs/2604.05405), [ASF](https://arxiv.org/abs/2503.07029)

### 2.2 Shared and Modality-Specific Representation Learning

Explicitly distinguishing common and specific information is an established approach to multimodal representation learning. Early work on Domain Separation Networks separates shared and domain-specific representations for domain adaptation. MISA combines modality-invariant and modality-specific representations using similarity, difference, and reconstruction constraints for multimodal affect analysis. FactorCL uses factorized contrastive learning to retain both shared and unique information relevant to downstream tasks. DeCUR learns common and unique representations through cross-modal and intra-modal correlation objectives in multimodal self-supervised learning. Together, these studies support learning cross-modal consistency while preserving useful differences. [DSN](https://papers.nips.cc/paper_files/paper/2016/hash/45fbc6d3e05ebd93369ce542e8f2322d-Abstract.html), [MISA](https://arxiv.org/abs/2005.03545), [FactorCL](https://papers.neurips.cc/paper_files/paper/2023/hash/6818dcc65fdf3cbd4b05770fb957803e-Abstract-Conference.html), [DeCUR](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/04236.pdf)

DecAlign further develops distinct alignment mechanisms for the two representations: prototype-guided optimal transport for modality-specific representations and distribution matching for common representations, followed by cross-modal interaction and fusion for prediction. TaskDec connects shared and modality-specific representation learning to local object relevance in dense 3D detection. It learns both representations within spatially corresponding BEV patches, using constraints within object regions to organize their consistency and differences during training. The learned representations also predict foreground gates, modality contribution weights, and object context, which regulate fusion inputs, attention queries, and fused outputs. This design directly connects the objectives of local representation learning to the fusion computations of the detection architecture. [DecAlign](https://proceedings.iclr.cc/paper_files/paper/2026/file/f7f5f501282771c96bb3fedcc96bedfe-Paper-Conference.pdf)

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

1. **不将 common/unique 分支本身写成首次提出。** FactorCL 也已明确联系任务相关信息；TaskDec 的具体定位是对应 BEV 区域、目标区域训练约束，以及表示到三处融合控制的计算联系。
2. **不把既有方法概括为“只做辅助损失”或“只做全局对齐”。** MISA 和 DecAlign 的表示会进入下游预测；DecAlign 还包含局部 token / 原型层面的交互，DeCUR 也考虑空间信息选择。
3. **明确 ASF 的继承关系。** 架构创新需要通过新增的表征组织和计算路径说明，不把已有 UCP、patch attention 或传感器组合训练改称原创。
4. **方法引用与结果表选项分开。** L4DR 是方法上直接相关的工作，应在 Related Work 中交代；某个新数据集上的对比是否进入主表，是实验设置和证据报告的问题。
5. **本文不单列天气小节。** 天气适应出现在近邻方法的介绍中；TaskDec 的主问题是局部信息组织和目标相关融合，正常场景同样存在。

若后续篇幅不足，先删 DSN 的历史引入，再合并 TransFusion/CMT 的介绍；尽量保留 ASF、3D-LRF、L4DR，以及 MISA、FactorCL、DeCUR、DecAlign 的方法关系。无需在 Related Work 中重复 Introduction 的贡献列表和数值结果。
