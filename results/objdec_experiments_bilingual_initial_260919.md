# ObjDec Experiments：中英文初稿

日期：2026-09-19。按[正文／附录组织方案](objdec_chapter_status_and_experiments_plan_260919.md)撰写。中文与英文正文对应，表格在第三部分统一提供，避免两个语言版本重复维护数字。方法名统一为ObjDec，历史文件名保持不变。

**初稿状态。** 4.1–4.4已依据完成的评测写出正文；4.5与表4已按公开方法参考／本地融合对照重组，五组本地实验的最终best/last测试均已完成。Concat受控对照保留在附录G.1/G.2。Fig.3组合排版尚待完成；Fig.4已扩展为七天气，Fig.5已有真实成对推理初稿，见[图稿及来源说明](../analysis_exports/objdec_fig4_fig5_260919/README.md)。方括号中的文献名待替换为正式引用；`〔待补〕 / [TO COMPLETE]`为投稿前编辑标记。附录A–H已有[中英文初稿](objdec_appendix_bilingual_initial_260920.md)，含实现细节、补充指标及图注；未完成项见[核对说明](objdec_appendix_source_notes_260920.md)。Fig.5补充了两模型各20帧的小规模推理，没有修改训练或全量评测协议。

## 一、中文正文

### 4.1 实验设置

**数据集与指标。** 我们以K-Radar为主要实验平台，并在V2X-Radar-V上考察架构在不同传感器输入与类别设置下的适用性 [K-Radar; V2X-Radar]。K-Radar v1采用Sedan单类别与窄范围设置，评测区域为\([0,72]\times[-6.4,6.4]\times[-2,6]\) m，过滤后的测试集包含10,065帧。v2采用修订标签，将横向范围扩展至\([-16,16]\) m、高度范围扩展至\([-2,7.6]\) m，并评测Sedan和Bus/Truck两类，共13,727个测试帧。我们报告三维与鸟瞰图平均精度\(\mathrm{AP}_{3D}\)和\(\mathrm{AP}_{BEV}\)，v2的Mean为两类AP的算术平均。K-Radar正文结果使用置信度预过滤阈值0.3；其他阈值、完整IoU结果和两版本评测器的具体差异见附录B、C。V2X采用去重后的1,487帧验证集和1,486帧测试集，报告Moderate难度下的AP\(_{R40}\)；Vehicle、Pedestrian和Cyclist的IoU阈值分别为0.7、0.5和0.5。

**对照方法与模型设置。** 我们区分文献报告结果、官方权重对应结果和本地训练结果。v1使用第3节定义的完整ObjDec。v2采用DecControlled Strong变体，保留共享／特有表征、前景门控与模态贡献控制，不包含目标上下文及其查询／输出调制。该设置用于检验解耦控制在宽范围与额外类别下的表现。ASF是三模态融合的直接参照，L4DR提供LiDAR–雷达架构对照 [ASF; L4DR]。V2X的ASF-style基线保留统一投影、局部注意力与后续特征变换，并在共同底座上移除ObjDec的表征分支与控制路径；该适配未使用SCL。不同来源、模态及初始化均在表中或表注标明。

**训练与模型选择。** K-Radar的ASF／ObjDec系列使用预训练模态编码器，冻结其参数，并按原训练设置更新BatchNorm统计；训练采用AdamW。v2本地对照固定相同训练集、11轮和有效batch size 2，评测末轮权重。ASF与Strong使用同组预训练编码器，L4DR从头训练原生网络，因此这一对照匹配训练日程与样本预算。v1完整模型与消融版本均经过1,000样本预评测选模，再进行全量评测；子集来源、候选范围与选择指标列于附录B〔待补：选模记录〕。V2X使用80轮预算、有效batch size 8，以验证集平均\(\mathrm{AP}_{3D}\)选择权重后评测测试集。K-Radar主配置保留ASF的传感器组合监督，V2X适配关闭该项。网络尺寸、学习率日程与损失权重见附录A。

### 4.2 K-Radar上的检测结果

**v1主结果。** 表1给出Sedan窄范围设置的比较。ObjDec取得88.36的\(\mathrm{AP}_{3D}@0.3\)与88.10的\(\mathrm{AP}_{BEV}@0.5\)，相对相同置信度设置下的官方ASF权重对应结果，分别提高8.04和7.77个百分点；在更严格的\(\mathrm{AP}_{3D}@0.5\)上由67.19提高至67.50。结果表明，该设置下的收益主要体现在宽松三维匹配与BEV检测。表中同时保留本地重训ASF：ObjDec相对该参照的\(\mathrm{AP}_{BEV}@0.5\)提高7.73点，\(\mathrm{AP}_{3D}@0.5\)接近，而\(\mathrm{AP}_{3D}@0.3\)略低0.22点。附录C进一步报告置信度敏感性；当额外置信度过滤阈值为0.0时，ObjDec与同一官方ASF归档的\(\mathrm{AP}_{3D}@0.3\)分别为88.06和87.34。因此，上述增益应结合所列权重与评测设置理解。

**v2扩展设置。** 表2考察更宽空间范围和双类别设置。在相同训练日程下，DecControlled Strong的平均\(\mathrm{AP}_{3D}@0.3/@0.5/@0.7\)为66.91/43.05/11.11，较本地ASF分别提高2.14/3.36/1.56个百分点；完整结果中的六项总体3D/BEV指标均有数值提升。Bus/Truck的\(\mathrm{AP}_{3D}@0.5\)由27.88提高至33.97，说明收益也出现在v1主设置之外的类别中。相对官方ASF归档，Strong的平均\(\mathrm{AP}_{3D}@0.5\)仍提高1.48点。官方L4DR在平均\(\mathrm{AP}_{3D}@0.3/@0.5\)上更高，反映了不同架构及训练条件下的性能差异。此实验支持解耦控制变体在扩展设置中的适用性。

