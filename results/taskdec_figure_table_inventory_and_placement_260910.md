# TaskDec 现有图表清单与正文、附录安排

日期：2026-09-10。依据现有文件、图片预览及作者最新写作决定整理。

依据作者进一步明确的视觉偏好，正文改为以 **5 张图 + 4 个紧凑表** 为目标：独立动机图、主框架图、PCA 图、真正的 BEV gate 热力图，以及实车场景检测对比图。原“2 图 + 4 表”方案过度压缩了视觉叙事，现已替换。以下是内容与版面规划，尚未在完整 LaTeX 稿中验证占页。

VoD 官方指标 compact 表仍保留在正文，支持原生强基线上的适配收益。独立动机与主框架分图，代表性 PCA 进入正文，中心距离/按天气 gate 均值统计移入附录。BEV gate 的 Fig.4 初稿已于 9 月 10 日生成，实车检测对比仍待制作；早期 v2 和缺模态完整表保留在附录。

**一、已经有哪些图。**

同一内容的 PNG/SVG/PDF 不重复计数，历史版本也不视为不同论文图。当前核心素材为两组结构图草稿和四张论文版分析图。

| 现有内容 | 文件入口 | 状态 | 推荐用途 |
|---|---|---|---|
| 整体 pipeline 图 | [v3 clean SVG](../paper_figures/task_dec_asf_pipeline_overview_v3_clean.svg)、[PNG](../paper_figures/task_dec_asf_pipeline_overview_v3_clean.png) | 已有 v1、v2、v3，均有 SVG/PNG；仍是草稿 | 正文 Fig.2 的主要基础 |
| Controller 细节图 | [v2 clean SVG](../paper_figures/task_dec_controller_detail_v2_clean.svg)、[PNG](../paper_figures/task_dec_controller_detail_v2_clean.png) | 已有 v1、v2，均有 SVG/PNG；仍需核对箭头语义 | 核心计算关系整合到正文 Fig.2；修正后的展开版可放附录 |
| 代表天气 PCA | [PDF](../analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_representative.pdf) | 已生成 PDF/SVG/PNG；Normal/Fog/Rain/Heavy snow，4×3 面板 | 压缩为两种天气×raw/common/unique 三列，作为正文 Fig.3 |
| 解耦中心距离 + 前景 gate | [PDF](../analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_decoupling_and_gate.pdf) | 已生成 PDF/SVG/PNG；横向双面板；不是空间热力图 | 附录量化诊断，支持正文 PCA/BEV gate 分析 |
| 全天气 PCA | [PDF](../analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_pca_all_weather_appendix.pdf) | 已生成 PDF/SVG/PNG；7×3 面板 | 附录 |
| Reliability readout | [PDF](../analysis_exports/taskdec_paper_visuals_260909/paper_fig_taskdec_reliability_readout.pdf) | 已生成 PDF/SVG/PNG；LiDAR 与放大的 Camera/Radar 读数 | 附录诊断 |
| 真实相机 + LiDAR BEV/GT + 完整 gate | [Fig.4 PDF](../analysis_exports/taskdec_bev_gate_fig4_260910/paper_fig4_taskdec_bev_gate_draft.pdf)、[PNG](../analysis_exports/taskdec_bev_gate_fig4_260910/paper_fig4_taskdec_bev_gate_draft.png)、[导出说明](../analysis_exports/taskdec_bev_gate_fig4_260910/README.md) | 新增初稿；阴天高速与雨夜路口两帧；21 帧完整 gate 已保存 | 正文 Fig.4；其余候选可供附录选用 |

现有框架图不能直接视为最终稿。预览中，pipeline 图的部分文字重叠，控制箭头的落点不够明确；controller 图将 common alignment / unique separation 等监督项画在前向路径上，容易误读。正式图应把训练损失与前向计算分开，准确显示 reliability 的逐模态输入，以及 query 在 attention 之前、output residual 在 PFT 之前注入的关系。

现有“中心距离＋gate”统计图左侧衡量二维 PCA 空间的模态中心距离，右侧按天气汇总前景/背景 gate 均值。它既没有 BEV 的 x/y 空间坐标，也没有逐 patch 的完整空间布局，不能称为 BEV gate 热力图。PCA 和 gate 均作为描述性诊断，不使用“证明天气切换”或未经检验的“显著”措辞。

