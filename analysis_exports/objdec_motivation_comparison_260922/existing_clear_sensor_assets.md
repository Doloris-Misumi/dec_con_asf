# 已找到的清晰三模态素材

2026-09-22。本轮查找用户所示“相机照片 + 高对比度 LiDAR 空间点云 + 扇形雷达热图”素材，未改动最终动机图或实验。

素材目录：`/home/hongsheng/figure/motivation_samples/`。

| 场景 | 同步索引（seq / radar / LiDAR / camera） | 三联图 |
|---|---|---|
| Normal | 14 / 00182 / 00149 / 00444 | [combined.png](/home/hongsheng/figure/motivation_samples/14_00182_00149/combined.png) |
| Rain | 32 / 00155 / 00150 / 00450 | [combinedr.png](/home/hongsheng/figure/motivation_samples/32_00155_00150/combinedr.png) |
| Heavy snow | 55 / 00129 / 00124 / 00351 | [combinedhs.png](/home/hongsheng/figure/motivation_samples/55_00129_00124/combinedhs.png) |

三个目录分别含 `image.png`（640×360）、`lidar.png`（560×560）、`radar.png`（560×560）。根目录另有 normal/rain/heavysnow 的单张图、透明底和三联图。

## 本次核实范围

- 同步索引来自本地 K-Radar info_label 文件头；天气来自 description.txt。
- 三张相机素材均与各自原始 stereo 相机照片的 front0 左半幅缩小到640×360完全一致，逐像素平均绝对差为0。
- LiDAR与雷达为已有渲染素材。已查看其形态和尺寸，但没有找到这批素材的生成脚本，尚未逐项复核点云／热图与原始数值的对应关系，不能把目录命名视为完整数值审计。
- seq14和seq32上述帧的v1标签只有文件头，没有该协议的目标标注；不宜直接替换输入后继续配原seq13的预测图。

## 对新版图的启示

前一版采用相机视角的点云投影，缩小后密集点挤在一起、空间结构不突出。用户希望的是空间点云视图和扇形功率图，关键在显示方式，并非要求将模糊的原始照片增强。

Normal组最适合参考无天气强调的输入表现；Heavy snow组更接近用户示例的斑点状扇形热图，但不应因此把ObjDec动机改成天气鲁棒性。

若继续修订完整动机图，优先对有车且有现成真实预测的seq13/radar00146重做空间点云与扇形功率显示，使输入与输出仍同帧。雷达若从稀疏xyz-power数据聚合，应在来源记录中明确，不写成原始完整range-azimuth张量。
