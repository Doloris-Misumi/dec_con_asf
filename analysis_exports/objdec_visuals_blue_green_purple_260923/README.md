# ObjDec 可视化统一配色稿（2026-09-23）

按用户指定的2026-09-15主架构参考图，将三模态统一为**Camera蓝、LiDAR绿、4D Radar紫**。本目录从已有数值缓存重新绘图，旧图保留。现稿中PCA编号为Fig.3、空间gate编号为Fig.4；两套相关图均已纳入本次重绘，避免编号调整时漏换配色。

## 配色与数据范围

| 编码对象 | 颜色 | 辅助形状 |
|---|---|---|
| Camera | `#4A9EEB` | 圆点 |
| LiDAR | `#58B77A` | 三角 |
| 4D Radar | `#9672D0` | 方块 |

以上为对参考图蓝／绿／紫的平面印刷色近似，不是对渐变图片的逐像素取色。标签另用同色系稍深颜色。分布图中Input／Shared／Specific是另一种编码，分别用灰／珊瑚红／暖金色，不能把这些列的颜色解释成传感器身份。

PCA坐标、投影基、各天气显示样本、中心与轮廓的统计口径不变。余弦、质心距离和gate是连续量，保留原定量色标；不将连续量也强行改成三种传感器颜色。真实相机图像不改色，LiDAR点云渲染使用绿色。gate保留原始16×90数组、统一[0,1]色标及GT参照。

## 推荐先看

| 用途 | PNG预览 | PDF排版 |
|---|---|---|
| 局部patch PCA：正常／大雪 | [PNG](sampled_patch_pca/objdec_pca_normal_heavysnow.png) | [PDF](sampled_patch_pca/objdec_pca_normal_heavysnow.pdf) |
| 局部patch PCA：七天气 | [PNG](sampled_patch_pca/objdec_pca_all_weather_appendix.png) | [PDF](sampled_patch_pca/objdec_pca_all_weather_appendix.pdf) |
| 全测试集帧均值PCA：正常／大雪 | [PNG](fulltest/objdec_fulltest_frame_pca_normal_heavysnow.png) | [PDF](fulltest/objdec_fulltest_frame_pca_normal_heavysnow.pdf) |
| 全测试集帧均值PCA：七天气 | [PNG](fulltest/objdec_fulltest_frame_pca_all_weather.png) | [PDF](fulltest/objdec_fulltest_frame_pca_all_weather.pdf) |
| 空间gate：七天气 | [PNG](gate/fig4_objdec_all_weather.png) | [PDF](gate/fig4_objdec_all_weather.pdf) |
| 架构图用shared／specific小图 | [正常天气PNG](architecture_insets/architecture_shared_specific_pca_normal.png) | [正常天气PDF](architecture_insets/architecture_shared_specific_pca_normal.pdf) |

每组均另有**同名SVG**，用于编辑标签、图例和矢量元素。相机图像与密集点云作为嵌入位图保留，SVG不等于原始照片变成矢量。

## 完整图稿清单

**`sampled_patch_pca/`：2组。** 正常／大雪、七天气。来源为每种天气24帧的既有局部前景patch导出，共168帧。原有抽样与PCA基不变。

**`fulltest/`：6组。** 全测试集10,065帧，PCA显示每种天气至多400个固定抽取的帧均值；中心与密度轮廓使用全部帧。

- `objdec_fulltest_frame_pca_normal_heavysnow`
- `objdec_fulltest_frame_pca_all_weather`
- `objdec_fulltest_weather_cosine_pairs`
- `objdec_fulltest_normal_snow_centroid_shift`
- `objdec_fulltest_direct_similarity_matrices`
- `objdec_fulltest_direct_similarity_distributions`

直接相似度由原始256维的匹配patch余弦逐帧平均得到，与“帧均值向量的余弦”区分。矩阵的Camera/LiDAR/Radar轴标签采用对应颜色；热图数值色标不变。

**`gate/`：8组。** 原七天气组合图，以及Normal、Overcast、Fog、Rain、Sleet、Light snow、Heavy snow各一组独立PNG/PDF/SVG。文件名为`fig4_objdec_all_weather`与`fig4_<weather>`。沿用原7个样本，没有重新挑选更有利的样本或再次推理。

**`architecture_insets/`：6组。** 正常／大雪各有shared单图、specific单图和两者并排预览。

用于粘贴的正常天气独立素材：

- Shared： [透明PNG](architecture_insets/architecture_common_pca_normal.png) · [SVG](architecture_insets/architecture_common_pca_normal.svg)
- Specific： [透明PNG](architecture_insets/architecture_unique_pca_normal.png) · [SVG](architecture_insets/architecture_unique_pca_normal.svg)

大雪版将文件名中的`normal`换为`heavysnow`。独立素材背景透明，组合预览背景为白色。

## c/u位置如何使用PCA小图

可以替换原来的装饰性token小条来说明两类表征的分布，但不能把PCA画成参与推理的算子。建议保留：

1. 同一个输入token分叉到Shared projection与Specific projection。
2. 两个输出处保留`c_m^p`、`u_m^p`以及指向Pool/Concat的实线箭头，表示传递高维表征。
3. 从输出符号用灰色虚线连接对应PCA小图，标记`PCA visualization`。PCA图本身不再用实线送入Pool/Concat。

本次提供局部patch PCA，更贴近主图的局部token含义；它仍然是多帧、多位置的集合，不是某一个token的内部结构图。全测试集帧均值PCA适合实验章节，不能与局部patch图混称。

原始PCA中相机点分布很窄，共享分支的三种颜色也不是完全重叠。保留这些真实结构；不要移动点云来画成理想化“shared全部重叠”。共享一致性的量化证据应结合原始高维余弦，PCA只展示投影后的分布。两个分支使用独立PCA基，不从跨面板的视觉间距直接计算对齐提升比例。

可加在架构图图注末尾：

**中文：** 共享与模态特有分支旁的小图展示已学习前景patch表征的PCA投影，仅用于可视化，不参与网络前向计算。

**English:** Insets beside the shared and modality-specific branches visualize PCA projections of learned foreground-patch representations; they are for illustration and are not part of the forward computation.

## 核查与复现

脚本：[recolor_objdec_visuals_260923.py](../../tools/analysis/recolor_objdec_visuals_260923.py)。仅CPU绘图，不调用GPU模型、不复制数据集或权重。缓存源文件在绘图前后核对SHA256；新旧显示帧ID逐项比对；三份数值统计CSV与旧版逐字节比对。核查结果见`validation_all.json`，颜色定义见`palette.json`。

```bash
cd /home/hongsheng/dec_con_asf
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 CUDA_VISIBLE_DEVICES='' \
  /home/hongsheng/miniconda3/envs/rl_3dod/bin/python tools/analysis/recolor_objdec_visuals_260923.py
```

Fig.5成对检测图不属于此次三模态配色调整范围。此前的主架构PNG也没有被自动改成新的PCA接线；本目录提供手工重排素材及明确的接线建议。
