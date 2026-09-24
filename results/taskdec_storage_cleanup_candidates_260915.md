# TaskDec 磁盘清点与可裁剪清单

核查时间：2026-09-15 夜间。**仅盘点并生成清单，没有删除、移动、压缩任何原有文件。** 以下统一用 GiB（2^30 bytes）；候选大小按实际已分配块 `st_blocks × 512` 求和，不按文件名猜测。清单中的候选都是单硬链接文件，两个批次互不重叠。

**建议先考虑 A 批，约 81.33 GiB：不裁剪已完成正式运行的 `model_N.pt` / `checkpoint_epoch_N.pth`，保留主要续训点、论文结果与原始日志。若还需要空间，B 批可再裁剪 VoD 中间模型约 74.98 GiB。合计约 156.31 GiB（0.153 TiB）。**

这些文件中，下载归档与已过时的临时恢复点最容易取舍；中间 checkpoint 具有逐轮回溯价值，应称为“可裁剪”，不能简单说所有旧权重都没有价值。

## 1. 空间用在哪里

| 范围 | 当前占用 | 说明 |
|---|---:|---|
| `/home/hongsheng/dec_con_asf` | 约 **222 GiB** | TaskDec 项目总目录；未沿 `pretrained` 软链接重复计入 K-Radar 权重 |
| `dec_con_asf/logs` | **127.55 GiB** | 主项目历史训练与评测 |
| 其中 `models/model_*.pt` | **63.29 GiB** | 主模型、Strong、消融与参数实验模型；A/B 均保留这些文件 |
| 其中 `utils` | **29.50 GiB** | 主要是另外保存的模型＋优化器＋调度器恢复状态 |
| 其中 `test_kitti` | **29.13 GiB** | 逐帧预测、GT、描述、条件划分、评测汇总；不是普通几行文本日志 |
| 其中 `train_iter` | **5.49 GiB** | TensorBoard 逐步训练记录 |
| VoD 原生管线 `output/VoD_models` | **90.35 GiB** | 其中 checkpoint 合计 **89.09 GiB** |
| `dec_con_asf/results` | 约 606 MiB | 结果、论文表格、文档等，删除它们得不偿失 |
| `dec_con_asf/analysis_exports` | 约 1.2 GiB | 包括在跑的 v2 对照、可视化、PPT 和审计产物，整体保留 |

8 月 29 日的 [VoD 空间笔记](vod_storage_and_download_notes_260829.md) 记录项目约 72 GB、分区可用约 5 TB；当前项目约 222 GiB，增长数量级约 150 GB，但旧记录的单位和数值是近似值，不能当作逐字节差分。

另外，9 月 11 日恢复的原始雷达数据逻辑大小 **156.44 GiB**，其下载 ZIP **53.54 GiB**；这两部分约 210 GiB，也是近期增加的明确数据项，其中解压数据正在被使用。

本次粗盘点还见到 `k_radar_dataset` 约 640 GiB、`YMMT` 约 318 GiB、`datasets` 约 173 GiB、`WCBR` 约 63 GiB、`vod` 约 41 GiB。这些不是本轮可删除清单。整个 home 约 1.6 TiB，而所在分区已用约 9.6 TiB；**分区剩余空间的变化不能全部归因于 TaskDec**，也可能来自该分区其他目录。缺少历史目录快照，无法精确归因全部约 0.8 TB 的下降。

## 2. A 批：较稳妥的候选，共 81.33 GiB

| 候选 | 文件数 | 可回收 | 判断与保留项 |
|---|---:|---:|---|
| K-Radar 旧 `utils/util_*.pt` | 80 | **25.65 GiB** | 已完成运行的中间恢复状态；对应 `models/model_N.pt` 全部存在并保留。每组留最后恢复点；Strong resume 留 10 / 16 / 20 |
| 五组已完成 VoD 的 `ckpt/latest_model.pth` | 5 | **1.52 GiB** | 定时保存的轮内恢复点；保留正式末轮。它们与末轮文件不相同，不能标成逐字节重复 |
| 已弃用 TaskDec-PP AMP 试跑的 ckpt | 3 | **0.62 GiB** | 只跑到 epoch 2；后续已改用 FP32。保留训练日志、配置及数值问题记录 |
| `/home/hongsheng/sparse_radar.zip` | 1 | **53.54 GiB** | 解压恢复记录为 complete、逐成员 CRC 已通过；本轮再查 34,994 个解压文件，路径与大小全部匹配。保留解压数据及恢复记录 |

### A1：具体 `utils` 目录

