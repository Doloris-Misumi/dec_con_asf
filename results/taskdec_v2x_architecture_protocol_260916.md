# V2X-Radar-V：完整 TaskDec 架构适配与锁定协议

2026-09-16。本文区分工程验证、正式训练与最终实验结果；正式 AP 以 `analysis_exports/v2x_taskdec_260916/controlled_80ep/results.md` 为准，未完成项不填造结果。

## 实际迁移的计算链

输入为同步前视相机、LiDAR、雷达（C+L+R）。图像经 ResNet-50/FPN、学习深度分布、LSS lift/BEV pooling 得到 BEV；两路点云分别通过独立 PointPillars VFE/scatter/BEV stem。三路独立特征为 64×256×256，空间范围 x=[0,102.4)、y=[−51.2,51.2)、z=[−5,3)，网格 0.4×0.4×8m。

完整 TaskDec 主路径：三路独立 BEV → canonical projection → 4×4 patch、128 维 token → 每模态 common/unique MLP → 前景 gate、模态评分及有界 token scale、common/unique 残差 → 任务上下文调制 query → 跨传感器 attention → 任务上下文调制输出 → PFT/unpatch → 统一 BEV neck 与 AnchorHeadSingle。16 query、8 attention heads；所有编码器均训练，没有先运行 concat 融合器再附加 TaskDec。

正式 `TaskAwareDecControlledA2Fusion` 来自 `models/fuser/patch_dec_a2_fusion.py` 的原样独立快照，SHA-256 为 `04bf1f4a1bf0a3874b36d3d5e70a2a052c95f09e24dde0fadbf929025bc67f51`。`A2Fusion` 快照 SHA-256 为 `6a918e943e61fc920949d95e811d1cd25dc859428df78649db7eba38fe4bce38`。数据集适配调整输入尺寸、通道、patch 宽度及类别数，未取消正式控制机制。完整有效参数保存在 `controlled_80ep/config.json` 的 `resolved_fuser`，不依赖日后原 YAML 修改。

继承边界：canonical projection、patch attention、PFT/unpatch 来自 ASF；ResNet、LSS、PointPillars、BEV neck 和 AnchorHeadSingle 是复用组件。TaskDec 的具体设计是将 common/unique 状态用于目标相关的 token、query 与输出控制，以及对应的前景、类别和表征约束。共同/特有概念本身不是首次提出；这些状态没有严格可辨识或统计独立的保证。当前类别上下文是 Vehicle/Pedestrian/Cyclist 监督，不是分类与回归任务分解。

损失：检测损失 + 0.12×TaskDec 辅助损失。辅助分支保留正式 common 一致性、unique 差异、common–unique 去相关、前景 gate 和类别上下文监督；其内部系数和控制强度来自正式 robust v1 配置。GT 仅用于训练损失，推理不读取 GT；已有 fuser contract 检查验证了这一点。三组均不启用 ASF SCL，避免其额外监督混入差值。

## 三组对照及能回答的问题

| 实验 | 主融合路径 | 参数量 | 解释 |
|---|---|---:|---|
| concat | 三路 BEV concat → 3×3 Conv/BN/ReLU | 33,136,685 | 同编码器和检测头体系下的合理本地原生融合基线；不称为官方 V2X 模型复现 |
| patch | 完整 ASF canonical patch attention | 33,478,957 | 相对 concat 检验 patch 融合结构；无 TaskDec 分解、控制和辅助损失 |
| taskdec | 完整 TaskDec 主融合 | 33,955,125 | 相对 patch 检验整套 TaskDec 解耦与任务控制的增量 |

三组不能独立归因到某个单一 TaskDec 组件，且参数量不严格相等；如预算允许，再补组件消融或重复种子。不能以本组三组实验声称已排除容量解释。

## 数据与评测协议

数据固定为 HF revision `c38cce27cd84fdbd5671a797dd6df2bbe3dcc907`；两份 ZIP 已按官方 SHA-256 校验，解压 CRC/大小/文件覆盖通过，压缩包保留。实际公开包 11,390 帧，ImageSets 原始 train/val/test=8391/1498/1501。图像、LiDAR、雷达、标定和标签各 11,390 份。

