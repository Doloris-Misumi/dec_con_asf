# ObjDec K-Radar v1：固定权重推理干预补测

## 状态与范围

2026-09-23 21:26（北京时间）在物理 **GPU2** 启动，PID为`634157`；**2026-09-24 00:08:23已完成全部8组、每组10,065帧及总体／七天气评测**，总耗时约162分钟。进程已退出，GPU2已释放。仅进行推理，未训练或更新权重。完整表与分析见[结果汇总](objdec_kradar_v1_interventions_results_260924.md)。

目的：在论文正式 K-Radar v1 主模型上检验空间 gate 的位置对应是否影响检测，以及 object-context 的 query/output 增量在固定权重推理中的作用。与此前 V2X 测试形成跨数据集补充。

## 固定模型与协议

- 权重：`logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`。
- 权重 SHA256：`99eb07e8a0b01ec397d3f2ac890091fe539194149a2c542cf41c465c9f02a2d3`。
- 使用该实验的原始 `config.yml`，严格加载权重；FP32、eval 模式。
- K-Radar v1 固定完整测试集 **10,065 帧**，C+L+R 输入，Sedan；原 ROI `[0, -6.4, -2, 72, 6.4, 6]`。
- 与主表一致：`score > 0.3`，原始 v1 **11-point AP**，IoU=0.3/0.5/0.7 的 3D 与 BEV。
- 从同一批预测中计算总体及七种天气结果，不为不同天气选取不同模型。

历史主表对应的核验值：

| 来源 | AP3D@0.3 | AP3D@0.5 | AP3D@0.7 | APBEV@0.3 | APBEV@0.5 | APBEV@0.7 |
|---|---:|---:|---:|---:|---:|---:|
| 原始完整测试集、conf=0.3 | 88.3550 | 67.5013 | 22.0390 | 88.8390 | 88.0953 | 62.6322 |

原始来源：[all_conf0.3.json](exp_260812_232650_TaskDecControlRobust_v1_model0_full/per_condition/all_conf0.3.json)。本次先评分baseline全集，与上述六项逐一核对；差异最大为**0.02125个百分点，核验通过**。预先固定的停止容差为0.05个百分点。这里的容差用于发现协议/链路问题，不是宣称微小差异具有统计意义的阈值。干预差值统一减本次baseline。

## 八组设置

| 标识 | 实际操作 | 回答的问题 |
|---|---|---|
| `baseline` | 保留全部原始推理路径 | 同次运行的参照结果 |
| `gate_mean` | 每帧 1,440 个位置的 gate 全部替换成该帧均值 | 保留平均调制强度、移除空间变化后会怎样 |
| `gate_shuffle_260923` | 打乱该帧 gate 的空间位置，保留全部数值 | 正确的位置对应是否重要 |
| `gate_shuffle_260924` | 第二个预先指定的随机种子 | 检查结果是否依赖单次打乱 |
| `gate_shuffle_260925` | 第三个预先指定的随机种子 | 同上，报告三次结果及均值/范围 |
| `no_query` | 仅将 object-context 的 query 增量置零 | 查询调制增量的推理贡献 |
| `no_output` | 仅将 object-context 的融合输出增量置零 | 输出调制增量的推理贡献 |
| `no_query_output` | 同时关闭上述两个增量 | 两种增量共同关闭的影响 |

打乱由“种子标识＋帧身份”的稳定哈希产生，便于恢复与复现；不挑选表现最差的一次打乱。三个种子是**推理干预重复**，不是三次独立训练。

gate 改动一致作用于 token 残差、模态缩放以及被 gate 调制的 object context，检验的是架构中整个空间 gate 的作用。`no_query` 不移除 query 或 cross-modal attention，`no_output` 不移除融合输出；它们只关闭对应的 context 增量，并保留 token modulation。

## 实现与预检

每帧只运行一次相机、LiDAR、雷达编码器，再将同一份编码特征用于八种融合/检测设置。这既节省重复编码时间，也让各设置的输入特征严格配对。干预由本次独立脚本在运行时注入，未编辑原有模型、训练脚本、评测器或 checkpoint。

已通过 8 个均匀抽取测试帧的预检（索引 0、1437、2875、4313、5750、7188、8626、10064）：

- 捕获原生网络的编码特征后，新流程的 baseline 与原生网络预测框、分数、类别逐项完全一致；八组运行后恢复 baseline 也完全一致。
- 均值化保持每帧 gate 均值；打乱保持全部 gate 数值及分布。
- 对应 query/output 增量确实归零，其他增量保留。
- 真实 GT 不进入本次正式推理：legacy 检测头在 eval 中仍要求 `gt_boxes` 字段，因此传入全零占位，原始 GT 仅在预测结束后交给格式导出与评分。
- GT 文本、样本顺序、天气描述与历史完整测试集档案逐帧比对；原始 KITTI 解析器与内存解析器对照通过。
- 预检峰值 PyTorch 分配显存约 **1.01 GiB**；进程实际显存以 `nvidia-smi` 为准。

原生网络在少数帧重复独立编码时本身存在输出波动，因此没有把“独立重跑两次完全相同”作为已达成的结论；预检使用原生编码输出做配对验证。失败的早期预检材料保存在输出目录中。本次全量baseline已完成上述历史AP复核；9月24日收集时再次核对模型、脚本与权重哈希一致。

预检评分只用于验证评测链路，并通过重复少量帧满足旧评测器的分块要求，已明确标记 `synthetic_smoke_only`，**不能用作论文实验结果**。

## 运行与输出

输出目录：[objdec_kradar_v1_interventions_260923](../analysis_exports/objdec_kradar_v1_interventions_260923/)。

实时查看：

```bash
tail -n 20 -F /home/hongsheng/dec_con_asf/analysis_exports/objdec_kradar_v1_interventions_260923/run.log
```

状态文件：`status.json`；启动记录：`launch.json`；冻结配置与源文件哈希：`manifest.json`；预检证据：`smoke/audit.json`。推理每 25 帧更新进度，每 100 帧压缩保存预测框与评测标签，支持从完整分块恢复；不保存全量特征、不复制权重或数据集。

推理结束后脚本自动计算指标并导出：

- `baseline_verification.json`：本次 baseline 与历史主表的六项差值。
- `results.json`：八组的总体及七种天气完整结果。
- `comparison.csv`、`results.md`：总体六项 AP 及相对 baseline 的差值。
- `shuffle_summary.json`：三个打乱种子的均值、范围及平均差值。
- `results_partial.json`、`metrics.log`：逐组评测进度及原始文本。

## 论文用途

这是固定模型的**推理干预**，与已有重新训练的“去前景门控”“去 object context”组件消融互补，不能混称为同一种消融。若打乱或均值化导致稳定退化，可支持空间对应在正式模型推理中有用；若 query/output 改动很小，应如实说明其即时贡献有限，不据此反推训练阶段无用，也不预设它们一定带来显著收益。

完整评测与baseline核验已通过。gate均值化使3D@0.3/BEV@0.5下降34.46/34.94点；三次空间打乱平均下降67.07/67.10点。同时关闭query与output增量仅使这两项下降0.0146/0.0087点，不能声称两条增量各自均贡献明显收益。建议正文机制分析给紧凑干预表，附录保留所有设置、全部IoU、天气结果及干预定义；具体边界见[结果分析](objdec_kradar_v1_interventions_results_260924.md)。