下面所有目录都在 `/home/hongsheng/dec_con_asf/logs/`。文件级完整路径见 [候选 CSV](../analysis_exports/storage_audit_260915/candidate_files.csv)。

| 运行前缀与方法 | 建议移除 | 必须保留的 util | 可回收 |
|---|---|---|---:|
| `exp_260831_003901_TaskDecAblWoSensorReliability...` | util_0–8.pt | util_9.pt | 2.88 GiB |
| `exp_260831_003901_TaskDecAblWoTaskContext...` | util_0–8.pt | util_9.pt | 2.88 GiB |
| `exp_260901_075156_TaskDecAblWoForegroundGate...` | util_0–8.pt | util_9.pt | 2.88 GiB |
| `exp_260901_075157_TaskDecAblWoDecouplingSupervision...` | util_0–8.pt | util_9.pt | 2.88 GiB |
| `exp_260903_012813_TaskDecControlStrength05...` | util_0–8.pt | util_9.pt | 2.88 GiB |
| `exp_260903_012813_TaskDecControlStrength10...` | util_0–8.pt | util_9.pt | 2.88 GiB |
| `exp_260904_075622_TaskDecGateBiasM06...` | util_0–8.pt | util_9.pt | 2.88 GiB |
| `exp_260904_075622_TaskDecGateBiasM18...` | util_0–8.pt | util_9.pt | 2.88 GiB |
| `exp_260825_224847_DecControlledASFStrong_v2_0_resume20...` | util_11–15、17–19.pt | util_10 / 16 / 20.pt | 2.57 GiB |

依据 [实际保存代码](../pipelines/pipeline_detection_v1_0.py)：`model_N.pt` 保存模型参数，`util_N.pt` 再保存同一轮模型、optimizer、scheduler 和训练计数。此清单只裁剪旧 util，不删除成对的模型。代价是不能再从被删 util 对应的轮数恢复当时的优化器状态，仍可加载对应模型进行推理、评测或另行微调。

### A2–A3：VoD 临时断点与 AMP 试跑

五个 `latest_model.pth` 分别来自下方 B 表的五组已完成训练。保存代码表明它们是按时间间隔生成的轮内状态，最终的 `checkpoint_epoch_80.pth` 或 `checkpoint_epoch_100.pth` 更晚。前后片段和大小检查也显示两者不是相同文件，本轮没有将它们误称为重复副本。

失败/弃用 AMP 权重目录：

`/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP/native_taskdec_pp_lr_b16_amp_ep80_260907_gpu3/ckpt/`

仅包括 `checkpoint_epoch_1.pth`、`checkpoint_epoch_2.pth`、`latest_model.pth`，不删除整个实验目录。[AMP 转 FP32 的原始记录](vod_native_taskdec_pp_comparison_260908.md)

### A4：已解压的雷达 ZIP

候选仅为 [sparse_radar.zip](/home/hongsheng/sparse_radar.zip)。实际输入位于：

`/home/hongsheng/k_radar_dataset/sparse_radar_tensor_wide_range/rtnh_wider_1p_1/`

该输入目录继续保留。[原恢复状态](../../WCBR/artifacts/l4dr_restore_260911/status.json) 显示 35,054 个含目录条目完成、`crc_verified=true`；本轮重新核对 34,994 个实际文件，缺失 0、大小不一致 0。没有再次读取全部 156 GiB 解压载荷重算哈希。删除 ZIP 的代价是失去本地压缩备份，未来需要时须重新获取；不会删除当前训练所读的解压文件。

## 3. B 批：可选裁剪 VoD 中间 checkpoint，再回收 74.98 GiB

下面只计算 `checkpoint_epoch_N.pth`，不重复计入 A 批 latest 文件。保留论文/汇报选中的模型、末轮和若干阶段点；裁剪后不能恢复已删除 epoch 的精确权重。所有 train log、TensorBoard、逐轮评测 CSV/JSON、保存的预测和结果表继续保留。

公共目录前缀：

`/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/`

