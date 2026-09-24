# ObjDec 图表与论文协作指南

更新：2026-09-24。用于协作者看代码、改图及完善论文；当前材料仍为工作稿。

## 先读这几份

1. [摘要](../results/taskdec_abstract_initial_draft_260917.md)：问题、架构和贡献概览。
2. [方法](../results/taskdec_methods_bilingual_initial_260917.md)：正文符号及真实前向关系。
3. [主图接线核查](../analysis_exports/objdec_architecture_redesign_260922/CENTERED_REVISION.md)：画图时优先遵循此文件，早期生成图仅作布局参考。
4. [实验初稿](../results/objdec_experiments_bilingual_initial_260919.md)与[附录初稿](../results/objdec_appendix_bilingual_initial_260920.md)：正文／附录分工。
5. [9月24日主模型推理干预结果](../results/objdec_kradar_v1_interventions_results_260924.md)：最新机制结论，部分旧稿尚需同步。

论文题目：**Decoupling to Fuse: Learning Shared and Modality-Specific Representations for Multi-Sensor 3D Object Detection**。
文中方法名统一为 **ObjDec**；代码中的TaskDec、task以及历史文件名暂不批量重命名。

## 六部分初稿

| 部分 | 文件 |
| --- | --- |
| Abstract | [中英文摘要](../results/taskdec_abstract_initial_draft_260917.md) |
| Introduction | [中英文引言](../results/taskdec_introduction_bilingual_initial_260917.md) |
| Related work | [中英文相关工作](../results/taskdec_related_work_bilingual_initial_260917.md) · [2025–2026 BibTeX](../results/taskdec_recent_references_2025_2026_260917.bib) |
| Method | [中英文方法](../results/taskdec_methods_bilingual_initial_260917.md) |
| Experiments | [中英文实验](../results/objdec_experiments_bilingual_initial_260919.md) |
| Appendix | [中英文附录](../results/objdec_appendix_bilingual_initial_260920.md) · [提纲](../results/objdec_appendix_writing_plan_260920.md) · [来源备注](../results/objdec_appendix_source_notes_260920.md) |

`results/`中还保留选模、诊断和阶段性讨论。文件名日期是创建日期，不意味着之后未更新；正文中的“待补”与旧状态需按下面的最终结果记录核对。

## 图稿与可编辑素材

| 用途 | 入口 | 当前状态 |
| --- | --- | --- |
| 动机图 | [真实样本版本](../analysis_exports/objdec_motivation_new_samples_260922/README.md) · [设计及图注](../analysis_exports/objdec_motivation_comparison_260922/design_and_captions.md) | 多个K-Radar样本候选，含SVG及输入／输出小图 |
| 主架构图 | [最新手工参考图](../cb40887aca547bfc940ba77ab865ed6e.png) · [接线说明](../analysis_exports/objdec_architecture_redesign_260922/CENTERED_REVISION.md) | 手工稿待补loss；早期PNG不作为实现依据 |
| 主图Shared／Specific插图 | [纯散点素材](../analysis_exports/objdec_pca_points_only_260924/README.md) | 点面积3倍、alpha=0.95，无轴／图注，透明PNG和SVG |
| Object context局部图 | [完整例图SVG](../analysis_exports/objdec_context_vector_example_260924/objdec_object_context_example.svg) · [纯向量条SVG](../analysis_exports/objdec_context_vector_example_260924/objdec_context_vector_asset.svg) | 中性色向量条，可直接插入PPT |
| PCA、直接高维相似度、全天气gate | [统一配色完整清单](../analysis_exports/objdec_visuals_blue_green_purple_260923/README.md) | PNG／PDF／SVG及统计来源 |
| 实际检测对照 | [Fig.4/5说明](../analysis_exports/objdec_fig4_fig5_260919/README.md) · [ASF/ObjDec成对预览](../analysis_exports/objdec_fig4_fig5_260919/fig5_asf_objdec_detection_draft.png) · [雪天与反例](../analysis_exports/objdec_fig4_fig5_260919/fig5_snow_and_counterexample.png) | 当前草图及选择说明 |

统一传感器配色：Camera **蓝 #4A9EEB**、LiDAR **绿 #58B77A**、4D Radar **紫 #9672D0**。
`z`来自融合描述，用中性灰蓝向量条，避免被误读成LiDAR特征。
PCA插图用灰虚线连接`c/u`，高维表征实线进入后续计算；PCA不是网络算子。
示意色块不是实测激活；真实结果图保留其样本来源、投影和统计口径。

