# ObjDec Methods：中英文初稿

日期：2026-09-17。版本：供讨论和后续 LaTeX 排版使用的初稿。

命名更新（2026-09-19）：方法名统一为 **ObjDec**，全称 **Object-Guided Representation Decoupling（目标引导的表征解耦）**。

机制说明更新（2026-09-20）：明确区分由特征预测的连续前景门控、仅用于训练损失的 GT 前景标签，以及可视化中后叠加的 GT 参照框。

正文按 Overview → Object-Guided Representation Decoupling → Representation-Driven Fusion → Training Objectives and Inference 组织，中英文段落及公式对应。以 K-Radar v1 完整 ObjDec 为主要定义，数据集适配及变体差异列于文末。公式编号为本章临时编号；`[ASF]` 为正式引用占位。

## 中文正文

### 3.1 总体架构

我们提出 ObjDec，一种学习共享与模态特有表征，并利用目标相关信息引导其融合的多传感器融合架构。如图 2 所示，给定相机、LiDAR 和四维雷达观测，各模态编码器首先生成空间对应的鸟瞰图（BEV）特征。我们采用 ASF 的统一空间投影，将不同通道数的特征映射为对应局部区域的 patch token，并保留其局部跨传感器注意力与后续特征变换作为交互基础 [ASF]。记参与融合的模态集合为 \(\mathcal M\)，模态数为 \(M=|\mathcal M|\)；\(t_m^p\in\mathbb R^d\) 表示模态 \(m\) 在 patch \(p\) 的输入 token。为简化记号，下文省略 batch 维。

ObjDec 在每个对应 patch 内学习共享与模态特有表征，并由这些表征预测前景门控、模态贡献权重和目标上下文。门控与模态权重调节输入 token 的更新和缩放，目标上下文则进一步调制注意力查询与融合输出。经局部交互、特征变换和空间重组后，融合 BEV 特征被送入三维检测头。训练和推理均从输入特征预测控制信号；真实目标框（GT）仅在训练时为表征约束与目标相关预测构建监督标签。

> **图 2 插入位置。** 展示完整前向路径，并将目标框监督以虚线连接到对应训练目标。建议使用本文件后附的中英文图注；现有主图需要按照已核查的 token 缩放公式和箭头顺序修订后再插入。

### 3.2 目标引导的表征解耦

空间对应的多模态特征同时包含跨传感器的共同响应与各自特有的观测信息。为显式组织这两类信息，我们为每个模态设置两个独立的映射分支：

\[
c_m^p=\phi_m^{c}(t_m^p),\qquad
u_m^p=\phi_m^{u}(t_m^p),
\quad c_m^p,u_m^p\in\mathbb R^d.
\tag{1}
\]

其中，\(c_m^p\) 和 \(u_m^p\) 分别表示共享与模态特有表征，\(\phi_m^c\) 与 \(\phi_m^u\) 由轻量多层感知机实现。各模态使用独立参数；共享表征之间的对应关系通过训练约束建立。

为了将表征学习与检测目标联系起来，我们根据训练标注构建用于监督的前景 patch 集合 \(\mathcal P_{\mathrm{fg}}\)：当 patch 中心位于真实三维框的 BEV 投影及其预设扩张范围内时，将其视为前景。式（1）的表征映射在所有空间位置执行；该集合仅指定以下三项训练约束的计算区域：

\[
\begin{aligned}
\mathcal L_c
&=\mathbb E_{p\in\mathcal P_{\mathrm{fg}},\,m<n}
\left[1-\operatorname{cos}(c_m^p,c_n^p)\right],\\
\mathcal L_u
&=\mathbb E_{p\in\mathcal P_{\mathrm{fg}},\,m<n}
\left[\operatorname{cos}(u_m^p,u_n^p)-\delta\right]_+,\\
\mathcal L_{\mathrm{sep}}
&=\mathbb E_{p\in\mathcal P_{\mathrm{fg}},\,m}
\left[\left|\operatorname{cos}(c_m^p,u_m^p)\right|\right].
\end{aligned}
\tag{2}
\]

