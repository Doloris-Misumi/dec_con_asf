# ObjDec 正文与附录图件编排（2026-09-26）

已采用：正文四张图。核心叙述为 Dec（局部共享／特有表征组织）→ Obj（目标引导其学习与融合）。原 Fig.5 改放附录E，保留同场景检测证据和反例。

## 正文

| 编号 | 内容 | 文件／状态 |
|---|---|---|
| Fig.1 | 动机图 | 作者最终手工版待接入；LaTeX明确占位 |
| Fig.2 | 主架构图 | 作者最终手工版待接入；LaTeX明确占位 |
| Fig.3 | 正常／大雪的Input、Shared、Specific帧均值PCA | `objdec_latex_260924/assets/figure3.pdf`，已接入；高维相似度另在附录 |
| Fig.4 | 三个场景的相机预测、完整BEV/gate、gate局部放大 | `objdec_latex_260924/assets/figure4.pdf`，已接入；不再称七天气正文图 |

正文表1–4保留K-Radar v1、v2、组件消融和V2X结果，数值不变。

## 已插入附录E的图

| 当前编号 | 内容 | LaTeX图文件 | 图标签 |
|---|---|---|---|
| E.1 | 全天气帧均值PCA | `figures/figure_e1.tex` | `fig:e1` |
| E.2 | 原始256维匹配patch余弦的逐帧分布 | `figures/figure_e2.tex` | `fig:e2` |
| E.3 | 帧均值向量同帧／错配与天气中心化对照 | `figures/figure_e_correspondence.tex` | `fig:e-correspondence` |
| E.4 | 七天气gate选例 | `figures/figure_e_gate_examples.tex` | `fig:e-gate-examples` |
| E.5 | 全测试集前景／背景gate统计 | `figures/figure_e_gate_statistics.tex` | `fig:e-gate-statistics` |
| E.6 | ASF／ObjDec同场景检测对照（原Fig.5） | `figures/figure_e_comparison.tex` | `fig:e-comparison` |
| E.7 | 雪天改善与定位反例 | `figures/figure_e3.tex` | `fig:e3`（保留旧标签，编号自动更新） |

以上图文件和素材在 `objdec_latex_260924/` 内自包含。E.2与E.3统计口径不同，图注已区分；不能把高shared余弦直接当成语义对齐证明。E.4的七个样本表仍为Table E.3，不对应正文Fig.4三个新样本。原20帧候选全集保留为 `assets/all_candidates.pdf`，不再重复插入论文。

附录D新增Table D.2：K-Radar v1完整八组固定权重干预及三次置换均值。使用本次配对baseline，不改历史主表；同时报告query/output增量影响很小的结果。附录F、G、H继续用表格报告缺传感器／退化、V2X／VoD、效率。

## 可选素材，不自动插入

- 同场景局部Shared／Specific高维相似度：`../analysis_exports/objdec_scene_mechanism_260924/fig4b_scene_spatial_similarity_draft.pdf`。
- 局部模态贡献系数：上述目录的 `individual/*/local_modality_scale.pdf`，不可直接视为可靠性真值。
- 完整V2X五组验证曲线：旧G.1编辑模板仍保留，但当前编译稿不插入该占位；最终曲线尚未制作，从日志汇总后再决定是否加入。

## 可复制与可编译入口

- [实验章](objdec_experiments_260925.tex)
- [完整源码说明](objdec_latex_260924/README.md)
- [编译预览](objdec_latex_260924/preview.pdf)
- [方法／实验／结论使用说明](objdec_methods_experiments_latex_notes_260925.md)

只同步文稿、图件和统计；本轮没有新增训练或改动检测预测。预览为普通article，不用于估计ICLR模板页数。
