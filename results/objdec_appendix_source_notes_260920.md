# ObjDec附录：来源、正文衔接与待补记录

日期：2026-09-20。本文件供作者核对，不进入匿名论文正文。

2026-09-22更新：正文保留V2X-Radar-V主对照，VoD完整补充结果已纳入附录G.4与表G.3a/G.3b、G.4。

附录稿：[中英文A–H及共用图表](objdec_appendix_bilingual_initial_260920.md)。本轮只整理已有文件，未启动训练、推理、GPU评测或复制checkpoint；附图引用现有PDF。

## 1. 与正文的补充关系

| 位置 | 本稿实际增加的内容 | 与正文的分工 |
| --- | --- | --- |
| A | 分支尺寸、变体配置、旋转框patch中心标签、损失归一化、SCL实际路径、伪代码 | 补复现信息；正文保留架构动机与主要前向公式 |
| B | AP采样、z-center、score/NMS、固定预测交叉检查、选模与来源 | 解释可比性；影响主结论的条件仍须在主表可见 |
| C | v1另一档conf和严格IoU、v2逐类3D/BEV、完整天气 | 从紧凑主表展开；保留少量主指标作核对锚点 |
| D | 四项移除到底关闭哪些路径、3D@0.7和BEV@0.3/@0.7 | 不复制主表已有的3D@0.3/@0.5与BEV@0.5 |
| E | 帧均值与匹配patch余弦定义、加权PCA、模态对分布、七个gate帧统计、反例和全部候选 | 补统计口径、变异与选例范围；不重复整张正文gate图 |
| F | 两版本十种输入、两档conf、移除与损坏的具体定义 | 补正文只讨论的少数组合；v1 LR/conf0.0尚为NR |
| G | V2X本地数据链路、共同底座、旧0.4m/patch对照、best与last；VoD完整EAA/DC、锚框适配及KITTI补充指标 | 正文保留V2X主对照；VoD提供另一底座上的补充适配证据 |
| H | 计时分布、边界、数值核查和适用范围 | 不重复参数量主结论；不把Graph抽样核查当全量AP复核 |

实际包含21个表格块（C.4a/b、G.3a/b分别为各自表格的两个面板）、1段算法，以及4组已有附图的中英文图注；Figure G.1完整训练曲线为待补。图E.4是五页候选图册，最终可单独放匿名补充材料。英文与中文按同一节序组织，数值表维护一套。

## 2. 数值来源与可重复汇表

[汇表脚本](../analysis_exports/objdec_appendix_draft_260920/make_tables.py)读取已有JSON/CSV和已核查归档，输出[共用数值表](../analysis_exports/objdec_appendix_draft_260920/generated_tables.md)及[来源SHA-256清单](../analysis_exports/objdec_appendix_draft_260920/sources.json)。当前清单记录36份源文件；包含VoD表的来源报告、两组原始metrics.json及kitti.txt，以及V2X三模态ObjDec、ASF-style和ObjDec-LR的final_best/final_last.json。脚本不跑模型，也不改源结果。

从项目根目录运行：

```bash
python analysis_exports/objdec_appendix_draft_260920/make_tables.py
```

重新生成只更新独立数值表和清单，**不会自动覆盖已编辑的附录稿**；需核对后同步。显示值统一从原始精度舍入，AP差值先由原始数值计算，因此可能不等于两个已舍入单元格相减的结果。v1 LR/conf0.3例外：目前可核查来源仅保留两位小数，表注已写明。

