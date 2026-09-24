# ObjDec 附录写作安排与材料索引

日期：2026-09-20。用途：确定附录目录、每节论证任务、图表与材料来源；这是可据以写作的提纲，不是附录正文定稿。本轮没有启动实验或修改训练配置。

已按本提纲写成[中英文附录初稿](objdec_appendix_bilingual_initial_260920.md)，包含共用附表与图注；[来源及待补说明](objdec_appendix_source_notes_260920.md)单独维护。下文保留原规划，实际已完成内容以初稿为准。

**2026-09-22安排更新。** 正文跨数据集验证以V2X-Radar-V为主，VoD作为附录G.4的补充实验；已写入中英文正文及完整EAA/DC表，沿用A–H编号。

**2026-09-23安排更新。** 正文表4分为公开代表方法参考与本地融合对照两个面板，本地组为ASF-style/ObjDec（C+L+R）及L4DR/ObjDec-LR（L+R）。Concat仅放附录G.1/G.2，作为公共底座受控对照；不因其移出主表而声称ObjDec优于全部已评测结构。详见[本轮表格与章节安排](objdec_v2x_paper_comparison_260923.md)。

论文：**Decoupling to Fuse: Learning Shared and Modality-Specific Representations for Multi-Sensor 3D Object Detection**。论文方法名统一使用 ObjDec；工程文件中的 TaskDec 名称保留。

## 1. 总体安排

沿用当前实验初稿的 **A–H** 编号，避免重新改动正文的附录引用。附录依次回答：如何实现、如何比较、完整结果如何、各组件如何起作用、表征与空间响应是什么样、输入失效时怎样、在另一数据集上怎样适配、代价和适用范围是什么。

每个实验小节按“问题与设置 → 表或图 → 主要观察 → 解释范围”写。已有训练日志作为作者核对材料，正文描述固定实验设置与最终发现；提交版使用匿名配置名、相对路径和正式引用，不保留本机用户名或绝对路径。

| 附录 | 建议英文标题 | 回答的问题 | 对应正文 |
|---|---|---|---|
| A 实现与训练细节 | Implementation and Training Details | 怎样重建 ObjDec？ | 方法3.1–3.4、实验4.1 |
| B 评测协议与模型选择 | Evaluation Protocols and Model Selection | 表中的结果怎样产生、哪些可直接比较？ | 实验4.1及各主表表注 |
| C 完整 K-Radar 结果 | Complete Results on K-Radar | 换类别、IoU、阈值和天气后表现怎样？ | 实验4.2 |
| D 组件与配置分析 | Component and Configuration Analyses | 移除了什么、保留了什么，变化体现在哪些指标？ | 实验4.3 |
| E 表征与定性分析 | Representation and Qualitative Analyses | shared/specific、gate和最终检测各提供什么证据？ | 实验4.4、Fig.3–5 |
| F 传感器可用性与损坏输入 | Sensor Availability and Corrupted Inputs | 同一权重在输入改变后保留多少性能？ | 实验4.2 |
| G 跨数据集架构适配 | Cross-Dataset Architecture Adaptation | V2X完整适配与对照如何构造，VoD适配有哪些补充结果？ | 实验4.5、Table 4 |
| H 计算效率与适用范围 | Computational Efficiency and Limitations | 新结构与部署优化的代价分别是什么？ | 实验4.3、结论 |

附录首页可用一小段引导：

> This appendix provides implementation details and evaluation protocols, followed by complete detection results, component analyses, representation visualizations, sensor-availability studies, and architecture adaptation to V2X-Radar-V and VoD. We also report computational costs and discuss the scope of the current evidence.

## 2. A：实现与训练细节

**A.1 Network architecture and tensor dimensions.** 用一张表列编码器输出、投影、patch、shared/specific分支、gate与模态评分、object context、attention、PFT和检测头。区别K-Radar v1、v2 Strong与V2X；给出通道、patch尺寸、query数和输出维度。正文已有概念和公式，附录补齐能够实现网络的尺寸与操作顺序。

**A.2 Foreground targets and auxiliary objectives.** 把此前Fig.4引起的疑问在这里讲透：

