# ASF / L4DR：Strong 预算下本地训练

2026-09-15，作者已明确选择“同训练集、11 轮、相同有效 batch，另记录实际 GPU 时间”。

本实验从本地训练得到新模型。历史官方行分别是 ASF 发布的结果日志归档、L4DR 发布双类别 checkpoint 的本地统一评测；本次不会覆盖它们。

## 确定的设置

- train=14,386，test=13,727。两种原生标签解析器对全部 train/test 的 GT 逐框一致，测试部分与 Strong 归档一致。
- epoch=11（0–10），batch=2，FP32，seed=20250215；每轮 7,193 步，总更新数 79,123，样本呈现数 158,246。
- AdamW，LR=0.001，MIN_LR=0.0001，weight decay=0.01。严格保留 Strong 的 scheduler 行为：CosineAnnealingLR(T_max=7193)，逐步推进、轮间不重置。
- ASF：原生 A2Fusion + SCL，沿用 Strong 的相机 / LiDAR / 雷达编码器和 FREEZE=True、FREEZE_BN=False。完整保留的 encoder state 严格加载，固定非统计张量分别 376 / 78 / 63 项与 Strong checkpoint 完全一致。仅原有各单模态检测头被移除；新融合模块和新检测头随机初始化。
- L4DR：原生 MGF / PointNet / BiDF，从头训练完整网络，不加载官方完整 detector checkpoint。保留原生通道数、雷达采样、体素化和任务损失。
- 两种新训练都直接读取 Strong 的原雷达根路径 `/home/hongsheng/k_radar_dataset`，避免两种路径形成输入差异。相机与 LiDAR 仍走原生加载方式。
- 末轮固定评测，conf>0.3、score prefilter=0.1、rotated class-agnostic NMS=0.01、revised evaluator（41 点平均，z_center=0.5）。全部天气、道路、昼夜都会导出。

相同优化步数与样本预算不等于相同 FLOPs、GPU 小时或总预训练费用。ASF/Strong 有单模态预训练；L4DR 此轮从头训练，默认公开配置的 35 轮被预算限定为 11 轮。本次应称“matched training-schedule reproduction”，不能替换官方完整训练模型的结果或宣称 L4DR 在原生完整训练下达到本次分数。

## 验证与状态

- `preflight.json`：训练预算、GT 核验、配置哈希。
- `asf_smoke/status.json`、`l4dr_smoke/status.json`：ASF 20 步、L4DR 200 步前向/反向/更新及四帧推理导出检查，均通过。四帧 GT 序列化与 Strong 完全相同。
- `asf/status.json`、`l4dr/status.json`：正式训练当前进度、有限损失、更新步数、显存峰值。
- `*/training_metrics.jsonl`：每 100 步的损失 / LR / 当前轮耗时，以及每轮完整耗时。
- `*/checkpoint_last.pt`：唯一一份最新可恢复 checkpoint（模型、优化器、调度器、RNG）。原子替换，不保存 11 份重复模型。
- `*/preds/`、`*/evaluation.json`：训练结束后自动生成全测试预测及 216 项 AP。
- `summary_status.json`：两任务均完成后标为 complete；某一行只有完成全量评测才写入结果表。
- `*_launch.json`：独立后台进程 PID、GPU、启动时脚本哈希；`runtime_provenance.json` 记录环境和原生模型 / 数据代码哈希。
- [结果与最近状态汇总](../../results/taskdec_v2_matched_training_260915.md)：报告在评测完成后自动更新；训练中以每 100 步更新的 `*/status.json` 为准，也可手动运行 `report.py` 刷新报告。

`training_wall_seconds` 是完成训练循环的单卡墙钟，含加载、前向、反向和优化器更新，末轮评测另计。GPU-hours 为这段时间占用一张卡的小时数，不等同 CUDA 内核实际活跃时间。历史 Strong 训练循环约 44.24 小时，但其 workers=0；本次 workers=4 且避免保留整轮点云，因此历史墙钟不能直接用于等算力宣称。

## 命令

工作目录 `/home/hongsheng/dec_con_asf`，解释器 `/home/hongsheng/miniconda3/envs/rl_3dod/bin/python`。新运行默认拒绝覆盖已有状态；独立复现应先创建新输出目录。

```bash
TASKDEC_PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
TASKDEC_RUN=analysis_exports/v2_matched_training_260915

"$TASKDEC_PY" -u "$TASKDEC_RUN/prepare.py"
CUDA_VISIBLE_DEVICES=2 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=4 "$TASKDEC_PY" -u "$TASKDEC_RUN/train.py" --model asf --smoke-steps 20
CUDA_VISIBLE_DEVICES=3 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=4 "$TASKDEC_PY" -u "$TASKDEC_RUN/train.py" --model l4dr --smoke-steps 200

"$TASKDEC_PY" "$TASKDEC_RUN/launch.py" --model asf --gpu 2
"$TASKDEC_PY" "$TASKDEC_RUN/launch.py" --model l4dr --gpu 3
```

训练结束自动推理、评分并更新报告，无需再调用评测命令。恢复已中断训练用相同模型参数附加 `--resume`，并使用 `>>` 追加日志；从最近完成轮的 checkpoint 继续。

此目录中 `*_training_only_smoke` 保留最初的训练功能验证；后续 `*_smoke` 补测了推理与导出。正式训练重新初始化，不沿用 smoke 更新后的参数。点云缓存修正仅解除 Dataset 对已读数组的长期引用，不改变 native 数据变换或模型结构。

L4DR 最初 20 步短测：训练损失、梯度、权重和运行统计均有限，但 eval 特征幅度过大，框尺寸的指数解码溢出（首帧 134 个 NMS 后预测含非有限尺寸）。诊断保留在 `l4dr_20step_diagnostic_smoke`，首次失败保留在 `l4dr_early_eval_nonfinite_smoke`。同配置延长至 200 步后，四帧均通过有限数值、类别和 GT 导出检查；保留的预测数为 0 / 3 / 0 / 0。这支持早期运行统计尚未稳定的解释，但没有单独隔离证明 BatchNorm 是唯一原因。本次没有更改归一化、裁剪预测或剔除异常框。正式训练从相同初始化重启，短测步数不计入 79,123 步。

雷达路径补充：`radar_path_spotcheck.json` 对当前 8 个测试帧的根目录软链接目标与恢复的官方 sparse radar tensor 文件逐字节哈希比较，均相同。因此软链接本身不能证明输入有差异；该抽查也不能代表全部文件。两种新训练直接使用同一 Strong 路径，不依赖此抽查来推断输入一致。
