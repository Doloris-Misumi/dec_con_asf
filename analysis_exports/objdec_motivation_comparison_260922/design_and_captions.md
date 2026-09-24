# ObjDec 动机图：已有融合—表征问题—我们的设计

日期：2026-09-22。

**最新替换版：**已另选四组真实样本，并改为黑底白色 LiDAR 空间点云与稀疏雷达功率扇形图。请优先查看 [新版主图 PNG](../objdec_motivation_new_samples_260922/objdec_motivation_seq22_rdr00484.png)、[PDF](../objdec_motivation_new_samples_260922/objdec_motivation_seq22_rdr00484.pdf)、[四组素材总览](../objdec_motivation_new_samples_260922/new_sample_candidates.png) 和 [新版说明及中英文图注](../objdec_motivation_new_samples_260922/README.md)。四组都已分别导出完整动机图。以下内容保留为前一版 seq13 的设计和来源记录，不能直接用作新版的样本图注。

推荐查看：**[真实样本第三版 PNG](objdec_motivation_real_kradar_v3.png)**、[PDF](objdec_motivation_real_kradar_v3.pdf)、[组合 SVG](objdec_motivation_real_kradar_v3.svg)。SVG 内示意底图为位图，真实素材作为独立图像嵌入，不是全矢量重绘。旧的第一、二版保留供对照。

本轮修订：输入端改为每模态一个普通 token；同一个 token 经两个独立投影得到 shared 与 unique。相机、LiDAR、雷达及最终检测输出替换为同一帧 K-Radar 真实数据与保存的 ObjDec 预测，中间的目标／背景照片也取自该帧。示意底图使用内置图像生成工具修订，真实素材随后确定性嵌入，未交给生成工具重绘。工具未暴露具体后端型号，不能据此确认是否为 GPT Image 2.5。

对应提示词：real_sample_template_prompt.txt、token_parallel_fix_prompt.txt；来源记录：[provenance.json](real_sample_assets/provenance.json)；检查记录：[real_sample_validation.json](real_sample_validation.json)。

## 这一版想说清楚什么

已有方法通过空间交互、对齐、注意力或门控利用多传感器互补信息。我们的切入点是：**共享与模态特有信息在表示层面的角色，以及它们与目标相关性的联系，需要显式组织；这些表征还应直接参与融合控制。**

三栏与 WCBR 的叙述顺序相似，但将“天气条件下的分支偏好”换为“目标引导的共享／特有表征学习”：

- 左：用一个 Interaction / weighting 概括所参考融合方法的操作，不重画各篇网络。下方落点为 Shared / specific roles remain implicit。这里是对关注方法的抽象概括，不代表所有融合文献都缺少解耦，也不表示它们只使用一个分支。
- 中：背景也能产生跨传感器共同响应；同一目标也会呈现传感器特有的有效线索。因此，跨模态一致性本身不足以确定信息对检测的价值。两种现象是直观动机，不是本文对所有方法失效原因的实证结论。
- 右：对每个模态的同一个输入 token，分别通过 Shared projection 和 Specific projection 得到两类表征；不是输入预先有两部分，也不是 shared 再生成 unique。通过目标区域内的训练约束建立两类表示的不同角色，再用其预测前景相关性、模态贡献与目标上下文，调制融合。原始输入保留旁路；目标标注只用于训练监督。

## 真实样本与输出来源

- 样本：K-Radar **seq13 / radar 00146 / LiDAR 00107 / camera 00321**；元数据天气为 overcast，本图不将天气作为方法动机。
- 相机：`/home/hongsheng/k_radar_dataset/13/cam-front/cam-front_00321.png` 的 front0 左半幅。输入与预测显示同一局部窗口 `[u0,v0,u1,v1]=[540,240,820,520]`，只裁切缩放，没有提亮、去雾或内容重绘。完整前向图另存为 [camera_full.png](real_sample_assets/camera_full.png)。
- LiDAR：同帧 `os2-64_00107.pcd`，按原校准平移到雷达坐标，再投影到该序列的原始相机视角；颜色为高度。
- 雷达：同帧 `sprdr_00146.npy`（实际指向 `sparse_cube/cube_00146.npy`），与模型使用的预处理雷达数据来源相同；颜色为 log10 功率。可视化使用真实数值，不补点或移动点。
- 两种点云均先取显示 ROI `x∈[0,72], y∈[-20,20], z∈[-2,6]` 米，再按真实相机标定投影并显示上述局部窗口。这里是方便辨认输入的展示方式，不表示模型先将点云投到相机平面再编码。ROI、颜色及投影规则详见来源记录。
- 输出：正式 K-Radar v1 ObjDec Robust `model_0.pt` 已保存的同帧预测，来自 `analysis_exports/objdec_fig4_fig5_260919/paired_predictions/objdec/seq13_rdr00146.npz`。保留所有 `score > 0.3` 的 Sedan 预测，共 **2 个**，分数为 **0.879677、0.785065**。橙色框是预测，没有用 GT 框替代预测。完整输出另存为 [objdec_camera_full.png](real_sample_assets/objdec_camera_full.png)，另有 [BEV 输出](real_sample_assets/objdec_bev_all_predictions.png)。
- 中间背景与车辆照片是同一真实相机图的局部裁切；其右侧响应图，以及右栏 gate／权重／context 图标仍是**解释机制的示意符号**，不表示该帧的实测特征或 gate。

本轮只读取数据与已有预测，在 CPU 上绘图，未启动训练或推理。原始数据及预测文件哈希核查通过。

## 参考论文与比较边界

