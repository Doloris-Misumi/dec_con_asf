# L4DR v2：统一 TaskDec / Strong 评测协议

2026-09-15。只做评测，不训练。最终结果由 `completion.json` 和 `results/taskdec_v2_l4dr_aligned_evaluation_260915.md` 判定，不能把 smoke 或 partial 当全量结果。

## 协议与权重

- 数据集标签 v2_0，宽 ROI `[0,-16,-2,72,16,7.6]`，Sedan + Bus/Truck，最终 conf > 0.3。
- Strong 原有 13,727 帧预测对应的 GT 和天气描述是共同参考。`prepare.py` 调用原生 L4DR 标签解析，并逐帧验证导出 GT 完全相同，记录于 `preflight.json`。
- Score 预筛 0.1；class-agnostic rotated NMS 0.01，pre 4096 / post 500。L4DR 实际读取 `MODEL.POST_PROCESSING`，此处与 Strong 的 `MODEL.HEAD.POST_PROCESSING` 对齐。
- L4DR 原配置有效 `MODEL.POST_PROCESSING` 的 NMS 为 0.7；其 `DENSE_HEAD.POST_PROCESSING` 虽写 0.01，但最终后处理不读取该副本。本次从推理开始就明确覆盖有效设置为 0.01，属于后处理也统一的实验；不是仅替换 evaluator 后原生 L4DR 默认设置的结果。
- 使用 TaskDec 原始 KITTI 导出函数、revised evaluator（41 点平均、z_center=0.5），没有改 evaluator 源码。
- 作者公开双类别权重 `/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v2.1-model_30.pt`，572 项参数严格加载，MGF，DENOISE_T=0.1。来源与固定 revision / SHA 见 `checkpoint_source.json`。
- 原本地 v1.1 model_34 是单类别，不能用于本次双类别表。v2.1 的发布名称不等于证明它对应论文 Table 10 的准确运行；本文统一的是测试标签与协议。
- 原始稀疏雷达复用 `/home/hongsheng/k_radar_dataset/sparse_radar_tensor_wide_range/rtnh_wider_1p_1`，此前 WCBR 已校验恢复完成。不能改用各序列根目录下指向 sparse_cube 替代输入的 symlink。
- ASF 保留官方归档，未在本次重新推理或逐帧复算。L4DR 与 Strong 已核实真实 GT 一致；不可把三行都标成“本次同场复测”。

## 文件

- `manifest.jsonl`：排序后的帧 ID、原生标签元数据和天气/道路/昼夜分组。不含点云或特征。
- `l4dr_config.yml`：本次独立配置。
- `l4dr_smoke/`：14 帧、七天气、两类预测的功能验证。
- `l4dr_partial_before_memory_fix/`：第一次全量启动后发现原生 Dataset 累计保留点云，主动停止的未完成记录；不计入 AP。
- `l4dr_full/preds/`：唯一一份 L4DR 全量预测文本；GT 直接引用 Strong，不重复保存，不建立天气复制目录。
- `strong_evaluation.json` / `l4dr_evaluation.json`：全量 18 条件 × 2 类 × 6 指标。
- `strong_archive_verification.json`：复算 Strong 的 216 个 AP 与原归档逐项比较，最大差值为 0。
- `*_protocol_diagnostic.json`：固定预测，交叉 11/41 点 AP 与 z_center 1.0/0.5 的 Total 指标。
- `completion.json`：仅在完整结果核验与报告导出通过后标记 complete。

## 执行与复现

工作目录 `/home/hongsheng/dec_con_asf`，解释器 `/home/hongsheng/miniconda3/envs/rl_3dod/bin/python`。
脚本默认拒绝覆盖已有运行状态。复现实验应使用独立输出目录，并保持共同 manifest 不变。

```bash
python -u analysis_exports/l4dr_v2_aligned_260915/prepare.py
CUDA_VISIBLE_DEVICES=2 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=4 python -u analysis_exports/l4dr_v2_aligned_260915/run_l4dr.py --smoke
CUDA_VISIBLE_DEVICES=3 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=4 python -u analysis_exports/l4dr_v2_aligned_260915/evaluate.py --model strong
CUDA_VISIBLE_DEVICES=3 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=4 python -u analysis_exports/l4dr_v2_aligned_260915/protocol_diagnostic.py --model strong
CUDA_VISIBLE_DEVICES=2 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=4 python -u analysis_exports/l4dr_v2_aligned_260915/run_l4dr.py
```

全量 L4DR runner 完成后自动接续 revised 全条件评分、固定预测协议交叉检查、CSV/LaTeX/Markdown 导出及结果索引更新。失败会写入状态并停止，不能跳过失败样本。

Dataset 包装只解除已读点云在缓存列表中的长期引用，传感器加载、过滤、采样和模型计算仍调用原生实现。随机种子 2023，batch=1，workers=4，cudnn deterministic=True。推理时间是含加载/文本写出的流水线耗时，不能直接用作论文模型延迟。

新增主要空间为约 237 MiB 权重、一份预测文本及约几十 MiB manifest；不复制完整数据。全量目录预期远小于 1 GiB。
