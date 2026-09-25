# Fig.4 与附录检测对照：紧凑图稿

2026-09-25生成，2026-09-26更新编排。沿用已有真实场景与推理缓存，只重排图稿，不重新推理。

**当前安排：正文共四张图。** Fig.4用于正文；历史文件名`objdec_fig5_compact.*`保留，但对应图片现放附录E.6，标签为`fig:e-comparison`，不再占正文Fig.5。完整章节、附图和索引见[图件编排](../../results/objdec_figures_main_appendix_plan_260926.md)。

## 文件

| 图 | PDF | SVG | PNG | LaTeX 图环境 |
|---|---|---|---|---|
| Fig.4 | [PDF](objdec_fig4_compact.pdf) | [SVG](objdec_fig4_compact.svg) | [PNG](objdec_fig4_compact.png) | [figure_4.tex](figure_4.tex) |
| Fig.5 | [PDF](objdec_fig5_compact.pdf) | [SVG](objdec_fig5_compact.svg) | [PNG](objdec_fig5_compact.png) | [figure_5.tex](figure_5.tex) |

三行在每列内直接相接，行间距为零，仅用细白边区分相邻面板。顶部统一保留一组列标题、一组框图例；Fig.4另保留统一gate色条。样本编号、天气名称、逐行标题、A/B/C、坐标刻度、均值、IoU、长段说明均不在图内显示。统计值、空间范围及解释移入图注。

相机和所有空间视图保持原始纵横比例；没有为了填满格子拉伸图像或热图。SVG中的文字、框和线条可编辑，照片与热图嵌入为位图。原始图稿未覆盖。

## Fig.4 中文图注

**同场景中的空间门控与检测结果。** 每行依次展示带有ObjDec预测框的相机图（左）、完整LiDAR BEV与预测前景gate（中，上下排列），以及gate局部放大图（右）。橙色实线和绿色虚线分别表示分数大于0.3的预测框及GT参照。相机图仅叠加所选目标的GT，BEV和gate视图保留其显示区域内的全部GT参照；白色点线框标出放大区域。完整BEV范围为前向x∈[0,72] m、横向y∈[-6.4,6.4] m，右侧放大窗口为14×8.4 m，x轴沿水平方向、y轴沿竖直方向。所有gate使用原始0.8 m网格和统一[0,1]色标，不做平滑。从上到下，整帧前景／背景gate均值分别为0.213／0.128、0.259／0.115和0.288／0.118。Gate由输入特征直接预测，GT叠加及区域统计均在预测后进行。Gate用于调制融合，不等同于检测置信度。

## Fig.4 English caption

**Spatial gating and detection in matched scenes.** Each row shows the camera image with ObjDec predictions (left), the full LiDAR BEV and predicted foreground gate (middle, top and bottom), and a magnified gate region (right). Orange solid and green dashed boxes denote predictions with scores above 0.3 and GT references, respectively. Camera panels show the selected target's GT; the BEV and gate panels retain all GT references within their displayed regions. White dotted rectangles mark detail windows. Full BEV views cover x∈[0,72] m and y∈[-6.4,6.4] m; right-hand windows span 14×8.4 m, with forward x horizontal and lateral y vertical. All gates use the native 0.8 m grid and a common [0,1] scale without smoothing. Foreground/background gate means are 0.213/0.128, 0.259/0.115, and 0.288/0.118 from top to bottom. Gates are predicted directly from features; GT overlays and region statistics are added after prediction. Gate values modulate fusion and are distinct from detection confidence.

## 附录E.6（原Fig.5）中文图注

**官方发布ASF权重与ObjDec在相同K-Radar v1测试帧上的定性比较。** 前两列展示检测框的标定相机投影及局部放大，后两列上方为完整LiDAR BEV，下方为对应区域放大。橙色实线为分数大于0.3的Sedan预测框，绿色虚线为GT。两方法使用相同输入、检测后处理、显示阈值及相机／BEV裁剪窗口，白色点线框标出放大区域。完整BEV范围为x∈[0,72] m、y∈[-6.4,6.4] m，每个局部窗口为12×6 m。从上到下，所示GT与保留预测框的最大3D IoU由ASF到ObjDec分别为0.572→0.719、0.000→0.476和0.000→0.741。这些值描述所选目标的框重合度，不是AP；中间案例仍未达到IoU=0.5。附录提供更多候选及反例。

## Appendix E.6 (formerly Fig.5): English caption

**Qualitative comparison of the released ASF checkpoint and ObjDec on identical K-Radar v1 test frames.** The first two columns show calibrated camera projections with enlarged insets; the last two show full LiDAR BEV views above matched detail windows. Orange solid boxes denote Sedan predictions with scores above 0.3; green dashed boxes denote GT. Both methods use identical inputs, detection postprocessing, display thresholds, and camera/BEV crop windows. White dotted rectangles mark the enlarged regions. Full BEV views cover x∈[0,72] m and y∈[-6.4,6.4] m, while each detail window spans 12×6 m. For the highlighted GT, maximum 3D IoU among retained predictions changes from ASF to ObjDec as follows, from top to bottom: 0.572 to 0.719, 0.000 to 0.476, and 0.000 to 0.741. These values describe selected-object box overlap rather than AP; the middle example remains below IoU 0.5. Additional candidates and counterexamples are provided in the appendix.

## 来源与重排细节

- Fig.4沿用9月24日三帧：`seq17_rdr00625`、`seq10_rdr01127`、`seq25_rdr00154`。相机GT覆盖规则、预测框、gate数值及放大范围与旧稿一致。
- Fig.5沿用9月19日三帧：`seq20_rdr00628`、`seq22_rdr00218`、`seq25_rdr00154`。所选目标和全部阈值过滤后的预测框保持一致；逐项核对原推理NPZ。相机放大窗沿用旧稿计算，插图占相机面板的比例由约38%增至45%。
- 为让三行BEV放大图保持等大且无缝排列，Fig.5局部窗口统一为12×6 m，按同一GT位置在原ROI内平移。旧稿第二、三行窗口曾在ROI边界处截短；本版补足窗口尺寸，不拉伸几何。两方法使用完全相同的窗口。
- Fig.4全文空间数组16×90，gate色标[0,1]，最近邻显示。输入图像不提亮、去雾、替换或生成；不改变预测框位置或删掉不利预测。
- `validation_and_provenance.json`保存不可见的样本索引、窗口、统计、原始输入哈希和数值来源；不把追溯信息堆进图内。
- 七天气图和20帧候选保留在原目录，可用于附录。

2026-09-26已同步独立实验章、中英文实验稿和完整LaTeX包：Fig.4为三个场景；七天气gate、原Fig.5及雪天反例放入附录E。完整20帧候选仅作归档。

## CPU 重绘

```bash
cd /home/hongsheng/dec_con_asf
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  /home/hongsheng/miniconda3/envs/rl_3dod/bin/python3.8 \
  analysis_exports/objdec_fig4_fig5_compact_260925/render_compact.py
```
