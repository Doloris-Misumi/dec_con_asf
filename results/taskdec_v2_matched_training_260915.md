# K-Radar v2：ASF / L4DR 按 Strong 训练预算本地复现

更新：2026-09-16T18:24:15.505468+08:00

作者已选择：**同训练集、11 轮、有效 batch=2，另记录实际单卡训练耗时**。本次是新增本地训练对照；此前官方结果与本次结果分别保存。

| 任务 | 状态 | 完成轮数 | 完成更新步数 | 已完成轮训练小时 | GPU |
| --- | --- | --- | --- | --- | --- |
| ASF | complete | 11 | 79123/79123 | 19.16 | 2 |
| L4DR | complete | 11 | 79123/79123 | 8.20 | 3 |

## 已核验的预算与初始化

- 训练 14,386 帧，测试 13,727 帧。ASF、L4DR 原生标签解析器逐帧 GT 完全一致；测试 GT 与 Strong 归档一致。
- 每轮 7,193 步，共 79,123 次更新，158,246 次训练样本呈现。batch=2、FP32、seed=20250215。
- AdamW，lr=0.001，min_lr=0.0001，weight_decay=0.01；保留 Strong 原始逐步 cosine 调度（T_max=7193，不在轮间重置）。
- ASF：原生 A2Fusion + SCL，沿用 Strong 同一组官方单模态编码器；编码器固定参数逐项匹配 Strong，全部保留状态严格加载。融合模块和检测头重新初始化；FREEZE=True、FREEZE_BN=False。
- L4DR：原生双类别 MGF + PointNet / BiDF 结构，从头训练全部模块；不加载已完整训练的官方 detector checkpoint。不为凑预算更改网络宽度或骨干。
- 两者使用 Strong 相同的雷达文件路径，保留各自原生采样、体素化和输入通道。ASF 为 C+L+R，L4DR 为 L+R。
- 11 轮后只评最后 checkpoint；统一 revised evaluator、conf>0.3、NMS=0.01。输出 Total、七天气、昼夜和道路完整结果。
- 只保留一份最新可恢复 checkpoint；更新时原子替换。训练结束自动全量推理、评分并刷新本表。

**可比性边界：** 这是相同样本与优化步数的训练预算，不能写成相同 FLOPs、相同 GPU 小时或相同总预训练成本。ASF/Strong 依赖已有单模态预训练；L4DR 此轮是原生网络从头训练且缩短为 11 轮，公开配置默认 35 轮。因此不能用这个受限预算结果代替 L4DR 的官方充分训练结果，也不能预设复现分数应下降。

Strong 原日志包含 epoch 0–10 共 11 轮，训练进度条累计约 44.24 小时。历史加载使用 workers=0；本次用 4 个 worker 并解除点云缓存，因此历史墙钟不能直接当成模型计算量。本次 training_wall_seconds 记录单卡训练循环耗时（含加载，不含末轮评测），对应占用一张卡的训练 GPU-hours；不代表 CUDA 内核活跃时间。

## 当前完整结果

仅列已经完成全量评测的运行。尚在训练的任务不填估计 AP。

| 方法 | Sedan@0.3 | Bus@0.3 | Mean@0.3 | Sedan@0.5 | Bus@0.5 | Mean@0.5 |
| --- | --- | --- | --- | --- | --- | --- |
| Strong (existing) | 74.58 | 59.24 | 66.91 | 52.14 | 33.97 | 43.05 |
| ASF (local, 11 epochs) | 74.45 | 55.09 | 64.77 | 51.52 | 27.88 | 39.70 |
| L4DR (local, 11 epochs) | 74.49 | 56.58 | 65.53 | 54.28 | 33.39 | 43.84 |

此前官方参考：ASF 官方结果归档两类均值为 66.55 / 41.57；L4DR 官方双类别 checkpoint 本地统一评测为 69.48 / 48.23。ASF 的归档数字并非上一轮在本地重新推理其 checkpoint 得到。

## 分天气

AP3D@0.3

| 类别 | 方法 | Total | Normal | Light snow | Heavy snow | Rain | Sleet | Overcast | Fog |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sed | Strong (existing) | 74.58 | 73.51 | 89.56 | 63.57 | 68.11 | 72.52 | 84.30 | 94.46 |
| sed | ASF (local, 11 epochs) | 74.45 | 73.45 | 89.77 | 63.36 | 65.80 | 70.81 | 82.15 | 92.09 |
| sed | L4DR (local, 11 epochs) | 74.49 | 73.12 | 82.74 | 51.99 | 76.27 | 54.55 | 80.06 | 92.33 |
| bus | Strong (existing) | 59.24 | 51.63 | 89.56 | 72.34 | 10.08 | 57.47 | 73.82 | — |
| bus | ASF (local, 11 epochs) | 55.09 | 50.39 | 84.75 | 68.02 | 3.59 | 50.78 | 65.31 | — |
| bus | L4DR (local, 11 epochs) | 56.58 | 54.60 | 89.16 | 54.27 | 7.81 | 59.89 | 82.07 | — |

AP3D@0.5

| 类别 | 方法 | Total | Normal | Light snow | Heavy snow | Rain | Sleet | Overcast | Fog |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sed | Strong (existing) | 52.14 | 49.39 | 60.75 | 50.49 | 48.30 | 49.13 | 59.62 | 80.30 |
| sed | ASF (local, 11 epochs) | 51.52 | 48.90 | 59.25 | 51.24 | 45.96 | 44.83 | 57.16 | 79.89 |
| sed | L4DR (local, 11 epochs) | 54.28 | 52.33 | 59.28 | 38.72 | 54.95 | 41.22 | 49.24 | 83.44 |
| bus | Strong (existing) | 33.97 | 23.94 | 75.09 | 39.37 | 5.05 | 38.48 | 49.65 | — |
| bus | ASF (local, 11 epochs) | 27.88 | 21.16 | 70.58 | 32.28 | 1.94 | 30.29 | 46.68 | — |
| bus | L4DR (local, 11 epochs) | 33.39 | 32.18 | 69.00 | 17.00 | 6.60 | 43.05 | 55.89 | — |

## 记录与复现

- [运行目录与命令](../analysis_exports/v2_matched_training_260915/README.md)
- [数据、预算与配置核验](../analysis_exports/v2_matched_training_260915/preflight.json)
- [ASF 当前状态](../analysis_exports/v2_matched_training_260915/asf/status.json)
- [L4DR 当前状态](../analysis_exports/v2_matched_training_260915/l4dr/status.json)
- [官方权重统一评测报告](taskdec_v2_l4dr_aligned_evaluation_260915.md)
