# TaskDec 动机图、主图审阅与 Fig.5 素材方案

日期：2026-09-17。审阅用户提供的两张 PNG，对照当前主模型配置和融合实现。此次工作包括文档与 CPU 素材检查，未修改图片、训练配置或已有实验结果，未运行 GPU 推理。

## 1. 两张图的定位

- [图片 1：主架构图](</home/hongsheng/dec_con_asf/ChatGPT Image 2026年9月15日 23_53_07.png>)：可作为 Fig.2 的视觉草稿。输入—统一 patch—表示与控制—交互—检测的整体顺序清楚，但存在公式简化、箭头方向和输入标注不符实际的情况。
- [图片 2：动机图](</home/hongsheng/dec_con_asf/ChatGPT Image 2026年9月15日 23_53_21.png>)：现在接近另一张完整方法图。重复展开控制器、注意力与训练损失，导致它与主图的信息重叠。建议收束为“空间对应后的信息混合—共同/特有信息的目标相关性—本文思路”三个面板。

两图统一的模态颜色、局部 patch 放大和训练/推理区分可以保留。正式论文版本应减少大标题、长段落、渐变和装饰边框，改成可编辑矢量稿。图片中的场景、点云和检测示意如来自生成过程，只能承担示意作用；真实实验图使用数据集观测与模型预测，不能把示意检测框当成结果。

## 2. 动机图必须调整的内容

| 当前内容 | 问题 | 建议修改 |
|---|---|---|
| `Naive ASF fusion (uniform weights)` | ASF 使用跨传感器注意力，本身不是均匀权重融合 | 改为 `Aligned multimodal features`，展示直接交互的概念；如特指 ASF，应明确其已有 attention，不设虚假的均匀权重基线 |
| 天气图标占据主要动机 | 易让人读成另一篇天气条件融合论文 | 选真实正常场景与局部观测，天气仅作可选条件；中心问题改为 `Shared information, modality-specific cues, and object relevance` |
| `common target information` | 当前约束并不保证 common 只含目标语义 | 改为 `shared representations`，在图注说明以目标区域约束训练 |
| `unique ... appearance, density, motion` | 分支语义未被逐项验证；主配置雷达未启用 Doppler 输入 | 改为 `modality-specific representations`；观测例子与学到的表征含义分开 |
| `Suppress background`、`Clean BEV features` | 低 gate 使调制趋弱，不会把原始背景 token 清零 | 改为 `Object-guided feature modulation`，或者“在目标相关区域调节更新强度” |
| 多个勾号承诺 robust/accurate | 概念图不能替代结果；缺 LiDAR 和部分迁移设置存在退化 | 删除结果保证式文字；以一条设计目的结尾 |
| controller、MHA、loss 全展开 | 与 Fig.2 重复，挤占引言版面 | 动机图不放详细损失和 token/query/output 公式，只留概念流程 |

