# VoD ObjDec：2×2 patch＋局部编码启动记录

2026-09-21 00:04:55启动，用户授权仅在GPU2先运行ObjDec。配置/目录保留准备时的260920标记。未启动Concat，未改动GPU0、1、3上的任务或历史实验。

## 实验设置

| 项目 | 设置 |
|---|---|
| 设备 | 物理GPU2，RTX A6000 48GB，UUID GPU-a669257e-8165-eea0-ffa3-c7016159e401 |
| PID | 325480，独立后台会话 |
| 数据 | 原生VoD，5,139 train /1,296 val；L+R，单帧LiDAR＋5帧Radar |
| 训练 | 从头80轮，seed666，FP32，Adam OneCycle，峰值LR0.003 |
| batch | 每次8帧，梯度累积2次，有效batch16；最后不足16帧按实际样本数归一化 |
| 网格/范围 | 原0.16m、320×320，原ROI与检测头保持一致 |
| patch/query | 2×2 /4；原mild为4×4 /16 |
| 局部编码 | L/R各两层3×3 Conv-BN-ReLU，64通道，stride1；STEM.ENABLED=True，LAYER_NUM=1（首层＋1层） |
| token规范化 | TO_EMBED.LAYER_NORM=True |
| 其余 | 保留原mild损失/控制强度、增强、锚框、score=0.1、NMS=0.01；没有整体照搬V2X其他超参数 |
| 参数量 | 18,605,583 |
| 验证 | 每5轮完整验证1,296帧；第80轮完成后结束；推理前移除gt_boxes |
| 选模 | 官方VoD EAA mAP，严格提高才更新best；同一权重记录DC和KITTI 3D/BEV |

batch8×2保持每轮322次优化更新，与batch16的更新次数一致；OneCycle按优化更新计数，未错误按643个微批次设置。BatchNorm每次使用8个样本，与历史batch16不同，正式比较需披露，后续配对基线应采用同样设置。

## 检查与当前状态

- GPU2启动前仅26MiB占用，其余GPU保留原任务。
- batch8×累积2通过三次真实数据FP32优化更新、有限loss/梯度检查及无GT推理、检测结果转换。预检峰值allocated20.61GiB /reserved22.18GiB；这些更新已丢弃，正式训练重新设seed、从头初始化。
- 独立8帧评测预检已跑通官方EAA/DC和KITTI完整3D/BEV接口。这是未训练模型的功能检查，epoch000不能写入性能表或用于选模。
- 正式第1轮已开始更新，首个更新loss3.2758、累积样本均值3.3269，LR0.0003，峰值allocated22.51GiB；检查时整卡约24GiB，保留显存余量。
- 00:06:05已完成20次优化更新（40/643微批次），loss2.1515、当轮样本均值2.3099，峰值allocated22.75GiB，未出现非有限值或OOM。
- PyTorch分配上限设为GPU总显存85%；所有loss、梯度范数及验证框/分数均检查有限值。实际后续进度以日志为准，不将启动检查作为训练完成结论。

## 结果保存与查看

实时日志：

```bash
tail -n 30 -F /home/hongsheng/dec_con_asf/vod_taskdec_native/logs/objdec_vod_patch2_local_gpu2_260920.log
```

- [运行清单、配置副本、来源SHA与预检](../analysis_exports/objdec_vod_patch2_local_260920/launch.json)
- [配置](../vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920.yaml)
- [隔离训练入口](../scripts/run_objdec_vod_patch2_local_260920.py)：复用原模型、数据、优化器与原生epoch外层保存逻辑，仅此进程替换单轮循环以支持累积，并接入周期验证；未修改共享训练源码。
- [运行状态](../analysis_exports/objdec_vod_patch2_local_260920/status.json)：初始化时为starting；每轮结束及验证前后更新，并记录累计训练/验证墙钟时间；不属于每步心跳。
- [评测目录](../analysis_exports/objdec_vod_patch2_local_260920/validation/)：每轮保存metrics.json、kitti.txt、预测result.pkl；不保存稠密特征或图像。
- 权重目录：`vod_taskdec_native/L4DR_taskdec/output/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920/objdec_p2_local_mild_b8a2_fp32_ep80_260920_gpu2/ckpt/`。每5轮保留一个正式权重（最多16个），另保留best_eaa及必要的latest恢复点，总量预计约4GiB，不涉及删除历史权重。

原先的[VoD迁移分析](objdec_vod_v2x_tuning_transfer_feasibility_260920.md)为本次实验依据。单独启动ObjDec是用户当前安排；对局部编码的收益归因仍需后续同设置Concat等对照。

## 完成记录：2026-09-21

训练于14:37完成80轮及全部16次周期验证，GPU2进程已退出。按EAA选择的最优为第75轮：EAA71.23、对应DC84.69；第80轮为70.83/84.66。最优与末轮权重均已保存。完整逐类结果、与旧版及L4DR的比较见[最终结果报告](objdec_vod_final_and_v2x_epoch60_results_260921.md)。本段覆盖上方启动阶段的进度快照，不改写历史记录。