| 运行目录（类别 / 实验名） | 建议保留的 epoch | 移除文件数 | 可回收 |
|---|---|---:|---:|
| `PP_Concat/native_pp_concat_lr_b16_amp_ep80_260907_gpu2/ckpt` | **80**，另留 1 / 10 / 20 / 40 / 60 / 79 | 73 | **14.73 GiB** |
| `TaskDec_PP/native_taskdec_pp_lr_b16_fp32_ep80_260907_gpu3/ckpt` | **73 / 80**；另留 1 / 4 / 10 / 20 / 40 / 60 / 70 / 72 / 74–79 | 64 | **13.33 GiB** |
| `TaskDec_PP_MildS05AuxHalf/native_taskdec_pp_mild_s05_auxhalf_b16_fp32_ep80_260908_gpu2/ckpt` | **70 / 80**；另留 1 / 10 / 20 / 40 / 60 / 79 | 72 | **14.99 GiB** |
| `TaskDec_PP_WarmPPConcat_MildS05AuxHalf/native_taskdec_pp_warm_ppconcat_mild_s05_auxhalf_b16_fp32_ep80_260908_gpu3/ckpt` | **73 / 79 / 80**；另留 1 / 10 / 20 / 40 / 59 / 60 / 70 | 70 | **14.58 GiB** |
| `L4DR/l4dr_vod_repro_ep100_g23_260910/ckpt` | **99 / 100**；另留 71 / 80 / 90 | 25 | **17.35 GiB** |

保留依据：[VoD 主表及官方 EAA/DC](paper_vod_main_table_draft_260909.md)、[初版 TaskDec checkpoint 扫描](vod_taskdec_pp_best_epoch_scan_260908.md)、[L4DR 本地复现报告](l4dr_vod_local_repro_results_260910.md)。PP-Concat epoch 80 也是已有 warm-start 路线的重要参照；warm TaskDec 的 AP_R40 最优 epoch 73 与官方 EAA/DC 采用的 epoch 79 都保留，不只留其中一个。

**B 是空间取舍方案，不表示这些中间模型性能差或实验没有价值。** 如果计划重新按新指标逐轮选模，应保留对应完整序列，或先完成该复评后再裁剪。

## 4. 实验记录：哪些先保留

- `results/` 中的论文表格、CSV、原始结果来源索引、方法记录：保留，体积小且关系到可复核性。
- `logs/*/test_kitti` 共约 29.13 GiB：暂不列为直接可删。这里有正式评测的 GT / pred / desc 和条件划分，直接删会影响离线重算；后续可以制作并验证压缩归档，再考虑移除展开目录。本轮未实施，也未将可能压缩节省的空间计入总量。
- `logs/*/train_iter` 共约 5.49 GiB：保留；能用于追查训练和数值问题。
- failed / smoke 的普通日志、JSON 和空实验目录：多数很小。建议保留错误记录，只裁剪已经确认不再使用的大权重，没有必要为了几 MB 丢失调试依据。
- PCA、gate 可视化、PPT：保留，合计远小于逐轮 checkpoint。

## 5. 明确保护范围与执行边界

当前 GPU2 / GPU3 的 ASF、L4DR v2 训练仍在运行；整个 `analysis_exports/v2_matched_training_260915/` 不在候选中。官方 pretrained、K-Radar/VoD 解压数据、v1 正式模型、v2 Strong、正式消融与参数实验的 `models/model_N.pt` 均保留。WCBR 目录未列入本轮删除范围。

候选清单生成时记录每个文件的大小、已分配空间、mtime_ns、inode、device 与硬链接数。若之后决定执行，应先确认原任务已经结束、候选未被更新或新实验引用，再按文件清单处理；本轮没有生成会递归删除实验目录的命令。

按本轮约 4,301 GiB 空闲估算：仅 A 批后约 4.28 TiB；A+B 后约 4.35 TiB。**清理这两批有实际收益，但不足以单独恢复到原先约 5 TiB。** 这也说明应把新增必需数据和共享分区其他目录的变化与可裁剪实验产物区分开。

## 文件清单

- [全部候选 CSV：393 个具体文件](../analysis_exports/storage_audit_260915/candidate_files.csv) / [JSON](../analysis_exports/storage_audit_260915/candidate_files.json)。A 批 89 个，B 批 304 个；仅供审阅。
- [明确保留的恢复状态与 VoD checkpoint](../analysis_exports/storage_audit_260915/retained_checkpoints.csv)。K-Radar `models/` 是整类保护，此 CSV 只列与裁剪逻辑直接相关的保留项，不是全部重要文件白名单。
- [分组大小与保留 epoch](../analysis_exports/storage_audit_260915/candidate_summary.json)。
- [K-Radar 日志占盘明细](../analysis_exports/storage_audit_260915/taskdec_logs_du_bytes.tsv)、[目录空间快照](../analysis_exports/storage_audit_260915/directory_footprint_snapshot.json)。
- [雷达解压文件路径/大小复核](../analysis_exports/storage_audit_260915/sparse_radar_extraction_size_check.json)、[在跑任务与磁盘快照](../analysis_exports/storage_audit_260915/active_jobs_and_disk.json)。
- [清单生成脚本](../analysis_exports/storage_audit_260915/build_candidate_manifest.py)：只读取已有文件、写审计清单，不含删除操作。