ASF 的原文 §3.2 明确使用 patch 内跨传感器注意力：[ASF](https://arxiv.org/html/2503.07029v2)。批评应指向本文研究的表示组织问题，不把已有注意力误画成固定等权融合。

推荐 Fig.1：

1. **对应局部区域的多模态观测。** 同一真实帧中标记目标与背景位置，表明三种模态观测相同位置但特征不同。
2. **需要解决的问题。** 一致响应不一定来自目标，模态差异也可能有用。共同信息、模态特有信息与目标相关性不是一一等同关系。
3. **TaskDec 的思路。** 学习共享/特有表示，并利用目标相关信息引导局部融合；明确本面板为概念示意。

## 3. 主图与实现的逐项对照

### 3.1 图名与继承关系

主标题建议使用 `TaskDec: Task-Aware Decoupled Fusion`，避免 `TaskDec-Controlled ASF` 将整个论文直接读成 ASF 外挂控制模块。与此同时，必须在方法正文及图注交代继承的 ASF unified projection、patch attention 与 PFT；图中可以用背景色或标记区分复用部分和本文设计。架构贡献由真实计算连接体现，不靠删除 ASF 名字取得。

### 3.2 输入标注

- LiDAR 主配置 `n_used=5`，不应把实际模型输入标为 `N×3`。可简写 `LiDAR observations`，细节移附录。
- 雷达 `cfg_RTNH.yml` 的 `INPUT_DIM=4`，注释明确第 5 维才包含 Doppler。稀疏立方体生成实现为 `(x,y,z,power)`；图中的 `(x,y,z,v)` 应改正。
- 投影前 BEV 通道数并不相同：相机 256、LiDAR 512、雷达 768。用 `C_m` 或分别标通道数，在统一投影之后再画公共维度 `d`。
- 冻结编码器权重符合 K-Radar 主配置，但 `FREEZE_BN=False`，不能进一步声称所有编码器状态都冻结。V2X 训练方式另行说明，不把雪花图标当成架构必需条件。

### 3.3 模态贡献概率与 token scale 应区分

图片 1 将 softmax 权重直接作为整个 token 的乘数；实际代码先以概率生成围绕 1 的缩放系数。对于主模型推理（schedule factor=1），可以写成：

\[
\alpha_m^p=\operatorname{softmax}_m(s_m^p/\tau),\qquad
w_m^p=\operatorname{clip}\left(1+\eta g^p(M\alpha_m^p-1),w_{\min},w_{\max}\right),
\]
\[
\widetilde{t}_m^p=w_m^p\left[t_m^p+\lambda g^p(c_m^p+u_m^p)\right].
\]

其中 M 是当前可用模态数，g 为 patch 级联合前景 gate，α 是模态贡献概率，w 才是实际 token scale。主图可只显示第二行和 `learned token scale w`，把第一行放方法公式，避免小字过多。权重是学习到的贡献分配，不作为已校准的物理可靠性概率解释。

当 g 较小时，解耦残差趋弱且 w 趋近 1，原始 token 仍然存在。因此不画成用 g 乘掉全部背景。

### 3.4 Task context 的语义与箭头

v1 主配置只有一个类别，实际 `context_mode=task_binary`：使用二元目标存在性预测生成上下文。主图标为 `object context` 或 `objectness-derived context`，不画成已验证的多类别语义 token，也不是分类/回归任务解耦。

主推理路径应明确为：

`controlled K/V + modulated Q → patch cross-attention → gated output residual → PFT → reshape/unpatch → fused BEV → detection head`

上下文只生成一次，分支送往 Q 和融合输出。主模型推理的两处更新为：

\[
Q'^p=Q^p+\beta g^p z^p,\qquad F'^p=F^p+\gamma g^p z^p.
\]

图片中下方 context 与 PFT/MHA 的箭头容易形成“PFT 输出上下文再回到 attention”的误读，需要重画；输出残差在 PFT 之前。

### 3.5 监督与前向分开

- GT 只指向 gate/context 的训练目标与前景约束区域，不连进推理输入。
- 共享对齐、unique 差异约束、同模态 common/unique 余弦分离是软约束，不能用图示暗示严格独立或精确正交。
- gate/context 的目标性监督包含前景和背景；表示解耦项在选定前景 patch 上计算，不宜把所有损失都画成只在前景上计算。
- SCL 沿用 ASF，主配置 `SCL=True`。若显示，应标为 inherited training objective；不能与新增解耦/控制目标混成均为本文原创的五个损失。
- 把损失简并成 `Detection and inherited combination supervision` 与 `Representation and object-related supervision` 两组，细节留方法正文或附录。

实现依据：[融合实现](../models/fuser/patch_dec_a2_fusion.py)、[主配置](../configs/ASF_task_dec_controlled_robust_v1_0.yml)、[ASF 基配置](../configs/v1_0/cfg_A2F_scl_final.yml)、[雷达配置](../configs/v1_0/cfg_RTNH.yml)、[稀疏雷达生成](../datasets/kradar_detection_v1_0.py)。

## 4. Fig.5 的已有素材：能复用什么，仍缺什么

| 素材 | 核查结果 | 用途 |
|---|---|---|
| TaskDec Robust model_0 的 conf=0.3 逐帧预测 | 找到 10,065 份 `pred/*.txt`，同时有 GT 和条件描述 | 可复用三维框，无需重新训练 |
| 官方 ASF v1 已提取归档 | `exp250303/test_kitti/none/0.3` 只有 `complete_results.txt`，没有逐帧框 | 汇总 AP 不能用于绘制预测，需为候选帧补推理 |
| 本地 ASF 重训逐帧预测 | 存在多份完整归档 | 可用于另行标明的重训对照，不能替代官方 checkpoint 行 |
| 官方 ASF v1 checkpoint | `/home/hongsheng/K-Radar-main/pretrained/v1_0_official/A2F_v1_0_model_10.pt` 已被现有测速脚本使用 | 少量候选帧推理的来源 |
| Fig.4 候选 | 21 帧真实相机、LiDAR、标签、标定路径及完整 gate | 可优先复用，避免额外导出大批特征 |
| 相机标定与投影工具 | 存在逐序列标定和渲染代码 | 需核对原图/去畸变/裁剪后的坐标系，不能直接套用旧示例路径 |

已保存 CPU 核查索引：[candidate_assets.json](../analysis_exports/taskdec_fig5_asset_audit_260917/candidate_assets.json)。

将 21 个候选的 GT 几何与历史评测 GT 框匹配后：12 帧具有唯一的量化几何匹配，4 帧有多个匹配，5 帧暂未匹配。这只是查找线索，仍需核对当时数据集顺序、帧号及标签过滤流程；不能把量化几何匹配当成正式帧身份验证。

- `seq13/rdr00146` 在该核查中唯一匹配到历史评测 ID `002700`；两份 GT，TaskDec 两份预测，条件为 day/highway/overcast。这尚不能说明两份预测都是 TP，也不证明相对 ASF 有提升。
- `seq25/rdr00154` 暂未通过该量化几何查找匹配，不能强行套上某个历史文件。它仍可作为两模型少量重新推理的候选。

### 历史 KITTI 文本的关键注意事项

当前 `dict_datum_to_kitti` 写出的字段采用 K-Radar 特有转换：中心以 `(yc,zc,xc)` 顺序写入 KITTI location，尺寸以 `(height,width,length)` 写入，yaw 保留原角度。二维框 `50 50 150 150` 是占位字段，不是真实相机检测框。

因此必须逆变换到 `(x,y,z,l,w,h,yaw)`，再通过逐序列标定投影三维框。不能把占位二维框叠到照片上，也不能直接套标准 KITTI 的相机坐标/yaw 或 bottom-center 假设。原始照片的 front0 半幅、去畸变和裁剪处理必须与投影矩阵对应。

## 5. Fig.5 推荐制作顺序和版式

1. 从已有 21 帧候选开始，以真实帧 ID 匹配 TaskDec 历史结果；有歧义的帧不复用错误文件。必要时两模型对候选帧同时推理，确保输入与后处理一致。
2. 使用官方 ASF v1 权重补导出候选帧，统一 C+L+R、label v1.0、ROI `[0,72]×[-6.4,6.4]×[-2,6]`、conf=0.3 和 NMS。只保存最终三维框、分数、帧号和来源清单。
3. 依据三维几何匹配选取两组有清楚观测的案例，分别检查漏检、额外预测或定位差异；不能仅比较预测数量，更不能预先假定某两帧一定展示改善。保存定量匹配阈值和选例依据。
4. 先完成同帧相机参照＋BEV 框对照，再核查相机投影。只有确认 GT 三维框与真实车辆对应后，才生成相机预测框对照。
5. 正文用两组案例；附录补充双方相近以及 TaskDec 失败的案例。定性选例用于解释行为，不替代全量 AP。

推荐正文每个案例四个面板：

| Camera + ASF | Camera + TaskDec | BEV + ASF | BEV + TaskDec |
|---|---|---|---|
| 同一真实相机帧与预测框 | 同帧、同视野、同显示阈值 | 同一 LiDAR 背景与 GT/预测 | 同一范围、缩放与 GT/预测 |

两个案例共 2×4 个面板。若相机投影仍待校验，可先做“原始相机参照＋ASF BEV＋TaskDec BEV”三列草稿，明确相机仅供场景参照；不画猜测位置的相机框。

- GT 使用固定灰/绿轮廓，预测统一另一颜色，方法由列标题区分。不要用更高饱和度或不同点云密度给某模型制造视觉优势。
- 保持相同相机裁剪、BEV 朝向、ROI、置信度和图例。局部放大时两模型放大相同区域。
- 相机视野宽于窄 ROI；ROI 外可见车辆不属于本次评测对象，不能将它们直接标成漏检。
- Fig.5 不再插 gate 列，避免与 Fig.4 重复；可在两图共享案例、用同一目标编号建立联系。

空间预算：复用已有图片/PCD 路径，几十帧最终框的 JSON/NPZ 很小；不保存中间 BEV、common/unique 特征或数据副本，候选拼图及最终 PDF/PNG 建议控制在数十 MiB 内。

**当前完成的是素材核查和可执行制作方案，不是已完成的官方 ASF–TaskDec Fig.5。** 此次没有启动新的训练、全量评测或候选帧 GPU 推理。

## 6. 与 Introduction 的对应

[中英文 Introduction 初稿](taskdec_introduction_bilingual_initial_260917.md)已按实际架构撰写。Fig.1 回答该稿第三段的研究问题；Fig.2 解释第四段的计算关系；Fig.5 最终承担第五段实验中的实际预测行为展示。引言不依据生成示意图声称背景已经清除、unique 已携带运动语义或天气变化时传感器主导权自动切换。
