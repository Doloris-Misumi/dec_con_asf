# V2X-Radar-V 完整 TaskDec 架构适配与受控实验

启动：2026-09-16 00:32（北京时间）。目标处于 active，以下仅记录实证进展，不代表已完成训练。

## 当前状态（2026-09-16 08:11 接续核查）

- **下载和数据准备已完成**：两包 SHA-256、CRC/文件覆盖通过，11,390 帧；原始 train/val/test=8391/1498/1501。主评测去重 val/test=1487/1486。原始压缩包保留，无重复下载。
- **完整 C+L+R 架构接入、梯度及小样本学习检查通过**。融合器为正式 TaskAwareDecControlledA2Fusion 的原样快照，TaskDec 负责主融合路径；不是简化 gate 插件。
- 三组稳定吞吐均已测得：concat 0.1482、patch 0.2117、TaskDec 0.2405 秒/批，batch2 FP32；80轮预计合计约56 GPU小时，另留评测/保存/并行余量。
- **评测器已修复并验证**：CUDA_HOME 固定11.3；修复可选 AOS 输出问题；原旋转框内核的重合边界数值错误改为双精度多边形裁剪。完美预测AP100、空预测AP0；10000框对独立OpenCV交面积最大误差5.34e−5m²。原失败日志与官方源码均保留。
- 正式协议和三组初始权重已锁定：80轮、FP32、micro-batch2、累积4、seed260916；共享编码器/head哈希一致，patch公共参数逐张量一致。正式入口8批训练→验证→保存→加载检查通过，烟测权重不用于正式训练。
- 已于08:11启动独立训练控制器 PID `3877430`，运行状态见下列动态文件。计划 GPU0 TaskDec；GPU1 concat 后接 patch。**启动控制器不等于训练完成；正式AP尚未产生。**
- GPU0/1 原有服务 PID140899/140935保留。GPU2 ASF仍运行；L4DR训练与自动评测状态已complete，但本实验仍不使用GPU2/3。

实时状态：`analysis_exports/v2x_taskdec_260916/controlled_80ep/controller_status.json`、`summary_status.json`。控制器日志：`controlled_80ep/controller.log`；各组日志/状态：`controlled_80ep/{taskdec,concat,patch}/{train.log,status.json}`。

架构与锁定协议：[taskdec_v2x_architecture_protocol_260916.md](taskdec_v2x_architecture_protocol_260916.md)。自动结果表：`controlled_80ep/results.md`、`complete_metrics.csv`、`main_table_rows.tex`，只有已完成评测才写入最终AP。

目标保持 active，主训练、最终评测和论文结论仍待实测。

<!-- V2X_LIVE_STATUS_BEGIN -->
## 自动运行观察（每五分钟更新）

核查时间：2026-09-17T19:41:58.922065+08:00

| 实验 | 状态 | PID已验证存活 | 已完成轮数 | 当前批次 | 训练秒/轮及依据 |
|---|---|---|---:|---:|---|
| taskdec | complete | False | 80 | 4196 | 885.1 (completed_training_epochs) |
| concat | complete | False | 80 | 4196 | 535.7 (completed_training_epochs) |
| patch | complete | False | 80 | 4196 | 762.0 (completed_training_epochs) |

当前排队顺序下的条件排期（显式计入剩余定期验证、最佳/末轮最终评测，再加25%预留）：2026-09-17T19:41:58.922065+08:00。
此时间是预测，首轮未结束时依据部分批次；不代表训练或评测完成。
验证开销优先使用该组已完成评测的均值；未启动组参考其他组实测。训练缓存、预测数量及并行干扰变化会影响排期。
完整状态与真实进程证据：`analysis_exports/v2x_taskdec_260916/controlled_80ep/runtime_observation.json`。
结果表与全部指标：同目录 `results.md` / `complete_metrics.csv`；论文LaTeX完整表：`paper_main_table.tex`。
<!-- V2X_LIVE_STATUS_END -->

## 启动时状态（历史记录，不代表当前状态）

