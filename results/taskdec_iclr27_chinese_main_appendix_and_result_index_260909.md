# TaskDec ICLR 2027 中文写作组织与实验索引

2026-09-17 全文梳理更新：已汇总 [现有结果、动机与三项贡献](taskdec_full_paper_evidence_motivation_contributions_260917.md)，纳入已完成的 v2 本地 ASF/L4DR、V2X 三组最终测试及 2×2 同轮进展。主线建议为“共享/特有状态驱动目标相关的局部融合”，天气承担条件分析。v1 对官方 ASF 的 AP3D@0.3 增益按原始精度为 **+8.04**（旧稿 +8.05 为舍入后相减）；v2 Strong 相对同日程 ASF 为 +2.14/+3.36（@0.3/@0.5）。V2X 原版低于 Concat，小 patch 尚未完成，不预写跨数据集领先。下方早期进度与图表建议作为历史记录保留，当前结果身份及写作边界优先参照新总稿。

2026-09-15 截稿前外部数据集核查：nuScenes 完整 trainval 压缩包实测合计 314.887 GB（293.261 GiB），关键帧版 45.364 GB；V2X-Radar-V 压缩 23.926 GB、ZIP 内文件合计 36.356 GB，当前公开划分为 8,391 / 1,498 / 1,501，与论文中的 7,000 / 1,500 / 1,500 不同。本机空间足够；nuScenes 原始 BEVFusion 有可访问初始化与 6 轮融合阶段，但实际接入和吞吐尚未验证。建议在只剩约 9 天的情况下选一条路线、9 月 17 日前完成工程可行性判断。详见 [体量、代码就绪程度与截稿排期](taskdec_nuscenes_v2x_size_and_deadline_feasibility_260915.md)。仅下载小型公开元数据，未新增训练。

2026-09-15 架构定位澄清：作者希望保持 TaskDec 的架构贡献。nuScenes 如继续推进，应复用成熟编码器和检测接口、迁移完整 TaskDec 主融合路径；不以 BEVFusion 前后的小型 gate 插件替代完整架构验证。已核对 ASF / 3D-LRF / L4DR 的公开实验范围，未发现证据将其缺少 nuScenes 结果归因于未公开的性能失败。详见 [实验范围与架构迁移边界](taskdec_nuscenes_scope_and_architecture_260915.md)。此项仍为研究设计。

2026-09-15 外部数据集建议：针对仅 K-Radar 难以充分支撑通用融合机制、现有 VoD 收益较小的问题，已核查 Dual-Radar、V2X-Radar-V、nuScenes 等官方资料。建议优先评估 Dual-Radar 的跨雷达配置验证或公开约 23.9 GB 的 V2X-Radar-V 单车端数据，见 [候选、获取条件与实验设计](taskdec_external_dataset_options_260915.md)。当前仅完成资料分析，未下载或启动新实验；不预设新数据集会有更大 AP 增益。

2026-09-15 动机梳理建议：将文章主线集中为“利用共享与特有表征，指导目标相关的局部融合”；天气作为条件分析，缺模态作为压力测试，v2 Strong 作为 Dec 家族的设置扩展。已整理与 WCBR 的差别、三段中文引言草稿、方法术语边界及现有证据用途，见 [动机与证据组织建议](taskdec_motivation_and_evidence_organization_260915.md)。该建议待作者定稿；不将 PCA、gate 或单一协议的性能差值写成完整因果证明。

2026-09-15 本地训练对照：作者选择按 Strong 的同训练集、11 轮和有效 batch=2 对齐，另记录实际单卡训练耗时。已启动 ASF（GPU2）与 L4DR（GPU3），各 79,123 次更新，末轮自动在相同 v2.0 GT / revised evaluator 下导出总表和完整分天气结果。ASF 使用 Strong 同组官方预训练编码器并训练新的 A2Fusion / head；L4DR 原生网络从头训练。这里对齐的是样本与更新预算，预训练成本和 GPU 小时并不相等。新结果完成前不替代下方官方参考。见 [本地复现进度与结果](taskdec_v2_matched_training_260915.md)。

2026-09-15 L4DR v2 统一评测：本次已完成 L4DR 双类别官方权重在 **v2.0、13,727 帧、与 Strong 完全相同 GT 和 revised evaluator** 下的全量评测。两类平均 AP3D@0.3 / @0.5：L4DR 为 69.48 / 48.23，Strong 为 66.91 / 43.05；Strong 相对 L4DR 的差值为 **-2.57 / -5.18 AP 点**。 详见 [统一评测结果与天气对照](taskdec_v2_l4dr_aligned_evaluation_260915.md)。ASF 保留官方归档，本次未逐帧复算。

日期：2026-09-09

用途：给后续专门写论文的新窗口使用。本文档把 ICLR 2027 页数要求、正文叙事、图表取舍、附录安排，以及所有已提到实验在本地目录中的位置统一整理出来。

2026-09-12 天气/Total 与协议复核：按作者最新要求，[v2 附录天气表](paper_kradar_v2_weather_l4dr_table10_260912.md) 和 [LaTeX](paper_kradar_v2_weather_l4dr_table10_260912.tex) 已直接加入 L4DR 论文行（†）。Strong 的 Sedan 天气等权平均比 L4DR 高 2.55 点、Total 低 1.22 点；Bus/Truck 天气均值低 0.23 点、Total 低 0.46 点。新发现：v2 Strong/ASF 使用 revised evaluator（41 个 precision 值平均、z_center=0.5），L4DR 当前公开代码使用旧 evaluator（选 11 个值平均、z_center=1.0）；此前仅检查 conf/标签不足以确认完全同协议。两边原始 test split 文件相同，ROI 和主要过滤开关相同，不能笼统归因于标签版本或测试集。v1 主配置未开启 revised，不能将这一 v2 差异直接套到 v1 主表。详见 [完整审计与后续复评设计](taskdec_v2_l4dr_weather_total_and_eval_protocol_audit_260912.md)。本轮没有运行 GPU 任务或改变原始 AP。

2026-09-12 全天气排表：按 Sedan / Bus–Truck 分组、Total 与七种天气横向排列。最新附表 @0.3 面板包含 L4DR、ASF、Strong 共 6 行；@0.5 面板保留 ASF、Strong 共 4 行，原 Total 紧凑表可用于正文。Strong 的 1,445 个 Fog GT 文件确认无 Bus/Truck GT，因此新表该格标为“—”，CSV 保留原日志 0.00；不将此格算作正负收益。L4DR 行明确为文献结果，尚未统一评测器，不作统一协议最优排名。

