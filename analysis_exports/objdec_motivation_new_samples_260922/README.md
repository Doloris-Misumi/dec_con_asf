# ObjDec 动机图：四组替换样本与新版成图

日期：2026-09-22。

这次重新选择了四组用于动机图的 K-Radar 样本，没有沿用上一版 seq13 / radar 00146，也避开了旧 WCBR 素材中的 seq14 / 00182、seq32 / 00155、seq55 / 00129。这里“新选”指本次动机图替换，部分帧此前已用于项目的定性分析并保存了预测。

推荐先看 [四组素材总览](new_sample_candidates.png)。每行从左到右是相机、LiDAR、雷达、真实 ObjDec 输出。每个场景都已做成同样版式的完整动机图。

| 场景 | 同步编号：sequence / radar / LiDAR / camera | 显示的预测数 | 完整动机图 |
| --- | --- | ---: | --- |
| 阴天车流，推荐主版 | 22 / 00484 / 00482 / 01445 | 4 | [PNG](objdec_motivation_seq22_rdr00484.png) · [PDF](objdec_motivation_seq22_rdr00484.pdf) · [SVG](objdec_motivation_seq22_rdr00484.svg) |
| 晴天道路，画面更清楚 | 20 / 00628 / 00595 / 01783 | 1 | [PNG](objdec_motivation_seq20_rdr00628.png) · [PDF](objdec_motivation_seq20_rdr00628.pdf) · [SVG](objdec_motivation_seq20_rdr00628.svg) |
| 日间公路，右侧近车 | 9 / 00347 / 00324 / 00969 | 3 | [PNG](objdec_motivation_seq9_rdr00347.png) · [PDF](objdec_motivation_seq9_rdr00347.pdf) · [SVG](objdec_motivation_seq9_rdr00347.svg) |
| 夜间街道，近处车辆 | 7 / 00272 / 00239 / 00718 | 1 | [PNG](objdec_motivation_seq7_rdr00272.png) · [PDF](objdec_motivation_seq7_rdr00272.pdf) · [SVG](objdec_motivation_seq7_rdr00272.svg) |

主版选择 seq22 是因为同帧前方车辆及多个预测框相对容易辨认；seq20 的图像清晰度更好，但保留的预测位于远处，完整画面下框较小。seq9 的近处框被相机视野裁切，seq7 只保留一项超过阈值的预测，因此它们适合备选。没有修改模型输出以让任何场景看起来更好。

## 这次修改

- 相机改为完整 front0 前视画面，照片直接嵌入 SVG；没有生成、增强、去雾或补画。
- LiDAR 改为黑底白色空间点云，使用固定的斜俯视正交投影，不再投到相机平面。全部保留显示 ROI 中的点，没有改变空间结构。
- 雷达改为扇形功率图。它来自本地 `sprdr_*.npy` 的稀疏 xyz-power 数据，在距离／方位角显示网格内做最大功率聚合；**不是原始稠密 range–azimuth 谱**。空网格用深紫色表示，没有插值补成观测。
- 输出图放大，使用同帧既有 ObjDec 预测；全部保留 `label == Sedan` 且 `score > 0.3` 的框。没有以 GT 替代预测，没有选择性删框。
- 维持一个输入 token 分别进入两个独立投影的结构；shared 与 unique 没有串联箭头，原始输入保留旁路。
- 将训练标注收简为 “Object-region supervision (training only)”，避免动机图中出现容易误读的复杂损失连线。
- 中栏仍解释“背景也可能一致、目标也可能存在有效差异”；不把天气作为主线。中栏向量条与右栏控制图标为示意，不是由相机裁切估计出的真实特征响应。

四组共用相同的点云显示范围、视角、雷达分箱及色标。没有做跨天气性能比较，也不将色彩强弱解释为跨天气可靠性结论。

## 图注：中文

**图 1：ObjDec 的设计动机。**（a）所参考的融合方法通过特征交互与自适应加权利用多传感器观测，但共享与模态特有信息的表征角色通常未被显式区分。（b）跨模态共同响应可能来自背景，而模态差异也可能包含描述同一目标的互补线索，因此一致性本身不足以确定目标相关性。（c）ObjDec 将各模态的同一个局部输入 token 经两个独立投影映射为共享与模态特有表征，通过目标区域内的训练监督组织两类表征，并使其引导前景相关性、模态贡献与目标上下文的建模，进而调制融合。原始输入保留残差路径，目标标注仅用于训练。图中相机照片、LiDAR 点云、雷达功率与橙色预测框均来自同一 K-Radar 样本（seq22 / radar 00484）；预测框为 ObjDec 在 score > 0.3 下保留的全部 Sedan 输出。LiDAR 采用斜俯视显示，雷达扇形图由稀疏 xyz-power 聚合得到；表征和控制图标为机制示意。

## Caption: English

**Figure 1: Motivation for ObjDec.** (a) Representative fusion approaches combine sensor observations through feature interaction and adaptive weighting, while the representational roles of shared and modality-specific information often remain implicit. (b) Cross-modal agreement may originate from background, whereas modality-specific differences may provide complementary descriptions of the same object. Agreement alone therefore does not determine object relevance. (c) ObjDec maps each modality's local input token into shared and modality-specific representations through two independent projections. Object-region training supervision organizes these representations, which guide foreground relevance, modality contributions, and object context to modulate fusion while retaining a residual input path. Ground-truth annotations are used only during training. Camera, LiDAR, radar, and orange prediction boxes come from the same K-Radar sample (sequence 22, radar frame 00484); all ObjDec Sedan predictions above a score threshold of 0.3 are retained. LiDAR is shown in an oblique view, and the radar fan aggregates sparse xyz-power samples. Representation and control glyphs are schematic.

切换到另一个成图版本时，将图注中的 sequence / radar 编号同步替换。

## 来源与复现

所有素材路径、同步信息、显示 ROI、雷达聚合参数、原始框与分数、文件 SHA-256 均在 [candidates.json](candidates.json) 和各 `samples/<frame>/provenance.json` 中。模型为正式 K-Radar v1 ObjDec Robust，预测缓存来源：

`analysis_exports/objdec_fig4_fig5_260919/paired_predictions/objdec/`

每组 `samples/<frame>/` 提供独立 `camera.png`、`lidar.png`、`radar.png`、`prediction.png`，方便后续手工排版。相机源是 2560×720 双目图片中的 front0 左半幅，成图以原始像素裁切嵌入；雷达源实际解析到该序列的 `sparse_cube/cube_*.npy`。

生成的底图只提供图形、标签和空白素材位；真实数据没有交给图像生成工具重绘。两个表征到融合的短连线为 SVG 矢量图元。SVG 含位图底图和真实素材，并非全部图元可单独编辑的纯矢量文件。内置图像工具没有暴露具体后端型号，因此不据此标称 GPT Image 2.5。

```bash
/home/hongsheng/miniconda3/envs/rl_3dod/bin/python /home/hongsheng/dec_con_asf/analysis_exports/objdec_motivation_new_samples_260922/render_candidates.py
/usr/bin/python3 /home/hongsheng/dec_con_asf/analysis_exports/objdec_motivation_new_samples_260922/assemble_figures.py
```

[validation.json](validation.json) 核验四组的原始数据及预测文件均未变化。本轮仅做 CPU 数值绘图和文档合成，没有启动训练或 GPU 推理。新增文件约 58 MiB。
