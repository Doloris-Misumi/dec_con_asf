# ObjDec：已完成章节与实验章节的正文／附录组织

日期：2026-09-19。本文是写作方案与材料索引，不是已经完成的实验章节。读取现有初稿、归档结果及训练状态；动态状态截至约19:54，未改变训练或评测。9月9日、17日的组织文件保留为历史记录，当前安排以本文件为准。

后续写作更新：已按本方案形成[实验章节中英文初稿](objdec_experiments_bilingual_initial_260919.md)，包含五个小节、四张正文表格及附录衔接备注；V2X未完成结果、Fig.5和选模记录保留明确占位。下文的状态清单保留本方案撰写时的快照。

2026-09-22组织决定：正文跨数据集验证使用V2X-Radar-V，VoD完整结果已补入[附录初稿](objdec_appendix_bilingual_initial_260920.md)G.4及表G.3a/G.3b、G.4。当前附录采用A–H编号，VoD并入G，不采用下文原规划的可选I节。历史进度快照不代表当前训练状态。

论文标题：**Decoupling to Fuse: Learning Shared and Modality-Specific Representations for Multi-Sensor 3D Object Detection**。

方法名：**ObjDec**。工程目录、脚本和历史实验标识仍使用 TaskDec，论文中统一名称即可。

## 1. 已完成的章节：初稿已具备，尚未整合成正式全文

| 部分 | 当前完成情况 | 核心内容 | 下一步整理 |
|---|---|---|---|
| 摘要 | 本地有中文初稿；英文经过对话修改，但本地摘要文件尚未收录完整英文正文 | 多传感器信息组织问题、ObjDec、主结果和开销 | 将实际提交英文与最终中文对应归档；不要把本地较早中文稿当成提交定稿 |
| 1 Introduction | 中英文初稿；ObjDec命名与近期文献已进入正文 | 空间对应之后的共享／特有信息组织，以及目标相关融合；三项贡献 | 精简第二段逐方法介绍；更新实验概述；插入独立动机图 |
| 2 Related Work | 两节完整双语初稿，文件记录23篇方法文献 | 多传感器融合检测；共享与模态特有表征学习 | 导入正式BibTeX，合并相邻引用，避免与引言重复；保持ASF等直接近邻的区别清楚 |
| 3 Method | 四节双语初稿、7组公式、主图图注及实现对应备注 | Overview → Object-Guided Representation Decoupling → Representation-Driven Fusion → Training Objectives and Inference | 主图按真实前向路径修订；将网络尺寸、损失系数、SCL实现和变体细节整理为附录 |
| 4 Experiments | 已有大量结果表、评测核查和图稿，尚无统一章节正文 | 性能、消融、表征、gate、扩展设置、可用性和效率 | 按下文组织；区分完成结果与训练中结果 |
| 5 Conclusion / Limitations | 当前所核查的章节材料中未形成独立完整初稿 | 总结设计和适用边界 | 实验结论确定后撰写，不先写多数据集全面领先 |
| Appendix | 方法备注和实验材料已存在，尚未统一编排 | 复现细节、完整指标、额外分析 | 建立统一节号、图表号和交叉引用 |

源文件：[摘要](taskdec_abstract_initial_draft_260917.md)、[引言](taskdec_introduction_bilingual_initial_260917.md)、[相关工作](taskdec_related_work_bilingual_initial_260917.md)、[方法](taskdec_methods_bilingual_initial_260917.md)。目前核查的项目根目录没有整篇论文的根LaTeX文件；results中已有若干独立结果表的LaTeX文件。

目前主线可以保留为：**对应空间内学习共享／特有表征 → 从表征预测目标相关控制 → 调制融合输入、查询和输出 → 用检测结果与内部行为共同检验设计。** 天气、缺模态和跨数据集实验承担适用范围分析，不需要再将全文改成天气方法。

## 2. 先固定每组证据验证的是哪个模型