2026-09-12 最新决定：作者确定 v2 表采用 **DecControlled Strong (ours)**，作为 Dec 方法家族在宽 ROI / 双类别设置下的扩展证据；表注说明不含 task-context 分支，不标成完整 TaskDec 配置。缺模态分析保留 v1，展示完整 CLR/LR/LC/RC 自身对照并交代缺 LiDAR 的退化，已有 ASF 对照可放附录。已导出 [Strong–ASF 完整对照](paper_kradar_v2_decstrong_asf_comparison_260912.md)、[216 组原始精度 CSV](paper_kradar_v2_decstrong_asf_comparison_260912.csv) 和 [正文紧凑表 LaTeX](paper_kradar_v2_decstrong_asf_comparison_260912.tex)，并补充 [v2 文献结果与可比性清单](kradar_v2_literature_candidates_260912.md)。文献涵盖 WRCFormer、REL、L4DR、DPFT、V2X-R/MDD、SRF、DinoRADE 等；REL 的 v2 严格 3D 指标报告值更高，且各文献存在标签/ROI/阈值差异，因此当前 v2 结论为相对官方 ASF 的方法家族扩展收益，不是全面 SOTA。VoD 是否完全撤下仍沿用“倾向撤下、未最终确认”的状态。

2026-09-12 讨论后更新：作者倾向不放 VoD 表，具体取舍尚未最终确定。已完成 [v2.0 现有结果重新核对](taskdec_v2_existing_results_recheck_260912.md)，纳入 8 份全量条件评测及官方 ASF 对照。原推荐的 DecControlled Strong 两类平均 AP3D@0.3 / @0.5 分别为 +0.36 / +1.48；另有此前推荐表未列出的 08-08 TaskDec Robust（含 task context），AP3D@0.5 为 +1.76，但 AP3D@0.3 为 −1.95。不能只根据 08-21 final 的退化概括全部 TaskDec v2 运行。后续表格取舍以该复核为依据；v2 属于同数据集内标签、ROI 与类别设置的扩展，不替代跨数据集证据。

2026-09-12 ASF 参照：[正文与补充材料中的 v2 实验安排](asf_v2_experiment_structure_reference_260912.md)。ASF 用 v1 做主要方法比较与效率表，v2 做同权重的模态组合/损坏输入比较、消融及可视化；附录另有完整指标与天气、注意力统计、相机骨干替换。该记录给出对应表号、来源、TaskDec 可借鉴部分及数值阈值差异。

2026-09-11 汇报材料：[24 页可编辑 PPT](../analysis_exports/taskdec_submission_briefing_260911/TaskDec_现有结果与投稿讨论_260911.pptx)、[PDF 预览](../analysis_exports/taskdec_submission_briefing_260911/TaskDec_现有结果与投稿讨论_260911.pdf)、[逐页讲稿与来源](../analysis_exports/taskdec_submission_briefing_260911/汇报讲稿与来源.md)。前 18 页主讲、后 6 页备份，已纳入完整 BEV gate 初稿、9 月 10 日协议审计及 L4DR VoD 本地复现，供讨论投稿与补证据优先级。

2026-09-10 写作口径更新（依据作者补充）：移除项也经过 1000 样本小测后选择最优对比结果，不能仅凭所选 epoch 不同判断消融不公平；主表采用官方 ASF checkpoint；v2 补充表明确标注不含 task context 的早期 DecControlled 变体；缺模态突出 LR/LC 的正向表现并简述 RC 例外；VoD 突出适配后相对原生强 PP-Concat 基线的 EAA 增益，L4DR 在主基准比较中充分讨论、在 VoD 泛化段一句带过并保留表格行。完整梳理见 [项目与论文复核](taskdec_project_and_paper_review_260909.md)。

## 0. 新窗口交接 Prompt

可以在新窗口第一条消息直接发下面这段：

```text
我现在要写 TaskDec 这篇 ICLR 2027 投稿。项目目录是 /home/hongsheng/dec_con_asf。请先阅读：
1. /home/hongsheng/dec_con_asf/results/taskdec_iclr27_chinese_main_appendix_and_result_index_260909.md
2. /home/hongsheng/dec_con_asf/results/taskdec_robust_paper_writing_advice_260828.md
3. /home/hongsheng/dec_con_asf/results/paper_main_table_kradar_v1_weather_compact_260901.md
4. /home/hongsheng/dec_con_asf/results/taskdec_v1_component_ablation_conf0_3_260901.md
5. /home/hongsheng/dec_con_asf/results/paper_supp_table_kradar_v2_generalization_260901.md
6. /home/hongsheng/dec_con_asf/results/paper_vod_main_table_draft_260909.md

写作目标：把文章包装成一个 task-aware decoupled fusion architecture，而不是 ASF 上的小模块。正文控制在 ICLR 2027 初投稿 9 页以内。主结果是 K-Radar v1.0 Sedan conf_thr=0.3，TaskDec Robust model_0。正文要突出 canonical patch space 中的 common/unique decomposition、foreground gate、sensor reliability control、task context modulation。ASF 作为 canonical patch fusion substrate 和强 baseline 简要介绍，协议争议只放附录，用中性措辞。
```

## 1. ICLR 2027 格式要求

官方要求摘要：

- 初投稿主文正文最多 9 页。
- rebuttal/discussion 和 camera-ready 阶段主文最多 10 页。
- references 不计入页数。
- appendix 可以不限页数，但审稿人不一定读。
- 投稿和 supplementary 都必须匿名。
- AI use statement 是必需项，不计入页数。
- ethics statement 和 reproducibility statement 推荐写，也不计入主文页数。

官方来源：

- ICLR 2027 Author Guidelines: https://iclr.cc/Conferences/2027/AuthorGuidelines

写作含义：

- 正文必须独立讲完整故事，不能指望审稿人去附录里拼结论。
- 按作者最新偏好，正文以 5 张图和 4 个紧凑表规划，实际排版时调整面板和篇幅；完整表、协议审计、超参细节、额外可视化进附录。此前 4–5 个图表块只是内部精简建议，已由第 4 节最新排布替代。

## 2. 文章核心定位

推荐中文 thesis：

> 我们提出 TaskDec，一种任务感知的解耦融合架构。它在统一 canonical patch 空间中，将各模态 patch token 分解为共享目标信息和传感器特有残差信息，并利用该解耦表征预测前景门控、传感器可靠性权重和任务上下文，从而动态调制 patch-level sensor fusion。

推荐英文 thesis：

> We propose TaskDec, a task-aware decoupled fusion architecture that decomposes canonical patch tokens into shared target evidence and sensor-specific residual evidence, and uses the decomposed states to control foreground gating, sensor reliability, and task-context modulation for patch-level sensor fusion.

