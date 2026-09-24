# ASF 的 v2.0 实验安排与 TaskDec 可借鉴部分（2026-09-12）

核对来源：[ASF NeurIPS 2025 正文](https://papers.nips.cc/paper_files/paper/2025/file/80bd5c815cdb033ac23eb27605adaaba-Paper-Conference.pdf)、[官方补充材料 ZIP（内含 ASF_appendix.pdf）](https://papers.nips.cc/paper_files/paper/2025/file/80bd5c815cdb033ac23eb27605adaaba-Supplemental-Conference.zip)、[官方实验页面](https://github.com/kaist-avelab/K-Radar/blob/main/docs/sensor_fusion.md)。已读取正文与附录，并检查关键表格 PDF 页面。本轮没有执行推理。

## ASF 如何分配两个基准

正文 §4.1 将 v1 用于已有方法比较，v2 用于消融及定性分析。v1 的 Table 1 比较 RTNH、3D-LRF、L4DR；Table 2 比较 3D-LRF、DPFT 与 ASF 的显存/FPS。不能把这些对比标为 v2 实验。[正文，pp.7–9](https://papers.nips.cc/paper_files/paper/2025/file/80bd5c815cdb033ac23eb27605adaaba-Paper-Conference.pdf#page=7)

| v2 材料 | 实际内容 | 对照性质 |
|---|---|---|
| 正文 Table 3，p.8 | Sedan/Bus-Truck；AP3D@0.3；Total、Normal、Overcast、Sleet、Heavy snow | 同一权重的 7 种模态组合及 3 种损坏输入设置，共 10 行/类 |
| 正文 Table 4，p.9 | 7 组配置；patch 尺寸、通道维度、patch 倍数、注意力头数、SCL | 结构/超参数消融，分类别报告 AP3D@0.3 |
| 正文 Fig.2 / Fig.3 | 分阶段 t-SNE；真实图像、点云、Radar、检测框、传感器注意力图 | 表征诊断与不同传感器可用性下的检测行为 |
| 附录 Table 5 / 6，p.3 | 按天气、距离统计三种传感器的注意力比例 | 分析融合行为 |
| 附录 Table 8，p.7 | BEVDepth 单目与 DSGN++ 双目，以及使用两者的 ASF | 相机骨干替换；camera 单独结果注明 sequences 1–20 |
| 附录 Table 9–12，pp.8–11 | AP3D/APBEV × IoU 0.3/0.5；两类、Total 与完整七天气 | 扩展正文 Table 3 的同权重模态组合比较 |
| 附录 Fig.5–8 | Bus/Truck t-SNE；LiDAR 损坏、低照度与恶劣天气的实车检测图 | 补充定性证据 |

正文 Table 3 的正常组合为 R、L、C、LR、CR、CL、CLR；损坏设置为 C*、C*LR、CL*R。这些行共享 CLR 训练的模型权重，并非十个分别训练的模型。附录 Table 7 的十随机种子统计属于 **v1.0**，不属于 v2。[正文 Table 3](https://papers.nips.cc/paper_files/paper/2025/file/80bd5c815cdb033ac23eb27605adaaba-Paper-Conference.pdf#page=8)、[附录](https://papers.nips.cc/paper_files/paper/2025/file/80bd5c815cdb033ac23eb27605adaaba-Supplemental-Conference.zip)

## 对我们当前取舍的建议

1. 可采用“v1 主性能与组件证据 + v2 宽 ROI/多类别扩展”的组织。ASF 的安排说明 v2 可以承担方法分析；我们不必强行把它写成第二张 SOTA 表。撤下 VoD 后，应把跨数据集泛化主张相应收窄为同数据集内设置扩展。
2. v2 优先给全量两类的 ASF–TaskDec 比较，保留 AP3D@0.3、AP3D@0.5，并在附录列 BEV 和全天气。严格 IoU 是 ASF 已报告的指标，但它放在附表；不能以其存在为理由只保留对我们有利的指标。
3. 目前 [v2 复核](taskdec_v2_existing_results_recheck_260912.md)中的 8 份全量结果是 CLR 评测。现有 LR/LC/RC 主缺模态表是 v1，不能改表头当作 v2。若以后新增 v2 可用性实验，应对 ASF 和选定的一个 TaskDec checkpoint 使用相同输入组合，再比较性能与退化幅度；本次不启动实验。
4. Fig.5 可以借鉴 ASF 的实车呈现方式，但任务应是解释我们的检测差异：同一帧相机图 + ASF/TaskDec 检测框 + GT + TaskDec gate。我们的前景 gate 与 ASF 的模态注意力 SAM 含义不同，应分别标注。
5. 当前 TaskDec reliability 在已有诊断中偏向 LiDAR，不能照搬 ASF 的“恶劣天气自动转向 Radar”解释。common/unique、任务上下文、gate 和最终检测结果之间的证据关系，应由我们自己的统计与消融支持。

## 数值来源注意

[官方网页](https://github.com/kaist-avelab/K-Radar/blob/main/docs/sensor_fusion.md)给 v2 的 Total AP3D@0.3 为 Sedan 79.3、Bus/Truck 60.4。现有官方原始日志中，conf=0.0 对应 79.2558/60.3794；conf=0.3 对应 74.9779/58.1284。前一轮 TaskDec 差值按 conf=0.3 计算。因此我们若参考论文表格外观，仍需保持已确定的统一阈值，不能直接混入论文公开数值。

局部单元格还存在正文、附录和网页版本差异：如 CLR Sedan Overcast AP3D@0.3，正文 Table 3 为 87.6，附录 Table 9 与网页为 86.1。正式填数以锁定的原始评测结果为依据，不能从多个版本按格挑选。

本地核对入口：[ASF conf=0.0 原始统计](/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/summary_conf0.0.json)、[ASF conf=0.3 原始统计](/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/summary_conf0.3.json)、[TaskDec v2 全量比较](taskdec_v2_existing_results_recheck_260912.md)。