**条件与传感器可用性。** 附录C、F给出分天气结果及固定权重的缺失／损坏模态分析。v2相对本地ASF，在IoU为0.3和0.5的26个有效天气–类别指标中，24项取得更高AP，另两项有所下降。v1模型去掉相机后\(\mathrm{AP}_{3D}@0.3\)为88.06，接近完整输入的88.36；去掉LiDAR后降至57.62。结果显示模型在部分输入变化下保持性能，同时仍明显依赖LiDAR。我们将天气分组和传感器可用性作为条件分析，并在附录保留全部组合及例外。

### 4.3 组件消融与计算开销

**组件作用。** 表3分别关闭模态贡献控制、目标上下文、解耦监督和前景门控，以检验第3节中的设计。在所报告的选模与评测流程下，四项移除均降低\(\mathrm{AP}_{3D}@0.3\)和\(\mathrm{AP}_{3D}@0.5\)。关闭模态贡献控制后，两项指标由88.36/67.50降至79.62/64.38；移除目标上下文后降至80.14/66.23，支持根据学习到的表征调节模态贡献和跨模态交互。移除解耦监督时仍保留表征分支与前向控制，结果降至80.23/66.16，说明表征约束在该配置中发挥作用。将前景门控固定为1并移除其监督后，两项指标降至80.00/64.80。正文未列的严格3D与BEV指标，以及各移除项的具体实现见附录D。

**计算开销。** 相对ASF，ObjDec参数量由78.13M增加至79.47M，增幅约1.7%。在同一RTX A6000、batch size 1的配对测速中，ASF与ObjDec的标准eager执行时间分别为84.00和84.69 ms。该计时包含预处理、设备传输、编码、融合、检测解码及NMS，不包含磁盘读取与批次整理。在相同CUDA Graph优化下，两者分别为59.30和59.57 ms，表明新增计算路径的延迟开销较小。优化结果目前经过抽样数值核对，尚未复核全测试集AP；附录H单独给出其计时协议、数值检查与运行限制。

### 4.4 表征与定性分析

**共享与模态特有表征。** 我们对v1完整测试集的10,065帧、51个序列及642,649个前景patch位置进行表征分析。PCA对每帧全部前景patch的均值向量进行可视化；跨模态相似度则在原始256维空间中，对匹配前景位置计算余弦，再在帧内与天气组内平均。两种分析分别描述场景层面的分布和局部对应表征的一致性。七种天气下，共享分支的平均跨模态余弦为0.951–0.959，模态特有分支为0.446–0.549，符合两类分支的学习目标。PCA还显示共享表征保留模态相关的残余结构，因此高维一致性不要求二维投影完全重合。结合表3的消融，这些结果支持表征组织与检测收益之间的联系；单凭相似度并不能证明严格语义分解。完整天气分布、投影口径及相似度分布见附录E。

> **Fig.3插入位置。** 将已有PCA与原始高维相似度组合排版；以上数值来自已完成的全量统计，组合图本身尚待制作。2026-09-23已统一为Camera蓝／LiDAR绿／Radar紫，使用[新版图稿索引](../analysis_exports/objdec_visuals_blue_green_purple_260923/README.md)中的全量PCA及高维相似度图。

**空间门控。** 图4从正常、阴天、雾、雨、雨夹雪、小雪与大雪中各选择一个真实场景，展示相机参照、LiDAR BEV、预测前景gate及叠加GT参照的同一gate。门控由多模态表征直接预测，训练时用GT衍生标签监督，推理时无需GT或预先检测的目标框。两列热图数值相同，绿色虚线框在预测完成后叠加，GT也用于事后的区域统计。七个所选案例的前景平均gate为0.282–0.371，背景均值为0.108–0.121；目标位置呈现局部较高响应，同时仍存在弱响应目标及框外响应。图中采用完整空间网格和统一色标，不进行平滑。上述数值描述定性选例，不作为各天气总体统计；完整选帧规则与逐帧数值见附录E。

> **Fig.4插入位置。** [七天气PDF（2026-09-23统一配色）](../analysis_exports/objdec_visuals_blue_green_purple_260923/gate/fig4_objdec_all_weather.pdf)已完成，另有各天气独立PNG/PDF/SVG用于重排。样本及gate数值与旧版相同。正文若改为3–4例，七天气版放附录并同步修改本段。

**检测可视化。** 图5对比官方ASF权重与ObjDec在相同测试帧上的检测输出。两模型使用相同输入、检测后处理及0.3置信度显示阈值，展示相机投影、完整BEV与共享局部放大区域。正常天气案例中，所示远处目标的最大3D IoU由0.572提高至0.719；阴天和雨夜案例中，ASF在该显示阈值下没有与所示目标重合的保留预测，而ObjDec对应框的3D IoU分别为0.476和0.741。阴天案例不构成IoU=0.5下的正确匹配。上述观察仅针对所选场景；附录E保留全部候选及定位较差的反例，不从单帧推断总体收益。

> **Fig.5插入位置。** [检测对照PDF](../analysis_exports/objdec_fig4_fig5_260919/fig5_asf_objdec_detection_draft.pdf)已完成初稿；[雪天及反例](../analysis_exports/objdec_fig4_fig5_260919/fig5_snow_and_counterexample.pdf)供附录备选。图中IoU为所选GT与保留预测的最大几何3D IoU，不是AP。