| 实验 | 实际身份 | 可承担的论证 | 状态 |
|---|---|---|---|
| K-Radar v1 | 完整ObjDec，正式Robust model_0 | 正文主性能、组件消融、表征与空间gate | 已完成 |
| K-Radar v2 | DecControlled Strong：没有object context及对应query/output注入 | 解耦控制变体在宽ROI、双类别、修订标签下的表现 | 已完成，包含同训练日程对照与分条件结果 |
| V2X 0.4m | Concat、ASF-style、ObjDec 4×4／2×2 | 完整架构适配、空间粒度的经验分析 | 四组80轮及最终test已完成 |
| V2X L4DR 0.16m | L+R，原生网络本地适配 | 外部架构参照 | 80轮最终评测已完成；旧9月18日总稿的“在训”已过时 |
| V2X 0.16m C+L+R | ObjDec、Concat、ASF-style | 同输入、同网格及共同底座下的融合架构比较 | 仍在训练；ObjDec完成25轮、Concat完成74轮、ASF-style完成7轮 |
| V2X 0.16m ObjDec-LR | 从训练起使用L+R的完整双模态架构 | 与L4DR的同模态、同网格比较 | 完成7轮；不等于从CLR模型中删除相机的推理 |
| VoD | PointPillars体系中的早期适配 | 可选补充适配结果 | 已有结果，沿用此前决定不放正文主表 |

v1/v2是同一数据集的不同设置。V2X在目标数据集上训练属于架构适配／跨数据集适用性验证，不是零样本迁移。同轮数、有效batch对齐也不等于相同计算量。

状态来源：[0.16m第25轮结果](objdec_grid016_epoch25_comparison_260919.md)、[0.4m最终结果](taskdec_experiment_results_260918.md)、[新对照配置](objdec_v2x_asf_lr_grid016_launch_260919.md)，以及各实验status.json。L4DR最终best文件为[final_best.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/final_best.json)，第80轮、去重test平均3D为78.24；其网格与旧0.4m三模态实验不同。

## 3. 正文实验章节：建议五个小节

这是一套默认安排：**5张正文图（含引言与方法图）＋4张正文表**。效率使用短段落；天气和可用性用正文概括与附录完整表承接。先保证字体可读，再根据模板排版调整，不把该数量或占页建议当作会议规定。

| 小节 | 英文标题 | 回答的问题 | 正文材料 |
|---|---|---|---|
| 4.1 实验设置 | Experimental Setup | 在什么数据、模型与协议下比较？ | 三段设置说明，指向附录A/B |
| 4.2 K-Radar检测结果 | Detection Performance on K-Radar | 主设置是否有效，宽域多类别设置是否仍有收益？ | Table 1：v1；Table 2：v2 |
| 4.3 组件与计算开销 | Component Ablations and Computational Cost | 哪些设计有用，代价多少？ | Table 3：四项消融；参数和同条件延迟短段落 |
| 4.4 表征与定性分析 | Representation and Qualitative Analysis | 分支呈现什么结构，控制如何响应目标，预测有什么可见差异？ | Fig.3表征；Fig.4 gate；Fig.5检测实例 |
| 4.5 跨数据集架构验证 | Architecture Evaluation on V2X-Radar-V | 换数据、编码器、类别与空间设置后是否适用？ | Table 4：最终可比结果；详细适配与粒度分析放附录G |

正文实验不按“做实验的时间顺序”叙述，也不把每个天气、每个IoU、每个训练版本都另设小节。

### 4.1 Experimental Setup：写三个短段落

**Datasets and metrics.** 简述K-Radar v1单类窄ROI、v2双类宽ROI，以及V2X三类与去重划分。v1正文固定conf=0.3，并保留3D@0.3、3D@0.5和BEV指标；完整置信度与IoU分析放附录。V2X使用去重val/test、AP_R40、Moderate、严格类别IoU=0.7/0.5/0.5。明确天气AP、全量AP和类别平均的不同聚合方式。

**Compared models.** 区分文献报告、官方权重对应评测、本地重训和同底座适配。正文交代v2 Strong没有object context；ASF-style是本地no-SCL适配；L4DR使用L+R。关键身份放表注，不能只在附录说明。

**Training and selection.** 正文简述初始化／冻结策略、训练轮数、有效batch和选模。v2对齐11轮和batch2；V2X各组按80轮预算、有效batch8、val选best后测test。v1完整与消融均经过1000样本小测选模，但子集来源、候选checkpoint和指标还需归档；在核实之前不称独立验证集。SCL用一句说明继承关系与哪些设置启用，详细计算放附录，不单独包装成贡献。

### 4.2 Detection Performance on K-Radar

**Table 1：v1主表。** 建议列为Method、Sensors、Source、AP3D@0.3、AP3D@0.5、APBEV@0.3、APBEV@0.5。文献与本地结果分组，若缩表可删BEV@0.3，保留严格3D指标。不要仅按工程旧主表复制整张排行榜；近期相关方法的数字与协议需要逐项从已有文献核查表确认。

当前最明确的结果是ObjDec 88.36 / 67.50 / 88.84 / 88.10；相对官方ASF权重归档，AP3D@0.3与APBEV@0.5增益为8.04和7.77个百分点。差值按原始精度计算。