还存在三套分析导出：主模型 RLC、同模型 LR、Balanced model_2 的全天气 PCA/距离/gate 图，以及 9 月 4 日的早期导出。正文与主分析统一使用 Robust model_0 的 9 月 9 日 RLC 导出；其他导出作补充诊断或内部参考，不重复全部入稿。

以下尚不是现成论文图：

- 独立的 “Patch-Level Evidence Availability” 动机图：作为正文 Fig.1，结合真实驾驶场景、同一目标区域的多模态观测和概念示意；概念分解与实测结果明确区分。
- ASF 与 TaskDec 检测框、漏检/误检的定性对比：拟作正文 Fig.5，在本次检查的论文素材目录中未找到已整理成稿的图。
- Token-scale 空间热力图尚未制作；Fig.4 的前景 gate 热力图已经完成初稿，不应将二者混称。
- Sensor case 展示：有 [候选帧与 patch 表](taskdec_sensor_case_candidates_260909.md)，不等于已经完成可视化；当前候选不支持传感器主导权切换的故事。

**二、已经有哪些表。**

下表按实验主题归类。表格主要以 Markdown 存在，部分已有 LaTeX 草稿；“已有表”不等于已经插入完整论文并完成排版。

| 表格主题 | 当前素材 | 状态 | 安排 |
|---|---|---|---|
| K-Radar v1.0 主结果 | [compact 表](paper_main_table_kradar_v1_weather_compact_260901.md)、[完整比较](paper_main_table_kradar_v1_conf0_3_draft_260901.md) | 完整数字与草稿已有 | compact 正文 Table 1，完整比较附录 |
| v1.0 天气分解 | [AP3D@0.3 / @0.5 两表](paper_main_table_kradar_v1_weather_compact_260901.md) | 已有七种天气与 Total | @0.3 正文 Table 2，@0.5 附录 |
| 组件消融 | [四项移除结果](taskdec_v1_component_ablation_conf0_3_260901.md) | 已有全量指标，已补记 1000 样本小测选择说明 | 精简正文 Table 3，完整指标和选择记录附录 |
| VoD 官方指标 | [EAA/DC 表与类别分解](paper_vod_main_table_draft_260909.md) | 已有 PP-Concat、TaskDec 和文献行 | 精简正文 Table 4，类别分解及完整背景表附录 |
| VoD KITTI 指标 | [AP_R40 的 E/M/H 表](paper_vod_main_table_draft_260909.md) | 已有不同方法、设置和所选 epoch | 附录；与 EAA/DC 分表，不混用最优 checkpoint |
| 缺模态 | [RLC/LR/LC/RC 表](paper_availability_missing_modalities_260902.md) | 已有官方 ASF 与 TaskDec 的八行比较 | 完整附录；正文短述 LR/LC 增益与 RC 例外 |
| K-Radar v2.0 | [selected-weather、rain/snow、Total 表](paper_supp_table_kradar_v2_generalization_260901.md) | 已有，正向推荐结果来自早期 DecControlled | 附录；正文一句交代早期变体及观察 |
| Controller 强度 | [strength 比较](taskdec_v1_control_strength_compare_260904.md) | 0.5/0.75/1.0 有 full 结果，0.0 见组件表；另有 subset-only 参考 | 附录，明确各行的 checkpoint 和评测范围 |
| Gate bias 等探索 | [已完成运行状态](taskdec_finished_runs_status_260907.md) | 混有 full 和 subset-only 状态 | 可选附录或内部参考，不作为完整 sensitivity 表直接入稿 |
| 协议与阈值 | [ASF/conf 核对表](asf_v1_conf_protocol_audit_260828.md)、[完整评测核对](full_eval_metric_audit_260821.md) | 已有 conf=0.0/0.3、发布 checkpoint 与本地运行记录 | 附录 |
| 效率 | [参数、耗时、显存表](paper_efficiency_table_260902.md) | 已有实测及 JSON | 附录；正文可用一句概括开销 |
| 超参数与训练设置 | [主配置](../configs/ASF_task_dec_controlled_robust_v1_0.yml)、[融合实现](../models/fuser/patch_dec_a2_fusion.py) | 信息已存在，尚需整理成统一论文表 | 附录，属于整理工作 |