这里，\(\operatorname{cos}(\cdot,\cdot)\) 为余弦相似度，\([a]_+=\max(a,0)\)，\(\delta\) 为相似度间隔，\(\mathbb E\) 表示对所列前景 patch 及模态或无序模态对取算术平均。\(\mathcal L_c\) 鼓励同一区域的共享表征保持一致；\(\mathcal L_u\) 对模态特有表征过高的跨模态相似性施加惩罚；\(\mathcal L_{\mathrm{sep}}\) 限制同一模态两类表征的相似程度。通过这些目标区域内的软约束，两类分支获得不同的表示角色，并与检测损失共同优化。前景集合仅用于训练监督，所有空间位置的表征均可直接由输入 token 计算。

### 3.3 表征驱动的融合

我们进一步利用解耦表征决定局部信息如何参与融合。对于 patch \(p\)，定义共享表征均值 \(\bar c^p=M^{-1}\sum_m c_m^p\) 和特有表征幅值均值 \(\bar u_{\mathrm{abs}}^p=M^{-1}\sum_m|u_m^p|\)，并构建联合描述 \(h^p=[\bar c^p;\bar u_{\mathrm{abs}}^p]\)。其中，分号表示特征拼接，绝对值按元素计算。

**输入 token 调制。** 联合描述用于预测 patch 级前景门控，各模态的贡献评分同时考虑原始 token、两类表征以及该模态共享表征与跨模态均值的差异：

\[
\begin{aligned}
g^p&=\sigma\!\left(f_g(h^p)\right),\\
s_m^p&=f_m\!\left([t_m^p;c_m^p;u_m^p;|c_m^p-\bar c^p|]\right),\\
\alpha_m^p&=\frac{\exp(s_m^p/\tau)}{\sum_{n\in\mathcal M}\exp(s_n^p/\tau)}.
\end{aligned}
\tag{3}
\]

其中，\(\sigma\) 为 sigmoid 函数，\(f_g\) 与 \(f_m\) 为可学习预测头，\(\tau>0\) 为温度。\(g^p\in(0,1)\) 是直接由多模态表征预测的连续前景相关性分数，在同一 patch 内由各模态共享。该预测头不生成目标框，也不依赖预先检测的目标区域；所有 patch 的门控均通过式（3）计算，并直接参与连续调制。\(\alpha_m^p\) 表示学习到的相对模态贡献。我们将其转换为围绕 1 的有界缩放系数，并更新输入 token：

\[
\begin{aligned}
w_m^p
&=\operatorname{clip}\!\left(1+\eta g^p(M\alpha_m^p-1),\,w_{\min},w_{\max}\right),\\
\widetilde t_m^p
&=w_m^p\left[t_m^p+\lambda g^p(c_m^p+u_m^p)\right].
\end{aligned}
\tag{4}
\]

\(\eta\) 和 \(\lambda\) 分别控制模态缩放与表征残差的强度，缩放区间包含 1。当模态贡献均匀时，\(w_m^p=1\)；当前景门控趋近于零时，表征残差减弱，缩放系数也趋近于 1，原始 token \(t_m^p\) 仍被保留。因此，门控调节局部更新幅度，而不通过二值掩码删除背景特征；模态评分决定各传感器特征的相对缩放。

**目标上下文引导的交互。** 为使跨模态交互进一步受到检测目标相关信息引导，我们从 \(h^p\) 预测目标上下文。在单类别主设置中，首先预测 patch 的目标存在性，再将其映射到 token 空间：

\[
r^p=\sigma\!\left(f_{\mathrm{obj}}(h^p)\right),\qquad
z^p=\tanh(W_z r^p),\quad z^p\in\mathbb R^d.
\tag{5}
\]

这里 \(f_{\mathrm{obj}}\) 是独立的目标存在性预测头，\(W_z\) 为可学习映射。前景门控控制更新强度，\(z^p\) 提供由目标存在性预测映射得到的上下文向量。多类别设置可使用前景类别概率生成上下文，对应监督方式在附录中说明。

设 \(Q\in\mathbb R^{N_q\times d}\) 为各 patch 复用的可学习查询，\(\widetilde T^p\in\mathbb R^{M\times d}\) 为堆叠后的受控模态 token。我们将上下文同时用于查询与注意力输出：

