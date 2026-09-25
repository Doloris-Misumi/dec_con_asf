# ObjDec Introduction：中英文对照（Dec 为核心）

更新：2026-09-24。六段依次为多传感器检测、既有融合进展、解耦动机、目标引导、ObjDec 架构、实验证据，最后列三点贡献。本阅读版省略引用标记，完整分组引用见 [英文 LaTeX](sections/introduction.tex)。英文与中文逐段对应。

## 中文

准确的三维目标检测是自动驾驶的重要基础。相机、LiDAR 与四维雷达通过不同的传感机制观测场景，提供视觉外观、几何结构和雷达回波等信息。融合这些观测能够弥补单一传感器的局限，为目标检测提供更充分的信息。要发挥这种优势，需要将传感特性与空间采样方式不同的特征整合为有利于检测的联合表征，这也推动了多传感器融合研究的持续发展。

已有方法通过空间交互与自适应融合推动了多传感器检测的发展。在共同空间中建立对应关系，使不同传感器的特征能够围绕同一区域交换信息。注意力与门控机制进一步调整各模态的贡献，前景建模与可靠性估计则帮助模型应对输入质量的差异。这些进展为不同场景与感知条件下的传感器信息融合提供了有效基础。

然而，空间对应与自适应加权本身，并不区分哪些信息可以跨传感器共享、哪些线索属于模态特有信息。即使在空间对齐的局部区域中，这两类信息仍混合在输入特征中，但它们在融合中发挥着不同作用：共享信息能够提供跨模态支持，模态特有线索则能够保留互补观测。仅学习一致性可能削弱有用差异，而仅强调差异又可能忽略传感器之间的共同证据。由此，我们从表征解耦的角度考虑融合：显式学习共享与模态特有表征，并利用二者构建融合后的检测特征。这一思路建立在多模态预测中学习和保留共同信息与差异信息的已有研究基础上。

对于密集三维检测，这种解耦还需要与检测目标建立明确联系。共同响应可能来自目标，也可能来自背景；模态特有差异既可能反映有用观测，也可能包含噪声。因此，区分这两类信息本身并不能保证其与检测目标相关。为此，我们将表征约束作用于目标区域，并利用目标相关信息引导学习到的特征参与融合。目标引导由此为解耦表征的学习与使用赋予明确的检测指向。

我们提出 **ObjDec**，一种以共享与模态特有表征解耦为核心的多传感器三维检测架构。在空间对应的鸟瞰图（BEV）patch 中，独立映射从各传感器 token 构建这两种表征，并使二者共同参与融合检测特征的构建。目标区域监督促进共享表征的跨模态一致性，保留模态特有差异，并限制两个分支之间的相似性。学习到的表征进一步决定特征更新、模态贡献和目标上下文，使其中的信息影响融合输入与跨模态交互。前景门控与上下文调制实现了解耦表征到融合计算的这一联系。表征映射在所有 patch 上运行，目标区域则限定训练时表征约束的作用位置。真实标注框仅提供训练监督；推理时，所有融合控制信号均由输入特征预测，无需先验检测结果或天气标签。

我们主要在 K-Radar 上评估 ObjDec。在 v1、置信度过滤阈值为 0.3 的设置下，ObjDec 的 AP3D@IoU=0.3 和 APBEV@IoU=0.5 分别达到 **88.36%** 和 **88.10%**。在相同过滤设置下，相较于公开融合基线权重对应的归档结果，两项指标分别提高 **8.04** 和 **7.77 个百分点**，参数量仅增加约 **1.7%**。组件消融评估各项设计的贡献，表征可视化与空间门控分析则考察模型学到的特征组织方式和融合行为。此外，我们在 K-Radar v2 上评估解耦控制变体，并在 V2X-Radar-V 上训练和测试该架构，在明确的数据集协议下考察其对扩展类别与传感器设置的适用性。

本文的主要贡献如下：

1. **以表征解耦为核心的融合架构。** 构建多传感器三维检测架构，在空间对应的局部区域中显式学习共享与模态特有表征，并利用二者构建融合检测特征。
2. **目标引导的解耦表征学习与使用。** 在目标区域内监督表征解耦，并将学习到的表征与前景门控、模态贡献控制和目标上下文联系起来，引导其参与面向检测的融合。
3. **检测性能与模型行为的实验评估。** 在 K-Radar 上评估检测性能及组件贡献，分析表征与空间门控，并通过扩展类别设置及 V2X-Radar-V 上的目标数据集训练，考察该架构的适用性。