- 训练时，将GT旋转框投影到BEV，按框局部两轴扩张后判断patch中心，得到二元标签 \(y^p\)。主配置扩张距离为0.7m。
- shared/specific映射和预测gate \(g^p\) 在所有空间位置计算。训练与推理的融合前向均用预测gate；GT标签仅用于损失。
- gate与单类别objectness的BCE如何加权；三个表征约束在什么位置计算；无有效前景的batch如何处理。
- 多类别上下文的类别目标、重叠框赋值方式、前景类别CE与单独gate监督。
- 低gate削弱新增残差和缩放偏离1的程度，原始token仍保留；最终检测框由后续检测头产生。

建议给一段训练/推理共用伪代码：先计算所有位置的表征、预测控制信号并融合；仅在training条件下构建标签和损失。GT到loss的虚线关系已有Fig.4展示，无需再复制一张相同大图。

**A.3 Optimization and inherited training objectives.** 用一张配置表列训练轮数、micro-batch/有效batch、优化器、学习率、冻结策略、初始化和损失权重。特别说明外层辅助权重与各项内部权重的乘积。SCL放在本小节用一段说明，并在正文保留其启用情况和引用：K-Radar主设置启用，V2X关闭。实际SCL从已受控的完整输入token中选组合，不是每次只用子集传感器重新独立预测gate/context；主路径与SCL路径的输出context残差也有区别。

**建议图表：** Table A.1网络尺寸与变体；Table A.2训练和损失配置；Algorithm A.1前向与训练监督。

**现成来源：** [方法初稿及实现备注](taskdec_methods_bilingual_initial_260917.md)、[v1配置](../configs/ASF_task_dec_controlled_robust_v1_0.yml)、[融合代码](../models/fuser/patch_dec_a2_fusion.py)。材料主要已经具备，需改写成正式附录语气。

## 3. B：评测协议与模型选择

**B.1 Dataset versions and evaluation settings.** 一张协议表按K-Radar v1、K-Radar v2、V2X三列排列：数据/标签版本、划分、类别、ROI、输入字段、检测头score预过滤、导出conf、NMS与AP计算方式。K-Radar v2的revised evaluator按41个precision值平均，不写成标准KITTI R40；V2X使用其记录的AP_R40口径。

**B.2 Model identities and checkpoint selection.** 区分论文报告值、官方权重结果归档、本地统一评测和本地重训。说明v1完整ObjDec、v2不含object context的Strong、V2X完整适配之间的身份差异。训练轮数和有效batch对齐描述为训练日程/样本预算匹配，另列初始化与实际耗时。

v1完整与消融模型都经过1,000样本小测，这一点已由作者说明。还需补成具体记录：样本ID或生成规则、所属划分、候选checkpoint范围、选择指标和并列处理。来源尚未核清前，不将这个子集命名为独立验证集，也不推断不同checkpoint编号意味着选模不公平。

V2X明确“按去重val严格Moderate平均3D AP选择best，然后报告test”。以当前Concat为例，第75轮是val选出的best；第80轮test略高不能据此改变选模规则。完整训练期验证曲线和best/last最终复评分别标识。

**B.3 Evaluator and postprocessing checks.** 用短段或可选小表呈现已有v2固定预测的11/41点、z中心交叉检查，解释早期L4DR对照为何不直接可比。正文只需保留影响表格解释的协议摘要，细节在这里展开。采用最终核验后的设置，不按实验排错时间线写。

**建议图表：** Table B.1协议与来源；选择清单可写成短表，不必单占整页。

**来源：** [v1阈值审计](asf_v1_conf_protocol_audit_260828.md)、[v2统一评测](taskdec_v2_l4dr_aligned_evaluation_260915.md)、[v2本地训练](taskdec_v2_matched_training_260915.md)、[V2X可比性](objdec_v2x_public_protocol_comparability_260919.md)。历史文件中的“重新评测”措辞需按当前来源核实：ASF归档不能写成本轮同时复测。

## 4. C：完整 K-Radar 结果

