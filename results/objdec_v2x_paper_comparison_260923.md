# V2X论文表格与章节重组

日期：2026-09-23。正文主表聚焦代表方法，Concat保留于附录作为受控基线。此文件记录表格纳入规则和对应章节；所有原始训练、checkpoint、指标JSON与历史报告均保留。

## 1. 正文表4：两个独立面板

### (a) 公开代表方法参考

| 方法 | 模态 | Vehicle 3D | Pedestrian 3D | Cyclist 3D | Mean 3D |
| --- | --- | ---: | ---: | ---: | ---: |
| PointPillars | L | 68.80 | 38.16 | 65.24 | 57.40 |
| CenterPoint | L | 72.19 | 50.59 | 75.26 | 66.01 |
| PV-RCNN | L | 79.38 | 58.83 | 78.01 | 72.07 |
| SQDNet | L | 79.65 | 58.79 | 79.46 | 72.63 |
| BEVDepth | C | 15.47 | 8.51 | 9.46 | 11.15 |
| RPFA-Net | R | 30.44 | 10.37 | 11.98 | 17.60 |

来源：[V2X-Radar正式论文表4，NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/file/a501f3238029713afdad57ce7924667a-Paper-Datasets_and_Benchmarks_Track.pdf)，本轮重新核对Moderate、严格IoU三列。Mean由公开类别数值计算。代表方法覆盖LiDAR、相机与雷达路线，并保留原表中较强的LiDAR方法；未依据是否低于ObjDec来筛选。公开表没有对应BEV结果，不从斜杠的第二个数臆造BEV。

### (b) 本地融合方法对照

| 方法 | 模态 | Vehicle 3D | Pedestrian 3D | Cyclist 3D | Mean 3D | Mean BEV |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ASF-style | C+L+R | 84.54 | 76.17 | 83.18 | 81.30 | 85.72 |
| ObjDec | C+L+R | 84.06 | 75.94 | 84.13 | 81.38 | 86.27 |
| L4DR | L+R | 83.17 | 73.25 | 78.31 | 78.24 | 82.56 |
| ObjDec-LR | L+R | 83.87 | 74.84 | 80.24 | 79.65 | 83.81 |

本地0.16 m、80轮预算、有效batch 8，使用1,486帧去重test、Moderate AP_R40，类别IoU 0.7/0.5/0.5。按val平均3D选出的ObjDec第70轮和L4DR第80轮对应上述数值。原始来源见[完整运行总表](objdec_v2x_current_total_table_260923.md)与[指标CSV](../analysis_exports/objdec_v2x_table_snapshot_260923/metrics.csv)。9月23日上午更新：ASF-style于03:33、ObjDec-LR于03:02完成最终best/last。ASF-style按val选中第80轮，ObjDec-LR选中第75轮。

两个面板分别写明Public validation与Local test，不合并加粗排名，不跨面板计算提升。当前本地协议与公开基准的版本、样本集合及ROI尚未完全对应，具体见[协议核查](objdec_v2x_public_protocol_comparability_260919.md)。

## 2. 章节论证顺序

正文4.5已改为三段，中英文对应：

1. **目的与设置：** 在新数据集和三类目标下重新训练完整ObjDec架构，检验适用性；明确0.16 m网格、预算、split和ROI。
2. **代表方法与比较组织：** 公开单模态方法提供研究背景；直接结构比较以ASF-style/ObjDec和L4DR/ObjDec-LR两组同模态实验为主。
3. **结果与补充：** 已填齐正式test：ObjDec-LR相对L4DR平均3D/BEV提高1.41/1.25点，三模态ObjDec相对ASF-style提高0.08/0.55点。后者3D差异较小，不称显著提升；L+R三类3D和BEV均有提高。Concat、逐类BEV、best/last和空间粒度保留附录G，VoD继续放G.4。

不将C+L+R ObjDec与L+R L4DR的差值全部解释为解耦融合的收益，也不以公开参考面板支持V2X公开基准SOTA。当前证据不支持“优于所有已评测融合结构”；正文只陈述实际比较成立的结果。

## 3. 其他方法如何处理

- **M2-Fusion：** 原论文表6是恶劣天气子集、IoU 0.5/0.25/0.25；与上述严格IoU和集合不对应，暂不加入这个数值表。
- **PhD-DETR：** 前次调研已确认使用V2X-Radar-V，但完整AP表和划分未核实，不补猜测值；保留为待核查文献线索。
- **SECOND、Fade3D、SMOKE、BEVHeight系列、RDIoU：** 完整公开清单保留在[公开方法核查](objdec_v2x_public_methods_sota_audit_260920.md)。正文先选六种代表以控制篇幅。
- **3D-LRF：** 已在K-Radar主表中报告；目前没有已核实的本地V2X结果，不把K-Radar数值搬入V2X表。
- **Concat：** 从正文Table 4移出，保留附录G.1/G.2及原始记录。按val选中的0.16m ObjDec相对它低0.52/0.20点3D/BEV，附录G.3如实说明。

## 4. 修改文件与待完成项

- [实验中英文初稿](objdec_experiments_bilingual_initial_260919.md)：更新稿件状态、4.5中英文、Table 4双面板及图注、章节重组记录。
- [附录中英文初稿](objdec_appendix_bilingual_initial_260920.md)：G.3明确补充Concat受控对照及其差值，原G.1/G.2完整表保持。
- [附录提纲](objdec_appendix_writing_plan_260920.md)：同步正文／附录分工和当前完成情况。
- [来源说明](objdec_appendix_source_notes_260920.md)：补充公开表来源与本轮修改记录。

ASF-style、ObjDec-LR的final_best/final_last已完成，正文与附录已按既定val选模规则补齐。ObjDec-LR第80轮test为79.75/83.80，作为附录补充，不替换第75轮best。Figure G.1的完整验证记录已齐，图稿待制作。本文没有启动新实验或改变现有评测口径。
