# ObjDec 英文 LaTeX 稿（2026-09-26更新）

将现有 Introduction、Related Work、Method、Experiments 和附录 A–H 组织为可复制、可编译的英文 LaTeX。保留原Markdown与独立章节。正文采用四张图，原Fig.5移至附录E；本轮同步至原仓库，不新增训练。

## 从哪里开始

- `sections/related_work.tex`：相关工作，两节。
- `sections/introduction.tex`：9 月 24 日按作者要求重写的引言，以 Dec 为核心、Obj 为检测指向，六段逐步展开，在论述后集中引用，不逐篇介绍其他方法。
- `introduction_bilingual.md`：当前引言的中英文对照阅读版。
- `sections/methods.tex`：方法，四节、七组公式。
- `sections/experiments.tex`：实验，五节，引用四张正文表和相关图件。
- `sections/conclusion.tex`：9 月 25 日新增的单段结论，概括解耦、目标引导与实验证据。
- `appendix.tex`：附录入口，依次引入 `sections/appendix_a.tex` 至 `appendix_h.tex`。
- `references.bib`：全稿统一的 36 条文献，包含引言原来的 14 条，引用键保持兼容。
- `tables/`：四张正文表、原有附表及新增固定权重干预表D.2，以及一个前向计算算法。
- `figures/`：图的插入语句、英文图注和明确标注的待插入位置。
- `assets/`：自包含PDF素材。正文Fig.3／4与附录E七张图已插入；五页完整检测候选图册保留为归档，不重复插入论文。
- `preview.tex` / `preview.pdf`：合并阅读和编译检查用稿。
- `conversion_manifest.json` / `validation.json`：源文件与素材哈希、原始表格单元格、数值及引用检查结果。

## 在现有论文中使用

建议把 `sections/`、`tables/`、`figures/`、`assets/` 和 `references.bib` 一起放到论文主 `.tex` 同级目录，再使用：

```latex
% 导言区：对照 preamble.tex 补齐缺少的宏包及定义。
% 若会议模板已加载 natbib / hyperref / caption，不要重复加载或覆盖其选项。

% 正文：已经有 Introduction 时，从 related_work 开始。
\input{sections/introduction}
\input{sections/related_work}
\input{sections/methods}
\input{sections/experiments}
\input{sections/conclusion}

% 使用会议模板要求的 bibliography style。
\bibliography{references}

\clearpage
\input{appendix}
```

也可以直接复制章节文件里的内容。实验章末尾和附录各节末尾的 `\input{tables/...}` / `\input{figures/...}` 仍需对应文件，或者将它们的内容一并展开复制。所有相对路径以主 `.tex` 所在目录为基准。

只需加载**一份** `references.bib`。它已包含 `objdec_introduction_references_260924.bib` 的全部条目；不要同时加载两份，以免重复引用键。若接入已有参考文献库，按键合并即可。

`appendix.tex` 自带 `\appendix`，且将公式、表格、图片按 A.1、B.1 等自动编号；已有附录入口时不要重复执行。`preamble.tex` 定义了 `algorithm` 浮动体；若模板已定义该环境，保留模板定义并删除重复定义。

## 本地编译

```bash
cd /home/hongsheng/dec_con_asf/results/objdec_latex_260924
pdflatex -interaction=nonstopmode -halt-on-error preview.tex
bibtex preview
pdflatex -interaction=nonstopmode -halt-on-error preview.tex
pdflatex -interaction=nonstopmode -halt-on-error preview.tex
```

预览使用普通 `article`，不是 ICLR 投稿模板。预览页数包含全部附录、全尺寸图件及占位框，不能用来判断正文是否满足会议页数要求；正式版仍需在会议模板中安排浮动体和压缩版面。

## 转换中处理的内容

