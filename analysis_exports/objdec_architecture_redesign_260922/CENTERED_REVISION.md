# ObjDec主架构图：横向居中修订

推荐图稿：[objdec_architecture_centered_draft.png](objdec_architecture_centered_draft.png)。使用内置image_gen编辑生成；原版另存保留。本稿用于布局讨论及手工矢量重画，图内特征、gate和检测框均为机制示意。

## 本轮对应修改

1. **主干居中。** 主特征流保持在画面中部，依次为输入token、Token modulation、受控token、跨模态注意力、输出残差、PFT、融合BEV、检测头及预测框。解耦与控制预测放在主线之上。
2. **明确Token modulation与主干的关系。** 主线上直接设置Token modulation模块，其下方以两条灰色虚线连接展开图，表示同一模块的计算细节，而非第二次调制。原始token从左侧输入；顶部同名端口复用上方得到的c、u、g、w。
3. **区分查询与融合输出。** 标注Q、Q′、F与F′，分别对应学习查询、经上下文调制的查询、注意力融合输出及再次注入上下文后的输出。
4. **压缩Detection。** 移除空的全高检测栏，改为紧贴中心主线的Fused BEV → 3D head → 3D boxes小框。

上述历史PNG使用Camera橙、LiDAR蓝、Radar紫。**2026-09-23更新：** 用户指定改为参考图中的Camera蓝（`#4A9EEB`）、LiDAR绿（`#58B77A`）、Radar紫（`#9672D0`），最新PCA与gate图及手工排版素材见[统一配色图稿](../objdec_visuals_blue_green_purple_260923/README.md)。本架构PNG尚未重新绘制，手工稿请采用新版颜色。

前向控制的g为标量、z为上下文向量、w为各模态的标量缩放系数。c/u仍是高维表征；主模块顶部的小圆为信号端口，不代表c/u被变成标量。

**c/u可视化插图。** 可使用[真实局部patch PCA小图](../objdec_visuals_blue_green_purple_260923/architecture_insets/architecture_shared_specific_pca_normal.png)替换装饰性token图案，但保留`c_m^p`、`u_m^p`和通往Pool/Concat的实线；灰色虚线连接PCA插图，并标注`PCA visualization`。后续算子仍接收高维表征，PCA不进入前向计算。图内应说明小图展示多帧前景patch集合，不能把共享分支的三种颜色都画成重叠来替代真实分布。

## g、α、w与z的来源（2026-09-23按代码核清）

旧图的`Controlled token = (t + λ·g·(c+u)) × α`把相对模态贡献和实际缩放系数混用了。正式稿与方法章节统一为：

\[
\widetilde t_m^p=w_m^p[t_m^p+\lambda g^p(c_m^p+u_m^p)],\qquad
w_m^p=\operatorname{clip}(1+\eta g^p(M\alpha_m^p-1),w_{\min},w_{\max}).
\]

三模态时M=3。α是softmax输出，三个α之和为1；w是围绕1的有界缩放，不要求三个w之和为1。模态评分相同时，α均为1/3、w均为1，保留输入幅值；g趋近0时，w也趋近1。

**Pool的准确含义。** 在同一个patch位置p，沿模态维计算`mean(c)`和`mean(abs(u))`，再拼接为`h=[mean(c); mean(abs(u))]`。这里不是把全部空间patch池化成一个全局向量，也不是把c与u逐元素相加。建议图内标为`Modality pooling + concat`，两条输入分别注明`mean`与`abs → mean`。

| 信号 | 实际输入与计算 | 含义及输出粒度 | 主图短标签 |
|---|---|---|---|
| g | h → 独立gate MLP → sigmoid | 每个patch一个标量，三模态共享 | `Foreground head → Sigmoid → g` |
| α | 每模态拼接`[t_m,c_m,u_m,abs(c_m−mean(c))]` → 各自评分MLP → 三模态分数softmax | 每个patch每个模态一个相对贡献，和为1 | `Modality scoring → Softmax → α` |
| w | α与g共同进入上述围绕1的缩放及clip | 每个patch每个模态一个实际缩放系数 | `Gate-conditioned scaling → w` |
| z | h → 独立object MLP → 目标存在概率r → Linear → tanh | 单类别主模型中将一个目标存在概率映射成d维上下文 | `Object head → Context embedding → z` |

因此，**g与z共用汇总描述h，但使用独立预测头；α不是仅从同一份h中分出的一路。** 模态评分需要保留各模态自身的t/c/u，以及shared表征偏离跨模态均值的程度。α是学习到的相对贡献，不是有直接可靠性真值监督的校准概率；图内优先使用`Modality contribution`。

推荐接线：

