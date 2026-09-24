# TaskDec 推理优化与官方 ASF 配对测速（2026-09-17）

TaskDec v1 正式权重无需重训，网络调用时间由 **84.69 ms 降至 59.57 ms**，降低 **29.7%**。
优化后的 TaskDec 比本轮原版 ASF 快 **29.1%**；双方采用同样优化时，TaskDec − ASF 的差值为 **+0.27 ms**。以下均为本轮同一协议的实测，未混入历史 86.45/79.95 ms。

## 1. 完整速度对照

| 模型 | 执行方式 | 参数量 M | 平均 ms ↓ | 中位数 ms | P95 ms | 前向 FPS ↑ | CUDA event 均值 ms |
|---|---|---:|---:|---:|---:|---:|---:|
| TaskDec Robust v1 model_0 | 原版 eager | 79.47 | 84.69 | 84.50 | 89.98 | 11.81 | 84.62 |
| TaskDec Robust v1 model_0 | CUDA Graph | 79.47 | 59.57 | 59.23 | 65.93 | 16.79 | 59.50 |
| ASF 官方 v1 model_10 | 原版 eager | 78.13 | 84.00 | 82.63 | 93.26 | 11.91 | 83.93 |
| ASF 官方 v1 model_10 | CUDA Graph | 78.13 | 59.30 | 59.10 | 64.82 | 16.86 | 59.23 |

每个数字汇总两轮各 100 帧，即 200 次计时、100 个不同计时帧。FPS=1000/平均毫秒，并非含读盘吞吐率。

| 模型 | 第 1 轮：原版 / 优化 ms | 第 2 轮：原版 / 优化 ms |
|---|---:|---:|
| taskdec | 84.51 / 59.49 | 84.87 / 59.65 |
| asf | 81.51 / 58.69 | 86.48 / 59.91 |

TaskDec 两轮优化结果为 59.49/59.65 ms，ASF 为 58.69/59.91 ms；逐轮快慢次序发生变化。当前证据支持“同等优化后延迟接近”，不足以认定某一架构在速度上稳定领先。其他卡训练带来的共享主机负载也限制了小差值的解释。

## 2. 计时协议与边界

- 仅使用 GPU2（RTX A6000），不改动 GPU0/1/3 的现有任务。其他卡上的训练仍在运行，主机 CPU/I/O 并非完全独占。
- 两模型均 C+L+R、batch=1、4 个 PyTorch CPU 线程、FP32 张量、无 autocast。matmul/cudnn 的 TF32 均保持原环境 True；cudnn deterministic=True、benchmark=False。
- PyTorch 1.10.1+cu113。参数、权重、图像大小、BEV 范围、模态、score threshold、NMS 和检测头不变。
- 同一 v1 测试集及过滤后 10065 帧。np.linspace 在测试集索引中选 120 帧，前 20 帧预热，后 100 帧正式计时；索引、序列和天气保存在 JSON。两轮使用相同索引。
- 每帧读取一次原始 CPU 输入，复制给原版与优化版；交替先后顺序，两种路径分别同步计时。模型运行顺序为 TaskDec → ASF → ASF → TaskDec。
- 时间覆盖整个 network(batch)：包含 CPU 点云预处理、H2D、三路编码、融合、检测头解码、NMS，以及原评测路径的 GT recall 统计。**历史表中的 forward 也已包含后处理，不能称为“不含 NMS 的纯网络时间”。**
- 不包括读盘/collate、模型初始化、首次图捕获、结果拷回核对及额外诊断。读盘仍是离线端到端流程的大头，不能把本表 FPS 当实际数据加载流水线 FPS。
- ASF 使用官方权重，在本地共同骨架中 strict load；相机、LiDAR、radar、原 ASF 融合器、检测头等 11 个共同代码/配置文件与官方本地仓库对应文件逐字节一致；两套解析后的 DATASET 与 HEAD 配置相同。见 asf_common_code_audit.json 和各 resolved_config.json。

## 3. 优化做了什么

对相机 Swin 骨干和完整融合器做 CUDA Graph 捕获与重放，将重复的 CPU 算子调度变成图提交。每一帧仍复制新图像和新 BEV 特征，并重新计算全部算子；没有跨帧缓存预测或 BEV 特征。

TaskDec 的 common/unique、前景 gate、模态控制、任务上下文、query 调制、融合输出调制均保留。没有删模块、改阈值、缩小输入、量化、混合精度或重训。相机几何变换仍读取每帧标定，没有采用跨场景共用标定缓存。

诊断 profile（14 帧、带同步 hooks，仅用于定位）显示：相机分支约 39.95 ms，其中 Swin 约 29.83 ms；LiDAR 19.30 ms、radar 14.06 ms、融合 11.03 ms、检测头 2.78 ms。优化主要针对相机与融合路径的调度开销。

