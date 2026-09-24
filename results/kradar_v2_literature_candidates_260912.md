# K-Radar v2 文献结果与可比性核对

日期：2026-09-12。目的：为 DecControlled Strong 的 v2 扩展实验补充文献参照。本次检索并核对论文、补充材料、官方配置；没有运行模型。以下为已确认的候选，不声称穷尽全部论文。

## 1. 可用于讨论的文献结果

表中均为原文报告值，单位为 AP 点；`—` 表示本轮没有从该来源取得对应值，不表示 0。同一方法的不同来源保留独立行，不拼成一个模型。**本表是文献参照，不是与我们 conf=0.3 结果统一复现后的排行榜。**

| 方法及结果来源 | 输入 | 设置 | 3D@0.3 Sedan | 3D@0.3 Bus/Truck | 3D@0.5 Sedan | 3D@0.5 Bus/Truck |
|---|---|---|---:|---:|---:|---:|
| ASF，NeurIPS 2025 正文 Table 3 / 附录 Table 11 | C+L+R | benchmark v2.0，宽 ROI | 79.3 | 60.4 | 52.9 | 31.6 |
| WRCFormer，arXiv:2512.22972v2，Table I | C+R | 原文称 label v2.0；ROI/置信度细节未完全核定 | 56.4 | 38.7 | — | — |
| InterFusion，REL Table 2 中的基线结果 | L+R | REL 的 benchmark v2.0，宽 ROI | — | — | 50.9 | 35.5 |
| 3D-LRF，REL Table 2 中的基线结果 | L+R* | REL 的 benchmark v2.0，宽 ROI | — | — | 51.4 | 36.8 |
| L4DR，REL Table 2 中的基线结果 | L+R | REL 的 benchmark v2.0，宽 ROI | — | — | 51.2 | 37.6 |
| REL，AAAI 2026 Table 2 | L+R | 原文 benchmark v2.0，宽 ROI | — | — | 53.0 | 40.0 |
| REL with L4DR，AAAI 2026 Table 2 | L+R | 同上，另一骨干上的变体 | — | — | 52.5 | 41.5 |
| L4DR，arXiv:2408.03677v6，Table 10 | L+R | 原文称 v2.0；当前官方配置为 label v2.1 | 75.8 | 59.7 | — | — |
| AttFuse with MDD，V2X-R / CVPR 2025 Table 6 | L+R | label v2.1，K-Radar 单车实验 | 74.03 | 54.58 | — | — |

*3D-LRF 的模态列沿用 REL 表中的 L+R 标记。原始 3D-LRF 另以图像提取天气信息，不应据此声称其实现完全不使用相机。