- 已核实原下载控制器 PID `3822890` 和 aria2 PID `3822892` 存活；未重复启动下载。
- 自动数据接管 PID `3829968` 已运行并核实存活。按分钟观察原下载；仅在原进程结束且未成功时最多重试三次断点续传。完成后独立计算 SHA-256，再做无覆盖解压、CRC 校验和完整划分/文件覆盖核对。
- GPU0/1 上已有 PID `140899` / `140935`，显存约 8.6 / 8.5 GiB；不将其视为空卡。尚未启动新 GPU 作业。
- GPU2/3 上 ASF PID `3796685`、L4DR PID `3798840` 仍训练，保留至各自自动全量评测结束。
- 已阅读用户指定五份记录，核查正式融合器、配置、skeleton loss，以及现有 VoD 的原生 PP 适配。正式完整融合器已按原文件保存到独立目录并记录 SHA-256。
- 原 `rl_3dod` 环境是 Python 3.8.20 / torch 1.10.1+cu113，有 torchvision、spconv、einops、easydict；缺 mmcv/mmdet/mmdet3d。正在建立独立 venv，只读复用原环境已安装依赖；不向现有环境安装或升级软件。

## 路径与命令

代码目录：`/home/hongsheng/dec_con_asf/v2x_taskdec/`。

产物目录：`/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/`。

原下载日志：`/home/hongsheng/datasets/V2X-Radar-V/download.log`。

数据接管日志：`analysis_exports/v2x_taskdec_260916/data_preparation.log`。

数据接管状态：`analysis_exports/v2x_taskdec_260916/data_preparation_status.json`。

接管启动命令（已启动，不要重复运行）：

```bash
/home/hongsheng/miniconda3/bin/python -u /home/hongsheng/dec_con_asf/v2x_taskdec/prepare_data.py
```

查看进度：

```bash
tail -n 10 -f /home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/data_preparation.log
```

预期数据位置：`/home/hongsheng/datasets/V2X-Radar-V/extracted_260916/V2X-Radar-V/training/`；划分位于相邻的 `extracted_260916/ImageSets/`。数据接管仅解压和验证，不会直接启动未经检查的训练。

## 数据与协议审查

固定 HF revision：`c38cce27cd84fdbd5671a797dd6df2bbe3dcc907`。

| 包 | 字节数 | 官方 SHA-256 |
|---|---:|---|
| V2X-Radar-V.zip | 23926089849 | `3d7506ccd8716e70cccdb3ec034de42c439b2a01399da04bef3f6f6fafbd93df` |
| ImageSets.zip | 48903 | `fc3426ec086f8b984ab3ad964ffc9e9eb21cd03a8ab1b271f74f956755401bb0` |

先前 ZIP 目录核查得到 train/val/test = 8391/1498/1501；本轮仍须等完整文件校验后复核。尚未完成数据几何检查。

已下载固定官方代码 revision `1624751e31260c68d544e60599079d2104ee8a73` 的六份数据转换、车辆端配置和评测文件，保存于 `official_sources/`，URL 和哈希见 `official_sources/sources.json`。

**发现必须避开的划分问题：** 官方车辆端 BEVDepth 示例 `train_dataloader()` 读取 `trainval.pkl`，`val_dataloader()` 又读取 `val.pkl`。这两者在当前 ImageSets 定义下会重叠。本实验明确使用 `train.txt` 训练、`val.txt` 验证；test 仅在配置和选模规则锁定后用于最终结果，不照抄该训练入口。

官方配置 BEV 范围为 x=[0,102.4]、y=[-51.2,51.2]，0.4m 网格；当前相机配置训练五类，但评测 current_classes 仅列 Car/Pedestrian/Cyclist。官方 KITTI 评测代码默认 R40，提供严格 0.7/0.5/0.5 和宽松 0.5/0.25/0.25 的 3D/BEV 阈值。最终类别、GT 过滤与 ROI 在读取真实数据及核对 evaluator 外层后锁定，暂不宣称与文献完全同协议。

官方转换脚本将相机底面中心经逆外参转到 LiDAR，再加半高；yaw 使用 `pi/2 - rotation_y`。仍需根据实际标定矩阵验证朝向，不能直接套用另一数据集的 yaw 公式。雷达通道和坐标尚待核对。

## 架构迁移审查

正式原文件：`models/fuser/patch_dec_a2_fusion.py` 的 `TaskAwareDecControlledA2Fusion`。独立快照：`v2x_taskdec/fuser/`，哈希清单 `fuser_provenance.json`。

