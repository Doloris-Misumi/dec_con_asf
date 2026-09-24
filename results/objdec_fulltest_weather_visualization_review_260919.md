# ObjDec 全测试集表征统计与分天气可视化

日期：2026-09-19。来源：`analysis_exports/objdec_fulltest_weather_260919/`。统计已于当天 03:39:01 完成；本次仅在 CPU 上读取现有统计绘图，没有重新跑 GPU 推理。

## 1. 覆盖范围与统计单位

- K-Radar v1 全测试集 **10,065 帧、51 个序列、642,649 个前景空间 patch 位置**；全部帧均有有效前景。
- 使用正式 v1 ObjDec 的历史 `TaskDecControlRobust_v1_0` checkpoint；权重、配置与导出脚本指纹见源目录的 `manifest.json`。
- 每帧对全部 GT 前景 patch 计算 256 维特征均值，按天气汇总时每帧等权。GT 仅用于分析区域划分，不进入推理特征计算。
- 跨模态余弦先在相同位置的前景 patch 上计算，再按帧、天气平均；不是先求天气均值再计算余弦。
- 正常天气 4,309 帧、大雪 1,098 帧；其余五种天气也全部参与全量统计与固定 PCA 基的拟合。
- 已验证导出帧索引恰好覆盖 0–10,064，无重复或漏帧。原始压缩统计约 85.5 MiB；本次仅新增小型图表、CSV 与质心数组。

## 2. 全量结果

以下为三种模态对（C–L、C–R、L–R）的平均原始 256 维余弦相似度。

| 天气 | 帧数 | 序列数 | Input | Common | Unique |
|---|---:|---:|---:|---:|---:|
| Normal | 4,309 | 17 | 0.0030 | 0.9553 | 0.4462 |
| Overcast | 383 | 2 | 0.0055 | 0.9590 | 0.4941 |
| Fog | 1,049 | 6 | 0.0012 | 0.9514 | 0.5281 |
| Rain | 1,317 | 8 | -0.0008 | 0.9528 | 0.4711 |
| Sleet | 1,106 | 7 | 0.0055 | 0.9566 | 0.5494 |
| Light snow | 803 | 4 | -0.0063 | 0.9558 | 0.5340 |
| Heavy snow | 1,098 | 7 | -0.0016 | 0.9536 | 0.5368 |

天气组的帧数和序列数不同；连续帧也不应被当作相互独立的重复实验。

**可支持的表述：** 在全部七种天气中，common 的跨模态一致性均较高（平均余弦 0.951–0.959），unique 的跨模态相似度则明显更低（0.446–0.549），与两类表征的设计目标一致。

**不能据此单独推出：** 已严格分离真实语义因素、模型完全不受天气影响，或检测增益必然由该几何结构导致。高余弦也可能受公共方向或低方差影响，需要结合消融和检测结果说明作用。

正常天气与大雪的对比还显示：

| 模态 | common 天气质心余弦 | unique 天气质心余弦 | unique 帧均值 RMS 离散度：正常 → 大雪 |
|---|---:|---:|---:|
| Camera | ≈1.000000 | ≈0.999999 | 0.126 → 0.145 |
| LiDAR | 0.999435 | 0.943053 | 2.652 → 6.994 |
| 4D Radar | 0.999747 | 0.999786 | 2.007 → 2.832 |

此处“天气质心余弦”是同一模态正常 / 大雪两个 256 维均值之间的相似度，与前表的跨模态 patch 余弦不同。最明显的天气组间变化出现在 **LiDAR unique 的质心和离散范围**。相机 common / unique 的变化本来就很小，不添加抖动将其人为画散，也不能仅以“小变化”证明其学到了有用的不变性。

天气与序列、场景、目标组成相关，这些结果是组间观察。以序列等权重新汇总时，unique 的正常 / 大雪平均跨模态相似度约为 0.440 / 0.584（帧等权为 0.446 / 0.537）；common 一致性较高的结论保持，但 unique 的精确天气差值依赖汇总权重，不宜给出天气因果解释。

## 3. 本次图稿与排版建议

