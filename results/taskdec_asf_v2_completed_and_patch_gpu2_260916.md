# ASF v2.0 完成结果与 V2X patch 的 GPU2 调度记录

记录日期：2026-09-16。用户明确授权：收集已完成的 ASF v2.0 结果，随后在 GPU2 直接启动原待运行 patch。

## K-Radar v2.0：本地 ASF 已完成

- 11 轮，79,123 次更新，13,727 帧测试；预测文件数量核对为 13,727，failure_count=0。
- 训练结束：2026-09-16 17:26；完整评测结束：18:24（北京时间）。训练用时 19.15894 GPU 小时，推理用时约 54.75 分钟。
- 此次 ASF 为原生 A2Fusion + SCL，采用 Strong 相同的单模态预训练编码器与冻结设置；表内均为相同 revised evaluator、相同测试集和 conf>0.3。
- AP 为项目 revised evaluator 的 41 点均值，不能写作标准 KITTI AP_R40。

| 方法 | Sedan@0.3 | Bus@0.3 | Mean@0.3 | Sedan@0.5 | Bus@0.5 | Mean@0.5 |
|---|---:|---:|---:|---:|---:|---:|
| Strong（已有） | 74.58 | 59.24 | 66.91 | 52.14 | 33.97 | 43.05 |
| ASF（本地 11 轮） | 74.45 | 55.09 | 64.77 | 51.52 | 27.88 | 39.70 |
| L4DR（本地 11 轮） | 74.49 | 56.58 | 65.53 | 54.28 | 33.39 | 43.84 |
| Strong − ASF | +0.13 | +4.15 | +2.14 | +0.62 | +6.09 | +3.36 |

Strong 相对 ASF 的均值增益为 +2.14238 / +3.35568 点（IoU 0.3 / 0.5）；主要增益来自 Bus。与 L4DR 的结论依指标而异：Strong 的 Mean@0.3 更高，但 Mean@0.5 更低。该结论限于此轮训练预算，不替代官方充分训练模型比较。

完整天气表：[原结果汇总](taskdec_v2_matched_training_260915.md)。三个模型的 648 项完整 AP（Total、天气、昼夜、道路；3D/BEV；三个 IoU）已收集为 [CSV](../analysis_exports/v2_matched_training_260915/completed_collection_260916/complete_metrics.csv)，[来源与哈希](../analysis_exports/v2_matched_training_260915/completed_collection_260916/sources.json)。未复制或删除任何 checkpoint。

## V2X-Radar-V patch：转移至 GPU2

- 保留原始三组训练设计及所有冻结训练/评测源码、初始化、数据划分和配置。
- patch 仍为三模态原生 A2Fusion 主融合路径，80 轮、FP32、micro-batch=2、累积=4、有效 batch=8。共享编码器与检测头的初始化与另外两组一致。
- 评测：第 1 轮及每 5 轮完整去重 val；完成训练后自动评测 best/last 在原始及去重 val/test 上的结果。
- GPU0 TaskDec / GPU1 Concat 原 PID 保持运行；旧控制器原有 GPU1→patch 队列由接管调度取消。GPU2 独立运行 patch。
- GPU2 启动前连续三次检查空闲显存≥26,000 MiB、利用率≤30%；沿用进程显存分配上限为总显存 30%（约 14.4 GiB，另有 CUDA 上下文开销）。
- 当前 patch 不含 SCL；论文可用 ASF（本地适配，w/o SCL）一类明确标记，不能把此配置隐去。它与上面的 K-Radar ASF + SCL 复现是不同实验。
- 接管进程对旧训练进程无法使用 waitpid 获取退出码，记账中如实保存 exit_code=null，并联合“进程已退出 + 完整结果状态”核验成功；训练和评测本身未改动。

实时状态：[控制器](../analysis_exports/v2x_taskdec_260916/controlled_80ep/controller_status.json)；[调度交接凭据](../analysis_exports/v2x_taskdec_260916/controlled_80ep/gpu2_handoff.json)。

```bash
tail -n 10 -F /home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/controlled_80ep/patch/train.log
```

### 实际启动核验

2026-09-16 21:36 启动成功：patch PID `3955975`，GPU2。21:37 核验已通过第 1 轮前 100 批，loss 有限、failure_count=0；nvidia-smi 进程显存约 7.42 GiB。GPU0 TaskDec PID `3877508`、GPU1 Concat PID `3877510` 保持运行。旧调度控制器已退出，新控制器 PID `3955866`，所有待运行队列均为空，三组均为独立活动任务。

启动凭据：[gpu2_launch_verification.json](../analysis_exports/v2x_taskdec_260916/controlled_80ep/gpu2_launch_verification.json)。