叙事重点：

- 不要写成“在 ASF 上加了一个模块”。
- 要写成“canonical alignment 是必要基础，但还不够；鲁棒融合还需要知道同一个 patch 里哪些是共享目标证据，哪些是模态特有残差/噪声”。
- ASF/UCP 是 canonical patch fusion substrate；TaskDec 是决定 patch 怎么被信任、怎么被调制的主体架构。

## 3. 正文 9 页布局建议

| 部分 | 页数预算 | 任务 |
|---|---:|---|
| 摘要 | 0.25 | 问题、方法、一两个关键数字。 |
| 1. 引言 | 1.05 | 提出 patch-level evidence availability，给贡献点。 |
| 2. 相关工作 | 0.75 | 紧凑对比 ASF、L4DR/3D-LRF/AW-MoE、DecAlign。 |
| 3. 方法 | 2.20 | 只保留 4 个关键小节，配主框架图。 |
| 4. 实验 | 3.20 | v1 主表、天气表、消融、泛化/缺模态。 |
| 5. 分析可视化 | 0.80 | PCA + centroid distance + gate。 |
| 6. 总结 | 0.25 | 简短收束，别过度声称。 |
| 浮动余量 | 0.50 | caption、公式、空白、排版损耗。 |

如果排版超页，优先移动到附录：

1. VoD 详细表。
2. 效率表。
3. reliability readout。
4. 完整 weather@0.5 表。
5. protocol sensitivity 全表。

## 4. 正文图表安排

2026-09-10 最新视觉排布（依据作者进一步反馈）：正文以 **5 图 + 4 个紧凑表** 为目标。Fig.1 独立动机、Fig.2 主框架、Fig.3 代表性 PCA、Fig.4 真正的 BEV gate 空间热力图、Fig.5 实车场景 ASF–TaskDec 检测对比；四表为 v1 主结果、天气、组件和 VoD 官方指标。现有“中心距离＋前景/背景 gate”是统计图，不是 BEV 热力图，转入附录。下面保留原候选材料说明，最新编号、来源与待制作状态见 [现有图表清单与安排](taskdec_figure_table_inventory_and_placement_260910.md)。Fig.4 已完成[两场景初稿 PDF](../analysis_exports/taskdec_bev_gate_fig4_260910/paper_fig4_taskdec_bev_gate_draft.pdf)：真实相机、LiDAR BEV/GT 和完整预测 gate，暂选阴天高速与雨夜路口；[21 帧导出及复现说明](../analysis_exports/taskdec_bev_gate_fig4_260910/README.md)包含选帧依据和核查记录。动机图与 ASF–TaskDec 实车检测对比尚待制作。

### Fig. 1 动机图：Patch-Level Evidence Availability

正文位置：引言第一页，最好在贡献点之前或之后。

图要表达：

- camera、LiDAR、4D radar 在同一 canonical patch 中提供的信息质量不同。
- 传感器“存在”不等于该 patch 上“可靠”。
- 目标证据可以拆成跨模态共享部分和模态特有部分。
- TaskDec 从 patch-level evidence availability 角度解决融合控制。

本地材料位置：

- 目前还没有正式绘图文件。
- 之前的图 prompt/写作建议参考：
  - `/home/hongsheng/dec_con_asf/results/taskdec_robust_paper_writing_advice_260828.md`
  - `/home/hongsheng/dec_con_asf/results/taskdec_iclr27_main_appendix_organization_260909.md`

建议 caption：

> 不同传感器即使同时可用，也可能在同一个目标 patch 上提供不同质量的证据。TaskDec 将 sensor availability 推进到 patch-level evidence availability，通过共享/特有表征解耦来控制融合。

### Fig. 2 主框架图：TaskDec Architecture

正文位置：方法章节开头或 3.3 附近。

图要表达：

1. 多模态 encoder 产生 BEV/canonical patch features。
2. ASF/UCP 被概括为较小的 `Canonical Patch Fusion Substrate`。
3. 中央放大的 TaskDec block：
   - common/unique decomposition
   - foreground gate
   - sensor reliability controller
   - task-context modulation
4. controlled tokens 进入 patch-level fusion 和 detection head。

本地代码位置：

- TaskDec fuser 主实现：
  - `/home/hongsheng/dec_con_asf/models/fuser/patch_dec_a2_fusion.py`
- ASF baseline fuser：
  - `/home/hongsheng/dec_con_asf/models/fuser/a2_fusion.py`
- skeleton / loss 集成：
  - `/home/hongsheng/dec_con_asf/models/skeletons/fusion_base_integrated.py`
- 主配置：
  - `/home/hongsheng/dec_con_asf/configs/ASF_task_dec_controlled_robust_v1_0.yml`
- 主实验日志配置备份：
  - `/home/hongsheng/dec_con_asf/logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`

注意：

- 图中 ASF 不要画太大，避免像“ASF + 插件”。
- TaskDec 控制器要画成主干的一部分，而不是旁支 auxiliary loss。

### Table 1 K-Radar v1.0 主结果表

正文位置：实验 4.2。

推荐只放代表性方法：

| Method | Sensors | APBEV@0.5 | AP3D@0.5 | APBEV@0.3 | AP3D@0.3 |
|---|---|---:|---:|---:|---:|
| RTNH | R | 36.00 | 14.10 | 41.10 | 37.40 |
| 3D-LRF | L+R | 73.60 | 45.20 | 84.00 | 74.80 |
| L4DR | L+R | 77.50 | 53.50 | 79.50 | 78.00 |
| ASF | C+L+R | 80.33 | 67.19 | 80.78 | 80.31 |
| AW-MoE | L+R | 84.20 | 61.50 | 88.20 | 83.90 |
| AW-MoE-LRC | C+L+R | - | 61.80 | - | 84.30 |
| TaskDec Robust | C+L+R | **88.10** | **67.50** | **88.84** | **88.36** |

整理结果位置：

- 主表草稿：
  - `/home/hongsheng/dec_con_asf/results/paper_main_table_kradar_v1_conf0_3_draft_260901.md`
- compact weather/main table：
  - `/home/hongsheng/dec_con_asf/results/paper_main_table_kradar_v1_weather_compact_260901.md`
- protocol 主说明：
  - `/home/hongsheng/dec_con_asf/results/v1_conf0_3_main_protocol_260819.md`
- published reference 整理：
  - `/home/hongsheng/dec_con_asf/results/published_k_radar_v1_references.md`
  - `/home/hongsheng/dec_con_asf/results/published_k_radar_v1_references.json`