| 参考 | 可借鉴之处 | 本图应保留的事实 |
| --- | --- | --- |
| [3D-LRF，CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/papers/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.pdf) | 从传感器差异提出针对性的空间交互与条件化融合 | 它已经考虑三维空间关系与天气相关雷达流门控，不能将其画成固定权重融合。 |
| [L4DR](https://arxiv.org/html/2408.03677) | 将观测质量差异与具体融合设计联系起来 | 它已有前景感知去噪、模态内／模态间特征建模及门控。不能声称它不关注前景、完全不保留模态信息。 |
| [ASF](https://arxiv.org/html/2503.07029v2) | 以简化交互范式对照说明设计，并展示特征空间组织 | 它已有统一投影及局部自适应跨传感器注意力。ObjDec 沿用其中的投影和局部交互基础，新意应落在目标引导解耦与表征驱动控制的结合。 |
| WCBR，本地 video_paper_figures_260919/motivation.png | “已有方法—为什么还不够—本文设计”的三栏构图 | 仅借鉴叙述与构图，不移植天气路由、天气文本输入或“所有已有方法都只有单一表示”的概括。 |

上表最后一列结合论文描述与本地实现进行方法层面的比较；“缺少显式组织”是本文的比较视角，而不是这些论文作者承认的统一缺陷。

## 中文图注初稿

**图 1：ObjDec 的设计动机。**（a）所参考的融合方法通过特征交互与自适应加权利用多传感器观测，其共享与模态特有信息的表示角色通常未被显式区分。（b）共同响应可能来自背景，而模态差异也可能提供描述同一目标的互补线索，因此跨模态一致性并不充分决定目标相关性。（c）对于每个模态，ObjDec 将同一个局部输入 token 分别映射为共享与模态特有表征，并利用目标区域内的训练约束组织两类表示。学习到的表征进一步预测前景相关性、模态贡献与目标上下文，直接引导融合，同时保留原始输入的残差路径。GT 仅提供训练监督。相机与点云输入、局部照片及橙色预测框均来自同一 K-Radar 样本（seq13 / radar 00146）；输出为 ObjDec 在 score > 0.3 下保留的全部 Sedan 预测。点云按真实标定投影到相机视角以方便展示。表征与控制图标为机制示意，不是该帧的实测响应。

## English caption draft

**Figure 1: Motivation for ObjDec.** (a) Representative fusion approaches exploit multi-sensor observations through feature interaction and adaptive weighting, while the representational roles of shared and modality-specific information often remain implicit. (b) Common responses may originate from background, whereas modality-specific differences may provide complementary descriptions of the same object. Cross-modal agreement alone therefore does not determine object relevance. (c) For each modality, ObjDec maps the same local input token into shared and modality-specific representations through two independent projections. Object-region training constraints organize these representations, which predict foreground relevance, modality contributions, and object context to guide fusion while retaining a residual input path. Ground-truth boxes provide training supervision only. Camera and point-cloud inputs, image crops, and orange predicted boxes come from the same K-Radar sample (sequence 13, radar frame 00146). The output shows all ObjDec Sedan predictions retained at score > 0.3. Point clouds are projected into the camera view using calibration for display. Representation and control glyphs illustrate the mechanism rather than measured responses of this frame.

## 与当前实现对齐的注意点

依据 results/taskdec_methods_bilingual_initial_260917.md 与 models/fuser/patch_dec_a2_fusion.py 中的 K-Radar 主实现：

1. 所有位置都会计算共享与特有分支。GT 前景区域用于限定部分表征损失，不是推理输入或先验检测结果。
2. 前景 gate 是连续预测，低 gate 减弱更新与缩放，并不删除背景；没有第三个“背景解耦分支”。
3. 模态贡献评分不等于经过校准的传感器可靠性；图中使用 Modality contribution。
4. 目标上下文参与注意力查询和融合输出的调制。动机图将其概括在融合控制内，准确的前向顺序放在主架构图。
5. Shared 与 modality-specific 是各模态独立映射学习到的分支。新版用单个模态的通用 token `t_m` 展示两路独立映射，并注明 `m = Camera, LiDAR, Radar`，不再画成三个输入先合并。
6. 输入 token 的颜色只用于区分模态；内部短条仅表示向量维度。Shared／unique 的不同符号仅在投影之后出现。解耦也不意味着完成了严格可辨识的因素分解。

## 手工定稿时的优先修改

- 保留这一版三栏比较逻辑，正文不必再重复展开三个竞争方法的架构。
- 真实相机、点云和最终预测输出已替换完成；手改时应直接使用 real_sample_assets 内素材或原始文件，不要让生成工具再次描绘这些数据内容。
- 若正文缩小后右侧太密，可删去三个控制量的内部小插图，仅保留两类表征到 Object-guided fusion 的路径。具体 gate、权重和上下文计算留给 Figure 2。
- 当前虚线训练路径已有 Loss 标记。矢量重画时建议统一为“预测与标签汇入损失”的方向，进一步与实线推理路径区分；不要将 GT 画成融合输入。
- 输入端已使用单色普通 token；正式矢量排版时可沿用当前并行投影结构，避免重新引入“输入已分为 shared 和 unique”的误读。

## 可复现生成流程

`render_real_sample_assets.py` 读取数值数据和真实预测，绘制点云与检测框素材；`assemble_real_sample_figure.py` 将生成的示意底图、原始照片和真实数值图嵌入 SVG，再导出 PNG/PDF。前者使用 rl_3dod 环境的 Matplotlib，后者使用系统 librsvg/cairo。所有输入路径、原始框、分数及哈希均已保存；原始照片直接嵌入 SVG，不经图像生成重绘。