### A. 正常 / 大雪的帧均值 PCA 六宫格

- [PNG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_frame_pca_normal_heavysnow.png)
- [PDF](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_frame_pca_normal_heavysnow.pdf)
- [SVG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_frame_pca_normal_heavysnow.svg)

**后续更新：** 已将天气与帧数改为每行左侧的横排标注，并新增完整七种天气版本（Normal / Overcast / Fog / Rain / Sleet / Light snow / Heavy snow）。

- [七天气 PNG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_frame_pca_all_weather.png)
- [七天气 PDF](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_frame_pca_all_weather.pdf)
- [七天气 SVG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_frame_pca_all_weather.svg)

七天气图每组最多展示 400 帧；Overcast 共 383 帧，全部显示。正常 / 大雪的显示帧与原六宫格保持一致，所有中心和统计使用各天气全部有效帧。七天气同列共用固定投影与坐标范围，范围包含全部七天气；因此范围可能比六宫格略大，但没有改变投影或数据。

两行对应正常 / 大雪，三列对应 Input / Shared / Modality-specific。橙色圆点为相机、蓝色三角为 LiDAR、紫色方块为雷达。每种天气固定随机展示 400 帧，三模态和三类表征使用相同帧；大号描边质心及密度轮廓使用该天气全部帧。使用 400 点只是显示抽样，统计范围仍是完整测试集。

沿用全量均值的固定 PCA 基，各天气同列共用投影与坐标范围。每类表征分别拟合；拟合时对天气、天气内帧、模态等权。PC1+PC2 解释方差分别为 Input 93.92%、Common 90.75%、Unique 96.31%。不做分位数裁剪，也不为了增强视觉效果旋转或重拟合投影。

**这张图比较适合分析天气间的分布变化。** 它是“帧均值 PCA”，每点不再是一个局部 patch，不能把旧的 24 帧 patch 散点图图注直接沿用。common 的三模态在该二维投影中仍有分离：PCA 中心化去除了整体公共方向后会突出残余差异，与原始向量余弦很高并不矛盾。不能写成“三种 common 在图上完全重合”。

### B. 七种天气 × 三种模态对的高维余弦热图

- [PNG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_weather_cosine_pairs.png)
- [PDF](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_weather_cosine_pairs.pdf)
- [SVG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_weather_cosine_pairs.svg)

三组热图展示 Input / Shared / Modality-specific，各组列为 C–L、C–R、L–R。统一色标 [-1, 1]，完整列出各天气帧数和数值。

**推荐作为正文表征分析的定量配图**，与 PCA 共同使用：PCA 展示分布，热图显示原始 256 维空间中 common / unique 的差异。如版面有限，正文可仅保留 Shared / Modality-specific 两组，完整 Input 和天气细节放附录。不要为各组使用独立色标来放大差异。

### C. 正常 → 大雪的质心变化热图

- [PNG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_normal_snow_centroid_shift.png)
- [PDF](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_normal_snow_centroid_shift.pdf)
- [SVG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_normal_snow_centroid_shift.svg)

在原始 256 维空间计算 `100 × (1 − cosine)`，避免直接比较不同表征空间的未归一化 L2 距离。LiDAR unique 为 5.695，common 为 0.057。建议放附录用于解释 A 中的观察，不必在正文再增加一张独立图。

论文组织建议：正文保留表征几何图并配全量高维统计；如果强调局部 patch 机制，旧 patch 级图仍有用途，但明确其采样范围。A 可作为全量天气分析图移至附录，B 提供正文所需的全量支撑，C 与均值 / 方差细节放附录。不要把 patch 级图与帧均值图当作相同统计单位混排。

## 4. 可直接改用的图注

**A 中文：** 不同天气下的前景帧均值表征。每帧特征由该帧全部前景 patch 平均得到；正常天气和大雪分别包含 4,309 和 1,098 帧。每类表征在全测试集帧均值上使用按天气与模态平衡的固定 PCA 投影，同列天气共享坐标范围。为提高可读性，每种天气展示 400 个随机帧；大号描边标记和密度轮廓使用全部帧计算。轮廓近似表示 80% KDE 概率质量，不是置信区间。