| 组成 | 真实代码路径 | 迁移要求 |
|---|---|---|
| canonical patch / CASAP / PFT | `A2Fusion` 的 to_embed、to_patch_embed、MultiheadAttention、pft、to_fused_feat | 保留主融合骨架，明确继承 ASF |
| common / unique | 各模态 MLP 与前景上的去相关、一致性、差异约束 | 保留表征与监督，不声称严格可辨识分解 |
| 前景与模态控制 | `_dec_control_scores`、gate、受限 token_scale、解耦残差 | 各模态独立输入，在融合前产生控制 |
| 任务上下文 | `_task_context`、query_delta、fused_delta | 保留 query 与输出的两处调制；按目标类别配置监督 |
| 检测损失 | skeleton 将 patch_dec_loss 加入检测损失 | 新训练入口必须显式聚合，不能只 forward 而漏掉辅助监督 |

现有 VoD 原生 `BaseBEVBackbone_TaskDecPP` 确实调用完整类，可作为点云接口参考；其旧配置和初始化、AMP 差异不直接继承到本次对照。更早 `SimpleBevEncoder` 是烟测实现，不作为本次合理原生基线。

相机优先评估复用已有 `CamBase` 的图像骨干、LSS 几何与 BEV pooling；其实现不依赖缺失的 OpenMMLab 栈。仍需用车辆端标定、实际图像尺寸和新 ROI 验证，尚未决定降为 L+R。

## 三组受控设计（预算尚未锁定）

1. 独立传感器编码器 + concat/conv 原生融合 + 统一 BEV neck/head。
2. 相同编码器/neck/head + ASF canonical patch attention，不含解耦及任务控制。
3. 相同编码器/neck/head + 完整 TaskDec 主融合。

共享参数初始化须显式拷贝并核对哈希，不仅依赖相同随机种子。三组均固定数据、micro-batch、有效 batch、精度、调度、训练更新数与选模规则；记录实际 GPU 时间，不声称参数量/运算量严格相等。是否使用 ImageNet 或目标域预训练需在配置中明确且对齐。先以稳定 FP32 检查学习与显存，避免沿用 VoD 的 AMP/FP32 不一致。

## 尚未完成与下一步

- 数据 SHA/解压、几何/投影/点云通道/增强一致性检查。
- 三组完整网络、真实样本前后向及所有关键路径梯度检查。
- 小样本过拟合与约 200 个稳定 micro-batch 显存、吞吐实测。
- 依实测锁定 epochs/有效 batch、训练/验证/最终 test 协议，9 月 17 日前给出排期。
- 三组全量对照、完整评测表、GPU 开销、复现记录与结论边界；均尚无结果，不填入成功数字。

目前没有必须用户处理的阻碍。目标保持 active；本轮属于实质进展。

## 00:45 融合器接口验证

独立 venv 已创建完成。CPU 合成输入上的 L+R 与 C+L+R 两种接口均通过；canonical patch、common/unique、前景 gate、模态 score、task head/context 与 attention 均得到有限非零分支梯度。推理输出在提供、移除或更改 GT 时完全一致；关闭 TaskDec 控制后，与相同共享参数的原始 patch attention 输出逐元素一致。证据：`analysis_exports/v2x_taskdec_260916/fuser_contract.json`。

这只证明完整融合器快照的接口与计算链正常，不代表真实数据网络已接入或学习有效；尚未使用新 GPU。测试首次因检查脚本中参数前缀名称写错而失败，按真实 `dec_control_fg_gate` / `dec_control_score` 更正后通过；未修改正式融合器。

复现命令：

```bash
cd /home/hongsheng/dec_con_asf
PYTHONDONTWRITEBYTECODE=1 v2x_taskdec/.venv/bin/python -m v2x_taskdec.check_fuser_contract
```

## 01:23 三模态接口初版与协议补查

新增 `v2x_taskdec/model.py`、`dataset.py`、`geometry.py`、`audit_data.py`，代码尚未通过真实数据/GPU验证。模型初版共享 ResNet-50/LSS 相机、两个独立 PointPillars 编码器、BEV neck 和 AnchorHeadSingle。三种融合仅选择 concat/conv、原始 A2Fusion、完整 TaskAwareDecControlledA2Fusion，不串联旧融合器。使用现有 OpenPCDet 组件而非早期 SimpleBevEncoder 烟测模型。

