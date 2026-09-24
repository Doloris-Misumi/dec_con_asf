# V2X-Radar-V L4DR：GPU1 自动接续训练

2026-09-17，用户授权：等 GPU1 上 Concat 完成后，自动补跑 L4DR，并在训练结束后评测。无需交互终端保持开启。

**后台接续控制器已启动：PID 3990038，启动时间 00:53:36（北京时间）。** 当前阶段以 [自动更新的结果报告](taskdec_v2x_l4dr_matched_training_260917.md) 和 `analysis_exports/v2x_l4dr_260917/matched_80ep/controller_status.json` 为准。

## 接续条件与执行链

控制器每30秒读取一次 Concat 状态。必须同时满足：Concat 状态为 complete、best/last 最终报告均已落盘、原 Concat 进程已退出、GPU1 除 PID140935 常驻服务外没有其他计算进程、空闲显存至少28,000 MiB，并连续两次通过资源检查。

之后自动执行：生成独立初始权重 → 200个训练batch/50次更新与8帧评测及checkpoint恢复 → 原生模块等价性、空输入和无GT推理检查 → 丢弃本次短测权重 → 从初始权重重新开始正式80轮 → best/last最终评测。某阶段失败则记录错误并停止，不继续使用未通过检查的配置。控制器不向其他训练或服务发送终止信号。

## 模型与公平比较边界

- 输入 L+R，无相机，不加载任何完整模型或单模态预训练权重。
- 原生三类别 L4DR：PointNet2MSG 雷达点特征、PointHeadPreMask 前景筛选、MME 双向点特征交互、MGF 多尺度门控融合、AnchorHeadSingle 检测头。采用本地已跑通的官方 VoD 分支代码；未仅抽取 MGF 填入 Concat。
- 保留原生0.16m横向体素及网络宽度。使用共同ROI `[0,-51.2,-5,102.4,51.2,3]`，柱高适配为8m、网格640×640。现有TaskDec横向体素为0.4m，因此不声称同FLOPs或完全相同前端。
- 雷达点采样为原生2048点近远采样/不足时重复策略。使用已有逐帧schema读取器，相同六个V2X字段加单帧相对时间0；未经证实的第五星标量不命名为物理速度。保留字段缺失标记。
- 点前景阈值0.2；训练使用检测损失加原生点前景损失，不使用TaskDec辅助损失。
- 类别Vehicle（Car/Truck/Bus合并）、Pedestrian、Cyclist。Anchor几何使用原实验仅由训练集计算的统计。

这是相同样本、轮数和有效batch下的外部架构参照。相对现有C+L+R方法，输入模态、分辨率、网络宽度和预训练来源存在差别，必须在论文中标注为 `L4DR (L+R, local adaptation)`。

## 必要适配和检查

全部代码和配置在独立目录 `analysis_exports/v2x_l4dr_260917/`，原L4DR及正在运行的TaskDec/Concat/patch源文件不变。

1. 复用已核验的V2X字段、ego坐标、GT转换、增强和ROI逻辑。CPU检查对22帧（包含空LiDAR/空Radar）逐框验证GT与原数据读取器一致，并验证eval采样可重复；精确帧数以 `checks_cpu.json` 为准。
2. 原生MME使用点柱坐标相等连接，原实现构造完整两两距离矩阵。独立副本改为整数键查找，保留配对及顺序，避免大规模中间矩阵。CPU/GPU检查对照原生前向与参数梯度。
3. 支持空模态和显式batch大小；空雷达的PointNet占位点被有效性mask排除，不参与前景监督和后续体素化。单柱单点雷达的BN退化情况使用已有运行统计，正常样本处理不变。
4. 原生point head中的无条件GT标签统计改为仅训练时执行。正式推理不传GT；检查无GT和篡改GT两次预测是否一致。
5. MGF、PointNet和检测训练路径保留。适配的scatter与原生非空输入输出精确对照；分别验证空LiDAR、空Radar和全部为空时的有限输出及反向传播。

## 训练与评测

训练8,391帧，80轮，FP32，micro-batch2、梯度累积4、有效batch8，seed260916。每轮4,196个batch和1,049次更新，总计83,920次更新。AdamW、1轮warmup、cosine、LR0.001→0.00001、weight decay0.01、clip10，与V2X现有实验相同；这不是VoD原始100轮onecycle配方。

第1轮及5/10/…/80轮完整去重val评测。按严格IoU、Moderate三类平均3D AP_R40选best，同分取更早轮。最终best和last都报告原始val/test以及去重val/test；test不参与选择。阈值和后处理复用原V2X统一代码。

每进程PyTorch分配上限40%（A6000约19.2 GiB），GPU1原有服务保留。实际显存与耗时写入状态；短测通过后才能进入正式训练。只保留一份初始权重与滚动best/last，不保存80份checkpoint或复制数据集。

## 实时查看

等待和接续阶段：

```bash
tail -f /home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/controller.log
```

正式训练开始后：

```bash
tail -F /home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/train.log
```

训练状态：`matched_80ep/l4dr/status.json`；评测进度：同目录 `evaluation_progress.json`。短测日志：`matched_80ep/smoke.log`；检查日志：`matched_80ep/checks_gpu.log`。结果报告由接续控制器自动更新。