### 4.5 V2X-Radar-V上的架构验证

**评测目的与设置。** 我们在V2X-Radar-V上考察ObjDec在另一数据集、三类目标和不同传感器组合下的架构适用性。模型在该数据集上重新训练，保留共享／特有表征、前景门控、模态贡献控制和目标上下文调制，并使用Vehicle、Pedestrian和Cyclist三类上下文。本地实验采用8,391帧训练集、去重后的1,487帧验证集与1,486帧测试集，ROI为\([0,102.4)\times[-51.2,51.2)\times[-5,3)\) m，统一使用0.16 m网格、80轮预算与有效batch size 8。

**代表方法与比较组织。** 表4(a)列出原数据集论文中PointPillars、CenterPoint、PV-RCNN、SQDNet、BEVDepth与RPFA-Net的公开结果，涵盖LiDAR、相机和雷达检测路线，作为基准背景参考 [V2X-Radar]。这些结果使用原论文的验证集协议，与本地数据版本、划分和评测范围存在差异，因此不与表4(b)跨面板排名或计算增益。表4(b)集中比较融合方法：C+L+R组在共同编码器与检测头上对照ASF-style和ObjDec，两者均使用2×2 patch与4个查询；L+R组对照独立训练的L4DR与ObjDec-LR，并保留各自原生网络。ASF-style为不含SCL的本地适配。

**同模态检测结果。** 表4(b)报告按验证集平均3D AP选择权重后的最终测试结果。在L+R输入下，ObjDec-LR取得79.65%的平均3D AP和83.81%的平均BEV AP，较L4DR分别提高1.41和1.25个百分点；Vehicle、Pedestrian与Cyclist的3D AP分别提高0.71、1.58和1.93点，三类BEV AP也均有提升。在C+L+R输入下，ObjDec取得81.38%的平均3D AP与86.27%的平均BEV AP，相对ASF-style分别提高0.08和0.55点。该组平均3D差异较小，主要收益体现在Cyclist及BEV指标；Vehicle和Pedestrian的3D AP仍分别低0.47和0.24点。两组同模态结果支持ObjDec在另一数据集及不同输入组合下的适用性，但L+R对照保留各自网络差异，不能将其全部收益归于单个融合组件。公共底座下的Concat受控对照、逐类BEV、空间粒度及best/last结果见附录G.1–G.3；VoD补充实验见附录G.4。

> **编辑记录，提交前移除。** 2026-09-23已补齐表4(b)。ObjDec、ASF-style、L4DR与ObjDec-LR分别采用val选中的第70、80、80与75轮；best/last最终测试均已完成。本节评估在目标数据集上训练后的适用性，不作零样本迁移或公开基准SOTA的主张。[当前完整3D/BEV记录](objdec_v2x_current_total_table_260923.md)；[表格与章节安排](objdec_v2x_paper_comparison_260923.md)。

## 二、English draft

### 4.1 Experimental Setup

**Datasets and metrics.** We use K-Radar as the primary benchmark and extend the evaluation to V2X-Radar-V to examine the architecture under different sensor inputs and object categories [K-Radar; V2X-Radar]. K-Radar v1 evaluates Sedan within a region of \([0,72]\times[-6.4,6.4]\times[-2,6]\) m, with 10,065 test frames after filtering. Version v2 uses revised labels, expands the lateral and vertical ranges to \([-16,16]\) and \([-2,7.6]\) m, and evaluates Sedan and Bus/Truck over 13,727 test frames. We report 3D and bird's-eye-view average precision, denoted by \(\mathrm{AP}_{3D}\) and \(\mathrm{AP}_{BEV}\); Mean on v2 is the arithmetic mean over the two classes. Main K-Radar results use a confidence prefilter of 0.3. Additional thresholds, complete IoU results, and the evaluator differences between v1 and v2 are detailed in Appendices B and C. On V2X, we use deduplicated validation and test sets containing 1,487 and 1,486 frames. We report Moderate AP\(_{R40}\) at IoU thresholds of 0.7, 0.5, and 0.5 for Vehicle, Pedestrian, and Cyclist, respectively.

**Compared methods and model configurations.** We distinguish published results, results associated with released checkpoints, and local training runs. The v1 experiments use the complete ObjDec architecture described in Section 3. For v2, we evaluate DecControlled Strong, which retains shared and modality-specific representations, foreground gating, and modality contribution control, but omits object context and its query/output modulation. This setting examines decoupled control under wider spatial coverage and an additional category. ASF serves as the direct three-sensor fusion reference, while L4DR provides a LiDAR–radar architectural comparison [ASF; L4DR]. The V2X ASF-style baseline retains unified projection, local attention, and subsequent feature transformation, with the ObjDec representation branches and control paths removed from the common backbone; this adaptation does not use SCL. Sources, modalities, and initialization differences are identified in the tables or captions.

**Training and model selection.** The K-Radar ASF/ObjDec models use pretrained modality encoders with frozen parameters, while BatchNorm statistics follow the original training behavior. We use AdamW for training. Local v2 comparisons use the same training set, 11 epochs, and an effective batch size of 2, followed by evaluation of the final checkpoint. ASF and Strong use the same pretrained encoders, whereas L4DR trains its native network from scratch; this comparison therefore matches the training schedule and sample budget. The full v1 model and ablated variants undergo preliminary evaluation on 1,000 samples for checkpoint selection, followed by full-set evaluation; Appendix B specifies the subset provenance, candidates, and selection metric [TO COMPLETE: selection records]. V2X uses an 80-epoch budget and an effective batch size of 8, selecting checkpoints by validation mean \(\mathrm{AP}_{3D}\) before testing. ASF's sensor-combination supervision is retained in the primary K-Radar configurations and disabled in the V2X adaptation. Network dimensions, learning-rate schedules, and loss weights are provided in Appendix A.