计算规模初案为 0.4m BEV、4×4 patch、128维 patch、16 query、8 attention heads，完整控制/上下文保持；这属于新数据的分辨率与宽度适配，不能描述为原 K-Radar 参数量完全不变。ASF 的 SCL 不属于新增 TaskDec 控制，当前三组均未启用它。最终训练预算仍待实测。

已验证 CPU spconv voxelizer API，三点生成两个预期 pillar；坐标转换在标准 KITTI 轴定义下 camera→LiDAR→camera 往返通过，联合 flip/rotation/scale 后 GT 框八角点集合与点云相同变换一致。真实标定可能有 pitch/roll，必须检查水平检测框近似的投影误差。数据增强对 camera lift 使用同一 world_aug 矩阵；不做缺少图像对应更新的 GT 数据库粘贴。

官方论文 https://arxiv.org/html/2411.10962v3 的 Table 4 将 car/bus/truck 合为 Vehicle，当前代码外层未发现相同合并。其论文 ROI 与当前 camera 配置 ROI 也有差别。本实验将固定自洽的本地协议并分别记录论文/代码差异，不直接借用文献表进行同协议排名。待实际数据审查后确定 Vehicle/Pedestrian/Cyclist 三类映射、雷达字段和最终 ROI。

下载 01:22 已到 99%；原进程仍正常，尚未标为解压完成。后续先运行 `python -m v2x_taskdec.audit_data`，依据所有 bin 文件的字节整除和 12 个训练样本的通道分布核查真实输入，避免套用 VoD 雷达七通道语义。

## 01:29 下载传输完成、正在独立校验

原 aria2 控制器于 01:25:02 报告 complete；接管进程随后进入独立 SHA-256 校验。尚不能据此声称解压完整。已启动受限等待后的 CPU 审查命令，数据接管 complete 后自动运行 `v2x_taskdec.audit_data`；日志为 `data_geometry_audit.log`，结果为 `data_geometry_audit.json`。

相机 CPU 构造及 ImageNet 权重 strict load 已通过，权重 SHA-256 记录于 `camera_constructor.json`。三组网络和数据 loader 均为初版，尚无 GPU 前向或训练结果。

## 01:50 数据格式、几何、重复帧与学习验证

两份 SHA-256 均匹配，解压 CRC/文件数/划分全部通过。完整性证据 `data_integrity.json`，原压缩包保留。实际为 11,390 帧、五类文件各 11,390 份、train/val/test=8391/1498/1501。

**当前公开包混有格式与坐标体系。** 全量扫描 `point_schema_audit.json` / `point_schema_manifest.json`：LiDAR 原四列255强度7460帧、四列归一化强度3482帧、六列216帧、全零232帧；雷达原五列255强度7460帧、四列归一化强度3712帧、五列归一化强度186帧、全零32帧。LiDAR存在234,232,452条非有限记录，雷达2条。使用逐文件清单，过滤非有限与全零点；全零模态不删除对应帧。六列LiDAR的ring/timestamp不作为输入。四列雷达缺少第五个标量通道，补零并加入字段可用性位；不将缺字段误写为测得的零速度。格式识别依赖记录宽度、时间字段和数值布局，未知/歧义会报错，本轮扫描无未识别文件。

雷达使用每帧 `Tr_radar_to_velo`；原LiDAR既有x向前也有y向前的平台，现统一到相机光轴水平投影为ego前向、左向为y、z向上的共同坐标。GT、两路点云和相机lift均一致变换。不能直接复用旧数据集yaw捷径或不处理外参。`geometry_checks.json`覆盖训练集每种布局的代表帧；联合旋转/缩放/反射的角点与投影数值检查通过，已人工查看 000006/009000/009004/009041 四帧叠图，框和路面场景无明显坐标错位。其余PNG与完整标定保留可查。

**官方split存在相同内容的不同ID。** ZIP CRC+size初筛54组重复图像，SHA-256确认其中22组跨划分重复；这些组图像、LiDAR、radar、标签均相同。12组涉及train/test、9组涉及train/val、1组涉及val/test。审计见 `cross_split_duplicates.json`。在模型选取前已冻结 `evaluation_splits/val_deduplicated.txt`（1487）与 `test_deduplicated.txt`（1486）：训练仍用原8391；val排除train相同图像、test排除train或原val相同图像，并去除自身重复。官方原split未改，完整原split AP作为补充；主选模使用独立去重val。重复规则与ID/hash见 `evaluation_split_audit.json`。该数据准备判断不依据模型预测。