来源：[ASF 正文](https://papers.nips.cc/paper_files/paper/2025/file/80bd5c815cdb033ac23eb27605adaaba-Paper-Conference.pdf#page=8)、[ASF 附录 ZIP](https://papers.nips.cc/paper_files/paper/2025/file/80bd5c815cdb033ac23eb27605adaaba-Supplemental-Conference.zip)、[WRCFormer Table I](https://arxiv.org/html/2512.22972v2#S4)、[REL Table 2](https://ojs.aaai.org/index.php/AAAI/article/download/37916/41878#page=5)、[L4DR Table 10](https://arxiv.org/html/2408.03677v6)、[V2X-R Table 6 与附录 §9.4](https://arxiv.org/html/2411.08402v4)。

REL Table 2 同时给出以下 BEV@0.5 Total，保留供完整指标表使用：

| 方法 | Sedan | Bus/Truck | 两类算术平均 3D@0.5（由上表计算） |
|---|---:|---:|---:|
| InterFusion | 68.3 | 50.4 | 43.20 |
| 3D-LRF | 68.4 | 53.2 | 44.10 |
| L4DR | 68.9 | 51.8 | 44.40 |
| REL | 76.6 | 53.6 | 46.50 |
| REL with L4DR | 69.1 | 58.2 | 47.00 |

这些平均数是本记录根据已发表的分类别 AP 计算的摘要，不是论文额外报告的官方指标。REL 正文明确宽 ROI 为 x=[0,72]、y=[−16,16]、z=[−2,7.6]，两类，IoU=0.5；但置信度截断、空 GT 帧处理及标签文件版本仍需进一步统一后才能计算对我们的公平差值。其[官方仓库](https://github.com/TongTianxu/REL)截至本轮读取只有待发布代码说明。[REL 原文](https://ojs.aaai.org/index.php/AAAI/article/download/37916/41878#page=5)

## 2. 确实涉及 v2，但不宜直接填入上述双类别表的论文

| 论文 | 已确认内容 | 入表处理 |
|---|---|---|
| DPFT，IEEE T-IV，2024 online；arXiv:2404.03015v2 | Table II 的 C+R 3D mAP=50.5，使用 revision v2.0；公开配置只启用 Sedan，ROI y=±6.4、z=[−2,6] | 作为窄 ROI / 单类别的文献参照，不能直接当作宽 ROI 两类平均 |
| SRF，IV 2026 | 作者实验室页面明确 v2.0 的 3D mAP=54.3；输入为双目相机+4D Radar tensor | 已确认使用 v2；尚未取得完整分类别表及阈值/ROI，暂不填 Sedan 或 Bus 列 |
| DinoRADE，CVPR 2026 DriveX Workshop | Tables 2–4 使用 label v2.1、窄 ROI、五类；Table 2 的 Sedan/Bus AP3D 为 71.38/54.92，五类平均 36.99 | 与宽 ROI、v2.0、两类设置分列；所查正文未明确给出 IoU 数值，不擅自补写 @0.3 |
| RADE-Net，IV 2026 | DinoRADE Table 3 列出其五类设置结果：Sedan/Bus AP3D=56.75/40.99 | 这是 DinoRADE 表中的报告来源，不能当作 RADE-Net 原论文在我们协议下的结果 |

来源：[DPFT 原文 Table II](https://arxiv.org/html/2404.03015v2#S4)、[DPFT 官方配置](https://raw.githubusercontent.com/TUMFTM/DPFT/main/config/kradar.json)、[SRF 作者实验室页面](https://ave.kaist.ac.kr/2026/02/12/srf-stereo-radar-fusion-for-3d-object-detection-in-adverse-weather-conditions/)、[DinoRADE 正文](https://openaccess.thecvf.com/content/CVPR2026W/DriveX/papers/Leitgeb_DinoRADE_Full_Spectral_Radar-Camera_Fusion_with_Vision_Foundation_Model_Features_CVPRW_2026_paper.pdf#page=6)、[RADE-Net / DinoRADE 官方仓库](https://github.com/chr-is-tof/RADE-Net)。

## 3. 核对中发现的具体区别

- **DPFT 的二手分类别数字不能直接抄。**WRCFormer Table I 将 DPFT 写成 Sedan=50.5、Bus=33.6；DPFT 原文 Table II 仅给出 mAP=50.5，公开配置把 Bus/Truck 映射为 −1。本轮没有在 DPFT 原文中确认 33.6 的来源，因此不将其列为 DPFT 原论文的 Bus 结果。WRCFormer 自身结果仍按其原文收录。[DPFT](https://arxiv.org/html/2404.03015v2)、[配置](https://raw.githubusercontent.com/TUMFTM/DPFT/main/config/kradar.json)、[WRCFormer](https://arxiv.org/html/2512.22972v2)
- **L4DR 的论文和当前仓库版本需区分。**arXiv v6 的 v2 结果在 Table 10（不同稿件可能编号不同）；当前官方配置是 `label_version: v2_1`、宽 ROI。官方 `v2.1.txt` 只列 Sedan，Total 3D@0.3=77.95，与论文 Table 10 的 75.8 不是同一条结果；不把两者混合成双类别行。[论文](https://arxiv.org/html/2408.03677v6)、[官方配置](https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/configs/cfg_PP_L4DR.yml)、[官方日志](https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/logs/v2.1.txt)
- **3D-LRF 的 v2 数字来自后续 REL 的比较。**本轮检查 CVPR 2024 正文和补充材料，确认原文核心实验为 Sedan；没有找到其自行报告的 v2 双类别表。因此标为“REL Table 2 中的基线”，而非“3D-LRF 原论文 v2 结果”。[3D-LRF 正文](https://openaccess.thecvf.com/content/CVPR2024/papers/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.pdf)、[补充材料](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Chae_Towards_Robust_3D_CVPR_2024_supplemental.pdf)
- **ASF 公开数字不能替换我们同阈值比较中的 ASF 行。**正文 Table 3 给 3D@0.3=79.3/60.4；我们现有 conf=0.3 归档为 74.98/58.13。另有小版本差异：附录 Table 11 的 CLR Bus 3D@0.5=31.6，而本地官方 conf=0.0 日志为 31.68299。引用论文时保留论文值，计算我们与 ASF 的增益时使用锁定的 conf=0.3 原始日志，不按单元格替换。[ASF 实验核对](asf_v2_experiment_structure_reference_260912.md)

## 4. 对当前论文表的建议

当前选定结果命名为 **DecControlled Strong (ours)**，在表注注明“Dec 家族的不含 task-context 分支的变体”。“我们的方法”可以指整个 Dec 方法家族，但这行不能让读者误以为是完整 TaskDec 架构的同一配置；不将 Strong 简写为 `TaskDec (full)`。

建议 v2 正文保留 ASF–DecControlled Strong 的同协议扩展表：两类 AP3D@0.3 和 @0.5，附录给 BEV、IoU=0.7 及全部天气/场景。若需要同时展示其他工作，使用明确分隔的“文献报告”与“统一 conf=0.3 比较”两个表块，模态与设置随行标注，不对跨块数值统一加粗排名。DPFT、SRF、DinoRADE 等协议尚不一致的候选放在相关工作或补充比较说明中。

现有证据支持：Strong 相对官方 ASF 的两类平均 3D@0.3 / @0.5 提高 0.36 / 1.48 点，说明解耦控制思路在 v2 设置仍有收益。REL 的已发表 3D@0.5 均值为 46.50 / 47.00，高于 Strong 当前的 43.05；这些不是统一协议差值，但足以说明不能据当前表宣称 v2 全面 SOTA。

后续如需扩大严格可比的主表，优先对齐 REL/L4DR 的标签、评价帧集和分数截断，并用同一评测器比较。当前任务只做资料与结果整理，不启动训练或推理。