TaskDec 主结果位置：

- 论文主结果整理：
  - `/home/hongsheng/dec_con_asf/results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.md`
  - `/home/hongsheng/dec_con_asf/results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.json`
- 全量评测日志整理：
  - `/home/hongsheng/dec_con_asf/logs/exp_260812_232650_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.md`
  - `/home/hongsheng/dec_con_asf/logs/exp_260812_232650_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.json`
- 主模型 checkpoint：
  - `/home/hongsheng/dec_con_asf/logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`

说明：

- `exp_260812_232650.../models` 目录本身为空；后续若要复跑/画图，优先用 `exp_260810_221258.../models/model_0.pt` 这个 ckpt。
- 论文主表用整理好的 `summary_conf0.3.md/json` 和 `full_eval_summary.md/json` 即可。

ASF 官方复评位置：

- 官方 v1.0 ckpt：
  - `/home/hongsheng/K-Radar-main/pretrained/v1_0_official/A2F_v1_0_model_10.pt`
- ASF released checkpoint `conf_thr=0.3` 本地复评：
  - `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.md`
  - `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.json`
- ASF protocol audit：
  - `/home/hongsheng/dec_con_asf/results/asf_v1_conf_protocol_audit_260828.md`

正文 caption 推荐：

> ASF is evaluated from the released official checkpoint under `conf_thr=0.3`; other literature results are taken from the corresponding papers.

正文不要写 ASF 争议细节，只用中性协议表述。

### Table 2 K-Radar v1.0 Weather Breakdown

正文位置：实验 4.3。

推荐只放 AP3D@IoU=0.3，保持紧凑。

| Method | Sensors | Total | Nor. | Ove. | Fog | Rain | Sle. | L.s. | H.s. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RTNH | R | 37.40 | 37.60 | 42.00 | 41.20 | 29.20 | 49.10 | 63.90 | 43.10 |
| 3D-LRF | L+R | 74.80 | 81.20 | 87.20 | 86.10 | 73.80 | 49.50 | 87.90 | 67.20 |
| L4DR | L+R | 78.00 | 77.70 | 80.00 | 88.60 | 79.20 | 60.10 | 78.90 | 51.90 |
| ASF | C+L+R | 80.31 | 79.57 | 89.89 | 90.67 | 80.97 | 80.20 | 80.89 | **71.71** |
| AW-MoE | L+R | 83.90 | 84.20 | 90.00 | **95.30** | 84.40 | 72.90 | **90.20** | 64.00 |
| AW-MoE-LRC | C+L+R | 84.30 | 84.70 | **91.00** | **95.30** | 84.00 | 72.90 | 89.60 | 63.70 |
| TaskDec Robust | C+L+R | **88.36** | **87.66** | 90.39 | 90.57 | **88.90** | **80.42** | 89.28 | 71.41 |

整理结果位置：

- `/home/hongsheng/dec_con_asf/results/paper_main_table_kradar_v1_weather_compact_260901.md`
- `/home/hongsheng/dec_con_asf/results/robust_v1_model0_weather_delta_260820.md`

推荐正文说法：

> TaskDec 在 Total、Normal、Rain、Sleet 上有最强 AP3D@0.3，并在 Light snow/Heavy snow 上保持竞争力；Fog 和 Overcast 并非全面最优，因此不要声称每个天气都 SOTA。

### Table 3 组件消融表

正文位置：实验 4.4。

选择流程：作者已说明移除项也经过 1000 样本小测，再选择最优对比结果。正文/表注说明先小测选择、再报告所选模型的全量结果；具体样本来源、选择指标、候选范围和 checkpoint 写入附录。不同最优 epoch 可以直接比较，不要求编号相同；本轮未逐条核对这些选择记录，不额外断言样本 ID 和搜索预算完全相同。

推荐正文表：

| Variant | Dec. sup. | FG gate | Reliability | Task ctx. | AP3D@0.5 | AP3D@0.3 |
|---|---|---|---|---|---:|---:|
| ASF | - | - | - | - | 67.19 | 80.31 |
| w/o reliability | yes | yes | no | yes | 64.38 | 79.62 |
| w/o task context | yes | yes | yes | no | 66.23 | 80.14 |
| w/o decoupling supervision | no | yes | yes | yes | 66.16 | 80.23 |
| w/o foreground gate | yes | no | yes | yes | 64.80 | 80.00 |
| Full TaskDec | yes | yes | yes | yes | **67.50** | **88.36** |

整理结果位置：

- `/home/hongsheng/dec_con_asf/results/taskdec_v1_component_ablation_conf0_3_260901.md`
- `/home/hongsheng/dec_con_asf/results/taskdec_ablation_plan_260831.md`

各消融原始路径：

- w/o sensor reliability：
  - config: `/home/hongsheng/dec_con_asf/configs/ASF_task_dec_controlled_robust_v1_0_wo_sensor_reliability.yml`
  - run config: `/home/hongsheng/dec_con_asf/logs/exp_260831_003901_TaskDecAblWoSensorReliability_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
  - result: `/home/hongsheng/dec_con_asf/logs/exp_260831_003901_TaskDecAblWoSensorReliability_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt`
- w/o task context：
  - config: `/home/hongsheng/dec_con_asf/configs/ASF_task_dec_controlled_robust_v1_0_wo_task_context.yml`
  - run config: `/home/hongsheng/dec_con_asf/logs/exp_260831_003901_TaskDecAblWoTaskContext_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
  - result: `/home/hongsheng/dec_con_asf/logs/exp_260831_003901_TaskDecAblWoTaskContext_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt`
- w/o decoupling supervision：
  - config: `/home/hongsheng/dec_con_asf/configs/ASF_task_dec_controlled_robust_v1_0_wo_decoupling_supervision.yml`
  - run config: `/home/hongsheng/dec_con_asf/logs/exp_260901_075157_TaskDecAblWoDecouplingSupervision_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
  - result: `/home/hongsheng/dec_con_asf/logs/exp_260901_075157_TaskDecAblWoDecouplingSupervision_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt`
- w/o foreground gate：
  - config: `/home/hongsheng/dec_con_asf/configs/ASF_task_dec_controlled_robust_v1_0_wo_foreground_gate.yml`
  - run config: `/home/hongsheng/dec_con_asf/logs/exp_260901_075156_TaskDecAblWoForegroundGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
  - result: `/home/hongsheng/dec_con_asf/logs/exp_260901_075156_TaskDecAblWoForegroundGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt`

推荐正文说法：