### 4.2 Detection Performance on K-Radar

**Main results on v1.** Table 1 compares methods under the Sedan narrow-region setting. ObjDec achieves 88.36 \(\mathrm{AP}_{3D}@0.3\) and 88.10 \(\mathrm{AP}_{BEV}@0.5\), improving over the results associated with the released ASF checkpoint at the same confidence threshold by 8.04 and 7.77 percentage points. At the stricter \(\mathrm{AP}_{3D}@0.5\), performance increases from 67.19 to 67.50. The gains in this comparison are concentrated at the lower 3D IoU threshold and in BEV detection. We also report a locally retrained ASF reference: ObjDec improves \(\mathrm{AP}_{BEV}@0.5\) by 7.73 points, achieves similar \(\mathrm{AP}_{3D}@0.5\), and is 0.22 points lower in \(\mathrm{AP}_{3D}@0.3\). Appendix C reports confidence sensitivity; with the additional confidence filter set to 0.0, ObjDec and the same official ASF archive achieve 88.06 and 87.34 \(\mathrm{AP}_{3D}@0.3\). The reported gains are therefore specific to the checkpoints and evaluation settings shown.

**Extended setting on v2.** Table 2 evaluates wider spatial coverage and two object categories. Under the matched training schedule, DecControlled Strong achieves mean \(\mathrm{AP}_{3D}@0.3/@0.5/@0.7\) of 66.91/43.05/11.11, exceeding locally trained ASF by 2.14/3.36/1.56 percentage points. All six aggregate 3D/BEV metrics in the complete results improve numerically. Bus/Truck \(\mathrm{AP}_{3D}@0.5\) increases from 27.88 to 33.97, showing gains on a category beyond the primary v1 setting. Strong also exceeds the official ASF archive by 1.48 points in mean \(\mathrm{AP}_{3D}@0.5\). The released L4DR checkpoint remains stronger in mean \(\mathrm{AP}_{3D}@0.3/@0.5\), reflecting differences in architecture and training conditions. These results support the applicability of the decoupled-control variant to the extended setting.

**Conditions and sensor availability.** Appendices C and F report weather breakdowns and missing/corrupted-input analyses with fixed model weights. On v2, Strong improves over locally trained ASF in 24 of the 26 valid weather–class entries at IoU 0.3 and 0.5, with decreases in the remaining two entries. On v1, removing the camera yields 88.06 \(\mathrm{AP}_{3D}@0.3\), close to 88.36 with all sensors, whereas removing LiDAR reduces it to 57.62. The model thus retains performance under some input changes while remaining dependent on LiDAR. We treat weather groups and sensor availability as conditional analyses and report the complete combinations and exceptions in the appendix.

### 4.3 Component Ablations and Computational Cost

**Component contributions.** Table 3 separately disables modality contribution control, object context, decoupling supervision, and foreground gating. Under the reported selection and evaluation procedure, all four changes reduce both \(\mathrm{AP}_{3D}@0.3\) and \(\mathrm{AP}_{3D}@0.5\). Disabling modality contribution control lowers these metrics from 88.36/67.50 to 79.62/64.38; removing object context yields 80.14/66.23, supporting representation-driven regulation of modality contributions and cross-modal interaction. Removing decoupling supervision retains the representation branches and forward control paths but reduces the scores to 80.23/66.16, indicating a contribution from the representation constraints in this configuration. Fixing the foreground gate to one and removing its supervision yields 80.00/64.80. Appendix D provides stricter 3D and additional BEV metrics omitted here, together with implementation details of each ablation.

**Computational cost.** ObjDec increases the parameter count from 78.13M to 79.47M relative to ASF, an increase of approximately 1.7%. In paired measurements on an RTX A6000 with batch size 1, standard eager execution takes 84.00 ms for ASF and 84.69 ms for ObjDec. Timing includes preprocessing, device transfer, encoding, fusion, detection decoding, and NMS, while excluding disk loading and collation. With the same CUDA Graph optimization, the times are 59.30 and 59.57 ms, respectively, indicating a small latency overhead for the added computation paths. The optimized path has undergone sampled numerical checks but has not yet been evaluated for full-test AP; Appendix H separately documents its timing protocol, numerical checks, and runtime limitations.

### 4.4 Representation and Qualitative Analysis

**Shared and modality-specific representations.** We analyze all 10,065 v1 test frames, covering 51 sequences and 642,649 foreground patch locations. PCA visualizes vectors obtained by averaging all foreground patches within each frame. Cross-modal similarity is measured separately by computing cosine similarity at matched foreground locations in the original 256-dimensional space, followed by averaging within frames and weather groups. The two analyses characterize scene-level distributions and local cross-modal consistency, respectively. Across the seven weather groups, mean cross-modal cosine similarity ranges from 0.951 to 0.959 for shared representations and from 0.446 to 0.549 for modality-specific representations, consistent with their learning objectives. PCA also reveals residual modality-related structure in shared features; high-dimensional consistency does not require complete overlap in a two-dimensional projection. Together with the ablations in Table 3, these observations support the connection between representation organization and detection performance, although similarity alone does not establish a strict semantic decomposition. Complete weather distributions, projection details, and similarity distributions are provided in Appendix E.

> **Figure 3 placement.** Combine the existing PCA plots with original-space similarity statistics. The numerical analysis is complete; the composite figure is pending.

