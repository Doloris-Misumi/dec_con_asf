# TaskDec v1：六种缺失／损坏模态设置补测（2026-09-18）

**完成更新（2026-09-18）**：六种设置、10,065帧的全量推理及 `conf>0.3 / conf>0.0` 的总体和七种天气评测，已于 **03:16:26** 全部完成，`failure_count=0`，GPU2已释放。结果见 [本次实验汇总](taskdec_experiment_results_260918.md) 与 `analysis_exports/taskdec_v1_availability_completion_260918/results.json`。下文保留原启动记录。

## 已启动任务

按照本轮确认，使用 **GPU2** 对 v1 正式 TaskDec Robust 权重补齐六种推理设置，不重新训练。2026-09-18 00:25:59（北京时间）已在独立后台会话启动，PID `4145522`；具体进度以 `status.json` 为准。

00:27:56 核验：已完成 **100 / 10,065 帧**（每帧六种设置），无失败，约 **1.06 帧/秒**；`nvidia-smi` 中该进程占用 **3,472 MiB**，GPU2 总占用 3,506 MiB。按初始速度估计全量推理约 2.6 小时，后续指标计算另需时间，数据读取负载变化可能影响速度。GPU0/1/3 原有进程保持运行。

| 输出标识 | 设置 | 本轮输入定义 |
|---|---|---|
| `c` | C | 仅相机特征参与融合 |
| `l` | L | 仅 LiDAR 特征参与融合 |
| `r` | R | 仅四维雷达特征参与融合 |
| `c_star` | C* | 仅损坏相机特征参与融合 |
| `c_star_lr` | C*+L+R | 损坏相机，正常 LiDAR 与雷达；保留三个分支 |
| `cl_star_r` | C+L*+R | 正常相机与雷达，LiDAR 无回波；保留三个分支 |

与已有 C+L+R、L+R、C+L、C+R 组合一起，可组成十行可用性／输入失效表。本轮六项会输出完整的总体与七种天气指标；旧组合的分天气结果仍需核对完整性，不能仅凭这六项启动就称整张分天气表已经完成。

## 模型与评测口径

- 权重：`logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`。
- SHA256：`99eb07e8a0b01ec397d3f2ac890091fe539194149a2c542cf41c465c9f02a2d3`。
- 配置：同实验目录的 `config.yml`，严格加载权重，FP32、`eval()`，不使用 autocast。
- 数据：K-Radar **v1_0**，完整测试集 **10,065 帧**，Sedan；ROI 为 `[0, -6.4, -2, 72, 6.4, 6]`。
- 主结果：`conf > 0.3`；补充输出 `conf > 0.0`。两种阈值从同一份预测生成，不重复跑编码器。
- 指标：原有 v1 评测器（`is_validation_updated=False`），AP3D 与 APBEV，IoU = 0.3 / 0.5 / 0.7。
- 分组：总体及 `normal / overcast / fog / rain / sleet / lightsnow / heavysnow`。
- 每帧核对 GT 和天气描述是否与已完成的 v1 C+L 评测保存文件完全一致；不一致时中止并记录错误，不把异常样本当作空预测继续评测。

## 星号的本地定义

以下是固定、可复现的本地输入失效设置。ASF 论文说明了传感器失效实验，但目前查到的材料未提供足够明确的完整损坏生成代码，因此**不能将这三行宣称为严格复现 ASF 星号数据或严重程度**。

**C***：原始 RGB 图像全黑 `(0,0,0)`，保留原来的相机标定和图像尺寸，再按原图像归一化规则处理。当前配置使用 ImageNet 均值和方差，因此送入编码器的是 `-mean/std`，不是归一化后的全零张量。相机编码器、相机融合分支均保留。

**L***：评测 ROI 内无 LiDAR 回波。为绕过当前稀疏卷积后端对空活跃体素的限制，明确采用“零稀疏高度压缩特征 → 原 LiDAR 稠密 BEV backbone”的空输入约定，保留训练好的偏置、BN 和后续 LiDAR 融合分支。不伪造占位点，也不直接把最终 LiDAR BEV 特征置零。该约定属于本地可复现的无回波模拟，需在论文实现说明中披露。

缺失模态行使用模型原有的 `avail_feats` 选择；损坏模态行仍保留相应 token，因此不能与直接去除该模态混为一谈。

## 启动前验证与运行方式

已完成测试集索引 `0 / 5000 / 10064` 的三帧预检：

- 六种设置均输出有限预测值；GT、天气与既有 v1 文件一致。
- C/L/R 共九项检查：复用同帧编码结果的预测框、分数、类别与原始完整 `network.forward` 一致（`atol=rtol=1e-5`）。
- 内存中的 KITTI 解析与原文件解析器一致，包括空预测。
- 原始评测器默认分成 50 块，不支持仅 3 帧直接评测。预检阶段将这三帧重复至 51 项，仅验证 CUDA 评测链路；**预检 AP 不是真实数据集结果，不用于论文**。全量评测不重复帧、不修改原评测算法。
- 预检 PyTorch 显存分配峰值约 **1.12 GiB**。全量推理设置 PyTorch 分配上限为 GPU 总显存的 30%；这不等于对所有第三方 CUDA 分配的硬限制。

同一帧的正常编码器结果复用，六种设置逐个运行融合与检测头；损坏相机另跑原相机编码器，空 LiDAR 特征另过原稠密 backbone。仅使用 GPU2，不改变其他 GPU 的训练或评测。启动时 GPU2 占用为 26 MiB。

预测、GT 与帧标识保存为一份压缩 JSONL，不保存中间特征，不复制原始数据或权重。全部推理后自动评测，逐组更新中间 JSON，最后生成结果表。

早期预检中发现的配置 JSON 序列化问题和三帧分块问题已修复，失败日志保留；这些问题未修改模型权重或原评测代码。

## 查看进度与输出

实时日志：

```bash
tail -f /home/hongsheng/dec_con_asf/analysis_exports/taskdec_v1_availability_completion_260918/run.log
```

结构化进度（每 50 帧更新；评测时逐分组更新）：

```bash
watch -n 5 cat /home/hongsheng/dec_con_asf/analysis_exports/taskdec_v1_availability_completion_260918/status.json
```

输出目录：`analysis_exports/taskdec_v1_availability_completion_260918/`

- `run.log`：全量任务日志；`status.json`：当前阶段、帧数、速度、显存峰值或异常。
- `manifest.json`、`resolved_config.json`：权重／脚本／评测源码摘要和固定协议。
- `predictions.jsonl.gz`：推理全部完成后由临时文件原子改名得到的完整预测包。
- `results_partial.json`：已完成的分组评测；`metrics.log`：原评测器文本输出。
- `results.json`、`results.md`：全量评测完成后的结果。
- `smoke/`：独立预检产物，其中的 AP 仅为链路检查数据。

运行脚本：`tools/analysis/run_taskdec_v1_availability_completion_260918.py`；启动脚本：`scripts/launch_taskdec_v1_availability_completion_260918.py`。若推理已完成、仅评测阶段失败，可在确认旧进程退出后使用运行脚本的 `--evaluate-only` 参数从预测包重算，不需要重复推理。