原 split 存在 SHA-256 确认的跨划分重复内容。训练保留全部 8391；主验证使用预先生成的 1487 帧去重 val，主测试为 1486 帧去重 test。val 排除 train 的相同图像，test 排除 train 或原 val 的相同图像，再去自身重复。保留原 split 的全量 AP 作为补充。规则与 ID 在模型预测之前已固定，见 `evaluation_split_audit.json`；这只能排除已发现的完全重复，不能保证序列级独立或不存在近邻帧泄漏。

公开包混有点云布局、不同强度尺度和全零模态。采用逐帧 schema 清单读取，过滤非有限/全零点但不删除对应帧；LiDAR 使用 xyz/intensity；雷达使用 xyz/intensity/第五星标量/字段可用性位。不把无字段的补零当作实测零速度，也不将未经官方字段证明的标量直接命名为物理速度。标定将原始 LiDAR 和雷达统一到相机光轴在地面的投影为前向的 ego 坐标。GT、点云和 camera lift 共同接受旋转/尺度/反射增强，不做未对齐图像的 GT 数据库粘贴。

目标三类 Vehicle=Car/Truck/Bus、Pedestrian、Cyclist；训练 anchor 尺寸和底面高度仅由训练集 ROI 内统计。ROI 按框中心过滤。其他标签类别不参与这三类本地指标。预测按同 ROI、有限值、正尺寸、相机前方和投影可见角点过滤；2D 框由 3D 框投影并裁到图像边界，用于官方难度过滤。该本地协议与论文及其他代码版本不混排排名。

评测基于固定官方仓库 revision `1624751e31260c68d544e60599079d2104ee8a73`：AP_R40，3D/BEV 严格 IoU 0.7/0.5/0.5、宽松 0.5/0.25/0.25，easy/moderate/hard 按官方 KITTI 风格高度/遮挡/截断条件。主指标为严格 moderate 三类 3D AP 均值。confidence 预过滤 0.001，BEV NMS 阈值 0.1，每类最多 500 框，三组一致；阈值来自本次锁定配置，不使用 K-Radar 的 conf=0.3 协议。

评测器工程修复保存在独立副本：CUDA_HOME 固定 cuda-11.3 避免旧 Numba 与系统 NVVM 不兼容；不请求 bbox 时不额外计算/打印 AOS，避免空数组和 None；复制 eval_types 避免跨调用累积；将会错误拒绝重合顶点的 float32 交面积计算替换为局部坐标下双精度凸多边形裁剪。AP 采样、匹配和阈值未更改。完美预测 AP=100、空预测 AP=0，包含空 GT；10000 对框与 OpenCV 独立实现比较的交面积最大误差 0.000053406 m²，自 IoU 最大误差 1.19e−7。原官方文件、修复差异和失败日志均保留。

## 训练预算与选模

三组均为单卡 FP32、micro-batch=2、累积4次、有效 batch=8；最后一组为7帧，按实际帧数归一化。全训练集每轮4196个 micro-batch、1049次 optimizer update，80轮共335680个 micro-batch、83920次更新。BN 按相同 micro-batch 工作，不能把累积等同于大 batch BN。

AdamW，peak lr=0.001、weight decay=0.01、梯度裁剪10；首轮线性 warmup 从约0.0001到0.001，随后按更新数 cosine 到0.00001。seed=260916。ResNet50 ImageNet 权重 SHA-256 `11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca`，其余随机初始化，无目标域 warm-start。编码器、neck、head 在三组间逐张量复制，patch/TaskDec 的公共融合张量也相同，证据见 `initialization.json`。

第1轮及5/10/…/80轮全量去重 val 评测，按严格 moderate mean 3D AP 最大值选择最佳，同分取较早轮。每组固定80轮，不按测试结果调整轮数、阈值或类别；最终对最佳和末轮分别报告原始及去重 val/test。保存最佳权重、末轮可恢复 checkpoint（含 optimizer）、最终预测与完整轻量日志，不保留逐轮大 checkpoint。