**C.1 Complete metrics and confidence settings.** 将正文选出的紧凑指标展开为AP3D/APBEV × IoU 0.3/0.5/0.7；v1和v2分面板，v2保留逐类及两类Mean。conf=0.3作为项目主设置，conf=0.0作为已有补充结果明确另列；conf=0.0仍可能保留检测头的score预过滤，不称为完全无阈值。

**C.2 Performance across weather conditions.** 按Total＋七天气排表，v2按Sedan和Bus/Truck分块，可借鉴此前L4DR式横向布局。AP3D@0.3和@0.5分面板，避免将所有IoU、3D/BEV、类别同时塞成不可读宽表。正文可用一句概括主要趋势，完整正负差值保留在表中。

表注说明：Total来自全体样本共同评测，不等于各天气AP的算术平均；无该类别GT的格子用“—”，尤其v2 Fog中的Bus/Truck。天气组帧数、GT数可在表头或单独小表交代。已有昼夜/道路结果作为可选补充，只在承担明确论点时排入PDF；其他完整机器结果可随匿名补充材料提供。

**建议图表：** Table C.1完整指标与阈值分面板；Table C.2完整天气结果，必要时跨页续表。

**来源：** [当前实验稿的数值索引](objdec_experiments_bilingual_initial_260919.md)、[v2五来源完整CSV](../analysis_exports/v2_matched_training_260915/reporting_strategy_260916/five_sources_full_metrics.csv)、[统一评测后的天气与Total](taskdec_v2_l4dr_aligned_evaluation_260915.md)、[v1天气材料](paper_main_table_kradar_v1_weather_compact_260901.md)。不要直接沿用9月12日尚未对齐的L4DR文献行来替换当前本地评测行。

## 5. D：组件与配置分析

**D.1 What each ablation removes.** 四项消融逐项解释实际干预，表中并列“改变的前向路径/损失”和完整检测指标：

- 去模态贡献控制：将相对模态缩放强度设为0，明确其他表征与控制路径保留。
- 去object context：关闭对应监督与query/output注入。
- 去解耦监督：关闭三项表征损失，但保留shared/specific分支和前向控制。
- 去前景gate：固定gate为1、关闭gate监督，保留其余结构。

正文表展示组件贡献，附录回答消融是否真的对应论文所说的设计。所选checkpoint和1,000样本选模规则引用B，避免重复解释。

**D.2 Control strength and configuration sensitivity（可选）.** 已有0.5/1.0强度结果可整理，但需先确认训练、初始化与选模的对应关系，并完整报告BEV等指标。现有表的部分BEV结果与主模型差距较大，不能仅因AP3D@0.3接近就概括为所有超参都不敏感。未核查是否已有的gate-bias、loss-weight等结果不占正式表格位置，也不因旧提纲提过就宣称已完成。

**建议图表：** Table D.1消融定义与完整结果；Table D.2已核实的配置敏感性为可选。

**D.3 Fixed-checkpoint inference interventions（2026-09-24已完成）.** K-Radar v1正式主模型的八组全量推理及baseline复核均完成：baseline、逐帧gate均值化、三种种子的空间打乱、关闭query增量、关闭output增量、同时关闭两种增量。固定10,065帧与conf=0.3，报告各IoU的3D/BEV及分天气结果。gate均值化使3D@0.3/BEV@0.5下降34.46/34.94点，空间打乱平均下降67.07/67.10点；同时关闭两种context增量仅下降0.0146/0.0087点。它们与D.1重新训练的组件消融分开呈现；三次打乱不称为三次训练，内部信号干预退化不称为加模块带来的等量收益。完整表、预测数量诊断及中英文表述见[结果汇总](objdec_kradar_v1_interventions_results_260924.md)，实现定义见[启动记录](objdec_kradar_v1_interventions_launch_260923.md)。

**来源：** [四项消融](taskdec_v1_component_ablation_conf0_3_260901.md)、[控制强度结果](taskdec_v1_control_strength_compare_260904.md)。历史表内同一主模型AP3D@0.7存在22.02/22.04等记录差异，正式汇表时按对应conf及原始JSON核定，统一来源后再计算差值。

