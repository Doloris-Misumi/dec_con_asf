# TaskDec 2×2 patch 独立对照：GPU3 启动记录

2026-09-17 00:01:51（北京时间）启动，PID `3981576`，GPU3。用户授权开展上一轮行人诊断后建议的较小 patch 对照。准备配置完成于 9 月 16 日 23:59，产物沿用 `v2x_taskdec_260916` 目录。

00:03:35 复核：正式训练已到 epoch 1 / batch 300，75 次参数更新，平均 loss 3.1898，无失败；GPU3 总占用 9,882 MiB（约 9.65 GiB），剩余 38,689 MiB。原三组训练/评测 PID 均仍存活，原始与新实验的源文件、输入 manifest 校验通过。核查凭据：`taskdec_patch2_80ep/taskdec/launch_verification.json`。

目标是假设检验：较细的空间融合粒度是否改善行人的中心定位和严格 IoU AP。诊断提示定位差距，但尚不能断言原 4×4 patch 是唯一原因，也不能预先宣称 2×2 会提升结果。

## 对照配置

| 设置 | 原 TaskDec | 本次 TaskDec |
|---|---|---|
| Patch 尺寸 | 4×4 BEV 单元 | 2×2 BEV 单元 |
| 物理 patch 范围 | 1.6×1.6 m | 0.8×0.8 m |
| 每 patch query 数 | 16 | 4 |
| 融合输出 | 128×256×256 | 128×256×256 |
| 参数量 | 33,955,125 | 33,654,069 |
| 三路输入 | Camera + LiDAR + Radar | 相同 |
| 训练预算 | 80 轮；FP32；batch 2；累积 4 | 相同，有效 batch 8 |
| 随机种子 / 优化器 | 260916 / AdamW | 相同 |
| 数据、增强、编码器、neck/head、损失及 LR 日程 | 原冻结配置 | 相同 |

实际 config diff 只有 `resolved_fuser.UCP.PATCH_SIZE` 和 `resolved_fuser.UCP.N_QUERY` 两项。Query 数是保持融合输出通道和空间形状的配套调整，因此本实验应表述为融合空间粒度对照，不能称作所有内部张量均不变的单参数消融。

从原 TaskDec 的**未训练初始权重**复制 605 个同名同形状张量；10 个尺寸变化的融合张量使用相同种子的新初始化。编码器、neck/head 的 SHA256 与原三个模型共享初始权重完全一致：`76f7e84abaec58108d27cc485ff43698131bd84e317f19d0bcabd3bf1ad346f9`。未使用训练后的 best/last，也未从检查阶段续训。

主路径仍为三路编码器 → TaskDec 融合架构 → neck/head。新运行器仅将原训练代码的产物目录绑定到独立目录，复用冻结的训练、预测、评测和选模逻辑；未改动 GPU0/1/2 的原实验或其代码。原源文件与配置校验、新脚本和配置校验均通过。

## 启动检查

在 GPU3 完成 100 个真实训练 batch（200 样本、25 次梯度累积更新）、8 帧评测、checkpoint 保存和严格恢复：全部通过，loss 和梯度有限。

- 实际融合输出已检查为 `[2,128,256,256]`。
- 100 batch 训练耗时 28.20 s，含启动和数据加载，仅作为初步成本参考。
- 训练显存 allocated 峰值 5.224 GiB，reserved 峰值 6.861 GiB；CUDA context 等会使 `nvidia-smi` 占用更高。
- 保持原每进程显存分配上限 30%（48 GiB 卡约 14.4 GiB）。检查期间无 OOM。
- 检查阶段权重恢复验证后仅删除本次生成的临时 best/last，保留检查日志、状态和 SHA 记录。正式训练重新从初始权重开始。

## 训练与评测安排

训练集 8,391 帧，每轮 4,196 个 batch、1,049 次更新，共 83,920 次更新。第 1 轮，以及第 5/10/…/80 轮进行 1,487 帧完整去重 val 评测。

选模规则沿用原定义：去重 val 的严格 IoU、Moderate、三类平均 3D AP_R40 最大者为 best，同分取更早轮次。严格 IoU 为 Vehicle 0.7、Pedestrian 0.5、Cyclist 0.5。80 轮后自动评测 best 和 last 的原始及去重 val/test，test 不参与选模。

关注同预算下行人 AP@0.5、总体三类 AP 及其他类别是否受损；后续几何诊断再核对行人中心误差与拥挤组表现。短期结果仅用于观察收敛，不替代完整预算架构比较。

正式训练滚动保留 best/last 和一份初始权重，不保存每轮权重或大规模 BEV 特征；共用原数据集。记录实际训练和评测耗时。

## 日志与产物

```bash
tail -f /home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/taskdec_patch2_80ep/taskdec/train.log
```

状态：`analysis_exports/v2x_taskdec_260916/taskdec_patch2_80ep/taskdec/status.json`。

配置、初始化及其来源：同目录上一级的 `config.json`、`initialization.json`、`provenance.json`、`source_manifest.json` 和 `input_manifest.json`。`config.json` 中旧的 `created_at` 保留以使 diff 只包含两项结构设置；本实验创建时间以 `provenance.json` 为准。

运行器：`analysis_exports/v2x_taskdec_260916/taskdec_patch2_experiment.py`；检查记录在 `taskdec_patch2_80ep/smoke/`。

Concat 第80轮结果另见 [结果收集](taskdec_v2x_concat80_results_260917.md)。