**Spatial gating.** Figure 4 presents one real scene from each of seven weather groups: normal, overcast, fog, rain, sleet, light snow, and heavy snow. Each example includes a camera reference, LiDAR BEV, the predicted foreground gate, and the same gate with GT references. Gates are predicted directly from multimodal representations and supervised by GT-derived labels during training; inference requires neither GT nor previously detected boxes. The two heatmaps are numerically identical, with green dashed boxes overlaid after prediction and GT also used for subsequent regional statistics. Mean foreground gate values range from 0.282 to 0.371 across these selected frames, compared with background means of 0.108–0.121. Object locations exhibit locally higher responses, alongside weakly responding objects and responses outside the boxes. All panels use complete spatial grids and a common color scale without smoothing. These values describe selected examples rather than aggregate weather-specific statistics; selection criteria and individual values are provided in Appendix E.

> **Figure 4 placement.** The seven-weather figure and separate per-weather PDFs are available. If the main figure is reduced to three or four examples, move the complete version to the appendix and revise the paragraph accordingly.

**Detection visualization.** Figure 5 compares the released ASF checkpoint and ObjDec on identical test frames, using the same inputs, detection postprocessing, and display confidence threshold of 0.3. We show camera projections, complete BEV views, and matched detail windows. In the normal-weather example, the maximum 3D IoU for the displayed distant object increases from 0.572 to 0.719. In the overcast and rainy-night examples, ASF has no retained prediction overlapping the highlighted object at this display threshold, while the corresponding ObjDec predictions achieve 3D IoUs of 0.476 and 0.741. The overcast example does not meet an IoU threshold of 0.5. These observations are specific to the selected scenes; Appendix E retains all candidates and examples with poorer localization, without inferring aggregate gains from individual frames.

> **Figure 5 placement.** A paired-prediction draft is available, with additional snow examples and a counterexample for the appendix. Displayed values are maximum geometric 3D IoUs for selected ground-truth objects, not AP.

### 4.5 Architecture Evaluation on V2X-Radar-V

**Purpose and setup.** We evaluate the applicability of ObjDec on another dataset with three object categories and different sensor combinations. Models are trained on V2X-Radar-V, retaining shared and modality-specific representations, foreground gating, modality contribution control, and object-context modulation, with context derived from Vehicle, Pedestrian, and Cyclist categories. Local experiments use 8,391 training frames, 1,487 deduplicated validation frames, and 1,486 deduplicated test frames within \([0,102.4)\times[-51.2,51.2)\times[-5,3)\) m. All local runs use 0.16 m grids, an 80-epoch budget, and an effective batch size of 8.

**Representative methods and comparison groups.** Table 4(a) provides published reference results for PointPillars, CenterPoint, PV-RCNN, SQDNet, BEVDepth, and RPFA-Net, covering LiDAR, camera, and radar detection [V2X-Radar]. These results use the original paper's validation protocol, which differs from our local data version, splits, and evaluation region; no ranking or gain is computed across panels. Table 4(b) focuses on locally trained fusion methods. The C+L+R group compares ASF-style and ObjDec using common encoders and detection heads, 2×2 patches, and four queries. The L+R group compares separately trained L4DR and ObjDec-LR with their respective native networks. ASF-style is a local adaptation without SCL.

**Matched-modality detection results.** Table 4(b) reports final test results for checkpoints selected by validation mean 3D AP. With L+R inputs, ObjDec-LR achieves mean 3D and BEV AP of 79.65% and 83.81%, exceeding L4DR by 1.41 and 1.25 percentage points. Vehicle, Pedestrian, and Cyclist 3D AP improve by 0.71, 1.58, and 1.93 points, respectively, with improvements in BEV AP for all three classes. With C+L+R inputs, ObjDec achieves mean 3D and BEV AP of 81.38% and 86.27%, exceeding ASF-style by 0.08 and 0.55 points. The mean 3D difference is small; gains are concentrated in Cyclist and BEV metrics, while Vehicle and Pedestrian 3D AP remain lower by 0.47 and 0.24 points. These matched-modality results support the applicability of ObjDec to another dataset and different input combinations. The L+R comparison retains native network differences, so its gains cannot be attributed solely to an individual fusion component. Appendices G.1–G.3 retain the Concat control on the common backbone, class-wise BEV scores, spatial-granularity analyses, and best/last-checkpoint results. Appendix G.4 provides the supplementary VoD experiments.

> **Editorial record; remove before submission.** Table 4(b) was completed on September 23, 2026. ObjDec, ASF-style, L4DR, and ObjDec-LR use validation-selected epochs 70, 80, 80, and 75, respectively; all best/last test evaluations are complete. This section evaluates applicability after training on the target dataset, without claiming zero-shot transfer or state-of-the-art performance on the published benchmark.

## 三、正文表格初稿：中英文共用

所有AP均以百分数报告，增益以百分点表示。显示值保留两位小数，差值先由未舍入结果计算。`—`表示来源未报告该项；`Pending`表示本轮比较尚无最终结果。表中不将不同协议的全部行统一加粗排名。

### Table 1. K-Radar v1主结果 / Main K-Radar v1 results