\[
\begin{aligned}
Q'^p&=Q+\beta g^p\mathbf 1_{N_q}(z^p)^\top,\\
F^p&=\operatorname{MHA}(Q'^p,\widetilde T^p,\widetilde T^p),\\
F'^p&=F^p+\gamma g^p\mathbf 1_{N_q}(z^p)^\top.
\end{aligned}
\tag{6}
\]

\(\operatorname{MHA}\) 为包含可学习查询、键和值投影的多头注意力，\(\mathbf 1_{N_q}\) 将同一局部上下文广播到该 patch 的全部查询位置；\(\beta\) 和 \(\gamma\) 控制两处残差强度。更新后的 \(F'^p\) 经过后续特征变换与空间重组，形成用于检测的融合 BEV。由此，共享与模态特有表征通过输入更新、模态贡献控制以及上下文引导的交互，共同参与检测特征的构建。

### 3.4 训练目标与推理

在主设置中，我们使用前景指示标签 \(y^p=\mathbb 1[p\in\mathcal P_{\mathrm{fg}}]\)，分别监督前景门控 \(g^p\) 与目标存在性预测 \(r^p\)。两者采用具有正样本权重的二元交叉熵，记为 \(\mathcal L_g\) 和 \(\mathcal L_{\mathrm{ctx}}\)，覆盖训练批次中的前景与背景 patch。式（2）的三项表征约束则在前景集合内计算。训练前向同样使用由特征预测的 \(g^p\) 和 \(r^p\)；标签 \(y^p\) 仅参与损失计算，不替代预测值进行融合。

整体目标为：

\[
\begin{aligned}
\mathcal L={}&\mathcal L_{\mathrm{det}}+\lambda_{\mathrm{scl}}\mathcal L_{\mathrm{scl}}\\
&+\lambda_{\mathrm{aux}}\bigl(
\lambda_c\mathcal L_c+
\lambda_u\mathcal L_u+
\lambda_{\mathrm{sep}}\mathcal L_{\mathrm{sep}}+
\lambda_g\mathcal L_g+
\lambda_{\mathrm{ctx}}\mathcal L_{\mathrm{ctx}}\bigr).
\end{aligned}
\tag{7}
\]

其中，\(\mathcal L_{\mathrm{det}}\) 包含检测分类、框回归及朝向损失；\(\mathcal L_{\mathrm{scl}}\) 为沿用 ASF 的传感器组合监督，即对单模态及两模态组合特征施加检测损失并求和 [ASF]。该项在 K-Radar 主设置中启用，各数据集的训练配置分别报告。\(\lambda_{\mathrm{aux}}\) 控制新增监督的整体权重，其余系数控制各项相对贡献。前向调制是可微的，检测损失与辅助目标共同优化表征分支和控制预测头。

推理时，模型保留相同的门控、模态贡献和上下文预测分支，沿式（4）—（6）生成检测特征，无需 GT 标签构建与损失计算。前景门控提供局部融合的连续控制信号，最终的目标类别、三维位置、尺寸和朝向由后续检测头预测。网络尺寸、损失系数、组合监督实现及数据集适配细节列于附录。

## English draft

### 3.1 Overview

We introduce ObjDec, a multi-sensor fusion architecture that learns shared and modality-specific representations and uses object-related information to guide their fusion. As illustrated in Figure 2, modality-specific encoders first transform camera, LiDAR, and 4D radar observations into spatially corresponding bird's-eye-view (BEV) features. We adopt ASF's unified projection to map features with different channel dimensions into patch tokens for corresponding local regions, and retain its local cross-sensor attention and subsequent feature transformation as the interaction backbone [ASF]. Let \(\mathcal M\) denote the participating modalities, with \(M=|\mathcal M|\), and let \(t_m^p\in\mathbb R^d\) be the input token of modality \(m\) at patch \(p\). We omit the batch dimension for clarity.

Within each corresponding patch, ObjDec learns shared and modality-specific representations and uses them to predict a foreground gate, modality contribution weights, and object context. The gate and modality weights regulate input-token updates and scaling, while object context further modulates attention queries and fused outputs. Local interaction is followed by feature transformation and spatial reassembly to produce fused BEV features for the 3D detection head. Control signals are predicted from input features during both training and inference; ground-truth (GT) boxes provide supervision targets for representation constraints and object-related predictions only during training.

> **Figure 2 placement.** Show the complete forward path, with dashed connections from ground-truth boxes to the corresponding training objectives. A suggested bilingual caption is provided below. The existing figure draft should be revised to match the verified token-scaling equations and operation order before insertion.

### 3.2 Object-Guided Representation Decoupling

Spatially corresponding multimodal features contain both responses shared across sensors and cues specific to each modality. To explicitly organize these two components, we introduce two independent mappings for each modality:

\[
c_m^p=\phi_m^{c}(t_m^p),\qquad
u_m^p=\phi_m^{u}(t_m^p),
\quad c_m^p,u_m^p\in\mathbb R^d.
\tag{1}
\]

Here, \(c_m^p\) and \(u_m^p\) denote shared and modality-specific representations, respectively, and \(\phi_m^c\) and \(\phi_m^u\) are lightweight multilayer perceptrons. Their parameters are separate across modalities; correspondence between shared representations is established through training constraints.

To connect representation learning to detection, we construct a foreground patch set \(\mathcal P_{\mathrm{fg}}\) for supervision from training annotations. A patch is marked as foreground when its center lies within the BEV footprint of a ground-truth 3D box expanded by a predefined margin. The representation mappings in Equation (1) operate at all spatial locations; this set only specifies where the following three training constraints are evaluated:

\[
\begin{aligned}
\mathcal L_c
&=\mathbb E_{p\in\mathcal P_{\mathrm{fg}},\,m<n}
\left[1-\operatorname{cos}(c_m^p,c_n^p)\right],\\
\mathcal L_u
&=\mathbb E_{p\in\mathcal P_{\mathrm{fg}},\,m<n}
\left[\operatorname{cos}(u_m^p,u_n^p)-\delta\right]_+,\\
\mathcal L_{\mathrm{sep}}
&=\mathbb E_{p\in\mathcal P_{\mathrm{fg}},\,m}
\left[\left|\operatorname{cos}(c_m^p,u_m^p)\right|\right].
\end{aligned}
\tag{2}
\]

Here, \(\operatorname{cos}(\cdot,\cdot)\) denotes cosine similarity, \([a]_+=\max(a,0)\), and \(\delta\) is a similarity margin. Each expectation denotes an arithmetic mean over the indicated foreground patches and modalities or unordered modality pairs. \(\mathcal L_c\) encourages agreement between shared representations of the same region; \(\mathcal L_u\) penalizes excessive cross-modal similarity between modality-specific representations; and \(\mathcal L_{\mathrm{sep}}\) limits similarity between the two representations of each modality. These soft constraints establish distinct roles for the two branches within object regions, alongside the detection objective. The foreground set is used only for training supervision; representations at all spatial locations are computed directly from input tokens.

### 3.3 Representation-Driven Fusion

We use the decoupled representations to determine how local information participates in fusion. For patch \(p\), let \(\bar c^p=M^{-1}\sum_m c_m^p\) and \(\bar u_{\mathrm{abs}}^p=M^{-1}\sum_m|u_m^p|\) denote the mean shared representation and the mean magnitude of modality-specific representations. Their concatenation forms a joint descriptor \(h^p=[\bar c^p;\bar u_{\mathrm{abs}}^p]\), where absolute values are elementwise.

**Input-token modulation.** The joint descriptor predicts a patch-level foreground gate. Each modality contribution score considers the original token, its two representations, and the deviation of its shared representation from the cross-modal mean:

\[
\begin{aligned}
g^p&=\sigma\!\left(f_g(h^p)\right),\\
s_m^p&=f_m\!\left([t_m^p;c_m^p;u_m^p;|c_m^p-\bar c^p|]\right),\\
\alpha_m^p&=\frac{\exp(s_m^p/\tau)}{\sum_{n\in\mathcal M}\exp(s_n^p/\tau)}.
\end{aligned}
\tag{3}
\]

Here, \(\sigma\) is the sigmoid function, \(f_g\) and \(f_m\) are learned prediction heads, and \(\tau>0\) is a temperature. The gate \(g^p\in(0,1)\) is a continuous foreground-relevance score predicted directly from multimodal representations and shared across modalities within a patch. This head neither generates bounding boxes nor requires previously detected object regions. Gates are computed at every patch through Equation (3) and directly used for continuous modulation. The weight \(\alpha_m^p\) represents the learned relative contribution of modality \(m\). We convert these contributions into bounded scaling factors centered on one and update the input tokens:

\[
\begin{aligned}
w_m^p
&=\operatorname{clip}\!\left(1+\eta g^p(M\alpha_m^p-1),\,w_{\min},w_{\max}\right),\\
\widetilde t_m^p
&=w_m^p\left[t_m^p+\lambda g^p(c_m^p+u_m^p)\right].
\end{aligned}
\tag{4}
\]

The coefficients \(\eta\) and \(\lambda\) control modality scaling and the representation residual, respectively, and the scaling interval contains one. Uniform modality contributions yield \(w_m^p=1\). As the gate approaches zero, the representation residual diminishes and the scaling factors approach one, preserving the original token \(t_m^p\). The gate therefore regulates local update strength without removing background features through a binary mask, while modality scores determine relative feature scaling.

**Object-context-guided interaction.** To guide cross-modal interaction with information related to detection targets, we also predict object context from \(h^p\). In the single-class primary setting, an objectness prediction is mapped into the token space:

\[
r^p=\sigma\!\left(f_{\mathrm{obj}}(h^p)\right),\qquad
z^p=\tanh(W_z r^p),\quad z^p\in\mathbb R^d.
\tag{5}
\]

Here, \(f_{\mathrm{obj}}\) is a separate objectness prediction head and \(W_z\) is a learned mapping. The foreground gate controls update strength, while \(z^p\) supplies a context vector derived from predicted objectness. Multi-class settings can instead use foreground class probabilities to form the context, with the corresponding supervision specified in the appendix.

Let \(Q\in\mathbb R^{N_q\times d}\) be learned queries reused across patches, and let \(\widetilde T^p\in\mathbb R^{M\times d}\) stack the controlled modality tokens. We incorporate the context into both the queries and attention outputs:

\[
\begin{aligned}
Q'^p&=Q+\beta g^p\mathbf 1_{N_q}(z^p)^\top,\\
F^p&=\operatorname{MHA}(Q'^p,\widetilde T^p,\widetilde T^p),\\
F'^p&=F^p+\gamma g^p\mathbf 1_{N_q}(z^p)^\top.
\end{aligned}
\tag{6}
\]

\(\operatorname{MHA}\) denotes multi-head attention with learned query, key, and value projections. The vector \(\mathbf 1_{N_q}\) broadcasts the local context over all query positions within the patch, and \(\beta\) and \(\gamma\) control the two residual strengths. The updated tokens \(F'^p\) undergo subsequent feature transformation and spatial reassembly to form the fused BEV representation. Shared and modality-specific representations thereby contribute to detection features through input updates, modality contribution control, and context-guided interaction.

### 3.4 Training Objectives and Inference

In the primary setting, foreground indicators \(y^p=\mathbb 1[p\in\mathcal P_{\mathrm{fg}}]\) supervise both the foreground gate \(g^p\) and objectness prediction \(r^p\). Their losses, \(\mathcal L_g\) and \(\mathcal L_{\mathrm{ctx}}\), use binary cross-entropy with positive-class weighting over foreground and background patches in a training batch. The three representation constraints in Equation (2) are evaluated within the foreground set. The training forward pass also uses the feature-predicted \(g^p\) and \(r^p\); labels \(y^p\) enter only the loss computation and do not replace these predictions in fusion.

The overall objective is

\[
\begin{aligned}
\mathcal L={}&\mathcal L_{\mathrm{det}}+\lambda_{\mathrm{scl}}\mathcal L_{\mathrm{scl}}\\
&+\lambda_{\mathrm{aux}}\bigl(
\lambda_c\mathcal L_c+
\lambda_u\mathcal L_u+
\lambda_{\mathrm{sep}}\mathcal L_{\mathrm{sep}}+
\lambda_g\mathcal L_g+
\lambda_{\mathrm{ctx}}\mathcal L_{\mathrm{ctx}}\bigr).
\end{aligned}
\tag{7}
\]

Here, \(\mathcal L_{\mathrm{det}}\) includes detection classification, box regression, and orientation losses. \(\mathcal L_{\mathrm{scl}}\) is the sensor-combination supervision inherited from ASF: the sum of detection losses on single-modality and two-modality feature combinations [ASF]. It is enabled in the primary K-Radar setting, and training configurations are reported separately for each dataset. The coefficient \(\lambda_{\mathrm{aux}}\) controls the overall weight of the added supervision, while the remaining coefficients balance its components. The forward modulation is differentiable, allowing detection and auxiliary objectives to jointly optimize the representation branches and control heads.

At inference, the model retains the same gate, modality contribution, and context prediction branches and forms detection features through Equations (4)–(6), without constructing GT labels or computing losses. The foreground gate provides continuous control over local fusion; the subsequent detection head predicts object classes, 3D locations, dimensions, and orientations. Network dimensions, loss weights, sensor-combination training details, and dataset-specific adaptations are provided in the appendix.

## 图 2 图注建议 / Suggested Figure 2 caption

**中文。** ObjDec 总体架构。各模态 BEV 特征经统一投影形成空间对应的 patch token，随后映射为共享与模态特有表征。由这些表征预测的前景门控与模态贡献共同调节输入 token，目标上下文进一步调制注意力查询与融合输出。输出经特征变换及空间重组后送入三维检测头。实线前向路径在训练与推理中均使用特征预测的控制信号；虚线将 GT 衍生标签连接到训练损失，不作为门控预测的输入。统一投影、局部跨传感器注意力及后续特征变换沿用 ASF [ASF]。

**English.** Overview of ObjDec. Modality-specific BEV features are projected into spatially corresponding patch tokens and mapped to shared and modality-specific representations. Foreground gates and modality contributions predicted from these representations jointly regulate input tokens, while object context modulates attention queries and fused outputs. Feature transformation and spatial reassembly produce BEV features for the 3D detection head. The solid forward path uses feature-predicted control signals during both training and inference. Dashed connections carry GT-derived labels to training losses, not to the gate predictor. Unified projection, local cross-sensor attention, and subsequent feature transformation follow ASF [ASF].

## 附录安排与实现核查备注（不直接进入方法正文）

以下内容区分为可移入附录的复现细节，以及作者改稿时需要保持一致的事实。正文并未引用具体附录编号，待全文顺序确定后统一编号。

### A. 建议的附录内容

| 附录内容 | 应包含的细节 | 正文对应位置 |
|---|---|---|
| 网络与符号明细 | 编码器、输入字段、通道数、patch尺寸、query数量、MLP结构和输出尺寸 | 3.1、3.2 |
| 前景目标生成与辅助损失 | 旋转框投影、扩张范围、patch中心判定、重叠框及空前景处理、正样本权重 | 3.2、3.4 |
| 控制信号与训练配置 | 缩放边界、强度系数、初始化、主模型冻结策略及SCL分支流程 | 3.3、3.4 |
| 数据集适配与变体 | v1完整ObjDec、v2 DecControlled Strong、V2X类别上下文及patch/query设置 | 实验设置及3.3、3.4 |

### B. 主模型配置与公式对应

下表对应 `configs/ASF_task_dec_controlled_robust_v1_0.yml` 及其 ASF 基配置。正文公式（3）—（6）使用该主配置：gate范围为0–1，没有启用训练阶段控制强度衰减。\(\lambda\) 是前向残差强度，与损失权重 \(\lambda_{\mathrm{aux}}\) 等符号区分。

| 正文符号 / 项 | 主配置值 | 实现字段 / 说明 |
|---|---:|---|
| \(d\) | 256 | `UCP.DIM_PATCH` |
| patch尺寸 | 2×2 BEV单元 | `UCP.PATCH_SIZE`；不同数据集的物理尺度不同 |
| \(N_q\) | 32 | `UCP.N_QUERY`；主模型重组后的融合通道为2048，不应画成始终256通道 |
| 分支MLP隐藏维度 | 256 | `PATCH_DEC_HIDDEN_DIM`；LayerNorm–Linear–GELU–Linear–LayerNorm |
| gate / modality score隐藏维度 | 128 | `DEC_CONTROL_GATE_HIDDEN_DIM` / `DEC_CONTROL_HIDDEN_DIM` |
| objectness head隐藏维度 | 160 | `DEC_CONTROL_CLASS_HIDDEN_DIM` |
| 前景扩张距离 | 0.7 m | `PATCH_DEC_FG_MARGIN`；沿框局部两轴的半长、半宽各加该值 |
| \(\delta\) | 0.1 | `PATCH_DEC_UNIQUE_MARGIN` |
| \(\tau\) | 1.0 | `DEC_CONTROL_TEMPERATURE` |
| \(\eta\) | 0.75 | `DEC_CONTROL_STRENGTH` |
| \(\lambda\) | 0.08 | 实际前向读取 `DEC_CONTROL_DEC_RES_SCALE` |
| \([w_{\min},w_{\max}]\) | [0.4, 2.1] | `DEC_CONTROL_SCALE_MIN/MAX` |
| \(\beta,\gamma\) | 0.16, 0.06 | query和输出残差强度 |
| \(\lambda_{\mathrm{scl}}\) | 1.0 | `LOSS.INDIV_WEIGHT`；六个单/双模态分支检测损失求和，未除以分支数 |
| \(\lambda_{\mathrm{aux}}\) | 0.12 | `LOSS.PATCH_DEC_WEIGHT` |
| \(\lambda_c,\lambda_u,\lambda_{\mathrm{sep}}\) | 0.12, 0.015, 0.10 | 三项表征损失的内部系数 |
| \(\lambda_g,\lambda_{\mathrm{ctx}}\) | 0.15, 0.30 | 两项目标相关监督的内部系数 |

外层权重与内部系数相乘才是相对于主检测损失的实际系数：common 0.0144、unique 0.0018、separation 0.012、gate 0.018、context 0.036。不要漏掉外层 `PATCH_DEC_WEIGHT`。

gate与objectness的BCE分别使用 \(\operatorname{clip}(N_{\mathrm{bg}}/\max(N_{\mathrm{fg}},1),1,k)\) 作为正样本权重；主配置的上限 \(k\) 分别为30和4。权重由当前batch全部patch的前景/背景数计算。若整个batch无选中前景，当前实现跳过整组新增辅助损失；缺少有效标注或少于两种训练模态时也不会执行该辅助损失块。前向仍照常计算，检测及已启用的组合监督保留。

前景mask使用旋转框局部坐标判断patch中心，而不是按patch与框的交叠面积或整块覆盖判断。二元模式下重叠框只影响同一个前景标记；多类别模式下当前实现按有效GT框遍历顺序覆盖重叠patch的类别目标，正式附录应明确。

模态评分头末层权重和bias初始化为0，初始softmax贡献均匀；gate头末层权重为0、bias为−1.2。目标存在性头末层权重和bias为0；上下文映射无bias，权重以标准差0.015初始化。common/unique分支在不同模态之间不共享参数。K-Radar主配置冻结编码器参数，但 `FREEZE_BN=False`，不可写成所有编码器状态均固定。

### C. SCL与主融合路径的具体区别

主检测路径使用式（6）的query调制和输出残差，输出残差位于PFT之前。沿用的SCL路径从本次完整输入计算得到的受控token中选取单模态及双模态组合，共用已调制query，经过attention、PFT和同一个检测头后求检测损失；这些组合分支没有额外应用主路径的context输出残差，也没有针对每个子集重新预测gate、模态权重和context。

因此，SCL提供组合特征上的辅助检测监督，不能把它描述为“每次仅使用对应子集观测，重新独立运行完整ObjDec”。正式附录应给出这一区别；正文中的 \(\mathcal L_{\mathrm{scl}}\) 定义仅承诺对组合特征施加检测损失。

### D. 不同设置中的模型身份

| 设置 | 上下文与训练差异 | 正文中应如何交代 |
|---|---|---|
| K-Radar v1完整ObjDec | `DEC_CONTROL_NUM_CLASSES=1`，auto选择 `task_binary`；sigmoid目标存在性，前景+背景BCE；SCL启用 | 本方法章的主要实例 |
| K-Radar v2 DecControlled Strong | 无object-context头、query调制或输出context残差；含解耦、gate与模态控制；控制强度和损失权重也不同 | 单独注明为DecControlled变体，不能将其结果作为完整式（5）—（6）的验证 |
| V2X完整ObjDec | Vehicle/Pedestrian/Cyclist三类；softmax类别概率投影为context；只在前景patch上施加类别加权交叉熵；SCL关闭 | 是完整架构的数据集适配，显式说明context监督改变及编码器/检测头配置 |
| V2X 4×4与2×2 | token维度128；query数分别16和4；融合输出通道均128 | 与K-Radar的2×2/32-query设置区分；空间粒度实验同时改变patch和query数 |

多类别上下文将式（5）的标量 \(r^p\) 替换为 \(K\) 维softmax概率，使用 \(d\times K\) 的无bias映射 \(W_z\)，其余context进入query/output的方式保持不变。类别交叉熵只对前景计算，类别权重按当前batch前景目标计数的倒频率确定并裁剪到配置上限；独立gate继续以目标前景/背景监督。V2X冻结配置启用三类模式，不能把正文单类别BCE直接抄入其实现细节。

### E. 行文和主图一致性

- 两类分支的相似度约束不等于统计独立、可辨识分解或严格正交；本文也没有重建损失要求 \(c+u=t\)。
- \(\alpha\) 是模态贡献概率，\(w\) 才是token缩放系数；不将其称为已校准的物理传感器可靠性。
- \(g\) 控制新增残差与缩放偏离1的程度，原始背景token仍保留。图中宜用“foreground-gated modulation”，不画成清空背景的mask操作。
- 区分三种对象：训练前景标签 \(y\)、特征预测门控 \(g\)、绘图参照 GT 框。训练和推理的融合路径均使用 \(g\)，GT 衍生的 \(y\) 只连接损失；不要画成先检测目标框、再按框生成门控。Fig.4 中的 GT 轮廓是门控预测完成后的参照叠加。
- 单类别context是由目标存在性标量映射形成的向量，不表述成分类/回归任务分解、实例关系建模或已验证的多类语义编码。
- common/unique、gate、score和context均在对应patch内计算；context只生成一次后分别送往query与attention输出，不能画出PFT反馈生成context的环路。
- 主图的三路输入与channel标注需与真实配置一致；K-Radar雷达输入为xyz/power，不能标为已经使用Doppler速度。编码器冻结属于训练设置，可以放图注或附录，不必作为架构的固定图标。
- 此初稿的公式和实现备注已经核对，但图2仍需修订，具体附录全文和正式LaTeX引用尚待编排；没有将这些事项写成已完成产物。

### F. 核查来源

- [ObjDec融合实现](../models/fuser/patch_dec_a2_fusion.py)：分支、前景目标、三项表征约束、控制预测、context与完整前向顺序。
- [ASF融合实现](../models/fuser/a2_fusion.py)：投影、learned query、MHA、PFT及空间重组。
- [损失组合实现](../models/skeletons/fusion_base_integrated.py)：主检测、SCL求和、外层辅助损失权重。
- [v1主模型配置](../configs/ASF_task_dec_controlled_robust_v1_0.yml)及[ASF基配置](../configs/v1_0/cfg_A2F_scl_final.yml)。
- [v2 Strong配置](../configs/ASF_dec_controlled_strong.yml)、[V2X架构与协议](taskdec_v2x_architecture_protocol_260916.md)、[V2X小patch实验配置说明](taskdec_v2x_patch2_launch_260917.md)。
- [主图核查记录](taskdec_figure_draft_review_and_fig5_plan_260917.md)、[Introduction初稿](taskdec_introduction_bilingual_initial_260917.md)。
