# ObjDec 主架构图：压缩输入、展开解耦与融合

日期：2026-09-22。当前推荐稿：[横向居中修订版](objdec_architecture_centered_draft.png)，对应[本轮修改、符号与图注](CENTERED_REVISION.md)。[此前初稿](objdec_architecture_draft.png)保留供对照。两者均为供讨论和手工矢量重画的生成式位图初稿，未修改论文正文或模型代码。以下保留前一版的设计记录，最新布局以居中修订说明为准。

## 本次调整

1. 输入区压缩到约15%，只保留各模态的Encoder、Projection + patchify和对应token。中央两个区合计约72%，展示表征分支、控制预测、token调制和注意力交互。检测头简化为末端小区。
2. 原长公式转换为加法、乘法、残差旁路和小增益标记。同一模态输入并行进入Shared/Specific两个独立映射；原始token在残差加法处保留。下方单模态示例的灰色向量代表任意模态，并非额外传感器。
3. 训练条使用明确的预测量名称作为信号端口，各自进入对应loss；GT派生patch标签用于表征约束、gate与objectness监督，GT框另用于检测监督。同名信号标签代表同一量，避免用跨图长线穿过其他模块。
4. 模态配色与已有PCA图一致：Camera橙`#D55E00`，LiDAR蓝`#0072B2`，Radar紫`#8B3FAA`。控制信号用中性灰／青绿色，训练监督用红色虚线。上述色值为提示词规定的设计色；最终矢量稿应直接使用这些值。

## 前向链路与代码核对

来源：[方法初稿](../../results/taskdec_methods_bilingual_initial_260917.md)、[融合实现](../../models/fuser/patch_dec_a2_fusion.py)。主图描述完整K-Radar ObjDec路径；v2 Strong不包含完整object-context路径，不应将本图直接称为Strong的计算图。

- 每个模态的同一个局部token分别经过两个独立MLP得到shared与specific，不是先将输入分成两部分，也不是shared继续生成specific。
- `Pool + concat`概括shared跨模态均值和specific逐元素绝对值的跨模态均值拼接，供gate与objectness预测使用。
- 模态贡献头读取原始token、shared、specific及shared相对跨模态均值的绝对偏差。图内`t, c, u, shared deviation`是该头输入端口的简写。
- `Bounded scale`由gate和相对贡献alpha共同生成，缩放围绕1并裁剪。它不是直接将原始token乘alpha。
- Token调制顺序：shared与specific相加 → gate及残差强度缩放 → 加回原始token → 有界模态缩放 → 受控token。低gate减弱更新，不删除背景。
- Objectness经投影形成context；gate与context相乘后分别注入learned queries和attention输出。输出残差位于PFT之前；PFT及空间重组后才进入检测头。
- 主图的多模态token组表示对各模态重复执行同一结构，各模态的表征映射参数独立。受控token随后沿传感器维堆叠为K/V；图中为简化未另画Stack算子。

## Loss对应关系

| 图中loss | 预测／表征来源 | 训练目标与范围 |
|---|---|---|
| L_dec | Shared与Specific两组表征 | GT前景位置内的shared一致性、specific相似度上界和同模态两分支分离约束 |
| L_gate | 预测gate的logit | GT派生patch前景／背景标签；不是GT直接输入gate头 |
| L_ctx | Objectness头的logit | K-Radar主设置的patch目标存在性标签；监督作用在context投影之前 |
| L_det | 检测头输出 | 目标类别、框回归与方向监督；图中3D boxes是检测输出的简写 |

SCL不再单独占主图底部的大框，以免与本文新增监督混淆。K-Radar主配置仍保留继承自ASF的传感器组合训练，具体路径与权重在方法和附录说明；从图中省略不代表训练时关闭。

## 中英文图注建议

**中文。** 图2：ObjDec架构。各传感器经编码与投影获得空间对应的BEV patch token。每个模态的同一个token通过两个独立映射得到共享与模态特有表征，进而预测前景门控、模态贡献和目标上下文。门控表征残差与有界模态缩放共同调制输入token；门控目标上下文进一步调制注意力查询与输出。融合token经PFT和空间重组形成BEV特征，由检测头输出三维预测。实线表示前向计算，红色虚线表示训练监督；同名信号端口表示同一量。GT仅用于构造监督，不参与推理。图中展示主检测路径，继承的传感器组合训练见附录；统一投影、局部注意力与PFT沿用ASF基础结构。

**English.** Figure 2: Overview of ObjDec. Sensor encoders and projection produce spatially corresponding BEV patch tokens. For each modality, two independent mappings transform the same token into shared and modality-specific representations, which support foreground gating, modality contribution prediction, and object context. A gated representation residual and bounded modality scaling modulate the input tokens. Gated object context further modulates attention queries and outputs. PFT and spatial reassembly produce fused BEV features for the 3D detection head. Solid arrows denote forward computation and red dashed arrows denote training supervision; repeated signal labels refer to the same quantity. Ground-truth annotations provide supervision only and are not required at inference. The figure shows the main detection path; inherited sensor-combination training is detailed in the appendix. Unified projection, local attention, and PFT follow the ASF foundation.

## 手工定稿建议

- 保留当前空间分配。排版仍可去掉大编号，并将顶部两个中央标题统一收在一个ObjDec框内。
- 统一最终上下标为正文的`t_m^p, c_m^p, u_m^p`等；生成图中的简写只表达计算角色。投影框里的额外参数符号可直接删除，进一步减字。
- 将红色的前向预测头改为中性青灰色，仅让loss与训练虚线使用红色，可更清楚地区分训练专用和训练／推理共用部分。
- 下方的预测信号端口应画成标准小端口，红色虚线从端口边界开始，避免看成从外层框引出的监督。GT两条目标线的交叉处不画结点；patch标签总线明确接L_dec、L_gate、L_ctx，GT框总线单独接L_det。
- 门控的几个灰色单元仅为示意，整幅图没有使用真实gate、PCA或检测样本。最终输出框也是示意，不能当成真实定性结果。
- 图为PNG位图，不是可编辑矢量。手工重画时保留上述链路，尤其不能让原始token直接绕过控制进入K/V，或让检测头绕过PFT。

## 生成记录

本轮使用内置`image_gen`工具。原图：[用户提供的架构原稿](../../b52c6b980abf09211eae140d5a245dd8.png)。原稿仅作结构与风格参考。

提示词依次保存为：[初始设计](generation_prompt.txt)、[布局修订](refinement_prompt.txt)、[主链路修正](graph_correction_prompt.txt)、[局部接线修正](wiring_refinement_prompt.txt)、[最终输入接线](input_wiring_prompt.txt)。`objdec_architecture_v1.png`至`v4.png`保留过程稿，部分含已修正的接线错误，不应作为正式图使用；推荐稿为`objdec_architecture_draft.png`。