## 6. E：表征与定性分析

这是最值得写充分的附录部分，承接论文的表征学习主线。先定义分析对象和统计单位，再看图。

**E.1 Extraction and statistical units.** 说明使用正式v1权重、覆盖10,065帧/51序列/642,649个前景patch位置。GT仅用于分析区域划分，不参与推理特征生成。明确以下三个不同量：

| 分析 | 单个观测是什么 | 聚合方式 |
|---|---|---|
| 全量帧均值PCA | 一帧、一模态、一类表征的前景patch均值向量 | 固定投影基后按天气展示 |
| 原始空间跨模态余弦 | 同一前景位置的一对模态向量 | 先位置、再帧、再天气聚合 |
| 天气质心变化 | 某天气、某模态的帧均值向量均值 | 比较天气组间质心与离散度 |

写清每种表征所用PCA拟合样本、是否共享投影基、归一化和显示抽样。不同表征若使用独立PCA空间，不跨图比较绝对距离；若只抽样显示，注明统计仍覆盖全量数据。连续帧不当作独立重复实验，分位范围不写成置信区间。

**E.2 Shared and modality-specific structure.** 给完整七天气PCA、原始空间相似度矩阵/分布以及按模态对拆分的统计。正文Fig.3保留最直观的组合，附录展示完整天气与分布。现有common平均跨模态余弦0.951–0.959、specific为0.446–0.549，是与训练目标一致的观察；结合D的消融解释作用，不单凭高余弦证明严格语义分离或排除表征坍塌。

**E.3 Spatial gating.** Fig.4保留预测gate和后叠加GT的同一热图。附录补充选帧规则、原始16×90网格、0.8m patch、统一色标、无平滑、FG/BG统计区域。七天气样本来自21帧既有候选池，不将七张示例的FG/BG均值称作全测试集gate统计。若正文已放七天气完整版，附录只加局部放大或未展示例子；若正文选3–4帧，则在附录放完整版。

**E.4 Detection examples and failure cases.** 在Fig.5之外选少量额外场景及至少一个定位较差案例；两模型共用阈值、视野、局部放大范围和颜色。图中选定目标的最大几何3D IoU不等于AP或官方一对一正确匹配。小雪例子存在较高gate但更差的最终框，可用于说明局部响应与完整三维定位之间的区别。20帧候选全集保留为材料索引，PDF中无需每帧都大幅重复。

**建议图表：** Table E.1天气/模态对的样本数和表征统计；Figure E.1七天气PCA；E.2原始空间相似度；E.3额外gate（按正文取舍）；E.4额外检测与失败案例。正常/大雪质心图为可选，不必为增加图量重复相似结论。

**来源：** [全量统计与图解](objdec_fulltest_weather_visualization_review_260919.md)、[全量PCA（蓝绿紫新版）](../analysis_exports/objdec_visuals_blue_green_purple_260923/fulltest/objdec_fulltest_frame_pca_all_weather.pdf)、[直接相似度分布（新版）](../analysis_exports/objdec_visuals_blue_green_purple_260923/fulltest/objdec_fulltest_direct_similarity_distributions.pdf)、[Fig.4/5与图注](../analysis_exports/objdec_fig4_fig5_260919/README.md)、[2026-09-23统一配色完整图稿](../analysis_exports/objdec_visuals_blue_green_purple_260923/README.md)。配色更新不改变原始数值、投影基或天气选例。

若后续有余力，“匹配位置与打乱位置”的高维相似度对照值得考虑，但当前没有完成，提纲不把它作为已有证据或必须立刻开跑的任务。

## 7. F：传感器可用性与损坏输入

**F.1 Fixed-checkpoint evaluation.** 每个数据设置固定同一checkpoint，列十种输入：C、L、R、C+L、C+R、L+R、C+L+R、C*、C*+L+R、C+L*+R。说明移除模态与损坏但保留分支的区别。