**A English:** Foreground frame-mean representations under normal and heavy-snow conditions. Each vector averages all foreground patches within a frame. The two groups contain 4,309 and 1,098 frames, respectively. Each representation uses a fixed PCA projection fitted to full-test frame means with balanced weather and modality weights; axis limits are shared across weather groups within each column. We display 400 randomly sampled frames per group for readability, while outlined centers and density contours use all frames. Contours approximate 80% KDE probability mass and are not confidence intervals.

**B 中文：** 全测试集分天气跨模态相似度。对同一前景位置的相机、LiDAR 和四维雷达特征在原始 256 维空间中计算余弦相似度，先对每帧全部前景位置平均，再对各天气的帧等权平均。括号标注帧数，三组图共用色标。所有天气中，共享表征表现出较高的跨模态一致性，模态特有表征保持较低的跨模态相似度。

**B English:** Cross-modal similarity across weather conditions on the full test set. Cosine similarity is computed in the original 256-dimensional space between modalities at matched foreground patch locations, averaged within each frame, and then averaged equally over frames in each weather group. Parentheses indicate frame counts, and all panels share the same color scale. Shared representations exhibit high cross-modal consistency across all weather groups, whereas modality-specific representations retain lower cross-modal similarity.

绘图脚本：[plot_objdec_fulltest_weather_260919.py](../tools/analysis/plot_objdec_fulltest_weather_260919.py)。抽样帧编号、CSV、质心数组及来源指纹均保存于 `paper_visuals/`，无需再次导出全量特征。

## 5. 为什么旧图中的 Shared L / R 更接近，新图看起来分开了？

两张图的分析对象与投影不同，不能将图面距离直接当作模型对齐强弱的变化。

1. **点代表的东西变了。** 旧图每点是一个前景 patch，展示局部位置间的差异；新图每点是一帧全部前景 patch 的平均，展示场景摘要之间的差异。平均会减少局部波动，让模态间残余的均值偏差更显眼；平均本身不意味着将两个模态的中心推远。
2. **PCA 的观察方向变了。** 旧 PCA 在采样前景 + 背景 patch 上拟合；新 PCA 在全测试集前景帧均值上按天气、模态平衡拟合。两者寻找的主要变化方向不同，就像同一对物体从不同方向投影，二维间距会变。这里不是在同一个投影里简单增加了样本。
3. **坐标范围也变了。** 旧 Shared 图有更大的局部散布和较宽坐标范围，新图对较小的残余差异显示得更清楚。论文不能根据屏幕上的厘米距离直接比较两图。

直接比较原始 256 维空间中对应前景位置的 L–R shared 余弦：

| 天气 | 旧 24 帧采样 | 全测试集 |
|---|---:|---:|
| Normal | 0.962366 | 0.962080 |
| Heavy snow | 0.956981 | 0.960135 |

两者都在 0.96 左右，不支持“全量图显示 shared 对齐变差”的判断。Shared 要求跨模态一致性，并不要求所有特征分量完全相同；高余弦与仍存在模态偏差可以同时成立。图中 L / R 点云方向相近也不等于逐帧相关性，后者需使用匹配帧的统计来判断。

额外核查保持**同一份旧采样的 L / R 前景帧均值中心**不变，仅替换 PCA 投影：

| 天气 | 原始 256D 中心距离 | 旧投影的二维距离 | 新投影的二维距离 |
|---|---:|---:|---:|
| Normal | 4.0103 | 2.8564 | 3.9867 |
| Heavy snow | 3.5970 | 1.9882 | 3.4345 |

这说明只换观察方向就足以让同一对中心在二维图上更分开。原 PCA 轴由保存的原特征和 PCA 坐标重建，坐标重建最大误差小于 1e-6；新投影直接读取固定基文件。记录见 [投影核查 JSON](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/pca_projection_comparison.json)。这些距离用于核对投影变化，不是新的模型性能指标。