| 材料 | 对应来源 |
| --- | --- |
| 网络与损失 | [v1配置](../configs/ASF_task_dec_controlled_robust_v1_0.yml)、[v1基配置](../configs/v1_0/cfg_A2F_scl_final.yml)、[Strong配置](../configs/ASF_dec_controlled_strong.yml)、[融合实现](../models/fuser/patch_dec_a2_fusion.py) |
| V2X网络与训练 | [模型代码](../v2x_taskdec/model.py)、[0.16m锁定配置](../analysis_exports/v2x_grid016_260918/matched_80ep/config.json)、[协议核查](objdec_v2x_public_protocol_comparability_260919.md) |
| v2固定预测检查表B.2 | [统一评测归档](taskdec_v2_l4dr_aligned_evaluation_260915.md)中“评测器差异”交叉表；不是本轮新实验 |
| v1/v2完整AP | 原始JSON路径见SHA清单；[v2五来源CSV](../analysis_exports/v2_matched_training_260915/reporting_strategy_260916/five_sources_full_metrics.csv) |
| 四项消融 | [完成结果归档](taskdec_v1_component_ablation_conf0_3_260901.md)；完整模型使用与表C.1一致的JSON |
| PCA与高维相似度 | [全量天气目录](../analysis_exports/objdec_fulltest_weather_260919/)、[图稿manifest](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/manifest.json)、[提取与加权PCA脚本](../tools/analysis/export_objdec_full_weather_means_260919.py)、[绘图脚本](../tools/analysis/plot_objdec_fulltest_weather_260919.py) |
| Gate与检测选例 | [图稿说明](../analysis_exports/objdec_fig4_fig5_260919/README.md)、[七帧gate统计](../analysis_exports/objdec_fig4_fig5_260919/fig4_selection.json)、[20帧成对几何结果](../analysis_exports/objdec_fig4_fig5_260919/fig5_candidate_metrics.json) |
| 传感器可用性 | [v1完成结果](../analysis_exports/taskdec_v1_availability_completion_260918/results.json)、[v2完成结果](../analysis_exports/taskdec_v2_availability_completion_260918/results.json)、[历史LR重算核查](full_eval_metric_audit_260821.md) |
| V2X最终结果 | 各组final_best.json/final_last.json路径见SHA清单，固定按dedup val选best、报告dedup test |
| VoD完整结果 | [核查后的EAA/DC表及历史来源](objdec_vod_current_tables_260922.md)；[2×2/局部编码第75轮JSON](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075/metrics.json)、[适配锚框第80轮JSON](../analysis_exports/objdec_vod_adapted_anchors_260921/validation/epoch_080/metrics.json)，近期两行与JSON逐值断言一致 |
| VoD KITTI及配置 | 同目录kitti.txt中明确标记的3D/BEV IoU=0.5/0.25/0.25 AP_R40段落；[局部编码配置说明](objdec_vod_patch2_local_launch_260921.md)、[训练集锚框适配说明](objdec_vod_adapted_anchors_launch_260921.md) |
| VoD文献行 | [L4DR AAAI 2025正式论文表3](https://ojs.aaai.org/index.php/AAAI/article/view/32397/34552)，含InterFusion与L4DR；三类公开值算术平均得到文献mAP |
| 效率 | [测速核查报告](taskdec_inference_optimization_260917.md)、[配对汇总JSON](../analysis_exports/inference_optimization_260917/comparison_summary.json) |

## 3. 需要保留的身份与数值区别

1. **v1完整ObjDec、v2 Strong、V2X ObjDec不是同一配置。** Strong没有object context；V2X采用三类前景CE、不同编码器、patch/query配置且关闭SCL。正文和附录已经分别表述。
2. **ASF官方归档与新推理分开。** AP表使用的ASF权重对应归档，不等于本轮全量重评；Fig.5确实另有20帧同输入的本地成对推理。
3. **conf=0.0仍有head score预过滤。** v1 legacy是11点汇总；v2 revised是41点均值，不能都简称KITTI R40。L4DR对齐包含生效NMS修改。
4. **22.02与22.04按来源区分。** 正式ObjDec的v1/conf0.3原始3D@0.7为22.04；conf0.0为22.02。不同报告中的旧值未混入同一表。
5. **PCA与余弦的统计对象不同。** PCA点是帧内前景均值；高维余弦先在对应patch求值，再按帧汇总。七帧gate是定性例子，不冒充全测试天气均值。
6. **best不由test选择。** Concat 0.16m为val选中的epoch75（test mean3D=81.90）；epoch80 test=81.97另列，不能据此替换best。
7. **VoD的EAA/DC都是3D指标。** 近期两组均80轮、每5轮验证并按EAA选模；第75轮与第80轮分别对应两个版本，不能将不同轮次的EAA/DC最优值拼接。表G.4另用KITTI难度过滤和AP_R40；JSON通用KITTI字段记录的是更严格IoU，汇表脚本明确解析kitti.txt的0.5/0.25/0.25段落。
8. **VoD历史对照不是完全匹配预算。** 旧Concat的AMP／实际batch、旧ObjDec的warm-start、本地L4DR的100轮与SyncBN均在G.4披露。新锚框EAA高于本地L4DR但DC更低，也未超过其论文总体结果；不以“只保留EAA”声称总体最优。

## 4. 投稿前待补，未写成已完成

| 优先级 | 缺项 | 当前处理 |
| --- | --- | --- |
| 必需 | v1的1,000样本来源、ID/生成规则、候选checkpoint范围、选择指标及并列规则 | 中英文B.2保留明确待补，不称独立验证集 |
| 已完成（9月23日） | 0.16m五组最终best/last | 已补齐正文表4(b)及附录G.1/G.2；全部按val选模，未用test改选权重 |
| 待制图 | 完整80轮验证曲线 | 五组验证记录已齐全；Figure G.1仍为布局和图注草案，数值表已完整 |
| 核查后决定 | v1 LR/conf0.0结果 | F.1为NR。可核查已有保存预测及汇总，不为补表擅自启动推理 |
| 正式排版 | [ASF]、[V2X-Radar]等引用、交叉引用、数学符号与图表字号 | 接入BibTeX及LaTeX后统一；本稿未编译PDF |
| 正式排版 | 21个表格块及七天气PCA较长 | C.4、G.3分面板，E.1拆续图，E.4可作单独匿名候选图册；不把所有表硬塞一页 |

控制强度0.5/1.0、gate bias等仍为**可选分析**。本轮没有把尚未完整核查训练/初始化/选模对应关系的配置敏感性表写入论文，正文对“控制强度分析”的预告同步收窄为已落实的干预细节与补充指标。无需为了满足旧提纲而声称完成了未核实实验。

CUDA Graph尚无全测试集AP复核；H节已说明抽样张量一致性、计时范围及退出异常。单种子结果不加统计显著性或误差条。完整天气和缺模态中的下降、低相机单路成绩以及Fig.E.3反例均保留，避免把局部正向结果写成普遍成立。

## 5. 本轮同步修改范围

- 新建附录中英文稿、此来源说明、数值汇表脚本及两个小型输出文件。
- 给原附录提纲增加初稿入口。
- 实验初稿增加附录入口，将未落实的控制强度分析预告改为已完成的补充指标与干预细节。
- 用现有最终文件补入正文表4的Concat 0.16m一行，和附录G保持一致；其余未完成行仍Pending。
- 方法正文、已完成的训练配置、checkpoint、预测和原始图像保持原状。

2026-09-22增补：新增G.4中英文VoD小节与三块数值表，同步正文4.5引用、附录提纲及汇表脚本；保留全部EAA/DC类别值、KITTI指标与锚框适配的回退。未启动新实验。

2026-09-23增补：从原始final_best/final_last.json补入0.16m三模态ObjDec的最终test结果；更新正文表4、附录G.1/G.2及中英文对应段落。主表仍使用val选中的第70轮，末轮80只作补充。另存[当前总表](objdec_v2x_current_total_table_260923.md)与原始精度CSV，ASF-style、ObjDec-LR仍待最终测试。未启动新实验。

2026-09-23章节重组：正文表4增加六种公开代表方法作为独立参考面板，本地面板聚焦ASF-style/ObjDec与L4DR/ObjDec-LR。Concat从正文表移入附录受控比较，G.1/G.2的数字及来源保持完整；G.3中英文明确其与ObjDec的差值。公开面板按原数据集论文表4核查，不纳入本地JSON汇表脚本；来源、纳入规则及本轮修改清单见[整理记录](objdec_v2x_paper_comparison_260923.md)。

2026-09-23上午补齐：ASF-style与ObjDec-LR最终best/last已完成，正文4.5中英文、表4(b)、附录G.1/G.2及相关说明已同步。所有主表行采用val选中的权重；前面的待完成记录仅描述较早时点。