建议在本地主表组或紧邻讨论中保留本地ASF重训参照：其AP3D@0.3为88.57。该结果会影响读者如何解释官方权重上的大幅增益，应当可见。正文用一句说明收益随checkpoint和置信度口径变化，附录给conf=0.0全表。保持“对官方权重的增益”和“对本地重训的比较”分开。

**Table 2：v2紧凑表。** 以匹配训练日程的ASF与DecControlled Strong为直接比较，同时分组提供本地L4DR及官方权重参考。建议正文主要保留两类平均3D@0.3/@0.5/@0.7和BEV@0.5；完整两类×全部IoU/BEV放附录C。

可强调Strong相对本地ASF的六项总体指标均有数值提升，平均3D@0.3/@0.5为+2.14/+3.36，Bus/Truck@0.5为+6.09。该结果检验解耦控制变体，不能用来证明不存在于Strong中的目标上下文分支。

天气与可用性在这一节结尾各用一句引出附录：分条件比较用于检验收益分布；固定权重下改变可用传感器用于描述依赖关系。正文明确去掉LiDAR有明显退化，不使用无条件的传感器失效鲁棒性结论。天气组是已见条件分析，不称未见天气泛化。

来源：[v1主结果与协议边界](taskdec_full_paper_evidence_motivation_contributions_260917.md)、[v2同日程结果](taskdec_v2_matched_training_260915.md)、[v2完整报告策略](taskdec_v2_reporting_strategy_260916.md)。

### 4.3 Component Ablations and Computational Cost

**Table 3：完整模型＋四项移除。** 建议列AP3D@0.3、AP3D@0.5、APBEV@0.5，行名统一为Full ObjDec、w/o modality contribution control、w/o object context、w/o decoupling supervision、w/o foreground gating。表注说明实际关闭的计算路径；“移除解耦监督”仍保留分支结构。

| 现有结果 | AP3D@0.3 | AP3D@0.5 |
|---|---:|---:|
| Full ObjDec | 88.36 | 67.50 |
| w/o modality contribution control | 79.62 | 64.38 |
| w/o object context | 80.14 | 66.23 |
| w/o decoupling supervision | 80.23 | 66.16 |
| w/o foreground gating | 80.00 | 64.80 |

写作上先归纳四种移除均降低已报告检测指标，再解释各设计与方法章的联系。当前不是“shared-only／unique-only”实验，也不是分别移除query/output调制的实验，不使用这些标题。控制强度扫描和gate bias放附录D。

开销用一个短段落：参数78.13M→79.47M，增加约1.7%。同一配对测速中eager为ASF84.00ms、ObjDec84.69ms；相同CUDA Graph优化后为59.30ms和59.57ms，支持延迟接近。优化版全量AP尚未复核，暂不将59.57ms与旧全量AP拼成已验证的精度—速度主结论。完整计时范围、抽样、重复次数、输出差异和退出异常放附录H。

来源：[四项消融](taskdec_v1_component_ablation_conf0_3_260901.md)、[控制强度](taskdec_v1_control_strength_compare_260904.md)、[效率复测](taskdec_inference_optimization_260917.md)。

### 4.4 Representation and Qualitative Analysis

这节与方法的表征学习定位直接对应，建议保留约三段，每段回答一个问题。

**Learned representations / Fig.3.** 说明Input、Shared和Modality-specific呈现不同模态结构。PCA负责展示分布；原始256维余弦负责直接展示相似度。现有全量统计覆盖10,065帧、51序列、642,649个前景patch位置，七天气Shared平均跨模态余弦为0.951–0.959，Specific为0.446–0.549。它们支持两类分支表现不同，检测作用由消融补充。

正文图建议组合为：上排Input／Shared／Specific三幅PCA，下排紧凑的原空间模态相似度矩阵或七天气相似度热图，两种统计图择一。可用已存结果重新排版；目前完整组合版尚未制作。每个PCA点采用patch或帧均值中的一种明确口径，不能混标；若用现有全量图，点是前景帧均值。相似度来自匹配前景patch，并非帧均值余弦。各表示空间分别拟合PCA，不跨列比较二维距离绝对大小。

**Spatial control / Fig.4.** 使用已有两帧真实相机、LiDAR BEV+GT和完整预测gate。分别对应清楚的空间目标与雨夜复杂场景；两帧FG/BG gate均值约0.30/0.11和0.29/0.12。强调门控在目标区域响应较强，同时保留弱响应目标。Gate调制更新幅度，不是把全部背景删除，也不是注意力权重或物理可靠性。