```text
c/u ── modality pooling + concat ── h ─┬─ foreground head + sigmoid ── g
                                      └─ object head + embedding ──── z

t_m,c_m,u_m,|c_m−mean(c)| ── scoring heads ── softmax ── α
                                                       │
g ─────────────────────────────────────────────────────┴─ scaling ── w
```

后续g同时接到表征残差、模态缩放、g×z三个位置；w接token调制的最终乘法；g×z分别经β、γ进入query及output加法节点。原始t必须有通往模态评分分支的连线，不能只画c/u进入一个Pool+Concat后直接输出全部信号。图中只保留短标签及少量算子符号，上述详细公式放正文。

单类别K-Radar主模型的z来源应画成`object probability → embedding`；不能画成丰富类别语义或物体级query。多类别适配可将该概率替换为类别概率向量，见方法附录。

代码依据：[gate及模态评分](../../models/fuser/patch_dec_a2_fusion.py:566)、[object context](../../models/fuser/patch_dec_a2_fusion.py:814)、[受控token](../../models/fuser/patch_dec_a2_fusion.py:869)。本节更新手工绘图规范，已有PNG未在此次说明中重新生成。

## 查询和输出的准确读法

| 标记 | 含义 | 去向 |
|---|---|---|
| Q | 在不同patch间复用的可学习特征查询 | 与beta缩放的门控上下文相加 |
| Q′ | 加入当前patch目标相关上下文后的查询 | 注意力的Q输入 |
| K,V | 各模态受控token沿传感器维堆叠 | 注意力的K/V输入 |
| F | 以query为索引、从多模态V汇总得到的融合特征 | 与gamma缩放的门控上下文相加 |
| F′ | 加入输出上下文残差后的融合特征 | PFT及空间重组，再到检测头 |

Q不是逐目标检测query；F可理解为更新后的query特征，但不能与原始Q混为一谈。门控上下文先由g与z相乘得到，再分别送往两个加法节点；Q本身只进入查询侧加法，不进入输出上下文分支。

## 中英文图注

**中文。** ObjDec架构概览。居中的实线展示从空间对应的多模态patch token到三维检测输出的主前向路径。各模态的同一个输入token通过独立的共享与模态特有映射生成两类表征，并据此预测前景门控、模态贡献和目标上下文。Token modulation以门控表征残差和有界模态缩放更新输入；灰色虚线连接其展开计算，同名端口表示相同信号。可学习查询Q经门控目标上下文调制成为Q′，以受控模态token作为K/V，形成融合输出F。再次注入门控上下文后得到F′，随后通过PFT与空间重组形成BEV特征并完成检测。红色虚线仅表示训练监督，GT不参与推理。图中省略继承的传感器组合训练支路，具体设置见附录。

**English.** Overview of ObjDec. The centered solid path connects spatially corresponding multimodal patch tokens to 3D detections. Independent shared and modality-specific mappings transform the same input token of each modality into two representations, which support foreground gating, modality contribution prediction, and object context. Token modulation updates the inputs through a gated representation residual and bounded modality scaling. Grey dashed lines link this module to its expanded computation; repeated ports denote the same signals. Learned queries Q are modulated by gated object context to form Q′, which reads controlled modality tokens as K/V and produces fused features F. An additional context residual yields F′ before PFT, spatial reassembly, and detection. Red dashed connections indicate training supervision only; ground-truth annotations are not used at inference. The inherited sensor-combination training branch is omitted for clarity and documented in the appendix.

## 手工定稿时的细节

- 保留中心主线及上下分工，避免将解耦预测分支误当成主特征流。
- 生成图的上下标仍有简写，正式稿统一为正文的`t_m^p, c_m^p, u_m^p`等。
- 右上context输出分叉处仍有一个多余的小箭头尖。手工稿应删除，改为标准分叉点：乘法输出分别指向查询加法与输出加法，不能指回乘法节点。两个下游终点方向已明确。
- 共享／特有分支入口可合并为一条清晰的输入分叉线，去掉生成图重复的短线，表示同一token经过两个独立映射。
- 主线粗实线、控制连线细实线、展开关系灰虚线、训练监督红虚线。正式图的粗细和箭头尺寸统一。

## 提示词记录

依次为[居中布局](centered_revision_prompt.txt)、[主链路核查](centered_wiring_refinement_prompt.txt)、[查询修正](centered_query_correction_prompt.txt)、[查询局部接线](centered_local_query_wiring_prompt.txt)、[context分叉](centered_context_fork_prompt.txt)。推荐PNG是本轮最后输出；`objdec_architecture_centered_v1.png`至`v4.png`为过程稿，部分接线错误已由后续稿修订。