## English

Accurate 3D object detection is essential for autonomous driving. Cameras, LiDAR, and 4D radar observe a scene through different sensing mechanisms, providing visual appearance, geometric structure, and radar-return information. Combining these observations can compensate for limitations of individual sensors and provide a richer basis for detecting objects. Realizing this potential requires integrating features with different sensing characteristics and spatial sampling patterns into a joint representation that supports detection, motivating continued research on multi-sensor fusion.

Existing approaches have advanced multi-sensor detection through spatial interaction and adaptive fusion. Establishing correspondence in a common spatial domain allows features from different sensors to exchange information about the same regions. Attention and gating mechanisms further adjust their contributions, while foreground modeling and reliability estimation help account for differences in input quality. Together, these developments provide an effective foundation for combining sensor observations under varying scene and sensing conditions.

Nevertheless, spatial correspondence and adaptive weighting do not by themselves distinguish the information that can be shared across sensors from the cues specific to each modality. Even within aligned local regions, these two types of information remain mixed in the input features, although they play different roles in fusion: shared information can provide cross-modal support, while modality-specific cues can preserve complementary observations. Learning consistency alone may suppress useful differences, whereas emphasizing differences alone may overlook evidence shared across sensors. This motivates approaching fusion through representation decoupling: explicitly learning shared and modality-specific representations and using both to construct the fused detection features. Such a formulation builds on advances in learning and retaining common and distinct information for multimodal prediction.

For dense 3D detection, this decoupling also needs a clear connection to detection targets. Shared responses may originate from either objects or background, and modality-specific differences may reflect useful observations or noise. Separating the two types of information therefore does not by itself ensure their relevance to detection. We address this issue by grounding representation constraints in object regions and using object-related information to guide the contribution of the learned features to fusion. Object guidance thus gives the learning and use of decoupled representations a detection-specific focus.

We introduce **ObjDec**, a multi-sensor 3D detection architecture centered on shared and modality-specific representation decoupling. Within spatially corresponding bird's-eye-view (BEV) patches, separate mappings construct the two representations from each sensor token, and both participate in building the fused detection features. Object-region supervision encourages cross-modal agreement in shared representations, preserves modality-specific differences, and limits similarity between the two branches. The learned representations further determine feature updates, modality contributions, and object context, allowing their information to shape fusion inputs and cross-modal interaction. Foreground gating and context modulation implement this connection between decoupled representations and fusion computation. The representation mappings operate at every patch; object regions specify where the representation constraints are applied during training. Ground-truth boxes provide training supervision only, while inference predicts all fusion-control signals from input features without prior detections or weather labels.

We evaluate ObjDec primarily on K-Radar. At a confidence-filtering threshold of $0.3$ on v1, ObjDec achieves $88.36\%$ $\mathrm{AP}_{\mathrm{3D}}$ at IoU $0.3$ and $88.10\%$ $\mathrm{AP}_{\mathrm{BEV}}$ at IoU $0.5$. Compared with the archived results associated with the released fusion baseline under the same filtering setting, these scores improve by $8.04$ and $7.77$ percentage points, respectively, with approximately $1.7\%$ more parameters. Component ablations assess the contribution of each design, while representation visualizations and spatial gate analyses examine the learned feature organization and fusion behavior. We also evaluate a decoupled-control variant on K-Radar v2 and train and test the architecture on V2X-Radar-V, examining its applicability beyond the primary category and sensor setting under the specified dataset protocols.

Our main contributions are as follows:

1. **A fusion architecture based on representation decoupling.**     We develop a multi-sensor 3D detection architecture that explicitly learns shared and modality-specific representations in corresponding local regions and uses both to construct fused detection features.
2. **Object-guided learning and use of decoupled representations.**     We supervise representation decoupling within object regions and connect the learned representations to foreground gating, modality contribution control, and object context, guiding their use in detection-oriented fusion.
3. **Evaluation of detection performance and model behavior.**     We evaluate detection performance and component contributions on K-Radar, analyze representations and spatial gating, and examine the architecture under extended categories and target-dataset training on V2X-Radar-V.