> 在小测选择后的全量评测中，移除解耦监督、前景门控、可靠性控制或任务上下文，均将 AP3D@0.3 从 88.36 降至约 79.6–80.2，支持各部分在 TaskDec 架构中的作用。

### Fig. 3 表征与门控可视化

正文位置：实验分析或方法之后的 analysis 小节。

推荐正文使用：

- PCA 代表天气图：
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_representative.pdf`
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_representative.png`
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_representative.svg`
- centroid distance + foreground gate：
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_decoupling_and_gate.pdf`
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_decoupling_and_gate.png`
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_decoupling_and_gate.svg`

原始导出：

- `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_patch_pca_weather_260909/taskdec_patch_states_pca.npz`
- `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_patch_pca_weather_260909/taskdec_patch_states_pca.csv`
- `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_patch_pca_weather_260909/pca_weather_analysis.md`
- `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_patch_pca_weather_260909/weather_pca_modality_distances.csv`
- `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_patch_pca_weather_260909/weather_sensor_reliability.md`

可视化脚本：

- 导出 PCA 数据：
  - `/home/hongsheng/dec_con_asf/tools/analysis/export_taskdec_patch_pca.py`
- 绘 weather PCA：
  - `/home/hongsheng/dec_con_asf/tools/analysis/plot_taskdec_weather_pca.py`
- 生成论文版图：
  - `/home/hongsheng/dec_con_asf/tools/analysis/make_taskdec_paper_visuals.py`
- 搜 sensor case：
  - `/home/hongsheng/dec_con_asf/tools/analysis/find_taskdec_sensor_cases.py`

安全说法：

> PCA 结果显示 shared target state 显著拉近跨模态中心距离，而 sensor-specific state 保留模态差异；foreground gate 在前景 patch 上更高，并在 fog/snow-like adverse conditions 下更强。

不要说：

> reliability 会随天气显式切换主导传感器。

当前 reliability head 在这个 checkpoint 里是 LiDAR-dominant，最多作为附录诊断图。

### Table 4 泛化与缺模态 compact 表

正文位置：实验 4.5，可选。

如果正文页数紧张，这张表移到附录，只在正文写一段话。

推荐 compact 表：

| Setting | Baseline | TaskDec | Metric | Delta |
|---|---:|---:|---|---:|
| K-Radar v2 Sedan adverse weather | 52.25 | 54.79 | selected-weather AP3D@0.5 | +2.54 |
| K-Radar v2 Bus/Truck adverse weather | 38.22 | 42.29 | selected-weather AP3D@0.5 | +4.07 |
| VoD native PP L+R | 69.88 | 70.18 | EAA mAP | +0.30 |
| VoD native PP L+R | 83.80 | 83.79 | DC/RoI mAP | -0.01 |
| K-Radar v1 LR availability | 86.02 | 88.06 | AP3D@0.3 | +2.04 |

表注：v2 两行的模型为 `DecControlled (early variant)`，没有 task-context 分支；VoD 两行均为 native PP warm-start epoch 79。缺模态的完整 RLC/LR/LC/RC 表放附录，其中 LC AP3D@0.3 提升 6.88，RC 下降 8.07；LR AP3D@0.5 略低 0.30。表内的模型身份与指标应分别标明。

对应位置：

- K-Radar v2：
  - `/home/hongsheng/dec_con_asf/results/paper_supp_table_kradar_v2_generalization_260901.md`
  - ours result: `/home/hongsheng/dec_con_asf/results/exp_260806_000825_DecControlledASFStrong_final/summary_conf0.3.md`
  - ASF v2 result: `/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/summary_conf0.3.md`
- VoD：
  - `/home/hongsheng/dec_con_asf/results/paper_vod_main_table_draft_260909.md`
  - native PP/TaskDec 历史对比：`/home/hongsheng/dec_con_asf/results/vod_native_taskdec_pp_comparison_260908.md`
  - checkpoint scan：`/home/hongsheng/dec_con_asf/results/vod_taskdec_pp_best_epoch_scan_260908.md`
- K-Radar v1 missing modality：
  - `/home/hongsheng/dec_con_asf/results/paper_availability_missing_modalities_260902.md`
  - `/home/hongsheng/dec_con_asf/results/v1_lr_conf0_3_sota_comparison_260828.md`

推荐正文说法：

> 在 VoD 的原生 PP 风格 L+R 骨干上训练后，TaskDec 将强 PP-Concat 基线的 EAA mAP 从 69.88 提高到 70.18，DC mAP 基本持平，支持架构在 K-Radar 之外的适用性。K-Radar v2.0 的补充实验采用不含 task context 的早期 DecControlled 变体，在选定天气的 AP3D@0.5 上获得增益。L4DR 在 VoD 上仍有更高绝对性能，详见完整对照表。

## 5. 正文段落组织

### 摘要

建议 5 句话：

1. 恶劣天气 3D 检测需要可靠地融合 camera、LiDAR、4D radar。
2. 现有 canonical patch fusion 解决了模态对齐，但没有显式分离共享目标证据和传感器特有残差。
3. 我们提出 TaskDec，在 canonical patch 空间中进行 common/unique decomposition，并用解耦表征控制 foreground gate、sensor reliability 和 task context。
4. 在 K-Radar v1.0 Sedan `conf_thr=0.3` 协议下，TaskDec 达到 AP3D@0.3 = 88.36，比 released ASF checkpoint 高 8.05 点，比 AW-MoE-LRC 高 4.06 点。
5. 组件消融支持各控制部分的作用，VoD 原生强基线上的 EAA 增益进一步支持架构适配能力；v2 的早期变体说明留在实验部分。

### 1. 引言

第一段：问题背景。

> 多模态 3D 检测通常被看作互补传感器融合问题，但在雨雾雪等条件下，这种互补性是局部且条件化的。一个传感器可以整体可用，却在某个目标 patch 上因为稀疏、散射、遮挡或视觉退化而不可靠。

第二段：已有方法不足。

> ASF 这类 canonical patch fusion 将不同传感器投到统一 patch 空间，是一个很强的融合基础。但统一空间并不自动回答一个问题：同一个 patch token 里哪些是跨模态共享的目标证据，哪些只是模态特有残差甚至噪声？

第三段：本文方法。

> TaskDec 把这个问题建模为 patch-level evidence availability。它将每个模态 patch token 分解为 shared target state 和 sensor-specific state，并从这些状态中预测前景门控、可靠性缩放和任务上下文，动态调制后续 patch-level attention。

第四段：贡献。

- 提出一种 canonical patch 空间上的任务感知解耦融合架构。
- 将 common/unique decomposition 从表征正则推进到检测融合控制。
- 在 K-Radar v1.0 获得强主结果，并通过天气、消融、缺模态、v2.0 和 VoD 实验验证。