**F.2 Complete results and retention.** v1完整ObjDec和v2 Strong分两个面板，不互换模型身份。列绝对AP、相对完整输入的差值；AP保持率可选，但定义为AP之比，不能叫召回率。先按同一conf做自身对照，再单列另一档conf。C*为黑色RGB经过原归一化；L*是当前无回波特征约定，必须写清具体入口。

**F.3 Interpretation and ASF reference.** 可以用自身对照回答输入依赖问题。已经具备可比来源的ASF结果可另列参考；ASF表3的报告值与本地值分别标明来源，星号损坏规则及相机单路范围未完全对齐时，不作严格优劣排名。报告去相机后的保持，也保留缺LiDAR的大幅退化；相机单路弱、黑帧几乎不掉点不能单独证明门控识别可靠性的能力。

**建议图表：** Table F.1两个数据设置的十组合结果，必要时拆为F.1/F.2。默认不再加一张重复同组数值的柱状图。

**来源：** [v1已有双模态结果](paper_availability_missing_modalities_260902.md)、[v1补齐六项](taskdec_experiment_results_260918.md)、[v2十项及ASF表3来源边界](taskdec_v2_availability_vs_asf_table3_260918.md)。v1旧表含历史状态备注，正式表以对应原始结果和最新核查为准。

## 8. G：跨数据集架构适配

**G.1 Data and protocol adaptation.** 列当前公开包划分、去重规则、ROI、Vehicle合类与评测过滤。B给跨数据集协议总表，G补具体适配过程和与公开基准的区别。原论文与本地的数据版本、报告集合和ROI差异不能只藏在附录，正文4.5与Table 4表注保留简明声明。

**G.2 Architectures and matched settings.** 用结构表明确比较对象：

- Concat：三路BEV通道拼接，经3×3 Conv/BN/ReLU后进入公共BEV主干与检测头；卷积融合可学习，并非等权平均。
- ASF-style：canonical projection、局部attention与PFT的本地适配；no-SCL。
- ObjDec：以shared/specific、gate、模态贡献与object context共同构成主融合路径。
- ObjDec-LR：从训练起只有L+R；与从CLR训练模型中临时去相机的推理区分。
- L4DR：本地适配的原生L+R网络；与ObjDec-LR同模态/网格，但编码器和融合骨架不同。

**G.3 Complete results and spatial granularity.** 先列最终best的逐类val/test和BEV，另列best/last；0.4m与0.16m分组。同网格的Concat/ASF-style/ObjDec用于融合结构比较，ObjDec-LR与L4DR形成双模态参照。旧4×4到2×2改变patch与query数；0.4m到0.16m同时改变物理patch覆盖范围。逐项说明，结论保持在实际干预范围内。

**G.3内补充Training trajectories。** 一个双面板图即可：平均3D与Pedestrian 3D随轮次变化。使用真实已完成的同轮验证点，不用平滑曲线掩盖回落；未完成的曲线到最新点结束，不外推。最终稿优先在完整80轮结果到齐后统一排表。

**当前材料状态（2026-09-23更新）。** 五组0.16m实验的最终best/last均已完成。ASF-style选中第80轮，test平均3D/BEV为81.30/85.72；ObjDec-LR选中第75轮，为79.65/83.81，相对L4DR提高1.41/1.25点。ObjDec CLR按val选择第70轮，test平均3D/BEV为81.38/86.27；Concat选第75轮，为81.90/86.47。旧0.4m各组最终结果已具备。当前正文表4不再列Concat，附录保留其完整结果。正式汇表从final_best.json更新，不照抄早期进度快照。

**建议图表：** Table G.1结构、空间粒度与训练设置；G.2完整最终结果（分面板）；Figure G.1训练曲线。更全的难度/IoU矩阵可作续表或机器可读补充。

**来源：** [公开协议可比性](objdec_v2x_public_protocol_comparability_260919.md)、[0.16m配置](taskdec_v2x_grid016_launch_260918.md)、[ASF与LR配置](objdec_v2x_asf_lr_grid016_launch_260919.md)、[0.4m完整结果](taskdec_experiment_results_260918.md)、[Concat最终best](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/final_best.json)、[L4DR最终best](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/final_best.json)。

