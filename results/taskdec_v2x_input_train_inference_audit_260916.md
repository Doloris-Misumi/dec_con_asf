# V2X-Radar-V 输入、训练与推理链路排查

日期：2026-09-16，约 14:55。范围：当前 `controlled_80ep` 三组架构迁移实验；只读检查原实验，独立诊断不更新模型权重，不改变正式协议、源码、checkpoint 或队列。

## 结论

尚未发现能够解释此前同轮次约 18 AP 差距的坐标错位、类别编号错误、融合器训练/推理分支不一致或评测框格式错误。不能因此宣称全部数据/所有算子已无问题，但新做的实际 checkpoint 和几何检查降低了这些解释的可能性。

确认两个重要事实：

1. 模态控制 softmax 已高度饱和到 LiDAR，失去明显的随位置调节能力；实际多头注意力仍使用三模态，不能称为整个网络只剩 LiDAR。
2. 当前迁移配置与 K-Radar、VoD 成功设置差别很大，且后续 TaskDec checkpoint 仍在改善。不能用早期 V2X 分数直接否定原方法，也不能将当前负对照写成成功泛化。

## 复核方式与证据

诊断目录：`analysis_exports/v2x_taskdec_260916/chain_audit_260916/`。只保存脚本和小 JSON/日志，未保存中间特征或额外大 checkpoint。首次 GPU 诊断峰值分配约 2.67 GiB；使用 GPU0，单进程显存上限 16%，检查结束后退出。

- `audit.py` / `audit.json`：从 1487 帧去重 val 的 ID 列表等间隔选定 64 帧（选择不依赖结果），包含 532 个 ROI 内三类 GT；记录实际 checkpoint epoch/SHA。比较正常推理、临时关闭 TaskDec 控制、临时使用当前 batch 的 BN 统计；仅内存中改变独立模型。
- `attention_and_geometry.py` / `.json`：同一批 64 帧的真实注意力、控制概率、局部特征变化、独立原生/相机坐标 IoU 对照以及 AP_R40。全部是诊断结果，不参与正式选模。
- `data_geometry.py` / `.json`：train/val 各 128 帧，检查同 ID 文件、标签往返、图像 resize 后投影逆变换与联合增强几何。
- `spatial_contract.py` / `.json`：通过真正的 CUDA BEV pooling 和点云 scatter 放置非对角脉冲，验证 `[y,x]` 顺序；精确验证 patch 输出恢复顺序。

正式源文件及输入清单哈希核查通过。原正式初始化脚本为三组复制相同编码器、neck、head 张量；patch 与 TaskDec 的共有 A2 参数逐项相同。`initialization.json` 中两组 `patch_shared_hash` 不同是因为 TaskDec 的集合还包括其额外分支，不能单凭此字段判断共有权重不一致。

## 1. 链路检查结果

| 检查 | 实测结果 | 解释边界 |
|---|---|---|
| 三模态样本 ID | train/val 抽查各128帧，无缺少对应文件 | 不能替代原始数据物理同步真值 |
| 相机框→ego→相机 | 中心最大误差约 3.8e−6 m | 证明内部变换一致，不证明标定真值正确 |
| resize 后相机 lift 与点云坐标 | 未增强最大误差约 4.3e−14 m；联合增强后小于 7.3e−6 m | 检验连续几何；不代表学习深度准确 |
| 相机 BEV / 点云 scatter | `(x,y,z)=(3,7,0)` 均落在输出 `[y,x]=[7,3]`，张量完全相同 | 单独检验排列，避免方形网格隐藏转置错误 |
| patch→BEV 顺序 | 索引张量还原逐元素完全相同 | 无发现 patch 展开顺序错误 |
| GT 前景 patch 掩码 | 两个实测 checkpoint 的抽查 batch 与独立 NumPy 判定一致 | 正式三类编号为 1/2/3，padding 为0 |
| TaskDec train/eval | 固定真实编码器特征，融合输出最大差为0 | 隔离融合器；不声称整网 BN 的 train/eval 相同 |
| 推理 GT 依赖 | 将 GT 的 xy 移动30m，推理融合输出最大差为0 | 未发现推理依赖训练 GT 或 teacher forcing |
| 预测框原生/相机 IoU | 三次合计3678对，逐组平均绝对误差约 2.8e−5～3.8e−5，最大0.00748 | 非严格数学等价；未发现大规模轴/尺寸错位，仍有数值/姿态近似差异 |

训练循环也已逐段读取：每轮恢复 `model.train()`，验证显式 `model.eval()`；统一 FP32；有效 batch=8 来自 micro-batch=2、累积4次，末尾不足8样本按实际样本数归一化；三组共享 loader/标签、head、decode 和 evaluator。**梯度累积不把 BN 的实际统计 batch 扩大成8。**

## 2. BN 和控制分支干预

以下是64帧中同类别、score≥0.1、严格 IoU 下的 GT 加权召回率，**不是 AP，也没有做一对一精度统计**。

| checkpoint | 正常推理 | 改用当前批次 BN 统计 | 关闭全部 TaskDec 控制 |
|---|---:|---:|---:|
| TaskDec epoch10 | 58.08% | 57.89% | 49.81% |
| TaskDec epoch22 | 69.74% | 70.30% | 61.28% |
| concat epoch30 | 75.94% | 76.88% | 不适用 |

这组检查不支持“BN 推理开关一改就能恢复巨大差距”的解释。关闭控制反而退化，说明当前 checkpoint 已依赖控制分支；这种推理干预不能替代重新训练的消融，也不能证明控制设计优于原始 patch。