1. Markdown 网页链接及 `[ASF]` 等占位统一为 `\citep` / `\citet`；保留作者–年份风格。
2. 公式去掉手写 `\tag`，章节、公式、表格及图件使用 `\label` / `\ref` / `\eqref`。外部文献的 Table 3 / Table 4 保留外部编号，不误连成本稿表格。
3. 原有数值、NR、缺失项、公开结果与本地结果分组均保留。表格中的增益仍以未舍入记录为依据，不用展示值重新计算。正文不含 Concat 的主表安排沿用原稿，附录仍完整保留该对照。
4. 附表 C.4 和 G.3 的 a/b 面板合并到同一表号。AP 表头、百分号、下划线和数学符号改为可编译写法。
5. 引言已同步更新独立版、合并版和中英文阅读版：多传感器检测 → 空间交互与自适应融合 → 解耦的必要性 → 目标引导的必要性 → ObjDec → 实验证据 → 三点贡献。Dec 构成架构核心，Obj 为解耦的学习与使用提供检测指向。引用按论述集中放置，逐方法介绍保留在 Related Work；后者两节的收束段也已同步调整。实验增益继续明确对应官方权重的归档结果。修改前版本保存在 `../draft_history/objdec_before_dec_priority_260924/`。
6. 全天气 PCA 图使用 9 月 23 日蓝／绿／紫版本，因此图注同步修正为相机蓝、LiDAR 绿、雷达紫。高维余弦分布采用灰／绿／黄表示Input／Shared／Specific（表征类型），与传感器蓝／绿／紫的编码含义不同；图注保持对应。
7. 算法中模态权重预测的输入说明补足原 token，避免将其简写为只读取 shared/specific。数学定义仍以方法式（3）为准。
8. 中文说明、素材索引、内部路径和旧进度日志不进入英文论文正文。科研结论、协议差异和原稿中适用范围的说明仍保留。

## 沿用原稿的待补项

以下位置以 `\drafttodo{...}` 显式显示，不能直接作为完整定稿提交：

- **v1 选模记录**：1,000 样本的来源或 ID/构建规则、候选 checkpoint、选择指标及平局规则。见附录 B.2；正文和消融表也保留关联说明。
- **Fig.1 / Fig.2**：需放入你最终确认的动机图和架构图。本包保留位置，不擅自选择旧的架构草图。
- **Fig.3已完成接入**：选定的正常／大雪帧均值PCA（无页脚），不再是待补组合图。
- **可选验证曲线**：最终五组曲线尚未制作，已从当前编译稿中移除占位；旧`figure_g1.tex`仅保留作为编辑模板，已有训练结果不受影响。

Fig.4采用9月25日三场景紧凑稿；原Fig.5紧凑检测对照改放附录E.6。全天气 PCA 和 gate 图在缩至会议版心后仍需检查字号；可将七天气分为续图，但应保持相同坐标和色标。

附录D.3与表D.2已纳入完成的K-Radar v1固定权重干预；同时保留context增量影响很小的观察。Appendix E补充帧级匹配／错配对照，限定高余弦的解释。

## 参考文献核查

完整条目的原始论文或正式会议来源 URL 均在 `references.bib`。引言已有 14 条及其核查说明见上一轮 `../objdec_introduction_latex_notes_260924.md`。

本次补齐 TransFusion、CMT、RCBEVDet、WCBR、DSN、MISA、DeCUR、AW-MoE、VoD、PointPillars、LSS、ResNet，并合并已有 CCF、SRF、MultiLoReFT、LMD。关键处理：

- ASF 按正式 NeurIPS 2025 条目；L4DR 按 AAAI 2025 期刊式会议条目。
- VoD 按 IEEE Robotics and Automation Letters 2022，7(2):4961–4968，不误记为 CVPR。
- WCBR、AW-MoE、MultiLoReFT 保留 arXiv 预印本状态，未补造会议、页码或 DOI。
- RAF 的 ECCV 2026、CCF 的 CVPR 2026 状态遵循作者公开记录；SRF 的 IV 2026 状态按作者实验室页面。未补造尚未核实的 proceedings 页码。
- V2X 公开参考行注明来自数据集作者论文 Table 4；VoD 两条公开行注明来自 L4DR 论文 Table 3，避免把转引数值写成本地复现。

转换脚本保存在项目 `tools/analysis/convert_objdec_paper_latex_260924.py`。重新运行会重生成本目录的章节、表格、图注和参考文献；开始人工改稿后不要直接重跑覆盖修改。

## 2026-09-25 更新

Method 总述及消融讨论已按 Dec 为核心、Obj 为检测指向做局部调整，七组方法公式和全部表格数值保持不变。新增 Conclusion、AdamW 引用及表 4(a) 的原始架构引用；共用文献库为 36 条。独立粘贴版、四张独立正文表和引用核查链接见 [本轮使用说明](../objdec_methods_experiments_latex_notes_260925.md)。不要重新运行旧转换脚本覆盖本轮人工改稿。

## 2026-09-26 协作版本

[正文四图与附录图件清单](../objdec_figures_main_appendix_plan_260926.md)。独立英文章节与合并稿保持一致；实验、附录中英文来源同步。主表1–4数值及Method公式保持不变。`validation.json`检查可达LaTeX输入、引用、原表数据、新增干预表及图件哈希；未插入的历史候选页不计入当前正文或附图数。