工程配置 `engineering_config.json`：C+L+R、Vehicle(Car/Truck/Bus)/Pedestrian/Cyclist，统一ego ROI x[0,102.4],y[-51.2,51.2],z[-5,3]，0.4m pillar；相机288×512，ResNet50 ImageNet初始化；全部编码器参与训练。anchor尺寸/底面高度来自训练集ROI内中位数，不使用val/test估计。其它原始标签保留在数据中但不列入这三类指标。训练预算尚待最终锁定。

**GPU0完整网络检查通过。** `smoke_taskdec.json`三帧含跨平台和全零LiDAR情形，检测损失/辅助损失/梯度有限，所有可用编码器与head/neck/fuser可反传，推理框有限；batch1峰值2.017GiB。`learning_check.json`四帧300步过拟合通过：均值loss 2.2302→0.00816，31个GT上IoU≥0.5同类别召回83.87%，峰值3.640GiB。仅作为工程学习验证，不是验证集AP。

第一次真实DataLoader吞吐检查因pin_memory将tuple转list而未将点云tensor搬到GPU，已修复递归to_device；保留原失败日志，未改正式模型结构。独立重测 `throughput_taskdec.json` 已通过：micro-batch2，220步去前20步后稳定200步均值0.24055s，中位0.23896s，p95=0.26567s；真实loader为4196批/8391帧；峰值分配3.758GiB、缓存6.475GiB，FP32全编码器训练，总参数33,955,125。单轮条件估算约16.8分钟，不含验证、保存和并行干扰。

GPU1批量启动请求自动审批曾超时（不是安全拒绝），尚未执行；允许的一次重试改为独立concat烟测，已成功启动。未中断现有服务或GPU2/3实验。后续完成concat/patch烟测与吞吐，并依据以上实测锁定三组统一预算及自动末轮评测。

## 08:12 正式队列启动核实

控制器PID3877430已实际启动TaskDec PID3877508（GPU0）及concat PID3877510（GPU1），两组均进入第1轮，首批损失有限。patch排队等待concat训练与最终评测完成。正式训练没有加载工程过拟合或pipeline smoke权重。

正式目录：`analysis_exports/v2x_taskdec_260916/controlled_80ep/`。每组的`launch.json`保存实际命令、PID、GPU和启动时资源；`initialization.json`保存权重SHA与共享张量核对。`source_snapshot_after_pipeline_review.tar.gz`是正式启动代码快照，早期快照同时保留；末次启动前修订仅更新状态字段和进程成本记账，配置和初始权重未变。

待核实：首个完整epoch的真实耗时和全量val评测；随后完成80轮三组和最佳/末轮原始+去重val/test。当前没有完整AP结论，不以早期val涨跌调整协议。

## 08:24 全训练集标签往返复核

补查全部8391个训练帧、ROI内69599个框。Vehicle/Pedestrian/Cyclist的坐标往返3D IoU保守下界分别为0.997670/0.998708/0.999696，无框低于对应严格阈值。位置误差最大4.215e−6m，朝向误差最大0.000220724rad；仅证明此坐标适配的内部几何一致性，不代表检测AP或标定真值正确。

首次OpenCV参考计算在近乎重合边界上产生错误低IoU，已保留原始审查文件并明确更正。正式双精度评测器对29个代表框的最低实际IoU为0.999956。说明和复现：`analysis_exports/v2x_taskdec_260916/label_roundtrip_audit_correction.md`；最终审查：`label_roundtrip_bounds_audit.json`、`near_coincident_evaluator_check.json`。此次未修改正式训练源码、初始权重或锁定协议。

## 08:35 首轮完整训练耗时与验证阶段

TaskDec/concat均完成8391帧、4196批、1049次更新；训练耗时分别1004.845/1004.373秒（约16.75分钟），目前进入1487帧全量去重val，完整AP尚未输出。08:34主进程PID3877508/3877510确认存活并有CPU计算活动，内存约6GiB，未见失败；不因日志暂未新增而重复启动或重跑。

