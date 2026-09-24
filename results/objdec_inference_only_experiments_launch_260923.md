# ObjDec：推理补充实验启动记录

2026-09-23。用户授权“想好之后直接帮我开吧”。执行此前方案的1＋2＋3，不启动新的训练。

**完成更新：** 七组GPU评测已于2026-09-23 09:55:45全部结束，基准复现通过。完整表格、正负结果及论文表述建议见[结果汇总](objdec_inference_only_results_and_paper_value_260923.md)。

## 运行与产物

统一目录：`analysis_exports/objdec_inference_studies_260923/`。每项有独立`status.json`、日志和启动记录。原有模型、权重和正式表格均保留。

| 工作 | 资源 | 当前状态／进程 | 输出 |
| --- | --- | --- | --- |
| K-Radar全量gate与帧级表征检查 | CPU | 已完成10,065帧 | `cache_analysis/`，CSV＋PDF/PNG＋解读 |
| V2X固定权重控制路径干预 | GPU2 | 已完成七组，耗时约91.90分钟；历史PID 591768 | `interventions/` |
| V2X距离、点数、召回与定位诊断 | CPU | 已完成1,486帧／11,854个有效GT | `diagnostics/` |

GPU0/1的π0.5服务保持运行，GPU3未启动新任务。GPU2推理内存池限制为55%；8帧小测分配显存峰值4.50 GiB，实际驱动占用另含CUDA上下文与缓存。各分析限制CPU线程，禁止生成core dump。

## 1. 已完成的K-Radar缓存结果

10,065帧、51个序列；总体FG/BG gate均值为0.270091/0.117634；99.06%的帧FG均值高于BG。按序列等权的FG−BG均值为0.150367，与按帧等权0.152457接近。七天气全部报告，不仅选择可视化样本。

表征对应性检查有一个重要限制：shared的同帧与跨序列错配余弦都约0.97–0.99，因此高余弦本身不能证明对象对应语义。去均值后L–R有一定对应性差异，涉及Camera的配对较弱。详见[缓存结果解读](../analysis_exports/objdec_inference_studies_260923/cache_analysis/report.md)。这些是前景patch帧均值的结果，不等于逐patch表征结论；未修改论文以放大证据。

## 2. GPU2：固定权重干预

冻结ObjDec三模态第70轮、既定val选择的`best.pt`。已核对SHA256，沿用0.16m/2×2配置、FP32、batch=2、原score/NMS和原评测器；只评去重test的1,486帧，不依测试表现挑选新参数。

七个设置全部自动完成：

1. baseline，先完整推理并复核历史AP。
2. gate_mean：每帧所有patch使用该帧预测gate均值。
3. gate_shuffle_260923。
4. gate_shuffle_260924。
5. gate_shuffle_260925。
6. no_query：只关闭query上下文增量。
7. no_output：只关闭融合输出上下文增量。

gate改动一致作用于token残差、模态scale和gated context。打乱仅在同帧patch之间进行，保留gate边际分布；模态评分、shared/specific以及原始上下文预测仍按原路径计算。原始输入及三路编码保持不变，多个干预复用当前batch编码特征，并使用独立融合状态。GT从送入网络的batch中移除。

8帧小测已验证：与原生网络在相同特征下输出一致、恢复baseline后输出一致、query/output关闭互不替代、gate均值或分布保持。完整baseline逐类严格Moderate AP偏差须不超过0.05个百分点；超出则自动停止并保存失败原因，不继续输出无法对应的干预结论。此为实现容差，不是宣称数值完全相同。

评分保存完整IoU/难度指标，`comparison.csv`汇总逐类3D/BEV及均值差。三个随机种子全部保留，另给均值和范围。它们是**推理干预**，不是重新训练的组件消融，也不能把推理分布变化造成的下降全部解释为语义贡献。

## 3. CPU：V2X预测误差诊断

使用同一去重test集合的既有预测：ObjDec CLR70、ObjDec-LR75、ASF-style80、L4DR80。主要比较ObjDec-LR/L4DR，补充ObjDec CLR/ASF-style。

- 固定score≥0.1；沿用ROI、Vehicle映射、投影过滤和Moderate目标条件。
- 各类别采用0.7/0.5/0.5的3D和BEV IoU，进行一对一几何匹配。
- 距离按xy径向0–30、30–60、≥60 m。
- 框内LiDAR点数按0–5、6–20、21–100、>100；Radar按0、1–5、6–20、>20。均为原始点云经过固定schema、标定变换后落在GT框内的数量，不是voxel数量。
- 保留所有GT作为召回分母；定位误差既报各自TP，也报两方法共同检测成功的GT。误差含xy中心、z中心、尺寸L1及模π朝向轴差。
- 分组全部输出含零样本组、正负差值；不据test收益改变分箱。

小测已通过解析IoU、点数、一对一匹配和原评测器预测过滤数量检查。该分析是GT中心的几何召回／误差，不是另一个官方AP；不把忽略对象处理尚未定义的分组结果称为precision或FP率。

已完成的总体诊断：ObjDec-LR/L4DR的3D召回为88.37%/87.72%，BEV为92.25%/91.68%；ObjDec CLR/ASF-style的3D召回为87.73%/87.84%，BEV为91.86%/91.68%。这些是固定score下按GT加权的召回，不能与AP均值混为一谈。完整正负分组及定位误差见[诊断结果](../analysis_exports/objdec_inference_studies_260923/diagnostics/report.md)。首轮配对CSV导出遇到字段并集问题，已从完整逐GT记录恢复，未重新推理或改动匹配，处理记录一并保留。

## 查看进度

```bash
tail -F /home/hongsheng/dec_con_asf/analysis_exports/objdec_inference_studies_260923/interventions.log /home/hongsheng/dec_con_asf/analysis_exports/objdec_inference_studies_260923/diagnostics.log
```

运行期间每32帧更新；评分阶段输出`phase=scoring`，阶段完成后自动保存JSON并开始下一项。此次实验已结束，最终日志为`phase=complete`。目前新增文件约333.45 MiB，只保存压缩框预测、统计和图，不复制checkpoint或保存全量BEV特征。