建议论文表述为：共享表征在完整高维空间中具有较高的跨模态一致性，帧均值 PCA 同时显示仍存在模态相关的残余结构；不能将旧图的投影接近写成“完全实现语义对齐”。

## 6. 直接展示高维相似度：矩阵与分布图

这两种图直接使用原始 256 维向量计算的余弦相似度，不依赖 PCA 的投影方向。没有重新进行 GPU 推理。

### D. 跨模态相似度矩阵

- [PNG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_matrices.png)
- [PDF](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_matrices.pdf)
- [SVG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_matrices.svg)

每个 3×3 方阵的行列均为相机、LiDAR、4D Radar；每个非对角格子表示一对模态在匹配前景空间位置上的余弦相似度。统计先在帧内对前景位置平均，再在天气内按帧等权平均。对角线的自比较省略；上下三角对称，重复数值不是不同证据。所有方阵使用相同的 [-1, 1] 色标。

两行是正常天气与大雪，三列是 Input / Shared / Modality-specific。相对 PCA，这张图可以直接读出“Shared 的 L–R 相似度约 0.96”；颜色仅编码数值，不涉及二维空间距离的解释。

### E. 相似度分布图

- [PNG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_distributions.png)
- [PDF](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_distributions.pdf)
- [SVG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_distributions.svg)

三列依次对应 C–L / C–R / L–R；每个面板比较 Input、Shared、Specific 的逐帧相似度分布。绿色 Shared 的分布集中于较高数值，黄色 Specific 较低；其中涉及 LiDAR 的 Specific 分布在大雪组更宽。

每个观测值是**一帧内部全部匹配前景 patch 的平均余弦**，不是“帧均值向量的余弦”，也不是所有单个 patch 余弦的分布。使用全部帧，不做显示抽样。小提琴表示密度，粗线为 25–75% 分位范围，细线为 5–95% 分位范围，白点为中位数；这些是描述性分布，不是置信区间。

| 天气 | L–R Shared 中位数 | Shared 5–95% 分位 | L–R Unique 中位数 | Unique 5–95% 分位 |
|---|---:|---|---:|---|
| Normal | 0.9632 | 0.9433–0.9776 | 0.3384 | 0.2113–0.4948 |
| Heavy snow | 0.9662 | 0.9141–0.9806 | 0.4538 | 0.2578–0.7363 |

它比只展示均值多回答一个问题：高相似度在多数帧中是否都存在。当前结果显示 L–R Shared 的高相似度分布于多数帧，并非由少数高值帧拉高均值。

**正文选择：** D 适合快速说明三模态的一致性关系；E 适合强调各帧的一致性和天气下的变化范围。二者择一配合 PCA 即可，无需将矩阵、分布图、原七天气热图全部堆进正文。全部七天气的分位统计见 `direct_similarity_distribution_statistics.csv`。

**解释边界：** 余弦衡量方向相似度，高相似度本身不能排除公共偏置或表征坍塌，也不等价于检测语义一致。若进一步验证表征是否保留位置区分能力，可另做“匹配前景位置 vs 打乱前景位置”的相似度对照；当前这两张图没有实施该对照，不能据此报告位置判别性结论。

**D English caption:** Cross-modal cosine similarity in the original 256-dimensional feature space. Rows show normal and heavy-snow conditions, and columns show input, shared, and modality-specific representations. Each off-diagonal entry averages cosine similarity at matched foreground patch locations within a frame, followed by an equal-weight average over frames in the weather group. Self-comparisons are omitted, and all panels use the same color scale.

**E English caption:** Distributions of per-frame cross-modal similarity. For each modality pair, we compute cosine similarity in the original 256-dimensional space at matched foreground patch locations and average within each frame. All 4,309 normal-weather frames and 1,098 heavy-snow frames are included. White markers denote medians, thick bars the interquartile range, and thin bars the 5th–95th percentiles. The plots describe variation across frames and do not represent confidence intervals.

绘图脚本：[plot_objdec_direct_similarity_260919.py](../tools/analysis/plot_objdec_direct_similarity_260919.py)。来源哈希及统计口径见 `paper_visuals/direct_similarity_manifest.json`。