稳定200批工程吞吐（FP32、batch2，每批更新）为 concat 0.1482、patch 0.2117、TaskDec 0.2405 s/batch；相应80轮约13.82、19.74、22.43 GPU小时，合计约56.00。峰值分配/缓存分别2.63/4.36、3.37/4.75、3.76/6.47 GiB。正式累积4次的完整首轮实测会用于更新排期；这些工程数字未包含验证、保存、并行干扰，不能冒充实际训练成本。

GPU0 跑 TaskDec，GPU1 顺序跑 concat 和 patch；不使用 GPU2/3。在 GPU0/1 已有服务之外，启动前需连续三次满足空闲显存≥26000 MiB及利用率≤30%，每进程分配上限为显存30%（约14.4 GiB），CPU线程受限、nice=10。保留已有服务和 ASF/L4DR 进程。按现吞吐加约25%余量，9月18日前完成三组具有时间可行性，目标仍以9月22日为主要对照截止；以正式运行实测修订，不承诺无故障完成。

## 复现与自动产物

在项目根目录运行，解释器为 `v2x_taskdec/.venv/bin/python`；设 `CUDA_HOME=/usr/local/cuda-11.3`、`CUDA_VISIBLE_DEVICES=0` 或 `1`、`OMP_NUM_THREADS=4`、`PYTHONDONTWRITEBYTECODE=1`。独立 venv 只读复用 rl_3dod 依赖；没有升级现有实验环境。

1. `python -m v2x_taskdec.freeze_experiment`：仅首次运行，拒绝覆盖已存在正式目录；冻结配置、权重、依赖、源码和输入哈希。
2. `python -m v2x_taskdec.train --variant taskdec --smoke-steps 8 --output analysis_exports/v2x_taskdec_260916/pipeline_smoke_taskdec`：独立端到端检查，正式三组训练不会加载它的权重。
3. `python -u -m v2x_taskdec.launch_controlled`：带文件锁的串联控制器；GPU0/1按上述分配自动训练并衔接评测，每5分钟写状态。
4. 出现故障后保留日志，解决实际错误后 `python -m v2x_taskdec.train --variant NAME --resume`：从末轮恢复，固定 epoch seed 重建样本和增强顺序。不能保证 CUDA 算子的跨运行逐位确定性。
5. `python -m v2x_taskdec.report`：生成正式目录内 `results.md`、`complete_metrics.csv`、`main_table_rows.tex` 与 `summary_status.json`。未完成的评测不产生 AP 行。

最终允许的结论是：完整 TaskDec 在此数据和编码器体系下的架构适配可行性与相对本地对照的实测效果。单种子不支持统计显著性；本地 ROI、类合并和去重协议不支持直接宣称文献 SOTA；目标域重训不是零样本泛化。负增益、零增益、数据质量限制与全部成本均保留。

## 补充：全训练集坐标往返与难度覆盖

已检查训练集ROI内69599个框。三类往返3D IoU保守下界分别0.997670/0.998708/0.999696，均高于严格IoU阈值；moderate有效GT分别26503/18243/18480。初次OpenCV参考在近乎重合边界上的异常已通过解析几何下界及正式评测内核复核排除，原诊断和更正全部保留。详见[审查更正与完整表](../analysis_exports/v2x_taskdec_260916/label_roundtrip_audit_correction.md)。不把该几何检查当作检测效果或独立标定精度证明。

## 最终交付一致性核验

三组与控制器完成后，观察器自动调用`v2x_taskdec/.venv/bin/python analysis_exports/v2x_taskdec_260916/audit_delivery.py`。检查预算、初始化、源文件和输入哈希、固定选模、checkpoint、预测帧覆盖、全部AP和CSV来源一致性。当前训练阶段该脚本应返回incomplete（退出码2），不能把未完成实验当作通过。最终结果解释仍需基于全部对照和已列明限制。