### 2. 相关工作

建议 3 段，不要铺太长。

第一段：4D radar / K-Radar / adverse-weather 3D detection。

- RTNH / K-Radar：数据集和 radar baseline。
- 3D-LRF、L4DR、AW-MoE、WCBR、FusionBev、DDMDGF：多数是 L+R 或 condition-aware/weather-aware fusion。
- 对比点：TaskDec 是 C+L+R canonical patch fusion 上的 decoupled control architecture，同时也支持 LR availability。

第二段：availability-aware / canonical fusion。

- ASF 是直接 baseline。
- 对比点：ASF 强在统一 canonical patch space 和 missing-sensor handling；TaskDec 进一步在该空间中建模 patch-level evidence reliability。

第三段：decoupled multimodal representation。

- DECALIGN 提供 common/unique 表征学习思想。
- 对比点：DECALIGN 偏全局/语义表征学习；TaskDec 把 common/unique decomposition 放到 object-level BEV/canonical patches，并用来控制检测融合。

### 3. 方法

只保留 4 个小节。

#### 3.1 Canonical Patch Fusion Substrate

定义：

- modality BEV feature：`F_m`
- canonical patch token：`x_{m,p}`
- ASF-style patch attention：`z_p = Attn(q_p, {x_{m,p}}, {x_{m,p}})`

写短一点。它是 TaskDec 的操作空间，不是本文要花大量篇幅重讲的贡献。

代码位置：

- `/home/hongsheng/dec_con_asf/models/fuser/a2_fusion.py`
- `/home/hongsheng/dec_con_asf/models/fuser/patch_dec_a2_fusion.py`

#### 3.2 Foreground-Aware Common/Unique Decomposition

定义：

- `c_{m,p} = C_m(x_{m,p})`
- `u_{m,p} = U_m(x_{m,p})`

说明损失：

- common alignment：前景 patch 上跨模态 common state 对齐。
- unique separation：不同模态 unique state 不坍缩。
- orthogonality：同一模态 common 和 unique 分离。

重点句：

> 我们只在 GT box 导出的 foreground patches 上强调解耦监督，因为 BEV patch 大多数是背景；如果全 patch 对齐，模型主要会学到背景一致性。

#### 3.3 Decoupling-Guided Fusion Control

这是方法核心。

控制信号：

- foreground gate `g_p`
- sensor reliability `r_{m,p}`
- token scale `s_{m,p}`

核心公式：

`x'_{m,p} = s_{m,p} [x_{m,p} + alpha g_p (c_{m,p}+u_{m,p})]`

要强调：

- decomposition 不是只为了 auxiliary loss。
- common/unique states 直接参与控制 token 被如何送入 fusion。
- reliability uniform 时，结构退化为接近 ASF 的融合；这体现是受控扩展，不是粗暴替换。

#### 3.4 Task Context and Objective

定义：

- task context `h_p`
- query modulation：`q'_p = q_p + beta_q g_p h_p`
- fused token modulation：`z'_p = z_p + beta_z g_p h_p`

总 loss：

`L = L_det + lambda_scl L_scl + lambda_dec L_dec + lambda_gate L_gate + lambda_cls L_cls`

具体 loss 权重、MLP 维度、scale clamp 放附录。

## 6. 实验章节组织

### 4.1 Setup

必须写清：

- K-Radar v1.0 Sedan，driving-corridor / narrow ROI。
- 主表协议：`conf_thr=0.3`，APBEV/AP3D at IoU 0.3/0.5。
- ASF 是 released official checkpoint 在本地同协议复评。
- 其它论文方法使用原文报告数字。
- Encoders/head 基本沿用 ASF-family 设置，本文修改 fusion controller。

路径：

- protocol audit：`/home/hongsheng/dec_con_asf/results/asf_v1_conf_protocol_audit_260828.md`
- main protocol：`/home/hongsheng/dec_con_asf/results/v1_conf0_3_main_protocol_260819.md`
- full metric audit：`/home/hongsheng/dec_con_asf/results/full_eval_metric_audit_260821.md`

### 4.2 Main Results

放 Table 1。

推荐文字：

> TaskDec 在 `conf_thr=0.3` 下达到 88.36 AP3D@0.3，相比同协议复评的 released ASF checkpoint 提升 8.05 点，相比已发表 C+L+R 方法 AW-MoE-LRC 提升 4.06 点。在 IoU=0.5 下，TaskDec 也略高于 ASF，并在 compact comparison 中取得最强 AP3D@0.5。

### 4.3 Weather Robustness

放 Table 2。

推荐文字：

> 总体提升不是由单一简单子集造成的。TaskDec 在 Normal、Rain、Sleet 上取得明显优势，在 snow 条件下也保持竞争力；Fog/Overcast 并非全面领先，说明 TaskDec 提升了广泛恶劣天气鲁棒性，但没有把每个天气模式都完全解决。

### 4.4 Component Ablation

放 Table 3。

推荐文字：

> 完整模型与移除项均经过 1000 样本小测选择，再报告所选模型的全量结果。去掉 reliability control、task context、decoupling supervision 或 foreground gate，均使 AP3D@0.3 降到约 79.6–80.2，支持这些控制部分的作用。选择指标及样本来源在实验设置和附录中说明。

### 4.5 Generalization and Availability

如果正文还有空间，放 compact Table 4；否则只写短段并指向 appendix。

推荐文字：

> TaskDec 在推理时缺失 camera 或 radar 的 LR/LC 设置下，相对官方 ASF 分别提高 2.04/6.88 AP3D@0.3；RC 是主要退化组合。VoD 实验将方法适配到原生 PointPillars 风格 L+R 管线，在所报告的 warm-start 设置下，EAA mAP 由强 PP-Concat 基线的 69.88 提高到 70.18，DC 基本持平，支持跨数据集与骨干的适用性。v2.0 补充结果来自不含 task context 的早期 DecControlled 变体。L4DR 在 VoD 上仍有更高绝对性能。

## 7. 附录安排

### Appendix A 方法细节

放：

- MLP 结构。
- common/unique loss 完整定义。
- gate/reliability/task context 公式。
- training schedule。
- 超参表。
- pseudo-code。

路径：

- `/home/hongsheng/dec_con_asf/models/fuser/patch_dec_a2_fusion.py`
- `/home/hongsheng/dec_con_asf/models/skeletons/fusion_base_integrated.py`
- `/home/hongsheng/dec_con_asf/configs/ASF_task_dec_controlled_robust_v1_0.yml`

### Appendix B 协议与置信度阈值审计