| Method | Sensors | Source | AP3D@0.3 | AP3D@0.5 | APBEV@0.3 | APBEV@0.5 |
|---|---|---|---:|---:|---:|---:|
| RTNH | R | Reported | 37.40 | 14.10 | 41.10 | 36.00 |
| RTNH | L | Reported | 72.70 | 37.80 | 76.50 | 66.30 |
| 3D-LRF | L+R | Reported | 74.80 | 45.20 | 84.00 | 73.60 |
| L4DR | L+R | Public log | 77.96 | 53.50 | 79.49 | 77.54 |
| DLRFusion | L+R | Reported | 74.80 | 45.70 | 82.90 | 73.20 |
| RAF on L4DR | C+L+R | Reported | — | 57.40 | — | 82.00 |
| AW-MoE | L+R | Reported | 83.90 | 61.50 | 88.20 | 84.20 |
| AW-MoE-LRC | C+L+R | Reported | 84.30 | 61.80 | — | — |
| ASF | C+L+R | Released checkpoint archive | 80.31 | 67.19 | 80.78 | 80.33 |
| ASF | C+L+R | Local retraining | 88.57 | 67.49 | 89.01 | 80.36 |
| ObjDec | C+L+R | Ours | 88.36 | 67.50 | 88.84 | 88.10 |

**中文图注。** K-Radar Sedan窄范围设置的检测比较。C、L、R分别表示相机、LiDAR和四维雷达。最后三行使用本项目v1标签与conf=0.3口径；官方ASF行来自其权重对应的结果归档，本地重训另列。其他行保留原文或公共日志的设置，不表示全部经过统一标签、预处理与评测器复现。文献行与本地行在正式排版中分组。

**English caption.** Detection results for the K-Radar Sedan narrow-region setting. C, L, and R denote camera, LiDAR, and 4D radar. The final three rows use the project's v1 labels and a confidence filter of 0.3. The released ASF result is taken from the checkpoint-associated archive, with local retraining reported separately. Other rows retain their published or public-log settings and are not uniformly reproduced under identical labels, preprocessing, and evaluators. Published references and project-protocol results are separated into groups in the final layout.

**来源备注。** 本地三行读取未舍入JSON；3D-LRF、RTNH、AW-MoE行沿用已归档主表及文献索引；L4DR使用公共日志精度，不混用78.00等文献舍入值；DLRFusion和RAF来自9月17日的原文核查表。正式排版为各文献行补作者–年份引用。DLRFusion使用Doppler，当前v1 ObjDec不使用该字段。不要为追求单一排名将Reported行改称同协议本地复现。

### Table 2. K-Radar v2扩展设置 / Extended K-Radar v2 evaluation

| Method | Sensors | Training / source | Mean AP3D@0.3 | Mean AP3D@0.5 | Mean AP3D@0.7 | Mean APBEV@0.5 |
|---|---|---|---:|---:|---:|---:|
| ASF | C+L+R | Released-result archive | 66.55 | 41.57 | 9.89 | 62.45 |
| L4DR | L+R | Released checkpoint, aligned evaluation | 69.48 | 48.23 | 10.86 | 65.23 |
| ASF | C+L+R | Local, 11 epochs | 64.77 | 39.70 | 9.55 | 58.77 |
| L4DR | L+R | Local, 11 epochs | 65.53 | 43.84 | 9.82 | 60.73 |
| DecControlled Strong | C+L+R | Ours, 11 epochs | 66.91 | 43.05 | 11.11 | 60.93 |

**中文图注。** K-Radar v2双类别结果，Mean为Sedan与Bus/Truck的等权平均。全部行采用对齐后的v2.0标签、revised evaluator和conf=0.3口径。官方来源与11轮本地训练分组。ASF和Strong使用相同预训练编码器；本地L4DR从头训练，其模态、结构和预训练成本不同。Strong为不含object context的解耦控制变体。完整逐类与BEV结果见附录C。

**English caption.** Results on the two-class K-Radar v2 setting. Mean averages Sedan and Bus/Truck equally. All rows use the aligned v2.0 labels, revised evaluator, and confidence filter of 0.3. Released-model references are grouped separately from 11-epoch local runs. ASF and Strong share pretrained encoders, whereas local L4DR is trained from scratch with different modalities, architecture, and pretraining cost. Strong is a decoupled-control variant without object context. Complete class-wise and BEV results are provided in Appendix C.

### Table 3. 组件消融 / Component ablations

| Variant | AP3D@0.3 | AP3D@0.5 | APBEV@0.5 |
|---|---:|---:|---:|
| Full ObjDec | **88.36** | **67.50** | **88.10** |
| w/o modality contribution control | 79.62 | 64.38 | 79.91 |
| w/o object context | 80.14 | 66.23 | 79.96 |
| w/o decoupling supervision | 80.23 | 66.16 | 80.04 |
| w/o foreground gating | 80.00 | 64.80 | 80.12 |

**中文图注。** K-Radar v1、C+L+R、conf=0.3下的组件消融。各版本经过1,000样本预评测选择checkpoint，再进行全量评测。去解耦监督仍保留共享／特有分支；去目标上下文同时关闭对应监督与query/output注入；去前景门控将gate固定为1并关闭其监督。附录B、D提供选模与实现细节〔待补：选模记录〕。

**English caption.** Component ablations on K-Radar v1 with C+L+R and a confidence filter of 0.3. Each variant undergoes checkpoint selection through a preliminary 1,000-sample evaluation before full-set evaluation. Removing decoupling supervision retains the shared and modality-specific branches. Removing object context disables its supervision and both query/output injections. Removing foreground gating fixes the gate to one and disables its supervision. Selection and implementation details are provided in Appendices B and D [TO COMPLETE: selection records].

### Table 4. V2X-Radar-V：公开参考与本地融合对照 / Published references and local fusion comparisons

**(a) 公开结果参考：原论文validation协议，与(b)不直接比较 / Published validation references; not directly comparable to (b)**

