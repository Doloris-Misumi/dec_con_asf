# V2X固定预测误差诊断

1,486帧、11,854个符合Moderate条件的GT。固定score≥0.1，严格IoU 0.7/0.5/0.5。下列为GT加权几何召回，不是AP；不含误检率或官方KITTI逐检测贪心匹配。

| 方法 | 3D召回% | BEV召回% | 3D TP数 |
| --- | ---: | ---: | ---: |
| L4DR | 87.72 | 91.68 | 10398 |
| ObjDec-LR | 88.37 | 92.25 | 10475 |
| ASF-style | 87.84 | 91.68 | 10413 |
| ObjDec CLR | 87.73 | 91.86 | 10399 |

ObjDec-LR较L4DR净多检出77个GT，3D/BEV召回提高0.65/0.57个百分点；三模态ObjDec较ASF-style的3D召回低0.12个百分点、BEV高0.18个百分点。固定阈值召回受置信度标定影响，不应替代完整PR/AP，也不能据此断言模型排序改变。

## 全部分组差值

每个差值为ObjDec减对应基线，单位为百分点。分组从实验前预先固定；点数与距离具有相关性，不能视为相互独立的原因。

| 对比 | 分组 | GT数 | Δ3D召回 | ΔBEV召回 |
| --- | --- | ---: | ---: | ---: |
| ObjDec-LR / L4DR | all | 11854 | +0.65 | +0.57 |
| ObjDec CLR / ASF-style | all | 11854 | -0.12 | +0.18 |
| ObjDec-LR / L4DR | range:0-30 | 4734 | +0.46 | +0.59 |
| ObjDec CLR / ASF-style | range:0-30 | 4734 | -0.51 | -0.46 |
| ObjDec-LR / L4DR | range:30-60 | 5461 | +0.62 | +0.51 |
| ObjDec CLR / ASF-style | range:30-60 | 5461 | -0.24 | +0.04 |
| ObjDec-LR / L4DR | range:60+ | 1659 | +1.27 | +0.66 |
| ObjDec CLR / ASF-style | range:60+ | 1659 | +1.39 | +2.47 |
| ObjDec-LR / L4DR | lidar:0-5 | 170 | +10.59 | +16.47 |
| ObjDec CLR / ASF-style | lidar:0-5 | 170 | -7.65 | -11.76 |
| ObjDec-LR / L4DR | lidar:6-20 | 565 | -1.24 | +0.88 |
| ObjDec CLR / ASF-style | lidar:6-20 | 565 | +3.19 | +2.12 |
| ObjDec-LR / L4DR | lidar:21-100 | 5228 | +0.78 | +0.08 |
| ObjDec CLR / ASF-style | lidar:21-100 | 5228 | +0.54 | +0.82 |
| ObjDec-LR / L4DR | lidar:101+ | 5891 | +0.42 | +0.51 |
| ObjDec CLR / ASF-style | lidar:101+ | 5891 | -0.80 | -0.24 |
| ObjDec-LR / L4DR | radar:0 | 4722 | +0.74 | +0.53 |
| ObjDec CLR / ASF-style | radar:0 | 4722 | +0.55 | +0.85 |
| ObjDec-LR / L4DR | radar:1-5 | 2137 | +1.26 | +1.26 |
| ObjDec CLR / ASF-style | radar:1-5 | 2137 | -0.51 | +0.28 |
| ObjDec-LR / L4DR | radar:6-20 | 1986 | +0.55 | +0.20 |
| ObjDec CLR / ASF-style | radar:6-20 | 1986 | -0.20 | -0.25 |
| ObjDec-LR / L4DR | radar:21+ | 3009 | +0.13 | +0.37 |
| ObjDec CLR / ASF-style | radar:21+ | 3009 | -0.83 | -0.66 |

ObjDec-LR在三个距离段均有3D/BEV召回收益；≥60m的3D收益约1.27个百分点。LiDAR 0–5点组的3D收益约10.59个百分点，但仅170个GT，且6–20点组的3D反而下降1.24个百分点，应与样本数及全部分组一起呈现。三模态ObjDec在≥60m相对ASF-style有收益，近距离和极稀疏组并非全面领先。

## 共同TP的定位误差

两方法共同检测成功的目标上，ObjDec-LR/L4DR的xy中心误差约0.08847/0.08844m，基本相当；朝向轴差约6.21°/6.39°。现有诊断支持一定召回收益，不支持把整体增益简单描述为普遍的中心定位改善。完整逐类、各自TP、共同TP误差保存在CSV。

## 可复现性

`protocol.json`固定输入、权重来源、score、匹配和分组。几何计算完成后，首次配对表导出因不同方法对的字段不同而失败；`finish_from_gt.py`从完整`per_gt.csv`恢复汇总，使用字段并集，未改预测和匹配。原异常保存在`export_failure.json`，恢复过程在`export_recovery.json`。重跑时先执行父目录`diagnostics.py`生成逐GT记录，再运行`finish_from_gt.py`汇总。
