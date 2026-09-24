# V2X-Radar-V：ASF-style C+L+R 与 ObjDec-LR 的 0.16m 对照

记录日期：2026-09-19。两组均由用户明确授权启动，沿用现有 0.16m 实验的固定 80 轮预算。

## 1. 启动信息

| 实验 | 物理 GPU | 主进程 PID | 后台启动时间（北京时间） | 参数量 |
|---|---:|---:|---|---:|
| ASF-style C+L+R，0.16m | 0 | 153026 | 2026-09-19 12:11:57 | 33,177,901 |
| ObjDec-LR，0.16m | 1 | 153142 | 2026-09-19 12:12:01 | 8,781,007 |

GPU0/1 上原有的服务进程保留；GPU2 的 Concat 与 GPU3 的 ObjDec C+L+R 训练保留。新任务是独立后台进程，不依赖终端持续连接。

启动后复核（12:16 左右）：两组均已记录第 1 轮第 200 个 batch，loss 分别为 2.8973 / 2.9584，failure_count=0，进程继续运行。GPU0/1 整卡剩余显存分别约 18.5 / 15.1 GiB。当前尚无完整轮次验证结果。

- [ASF-style 实时日志](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/train.log)
- [ASF-style 状态](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/status.json)
- [ObjDec-LR 实时日志](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/train.log)
- [ObjDec-LR 状态](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/status.json)

同时查看两个日志：

```bash
tail -n 10 -F /home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/train.log /home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/train.log
```

日志每 100 个 batch 更新一次，完整验证期间需同时查看状态文件，避免把日志暂时不刷新误认为训练停止。

## 2. 对齐内容与实验意义

两组沿用 `analysis_exports/v2x_grid016_260918/matched_80ep/config.json` 的设置：

- 80 轮；micro-batch=2、梯度累积=4、有效 batch=8；每轮 4,196 个 batch / 1,049 次更新。
- 同一训练集、去重验证集、数据增强、seed=260916、FP32、AdamW、1 轮 warmup 与按更新步数的 cosine 学习率。
- voxel/grid=0.16m；BEV 640×640；patch=2×2；4 个 query；融合输出 128 通道，检测头输入为 384×320×320。
- 相同的类别映射、ROI、anchor、检测头、置信度过滤与 NMS。
- 第 1、5、10、…、80 轮做完整去重验证集评测；按验证集 strict Moderate mean AP3D_R40 选 best，平分保留更早轮次。
- 训练结束自动对 best/last 做完整验证集与测试集的原列表 / 去重列表评测，测试集不参与选模型。

**ASF-style** 使用现有 A2Fusion 的 canonical projection、patch attention、PFT 路径，去除 ObjDec 的 common/unique 分支和控制路径，解耦辅助损失权重为 0。该实验是统一底座上的 ASF-style 本地适配对照，不等同于完整官方训练配方；论文中应标明本地适配及 no-SCL 设置。

**ObjDec-LR** 从训练开始就仅使用 LiDAR 与 Radar：无相机图像加载、无相机编码器、无相机 token 或解耦分支，保留双模态 common/unique、前景门控、模态控制、上下文调制与解耦损失（权重 0.12）。它用于检验架构在 L+R 设置下的效果；与对 C+L+R 模型临时去掉相机的缺模态推理是不同实验。与 L4DR 比较时，仍需说明两者网络结构不同，不能把同模态、同网格写成所有组件都相同。

两组与现有 V2X 0.16m ObjDec 一样均未启用 SCL。

## 3. 初始化和可复核性

所有新模型参数均从现有**未训练初始权重** `matched_80ep/taskdec_initial.pt` 中按键和形状严格匹配复制，无已训练 checkpoint 热启动；相机仍沿用原设置的 ImageNet 初始化。

源初始权重 SHA256：`bd2fc4b3e66682f245ce09621893784dc0cefd3b77b31dce5c50e6ace9631131`。

- ASF-style 复制 547 个张量；ObjDec-LR 复制 239 个张量；没有未匹配、临时随机初始化的新增张量。
- 两组公共编码器与检测头参数分别对源张量子集做哈希一致性检查。
- 各目录的 `initialization.json`、`source_manifest.json`、`input_manifest.json`、`provenance.json` 保存参数来源、配置与代码指纹。
- 正式训练从保存的初始权重开始，100-batch 预检的更新不计入正式训练，也不用于热启动。
- 新增独立启动文件 `analysis_exports/v2x_grid016_controls_260919/run.py` 和 `launch.py`，原有运行中的训练源码未修改。

## 4. 启动前预检与显存

| 项目 | ASF-style C+L+R | ObjDec-LR |
|---|---:|---:|
| 训练样本 / 更新次数 | 200 / 25 | 200 / 25 |
| 100 个 batch 训练耗时 | 89.46 s | 88.94 s |
| PyTorch 峰值 allocated | 16.56 GiB | 19.69 GiB |
| PyTorch 峰值 reserved | 18.36 GiB | 21.84 GiB |
| loss / gradient 有限性 | 通过 | 通过 |
| 模态路径、融合与检测头形状 | 通过 | 通过 |
| 8 帧短验证、保存与恢复 | 通过 | 通过 |

设置 PyTorch 单进程显存上限为整卡的 60%，并保留原有约 8.5 GiB 服务进程。正式启动后初次检查训练进程占用约 20.5 / 24.0 GiB（nvidia-smi 口径），加上原服务仍有显存余量。后续输入与验证可能改变峰值，该记录不是“全程不会 OOM”的保证。

100-batch 耗时仅用于初步预算，不能当推理速度或论文效率指标；完整耗时以正式 epoch / validation / final evaluation 记录为准。

磁盘仅保留初始权重、滚动 best/last、日志与评测结果。预检权重已按清单清理，原始实验权重和其它文件未删除。