**三、推荐正文的五张图与四张表。**

| 正文编号 | 内容 | 放置位置 | 读者应得到的信息 |
|---|---|---|---|
| Fig.1 | 独立动机图：真实场景、目标局部观测差异、局部证据控制的概念 | 引言 | 为什么统一空间之后仍需要局部任务控制 |
| Fig.2 | TaskDec 主框架：common/unique + 三路控制与融合位置 | 方法开头 | 各部分如何组成完整方法 |
| Fig.3 | 代表天气 PCA：建议 Normal + 一种恶劣天气，raw/common/unique 三列 | 表征分析 | 分离后的表示具有怎样的跨模态结构 |
| Fig.4 | BEV gate 空间热力图：x/y 米制坐标、预测 gate、GT 框和点云参照 | 控制分析 | 控制强度在场景的什么位置较高 |
| Fig.5 | 实车场景检测对比：同帧 camera/BEV、官方 ASF 与 TaskDec 预测 | 定性结果 | 读者可直接看到所选案例中的漏检、误检及定位差别 |
| Table 1 | K-Radar v1.0 compact 主结果 | Main results | 指定协议下的总体表现，与官方 ASF 及代表方法比较 |
| Table 2 | 七种天气的 AP3D@0.3 | Weather analysis | 收益分布及不同天气的表现 |
| Table 3 | Full 与四项组件移除，保留 AP3D@0.3/@0.5 | Component analysis | 解耦监督、gate、reliability 和 task context 的作用 |
| Table 4 | VoD 原生 PP 的 EAA/DC compact 比较 | Generalization | 架构可适配，并在强 PP-Concat 上提高 EAA |

Fig.1、Fig.5 尚待制作；Fig.4 已有两场景初稿及 21 帧候选总览；Fig.2 有待修正的草稿；Fig.3 有现成数据和图片可压缩。Table 1–3 可从既有表格精简，Table 4 的具体候选如下，均为 L+4DR：

| Method | 来源 / checkpoint | EAA mAP | DC mAP |
|---|---|---:|---:|
| InterFusion | 已收集文献，L4DR Table 3 | 69.83 | 83.80 |
| L4DR | 已收集文献，L4DR Table 3 | 72.70 | 87.47 |
| PP-Concat | 本地，epoch 80 | 69.88 | 83.80 |
| TaskDec-PP | 本地，mild + warm start，epoch 79 | 70.18 | 83.79 |

文字重点放在两条本地结果：EAA +0.30、DC 基本持平。L4DR 的绝对性能如实保留，一句带过；主基准中的 L4DR 比较可以展开。表注/设置写清 VoD 目标数据集训练、warm start 和数值来源，详细训练差异放附录。该 compact 表不加入 R+C 方法、FPS 或逐类别指标。

**四、附录按内容分组。**

| 附录组 | 图 | 表 |
|---|---|---|
| 方法与复现 | 修正后的 controller 细节展开图，可选 | 结构/超参数/训练设置、模型选择流程 |
| 协议 | 暂不需要新增图 | conf=0.0/0.3、checkpoint 来源、本地运行敏感性、LR 重算说明 |
| v1.0 完整结果 | 正文之外的定性检测案例，包括有代表性的失败情况 | 完整文献比较、天气 AP3D@0.5、完整组件指标 |
| 缺模态与扩展 | 不必重复同类 PCA 网格 | RLC/LR/LC/RC、v2 早期变体、VoD AP_R40 与官方类别分解 |
| 机制诊断 | 全天气 PCA、中心距离/按天气 gate 统计、reliability readout、额外 BEV gate 案例 | strength；gate bias 仅在评测范围明确时使用 |
| 效率 | 无需重复画柱状图 | 参数、forward latency/FPS、显存；含数据加载耗时另列 |

代表天气 4×3 PCA 压缩为正文 2×3 版，附录保留全天气 7×3 版。LR/Balanced 的 PCA 仅在讨论对应问题时选用，旧版本不作为独立证据重复展示。

排版紧张时，优先精简重复文字、表格中的文献行和图中案例数。保留独立动机、主框架和正文 PCA；先按两种天气安排 PCA、两帧安排 gate、两至三帧安排检测对比。主结果与天气表可以排成同一表的两个面板，但真正节省空间仍依赖精简列、caption 和留白。图表数量本身不等于占页，最终以实际排版和缩小后的可读性决定。