**Detection examples / Fig.5.** 两个同场景方法对照，统一阈值、ROI、GT和显示设置；优先用真实相机参照＋ASF BEV预测＋ObjDec BEV预测的三列版式，三维框投影核验完成后再叠到相机。附录补充失败案例。现有素材方案不能当成已完成Fig.5；官方ASF的逐帧候选预测仍需补齐或核验。

这里不将高余弦、模态分开、天气组间差异写成严格语义分解或因果证据。匹配位置与打乱位置对照、有效秩等可以作为后续可选诊断，目前未完成，不写入已有结果。

来源：[全量表征统计与图稿](objdec_fulltest_weather_visualization_review_260919.md)、[完整gate图稿](../analysis_exports/taskdec_bev_gate_fig4_260910/README.md)、[Fig.5素材与制作方案](taskdec_figure_draft_review_and_fig5_plan_260917.md)。

### 4.5 Architecture Evaluation on V2X-Radar-V

**Table 4：正文预留，最终数字等待统一测试。** 建议列Method、Sensors、Grid、Vehicle、Pedestrian、Cyclist、Mean AP3D。三模态同底座组：Concat、ASF-style、ObjDec，统一0.16m；双模态组：L4DR和ObjDec-LR，明确二者骨架不同。不能将不同轮次的val与最终test放同一排名。

本表的基本问题是完整融合路径在新输入体系中的适用性。即使不同方法各有长处，也可以报告；不把“必须所有行第一”设为保留表格的条件。若篇幅要求正文只保留三模态同底座组，双模态外部架构组可完整放附录，并在正文指向它；分组依据是输入与实验问题，不是结果高低。

旧0.4m test已完成：Concat75.77、ASF-style72.17、ObjDec4×4为72.22、ObjDec2×2为74.03。2×2比4×4和ASF-style高，但仍低于Concat。这些结果适合放附录解释空间粒度，不写跨数据集全面领先。patch与query数同步变化，不能归因于单一网格因素。

新0.16m实验未完成时，正文可以先写设置与比较问题，Table 4保留待填状态。若投稿冻结时仍未完成，则使用已完成、同协议的一整组结果并准确陈述边界，不用早期优势轮次代替最终测试，也不将新旧网格中各自最好指标拼接。

## 4. 正文图表的插入位置与当前状态

| 编号 | 内容 | 插入位置 | 当前状态 |
|---|---|---|---|
| Fig.1 | 独立动机：混合信息→共享／特有组织→目标引导融合 | Introduction研究问题段附近 | 9月19日有新版概念草图；需手工减字并统一ObjDec名称 |
| Fig.2 | 主架构及训练监督路径 | Method 3.1 Overview之后 | 有概念草图与核查备注；公式、箭头和通道需修订 |
| Fig.3 | PCA＋原始高维相似度 | Experiments 4.4第一段 | 基础图与全量数据已具备，正文组合排版待做 |
| Fig.4 | 真实场景＋完整空间gate | 4.4第二段 | 已有两帧初稿，改名、字体与图例统一后可排版 |
| Fig.5 | 同帧ASF／ObjDec预测框对照 | 4.4第三段 | 素材方案已完成；成图未完成 |
| Table 1 | K-Radar v1主性能 | 4.2第一部分 | 数据已具备，需更新来源分组与关键对照 |
| Table 2 | K-Radar v2紧凑比较 | 4.2第二部分 | 已完成；需显式标明Strong变体 |
| Table 3 | 完整模型与四项消融 | 4.3 | 数字已完成；选模流程待补充记录 |
| Table 4 | V2X最终同协议架构比较 | 4.5 | 有旧组完整结果，新0.16m组尚未完成 |

默认维持5图4表。若版面不足，优先减少每图案例与重复指标、压缩引言中的逐方法介绍；可将Fig.4与Fig.5组合成一张含gate和预测的多面板图，保留正文中的真实场景。不要同时放全七天气PCA、全七天气余弦矩阵和全部小提琴图。

## 5. 附录结构：复现细节、完整结果、扩展分析

