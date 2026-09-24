# TaskDec：nuScenes / V2X-Radar-V 体量与截稿前可行性

核查时间：2026-09-15 23:05–23:18（北京时间）。按作者给定的 9 月 18 日摘要、9 月 25 日全文安排；不是对会议官方网站截止时间的独立核验。现在已接近 9 月 16 日，实际应按约 9 天剩余时间、再扣除写作和复核时间计算。

**结论：两个数据集在本机都放得下。新开一个数据集并完成一套有意义的受控验证，有条件可行；同时新开两个，或期待完整大规模训练和多种子消融，当前时间不宜承诺。**

若侧重独立数据集的论文说服力，我倾向先给 **nuScenes C+L 约 24–36 小时的接入验证窗口**。它的官方训练数据和预训练入口均可访问，原始 BEVFusion 融合阶段为 6 轮。V2X-Radar-V 的数据明显更轻，但本轮没有核实到可直接复用的单车 C+L+R 融合配置与配套完整 checkpoint，因此不能仅凭体积把它判为更快的路线。9 月 17 日前必须用实际管线、显存和训练速度决定是否继续，不能把“有官方代码”当成“已经复现”。

本轮只做资料、文件元数据和受限 Range 请求；未下载完整传感器包、未安装环境、未启动新 GPU 任务。审计目录占盘不足 1 MB；两次 ZIP 目录读取合计传输了约 14 MB，其余为小型公开文本与元数据。

## 1. 数据量：直接读取发布对象，不混用 GB / GiB

本表 GB = 10^9 bytes，GiB = 2^30 bytes。nuScenes 用官方 S3 对象的 HTTP Content-Length 求和；V2X-Radar-V 的解压大小来自 ZIP 中央目录里的各文件 uncompressed size，尚未对完整载荷做下载校验。

| 数据版本 | 训练 / 验证规模 | 实际压缩包大小 | 解压与占盘判断 |
|---|---|---:|---|
| nuScenes mini | 10 个场景，8 train / 2 val | **4.168 GB** | 只用于接入与短程调试；不替代正式外部数据集结果 |
| nuScenes trainval，仅关键帧 | 700 train / 150 val 场景；约 2.8 万 / 0.6 万标注帧 | **45.364 GB = 42.249 GiB**，含 metadata | 完整 train/val 划分，但缺非关键帧扫描；不能直接复现原始多帧 LiDAR BEVFusion |
| nuScenes trainval，完整 blobs | 同上，额外含扫描与图像 sweeps | **314.887 GB = 293.261 GiB**，含 metadata | 未完整解压测量；建议为下载包、解压、预处理及训练产物合计规划 **1–1.5 TB**，这是空间预算而非实测解压体积 |
| V2X-Radar-V，当前公开版本 | **8,391 train / 1,498 val / 1,501 test**，共 **11,390 帧** | **23.926 GB = 22.283 GiB**；另有 48.9 KB 划分文件 | ZIP 内文件合计 **36.356 GB**；压缩包＋解压文件共 **60.282 GB**。加环境、预处理和有限 checkpoint，规划 **80–120 GB** |

nuScenes 完整 blobs 已包含关键帧，不需要再重复下载 keyframes 包。以官方 val 做对照时，无须为了凑“完整数据集”下载隐藏标签的 test 数据。原始 C+L 路线不需要另外下载 nuImages 原始图像来重训相机，作者已发布相应初始化权重。

nuScenes 分块：10 份 blobs 合计 314,424,925,642 bytes，metadata 461,678,030 bytes；10 份 keyframes 合计 44,902,690,772 bytes。流传的“约 293 GB”通常与这里 293.26 GiB 的数字接近，不应与 315 GB 当成两份相差很大的数据。