主图待补的监督：`Lc`连接跨模态shared，`Lu`连接跨模态specific，`Lsep`连接同模态c/u；`Lg`连接前景预测；`Lctx`连接生成z之前的objectness预测；`Ldet`连接检测头输出。GT标签仅进入训练损失。
Token modulation应含固定系数lambda；模态softmax贡献alpha与实际缩放w不同。详见接线说明。

## 结果与表格从哪里取

| 证据 | 最新记录与用途 |
| --- | --- |
| K-Radar v1主结果 | [conf=0.3主表](../results/paper_main_table_kradar_v1_conf0_3_draft_260901.md) · [协议核查](../results/taskdec_main_protocol_audit_vs_kradar_official_260910.md) |
| 主模型gate／context推理干预 | [完整8组、6项AP、七天气及分析](../results/objdec_kradar_v1_interventions_results_260924.md) |
| K-Radar v2 | [匹配训练记录](../results/taskdec_v2_matched_training_260915.md) · [对齐天气／IoU结果](../results/paper_kradar_v2_weather_l4dr_table10_260912.md) |
| V2X正文泛化 | [最终总表](../results/objdec_v2x_current_total_table_260923.md) · [正文两面板组织](../results/objdec_v2x_paper_comparison_260923.md) · [机器可读CSV](../analysis_exports/objdec_v2x_table_snapshot_260923/metrics.csv) |
| VoD附录 | [现有EAA/DC及逐类完整表](../results/objdec_vod_current_tables_260922.md) |
| 缺模态／退化 | [v1](../analysis_exports/taskdec_v1_availability_completion_260918/results.md) · [v2及ASF表3对照](../results/taskdec_v2_availability_vs_asf_table3_260918.md) |
| V2X补充推理 | [结果及论文价值](../results/objdec_inference_only_results_and_paper_value_260923.md) |

解释边界：

- K-Radar v1的gate均值化／打乱造成明显退化，支持空间对应关系的重要性；不能把固定权重干预降点写成重新训练消融的增益。
- 主模型query与output context增量同时关闭，总体3D@0.3／BEV@0.5仅下降约0.015／0.009点；不能写成各路径均有显著独立收益。
- v2表中的DecControlled Strong是早期变体，不能把它改名成与v1完全相同的权重或架构。
- V2X公开表和本地实验的split／ROI／协议不同，应分面板报告。当地同模态对照是ASF-style vs ObjDec、L4DR vs ObjDec-LR。Concat记录保留于附录。
- VoD中EAA/DC不是3D/BEV，官方AP11与KITTI AP_R40也不是同一套指标；不跨轮次拼接各指标最佳值。

## 代码入口

- [主ObjDec融合实现](../models/fuser/patch_dec_a2_fusion.py)：表征映射、gate、模态评分、objectness、context及辅助损失。
- [ASF交互基础](../models/fuser/a2_fusion.py)、[集成检测器](../models/skeletons/fusion_base_integrated.py)。
- [v1主配置](../configs/ASF_task_dec_controlled_robust_v1_0.yml)。
- [V2X数据和模型](../v2x_taskdec/)、[0.16 m实验](../analysis_exports/v2x_grid016_260918/run.py)、[ASF-style/LR实验](../analysis_exports/v2x_grid016_controls_260919/run.py)。
- [VoD局部编码配置](../vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920.yaml)、[适配锚框配置](../vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Anchors_260921.yaml)。
- [绘图工具](../tools/analysis/)、[K-Radar推理干预](../analysis_exports/objdec_kradar_v1_interventions_260923/run.py)。

## 新电脑上可以直接做什么

查看中英文MD稿、用PPT／矢量软件编辑已导出的SVG、核查JSON/CSV结果，都不需要GPU。
Object-context示意图只需Python和Matplotlib，可从仓库根目录运行：

```bash
python analysis_exports/objdec_context_vector_example_260924/draw_context_example.py
```

数据驱动的PCA／gate重绘依赖本机缓存，缓存路径与来源写在对应README／manifest中；本次不上传权重、完整数据集、特征数组和逐帧预测缓存。已导出的PNG/SVG/PDF可以直接编辑。
一些实验启动器保留了开发机绝对路径、指定GPU号和源码哈希校验；在新机器上运行前需要配置资源，不把这些归档启动器当作开箱即用安装包。
旧实验记录中的绝对文件链接只在原工作站有效，本指南及根README使用仓库相对链接。
