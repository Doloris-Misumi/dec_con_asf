# ObjDec Introduction：中英文初稿

日期：2026-09-17。依据当前实现与已归档结果撰写；本轮补充 2025–2026 年相关文献，保留原有动机、架构与结果叙述。修改前版本见 [备份](draft_history/before_recent_literature_taskdec_introduction_bilingual_initial_260917.md)。

命名更新（2026-09-19）：方法名统一为 **ObjDec**，全称 **Object-Guided Representation Decoupling（目标引导的表征解耦）**。

论文标题（已确定）：**Decoupling to Fuse: Learning Shared and Modality-Specific Representations for Multi-Sensor 3D Object Detection**

逻辑：多传感器检测 → 已有空间交互与自适应融合 → 局部信息组织和目标相关性 → ObjDec 架构 → 实验证据 → 三点贡献。中文与英文按段对应。正文中的链接可在 LaTeX 稿中替换为正式引用。

## 中文

准确的三维目标检测是自动驾驶环境感知的重要基础。相机、LiDAR 与四维雷达从不同角度观测场景，为检测提供外观、几何和雷达回波等信息。由于成像机制和空间采样方式不同，这些观测既包含对同一目标的共同描述，也保留各自特有的线索。如何将它们转化为有利于检测的联合表征，是多传感器融合的核心问题。这不仅需要建立空间对应关系，还需要确定不同信息应当如何参与融合。[BEVFusion](https://arxiv.org/abs/2205.13542)、[MoME（2025）](https://arxiv.org/abs/2503.19776)、[RobuRCDet（2025）](https://proceedings.iclr.cc/paper_files/paper/2025/hash/21dabaacda3edba8bb281da45d7cbc17-Abstract-Conference.html)

已有研究从空间交互、特征对齐和自适应加权等方面推动了融合检测的发展。三维空间交互、前景去噪及 Doppler 引导的多路交互，为利用不同传感器观测提供了有效基础。[3D-LRF](https://openaccess.thecvf.com/content/CVPR2024/papers/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.pdf)、[L4DR](https://arxiv.org/abs/2408.03677)、[DLRFusion（2025）](https://openaccess.thecvf.com/content/ICCV2025/html/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.html) 近期的三传感器融合进一步研究统一局部空间中的跨传感器注意力，以及显式监督的图像可靠性建模。[ASF（2025）](https://arxiv.org/abs/2503.07029)、[RAF（2026）](https://arxiv.org/abs/2607.04587) 与此同时，解耦表征的对齐和使用也持续发展：DecAlign 为共同与特有表示设计不同的对齐机制，SPFD 则将共享/私有特征组织引入 RGB–Event 检测架构。[DecAlign（2026）](https://proceedings.iclr.cc/paper_files/paper/2026/file/f7f5f501282771c96bb3fedcc96bedfe-Paper-Conference.pdf)、[SPFD（2026）](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Beyond_Duality_A_Hybrid_Framework_of_Leveraging_Shared_and_Private_CVPR_2026_paper.html) 本文在这些研究基础上关注密集三维检测中的进一步问题：如何将局部表征组织与目标相关性联系起来，并使二者共同影响融合过程。

我们关注空间对齐之后的信息组织问题。在同一个局部区域中，跨模态共同响应可能来自目标，也可能来自背景；模态之间的差异则可能反映有用的观测特性，也可能包含噪声。因此，跨模态一致性并不自动等同于目标相关性，而模态差异也不应被一概消除。[FactorCL](https://papers.neurips.cc/paper_files/paper/2023/hash/6818dcc65fdf3cbd4b05770fb957803e-Abstract-Conference.html)、[特征因果分解（Liu 等，2025）](https://proceedings.nips.cc/paper_files/paper/2025/hash/55123f38c9f4acf417335cff41be6e27-Abstract-Conference.html) 对于检测任务，需要同时考虑哪些信息可以共享、哪些差异值得保留，以及这些信息与局部目标的关系。由此，我们提出如下研究问题：**如何学习共享与模态特有表征，并依据目标相关信息引导二者参与局部融合？** 这一问题同样存在于正常驾驶场景中，光照变化、遮挡和恶劣天气则提供了考察其表现的不同条件。

为此，我们提出 **ObjDec**，一种学习共享与模态特有表征，并利用目标相关信息引导其融合的多传感器融合架构。在 ASF 的统一空间投影与局部跨传感器交互基础上，ObjDec 为各模态的对应 patch 构建共享与特有表征，并在训练时利用目标区域内的约束促进共享表示的一致性、保留特有表示之间的差异，以及限制同一模态两类表示的相似性。在此基础上，架构预测前景门控、模态贡献权重和目标上下文：前两者共同调节输入 token 的特征更新与缩放，目标上下文则通过门控残差调制注意力查询和融合输出。这样，表征学习与融合控制形成直接的计算联系，共同参与检测特征的构建。目标框仅用于训练监督，推理时的控制信号由输入特征预测，无需目标框或天气标签。

我们以 K-Radar 为主要实验平台评估 ObjDec。在 v1 的统一置信度过滤设置（conf=0.3）下，ObjDec 的 AP3D@0.3 和 APBEV@0.5 分别达到 **88.36** 和 **88.10**；相对官方 ASF 权重对应的评测结果，分别提高 **8.04** 和 **7.77** 个百分点，参数量增加约 **1.7%**。组件消融检验各项设计对检测性能的贡献，表征可视化与空间门控分析则描述模型学习到的局部表示和控制行为。此外，我们考察解耦控制变体在 K-Radar v2 扩大空间范围和类别设置下的表现，以及完整架构在 V2X-Radar-V 上的迁移结果，并分别报告模型变体、评测设置及适用边界。

本文的主要贡献如下：

1. **面向目标检测的局部表征学习。** 在空间对应的多传感器特征中显式组织共享与模态特有表示，并通过目标区域内的表征约束，将跨模态一致性与差异性学习联系到检测任务。
2. **表征驱动的目标引导融合架构。** 将解耦表示与前景门控、模态贡献控制和目标上下文相结合，联合调制融合输入、注意力查询及融合输出，使学习到的表示直接参与检测特征的构建。
3. **检测性能与机制的联合评估。** 通过 K-Radar 主结果、组件消融、表征与空间门控分析，以及扩展设置下的比较，评估该设计的收益、内部行为和适用范围。

## English

Accurate 3D object detection is essential for autonomous driving. Cameras, LiDAR, and 4D radar observe a scene through different sensing mechanisms, providing appearance, geometric, and radar-return information for detection. Their observations contain both common descriptions of the same objects and cues specific to each modality. A central challenge in multi-sensor fusion is to turn these observations into a joint representation that supports detection. This requires establishing spatial correspondence and determining how different information should contribute to fusion. [BEVFusion](https://arxiv.org/abs/2205.13542), [MoME (2025)](https://arxiv.org/abs/2503.19776), [RobuRCDet (2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/21dabaacda3edba8bb281da45d7cbc17-Abstract-Conference.html)

Recent work has advanced fusion-based detection through spatial interaction, feature alignment, and adaptive weighting. Three-dimensional interaction, foreground denoising, and Doppler-guided interaction provide effective foundations for exploiting sensor observations. [3D-LRF](https://openaccess.thecvf.com/content/CVPR2024/papers/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.pdf), [L4DR](https://arxiv.org/abs/2408.03677), [DLRFusion (2025)](https://openaccess.thecvf.com/content/ICCV2025/html/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.html) Recent three-sensor architectures further investigate cross-sensor attention in a unified local space and explicitly supervised image reliability. [ASF (2025)](https://arxiv.org/abs/2503.07029), [RAF (2026)](https://arxiv.org/abs/2607.04587) The alignment and use of decoupled representations have also progressed: DecAlign develops distinct alignment mechanisms for common and modality-specific representations, while SPFD organizes shared and private features within an RGB–event detection architecture. [DecAlign (2026)](https://proceedings.iclr.cc/paper_files/paper/2026/file/f7f5f501282771c96bb3fedcc96bedfe-Paper-Conference.pdf), [SPFD (2026)](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Beyond_Duality_A_Hybrid_Framework_of_Leveraging_Shared_and_Private_CVPR_2026_paper.html) Building on these studies, we investigate how local representation organization and object relevance can jointly guide fusion for dense 3D detection.

We focus on how information is organized after spatial alignment. Within the same local region, responses shared across modalities may originate from either objects or background, while differences between modalities may reflect useful sensing characteristics or noise. Cross-modal consistency therefore does not automatically imply object relevance, and modality differences should not be removed indiscriminately. [FactorCL](https://papers.neurips.cc/paper_files/paper/2023/hash/6818dcc65fdf3cbd4b05770fb957803e-Abstract-Conference.html), [Liu et al. (2025)](https://proceedings.nips.cc/paper_files/paper/2025/hash/55123f38c9f4acf417335cff41be6e27-Abstract-Conference.html) Detection requires considering which information can be shared, which differences should be retained, and how both relate to local objects. This motivates our research question: **How can shared and modality-specific representations be learned and incorporated into local fusion under the guidance of object-related information?** This question also arises in ordinary driving scenes; changes in illumination, occlusion, and adverse weather provide different conditions under which to examine it.

We introduce **ObjDec**, a multi-sensor fusion architecture that learns shared and modality-specific representations and uses object-related information to guide their fusion. Building on ASF's unified projection and local cross-sensor interaction, ObjDec constructs shared and modality-specific representations for corresponding sensor patches. During training, constraints within object regions encourage consistency among shared representations, maintain differences among modality-specific representations, and limit similarity between the two representations of each modality. The architecture then predicts foreground gates, modality contribution weights, and object context. The gates and weights jointly regulate updates to and scaling of input tokens, while object context modulates attention queries and fused outputs through gated residuals. This connects representation learning directly to fusion control, allowing both to shape the features used for detection. Ground-truth boxes are used only for training supervision; at inference, control signals are predicted from input features without ground-truth boxes or weather labels.

We evaluate ObjDec primarily on K-Radar. Under a common confidence-filtering setting of 0.3 on v1, ObjDec achieves **88.36 AP3D@0.3** and **88.10 APBEV@0.5**, improving over the corresponding evaluation of the released ASF checkpoint by **8.04** and **7.77** percentage points, respectively, with approximately **1.7%** more parameters. Component ablations assess the contribution of each design to detection performance, while representation visualizations and spatial gate analyses characterize the learned local representations and control behavior. We further examine a decoupled-control variant under the wider spatial coverage and expanded category setting of K-Radar v2, as well as the transfer of the full architecture to V2X-Radar-V, reporting the model variants, evaluation settings, and limitations separately.

Our main contributions are as follows:

1. **Local representation learning for object detection.** We explicitly organize spatially corresponding multi-sensor features into shared and modality-specific representations, using constraints within object regions to connect the learning of cross-modal consistency and differences to detection.
2. **An object-guided fusion architecture driven by learned representations.** We combine decoupled representations with foreground gating, modality contribution control, and object context to jointly modulate fusion inputs, attention queries, and fused outputs, allowing the learned representations to directly shape detection features.
3. **Evaluation of detection performance and model behavior.** Through main results on K-Radar, component ablations, representation and spatial gate analyses, and comparisons under extended settings, we assess the benefits, internal behavior, and scope of the design.

## 使用说明与核查依据（不进入 Introduction 正文）

- 当前英文约 700 词量级，五个段落加三条贡献；正式排版时可压缩第二段的逐方法介绍和贡献复述。该版本优先供讨论逻辑，不代表已经满足最终占页要求。
- 不使用 entangled、disentangled factors、statistical independence、causal、first 等超出现有证据或用户偏好的表述。这里的 decoupled 指有约束的共享/特有分支组织，不承诺严格独立或可辨识分解。
- 当前 K-Radar v1 主模型的目标上下文（object context）是二元 objectness 派生上下文，不是分类/回归任务分解，也不是多类别语义上下文；主图与方法节应明确。
- 模态贡献权重不是已校准的传感器可靠性概率；前景 gate 主要控制更新幅度，不等于把全部背景 token 清零。
- 数值和变体身份见[全文证据总稿](taskdec_full_paper_evidence_motivation_contributions_260917.md)、[置信度协议核查](asf_v1_conf_protocol_audit_260828.md)、[v2 同训练日程结果](taskdec_v2_matched_training_260915.md)。差值按归档原始精度计算，显示值先四舍五入再相减可能差 0.01。
- v1 的大幅 ASF 增益依赖所述置信度过滤口径；conf=0.0 与本地重训 ASF 对照必须保留在实验部分，不能将本段改写为所有协议全面领先。
- K-Radar v2 的 DecControlled Strong 不含目标上下文（object context）分支；v1/v2 是同一数据集的不同设置。目标数据集上训练的 V2X 结果是架构迁移验证，不是零样本泛化；当前不写多数据集一致领先。
- 当前完整 V2X 4×4 结果尚未超过 Concat，2×2 和 L4DR 的最终比较需随实验归档更新。该句只交代验证范围，不预先宣称有益迁移或最终排名。
- 这里没有写“更快于 ASF”，也没有把目前抽样测速和未重测全量 AP 的优化实现混为已完成的精度—效率主结论。
- 参考 WCBR 引言的“问题—结构—学习目标—证据”组织方式，不沿用其天气条件路由动机。正式相关工作应交代共享/特有表征的既有研究；DecAlign 是本稿已核验的一项概念近邻，不能把分支拆分本身写为首次提出。
- 图 1 动机应对应第三段，图 2 架构对应第四段；图 3–5 分别承担表征、空间控制和实际预测分析。图 5 尚未形成完成的 ASF–ObjDec 正文对比图，本稿不声称其已完成。

## 本轮文献补充说明（不进入 Introduction 正文）

- 引言正文由 4 篇方法引用扩展至 12 篇，其中 9 篇为 2025–2026 年发表/公开版本；详细来源见 [近期文献核查表](taskdec_recent_literature_and_comparability_260917.md)。
- 第一段补充 BEVFusion、MoME、RobuRCDet 作为融合路线与模态贡献的背景；第二段补充 DLRFusion、RAF、SPFD；第三段以 FactorCL 和 Liu 等（2025）支持共同信息、特有信息及噪声需要区别对待的研究背景。
- SPFD 已把 shared/private 学习用于检测，Liu 等已研究从模态特有信息中排除冗余。这里没有将“表征解耦用于检测”或“区分差异与噪声”本身称为首次提出。ObjDec 的具体定位仍是对应 BEV 区域中的目标监督和表征驱动的融合控制。
- 新文献的发表年份、传感器配置与 AP 可比性已单独登记；增加引用不等于建立新的统一协议 SOTA 排名。