放：

- ASF `conf_thr=0.0` vs `conf_thr=0.3`。
- ASF released ckpt 来源。
- 为什么正文主表用 `conf_thr=0.3`。
- ASF local repro 只作为 protocol sensitivity，不放正文争议。

路径：

- `/home/hongsheng/dec_con_asf/results/asf_v1_conf_protocol_audit_260828.md`
- `/home/hongsheng/dec_con_asf/results/v1_conf0_3_main_protocol_260819.md`
- ASF official ckpt: `/home/hongsheng/K-Radar-main/pretrained/v1_0_official/A2F_v1_0_model_10.pt`
- ASF official re-eval: `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.md`

措辞：

- 用 `protocol sensitivity`、`confidence-threshold disclosure`。
- 不要用 accusation。

### Appendix C K-Radar v1.0 完整比较

放：

- 完整主表，包括 PointPillars、InterFusion、WCBR、L4DR-DA3D、RTNH L/R。
- AP3D@0.5 weather table。
- APBEV weather table 如果空间允许。
- condition breakdown。

路径：

- `/home/hongsheng/dec_con_asf/results/paper_main_table_kradar_v1_conf0_3_draft_260901.md`
- `/home/hongsheng/dec_con_asf/results/paper_main_table_kradar_v1_weather_compact_260901.md`
- `/home/hongsheng/dec_con_asf/analysis_exports/v1_results_big_table_260817.md`
- `/home/hongsheng/dec_con_asf/analysis_exports/v1_all_results_big_table_260817.csv`

### Appendix D Missing-Modality Availability

放：

- RLC、LR、LC、RC 对比 ASF。
- 明确说明：这些是 C+L+R-trained checkpoints，在推理时禁用某些传感器，不是纯 LR/LC/RC trained model。

路径：

- `/home/hongsheng/dec_con_asf/results/paper_availability_missing_modalities_260902.md`
- `/home/hongsheng/dec_con_asf/results/v1_lr_conf0_3_sota_comparison_260828.md`
- ours LR eval:
  - `/home/hongsheng/dec_con_asf/logs/exp_260819_231927_TaskDecControlRobust_v1_0_eval_LR_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.md`
- ASF LR/LC/RC logs:
  - `/home/hongsheng/K-Radar-main/logs_avail_eval/official_v1_A2F_model10_LR_cond_gpu2.log`
  - `/home/hongsheng/K-Radar-main/logs_avail_eval/availability_official_asf_v1_model10_lc_gpu2_260902.log`
  - `/home/hongsheng/K-Radar-main/logs_avail_eval/availability_official_asf_v1_model10_rc_gpu1_260902.log`

### Appendix E K-Radar v2.0 泛化

模型身份：本节推荐结果来自 `DecControlledASFStrong_final` / `DecControlledA2Fusion`，没有完整 TaskDec 的 task-context 分支。正文一句说明、表中标注 `DecControlled (early variant)`，配置细节放本附录。

放：

- selected adverse-weather AP3D@0.5 表。
- AP3D@0.3 rainy/snowy 表。
- full total metrics。

路径：

- `/home/hongsheng/dec_con_asf/results/paper_supp_table_kradar_v2_generalization_260901.md`
- ours:
  - `/home/hongsheng/dec_con_asf/results/exp_260806_000825_DecControlledASFStrong_final/summary_conf0.3.md`
  - `/home/hongsheng/dec_con_asf/results/exp_260806_000825_DecControlledASFStrong_final/summary_conf0.3.json`
- ASF:
  - `/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/summary_conf0.3.md`
  - `/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/summary_conf0.3.json`

推荐 claim：

> 早期 DecControlled 变体在 v2.0 的选定恶劣天气 AP3D@0.5 上提高 Sedan/Bus-Truck 指标，支持解耦控制思路的扩展性；该结果不代表完整 TaskDec 的无修改迁移。

### Appendix F VoD 外部数据集迁移

写作重点：验证 TaskDec 能在目标数据集上训练并适配原生 PP L+R 骨干，且在强 PP-Concat 基线上提高 EAA。L4DR 在 K-Radar 主表与相关工作中充分讨论，在本节正文只需一句说明绝对性能仍更高；保留其完整表格行。warm-start、精度和 checkpoint 选择记录放设置，不将额外匹配训练列为当前写作的前置要求。

放：

- same-protocol KITTI AP_R40 表。
- VoD official EAA/DC 表。
- native PP-Concat 与 TaskDec-PP 设置说明。
- 说明 L4DR 仍是更强的 specialized VoD method。

路径：

- 总表：
  - `/home/hongsheng/dec_con_asf/results/paper_vod_main_table_draft_260909.md`
- 实验设计：
  - `/home/hongsheng/dec_con_asf/results/vod_experiment_design_260828.md`
- 已知论文扫描：
  - `/home/hongsheng/dec_con_asf/results/vod_known_papers_scan_260829.md`
- native PP / TaskDec 对比历史：
  - `/home/hongsheng/dec_con_asf/results/vod_native_taskdec_pp_comparison_260908.md`
- checkpoint scan：
  - `/home/hongsheng/dec_con_asf/results/vod_taskdec_pp_best_epoch_scan_260908.md`

VoD 代码和数据：

- VoD 数据：
  - `/home/hongsheng/vod/view_of_delft_PUBLIC`
- VoD 适配代码：
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native`
- PP-Concat run：
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/PP_Concat/native_pp_concat_lr_b16_amp_ep80_260907_gpu2/train_20260907-223434.log`
- TaskDec first FP32 run：
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP/native_taskdec_pp_lr_b16_fp32_ep80_260907_gpu3/train_20260907-231606.log`
- TaskDec mild run：
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP_MildS05AuxHalf/native_taskdec_pp_mild_s05_auxhalf_b16_fp32_ep80_260908_gpu2/train_20260908-232915.log`
- TaskDec warm-start mild run：
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP_WarmPPConcat_MildS05AuxHalf/native_taskdec_pp_warm_ppconcat_mild_s05_auxhalf_b16_fp32_ep80_260908_gpu3/train_20260908-232940.log`
- warm-start best ckpt 候选：
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP_WarmPPConcat_MildS05AuxHalf/native_taskdec_pp_warm_ppconcat_mild_s05_auxhalf_b16_fp32_ep80_260908_gpu3/ckpt/checkpoint_epoch_79.pth`
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP_WarmPPConcat_MildS05AuxHalf/native_taskdec_pp_warm_ppconcat_mild_s05_auxhalf_b16_fp32_ep80_260908_gpu3/ckpt/checkpoint_epoch_80.pth`
- eval logs：
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native/logs/eval_warm_ppconcat_mild_ep059_079_gpu2.log`
  - `/home/hongsheng/dec_con_asf/vod_taskdec_native/logs/eval_warm_ppconcat_mild_s05_auxhalf_gpu3.log`

