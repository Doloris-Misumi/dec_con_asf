# V2X-Radar-V：0.16m TaskDec 与 Concat，80轮固定预算

2026-09-18，作者授权检查配置后直接开始80轮。正式状态以 `analysis_exports/v2x_grid016_260918/controller_status.json` 及各训练目录的 `status.json` 为准。

**08:20:04 更新**：两组完整预检均已通过，后台控制器已启动，PID `4170533`。GPU3通过连续空闲检查后启动TaskDec；GPU2的Concat等待Strong v2补测成功完成并退出。控制器和训练子进程均为独立后台会话。

**正式启动核验**：TaskDec子进程PID `4170570`，08:20:49开始第1轮，首batch loss=4.83677，无失败。08:21左右驱动显示GPU3占用30,468MiB（约29.75GiB），余量18,103MiB（约17.68GiB）。GPU2 Strong推理已到900/13,727帧，无失败；Concat仍为队列状态。GPU1 L4DR PID3995315继续训练。

## 配置与排期

| 项目 | TaskDec | Concat |
|---|---|---|
| GPU | 3 | 2；等待v2 Strong评测成功完成并退出、GPU空闲后接续 |
| XY柱／BEV网格 | 0.16m，640×640 | 相同 |
| 融合 | 完整TaskDec，2×2 patch、query4 | 原三路concat＋Conv/BN/ReLU |
| 融合输出／检测网格 | 128通道640×640／320×320 | 相同 |
| 三路输入 | Camera＋LiDAR＋Radar | 相同 |
| 训练集 | 原8,391帧 | 相同 |
| 训练预算 | 80轮，FP32，micro-batch2，累积4，有效batch8 | 相同 |
| 优化器与LR | 原AdamW、首轮warmup、按更新数cosine | 相同 |
| Seed | 260916 | 相同 |
| 学习参数量 | 33,654,069 | 33,136,685 |
| 评测 | 第1轮及每5轮，完整去重val 1,487帧 | 相同 |
| 选模 | val严格IoU、Moderate三类平均3D AP_R40最高；同分取早轮 | 相同 |
| 训练结束 | 自动评best/last的原始和去重val/test | 相同 |

每轮4,196个micro-batch、1,049次参数更新，80轮共83,920次更新。继续采用原ROI、类别映射、训练增强、loss权重、NMS与评测协议。test不用于选配置或延长轮数。旧实验及GPU1 L4DR保持运行。

相对已完成的0.4m TaskDec 2×2，配置差异仅为 `voxel_size`、运行内存上限及创建时间；patch/query、模型宽度、训练batch、loss和日程不变。物理patch随网格细化由0.8×0.8m变为0.32×0.32m，不能声称物理patch尺度保持不变。

## 初始化与几何核查

从各自原**未训练初始权重**复制同形状张量；未使用80轮best/last续训。两组编码器、neck/head张量SHA完全相同：

`92eaf7cee4de9f7c346c34cfb5cd97c3b8124a1298c786fc5e63f1624ea12ae0`

旧相机 `voxel_size` 缓冲区不从0.4m初始化覆盖，按0.16m重新生成。相机投影、点云pillar、fuser几何、foreground栅格和检测anchors共用新网格。anchors依新网格构建，不复制旧空间布局。坐标范围和所有相机标定保持原规则。

两组初始权重SHA：

- TaskDec：`bd2fc4b3e66682f245ce09621893784dc0cefd3b77b31dce5c50e6ace9631131`。
- Concat：`2bb8f3da5f8e79e1ce763eaba04ceab43b7ce2bd6e413822b8e8b0d556955701`。

输入、配置、源码均保存校验摘要；使用独立产物目录和运行器，复用原训练、预测、评测逻辑，不修改原实验代码。TaskDec仍作为唯一融合主路径，不是在Concat输出上附加模块。

## 资源检查

首先在GPU3做8个真实训练batch，loss和梯度均有限：

| micro-batch | 峰值allocated | 峰值reserved | 8个batch耗时 |
|---|---|---|---|
| 1 | 12.87GiB | 13.92GiB | 6.59秒 |
| 2 | 25.33GiB | 27.55GiB | 10.71秒 |

因此保留micro-batch2及原BN口径。两组PyTorch分配上限设为显存75%（A6000约36GiB），只在对应卡独占空闲时启动。CUDA context和非PyTorch分配另占少量空间，运行时同时看驱动显存。

正式启动前，各自完成100个训练batch、8帧验证、checkpoint保存和严格恢复；检查实际融合输出 `[2,128,640,640]` 与检测输入 `[2,384,320,320]`。检查权重验证后仅删除本次临时best/last，保留日志与SHA记录；正式80轮重新从冻结的初始权重开始。检查最终结果见 `matched_80ep/smoke_{taskdec,concat}/status.json`。

已通过的100 batch完整检查：

| 模型 | 训练耗时 | 峰值allocated / reserved | 更新次数 | 验证与恢复 |
|---|---|---|---|---|
| TaskDec | 114.00秒 | 25.63 / 27.58GiB | 25 | 通过 |
| Concat | 32.76秒 | 10.21 / 13.90GiB | 25 | 通过 |

按100 batch平均速度粗算，TaskDec训练部分约106.3小时（4.4天），Concat约30.5小时；未计入正式全量验证、最终评测和运行负载变化。每5轮完整验证的原安排不变。

当前短预检不能直接当作完整80轮耗时；需要结合100 batch和首轮实际速度更新排期。只保留一份best、一份可恢复last、一份初始权重及最终预测，不保存每轮大权重或BEV特征。

## 查看日志

TaskDec：

```bash
tail -f /home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/train.log
```

Concat排队／两组控制器：

```bash
watch -n 10 cat /home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/controller_status.json
```

Concat启动后：`analysis_exports/v2x_grid016_260918/matched_80ep/concat/train.log`。

v2 Strong九项补测继续独立运行，见 [v2启动记录](taskdec_v2_availability_completion_launch_260918.md)。控制器需同时确认其成功完成、原PID退出、GPU2空闲，再启动Concat，不终止该任务或挤占GPU1。

运行器、控制器及启动器分别为同目录的 `run.py`、`controller.py`、`launch.py`。训练进程有独立文件锁；失败时记录状态，不隐藏异常、不自动覆盖已有checkpoint。
