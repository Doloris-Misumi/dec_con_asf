# Fig.3：正常天气与大雪下的真实表征 PCA

选定原图：`../objdec_visuals_blue_green_purple_260923/fulltest/objdec_fulltest_frame_pca_normal_heavysnow.pdf`。

## 新版文件

- [PDF](objdec_fig3_pca_normal_heavysnow_no_footer.pdf)
- [SVG](objdec_fig3_pca_normal_heavysnow_no_footer.svg)
- [PNG](objdec_fig3_pca_normal_heavysnow_no_footer.png)
- [LaTeX 图环境与英文图注](figure_3.tex)

只删除底部 `Each point: one frame mean ...` 说明，原图保留。特征、PCA 投影基、抽样帧、点的位置、颜色、坐标范围、中心及轮廓计算均沿用原实现。没有重新推理或为了外观重新拟合 PCA。导出时紧裁外边界。

## 图中元素

| 元素 | 含义 |
|---|---|
| Input representations | 输入解耦分支之前的局部 patch token，记为 t。不是原始图像或点云坐标。 |
| Shared representations | Shared 映射产生的共享表征 c。 |
| Modality-specific representations | Specific 映射产生的模态特有表征 u。 |
| 一个小标记 | 一帧、一个模态、一个表征分支的全部 GT 前景 patch 向量先平均，得到 256 维向量，再投影到二维。不是单个目标或单个 patch。 |
| 蓝圆 / 绿三角 / 紫方块 | Camera / LiDAR / 4D Radar。 |
| Normal / Heavy snow | 正常天气 / 大雪样本。不是同一场景施加两种天气。 |
| n = 4,309 / 1,098 | 对应天气在完整 v1 测试集中的帧数。为避免遮挡，散点仅显示各天气固定随机抽取的 400 帧；每个面板为每种模态显示 400 个小标记。 |
| All-frame center | 大号深色描边标记，表示该天气、该模态、该分支的全量帧均值中心。不是仅对显示的 400 帧求中心，也不是三种模态合并成一个中心。 |
| 同色轮廓线 | 用对应全量帧做核密度估计，近似包围 80% 密度质量的等密度轮廓，不是置信区间。分布近乎退化时不画轮廓。 |
| PC1 / PC2 | 第一 / 第二主成分，即保留特征变化最多的两个相互正交的投影方向。数值为中心化特征的投影得分，无米等物理单位；正负号不表示检测好坏。 |
| 坐标轴括号内百分数 | 对应主成分的解释方差比例，不是准确率、模态权重或相似度。 |

每种表征分别使用全测试集 10,065 帧拟合一套 PCA。拟合时七种天气的总权重相等，三种模态的总权重相等，每种天气内各帧权重相等。不进行逐模态中心化或 L2 单位化后再画本图。

| 表征 | PC1 | PC2 | 累计解释方差（由未四舍五入值计算） |
|---|---:|---:|---:|
| Input | 71.7% | 22.3% | 93.9% |
| Shared | 67.2% | 23.6% | 90.8% |
| Specific | 59.0% | 37.3% | 96.3% |

同一列的上下两行共用投影基及坐标范围，可比较该表征的两种天气分布。不同列的投影基和特征尺度不同，不能从图上跨列比较绝对距离或“对齐提升了几倍”。高解释方差不等于证明语义解耦。Shared 的二维分布保留了模态结构；跨模态一致性仍由原始 256 维匹配前景 patch 余弦统计补充，不将此图描述为 Shared 三模态完全重叠。

相机的帧均值变化很小，很多蓝点在投影中相互重叠，并被大号中心标记遮挡；不是只画了一个样本。

## 中文图注

**图 3：K-Radar v1 正常天气与大雪条件下输入、共享及模态特有表征的 PCA 可视化。** 每个小标记对应一帧中某一模态的全部 GT 前景 patch 特征的 256 维均值向量，经 PCA 投影至二维。蓝色圆点、绿色三角和紫色方块分别表示相机、LiDAR 和四维雷达。每种天气随机抽取 400 帧显示散点，并在各列及各模态间使用相同帧；大号描边标记和密度轮廓使用对应天气的全部帧计算（正常天气 4,309 帧，大雪 1,098 帧）。轮廓近似包围 80% 的估计密度质量，近乎退化的分布不绘制轮廓。每类表征在全测试集上独立拟合 PCA，各天气组和各模态的总权重相等；同列两种天气共用投影基与坐标范围。坐标轴括号内为解释方差比例。GT 仅用于选取本分析的前景区域。

## English caption

**PCA visualization of input, shared, and modality-specific representations on K-Radar v1 under normal and heavy-snow conditions.** Each small marker represents the 256-dimensional feature vector averaged over all GT-defined foreground patches of one frame and one modality, projected onto two principal components. Blue circles, green triangles, and purple squares denote camera, LiDAR, and 4D radar, respectively. We display the same 400 randomly sampled frames per weather condition across all columns and modalities. Large outlined markers and density contours are computed using all frames of the corresponding weather group (n = 4,309 and 1,098); contours enclose approximately 80% of the estimated density where estimation is non-degenerate. A separate PCA basis is fitted for each representation using the full test set with equal total weights for weather groups and modalities; both weather rows share that basis and axis limits within each column. Axis percentages indicate explained variance. GT is used only to select regions for this analysis.

## 正文衔接

既然 Fig.3 只选用 PCA，正文介绍高维余弦时应引用附录中的相似度图或数值表，不要将 Fig.3 称为“PCA 与高维相似度组合图”。现有论文工程的 Fig.3 占位图注也应由这里的 PCA 图注替换。

## 重绘

```bash
cd /home/hongsheng/dec_con_asf
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  /home/hongsheng/miniconda3/envs/rl_3dod/bin/python3.8 \
  analysis_exports/objdec_fig3_260925/export_no_footer.py
```

`validation.json` 记录源数据哈希、投影解释方差与抽样帧一致性核查。