推荐 claim：

> With target-dataset training under the reported warm-start setting, TaskDec transfers to a native VoD PP-style L+R backbone, improving the strong PP-Concat baseline from 69.88 to 70.18 EAA mAP while maintaining comparable DC mAP. Specialized L4DR retains higher absolute performance.

### Appendix G 超参与 sensitivity

放：

- `DEC_CONTROL_STRENGTH=0.0/0.5/0.75/1.0`
- gate init bias 如需展示。
- early vs late checkpoint 只作为训练动态说明，别强调 checkpoint hunting。

路径：

- `/home/hongsheng/dec_con_asf/results/taskdec_v1_control_strength_compare_260904.md`
- strength 0.5:
  - `/home/hongsheng/dec_con_asf/logs/exp_260904_013929_TaskDecControlStrength05_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.md`
- strength 1.0:
  - `/home/hongsheng/dec_con_asf/logs/exp_260904_013931_TaskDecControlStrength10_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.md`

推荐说法：

> 相邻 controller strength 设置与主模型接近，而禁用 reliability control 明显下降，说明方法对强度不是极端脆弱，但动态控制本身很关键。

### Appendix H 效率

放：

| Method | Params | Forward latency | FPS | Peak memory |
|---|---:|---:|---:|---:|
| ASF | 78.13M | 79.95 ms | 12.51 | 0.97 GB |
| TaskDec | 79.47M | 86.45 ms | 11.57 | 0.98 GB |

路径：

- `/home/hongsheng/dec_con_asf/results/paper_efficiency_table_260902.md`
- JSON/MD 原始测量：
  - `/home/hongsheng/dec_con_asf/results/efficiency_260902/official_asf_v1_model10_rlc.json`
  - `/home/hongsheng/dec_con_asf/results/efficiency_260902/official_asf_v1_model10_rlc.md`
  - `/home/hongsheng/dec_con_asf/results/efficiency_260902/taskdec_robust_v1_model0_rlc.json`
  - `/home/hongsheng/dec_con_asf/results/efficiency_260902/taskdec_robust_v1_model0_rlc.md`
  - `/home/hongsheng/dec_con_asf/results/efficiency_260902/l4dr_v1_1_model34_lr_local_sparsecube.json`
  - `/home/hongsheng/dec_con_asf/results/efficiency_260902/l4dr_v1_1_model34_lr_local_sparsecube.md`

推荐 claim：

> TaskDec 相比 ASF 只增加 1.34M 参数和约 6.50 ms forward latency，额外开销较小。

### Appendix I 额外可视化与诊断

放：

- all-weather PCA grid。
- reliability readout diagnostic。
- sensor case search。

路径：

- all-weather PCA:
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_all_weather_appendix.pdf`
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_all_weather_appendix.png`
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_all_weather_appendix.svg`
- reliability readout:
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_reliability_readout.pdf`
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_reliability_readout.png`
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_reliability_readout.svg`
- caption note:
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_paper_visuals_260909/paper_visual_caption_notes.md`
- PCA visualization summary:
  - `/home/hongsheng/dec_con_asf/results/taskdec_weather_pca_visualization_260909.md`
- sensor candidate summary:
  - `/home/hongsheng/dec_con_asf/results/taskdec_sensor_case_candidates_260909.md`
- RLC sensor search:
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_patch_pca_weather_260909/taskdec_sensor_case_search.md`
- LR sensor search:
  - `/home/hongsheng/dec_con_asf/analysis_exports/taskdec_patch_pca_weather_lr_260909/taskdec_sensor_case_search.md`

安全说法：

> 当前 selected checkpoint 的 reliability readout 比较保守且 LiDAR-dominant，因此我们把它作为辅助诊断，而不是作为天气相关 sensor switching 的证据。

## 8. 正文不建议放的内容

正文不要放：

- ASF 学术不端/质疑措辞。
- ASF local repro 比 official ckpt 更强这件事。
- 大量 checkpoint 选择历史。
- VoD 上落后 L4DR 的详细讨论。
- reliability 根据天气显式切换主导传感器的说法。
- 所有超参组合扫描。
- loss 权重和 MLP 结构细枝末节。

这些内容放附录或者内部保留。

## 9. 稳妥 claim 清单

可以写：

1. 主结果：

   > 在 K-Radar v1.0 Sedan `conf_thr=0.3` 协议下，TaskDec Robust 达到 88.36 AP3D@0.3，在 compact protocol-compatible comparison 中取得最强结果。

2. ASF 对比：

   > 相比同协议复评的 released ASF checkpoint，TaskDec AP3D@0.3 提升 8.05 点，AP3D@0.5 提升 0.31 点。

3. 消融：

   > 去掉 decoupling supervision、foreground gate、reliability control 或 task context 都明显降低 AP3D@0.3，说明这些部分共同构成有效架构。

4. 天气：

   > TaskDec 在 total AP3D@0.3 上最强，并在 normal、rain、sleet 上优势明显，但不声称每个天气子集都最优。

5. 泛化：

   > TaskDec 在 VoD 原生 PP L+R 强基线上取得 EAA mAP 增益，支持架构适配能力；v2.0 的 selected adverse-weather 增益来自不含 task context 的早期 DecControlled 变体。

## 10. 高风险 claim 清单

避免写：

- TaskDec beats ASF under all protocols.
- TaskDec beats L4DR on VoD.
- TaskDec proves weather-dependent sensor switching.
- TaskDec is pure L+R-trained SOTA.
- Every component improves every metric.
- TaskDec solves K-Radar v2.0 broadly.

## 11. 最小可行正文故事线

如果时间/页数很紧，就按这个最小故事写：

1. 引言：sensor availability 应该推进到 patch-level evidence availability。
2. 方法：TaskDec 在 canonical patch 空间中解耦 common/unique，并用它们控制融合。
3. 主结果：K-Radar v1.0 `conf_thr=0.3` 达到 88.36 AP3D@0.3。
4. 天气：不是单一子集收益，rain/sleet 等条件下有明显提升。
5. 消融：四个核心部件都重要。
6. 泛化：以 VoD 原生强基线上的 EAA 增益和 LR/LC 的缺模态表现为主要扩展证据；v2 标注早期变体，RC 作为例外简述，细节进附录。

这是最像 ICLR 投稿的版本：主文干净、主张明确、附录厚实。