在一个固定两帧 batch 上，weighted auxiliary loss 对三路 BEV 输入的梯度范数约为 detection loss 梯度的 4%～12%。没有看到该 batch 的辅助梯度压倒检测梯度，但不能据此排除整个训练过程中存在目标冲突。

## 3. 已确认的控制饱和

对64帧按 batch 汇总，前景 patch 的平均模态控制概率为：

| checkpoint | Camera | LiDAR | Radar |
|---|---:|---:|---:|
| epoch10 | 0.0000030 | 0.9999700 | 0.0000270 |
| epoch22 | 约9.6e−10 | 0.9999992 | 约7.9e−7 |

但 epoch22 的实际前景多头注意力均值约为 Camera **28.55%**、LiDAR **47.14%**、Radar **24.31%**。控制概率经有界缩放作用于 K/V，不是最终注意力，也不是“模态贡献百分比”。因此准确描述应为：**模态控制分支近乎固定偏向 LiDAR，完整融合仍使用三路输入。**

它是需要处理的训练现象，但尚无因果证据证明它单独造成所有 AP 差距。现配置没有启用控制概率的平衡正则，三路编码器又在同时学习，LiDAR 先成为强分支后控制容易饱和，是合理待验证解释。

## 4. 迁移设置与成功实验不是同一配方

| 条件 | K-Radar 正式设置 | VoD 较好设置 | 当前 V2X |
|---|---|---|---|
| 编码器/初始化 | 三路检测预训练编码器，冻结参数；BN未冻结 | mild + PP-Concat warm start | 相机只有ImageNet初始化；点云编码器、相机深度lift等新建；全部联合训练 |
| 模态 | C+L+R | L+R | C+L+R |
| patch | 2×2 | 4×4，0.16m单元 | 4×4，0.4m单元 |
| patch物理边长 | 需结合原BEV分辨率理解 | 0.64m | **1.60m** |
| common / patch维度 | 256 / 256 | 64 / 128 | 64 / 128 |
| query数 | 32 | 16 | 16 |
| 融合输出通道 | 2048 | 128 | 128，后接新增共享neck |
| 模态控制强度 | 0.75 | mild=0.5 | 0.75 |
| 辅助监督 | 原正式配方 | mild进一步减弱 | 沿用K-Radar主要权重，外层0.12 |
| SCL | 启用 | 未启用 | 三组均未启用 |

当前每个模态把 4×4×64=1024 个标量压为一个128维 patch token，再通过 query 恢复细网格；物理覆盖面积比 VoD 的 patch 大 **6.25倍**。本次融合输出的 patch 内相对变化量也明显小于 concat（64帧每batch中位数再平均，epoch22约0.122、concat约0.466）。该量受背景、特征归一化和架构影响，**只能支持继续检查空间压缩，不能把它直接换算成定位误差或当作因果证明**。

VoD 记录也并非“任意从头训练都稳定胜过 concat”：首版 FP32 的 moderate AP_R40=74.71，concat=77.05；mild+warm-start 才到77.42。官方 EAA 提升为69.88→70.18。来源：`results/paper_vod_main_table_draft_260909.md`，以及 `TaskDec_PP_WarmPPConcat_MildS05AuxHalf.yaml`。这些经验尚未完整迁移到当前 V2X 设置。

## 5. 最新诊断不能被早期完整val分数掩盖

固定64帧、相同评测器下：

| checkpoint | Vehicle | Pedestrian | Cyclist | 三类平均 strict moderate AP_R40 |
|---|---:|---:|---:|---:|
| TaskDec epoch10 | 39.69 | 17.82 | 55.34 | **37.62** |
| TaskDec epoch22 | 58.04 | 37.65 | 67.46 | **54.38** |
| concat epoch30 | 64.10 | 47.02 | 72.30 | **61.14** |

TaskDec 后续 checkpoint 仍有明显学习进展。这里轮次不同，且只有64帧，**不能替代正式1487帧验证集，也不能据此宣称其完整val已经达到54.38**。正式epoch20的36.54与本表epoch22的54.38不能当作一次同协议完整val跳升。应等待既定epoch25全量验证。

## 后续判断顺序

1. 保持当前正式实验作为固定配方的对照；用下一次完整val确认后续学习趋势，不根据诊断子集改选模。
2. 原始patch基线非常关键：若它也明显落后concat，应优先检查patch压缩/新建编码器联合训练；若patch良好而TaskDec差，再隔离控制饱和、语义辅助监督和优化强度。当前patch尚无正式结果。
3. 若开展新实验，独立命名并固定预算，优先分别验证较小物理patch、VoD式mild控制/辅助权重、以及共享同等预训练或warm-start成本。每次改变一个主要因素；不能将新增训练成本藏进“相同预算”。
4. 这些是独立架构适配实验建议，不是已证实bug的修复。本轮没有擅自改动在跑配方，也没有启动新的长训练。

复现命令示例（需先确认GPU0仍有余量）：

```bash
cd /home/hongsheng/dec_con_asf
CUDA_VISIBLE_DEVICES=0 CUDA_HOME=/usr/local/cuda-11.3 OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 NUMBA_NUM_THREADS=3 PYTHONDONTWRITEBYTECODE=1 v2x_taskdec/.venv/bin/python analysis_exports/v2x_taskdec_260916/chain_audit_260916/audit.py
```

脚本读取运行目录中的当前 `last.pt`，重跑时epoch可能已变化；本轮的精确epoch及SHA以归档JSON为准。原 `best.pt` / `last.pt` 未复制或修改。
