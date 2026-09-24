# ObjDec PCA 改图与全测试集分天气统计

更新日期：2026-09-19。

**完成更新（2026-09-19 中午）：** 全量统计已于 03:39 完成，覆盖 10,065 帧、51 个序列、642,649 个前景 patch 位置。全量绘图、定量结果及正文 / 附录安排见 [全量结果与可视化说明](objdec_fulltest_weather_visualization_review_260919.md)。下文第 2 节保留启动时的设置记录，不代表任务仍在运行。

## 1. 已完成的散点图

现有 168 帧导出已重新绘图，原图和原始数据均保留。新图仍是每种天气 24 帧的散点展示，**不是全测试集均值结果**。

- 正文六宫格：正常天气 / 大雪 × 输入、共享、模态特有表征。
  - [PNG 预览](../analysis_exports/objdec_pca_redesign_260919/objdec_pca_normal_heavysnow.png)
  - [PDF 矢量图](../analysis_exports/objdec_pca_redesign_260919/objdec_pca_normal_heavysnow.pdf)
  - [SVG 可编辑图](../analysis_exports/objdec_pca_redesign_260919/objdec_pca_normal_heavysnow.svg)
- [附录七种天气 PDF](../analysis_exports/objdec_pca_redesign_260919/objdec_pca_all_weather_appendix.pdf)
- [采样集高维相似度 CSV](../analysis_exports/objdec_pca_redesign_260919/sampled_high_dimensional_cosine.csv)
- [绘图来源与参数](../analysis_exports/objdec_pca_redesign_260919/plot_manifest.json)

具体调整：

1. 相机：橙色圆点；LiDAR：蓝色三角；4D 雷达：紫色方块。
2. 散点面积从旧图的 5 调整为 24；每帧最多展示 6 个前景 patch，normal 和 heavysnow 各显示 144 个位置 / 模态。
3. 相同 `(frame, patch)` 在三模态、三种表征中严格对应，随机种子固定。
4. 大号深色描边标记表示帧等权中心；密度轮廓约包围 80% KDE 概率质量，不是置信区间。近退化分布不强行拟合轮廓。
5. 各列内天气共用坐标范围，保留全部相关前景点的范围，不以分位数裁掉离群点。
6. 标注 PC1、PC2 解释方差。沿用旧数据的 PCA 坐标，不旋转或重新拟合来改变视觉结论。

解释边界：原 PCA 对每种表征独立拟合，拟合样本包含前景与已采样背景；不同天气共用同一列的投影。各列特征尺度不同，不能直接将列间距离比当作定量解耦收益。相机点高度重叠是数据本身的现象，没有添加抖动来人为展开。

### 图注草稿

**中文：** 不同天气条件下的前景表征可视化。两行分别对应正常天气和大雪，三列分别展示输入、共享及模态特有表征。颜色和标记形状区分相机、LiDAR 与四维雷达。同一组前景 patch 在各模态及表征之间对应，各天气在同一表征空间内使用固定 PCA 投影和坐标范围。大号描边标记表示对帧等权的分布中心，细线表示密度轮廓。每种天气包含 24 帧；该图用于展示采样表征的几何结构，全测试集统计另行报告。

**English:** Foreground representation visualizations under normal and heavy-snow conditions. Columns show input, shared, and modality-specific representations. Colors and marker shapes identify camera, LiDAR, and 4D radar features. The same foreground patch locations are sampled across modalities and representations. Weather groups share a fixed PCA projection and axis limits within each representation space. Large outlined markers denote frame-balanced centers, and thin curves indicate density contours. Each weather group contains 24 frames; full-test statistics are reported separately.

## 2. 全测试集均值统计已启动

- 启动：2026-09-19 01:12:09 +08:00；物理 GPU0；PID `62013`。
- 范围：K-Radar v1 正式测试集全部 **10,065 帧**，保留全部七种天气。
- 模型：正式 v1 ObjDec 对应的历史工程 checkpoint：
  `logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`。
- 配置、权重、运行脚本指纹见输出目录中的 `manifest.json`。
- FP32、batch=1、2 个数据加载 worker；PyTorch 显存上限设置为整卡的 28%。七天气小测峰值 allocated 约 1,006 MiB，该数值不包括 CUDA 上下文及缓存。
- 运行目录：`analysis_exports/objdec_fulltest_weather_260919/`。
- 实时状态：`status.json`；实时日志：`run.log`。

```bash
tail -f /home/hongsheng/dec_con_asf/analysis_exports/objdec_fulltest_weather_260919/run.log
```

### 统计定义

1. 使用原模型定义的 GT 前景 patch 掩码（含配置中的 margin）划分分析区域，GT 不参与推理特征的修改。
2. 每帧、每种模态、每类表征，使用**全部前景 patch**计算 256 维均值，不再限于原导出的最多 36 个前景 patch。
3. 按天气对有效帧均值等权平均。没有前景 patch 的帧照常处理、记录数量，但不将其作为零向量混入前景均值。
4. 同时保留逐帧跨模态余弦相似度、前景 patch 内离散度、向量范数、前景/背景 gate 及模态权重等小型统计。
5. 附带 patch 等权和序列等权的相似度统计，检查目标数量和连续帧占比对结论的影响。
6. 帧均值图的 PCA 在全量有效帧均值上拟合，每种天气、天气内每帧及每模态分别等权。同一表征使用一个固定投影；这与上面的 patch 级散点图是不同分析，不直接比较两者坐标。

### 自动生成的最终文件

只有 `status.json` 为 `complete` 后，下列全量结果才可作为完整测试集结果引用：

- `weather_statistics.csv`：各天气样本数、序列数、前景 patch 数及原始高维相似度。
- `objdec_fulltest_weather_frame_means.png/.pdf/.svg`：正常天气与大雪的帧均值分布、完整样本中心及中心移动箭头。
- `frame_mean_pca_basis.npz`：固定投影基、中心化均值与解释方差。
- `analysis.md`：完整统计和解释说明。
- `chunks/frames_*.npz`：每 100 帧保存一次均值和小型统计，供复查与恢复。

磁盘策略：不保存全测试集 patch 特征、检测框、原始传感器数据或新权重。10,065 帧的核心均值数组未压缩约 88.5 MiB，落盘使用压缩 NPZ；图像和统计表另占少量空间。散点新版全部输出约 4 MiB。

## 3. 已完成的验证

- 七种天气各一帧的完整加载、推理、统计与绘图通过。
- 在第一帧上比较有无统计 hook 的检测框、分数和类别，最大差值均为 **0**。
- 在旧导出已覆盖全部前景 patch 的五个可对齐样本上，逐模态、逐表征核对均值，最大绝对差约 **2.86e-6**。
- 首次小测在结果已全部写出后触发旧 CUDA 扩展的解释器退出错误；已沿用原导出脚本的成功后显式退出方式处理。第二次 `smoke_verified` 正常退出，exit code=0。
- 未修改网络、训练配置、checkpoint 或已有实验进程。

全量推理完成前，24 帧采样图中的差异仍只是初步观察；天气与场景/序列相关，不把观测差异写成天气的因果效应。