| 附录 | 内容 | 建议图表／材料 | 正文保留的必要信息 |
|---|---|---|---|
| A. Implementation Details | 编码器、投影、通道、patch/query、前景目标生成、损失、SCL、初始化和冻结策略 | Table A1：模型配置；A2：训练及损失系数 | ASF继承关系，SCL是否启用，推理不需要GT |
| B. Evaluation and Selection Protocols | v1/v2标签与ROI、评测器、score/NMS、1000样本选模、V2X去重与选best规则 | Table B1：协议与checkpoint来源 | conf、模型身份、模态、主要选模规则 |
| C. Complete K-Radar Results | v1全部IoU与conf；v2逐类IoU/BEV；完整七天气、昼夜及有用条件分组 | Table C1–C3，过宽时按v1/v2分面板 | 对主要结论有影响的阈值敏感性与例外 |
| D. Additional Ablations | 四项消融的全部指标与关闭项、控制强度、gate bias | Table D1；必要时一幅敏感性曲线 | 不把无监督消融等同于移除分支；部分bias仅subset |
| E. Extended Representation Analysis | 全天气PCA、余弦分布、天气质心与离散度、完整gate案例、模态贡献分布 | Fig.E1七天气PCA；E2相似度分布；E3额外gate；E4检测成功／失败；统计CSV索引 | PCA统计单位与投影口径；分析不构成因果证明 |
| F. Sensor Availability and Corruption | 固定权重的7种非空模态子集及3种本地损坏设置；v1/v2、天气与两档conf | Table F1：v1十行；F2：v2十行，必要时拆天气面板 | 缺LiDAR退化；缺失与损坏不同；Strong身份 |
| G. V2X Adaptation and Spatial Granularity | 0.4/0.16m、4×4/2×2、query变化、L+R对照、完整类别与难度、训练曲线和成本 | Table G1；Fig.G1：同轮趋势；完整指标附表按需拆分 | 不称零样本泛化；不混val/test或不同网格 |
| H. Efficiency and Limitations | eager/graph配对测速、硬件、时间范围、数值检查、未解决的部署问题和适用边界 | Table H1：相同执行方式的完整测速 | 同等优化延迟接近；单种子、模态依赖等主要限制 |
| I. Optional VoD Results | 如保留，报告原生PP适配及实际初始化、FP32和选模条件 | Table I1：完整可比行 | 不与V2X混成零样本泛化，不拼不同checkpoint指标 |

附录建议约11–12个表号、5–6个图号，具体取决于天气大表拆分和是否保留VoD；这是材料组织量级，不需要为达到数量重复内容。正文表的完整扩展版本可以放附录，但要解释它新增了哪些维度。

缺模态的十行总表：C、L、R、C+L、C+R、L+R、C+L+R、C*、C*+L+R、C+L*+R。v1原四组合与后补六组合合并时还需核对全部天气／阈值字段；六项补测已结束不等于旧四组合所有细粒度字段都已重新审计。v2十组已在同一轮完成。

v2和ASF论文表3的比较可作为附录参考表，使用对应的conf=0.0输出并明确仍有检测头score预过滤。ASF相机单路样本范围及星号损坏规则未完全对齐，不把这些行作为严格配对胜负。来源：[v1补测](taskdec_v1_availability_completion_launch_260918.md)、[v2可用性完整对照](taskdec_v2_availability_vs_asf_table3_260918.md)。

## 6. 现在即可写，与后续需要补齐的内容

**现在即可写：** 4.1设置框架；4.2 v1/v2结果；4.3消融和保守效率结论；4.4表征与gate文字；附录A–F的大部分内容。正文4.5先完成设置和表结构，最终结论随完整结果填写。

**优先完成的编辑与证据整理：**

1. 将已提交英文摘要与本地中文、引言、方法的命名和结果表述统一；更新旧总稿中过时的实验状态。
2. 固定正文四张表的来源与显示精度；为v1官方ASF、本地重训及阈值敏感性写清楚相邻说明。
3. 补齐1000样本选模的子集来源、样本ID、候选checkpoint和指标。现有“做过小测”的作者说明保留，但不替代记录。
4. 将全量PCA与高维余弦重新组合为Fig.3；只需CPU绘图，不需要重复导出全量特征。
5. 完成Fig.1/2手工修订与Fig.5同帧真实预测对照。若要补候选帧推理，另行安排空闲GPU，不在本次写作梳理中启动。
6. 等0.16m各组完成后，从固定选模协议读取最终test，冻结Table 4；避免依据测试结果重新选择配置或checkpoint。

**有余力再做，不作为已完成结果：** 增补shared-only／specific-only或匹配与打乱位置诊断，可更直接检验表征作用；若要把优化速度与原精度配成正式结果，再补优化执行路径的全量AP核验及退出异常排查。这些需新的实验安排，本次没有启动。

全文的主要结论保持为：**目标区域约束与表征驱动的融合计算，在指定K-Radar协议下带来检测收益；消融和全量表征分析说明该设计的作用与行为，扩展实验进一步展示适用范围和限制。**