| Method | Sensors | Vehicle 3D | Pedestrian 3D | Cyclist 3D | Mean 3D |
|---|---|---:|---:|---:|---:|
| PointPillars | L | 68.80 | 38.16 | 65.24 | 57.40 |
| CenterPoint | L | 72.19 | 50.59 | 75.26 | 66.01 |
| PV-RCNN | L | 79.38 | 58.83 | 78.01 | 72.07 |
| SQDNet | L | 79.65 | 58.79 | 79.46 | 72.63 |
| BEVDepth | C | 15.47 | 8.51 | 9.46 | 11.15 |
| RPFA-Net | R | 30.44 | 10.37 | 11.98 | 17.60 |

**(b) 本地统一协议：去重test、0.16m、80轮预算、val选模 / Local protocol: deduplicated test, 0.16 m, 80 epochs, validation selection**

| Method | Sensors | Vehicle 3D | Pedestrian 3D | Cyclist 3D | Mean 3D | Mean BEV |
|---|---|---:|---:|---:|---:|---:|
| ASF-style | C+L+R | 84.54 | 76.17 | 83.18 | 81.30 | 85.72 |
| ObjDec | C+L+R | 84.06 | 75.94 | 84.13 | 81.38 | 86.27 |
| L4DR | L+R | 83.17 | 73.25 | 78.31 | 78.24 | 82.56 |
| ObjDec-LR | L+R | 83.87 | 74.84 | 80.24 | 79.65 | 83.81 |

**中文图注。** 两个面板均提取Moderate难度、Vehicle/Pedestrian/Cyclist的严格IoU 0.7/0.5/0.5结果，Mean为三类算术平均。(a)取自V2X-Radar正式论文表4，由数据集作者报告，未在本地复现；其Mean由公开逐类数值计算，原表斜杠表示严格／宽松IoU，不是3D／BEV。(b)报告本地AP\(_{R40}\)，前两行为共同编码器与检测头上的三模态对照，后两行为独立训练的L+R架构对照；ASF-style为no-SCL适配。两个面板的数据版本、划分、报告集合与ROI不同，不跨面板加粗排名或计算增益。(b)四行权重依次由val选中第80、70、80、75轮。Concat受控基线和完整BEV/best/last结果见附录G.1/G.2。

**English caption.** Both panels use Moderate difficulty and strict class IoUs of 0.7/0.5/0.5; Mean is the arithmetic class average. Panel (a) reproduces selected results from Table 4 of the V2X-Radar paper, reported by the dataset authors without local reproduction. Its means are calculated from published class scores; slash-separated entries in the source denote strict/loose IoUs, not 3D/BEV. Panel (b) reports local AP\(_{R40}\), comparing three-sensor fusion with common encoders and detection heads, and separately trained L+R architectures. ASF-style omits SCL. Data versions, splits, reporting sets, and ROIs differ across panels, precluding a combined ranking or cross-panel gains. Panel (b) uses validation-selected epochs 80, 70, 80, and 75, respectively. The Concat control and complete BEV/best/last results are retained in Appendices G.1/G.2.