**五、ASF 图 3 风格是否适合，以及本项目如何实现。**

适合。ASF 图 3 的说明将 front-view camera、LiDAR、4D Radar 和 sensor attention map（SAM）放在一起，展示不同传感器组合的定性结果。SAM 是 CASAP 的跨传感器 attention 分布；它与 TaskDec 的前景 gate 不是同一种量。来源：[ASF 原文 Figure 3](https://arxiv.org/html/2503.07029v2#S3.F3)。本轮读取了原文图注；图片直链与 PDF 获取失败，因此不将未查看的图片细节描述成已核实的视觉观察。

建议借鉴“真实观测＋预测结果＋解释信号”的组织方式，按 TaskDec 的论点重新设计：

| 每行一个真实场景 | Camera + ASF 预测 | Camera + TaskDec 预测 | 同帧 BEV 对比 |
|---|---|---|---|
| Rain 或 Light snow 候选 | GT 与官方模型预测框 | GT 与主模型预测框 | 用相同目标编号辅助定位比较 |
| 另一种天气/距离条件候选 | 同上 | 同上 | 同上 |
| 第三个案例，版面允许时 | 可展示遮挡、远距或失败情况 | 同上 | 同上 |

天气仅是候选筛选范围，尚未确认这些帧存在 TaskDec 改善。按同帧、同传感器组合、同 ROI 和同置信度阈值生成两模型预测，再依据实际匹配结果选案例；预测与 GT 使用不同颜色，局部放大框在两模型中对应同一区域。相机用于展示的视野可以比评测 ROI 更宽，需要标明实际比较区域。定性案例用于说明具体行为，不替代全量 AP。

Gate 图另作 Fig.4，建议每帧使用“真实相机参照＋LiDAR BEV/GT＋预测 gate 热力图”三个面板。所有 gate 图采用一致色标和朝向，显示原始 patch 网格或注明展示插值方式。gate 是所有可用模态共同产生的每 patch 标量，不是相机/雷达各自的可靠性热力图。GT 框仅用于叠加参照，不能将 GT 前景 mask 当成预测 gate。

已核对的实现基础：

- [main_save_rendered_frames.py](../tools/movie_maker/main_save_rendered_frames.py) 内有 `RenderObject3D`、相机 3D 框投影和 BEV GT/预测绘制；旧路径、输入格式与裁剪标定需要适配，不能直接视为开箱即用。
- [util_ui_vis.py](../utils/util_ui_vis.py) 中有内外参与点云相机投影工具；本地 `resources/cam_calib/` 存在标定材料。
- `/home/hongsheng/k_radar_dataset` 中抽查了 34、39、48、53 序列，均存在 `cam-front`、`info_label`、`os2-64` 和 `info_calib`，具备真实场景素材。
- [patch_dec_a2_fusion.py](../models/fuser/patch_dec_a2_fusion.py) 中已有每 patch gate 及 patch 网格/米制坐标定义，可以对选定帧读取完整输出并还原为空间图。
- [export_taskdec_patch_pca.py](../tools/analysis/export_taskdec_patch_pca.py) 当前只保存选中的前景/背景 patch gate。完整 BEV 热力图应重新导出选定帧的全 patch gate；不能把未采样位置填零当成完整预测。

这项工作主要是少量选定帧的模型推理、标定对齐和可视化导出，无需为生成图重新训练。论文中的照片、检测框和热力图应来自实际数据与模型输出。

9 月 10 日制作更新：已用 Robust model_0、RLC、v1.0 test 对七种天气各 3 帧进行推理，保存每帧 16×90 的完整 gate。Fig.4 暂选 seq13/rdr00146（阴天）与 seq25/rdr00154（雨夜），使用完整 0–72 m、±6.4 m ROI、统一 [0,1] 色标和原始 0.8 m patch。绿色框为 GT，融合器预测 gate 时不接收 gt_boxes；相机只作场景参照。候选选择、空间对齐、数值核查、运行说明及复现命令见 [Fig.4 导出说明](../analysis_exports/taskdec_bev_gate_fig4_260910/README.md)。尚未编译完整 LaTeX 稿。
