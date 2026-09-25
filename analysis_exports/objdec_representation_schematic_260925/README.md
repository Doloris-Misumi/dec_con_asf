# ObjDec 主图：Shared / Specific 概念示意

两张独立图均为 **宽 4.17 cm × 高 3.2 cm**。无文字、坐标轴、图例或背景框，透明背景，保持相机蓝、LiDAR 绿、雷达紫。

- `objdec_shared_aligned_no_text.svg / .pdf / .png`：每个模态的三个点从左侧独立小簇沿箭头汇聚为右侧紧凑的混合簇；输出每种颜色仍各三个点。该图表示希望学习到的对齐关系，不是 PCA 测量或训练过程记录。
- `objdec_specific_separated_no_text.svg / .pdf / .png`：三个颜色的小簇保持空间分离，每簇仅三个大点。
- `objdec_shared_specific_side_by_side_no_text.*`：无字并排预览，整体宽 8.74 cm × 高 3.2 cm；左为 Shared，右为 Specific。若分别放入两个预留框，使用前两份独立文件。

## 缩印可读性

Shared 输出圆点外径约 **5.16 mm**，Specific 圆点外径约 **5.52 mm**；不透明度 100%。用少量大点、明显留白和汇聚箭头表达区别，取消真实 PCA 中的密集轨迹。

若 56 cm 宽的整图缩至 17.8 cm 宽，独立示意宽约 1.33 cm，Shared / Specific 的大点外径分别约 1.64 / 1.75 mm。数字为该缩放比例下的几何尺寸，不是对所有显示或打印条件的保证。

PPT 优先使用 SVG；直接使用可编辑的圆形和路径元素，无嵌入位图。PDF 为矢量，PNG 为 600 dpi 透明图。两张图按原始尺寸插入预留区域即可。

按作者要求，所有文字留在 PPT 中单独添加。建议文字为 `Shared: aligned` 和 `Specific: separated`，字号与主图其他标签统一。

这些是**机制概念示意**；真实数据的表征结果仍放 Fig.3，并保留 PCA / 相似度分析的统计说明。

重绘脚本：`export_schematics.py`（CPU，使用 rl_3dod 环境中的 Matplotlib）。