## 4. 数值核对与现有限制

每轮核对 120 帧（含预热），两轮共 240 次对照；中间特征、dense 输出以及 NMS 后框、分数、类别都参与核对。

| 核对项 | TaskDec | ASF |
|---|---:|---:|
| 捕获模块相同输入下逐位一致 | 240/240 | 240/240 |
| 全路径所有检查张量逐位一致 | 218/240 | 218/240 |
| 相机 BEV 一致 | 240/240 | 240/240 |
| LiDAR BEV 一致 | 240/240 | 240/240 |
| radar BEV 一致 | 218/240 | 218/240 |
| 最终类别一致 | 238/240 | 235/240 |

少数全路径差异最先出现在未改动的 radar 分支；对应帧追加的“原版对原版”复测也出现波动。单独固定输入检查相机骨干及融合器，图重放输出均逐位一致。另对索引 5328 反复诊断 14 次，复现了同样现象。因此证据支持图捕获模块保持当前运算结果，不能把全路径波动直接归因于加速，也不能宣称全测试集 AP 已完全不变。
TaskDec / ASF 的全路径不一致对照中，原版重复推理也出现变化的次数分别为 22 / 22。详见 JSON 的 verification/eager_repeat/adapters。

**尚未重跑全测试集 AP。正式将新延迟与原 AP 配成论文结果前，应做全量精度复核。** 本轮是已执行的速度优化与抽样数值检查，不是新一轮完整检测评测。

配对测试（同时保留 eager/graph 及核对缓冲）的 PyTorch allocated 峰值：TaskDec 1.161 GiB、ASF 1.153 GiB；不是独立部署峰值，也不含 CUDA context/native allocator 的全部显存。

退出异常：本轮四次测速均在完整结果写盘之后报 `free(): invalid pointer`，子进程退出码为 -6（SIGABRT）。未启用 graph adapter 的原版 profile 进程也有该现象，原因尚未定位。四轮完整结果、日志与非零退出码均保留在 comparison_process_status.json；不能把它们描述为正常退出。本轮没有更改本地原生库环境，当前按实验性部署开关使用。

## 5. 使用方式

文件：`tools/analysis/taskdec_inference_optimizations.py`。先按原流程加载权重，再安装：

```python
from tools.analysis.taskdec_inference_optimizations import install, set_enabled
model.eval()
install(model, "graph_both")  # checkpoint 必须在安装前加载
with torch.no_grad():
    output = model(batch)   # 首帧准备 CUDA Graph，稳态测速须先预热
set_enabled(model, False)   # 同一实例切回原 eager 路径
```

仅用于 eval/no_grad、每模型实例同一时刻一帧。图输出缓冲会被后续帧复用，需要长久保存的张量应及时 clone。不同输入形状/模态子集及融合可视化请求回退到原融合执行。安装后不再修改权重或精度设置，不用于训练或导出新 checkpoint。当前训练入口没有接入该开关。

复测示例（输出文件必须不存在，独占一个空闲 GPU 再执行）：

```bash
cd /home/hongsheng/dec_con_asf
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 \
  /home/hongsheng/miniconda3/envs/rl_3dod/bin/python -u \
  tools/analysis/benchmark_taskdec_inference_260917.py \
  --gpu 2 --model taskdec --optimization graph_both --verify --check-adapters \
  --warmup 20 --samples 100 --output /tmp/taskdec_speed_recheck.json
```

## 6. 论文表述建议与原始记录

可以写：TaskDec 在保留完整架构的条件下，通过图重放降低推理执行开销；报告标准 eager 与相同部署优化下的双方结果。优化后 TaskDec 对原版 ASF 的领先可以作为部署结果，但不能用来证明 TaskDec 架构本身比同等优化的 ASF 更快。

所有新增结果在 `analysis_exports/inference_optimization_260917/`：

- `comparison_summary.json/.csv`：本报告汇总数据。
- `taskdec_paired_r1/r2.json`、`asf_paired_r1/r2.json`：逐帧时间与数值核对。
- `comparison_process_status.json`：各进程退出码、完整性及耗时。
- `taskdec_diagnostic_5328.json`：原版 radar 波动定位。
- `taskdec_profile.json`、`taskdec_graph_pilot.json`：前期定位/小样本试测，不计入正式汇总。
- `original_source_manifest.json`：原训练模型相关源码 hash，本轮前后核对未变。

原 checkpoint、数据、现有训练源码均保留；只新增分析脚本、开关、短日志和 JSON，不复制 checkpoint 或导出大型特征。历史效率表保留原数值，不覆盖。