**来源备注，提交时转为正式引用。** (a)已于2026-09-23重新核对[NeurIPS 2025 V2X-Radar正式论文表4](https://papers.nips.cc/paper_files/paper/2025/file/a501f3238029713afdad57ce7924667a-Paper-Datasets_and_Benchmarks_Track.pdf)。(b)来自各运行目录的`final_best.json / results.test_deduplicated`。M2-Fusion的公开结果属于恶劣天气子集及不同IoU；PhD-DETR的完整车端结果尚未核实，因此不填入这两个面板。完整纳入规则见[本轮整理记录](objdec_v2x_paper_comparison_260923.md)。

## 四、附录衔接与投稿前待办（编辑备注，不进入正文）

2026-09-20：已完成[附录中英文初稿](objdec_appendix_bilingual_initial_260920.md)，与本章互补；[来源及待补说明](objdec_appendix_source_notes_260920.md)记录数值来源和未完成项。[原提纲](objdec_appendix_writing_plan_260920.md)保留。下方旧进度备注仅代表原稿核查时点，当前最终结果以表4及附录G为准。

2026-09-22：正文跨数据集验证集中于V2X-Radar-V；VoD已补入附录G.4，包含表G.3a/G.3b的官方EAA/DC及表G.4的补充KITTI指标。正文4.5仅保留交叉引用。

2026-09-23：表4重组为(a)六种公开代表方法的背景参考、(b)ASF-style/ObjDec及L4DR/ObjDec-LR两组本地同模态对照；Concat从正文主表移至附录G.1/G.2的受控比较，保留完整证据。中英文4.5同步改写，未改变原始数值、选模规则或训练设置。

### 4.1 附录内容与正文引用对应

| 附录 | 应补入的已有材料 | 正文引用位置 |
|---|---|---|
| A 实现细节 | 方法初稿末尾的网络尺寸、前景目标、损失、SCL路径；训练配置 | 4.1 |
| B 协议与选模 | v1/v2标签、ROI、AP计算、score预过滤和NMS；v1选模记录；V2X去重和val选best | 4.1、表1–3 |
| C 完整K-Radar结果 | 全部IoU/BEV、v1 conf=0.0、v2逐类与完整七天气、昼夜 | 4.2 |
| D 额外消融 | 各关闭项的实际干预、正文未列的严格3D与BEV指标；配置敏感性待核查后再决定 | 4.3 |
| E 表征与可视化 | 全天气PCA、余弦分布、质心变化、七天气gate、成对检测候选及反例 | 4.4 |
| F 可用性与损坏 | v1/v2十种输入设置、固定权重、两档conf；明确本地C*/L*规则 | 4.2 |
| G 跨数据集架构适配 | G.1–G.3：V2X数据版本、去重、ROI、合类、网格与patch/query、完整结果及曲线；G.4：VoD训练适配、EAA/DC与锚框取舍 | 4.5 |
| H 效率与限制 | 完整配对测速、抽样数值差异与退出异常、单种子及适用范围 | 4.3 |

### 4.2 当前不能当作定稿的事项

1. **选模来源。** 作者已说明完整与移除版本都做过1,000样本小测；具体ID、指标、候选checkpoint、是否使用测试划分仍待记录。正文因此不称它为独立validation。若来自测试集，应据实修改协议描述和结果解释。
2. **图3。** 全量统计已经完成，但原有局部patch PCA与当前帧均值PCA不同；本初稿按全量帧均值版本撰写。最终若换图，统计单位和图注一起修改。不能根据独立PCA空间的距离比声称对齐提高若干倍。
3. **图4、5。** 七天气gate与三场景检测对照初稿已完成；定稿需决定正文选例数、图内字号和附录重排。Fig.5基于官方ASF权重的本地20帧推理，输入与检测配置已核对，不能称为新的全量AP评测。两次推理在完整导出后触发历史native退出错误，独立文件及数值核查通过，详细记录保留在图稿目录。
4. **V2X。** 核查约20:03时，ObjDec CLR完成26轮、Concat完成75轮且在验证、ASF-style及ObjDec-LR各完成7轮。四组均没有final_best.json；L4DR已完成。正式表按统一规则填最终test，不填本轮次的val，不拼接各轮最高类别分数。
5. **效率。** 100个不同计时帧、两轮重复；FP32张量且原环境TF32开启。新计时含解码/NMS与原路径GT recall统计，不含读盘。CUDA Graph路径未做全量AP复核；四次测速在结果写盘后均有native退出异常，原版profile也有同类现象。相关情况应保留于附录H，不能写成已完成稳定部署或精度完全无损。
6. **结果定位。** v1对官方权重的较大数值差距依赖阈值与checkpoint，已在正文保留本地重训与conf=0.0参照。v2 Strong不包含完整上下文路径。当前单种子和选模结果不提供统计显著性结论。
7. **文献与图表。** 本稿引用占位需接入正式BibTeX；表1的不同来源设置、表2的初始化差异应在正文表注可见。旧0.4m结果保留在附录G.1，VoD已纳入G.4，二者不用于预告V2X新0.16m成绩。

### 4.3 数值与素材来源

| 材料 | 直接来源 |
|---|---|
| ObjDec v1原始AP | [summary_conf0.3.json](exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.json)；[conf0.0](exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.0.json) |
| 官方ASF v1原始AP | [官方权重结果归档](/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.json)；[阈值审计](asf_v1_conf_protocol_audit_260828.md) |
| 本地ASF v1 | [summary_conf0.3.json](exp_260818_202519_ASF_v1_0_local_repro_model2_full/summary_conf0.3.json) |
| 表1文献行 | [已有主表](paper_main_table_kradar_v1_conf0_3_draft_260901.md)、[公共日志精度](v1_conf0_3_main_protocol_260819.md)、[近期原文核查](taskdec_recent_literature_and_comparability_260917.md) |
| v2各来源原始精度 | [五来源完整CSV](../analysis_exports/v2_matched_training_260915/reporting_strategy_260916/five_sources_full_metrics.csv)、[训练及协议](taskdec_v2_matched_training_260915.md) |
| 四项消融 | [消融结果与各日志路径](taskdec_v1_component_ablation_conf0_3_260901.md) |
| 全量表征 | [weather_statistics.csv](../analysis_exports/objdec_fulltest_weather_260919/weather_statistics.csv)、[统计口径与图稿](objdec_fulltest_weather_visualization_review_260919.md) |
| 空间gate | [历史两帧图与核查说明](../analysis_exports/taskdec_bev_gate_fig4_260910/README.md) |
| 七天气gate与检测对照 | [图稿、选帧和中英文图注](../analysis_exports/objdec_fig4_fig5_260919/README.md)、[输入与文件核查](../analysis_exports/objdec_fig4_fig5_260919/validation.json) |
| 缺模态 | [v1完整与早期组合](paper_availability_missing_modalities_260902.md)、[v1补测](taskdec_experiment_results_260918.md)、[v2十组](taskdec_v2_availability_vs_asf_table3_260918.md) |
| 效率 | [comparison_summary.json](../analysis_exports/inference_optimization_260917/comparison_summary.json)、[协议与运行边界](taskdec_inference_optimization_260917.md) |
| V2X配置与最终L4DR | [新对照配置](objdec_v2x_asf_lr_grid016_launch_260919.md)、[L4DR final_best.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/final_best.json) |
| VoD附录结果 | [当前EAA/DC及KITTI表、原始结果入口](objdec_vod_current_tables_260922.md)、[2×2及局部编码设置](objdec_vod_patch2_local_launch_260921.md)、[训练集锚框适配设置](objdec_vod_adapted_anchors_launch_260921.md) |

本稿的主结果差值由原始精度计算：v1对官方ASF为+8.04 AP3D@0.3、+7.77 APBEV@0.5；对本地ASF为−0.22 AP3D@0.3、+7.73 APBEV@0.5；v2对本地ASF为+2.14/+3.36/+1.56 Mean AP3D@0.3/@0.5/@0.7。不要用先四舍五入的显示值重新计算并覆盖这些差值。

2026-09-23上午补齐：ASF-style与ObjDec-LR最终best/last已完成，正文4.5中英文、表4(b)、附录G.1/G.2及相关说明已同步。所有主表行采用val选中的权重；前面的待完成记录仅描述较早时点。