并行时concat显著慢于单独工程测速，若持续该速度，其80轮纯训练约22.32 GPU小时而非13.82；TaskDec约22.33 GPU小时。patch仍未正式开始，保留独立工程估计约19.74 GPU小时。因此当前三组纯训练条件估算约64.4 GPU小时，另加验证和保存，不再将初始56小时估计当作正式实际成本。所有预算、初始化与选模协议保持锁定。

## 08:44 首轮全量验证及第二轮衔接通过

concat与TaskDec均完成1487帧全量去重val，42项指标齐全且有限，最佳及末轮checkpoint已保存，实际进程均进入第2轮。首轮严格moderate三类平均3D AP分别2.206971与1.239448，仅作为早期学习记录，不据此调整协议或推断最终架构优劣。

验证总耗时分别869.197与844.044秒，推理约162秒，逐框转换占较大CPU开销；独立合成1500框转换耗时0.521秒，与首次高密度预测转换的长等待一致。证据`controlled_80ep/first_epoch_pipeline_receipt.json`、各组`val_epoch_001.json`、`epochs.jsonl`和`best.pt`/`last.pt`。全训练与最终test尚未完成，goal保持active。

## 08:47 将实测验证成本纳入排期

观察器已升级为显式计入剩余16/16/17次定期验证及最佳/末轮在原始+去重val/test上的最终评测，再加25%余量。首轮验证实测844.0/869.2秒，据此保守预测三组完成约为2026-09-19 03:17；后续轮次缓存和预测密度变化会使估计更新。证据`controlled_80ep/schedule_revision_after_first_validation.json`。仅替换本任务自身观察器（新PID3880755），没有停止训练或修改协议。

另核实原ASF仍在第7/11轮，L4DR训练及自动评测已complete；GPU2/3继续保留，不提前启用。主要对照仍按9月22日前完成规划。

## 08:52 完成交付核验入口

新增独立`analysis_exports/v2x_taskdec_260916/audit_delivery.py`，仅在三组和控制器均完成后读取大checkpoint。核对80轮/83920次更新、每轮8391帧、17次固定验证、按val最大值且同分取早的选模、最佳/末轮权重哈希、所有原始val/test预测帧、4个划分×2个checkpoint的全部42项指标，以及1008行CSV逐值一致性。GPU进程时长保留轮询上界及可核实下界，避免把最多5分钟退出观察延迟当成精确GPU计算时间。

当前执行输出明确为incomplete（训练及patch排队未结束），不能当作交付验收通过。观察器PID3881196会在控制器退出完成记账后自动运行核验并生成`controlled_80ep/delivery_audit.json`与日志；自动检查通过后仍需人工式结论边界复核，不自动将goal标为complete。正式训练源码与协议均未更改。

## 09:35 原生融合第5轮验证完成

concat第5轮在1487帧去重val上严格moderate三类平均3D AP=33.238684，42项指标齐全且有限，验证耗时753.366秒；按既定规则保存为当前最佳，已自动进入第6轮。证据`controlled_80ep/concat/val_epoch_005.json`。TaskDec第5轮仍训练，不能用不同轮次比较得出架构结论；三组80轮预算、选模及最终test协议均不变。

## 09:56 两组第5轮同轮次验证

TaskDec第5轮在1487帧去重val上的严格moderate三类平均3D AP=32.444691；同轮concat=33.238684，差值−0.793993点。两份42项指标均齐全且有限。TaskDec本次验证耗时759.384秒，保存当前最佳后已自动进入第6轮。

该结果仅为早期同轮次学习记录，patch尚未正式运行，不能据此形成三组架构结论。保留当前负差值，不改变80轮预算、初始化、阈值、固定选模或最终测试规则。证据：`controlled_80ep/{taskdec,concat}/val_epoch_005.json`。

## 10:31 原生融合第10轮验证

concat第10轮去重val严格moderate三类平均3D AP=42.364754，验证耗时745.130秒，1487帧和42项指标完整；保存当前最佳后已进入第11轮。证据`controlled_80ep/concat/val_epoch_010.json`。TaskDec仍在第8轮训练，无失败；不以不同轮次指标作最终架构比较，固定预算与协议不变。