来源：[nuScenes 官方下载说明](https://www.nuscenes.org/nuscenes#download)、[官方场景划分](https://github.com/nutonomy/nuscenes-devkit/blob/master/python-sdk/nuscenes/utils/splits.py)、[V2X-Radar-V 官方文件列表](https://huggingface.co/datasets/yanglei18/V2X-Radar/tree/main/V2X-Radar-V)。逐对象实测值见 [nuScenes 大小审计 JSON](../analysis_exports/taskdec_external_data_feasibility_260915/nuscenes_size_audit.json) 与 [V2X-Radar-V 目录和划分审计 JSON](../analysis_exports/taskdec_external_data_feasibility_260915/v2x_radar_v_size_audit.json)。

### V2X-Radar-V 当前版本与论文数字不同

作者论文 §5.1 写单车数据为 7,000 / 1,500 / 1,500，并在 val 上报告结果；当前公开包和独立 ImageSets.zip 则是上表的 8,391 / 1,498 / 1,501。官方仓库 changelog 记载 2026-01-13 重新上传了更完整的数据版本，这支持存在发布版本变化，但不能据此自行推定全部修订内容。[作者论文](https://arxiv.org/html/2411.10962v5)、[官方更新记录](https://github.com/yanglei18/V2X-Radar#changelog)

本轮核对到：

- image_2、velodyne、radar、calib、label_2 各有 11,390 个文件，帧 ID 唯一。
- train / val / test 的帧 ID 两两无交集；trainval 恰为 train 与 val 的并集。
- 三个集合中的每个 ID 均有上述五组文件。此项是文件目录覆盖检查，不代表已经验证坐标、标定和原始载荷内容。
- 全部标签都在名为 training 的目录中；不能按这个目录名称把 11,390 帧全部用于训练。

若采用当前版本，应在表注记录版本、split 和本地复现口径；不直接将当前 8,391 帧训练结果与论文 7,000 帧训练结果混为严格同协议排序。目录与元数据已够确定工程数据量，但协议适配仍需实际样本检查。

## 2. 下载时间与本机资源

截至 23:15，工作磁盘可用约 **4,301 GiB（4.2 TiB）**。两者都不受当前剩余硬盘容量限制。普通目录浅查未发现已准备好的 nuScenes / V2X-Radar-V；没有穷举所有挂载点。

下载耗时的带宽情景如下，只计传输，不含解压、重试与数据转换；本轮未做持续带宽实测。

| 下载目标 | 持续 10 MB/s | 持续 50 MB/s |
|---|---:|---:|
| V2X-Radar-V 23.926 GB | 约 40 分钟 | 约 8 分钟 |
| nuScenes 关键帧 45.364 GB | 约 1.26 小时 | 约 15 分钟 |
| nuScenes 完整 trainval 314.887 GB | 约 8.75 小时 | 约 1.75 小时 |

若只有 2 MB/s，nuScenes 完整 trainval 约需 43.7 小时，足以改变本次优先级。HEAD / 小范围下载成功只证明当前入口可访问，不证明整包可持续跑到上述带宽。

本机是 4 × RTX A6000 48 GB。GPU0/1 已有 Python 进程，不能因为瞬时利用率低就当成空闲。GPU2/3 正在执行已授权的 v2 ASF / L4DR 复现。23:15 状态为 ASF 4,000 / 79,123 步，L4DR 已完成首轮 7,193 步，首轮约 55 分钟。按当前整轮速度粗推，GPU3 可望在 9 月 16 日上午完成训练、GPU2 在当日下午至晚间完成；两者之后还要自动全量评测。此处只是排期估计，以完成标记为准，不占用或中止原任务。

因此新实验应暂按 **后续两张卡** 规划。给数据接入、GPU 任务和论文复核留出余量后，以 9 月 18–22 日约 5 天 × 2 卡 = **240 GPU 小时**作为主要训练预算，比把全部剩余日历天都算成满负荷训练更合理。

## 3. nuScenes：数据大，但已有可核实的初始化与短融合阶段

已核实 MIT BEVFusion：

- 官方 C+L 检测权重约 163.7 MB、LiDAR 检测初始化约 33.4 MB、nuImages 相机初始化约 110.4 MB；三份官方链接的 1 KB Range 请求均返回 HTTP 206 与二进制内容。
- 原始 C+L fusion 阶段配置为 **6 epochs**；官方训练说明使用相机初始化及 LiDAR detector 初始化。这个 6 轮不包含单模态预训练成本。
- 原始配置是 **4 samples / GPU**，官方示例 8 GPU；训练集有 **CBGS** 重采样。6 轮不能简单理解成 6 × 原始 2.8 万帧。
- 原始训练和验证均载入 **9 个额外 LiDAR sweeps**，再加当前帧。因此仅 45 GB 关键帧不满足原始配置。

来源：[官方训练与模型说明](https://github.com/mit-han-lab/bevfusion)、[下载脚本](https://github.com/mit-han-lab/bevfusion/blob/main/tools/download_pretrained.sh)、[原始数据配置](https://github.com/mit-han-lab/bevfusion/blob/db75150717a9462cb60241e36ba28d65f6908607/configs/nuscenes/default.yaml)、[原始融合阶段配置](https://github.com/mit-han-lab/bevfusion/blob/db75150717a9462cb60241e36ba28d65f6908607/configs/nuscenes/det/transfusion/secfpn/camera%2Blidar/default.yaml)。访问测量见 [权重入口记录](../analysis_exports/taskdec_external_data_feasibility_260915/bevfusion_weight_access.json)。

工程上还发现一个应提前处理的细节：当前 main 的检测配置在加入 BEVFusion-R 后包含额外 radar 读取，并改了训练 LiDAR sweeps。此次 C+L 复现应核对并固定原始协议，不能仅凭配置文件名推断行为。已保存加入该修改前的 revision `db75150717a9462cb60241e36ba28d65f6908607` 的相关配置；本轮没有 clone、安装或运行它。[配置修订](https://github.com/mit-han-lab/bevfusion/commit/d0152cf97c0ee3c7999c3f2227ab33e6620cee8f)

风险在旧版 mmcv / mmdet / CUDA 扩展环境、官方数据转换、环视几何、TaskDec BEV 网格与任务监督适配，以及新训练速度。官方 repo 已归档；有现成源码与权重并不等于在本机已经通过复现。应在独立环境中适配，避免修改现有实验环境。

空间优化可以在下载 blobs 后按清单保留所需相机关键帧、LiDAR scans 和必要 metadata；但 tgz 文件不能指望按模态只传输所需字节，选择性解压主要省落盘，未必省网络。本次不建议为了少下载两百 GB 临时更改 sweeps 协议后继续沿用官方基线名义比较。

## 4. V2X-Radar-V：轻量数据，但单车融合训练入口仍需建设

数据方面，当前包每帧有一张相机图像、LiDAR、4D radar、标定与 KITTI 标签，易于沿用已有 VoD / OpenPCDet 的数据与点云检测经验。车辆端数据不要求扩展成车路协同任务。

代码方面，已检查官方仓库的完整文件树、README 与代表配置：

- BEVHeight 目录确有 V 子集的相机实验与数据转换入口；一个 V 相机配置默认 `max_epochs=120`。这不是所有方法的统一训练轮数，但说明不能把它视为现成 6 轮融合微调。
- OpenCOOD 的 `single_lidaronly` / `single_radaronly` 配置虽然含 single 字样，数据根实际指向 **V2X-Radar-C**；不能当作已完成 V 子集的多模态基线。
- 官方 model zoo 已发布若干模型，但本轮见到的主要是 **协同检测** 表及对应权重，不能作为已核实的 V 单车 C+L+R checkpoint。

来源：[官方代码与 model zoo](https://github.com/yanglei18/V2X-Radar)、[V 子集相机配置](https://github.com/yanglei18/V2X-Radar/blob/main/CodeBase/BEVHeight/exps/v2x-radar-v/bev_height_lss_r101_864_1536_256x256.py)、[single LiDAR 配置的真实数据根](https://github.com/yanglei18/V2X-Radar/blob/main/CodeBase/OpenCOOD/opencood/hypes_yaml/v2x-radar/lidar_only/single_lidaronly_lidarpillarnet.yaml)。

若走 V 路线，需要补齐当前 split、点云通道、坐标变换、雷达视野、类别合并与 AP 协议，并建立合理强度的融合对照。KITTI 格式有助于接入，但并不意味着这些定义与 VoD 或 K-Radar 相同。作者对 radar-only 与 LiDAR/camera 的 GT 视野处理也不同，多模态比较要明确统一目标区域。

这条路线适合强调新的 4D radar 采集平台。若允许先做 L+R，现有 VoD 经验可能减轻相机接入成本；但应先核验完整 TaskDec 在该双模态路径中的实现，不把当前 VoD 适配代码自动等同于最终主架构。若坚持这次新增数据必须完整 C+L+R，则新相机 BEV 分支及多模态初始化会提高 10 天内完成的风险。

## 5. 十天内应该交付什么

建议锁定一个外部数据集，目标是全量 train/val 上的一套可比较实验：

| 对照 | 需要回答的问题 |
|---|---|
| 目标数据集原生融合基线 | 数据和检测管线是否正常，本地结果是否达到合理水平 |
| 同编码器、检测头与 patch 融合结构，移除解耦/任务控制 | 换成 patch attention 本身能解释多少变化 |
| 完整 TaskDec | 共享/特有状态及任务控制的增量作用 |

三者统一数据、初始化来源、有效 batch、精度、训练预算和选模规则。若选同一预训练骨干后的冻结训练，应明确为受控架构适配实验；冻结 BN 等细节也要一致。若从已经训练好的融合 detector 继续训练，原生基线也要获得对应的继续训练预算。原始 8 卡示例不意味着必须有 8 卡；减少 GPU 后可以考虑累积梯度，但有效 batch、BN 行为与调度需核对，不能说两卡积累就与八卡严格数值等价。

保留作者要求的架构定位：复用编码器和检测接口，**TaskDec 承担主融合路径**；包括 canonical patch 表征、common/unique 分解、前景控制、模态控制和任务上下文等实际主配置组成。不能为了赶进度，仅在原始 ConvFuser 前后加一个 gate，然后当作完整 TaskDec 验证。

没有本机吞吐测量前，不给“必定几小时跑完”承诺。应先在正式数据管线、相同训练方式下测约 200 个稳定 micro-batch，包括 I/O、前后向、梯度同步与累积更新，并取得 CBGS 后的真实 `len(loader)`。用 `每轮 loader 步数 × 每步墙钟时间 × 轮数` 估计训练时间，再加完整验证、checkpoint 和故障余量。

一个可操作的时间判断：若 nuScenes 两卡的每轮约 3 小时，三组各 6 轮为 54 小时训练，留有余量；若每轮达 8 小时，三组即 144 小时，还没计评测与修复，已超过这里预留的 5 天主要训练窗口。这些是**条件算例，不是测得的 BEVFusion / TaskDec 速度**。V 路线也用自己的 loader 和稳定速度估算，不能从样本数按比例套用 K-Radar 毫秒数。

## 6. 建议的排期与退出节点

以下均为计划建议，本轮未执行大型下载或新实验。

| 时间 | 应完成的工作与判断 |
|---|---|
| 9 月 16 日 | 选择一个主路线；准备数据和独立环境；先用小样本检查图像/点云/GT 对齐；等待现有 GPU2/3 任务评测结束 |
| **9 月 17 日晚前** | 原生基线可评测、完整 TaskDec 可稳定反传，确认正式 loader 长度、显存与约 200 步耗时；按剩余 GPU 小时判断三组能否完成 |
| 9 月 18 日摘要 | 尽量已有首个完整验证结果用于决定摘要措辞；若没有，摘要只写已有证据，不写尚未得到的外部增益或 SOTA |
| 9 月 18–22 日 | 完成基线、结构对照、完整 TaskDec；根据已测时间决定是否能补关键对照第二个种子，不能预先承诺多种子结果 |
| **9 月 23 日** | 固定结果与主要表格，检查全量评测和初始化/预算对齐；性能无增益也如实保留，不根据验证涨幅频繁换数据集 |
| 9 月 24–25 日 | 写作、图表、附录、数值与投稿材料检查；保留问题处理时间 |

若 9 月 17 日仍卡在环境、标定或完整架构接入，nuScenes 就不宜继续作为本次投稿必须交付项。只有在 V2X-Radar-V 适配已接近跑通时才值得切换；否则临时新开另一个未知管线会进一步压缩论文时间，已有 VoD 的受控复核是工程上更确定的退路。退出节点依据工程完成度和可用时间，不依据哪个数据集更容易得到正增益。

最终选择的侧重点：**nuScenes 更适合验证通用融合架构在成熟基准上的适用性；V2X-Radar-V 更适合在新的 4D radar 平台上验证，并明显节省数据空间。按本次已查到的代码和权重条件，我更倾向先对 nuScenes 做限时接入判断，而不是因为它数据较大就直接排除。** 两条路线在目标数据集重新训练后都属于跨数据集适用性验证，不是源模型零样本跨域迁移。

## 可复核产物

- [大小与目录审计脚本](../analysis_exports/taskdec_external_data_feasibility_260915/audit_sizes.py)：只做 HEAD、有限 ZIP Range 和 48.9 KB split 下载，拒绝不支持 Range 的整包响应。
- [nuScenes 压缩包大小](../analysis_exports/taskdec_external_data_feasibility_260915/nuscenes_size_audit.json)、[V 子集解压体积、划分与覆盖](../analysis_exports/taskdec_external_data_feasibility_260915/v2x_radar_v_size_audit.json)。
- [官方划分原始小文件](../analysis_exports/taskdec_external_data_feasibility_260915/V2X-Radar-V_ImageSets.zip)。
- [BEVFusion 权重入口检查](../analysis_exports/taskdec_external_data_feasibility_260915/bevfusion_weight_access.json)、[原始配置 revision 记录](../analysis_exports/taskdec_external_data_feasibility_260915/bevfusion_original_revision.json)。
- 保存了本轮官方树与相关配置文本。BEVFusion 查询树 revision：`326653dc06e0938edf1aae7d01efcd158ba83de5`；V2X-Radar：`1624751e31260c68d544e60599079d2104ee8a73`。用于审计，不表示已完成代码安装与运行。