**G.4 Additional architecture adaptation on VoD（已补入）。** 报告原生PointPillars底座上的L+R适配，以表G.3a/G.3b分别展示官方EAA与DC，表G.4补充同一权重的KITTI 3D/BEV难度指标。2×2 patch＋局部编码版本为71.23/84.69，训练集适配锚框版本为72.03/83.76（EAA/DC）；保留类别收益与区域回退。交代80轮、有效batch16、每5轮EAA选模，以及历史基线／本地L4DR的训练差异。正文4.5只加一句引用，不再安排VoD正文表。来源：[完整数值及评测记录](objdec_vod_current_tables_260922.md)。

## 9. H：计算效率与适用范围

**H.1 Architecture and execution costs.** 先列ASF与ObjDec在相同eager路径下的参数/时间，再列双方采用同样CUDA Graph优化的结果。当前配对均值为84.00/84.69ms（ASF/ObjDec eager）和59.30/59.57ms（相同Graph优化）。解释计时涵盖预处理、传输、网络、解码、NMS及原路径的GT recall统计，排除读盘等；FP32张量与TF32设置、预热、样本数、同步方法和硬件写清。

将计算量、参数量、训练GPU小时、计时延迟分别命名；并发训练下的实际耗时不当作隔离条件的架构速度基准。100个不同计时帧重复两轮不是200个不同样本。

**H.2 Numerical checks and runtime scope.** 摘述抽样数值检查及原路径重复推理波动；Graph尚未完成全测试集AP复核，不能把新延迟与旧AP组合成已验证的全量精度无损结果。已知native退出异常用简短、具体的运行范围说明，详细日志留在可复现材料中；不把异常未定位写成稳定部署完成。

**H.3 Limitations.** 用约一至两段围绕当前证据写：单种子和选模范围；v2变体的身份；低分辨率/小目标表现与空间粒度；缺LiDAR下的退化；表征相似性不能替代语义或因果证明；V2X为目标数据集上训练后的架构适配，非零样本迁移。正文结尾保留最影响核心结论的简短限制，附录展开其依据。

**建议图表：** Table H.1同路径的完整配对效率表；profile分解图只有在确实解释瓶颈时再加入。

**来源：** [效率协议与数值核查](taskdec_inference_optimization_260917.md)、[原始汇总](../analysis_exports/inference_optimization_260917/comparison_summary.json)。

## 10. 图表规模、正文衔接与写作顺序

默认核心表约11张：A两张、B一张、C两张、D一张、E一张、F一张双面板、G两张、H一张。F若拆表或补D.2，编号顺延。核心图约4–5张：全天气PCA、原始相似度、额外gate（可省）、额外检测与反例、V2X曲线。另有一段前向/训练伪代码。这是素材规划，跨页表与复合图在正式排版时合并，不为凑数量重复正文。

2026-09-22实际稿已包含21个表格块，其中新增VoD表G.3的EAA/DC两个面板及表G.4。以上约11张为原规划量级，最终数量以实际稿与排版合并方案为准。

正文应保留这些信息：核心方法公式与GT仅训练监督；SCL启用情况；v2 Strong不含object context；主结果来源和置信度；V2X本地协议定位；关键失败范围。附录补充具体定义、完整数字和核查依据。

| 优先级 | 具体工作 | 是否需要新GPU实验 |
|---|---|---|
| 第一批 | A实现、B已知协议、D消融定义、F十组合表 | 不需要；B的v1选模记录需继续核清 |
| 第二批 | C原始数值统一汇表、E完整图注及统计单位、H计时协议 | 不需要 |
| 第三批 | G结构/协议先写，最终test表及80轮曲线随在训组完成后填入 | 等当前已启动实验，不在本提纲中另开实验 |
| 可选补证据 | matched/shuffled位置相似度、Graph全量AP、多种子等 | 尚未在此任务执行，按核心结论需要另定优先级 |

最需要补齐的记录是：v1的1,000样本选模明细、三组V2X最终结果，以及若要把优化延迟与AP配成正式部署结果所需的全量精度复核。其余大部分工作可以直接从已有材料整理，不必先等待全部训练结束。
