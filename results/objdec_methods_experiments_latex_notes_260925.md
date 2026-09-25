# ObjDec：Method、Experiments、Conclusion 与独立表格

更新：2026-09-26。本轮同步最新章节、图件和共用文献库至原仓库。

## 可直接复制的章节

- [Method](objdec_methods_260925.tex)：四小节、七组编号公式。
- [Experiments](objdec_experiments_260925.tex)：五小节，使用四个独立表格文件。
- [Conclusion](objdec_conclusion_260925.tex)：单段结论，无新增实验数值或引用。
- [Conclusion 中英文对照](objdec_conclusion_bilingual_260925.md)。
- [共用 BibTeX](objdec_introduction_references_260924.bib)：36 条，覆盖 Introduction、Related Work、Method、Experiments 和现有附录。旧 citation keys 不变。
- [完整源码目录](objdec_latex_260924/README.md)：已同步章节、Conclusion、四张正文表、19 张附表及共用文献库。
- [完整编译预览](objdec_latex_260924/preview.pdf)：普通 article 排版，用于检查内容，不用于判断 ICLR 正文页数。

## 本轮定位调整

两章主体已符合 Dec 为核心、Obj 引导其服务于检测的逻辑，只作局部修改：

1. Method 总述先说明解耦表征构成架构核心，再说明目标区域监督、门控和上下文如何让表征参与融合；3.2 改为 “Shared and Modality-Specific Representation Decoupling”。
2. Experiments 的消融讨论先讲解耦监督，再讲前景门控、模态贡献和目标上下文。明确“去解耦监督”保留了表征分支及前向路径，不等于移除解耦架构。表格行顺序与数值保持不变。
3. 原公式、SCL 的继承归属、GT 只用于训练监督、v1/v2 变体区别、V2X 对照协议保持原定义。
4. Conclusion 概括局部表征解耦、目标引导及已报告证据，不增加零样本迁移、统计显著性或统一协议 SOTA 声称。

中英文源稿的对应段落同步更新：`taskdec_methods_bilingual_initial_260917.md`、`objdec_experiments_bilingual_initial_260919.md`。

## 表格文件

每个文件均含 `table` 环境、完整 `caption`、`label` 和表体，可以独立移动位置。

| 文件 | 内容 | 标签 |
|---|---|---|
| [table_1.tex](objdec_tables_260925/table_1.tex) | K-Radar v1 主结果 | `tab:1` |
| [table_2.tex](objdec_tables_260925/table_2.tex) | K-Radar v2 扩展设置 | `tab:2` |
| [table_3.tex](objdec_tables_260925/table_3.tex) | 组件消融 | `tab:3` |
| [table_4.tex](objdec_tables_260925/table_4.tex) | V2X 公开参考与本地融合对照，含 a/b 面板 | `tab:4`、`tab:4a`、`tab:4b` |

表 4(a) 给各方法补上原始架构论文引用，表注继续说明所有分数来自 V2X-Radar 数据集论文 Table 4，不将这些分数归为原始方法论文在 V2X 上的报告结果。两个面板仍不跨协议排名。附录表仍逐表存于 `objdec_latex_260924/tables/`。

## 放入现有 LaTeX 工程

把三个章节文件、`objdec_tables_260925/` 文件夹和共用 `.bib` 放在主 `.tex` 同级，然后使用：

```latex
\input{objdec_methods_260925}
\input{objdec_experiments_260925}
\input{objdec_conclusion_260925}

% 参考文献样式沿用会议模板，只保留一个 bibliography 命令。
\bibliography{objdec_introduction_references_260924}
```

所需宏包为 `amsmath`、`amssymb`、`booktabs`、`tabularx`、`array`、`subcaption`、`natbib`；模板已有时不重复加载。表 4 的 a/b 面板使用 `subtable` 环境。引用使用 `\citep`。

独立实验章末尾已 `\input` 四张表；移动表格时移动相应的插入语句，不要再重复粘贴表体。章节正文保留 `fig:2`—`fig:4`、`app:a`—`app:h` 等交叉引用，需与主稿图件及附录标签一致。独立章不自动载入历史图件，在注释中留下插图位置；完整源码目录保留图件及占位图，以检查所有交叉引用。

## 已有的待完成内容

表 3 的 1,000 样本选模记录仍待补齐，保留标准 LaTeX 加粗待补标记。Fig.1／Fig.2需接入作者最终手工图；Fig.3已接入选定的正常／大雪PCA，Fig.4已接入三场景紧凑版。完整附录与旧稿中的待补项不在本轮伪装为已经完成。

## 本轮新增引用核查

共用库由 25 条扩展为 36 条：先纳入完整稿已有的 AW-MoE、VoD、PointPillars、LSS、ResNet，再补六条原始方法／优化器文献。

| key | 原始来源 |
|---|---|
| `yin2021centerpoint` | [CVPR 2021 正式页](https://openaccess.thecvf.com/content/CVPR2021/html/Yin_Center-Based_3D_Object_Detection_and_Tracking_CVPR_2021_paper.html) |
| `shi2020pvrcnn` | [CVPR 2020 正式页](https://openaccess.thecvf.com/content_CVPR_2020/html/Shi_PV-RCNN_Point-Voxel_Feature_Set_Abstraction_for_3D_Object_Detection_CVPR_2020_paper.html) |
| `mo2024sqd` | [作者 SQDNet 仓库的 BibTeX](https://github.com/yujmo/SQDNet)，题名与 V2X-Radar 参考文献 [61] 对应 |
| `li2023bevdepth` | [AAAI 2023 正式页](https://ojs.aaai.org/index.php/AAAI/article/view/25233) |
| `xu2021rpfa` | [共同作者上传的完整论文](https://www.researchgate.net/publication/355607897_RPFA-Net_a_4D_RaDAR_Pillar_Feature_Attention_Network_for_3D_Object_Detection)；IEEE 页面要求 JavaScript，使用作者 PDF 核对作者、题名、会议和 DOI，页码另与数据集论文参考文献 [40] 交叉核对 |
| `loshchilov2019adamw` | [ICLR 2019 原文](https://openreview.net/pdf?id=Bkg6RiCqY7) |

V2X 表格数值出处保留为[数据集正式论文](https://proceedings.neurips.cc/paper_files/paper/2025/file/a501f3238029713afdad57ce7924667a-Paper-Datasets_and_Benchmarks_Track.pdf)。本轮没有重新调研或修改既有论文的检测数值。

## 2026-09-26 图件与机制分析更新

正文四张图，原Fig.5移附录E.6；实验4.4及中英文源稿同步。附录E纳入全天气PCA、原始高维相似度、帧级匹配／错配控制、七天气gate及全量统计、检测对照和反例；附录D新增配对推理干预表D.2。四张原正文表的数值保持不变。完整编排见[objdec_figures_main_appendix_plan_260926.md](objdec_figures_main_appendix_plan_260926.md)。
