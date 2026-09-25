# ObjDec Introduction：LaTeX 使用与引用核查

日期：2026-09-24。当前版本按作者确认的 **Dec 为核心、Obj 引导其服务于检测** 的定位重写为六段引言和三条贡献：**多传感器检测 → 已有空间交互与自适应融合 → 为什么需要解耦 → 为什么需要目标引导 → ObjDec 架构 → 实验证据 → 三点贡献**。不逐篇介绍其他方法，引用集中放在相应论述后。原 [9 月 17 日中英文初稿](taskdec_introduction_bilingual_initial_260917.md) 保留为历史版本，当前稿以以下 `.tex` 及中英文对照为准。本轮修改前版本另存于 备份目录（本地历史备份：`draft_history/objdec_before_dec_priority_260924/`）。只在本地修改。

## 可直接使用的文件

- [英文正文](objdec_introduction_260924.tex)：包含 `\section{Introduction}`、章节标签和正文，不包含导言区、文档环境或参考文献列表。
- [中英文对照阅读版](objdec_introduction_bilingual_260924.md)：六段逐段对应，含三点贡献；阅读版省略引用标记，完整引用保留在 LaTeX 中。
- [共用 BibTeX](objdec_introduction_references_260924.bib)：2026-09-25 已补齐 Related Work、方法、实验及附录所需引用，共 36 条去重文献；引言引用 14 篇，Related Work 引用 23 篇，各章共用这一份。
- [Related Work 英文 LaTeX](objdec_related_work_260925.tex)：可直接接在引言之后，沿用当前 Dec 为核心、Obj 引导的定位。
- [当前完整编译预览](objdec_latex_260924/preview.pdf)：验证扩充后的共用文献库。
- [编译预览 PDF](objdec_latex_260924/preview.pdf)：用于检查文本、引用和数学符号；采用普通 article 排版，不代表 ICLR 模板中的最终占页。
- [预览源文件](objdec_latex_260924/preview.tex)。

## 粘贴到论文

将英文 `.tex` 的内容直接粘贴到 Introduction 所在位置，或者将文件放入论文目录后使用：

```latex
\input{objdec_introduction_260924}
```

正文使用 natbib 的 `\citep{key1,key2,...}` 在论述后集中引用，不以作者或方法名逐篇展开。若论文模板已经加载 natbib，无须重复加载；否则在导言区加入 `\usepackage{natbib}`。

将配套 `.bib` 的条目合并到论文已有参考文献库，保留模板原有的参考文献样式。若尚无参考文献库，可在论文末尾的参考文献位置使用：

```latex
\bibliography{objdec_introduction_references_260924}
```

已有参考文献库时，合并条目后继续使用原来的 `\bibliography{...}`，不要再建立第二套 References。新文件沿用旧近期文献库中已有的 citation keys，合并时相同 key 只留一份。若同一篇论文已经使用其他 key，统一 key 后再引用，避免重复条目。

原稿的讨论记录、实验待办、图号规划和使用说明不进入 `.tex` 正文。本版没有插入尚未确定的图表标签，避免出现未定义的交叉引用。

## 本次引用和行文调整

1. 引言按问题推进，不逐篇介绍其他方法。第二段概括空间交互与自适应融合的进展；第三段先说明共享信息与模态特有信息的不同作用，确立解耦动机；第四段再说明目标区域监督与目标相关融合如何让解耦服务于检测。
2. 补齐原近期 `.bib` 未覆盖的 BEVFusion、3D-LRF、L4DR、ASF、DecAlign 和 FactorCL，并补充 K-Radar、V2X-Radar 的数据集引用。
3. ASF 使用 NeurIPS 2025 正式题名；L4DR 使用 AAAI 2025 发表记录；BEVFusion 对应原稿链接中的 Liu 等 ICRA 2023 论文。它们的预印本年份与最终发表年份不再混用。
4. 背景、已有融合进展、表征学习动机、实验数据来源分别使用集中引用；不将多篇文献拆成方法清单。“一致性不自动等于目标相关性”是本文的动机分析，不将既有文献当作本模型 gate 效果的直接证据。
5. ObjDec 段以表征解耦构建融合架构为主线，将 gate、模态权重和 context 写为解耦表征参与融合的实现机制。贡献顺序改为“解耦融合架构—目标引导的学习与使用—实验证据”。ASF 基础机制的归属继续在 Related Work 和 Method 中明确说明；不将 shared/private 分支本身写成首次提出，也不声称已有方法均忽略前景或无法自适应。
6. 保留原有 v1 数值及 `conf=0.3` 前提。引言中的 released fusion baseline 对应**官方 ASF 权重关联的归档结果**，不是新完成的同步逐帧重评测，也不是直接拿论文表中数字相减；具体名称及来源在实验部分明确。提升写作 percentage points，参数增幅写作百分比。
7. 将 V2X 的 architecture transfer 明确为在目标数据集上训练和测试；不写成零样本迁移。v2 仍称 decoupled-control variant。
8. 统一使用 ObjDec / object context / modality contribution。表征映射在所有 patch 上运行，目标区域限定解耦训练约束的作用位置；推理控制信号从输入特征预测，不需要 GT 或先验检测框。
9. 同步更新 [合并稿中的引言](objdec_latex_260924/sections/introduction.tex)、两份 PDF 预览及源码包。独立引言与合并稿正文一致，后者只调整 BibTeX 文件名并保留 Fig.1 插入语句。Related Work 中英文两节收束段与此定位一致；方法和实验章节未改写。

## 文献核查与 citation keys

| 文献 | key | 核验来源与版本 |
| --- | --- | --- |
| BEVFusion | `liu2023bevfusion` | [作者 arXiv 记录](https://arxiv.org/abs/2205.13542)，ICRA 2023；不是另一篇同名 CVPR 2023 论文 |
| MoME | `park2025mome` | [CVPR 2025 正式页面](https://openaccess.thecvf.com/content/CVPR2025/html/Park_Resilient_Sensor_Fusion_Under_Adverse_Sensor_Failures_via_Multi-Modal_Expert_CVPR_2025_paper.html) |
| RobuRCDet | `yue2025roburcdet` | [ICLR 2025 正式页面](https://proceedings.iclr.cc/paper_files/paper/2025/hash/21dabaacda3edba8bb281da45d7cbc17-Abstract-Conference.html) |
| 3D-LRF | `chae2024threedlrf` | [CVPR 2024 正式页面](https://openaccess.thecvf.com/content/CVPR2024/html/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.html) |
| L4DR | `huang2025l4dr` | [AAAI 2025 正式记录](https://ojs.aaai.org/index.php/AAAI/article/view/32397)，39(4):3806–3814；按出版记录使用 `@article` |
| DLRFusion | `chae2025dlrfusion` | [ICCV 2025 正式页面](https://openaccess.thecvf.com/content/ICCV2025/html/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.html) |
| ASF | `paek2025asf` | [NeurIPS 2025 正式页面](https://proceedings.neurips.cc/paper_files/paper/2025/hash/80bd5c815cdb033ac23eb27605adaaba-Abstract-Conference.html) |
| RAF | `park2026raf` | [作者 arXiv v1 记录](https://arxiv.org/abs/2607.04587)，作者注明 ECCV 2026；未填未经核实的会议页码或 DOI |
| DecAlign | `qian2026decalign` | [ICLR 2026 正式 PDF](https://proceedings.iclr.cc/paper_files/paper/2026/file/f7f5f501282771c96bb3fedcc96bedfe-Paper-Conference.pdf)，作者为 Qian、Xing、Li、Zhao、Tu |
| SPFD | `wang2026spfd` | [CVPR 2026 正式 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Wang_Beyond_Duality_A_Hybrid_Framework_of_Leveraging_Shared_and_Private_CVPR_2026_paper.pdf)；本轮 HTML 页面访问失败，使用 CVF PDF 核验 |
| FactorCL | `liang2023factorcl` | [NeurIPS 2023 正式页面](https://papers.neurips.cc/paper_files/paper/2023/hash/6818dcc65fdf3cbd4b05770fb957803e-Abstract-Conference.html) |
| Feature Causality Decomposition | `liu2025featurecausality` | [NeurIPS 2025 正式页面](https://proceedings.nips.cc/paper_files/paper/2025/hash/55123f38c9f4acf417335cff41be6e27-Abstract-Conference.html)，作者 Ye Liu、Zihan Ji、Hongmin Cai |
| K-Radar | `paek2022kradar` | [作者 arXiv 记录](https://arxiv.org/abs/2206.08171)，NeurIPS 2022 Datasets and Benchmarks |
| V2X-Radar | `yang2025v2xradar` | [NeurIPS 2025 正式页面](https://proceedings.nips.cc/paper_files/paper/2025/hash/a501f3238029713afdad57ce7924667a-Abstract-Datasets_and_Benchmarks_Track.html)，按正式页面的 13 位作者记录，包含 Kai Wu |

## 本地验证

预览使用 `pdflatex → bibtex → pdflatex → pdflatex` 编译。Citation key、条目数量和编译检查结果记录在 [validation.json](objdec_latex_260924/validation.json)。这里的通用预览只验证正文与引用可用性，最终排版继续使用论文已有模板。

## 2026-09-26协作更新

本文件保留引言与Related Work的核查记录；方法、实验、结论及附录的当前状态见[完整LaTeX说明](objdec_latex_260924/README.md)。当前预览已同步全部章节，正文四图、附录E七图，共用36条参考文献。
