# ObjDec Appendix：中英文初稿

日期：2026-09-20。与[方法正文](taskdec_methods_bilingual_initial_260917.md)和[实验正文](objdec_experiments_bilingual_initial_260919.md)配套。中文与英文对应，数值表格共用；正文已有的架构推导与主结果讨论通过交叉引用衔接。公式A.1等为附录独立编号，正文公式仍按现有第3节编号引用。

**编辑说明（投稿时移除）：** 文中的〔待补〕与Pending表示尚未完成的记录或结果，不是实验结论。表格来源和待办单独放在[作者核对说明](objdec_appendix_source_notes_260920.md)，不混入论文叙事。本文件是一版可编辑初稿，尚未整合到LaTeX或完成最终图表排版。

**2026-09-22更新。** 正文以V2X-Radar-V作为主要跨数据集架构验证；VoD补充实验收入G.4及表G.3a/G.3b、G.4，包含完整区域／类别结果、选模方式和适配取舍。

## 一、中文附录正文

### A. 实现与训练细节

#### A.1 表征维度与前景标签

本节补充第3节中省略的张量尺寸与监督目标构造。网络设置见表A.1。共享与模态特有分支均由LayerNorm–Linear–GELU–Linear–LayerNorm组成，每个模态使用独立参数。前景门控与模态评分头使用128维隐藏层；单类别objectness头使用160维隐藏层。模态评分头末层初始化为零，使初始模态贡献均匀；v1前景头的末层权重初始化为零、偏置为−1.2。上下文投影不使用偏置，其权重按标准差0.015初始化。

对BEV patch中心 \(p=(p_x,p_y)\) 与真实目标框 \(b=(x_b,y_b,l_b,w_b,\theta_b)\)，先将相对位置旋转到框的局部坐标系：

\[
\begin{aligned}
a_{pb}&=(p_x-x_b)\cos\theta_b+(p_y-y_b)\sin\theta_b,\\
b_{pb}&=-(p_x-x_b)\sin\theta_b+(p_y-y_b)\cos\theta_b,\\
y^p&=\mathbb{1}\!\left[\exists b:\ |a_{pb}|\le l_b/2+\epsilon,\quad |b_{pb}|\le w_b/2+\epsilon\right].
\end{aligned}
\tag{A.1}
\]

这里 \(\epsilon\) 是沿框局部两轴的扩张距离，v1与V2X取0.7m，v2 Strong取0.6m。该判定使用patch中心，不按patch与框的面积交比赋值。多个框覆盖同一位置时，二元前景标签取并集；多类别上下文标签按有效GT框的遍历顺序覆盖，保留最后写入的类别。填充框和非正尺寸框不参与赋值。

式（A.1）只构造训练目标。第3节中的表征分支和预测gate在所有patch上计算，前向融合在训练和推理时均使用预测值。用于可视化的GT轮廓在预测后添加；其作用与训练标签、预测gate分别对应不同的数据处理步骤。

#### A.2 辅助监督的归一化与边界情况

令 \(N_+\) 和 \(N_-\) 为当前batch的前景与背景patch数。前景门控使用加权二元交叉熵，其正样本权重为

\[
\omega_+=\operatorname{clip}\!\left(\frac{N_-}{\max(N_+,1)},1,k\right).
\tag{A.2}
\]

损失对batch内全部patch取均值。门控头取 \(k=30\)；v1单类别objectness头取 \(k=4\)。第3节式（2）的表征约束只在前景位置计算。若整个batch没有选中的前景、没有有效GT，或参与该训练路径的模态少于两个，当前实现跳过新增辅助损失块，保留相应的检测训练路径。

V2X的object context使用三类softmax概率，经无偏置线性投影和tanh得到上下文向量；类别交叉熵只在前景patch上计算。类别权重按当前batch前景类别计数的倒频率构造，并按配置裁剪。独立的gate仍使用前景/背景监督。表A.2给出前向控制系数与实际辅助损失权重，其中外层辅助系数需要与内部系数相乘。

#### A.3 优化与传感器组合监督

K-Radar融合模型使用已有单模态预训练编码器，冻结其参数，但BatchNorm统计按原训练模式更新。配置采用AdamW，初始学习率 \(10^{-3}\)、最小学习率 \(10^{-4}\)、权重衰减0.01、batch size 2，以及原训练入口的余弦调度；配置上限为11轮。所报告权重的选择程序见B.2。V2X的共享底座从ImageNet初始化相机ResNet-50，其余参数从未训练初始化开始，所有编码器均参与训练。V2X同样使用AdamW、初始学习率 \(10^{-3}\) 和权重衰减0.01；80轮预算采用micro-batch 2、累积4次更新、有效batch 8，1轮warmup后按更新步数余弦衰减至 \(10^{-5}\)。

K-Radar采用ASF的传感器组合监督（SCL）[ASF]。对于三模态输入，六个单模态/双模态组合分支分别计算检测损失后求和，不除以组合数。组合从本次完整输入生成的受控token中选取，并共用已经调制的query；每个子集不再独立计算gate、模态贡献和context。组合分支不额外施加主融合路径的context输出残差。V2X实验关闭SCL。该实现使SCL提供组合特征上的检测监督，其计算过程与F节的固定权重缺模态推理有所区别。

### B. 评测协议与模型选择

#### B.1 AP计算与后处理

各数据设置的额外评测细节见表B.1。K-Radar v1使用legacy AP汇总：从41个precision采样位置每隔4个取值，共11点；v2的revised实现对41个值取均值，并使用对应的高度中心约定。二者均与V2X的标准AP_R40汇总区分。K-Radar的conf是检测头score预过滤后、导出预测时追加的阈值；因此conf=0.0不表示检测头也保留了所有低分预测。

在v2的L4DR统一评测中，导出、GT、conf及生效的NMS阈值被对齐到Strong的设置，旋转NMS阈值为0.01。L4DR的原生生效配置与此不同，因此该行表示包含后处理适配的本地统一评测，不是仅替换AP汇总函数。固定预测下对AP采样与高度中心的交叉检查见表B.2；这一区分说明为何标签名称或IoU阈值相同仍不足以保证数值直接可比。

#### B.2 结果来源与权重选择

K-Radar表格分别标明官方权重对应的结果归档、本地加载官方权重评测，以及本地训练。ASF归档的配置与报告口径对应，但不将归档行描述为本次与其他模型同时进行的逐帧重评。v2本地ASF与Strong使用同组预训练编码器；本地L4DR从头训练原生L+R网络。三者匹配训练集、11轮与有效batch，但预训练成本、模态和网络结构不同。

v1完整模型与移除版本均经过1,000样本预评测后选择checkpoint，再进行完整集合评测。〔待补：该子集的来源与ID/生成规则、各候选范围、选择指标及并列处理。〕在这些记录补齐前，不将其命名为独立验证集。v2本地训练对照采用末轮权重；Strong作为既有Dec变体单独标识，不用于验证完整object-context路径。

V2X在第1轮及随后每5轮评测去重验证集，按严格IoU下的Moderate三类平均3D AP选择best，并在并列时保留更早轮次。训练结束后分别评测best与第80轮last的原始/去重val和test；test不用于选择checkpoint。最终独立复评与训练期验证可能在极小数位上不同，两类记录保持各自来源，不用复评值重写训练曲线。

### C. 完整 K-Radar 结果

#### C.1 置信度与更严格的匹配条件

表C.1补充正文未展开的IoU=0.7及另一档置信度设置。在conf=0.0时，ObjDec与官方ASF归档的3D@0.3分别为88.06和87.34，差值小于正文conf=0.3下的差值；3D@0.5分别为72.83和72.95。相同权重的排名与差值因导出阈值和IoU而改变，因此应分别描述各操作点。对于更严格的3D@0.7，ObjDec在两档conf下均高于官方ASF，而BEV@0.7略低。这里补充的是匹配条件对结果的影响，不将某个操作点的优势扩展到全部指标。

表C.2将v2两类Mean展开为逐类3D/BEV指标。Strong相对本地ASF在Bus/Truck的BEV@0.7上由16.84提高至23.13；与官方L4DR相比，该指标仍低于29.65。逐类表有助于区分同训练日程的融合对照与不同架构/初始化的参照。

#### C.2 天气分组与聚合方式

表C.3与C.4报告完整天气分组。Total由全体样本共同形成的精确率–召回率序列计算，天气AP均值不能重建Total。表中无对应类别GT的格子标为“—”；v2 Fog没有Bus/Truck目标，不计入该类别的天气平均或正负收益计数。

v1的雨天3D@0.5为74.92，高于两种ASF来源；雨夹雪下该指标为57.60，低于两种ASF来源。v2 Strong相对本地ASF的提升覆盖多数类别–天气项，但Sedan的小雪@0.3与大雪@0.5仍有下降。完整分组表支持对条件差异的分析，不将天气标签视为独立受控干预，也不以天气优势替代表征设计的主论证。

### D. 组件干预与补充指标

#### D.1 消融的实际计算变化

本节补充正文Table 3的干预定义。关闭模态贡献控制时，将式（4）的缩放强度设为0，使模态缩放为1；表征残差、预测gate及上下文路径保留。关闭object context时，移除其监督并关闭query与attention输出中的上下文注入。关闭解耦监督时，仅将共享对齐、特有相似度约束和两分支分离三项损失的权重设为0；两类分支仍生成特征并参与前向控制。关闭前景gate时，将其输出固定为1并关闭gate监督，保留其他分支。

这些定义区分了辅助监督、门控幅度和前向路径本身。特别是，“无解耦监督”的结果不等价于移除shared/specific网络，也不等价于简单Concat。

#### D.2 严格三维与BEV结果

表D.1给出正文未列出的3D@0.7、BEV@0.3与BEV@0.7。关闭模态贡献控制后，3D@0.7由22.04降至11.08；其BEV@0.7仍为61.36，接近完整模型的62.63。这说明该干预对严格三维框匹配与水平重合的影响程度不同，不能仅根据BEV指标推断三维定位变化。四项移除在所列补充指标上均低于完整模型，但这些是当前单种子及选择程序下的观察，不提供统计显著性结论。

#### D.3 固定权重空间gate与context干预

固定K-Radar v1主模型权重和每帧编码特征，均值gate将3D@0.3／BEV@0.5从本次配对baseline的88.36／88.11降至53.90／53.16；三次帧内置换平均为21.29／21.01。联合关闭query／output上下文增量仅变化−0.0146／−0.0087个百分点。三种随机种子是推理置换，不是独立训练；gate共同影响token残差、模态缩放和context，不隔离解耦贡献。完整八组及置换均值见英文附表D.2和[结果记录](objdec_kradar_v1_interventions_results_260924.md)，不使用历史主表baseline计算干预差值。

### E. 表征统计与额外可视化

#### E.1 统计单位与加权PCA

令 \(x_{im}^p\) 为帧 \(i\)、模态 \(m\)、位置 \(p\) 的某类表征，\(\mathcal P_i\) 为该帧GT前景位置集合。帧均值与跨模态相似度分别定义为

\[
\mu_{im}=\frac{1}{|\mathcal P_i|}\sum_{p\in\mathcal P_i}x_{im}^p,\qquad
s_i^{mn}=\frac{1}{|\mathcal P_i|}\sum_{p\in\mathcal P_i}\operatorname{cos}(x_{im}^p,x_{in}^p).
\tag{E.1}
\]

天气组 \(w\) 中的余弦统计对 \(s_i^{mn}\) 按帧等权平均。它不同于先对向量求均值再计算余弦，也不同于把所有patch直接汇总后的加权结果。当前全部10,065帧均有有效前景，共包含642,649个前景空间位置；模态对拆分统计见表E.1。

Input、Shared与Specific分别拟合一个PCA基。在每类表征内，三模态与全部天气共享该投影基。拟合使用帧均值 \(\mu_{im}\)，每个向量的权重为 \(1/(|\mathcal W|N_wM)\)，其中 \(N_w\) 是所属天气的帧数、\(M=3\)。使用加权中心化协方差的前两特征向量，不额外做逐向量单位化或按通道标准化。该权重使各天气和各模态对拟合的总体贡献相同。不同表征列具有不同坐标基与尺度，不跨列比较绝对欧氏距离。

七天气散点图每种天气最多显示400帧，阴天显示全部383帧；各模态和表征面板共用同一组显示帧。质心和密度轮廓使用全部帧。固定随机种子与PCA基后不按视觉效果重新拟合，也不添加抖动或截除离群点。附图E.1提供正文PCA的完整天气展开。

#### E.2 高维相似度的分布与天气变化

表E.1显示Specific并未在所有模态对上趋近正交，例如C–R余弦在七天气中约为0.65；涉及LiDAR的模态对则有更明显的天气组间变化。该结果与共享/特有分支的相对组织目标一致，不要求Specific在不同传感器间完全无共同信息。

附图E.2和表E.2进一步展示逐帧相似度分布。正常天气与大雪下，L–R Shared中位数分别为0.9632和0.9662；Specific的5–95%分位范围由0.2113–0.4948变为0.2578–0.7363。小提琴宽度表示经验密度，粗线表示25–75%分位，细线表示5–95%分位；它们描述帧间变异，不是置信区间。

作为聚合敏感性检查，按序列等权重新汇总时，Specific在正常/大雪的平均跨模态余弦约为0.440/0.584，而帧等权结果为0.446/0.537。Shared保持较高一致性的观察未改变，Specific的精确组间差值则依赖汇总权重。天气与序列、场景及目标组成相关，高余弦本身也不能排除公共方向或低方差，因此这些统计与组件消融共同解释，不单独作为语义可辨识性或天气因果效应的证明。

**帧级对应性对照（附图E.3）。** 对前景均值向量比较同帧配对与同天气、不同序列的错配，使用十个固定随机种子，并让同帧对照使用相同的保留样本。未中心化时Shared的C–L／C–R／L–R同帧余弦为0.979214／0.970201／0.987697，错配为0.979205／0.970225／0.987136。减去各模态的天气组均值后，L–R同帧／错配为0.148740／−0.014689，相机相关同帧值接近零。这表明原始高余弦受到共同均值方向影响；帧均值会丢失局部信息，该对照不能代替逐patch对应性检查，也不单独证明共享分支无用。

#### E.3 Gate与检测图的制作协议

正文Fig.4现在采用三个场景：相机预测、完整LiDAR BEV与gate、gate局部放大。其前景／背景gate均值依次为0.213／0.128、0.259／0.115、0.288／0.118，局部窗口为14×8.4m。Gate由输入特征预测，GT在预测完成后用于参照叠加和区域统计。热图采用原始16×90网格、0.8m patch和统一[0,1]色标，不平滑；相机只显示选定目标GT，BEV与gate保留显示区域内全部GT。

七天气gate选例移至附图E.4，表E.3继续对应这七个附录样本，并非正文的三个场景。七天气样本从21帧完整gate候选中选择，历史导出在融合器入口暂时移除GT；一个存在未解释重复推理差异的候选未纳入。附图E.5给出全量统计：按帧等权的前景／背景均值为0.2701／0.1176，99.06%的帧满足前景均值大于背景均值。选例统计和全测试集统计分别报告。

原Fig.5的ASF／ObjDec检测对照移至附图E.6。两模型使用相同输入、后处理、0.3显示阈值、相机裁剪及12×6m BEV局部窗口；20帧候选均核对了输入哈希和GT。三行选定目标的最大几何3D IoU依次由0.572／0／0变为0.719／0.476／0.741，不是AP或官方一对一匹配结果，中间案例仍未达到IoU=0.5。附图E.7补充大雪改善（0.095→0.728）及小雪反例（0.354→0.223）；后者有较高gate但定位更差。全部20帧候选保留为归档图册，不在论文PDF中重复铺开。

### F. 传感器可用性与损坏输入

#### F.1 两种输入干预

移除模态时，仅向融合器提供剩余传感器的特征，并重新计算该集合上的gate、模态贡献和context。损坏输入则保留对应模态分支。C*以原始RGB黑帧替代图像，再执行原归一化和相机编码器；L*采用无回波输入约定，将高度压缩的稀疏LiDAR特征置零，再经过原稠密BEV骨干。后一处理避免调用不支持空输入的稀疏算子，因此其精确定义是该特征入口的无回波模拟。

十种设置在各自数据版本内使用同一权重，不按组合重训或重新选择checkpoint。完整v1 ObjDec与v2 Strong分别报告于表F.1和F.2。与A.3中复用完整输入受控token的SCL相比，这里的缺模态推理从实际可用特征重新计算融合控制。

#### F.2 阈值、依赖与ASF参照

除正文讨论的完整输入与双模态组合外，表F.1/F.2补充单传感器、损坏输入和另一档conf。v2的C+L*+R在conf=0.3时平均3D@0.3为27.99，conf=0.0时为34.70；相同阈值下，移除LiDAR的C+R分别为34.25和34.73。损坏但保留分支与直接移除分支在不同阈值下并不总是等价。

黑帧C*+L+R接近完整输入，而单相机预测很弱。该组合只能说明当前模型对这种相机输入变化不敏感；低相机贡献也可能造成类似现象。缺LiDAR的明显下降则说明传感器依赖仍然存在。若计算AP保持率，分母始终为同一权重、同一阈值下的完整输入AP；这一比值不解释为目标召回率。

ASF表3 [ASF] 可用于了解相同类型的可用性设置，但其损坏输入细节与相机单路评测范围未完全对应到本地规则。本附录以固定权重的内部比较为主，不将星号行作为严格跨方法鲁棒性排名。

### G. 跨数据集架构适配

#### G.1 数据处理与公共底座

使用公开包的8,391个训练帧，原始val/test为1,498/1,501帧，去重后分别为1,487/1,486帧。Car、Truck和Bus合并为Vehicle；其余两类为Pedestrian与Cyclist。ROI及难度/IoU口径见表B.1。本地适配还包括ROI内GT过滤、由标定投影生成难度过滤所需的二维框，以及交面积数值修复。该处理与公开论文表格的数据版本、报告集合和空间覆盖有差异 [V2X-Radar]，因此这里扩展的是正文所定义的本地架构比较。

相机底座使用ResNet-50、多尺度特征组合与学习深度分布，再以LSS投影到BEV；输入图像为288×512。LiDAR与Radar分别使用独立PillarVFE、scatter及BEV卷积stem。点云字段数分别为4与6，每柱最多32个点、最多32,000柱。三路各输出64通道，融合后统一为128通道，再进入公共多尺度BEV主干；检测头接收384通道，并使用按训练集统计确定的anchor设置。

初始化时，共同编码器及检测头张量从同一未训练初始化中复制；没有以已训练的目标数据集checkpoint热启动。增广为全局旋转±0.392699弧度、缩放[0.95,1.05]及概率0.5的翻转，相机几何与点云使用同一空间变换。其余训练设置见A.3。

#### G.2 融合结构与空间分辨率

Concat在BEV通道维拼接后应用3×3 Conv/BN/ReLU，学习跨模态通道及相邻位置的组合。ASF-style采用统一投影、局部attention和PFT。ObjDec将第3节中的表征、门控、模态贡献与上下文路径一起作为融合计算；三模态组使用共同编码器与检测头。ObjDec-LR从训练起只建立LiDAR与Radar分支，其与L4DR的比较保留两者原生网络差异。

0.4m设置的BEV为256×256；0.16m设置为640×640，检测头空间步长均为BEV的2倍。旧4×4 patch使用16个query，2×2 patch使用4个query，均输出128通道。对应的物理patch覆盖从0.4m网格上的1.6m或0.8m变为0.16m网格上的0.32m。改变网格和patch不仅改变计算量，也改变局部融合区域与目标尺寸的相对关系。

#### G.3 完整预算下的补充结果

正文表4集中呈现公开方法参考与本地融合对照，本节补充公共底座下的Concat受控基线。表G.1保留正文未展开的0.4m组、选中轮次和val/test对应关系；表G.2补充已完成0.16m组的逐类BEV与末轮结果。0.4m下，ObjDec从4×4改为2×2后，test行人3D AP由58.75提高至62.36，平均3D由72.22提高至74.03。该变化同时涉及patch与query数。Concat在0.4m与0.16m下的test平均3D分别为75.77和81.90，表明公共检测底座同样受益于更细网格；更细分辨率带来的提升不能全部归因于ObjDec。在0.16m下，按val选中的ObjDec相对Concat平均test 3D/BEV分别低0.52/0.20个百分点，因此当前结果不支持优于所有已评测融合结构的结论。

五组0.16m实验均已完成80轮训练与最终best/last评测。三模态ObjDec按val选中的第70轮在test取得81.38/86.27的平均3D/BEV AP，第80轮为81.55/86.35；ObjDec-LR选中的第75轮为79.65/83.81，第80轮为79.75/83.80。末轮test的变化不改变主表按val选模的规则。ASF-style与L4DR均选中第80轮。相对L4DR，ObjDec-LR的三类3D AP分别提高0.71/1.58/1.93点，BEV分别提高0.29/1.73/1.73点。相对ASF-style，三模态ObjDec的Cyclist 3D与BEV提高0.95/1.21点，Vehicle 3D和BEV则略有回退。〔待制图：Figure G.1完整80轮验证曲线，所需验证节点已齐全。〕曲线使用真实验证节点，不将逐类最优值拼接为单个模型。

#### G.4 VoD上的补充架构适配

**设置。** 为补充正文V2X-Radar-V上的架构验证，我们在VoD的原生PointPillars检测底座中训练LiDAR–四维雷达版本，使用5,139帧训练集和1,296帧验证集，输入为单帧LiDAR与五帧Radar。两组近期ObjDec实验均采用0.16 m网格、320×320 BEV、2×2 patch及4个查询；每个模态增加两层64通道的3×3 Conv–BN–ReLU局部编码，并使用token LayerNorm。两组均从头训练80轮，seed为666，采用FP32、Adam OneCycle与0.003峰值学习率，微批次8、梯度累积2次，有效batch size为16。每5轮完整验证，以官方EAA平均AP选模，并用同一权重报告DC及其他指标。两组均保持score=0.1、NMS=0.01。

**锚框适配。** 第二组仅改变三类锚框尺寸与底部高度，其余配置保持一致。先验来自增强前训练标注：经标定转换到LiDAR坐标，按原生训练ROI的框中心规则过滤，取尺寸与底部高度的逐维中位数并舍入到0.01 m，不使用验证标注拟合。Car、Pedestrian、Cyclist的长／宽／高分别为4.19/1.81/1.52、0.65/0.63/1.69、1.94/0.78/1.76 m，底部高度分别为−1.65、−1.62、−1.68 m。尺寸和高度同时改变，因此此实验考察整组锚框先验的作用。

**结果。** 表G.3a/G.3b采用官方VoD的区域／类别过滤与11点3D AP；Car、Pedestrian、Cyclist的IoU阈值分别为0.5、0.25、0.25。EAA与DC表示整体标注区域与驾驶走廊，均为3D检测指标。2×2 patch与局部编码版本选中第75轮，EAA/DC为71.23/84.69；适配锚框版本选中第80轮，达到72.03/83.76。EAA提高0.80点，主要来自Cyclist的4.51点增益，同时DC下降0.93点。相对本地L4DR参照，适配锚框版本的EAA高1.03点、DC低1.08点；仍低于L4DR论文报告的总体EAA/DC [L4DR]。表G.4另列相同权重的KITTI AP_R40：Moderate平均3D由78.64变为78.35，BEV由80.55变为80.92，进一步显示该适配涉及指标间的取舍。

**比较范围。** 表中历史PP-Concat采用AMP和实际batch size 16，旧ObjDec从Concat权重初始化；本地L4DR采用100轮、双GPU和SyncBN，第99轮是已评估末期候选中的较优权重。它们提供历史与外部架构参照，训练条件并非完全匹配。尚未补齐具有相同局部编码与训练设置的Concat对照，因此相对历史基线的组合收益不能全部归因于表征解耦。此处报告在VoD上训练后的架构适用性与具体适配收益，不声称零样本迁移或VoD总体最优。

### H. 效率测量与适用范围

#### H.1 配对计时设计

在RTX A6000上，以batch size 1、4个PyTorch CPU线程、FP32张量且不使用autocast进行计时；原环境的matmul/cudnn TF32保持开启，cuDNN deterministic开启、benchmark关闭。PyTorch版本为1.10.1+cu113。测试索引均匀选取120帧，前20帧预热、后100帧计时，并对同一组帧重复两轮。

每帧的CPU输入复制给eager与Graph路径，交替运行顺序并分别同步。模型运行次序为ObjDec、ASF、ASF、ObjDec。计时覆盖network调用，包括点云预处理、H2D、编码、融合、解码、NMS和原评测路径的GT recall统计；不包含读盘、collate、首次图捕获、初始化或结果核对。其他GPU训练仍在运行，因此主机负载并非完全隔离。表H.1补充中位数、P95和计时标准差，不将平均延迟的极小差异解释为稳定架构优势。

#### H.2 图重放与数值核查

CUDA Graph仅捕获相机Swin骨干与融合器的重复执行路径。每帧仍输入新的图像与BEV特征并执行全部算子，标定逐帧读取，不跨帧缓存预测。不同形状、模态子集或融合可视化请求回退至原融合执行路径。

每种模型共进行240次含预热的数值对照。被捕获模块在固定输入下均逐位一致；完整路径中，两个模型均有218/240次全部检查张量逐位一致，首次差异出现在未修改的Radar分支，对应原版重复推理也可出现波动。最终类别一致次数为ObjDec 238/240、ASF 235/240。该检查限定于抽样输入，尚未形成优化路径的全测试集AP结果。

四次测速均在完整结果写盘后出现native退出异常；可视化的两次小规模预测导出也存在同类退出问题，文件完整性与数值检查单独保存。本文的部署分析因此限于已测执行路径与抽样一致性，不据此声称稳定在线部署。原始日志与核查记录作为复现材料保留。

#### H.3 证据范围

当前实验以单种子为主，v1的选择子集记录仍需补全；本附录不报告多种子误差条或显著性检验。v2 Strong省略object context，提供的是解耦控制变体的扩展证据。V2X与VoD结果来自目标数据集上的训练，反映架构适配能力而非零样本迁移。空间粒度、较弱的单相机预测及缺LiDAR下的退化仍限定了适用条件。

表征约束采用软相似度目标，不要求严格独立、语义可辨识分解或 \(c+u=t\) 的重建等式。余弦与PCA描述学习到的结构，检测消融与定性案例提供互补证据；当前结果不足以将某一表征几何变化独立识别为检测收益的唯一原因。

## 二、English appendix

### A. Implementation and Training Details

#### A.1 Representation dimensions and foreground targets

This section specifies tensor dimensions and supervision targets omitted from Section 3. Network settings are listed in Table A.1. Both the shared and modality-specific branches follow LayerNorm–Linear–GELU–Linear–LayerNorm, with separate parameters for each modality. The foreground and modality-scoring heads use a hidden dimension of 128, while the single-class objectness head uses 160. The final modality-scoring layer is initialized to zero, giving equal initial modality contributions. For v1, the final foreground layer has zero weights and a bias of −1.2. Context projections have no bias and use an initial weight standard deviation of 0.015.

For a BEV patch center \(p=(p_x,p_y)\) and a ground-truth box \(b=(x_b,y_b,l_b,w_b,\theta_b)\), we rotate their relative displacement into the box coordinate system and assign the foreground target according to Eq. (A.1). The margin \(\epsilon\) extends each local box axis by 0.7 m on v1 and V2X, and by 0.6 m for v2 Strong. Membership is determined by the patch center rather than patch–box area overlap. Binary foreground labels form the union of valid box footprints. For multiclass context, overlapping labels are overwritten in GT iteration order, retaining the last assigned class. Padded boxes and boxes with nonpositive dimensions are ignored.

\[
\begin{aligned}
a_{pb}&=(p_x-x_b)\cos\theta_b+(p_y-y_b)\sin\theta_b,\\
b_{pb}&=-(p_x-x_b)\sin\theta_b+(p_y-y_b)\cos\theta_b,\\
y^p&=\mathbb{1}\!\left[\exists b:\ |a_{pb}|\le l_b/2+\epsilon,\quad |b_{pb}|\le w_b/2+\epsilon\right].
\end{aligned}
\tag{A.1}
\]

Equation (A.1) constructs training targets only. The representation branches and predicted gate are evaluated at every patch, and fusion uses the predicted values during both training and inference. GT outlines in the visualizations are added after prediction. Training labels, predicted gates, and reference overlays therefore belong to distinct processing steps.

#### A.2 Auxiliary-loss normalization and boundary cases

Let \(N_+\) and \(N_-\) denote foreground and background patch counts in the current batch. Foreground gating uses binary cross-entropy with positive weight \(\omega_+\) defined in Eq. (A.2), averaged over all batch patches. The upper bound is \(k=30\) for the gate and \(k=4\) for single-class objectness on v1. The representation constraints in Section 3, Eq. (2), are evaluated only at foreground locations. If a batch has no selected foreground, no valid GT, or fewer than two modalities on this training path, the implementation skips the added auxiliary-loss block while retaining the corresponding detection-training path.

\[
\omega_+=\operatorname{clip}\!\left(\frac{N_-}{\max(N_+,1)},1,k\right).
\tag{A.2}
\]

On V2X, object context is obtained from three-class softmax probabilities through a bias-free linear projection and tanh. Classification cross-entropy is evaluated only on foreground patches, with inverse-frequency class weights computed from foreground counts in the current batch and clipped according to the configuration. The separate gate retains foreground/background supervision. Table A.2 lists forward-control coefficients and auxiliary-loss weights; effective loss weights are the products of the outer and inner coefficients.

#### A.3 Optimization and sensor-combination supervision

K-Radar fusion models use pretrained single-modality encoders. Their parameters are frozen, while BatchNorm statistics follow the original training mode. The configuration uses AdamW, an initial learning rate of \(10^{-3}\), a minimum learning rate of \(10^{-4}\), weight decay of 0.01, batch size 2, and the cosine schedule of the original training entry point, with an 11-epoch limit. Checkpoint selection is described in Section B.2. On V2X, the shared backbone initializes its camera ResNet-50 from ImageNet and all other parameters from untrained initialization. All encoders are trained, using AdamW with an initial learning rate of \(10^{-3}\) and weight decay of 0.01. The 80-epoch schedule uses micro-batches of two and four accumulation steps, giving an effective batch size of eight, followed by cosine decay by optimizer update to \(10^{-5}\) after one warmup epoch.

K-Radar uses ASF's sensor-combination supervision (SCL) [ASF]. For three-sensor inputs, detection losses from the six one- and two-sensor branches are summed without division by the number of combinations. Subsets are selected from the controlled tokens already computed using the full input and share the modulated query. Gate, modality contribution, and context are not independently recomputed for each subset. The subset branches do not receive the additional context output residual used by the main fusion path. SCL is disabled on V2X. This implementation provides detection supervision on feature combinations and differs from the fixed-weight missing-sensor inference in Section F.

### B. Evaluation Protocols and Model Selection

#### B.1 AP computation and postprocessing

Additional evaluation settings are listed in Table B.1. K-Radar v1 uses the legacy AP aggregation, selecting every fourth value from 41 precision samples, for 11 values in total. The revised v2 implementation averages all 41 values and uses its corresponding height-center convention. Both are distinguished from the standard AP_R40 aggregation used on V2X. K-Radar's reported confidence threshold is an additional prediction-export filter applied after the detection head's score prefilter. Thus, confidence 0.0 does not remove the head-level prefilter.

For aligned v2 evaluation of L4DR, export, GT, confidence, and the effective rotated-NMS threshold are matched to Strong, with NMS set to 0.01. This differs from L4DR's native effective configuration. The resulting row therefore includes a postprocessing adaptation rather than only a change to AP aggregation. Table B.2 cross-checks AP sampling and height-center conventions with predictions fixed, illustrating why identical class names and IoU thresholds alone do not establish comparability.

#### B.2 Result provenance and checkpoint selection

The K-Radar tables distinguish archived results associated with official weights, local evaluation of official weights, and local training. The ASF archive corresponds to the reported configuration and evaluation settings, but is not described as a simultaneous frame-by-frame reevaluation with the other models. Locally trained ASF and Strong on v2 use the same pretrained encoders; local L4DR trains its native L+R network from scratch. Training data, 11 epochs, and effective batch size are matched, while pretraining cost, sensor inputs, and architecture differ.

The full v1 model and ablated variants undergo checkpoint selection using a 1,000-sample preliminary evaluation before full-set evaluation. [TO COMPLETE: subset origin and IDs or construction rule, candidate ranges, selection metric, and tie handling.] Until these records are recovered, we do not label this subset an independent validation set. The local v2 training comparison uses final-epoch weights. Strong is identified as an existing decoupled-control variant and does not validate the complete object-context path.

On V2X, the deduplicated validation set is evaluated at epoch 1 and every fifth epoch thereafter. The best checkpoint is selected by mean Moderate 3D AP at the strict class-specific IoUs, retaining the earlier epoch in a tie. After training, best and epoch-80 last checkpoints are evaluated on both raw and deduplicated validation and test sets. Test performance is not used for selection. Small numerical differences can occur between training-time validation and final independent reevaluation; their provenance is retained, and reevaluated scores are not substituted into training curves.

### C. Complete Results on K-Radar

#### C.1 Confidence thresholds and stricter matching

Table C.1 extends the main comparison to IoU 0.7 and the additional confidence setting. At confidence 0.0, ObjDec and the official ASF archive obtain 88.06 and 87.34 for 3D@0.3, a smaller difference than at confidence 0.3 in the main text; their 3D@0.5 scores are 72.83 and 72.95. Rankings and margins for fixed weights can change with export thresholds and IoU, so operating points are reported separately. ObjDec exceeds official ASF at the stricter 3D@0.7 criterion under both confidence settings, while its BEV@0.7 is slightly lower. These results characterize sensitivity to matching conditions without extending an advantage at one operating point to all metrics.

Table C.2 expands the v2 class means into per-class 3D and BEV metrics. For Bus/Truck BEV@0.7, Strong improves over locally trained ASF from 16.84 to 23.13, but remains below the 29.65 obtained by official L4DR under aligned evaluation. The per-class breakdown separates fusion comparisons under matched training schedules from references with different architectures and initialization.

#### C.2 Weather groups and aggregation

Tables C.3 and C.4 provide the complete weather breakdown. Total AP is computed from the precision–recall sequence over the entire set and cannot be reconstructed by averaging weather APs. A dash marks a class–weather group with no corresponding GT. In particular, v2 Fog contains no Bus/Truck objects and is excluded from weather averages or gain/loss counts for that class.

On v1, rainy-weather 3D@0.5 is 74.92, exceeding both ASF sources, whereas sleet yields 57.60, below both. On v2, Strong improves over locally trained ASF in most class–weather entries, with decreases for Sedan in light snow at IoU 0.3 and heavy snow at IoU 0.5. These complete breakdowns support analysis across conditions. Weather labels are not treated as controlled interventions, and weather-specific performance does not replace the main evidence for the representation design.

### D. Component Interventions and Additional Metrics

#### D.1 What each ablation changes

This section specifies the interventions in main-text Table 3. Disabling modality contribution control sets the scaling strength in Eq. (4) to zero, giving unit modality scaling while retaining representation residuals, predicted gating, and context. Disabling object context removes its supervision and its injection into queries and attention outputs. Disabling decoupling supervision sets only the shared-alignment, modality-specific similarity, and inter-branch separation loss weights to zero; both representation branches still generate features and participate in forward control. Disabling the foreground gate fixes its value to one and removes its supervision, retaining the other branches.

These definitions distinguish supervision changes, gating amplitude, and the forward paths themselves. In particular, removing decoupling supervision does not remove the shared/specific networks and is not equivalent to Concat.

#### D.2 Strict 3D matching and BEV results

Table D.1 reports 3D@0.7, BEV@0.3, and BEV@0.7, which are omitted from the main ablation table. Disabling modality contribution control reduces 3D@0.7 from 22.04 to 11.08, while BEV@0.7 remains at 61.36, close to the full model's 62.63. This intervention affects strict 3D matching and horizontal overlap differently; BEV scores alone therefore do not characterize its effect on 3D localization. All four ablations underperform the full model on the listed supplementary metrics. These observations follow the current single-seed experiments and selection procedure and do not establish statistical significance.

#### D.3 Fixed-weight spatial-gate and context interventions

Table D.2 complements the retrained ablations with inference-time interventions on the final K-Radar v1 checkpoint. Each setting uses the same encoded features per frame. Replacing the gate by its frame-wise mean preserves its mean amplitude but removes spatial variation; permuting its values preserves the per-frame distribution while changing correspondence with local features. The three fixed seeds are repeated permutations, not independently trained models. GT is not used to generate the modified signals.

Frame-mean gates reduce 3D@0.3/BEV@0.5 from 88.36/88.11 to 53.90/53.16, while the three permutations average 21.29/21.01. This supports the trained model's dependence on spatial correspondence. The same gate affects token residuals, modality scaling, and gated context; this experiment does not isolate those paths or attribute the entire decline to representation decoupling. Internal-signal distribution changes also distinguish these results from retraining without a gate.

Jointly removing the query and output context increments changes 3D@0.3 and BEV@0.5 by \(-0.0146\) and \(-0.0087\) percentage points, respectively; all six overall AP changes have magnitudes below 0.08 points. Removing these residual increments retains cross-modal attention and the trained representations. These results do not establish independently large inference contributions for the context paths, nor do they remove their possible training-time effects. The paired baseline is evaluated in the same pass as the interventions and is kept separate from the historical main-table scores.

### E. Representation Statistics and Additional Visualizations

#### E.1 Statistical units and weighted PCA

For frame \(i\), modality \(m\), and location \(p\), let \(x_{im}^p\) denote a representation and \(\mathcal P_i\) the GT foreground locations. Equation (E.1) defines the frame-mean vector \(\mu_{im}\) and the mean matched-location cosine \(s_i^{mn}\). Weather-group cosines average \(s_i^{mn}\) equally over frames. This differs both from taking the cosine of frame-mean vectors and from pooling all patches with equal patch weights. All 10,065 analyzed frames contain valid foreground, totaling 642,649 foreground spatial locations. Table E.1 separates modality pairs.

\[
\mu_{im}=\frac{1}{|\mathcal P_i|}\sum_{p\in\mathcal P_i}x_{im}^p,\qquad
s_i^{mn}=\frac{1}{|\mathcal P_i|}\sum_{p\in\mathcal P_i}\operatorname{cos}(x_{im}^p,x_{in}^p).
\tag{E.1}
\]

Input, Shared, and Specific each have a separately fitted PCA basis. Within each representation type, all modalities and weather groups share that basis. PCA is fitted to \(\mu_{im}\), weighting each vector by \(1/(|\mathcal W|N_wM)\), where \(N_w\) is its weather-group frame count and \(M=3\). The leading two eigenvectors of the weighted centered covariance are used, without per-vector normalization or channel standardization. Each weather group and modality therefore contributes equally to fitting. Different representation columns have different bases and scales, so absolute Euclidean distances are not compared across columns.

The seven-weather scatter plot displays up to 400 frames per weather group, including all 383 overcast frames. Displayed frame indices are shared across modalities and representation panels; centroids and density contours use all frames. With the random seed and PCA bases fixed, we do not refit for visual separation, add jitter, or clip outliers. Figure E.1 expands the main PCA visualization to all weather groups.

#### E.2 High-dimensional similarity distributions and weather variation

Table E.1 shows that Specific features are not approximately orthogonal for every modality pair: C–R cosines remain around 0.65 across the seven weather groups, while pairs involving LiDAR vary more across groups. This is compatible with the relative organization encouraged by the two branches and does not require modality-specific features to contain no information in common.

Figure E.2 and Table E.2 further show frame-level similarity distributions. The L–R Shared medians are 0.9632 in normal weather and 0.9662 in heavy snow. For Specific, the 5th–95th percentile range changes from 0.2113–0.4948 to 0.2578–0.7363. Violin width represents empirical density; thick and thin intervals show the 25th–75th and 5th–95th percentiles. These describe across-frame variability, not confidence intervals.

As an aggregation-sensitivity check, equal weighting of sequences gives mean cross-modal Specific cosines of approximately 0.440/0.584 in normal/heavy-snow conditions, compared with 0.446/0.537 under equal frame weighting. Shared features retain high consistency, while the precise Specific difference depends on aggregation weights. Weather is associated with sequence, scene, and object composition. High cosine values also cannot exclude a common dominant direction or low variance. These statistics are therefore interpreted together with component ablations, rather than as independent proof of semantic identifiability or a causal weather effect.

**Frame-level correspondence controls.** Figure E.3 compares cosines of foreground-mean vectors for the same frame and for different-sequence frames within the same weather group, using ten fixed permutation seeds. Matched scores use the same retained anchors. Before centering, Shared C--L, C--R, and L--R cosines are 0.979214/0.970201/0.987697 for matched pairs and 0.979205/0.970225/0.987136 for mismatches. After subtracting each modality's weather-group mean, the matched/mismatched L--R values are 0.148740/\(-0.014689\), while the camera-related matched values remain close to zero. Thus, a common mean direction can account for much of the high uncentered frame-level similarity. This check does not resolve patch-level correspondence because frame averaging discards local information; it also does not isolate the contribution of the Shared branch. It is a control on the interpretation of similarity, rather than proof of either semantic decomposition or branch redundancy.

#### E.3 Construction of gate and detection visualizations

Main-text Figure 4 presents three scenes with camera predictions, complete LiDAR BEV and gate maps, and gate detail windows. Foreground/background gate means are 0.213/0.128, 0.259/0.115, and 0.288/0.118 from top to bottom. Full maps cover forward \(x\in[0,72]\) m and lateral \(y\in[-6.4,6.4]\) m; detail windows span 14\(\times\)8.4 m. The gate uses the native 16\(\times\)90 array and a common [0,1] scale without smoothing. Camera panels show the selected target's GT, while BEV and gate panels retain all GT references within the displayed region. GT overlays and regional statistics are added after feature-based prediction; no prior detector provides the gate.

Figure E.4 separately retains the seven-weather gate examples selected from 21 complete-gate candidates for scene readability, object arrangement, and local responses. During that export, GT fields were withheld at the fusion-module input and used only afterward. One historical candidate with unexplained repeated-inference differences was excluded. Table E.3 summarizes these seven appendix examples, not the three main-text scenes. Figure E.5 adds the full-test analysis: equally weighted frame-level foreground/background gate means are 0.2701/0.1176, and foreground means exceed background means in 99.06\% of frames. Selected examples and full-test statistics have different sampling units and are reported separately.

Figure E.6 compares strictly loaded released ASF and final ObjDec checkpoints on identical test frames, using FP32, batch size 1, the same detection postprocessing, and a score\(>0.3\) filter. Input-tensor hashes and GT were checked for all 20 candidates in the paired visualization pool. Original camera images, sequence-specific calibration, intrinsics, and distortion are retained. Both methods use identical camera crops, complete BEV ranges, and 12\(\times\)6 m BEV detail windows. The selected objects' maximum geometric 3D IoUs among retained predictions change from 0.572/0.000/0.000 to 0.719/0.476/0.741 from top to bottom. These values are neither AP nor the official one-to-one matching outcome; the middle example remains below IoU 0.5.

Figure E.7 adds heavy- and light-snow examples: the selected objects' maximum 3D IoUs change from 0.095 to 0.728 and from 0.354 to 0.223, respectively. The latter also has a locally high gate response, illustrating that foreground-related activation is insufficient to determine final box accuracy. The complete 20-frame candidate atlas is retained as an archival asset; it is not repeated in the manuscript. Selected qualitative cases do not estimate aggregate detection gains.

### F. Sensor Availability and Corrupted Inputs

#### F.1 Two input interventions

When a modality is removed, only the remaining sensor features are supplied to fusion, and gating, modality contributions, and context are recomputed for that set. Corrupted inputs instead retain the corresponding branch. C* replaces the raw RGB image with a black frame before the original normalization and camera encoder. L* uses a no-return convention: height-compressed sparse LiDAR features are zeroed before the original dense BEV backbone. This avoids sparse operators that do not support empty inputs; its precise interpretation is a no-return simulation at that feature interface.

All ten settings use one fixed checkpoint within each dataset version, without retraining or checkpoint selection per combination. Tables F.1 and F.2 report the full v1 ObjDec and v2 Strong, respectively. Unlike the SCL path in Section A.3, which reuses full-input controlled tokens, missing-sensor inference recomputes fusion control from the features actually available.

#### F.2 Threshold effects, sensor dependence, and the ASF reference

Beyond the complete-input and two-sensor combinations discussed in the main text, Tables F.1 and F.2 add single-sensor inputs, corrupted inputs, and the second confidence setting. On v2, C+L*+R obtains mean 3D@0.3 of 27.99 at confidence 0.3 and 34.70 at confidence 0.0. Removing LiDAR, C+R, yields 34.25 and 34.73 at those thresholds. Retaining a corrupted branch and removing that branch are not always equivalent across operating points.

Black-frame C*+L+R remains close to complete-input performance, while camera-only predictions are weak. This combination establishes limited sensitivity to that particular camera-input change; a low camera contribution could also produce such behavior. The substantial decline without LiDAR indicates continued sensor dependence. If AP retention is reported, its denominator is complete-input AP for the same checkpoint and threshold; it is not interpreted as object recall.

ASF Table 3 [ASF] provides a reference for similar availability settings, but its precise corruption rules and camera-only evaluation scope are not fully matched to the local protocol. This appendix primarily compares input settings within fixed weights and does not use the starred rows for a strict cross-method robustness ranking.

### G. Cross-Dataset Architecture Adaptation

#### G.1 Data processing and the common backbone

We use 8,391 training frames from the public package. The raw validation/test sets contain 1,498/1,501 frames and become 1,487/1,486 after deduplication. Car, Truck, and Bus are merged into Vehicle; the other classes are Pedestrian and Cyclist. ROI, difficulty, and IoU settings are listed in Table B.1. Local adaptation additionally includes ROI-based GT filtering, calibrated 2D box projection for difficulty filtering, and an intersection-area numerical correction. Dataset version, reporting split, and spatial coverage differ from the published benchmark tables [V2X-Radar]; the results here extend the local architectural comparison defined in the main text.

The camera branch combines ResNet-50 multiscale features with a learned depth distribution and LSS projection to BEV, using 288×512 input images. LiDAR and radar use independent PillarVFE, scatter, and BEV convolutional stems, with four and six point fields, respectively. Each pillar contains at most 32 points, and at most 32,000 pillars are retained. Each modality outputs 64 channels. Fusion produces 128 channels before the common multiscale BEV backbone; the detection head receives 384 channels and uses anchors determined from training-set statistics.

Common encoder and detection-head tensors are copied from the same untrained initialization, without warm-starting from a trained target-dataset checkpoint. Augmentations include global rotation within ±0.392699 radians, scaling within [0.95,1.05], and flipping with probability 0.5. Camera geometry and point clouds share the same spatial transform. Other training settings are provided in Section A.3.

#### G.2 Fusion structures and spatial resolution

Concat applies a 3×3 convolution, BatchNorm, and ReLU after channel-wise BEV concatenation, learning combinations across modalities and neighboring locations. ASF-style uses common projection, local attention, and PFT. ObjDec jointly incorporates the representation, gating, modality-contribution, and context paths from Section 3 into fusion. The three-sensor group shares encoders and a detection head. ObjDec-LR is trained with only LiDAR and radar branches from the outset; comparisons with L4DR retain their native architectural differences.

The 0.4 m and 0.16 m settings use BEV grids of 256×256 and 640×640, respectively, with detection-head stride two relative to BEV. The earlier 4×4 patch setting uses 16 queries, and the 2×2 setting uses four; both output 128 channels. Physical patch coverage changes from 1.6 m or 0.8 m at a 0.4 m grid to 0.32 m at a 0.16 m grid. Grid and patch changes therefore alter both computation and the size of local fusion regions relative to objects.

#### G.3 Supplementary results under the full training budget

The main Table 4 presents published references and local fusion comparisons; this section additionally reports the Concat control on the common backbone. Table G.1 retains the earlier 0.4 m group, selected epochs, and corresponding validation/test scores omitted from the main table. Table G.2 adds per-class BEV and last-epoch results for completed 0.16 m runs. At 0.4 m, changing ObjDec from 4×4 to 2×2 patches increases test Pedestrian 3D AP from 58.75 to 62.36 and mean 3D AP from 72.22 to 74.03. This change also modifies the query count. Concat obtains mean test 3D AP of 75.77 at 0.4 m and 81.90 at 0.16 m, showing that the common detection backbone also benefits from finer grids. Gains from finer resolution cannot all be attributed to ObjDec. At 0.16 m, validation-selected ObjDec trails Concat by 0.52 and 0.20 percentage points in mean test 3D and BEV AP, respectively; these results do not establish superiority over all evaluated fusion architectures.

All five 0.16 m runs have completed 80 training epochs and final best/last evaluations. Validation-selected three-sensor ObjDec at epoch 70 obtains mean test 3D/BEV AP of 81.38/86.27, compared with 81.55/86.35 at epoch 80. ObjDec-LR obtains 79.65/83.81 at its selected epoch 75 and 79.75/83.80 at epoch 80. Last-checkpoint test differences do not change the validation-based selection rule. ASF-style and L4DR both select epoch 80. Relative to L4DR, ObjDec-LR improves class-wise 3D AP by 0.71/1.58/1.93 points and BEV AP by 0.29/1.73/1.73 points. Relative to ASF-style, three-sensor ObjDec improves Cyclist 3D and BEV AP by 0.95/1.21 points, with small decreases in Vehicle 3D and BEV AP. [FIGURE TO PREPARE: complete 80-epoch validation curves for Figure G.1; all required validation checkpoints are available.] Curves use actual validation checkpoints without combining per-class maxima from different models.

#### G.4 Additional architecture adaptation on VoD

**Setup.** We supplement the main V2X-Radar-V evaluation by training a LiDAR–4D-radar version within a native PointPillars detection backbone on VoD, using 5,139 training and 1,296 validation frames. Inputs comprise one LiDAR frame and five radar frames. Both recent ObjDec runs use a 0.16 m grid, a 320×320 BEV, 2×2 patches, and four queries. Each modality has two 64-channel 3×3 Conv–BN–ReLU layers for local encoding, followed by token LayerNorm. Both models are trained from scratch for 80 epochs with seed 666, FP32, Adam OneCycle, and a peak learning rate of 0.003. A microbatch of eight with two accumulation steps gives an effective batch size of 16. Full validation is performed every five epochs; checkpoints are selected by official EAA mean AP and used unchanged for DC and other metrics. The score and NMS thresholds remain 0.1 and 0.01.

**Anchor adaptation.** The second run changes only class-specific anchor dimensions and bottom heights. Priors are computed from training annotations before augmentation, transformed into LiDAR coordinates and filtered using the native training ROI's box-center rule. Dimension and bottom-height medians are rounded to 0.01 m, without fitting to validation annotations. Length/width/height values for Car, Pedestrian, and Cyclist are 4.19/1.81/1.52, 0.65/0.63/1.69, and 1.94/0.78/1.76 m, with bottom heights of −1.65, −1.62, and −1.68 m. This comparison evaluates the joint change in dimensions and heights.

**Results.** Tables G.3a/G.3b use official VoD region/class filtering and 11-point 3D AP, with IoU thresholds of 0.5/0.25/0.25 for Car/Pedestrian/Cyclist. EAA and DC denote the Entire Annotated Area and Driving Corridor; both report 3D detection. The 2×2-patch model with local encoding selects epoch 75 and obtains EAA/DC of 71.23/84.69. Adapted anchors select epoch 80 and yield 72.03/83.76. The 0.80-point EAA gain is primarily associated with a 4.51-point Cyclist improvement, while DC decreases by 0.93 points. Relative to the local L4DR reference, EAA is 1.03 points higher and DC is 1.08 points lower; aggregate EAA/DC remain below the published L4DR results [L4DR]. Table G.4 additionally reports KITTI AP_R40 for the same checkpoints: Moderate mean 3D AP changes from 78.64 to 78.35, whereas BEV AP increases from 80.55 to 80.92, showing a tradeoff across metrics.

**Comparison scope.** Historical PP-Concat uses AMP and a physical batch size of 16, and the earlier ObjDec is initialized from Concat. Local L4DR uses 100 epochs, two GPUs, and SyncBN; its epoch-99 checkpoint is the better of the evaluated late-stage candidates. These rows provide historical and external architectural references with differing training conditions. A Concat reference with the same local encoding and training settings is not yet available, so the combined gains over the historical baseline cannot be attributed entirely to representation decoupling. These results support architecture adaptation after training on VoD, without establishing zero-shot transfer or overall state-of-the-art performance on VoD.

### H. Efficiency Measurement and Scope

#### H.1 Paired timing protocol

Timing uses an RTX A6000, batch size 1, four PyTorch CPU threads, FP32 tensors, and no autocast. The original environment's matmul/cuDNN TF32 settings remain enabled; cuDNN deterministic is enabled and benchmark is disabled. The PyTorch version is 1.10.1+cu113. We sample 120 test indices uniformly, using the first 20 for warmup and the remaining 100 for timing, and repeat the same frames in two rounds.

Each frame's CPU input is copied for the eager and Graph paths, alternating their order and synchronizing each measurement. Model order is ObjDec, ASF, ASF, ObjDec. Timing covers the network call, including point-cloud preprocessing, host-to-device transfer, encoding, fusion, decoding, NMS, and GT recall computation in the original evaluation path. Disk access, collation, initial graph capture, initialization, and result verification are excluded. Training on other GPUs remains active, so host load is not fully isolated. Table H.1 adds median, P95, and timing standard deviation; very small mean-latency differences are not interpreted as stable architectural advantages.

#### H.2 Graph replay and numerical checks

CUDA Graph captures only the repeated camera-Swin and fusion computations. Each frame supplies new images and BEV features and executes the captured operators; calibration is read per frame, and predictions are not cached across frames. Inputs with different shapes, sensor sets, or visualization requirements fall back to eager execution according to the implementation conditions.

The paired runs checked 240 forwards for each model. Under identical captured inputs, all capture checks were exact. Across the full paths, all checked tensors were exactly equal in 218/240 cases for each model; repeated eager checks also showed variation in the unmodified radar path. Label arrays matched in 238/240 cases for ObjDec and 235/240 for ASF. These sampled checks therefore do not establish complete numerical equivalence of the full inference pipeline.

All four timing runs encountered a native exit error after their result files had been written. An independent read verified the stored timing and comparison records; the original profiling path exhibited a similar exit issue. The two visualization inference jobs likewise completed their exports before native exit errors, and their output files were checked independently. Full-test AP has not been reevaluated for the Graph path. We therefore report measured latency and sampled checks, without claiming fully validated deployment or unchanged full-set detection accuracy.

#### H.3 Scope of the evidence

The experiments use the current single-seed training and checkpoint-selection procedures, with part of the v1 preliminary-selection record still to be documented. Strong on v2 does not contain the complete object-context path. V2X and VoD experiments train on their target datasets and establish adaptation under the stated protocols, rather than zero-shot transfer. Sensor-availability results retain weak camera-only performance and a marked dependence on LiDAR. Finally, cosine constraints and foreground supervision organize representations but do not establish an identifiable semantic decomposition, statistical independence, or an exact reconstruction identity \(c+u=t\). These boundaries delimit what the present ablations and visualizations support.

## 三、共用附表 / Shared supplementary tables

所有AP均以百分数报告，AP差值为百分点。除另有说明外，显示值保留两位小数，差值从未舍入数据计算。`—`表示不适用或无该类GT，`NR`表示本稿尚无已核查的记录，`Pending`表示最终实验结果待补。C、L、R分别为相机、LiDAR、四维雷达。表格随对应附录小节排版，此处集中维护一套数字。

AP is reported in percent and AP differences in percentage points. Values are rounded to two decimals unless specified otherwise; differences use unrounded records. A dash denotes an inapplicable item or absence of class GT, NR an unverified record in this draft, and Pending an unavailable final experiment result. C, L, and R denote camera, LiDAR, and 4D radar. Tables are maintained once here and placed alongside their corresponding sections in the manuscript.

<a id="table-a1"></a>
### Table A.1. 表征与融合尺寸 / Representation and fusion dimensions

| Item | K-Radar v1 ObjDec | K-Radar v2 Strong | V2X ObjDec, 2×2 |
| --- | --- | --- | --- |
| Input BEV channels, C/L/R | 256 / 512 / 768 | 256 / 512 / 768 | 64 / 64 / 64 |
| Common projection channels | 256 | 256 | 64 |
| Token dimension | 256 | 256 | 128 |
| Shared/specific MLP hidden dimension | 256 | 256 | 128 |
| Patch size, BEV cells | 2×2 | 2×2 | 2×2 |
| Queries per patch | 32 | 32 | 4 |
| Attention heads | 16 | 16 | 8 |
| Reassembled fusion channels | 2048 | 2048 | 128 |
| Gate / modality-score hidden dimensions | 128 / 128 | 128 / 128 | 128 / 128 |
| Object-context hidden dimension | 160 | — | 160 |
| Context target and activation | Objectness, sigmoid | — | 3 classes, softmax |
| Query/output context modulation | Enabled | — | Enabled |
| Sensor-combination supervision | Enabled | Enabled | Disabled |

**中文。** 输入通道按C/L/R排列。V2X-LR去掉相机编码器，其余相应融合尺寸不变。旧V2X 4×4版本采用16个query，token为128维，重组后仍为128通道。共享与模态特有分支输出维度均与token维度一致。

**English.** Input channels are ordered C/L/R. V2X-LR omits the camera encoder while retaining the corresponding fusion dimensions. The earlier V2X 4×4 variant uses 16 queries and 128-dimensional tokens, also producing 128 reassembled channels. Both representation branches preserve token dimensionality.

<a id="table-a2"></a>
### Table A.2. 控制与监督系数 / Control and supervision coefficients

| Item | v1 ObjDec | v2 Strong | V2X ObjDec |
| --- | --- | --- | --- |
| FG margin \(\epsilon\), m | 0.7 | 0.6 | 0.7 |
| Specific similarity margin \(\delta\) | 0.1 | 0.1 | 0.1 |
| Modality scaling strength \(\eta\) | 0.75 | 0.65 | 0.75 |
| Residual strength \(\lambda\) | 0.08 | 0.08 | 0.08 |
| Temperature \(\tau\) | 1.0 | 1.0 | 1.0 |
| Modality scale clipping interval | [0.4, 2.1] | [0.45, 2.0] | [0.4, 2.1] |
| Gate range | [0, 1] | [0, 1] | [0, 1] |
| Gate initial bias | −1.2 | −1.5 | −1.2 |
| Query / output context strength, \(\beta / \gamma\) | 0.16 / 0.06 | — | 0.16 / 0.06 |
| Outer auxiliary weight, \(\lambda_{\rm aux}\) | 0.12 | 0.10 | 0.12 |
| Inner common / specific / separation weights | 0.12 / 0.015 / 0.10 | 0.12 / 0.015 / 0.10 | 0.12 / 0.015 / 0.10 |
| Inner gate / context weights | 0.15 / 0.30 | 0.12 / — | 0.15 / 0.30 |
| Effective common / specific / separation weights | 0.0144 / 0.0018 / 0.012 | 0.012 / 0.0015 / 0.010 | 0.0144 / 0.0018 / 0.012 |
| Effective gate / context weights | 0.018 / 0.036 | 0.012 / — | 0.018 / 0.036 |
| Gate positive-weight cap | 30 | 30 | 30 |
| Objectness / foreground-class weight cap | 4 | — | 4 |
| SCL coefficient | 1.0 | 1.0 | 0 |

**中文。** 系数对应正文公式，主配置未启用控制强度退火。Strong的context项不存在，不将其写为已训练但仅在推理时关闭。V2X的类别权重与v1二元正样本权重有不同定义，见A.2。

**English.** Coefficients follow the main-text equations. The primary configurations do not anneal control strength. Strong has no context path, rather than a trained path disabled only at inference. V2X foreground-class weights differ from v1 binary positive weights as described in Section A.2.

<a id="algorithm-a1"></a>
### Algorithm A.1. 前向计算与训练监督的分工 / Forward computation and training supervision

```text
Input: available sensor observations X; model variant; optional training GT
1  Encode X and project BEV features into spatially corresponding patch tokens t.
2  Compute shared c and modality-specific u for every available patch and modality.
3  Predict foreground gate g and modality contributions from c and u.
4  If the variant uses object context, predict context z from its context head.
5  Construct controlled tokens and queries using the main-text forward equations.
6  Apply local cross-modal attention, the enabled context output residual, and PFT.
7  Reassemble the BEV feature and obtain predictions from the detection head.
8  If training:
9      Compute the detector's training losses using GT.
10     If SCL is enabled, add detection losses on the six controlled-token subsets.
11     Construct foreground/context targets from valid GT boxes using Eq. (A.1).
12     If valid foreground exists and at least two modalities are available:
13         Add foreground representation losses, gate loss, and enabled context loss.
14     Return predictions and the total loss with Table A.2 coefficients.
15 Return predictions.
```

**中文。** 伪代码说明数据依赖，不指定底层算子的实际执行顺序。第1–7步共用于训练和推理，GT从第9步起只参与监督；第11步的前景集合不替代第3步的预测gate。第10步遵循A.3中的SCL实现，V2X跳过该步。输出损失采用正文式（7），不再次展开相同公式。

**English.** The pseudocode specifies data dependencies rather than low-level operator scheduling. Steps 1–7 are shared by training and inference; GT enters supervision from step 9 onward. The target foreground set in step 11 does not replace the predicted gate in step 3. Step 10 follows the SCL implementation in Section A.3 and is skipped on V2X. Losses follow main-text Eq. (7).

<a id="table-b1"></a>
### Table B.1. 附加协议细节 / Additional protocol details

| Setting | K-Radar v1 | K-Radar v2 | V2X-Radar-V local adaptation |
| --- | --- | --- | --- |
| Evaluated classes | Sedan | Sedan; Bus/Truck | Vehicle; Pedestrian; Cyclist |
| Test frames | 10,065 | 13,727 | 1,486 deduplicated; 1,501 raw |
| Validation frames | Selection subset: B.2 | Final-epoch local comparison | 1,487 deduplicated; 1,498 raw |
| x / y / z range, m | [0,72] / [−6.4,6.4] / [−2,6] | [0,72] / [−16,16] / [−2,7.6] | [0,102.4) / [−51.2,51.2) / [−5,3) |
| Reported difficulty | Project legacy class evaluation | Project revised class evaluation | Moderate |
| Primary class IoUs | 0.3 / 0.5 / 0.7 for Sedan | 0.3 / 0.5 / 0.7 for both classes | 0.7 / 0.5 / 0.5 by class |
| Additional loose IoUs | — | — | 0.5 / 0.25 / 0.25 by class, in raw reports |
| AP aggregation | 11 values from 41 precision samples | Mean of 41 precision values | AP_R40 |
| 3D evaluator z-center parameter | 1.0 | 0.5 | Native V2X evaluation convention |
| Head score prefilter | 0.1 | 0.1 | 0.001 |
| Additional export confidence filter | 0.3; 0.0 supplement | 0.3; 0.0 for availability supplement | No K-Radar-style additional 0.3 filter |
| Effective rotated-NMS IoU | 0.01 | 0.01 for aligned comparison | 0.1 |
| Max detections in local V2X postprocessing | — | — | 500 per class |

**中文。** 同一数据集列中的条目不意味着各方法有相同初始化或训练成本，来源区别见B.2。v1的1,000样本仅按已知用途写作selection subset，所属划分待核实。坐标范围列帮助解释协议差异，主表仍保留必要范围说明。

**English.** Sharing a dataset column does not imply matched initialization or training cost; provenance is specified in Section B.2. The v1 1,000-sample set is identified only by its known selection role, pending confirmation of its split origin. Spatial ranges clarify protocol differences and do not replace essential main-table disclosures.

<a id="table-b2"></a>
### Table B.2. 固定预测的v2评测器交叉检查 / v2 evaluator cross-check with fixed predictions

| Checkpoint | Precision values averaged | z-center | Mean 3D@0.3 | Mean 3D@0.5 |
| --- | --- | --- | --- | --- |
| Strong | 11 | 1.0 | 62.01 | 39.46 |
| Strong | 11 | 0.5 | 63.26 | 43.66 |
| Strong | 41 | 1.0 | 63.93 | 40.04 |
| Strong | 41 | 0.5 | 66.91 | 43.05 |
| L4DR released | 11 | 1.0 | 66.44 | 46.37 |
| L4DR released | 11 | 0.5 | 70.86 | 47.75 |
| L4DR released | 41 | 1.0 | 67.43 | 45.27 |
| L4DR released | 41 | 0.5 | 69.48 | 48.23 |

**中文。** 两类均值，conf=0.3。每个checkpoint内保持GT、预测、NMS和置信度不变，仅交叉改变precision汇总与3D IoU高度中心。改变z-center不影响BEV几何IoU，但AP采样规则仍影响BEV AP。该检查不解释公开论文与本地结果差异中的全部因素。

**English.** Two-class means at confidence 0.3. GT, predictions, NMS, and confidence are fixed within each checkpoint; only precision aggregation and the 3D IoU height-center convention change. The z-center parameter does not affect geometric BEV IoU, whereas AP sampling still affects BEV AP. This check does not account for every difference between published and local results.

<a id="table-c1"></a>
### Table C.1. v1完整指标与置信度 / Complete v1 metrics and confidence settings

| Method | conf | 3D@0.3 | 3D@0.5 | 3D@0.7 | BEV@0.3 | BEV@0.5 | BEV@0.7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | 0.3 | 80.31 | 67.19 | 18.85 | 80.78 | 80.33 | 62.85 |
| ASF released archive | 0.0 | 87.34 | 72.95 | 18.85 | 88.59 | 86.97 | 62.85 |
| ASF local | 0.3 | 88.57 | 67.49 | 18.69 | 89.01 | 80.36 | 61.59 |
| ASF local | 0.0 | 87.96 | 72.96 | 18.68 | 88.80 | 87.41 | 61.57 |
| ObjDec | 0.3 | 88.36 | 67.50 | 22.04 | 88.84 | 88.10 | 62.63 |
| ObjDec | 0.0 | 88.06 | 72.83 | 22.02 | 88.84 | 87.18 | 62.63 |

**中文。** 同一方法两行使用同一权重；conf表示检测头预过滤之外的导出阈值。官方ASF行为权重对应归档。部分主指标为便于核对保留，新增严格IoU与阈值设置构成补充。

**English.** Each pair uses the same checkpoint and changes the export confidence filter, in addition to the detector prefilter. Released ASF results are checkpoint-associated archives. Main metrics are retained as anchors for the additional IoU and threshold results.

<a id="table-c2"></a>
### Table C.2. v2逐类完整指标 / Complete class-wise v2 metrics

| Method | Class | 3D@0.3 | 3D@0.5 | 3D@0.7 | BEV@0.3 | BEV@0.5 | BEV@0.7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | Sedan | 74.98 | 52.09 | 11.85 | 77.85 | 71.70 | 43.21 |
| ASF released archive | Bus/Truck | 58.13 | 31.06 | 7.93 | 67.85 | 53.21 | 20.85 |
| L4DR released, aligned | Sedan | 76.79 | 54.68 | 11.23 | 79.90 | 73.61 | 49.16 |
| L4DR released, aligned | Bus/Truck | 62.17 | 41.78 | 10.49 | 67.12 | 56.86 | 29.65 |
| ASF local | Sedan | 74.45 | 51.52 | 11.58 | 77.37 | 71.11 | 42.23 |
| ASF local | Bus/Truck | 55.09 | 27.88 | 7.52 | 64.27 | 46.43 | 16.84 |
| L4DR local | Sedan | 74.49 | 54.28 | 14.08 | 75.13 | 71.59 | 48.20 |
| L4DR local | Bus/Truck | 56.58 | 33.39 | 5.56 | 61.46 | 49.86 | 22.50 |
| DecControlled Strong | Sedan | 74.58 | 52.14 | 12.31 | 77.32 | 71.27 | 44.26 |
| DecControlled Strong | Bus/Truck | 59.24 | 33.97 | 9.92 | 65.14 | 50.59 | 23.13 |

**中文。** conf=0.3。补充正文以两类Mean为主的比较。Strong不含object context；本地训练组匹配训练集、11轮与有效batch，初始化和模态差异见B。

**English.** Confidence is 0.3. These class-wise results complement the class means in the main text. Strong omits object context. Local runs match the training split, 11 epochs, and effective batch size; initialization and modality differences are specified in Appendix B.

<a id="table-c3"></a>
### Table C.3. v1天气分组 / Weather-wise v1 3D AP

| Method | IoU | Total | Normal | Overcast | Fog | Rain | Sleet | Light snow | Heavy snow |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | 0.3 | 80.31 | 79.57 | 89.89 | 90.67 | 80.97 | 80.20 | 80.89 | 71.71 |
| ASF local | 0.3 | 88.57 | 87.83 | 90.16 | 90.77 | 80.92 | 80.51 | 89.45 | 71.64 |
| ObjDec | 0.3 | 88.36 | 87.66 | 90.39 | 90.57 | 88.90 | 80.42 | 89.28 | 71.41 |
| ASF released archive | 0.5 | 67.19 | 64.56 | 79.71 | 79.57 | 67.33 | 67.28 | 77.63 | 61.61 |
| ASF local | 0.5 | 67.49 | 64.70 | 80.10 | 79.59 | 68.31 | 66.82 | 78.46 | 61.67 |
| ObjDec | 0.5 | 67.50 | 65.98 | 80.26 | 79.71 | 74.92 | 57.60 | 78.33 | 60.51 |

**中文。** Sedan，conf=0.3。Total在整个评测集合上重新计算，不是天气AP均值。

**English.** Sedan at confidence 0.3. Total is evaluated over the combined set and is not an average of weather APs.

<a id="table-c4a"></a>
### Table C.4a. v2天气分组 AP3D@0.3 / Weather-wise v2 3D AP

| Method | Class | Total | Normal | Overcast | Fog | Rain | Sleet | Light snow | Heavy snow |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | Sedan | 74.98 | 74.14 | 82.35 | 92.26 | 66.37 | 70.43 | 88.24 | 63.61 |
| L4DR released, aligned | Sedan | 76.79 | 75.52 | 83.57 | 93.60 | 78.25 | 67.17 | 87.71 | 58.49 |
| ASF local | Sedan | 74.45 | 73.45 | 82.15 | 92.09 | 65.80 | 70.81 | 89.77 | 63.36 |
| L4DR local | Sedan | 74.49 | 73.12 | 80.06 | 92.33 | 76.27 | 54.55 | 82.74 | 51.99 |
| DecControlled Strong | Sedan | 74.58 | 73.51 | 84.30 | 94.46 | 68.11 | 72.52 | 89.56 | 63.57 |
| ASF released archive | Bus/Truck | 58.13 | 53.28 | 75.33 | — | 7.89 | 59.55 | 88.26 | 68.20 |
| L4DR released, aligned | Bus/Truck | 62.17 | 56.27 | 87.43 | — | 2.96 | 74.75 | 80.47 | 63.76 |
| ASF local | Bus/Truck | 55.09 | 50.39 | 65.31 | — | 3.59 | 50.78 | 84.75 | 68.02 |
| L4DR local | Bus/Truck | 56.58 | 54.60 | 82.07 | — | 7.81 | 59.89 | 89.16 | 54.27 |
| DecControlled Strong | Bus/Truck | 59.24 | 51.63 | 73.82 | — | 10.08 | 57.47 | 89.56 | 72.34 |

**中文。** conf=0.3；“—”表示该天气无此类别GT，不能作为零分参与平均。

**English.** Confidence is 0.3. A dash indicates no GT objects of the class in that weather group and is excluded from any class–weather comparison.

<a id="table-c4b"></a>
### Table C.4b. v2天气分组 AP3D@0.5 / Weather-wise v2 3D AP

| Method | Class | Total | Normal | Overcast | Fog | Rain | Sleet | Light snow | Heavy snow |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | Sedan | 52.09 | 49.63 | 53.38 | 80.55 | 46.85 | 44.05 | 59.25 | 49.52 |
| L4DR released, aligned | Sedan | 54.68 | 50.21 | 56.53 | 83.81 | 53.03 | 47.42 | 62.32 | 53.33 |
| ASF local | Sedan | 51.52 | 48.90 | 57.16 | 79.89 | 45.96 | 44.83 | 59.25 | 51.24 |
| L4DR local | Sedan | 54.28 | 52.33 | 49.24 | 83.44 | 54.95 | 41.22 | 59.28 | 38.72 |
| DecControlled Strong | Sedan | 52.14 | 49.39 | 59.62 | 80.30 | 48.30 | 49.13 | 60.75 | 50.49 |
| ASF released archive | Bus/Truck | 31.06 | 23.93 | 47.04 | — | 2.48 | 38.83 | 70.81 | 32.55 |
| L4DR released, aligned | Bus/Truck | 41.78 | 36.60 | 76.06 | — | 0.68 | 62.92 | 53.30 | 41.11 |
| ASF local | Bus/Truck | 27.88 | 21.16 | 46.68 | — | 1.94 | 30.29 | 70.58 | 32.28 |
| L4DR local | Bus/Truck | 33.39 | 32.18 | 55.89 | — | 6.60 | 43.05 | 69.00 | 17.00 |
| DecControlled Strong | Bus/Truck | 33.97 | 23.94 | 49.65 | — | 5.05 | 38.48 | 75.09 | 39.37 |

**中文。** conf=0.3；“—”表示该天气无此类别GT，不能作为零分参与平均。

**English.** Confidence is 0.3. A dash indicates no GT objects of the class in that weather group and is excluded from any class–weather comparison.

<a id="table-d1"></a>
### Table D.1. 正文消融的补充指标 / Additional ablation metrics

| Variant | 3D@0.7 | BEV@0.7 | BEV@0.3 |
| --- | --- | --- | --- |
| Full ObjDec | 22.04 | 62.63 | 88.84 |
| w/o modality contribution control | 11.08 | 61.36 | 80.38 |
| w/o object context | 17.10 | 54.91 | 80.68 |
| w/o decoupling supervision | 16.49 | 55.71 | 80.65 |
| w/o foreground gate | 19.41 | 55.49 | 80.65 |

**中文。** v1，conf=0.3；正文已展示的3D@0.3/@0.5及BEV@0.5不再重复。完整模型取与C.1一致的原始JSON，移除项来自对应结果归档。

**English.** v1 at confidence 0.3. The 3D@0.3/@0.5 and BEV@0.5 columns already shown in the main ablation table are omitted. The full-model row follows the same JSON as Table C.1; ablated rows follow their experiment records.

<a id="table-e1"></a>
### Table E.1. 按模态对拆分的全量高维相似度 / Full-set similarity by modality pair

| Weather | Frames | Sequences | FG patches | Shared C–L | Shared C–R | Shared L–R | Specific C–L | Specific C–R | Specific L–R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Normal | 4309 | 17 | 317581 | 0.9455 | 0.9584 | 0.9621 | 0.3429 | 0.6545 | 0.3410 |
| Overcast | 383 | 2 | 33918 | 0.9520 | 0.9574 | 0.9676 | 0.4211 | 0.6501 | 0.4111 |
| Fog | 1049 | 6 | 43909 | 0.9391 | 0.9505 | 0.9647 | 0.4659 | 0.6612 | 0.4572 |
| Rain | 1317 | 8 | 125257 | 0.9431 | 0.9565 | 0.9586 | 0.3855 | 0.6511 | 0.3767 |
| Sleet | 1106 | 7 | 41665 | 0.9584 | 0.9478 | 0.9638 | 0.5112 | 0.6529 | 0.4840 |
| Light snow | 803 | 4 | 36196 | 0.9470 | 0.9582 | 0.9622 | 0.4787 | 0.6590 | 0.4643 |
| Heavy snow | 1098 | 7 | 44123 | 0.9525 | 0.9481 | 0.9601 | 0.4954 | 0.6458 | 0.4693 |

**中文。** 原始256维空间；先对帧内匹配前景位置求平均，再对天气内各帧等权平均。

**English.** Cosines in the original 256-dimensional space are averaged over matched foreground locations within each frame, then equally over frames within a weather group.

<a id="table-e2"></a>
### Table E.2. L–R相似度分位数 / L–R similarity quantiles

| Weather | Branch | Pair | Median | 5th percentile | 95th percentile |
| --- | --- | --- | --- | --- | --- |
| normal | common | LiDAR–4D Radar | 0.9632 | 0.9433 | 0.9776 |
| normal | unique | LiDAR–4D Radar | 0.3384 | 0.2113 | 0.4948 |
| heavysnow | common | LiDAR–4D Radar | 0.9662 | 0.9141 | 0.9806 |
| heavysnow | unique | LiDAR–4D Radar | 0.4538 | 0.2578 | 0.7363 |

**中文。** 每个观测值为一帧中匹配前景patch余弦的均值；分位范围描述帧间变异，不是置信区间。

**English.** Each observation is a frame-level mean of matched-patch cosines. Quantiles describe variation across frames, not confidence intervals.

<a id="table-e3"></a>
### Table E.3. 七个附录gate选例的逐帧统计 / Frame-level statistics of the seven appendix gate examples

| Weather | Frame ID | GT objects | FG patches | FG gate mean | BG gate mean | FG − BG |
| --- | --- | --- | --- | --- | --- | --- |
| Normal | seq20_rdr00628 | 1 | 28 | 0.3154 | 0.1208 | 0.1946 |
| Overcast | seq13_rdr00146 | 2 | 60 | 0.2995 | 0.1112 | 0.1883 |
| Fog | seq39_rdr00582 | 1 | 40 | 0.2942 | 0.1078 | 0.1864 |
| Rain | seq25_rdr00154 | 4 | 142 | 0.2882 | 0.1181 | 0.1702 |
| Sleet | seq50_rdr00456 | 2 | 65 | 0.2913 | 0.1179 | 0.1734 |
| Light snow | seq43_rdr00169 | 1 | 35 | 0.3711 | 0.1103 | 0.2608 |
| Heavy snow | seq55_rdr00385 | 1 | 35 | 0.2817 | 0.1186 | 0.1631 |

**中文。** 每帧均为1,440个完整patch。前景依据0.7m扩张GT区域在预测后划分；这些是七个定性选例的帧内统计，不是七天气总体均值。

**English.** Each frame has 1,440 complete patches. Foreground regions use GT footprints expanded by 0.7 m after prediction. Values summarize seven qualitative examples, not weather-wide means.

<a id="table-f1"></a>
### Table F.1. v1固定权重的输入可用性 / v1 input availability with fixed weights

| Input | conf | 3D@0.3 | 3D@0.5 | BEV@0.5 | Δ 3D@0.3 vs CLR |
| --- | --- | --- | --- | --- | --- |
| C+L+R | 0.3 | 88.36 | 67.50 | 88.10 | +0.00 |
| C+L+R | 0.0 | 88.06 | 72.83 | 87.18 | +0.00 |
| L+R | 0.3 | 88.06 | 71.68 | 85.45 | -0.30 |
| L+R | 0.0 | NR | NR | NR | NR |
| C+L | 0.3 | 86.77 | 72.58 | 86.35 | -1.59 |
| C+L | 0.0 | 86.16 | 69.74 | 83.76 | -1.90 |
| C+R | 0.3 | 57.62 | 34.59 | 55.52 | -30.74 |
| C+R | 0.0 | 63.65 | 38.48 | 60.28 | -24.41 |
| L | 0.3 | 79.58 | 60.05 | 77.96 | -8.77 |
| L | 0.0 | 85.46 | 59.23 | 77.96 | -2.60 |
| R | 0.3 | 49.81 | 26.64 | 46.80 | -38.55 |
| R | 0.0 | 61.75 | 30.86 | 52.60 | -26.31 |
| C | 0.3 | 0.86 | 0.16 | 0.21 | -87.49 |
| C | 0.0 | 0.32 | 0.03 | 0.14 | -87.74 |
| C* | 0.3 | 0.00 | 0.00 | 0.00 | -88.36 |
| C* | 0.0 | 0.17 | 0.01 | 0.07 | -87.89 |
| C*+L+R | 0.3 | 88.36 | 67.41 | 88.09 | +0.00 |
| C*+L+R | 0.0 | 88.06 | 72.75 | 87.17 | +0.00 |
| C+L*+R | 0.3 | 50.26 | 34.83 | 49.27 | -38.09 |
| C+L*+R | 0.0 | 63.05 | 38.48 | 61.12 | -25.01 |

**中文。** 10,065帧，正式v1 ObjDec。LR的conf=0.3行使用保存预测的已核查复算值（来源保留两位小数）；NR表示本稿尚无已核实的LR conf=0.0汇总，不是零分。所有其余行来自原始JSON。

**English.** The same v1 ObjDec checkpoint is evaluated on 10,065 frames. The LR/conf=0.3 row uses the audited recomputation of saved predictions, reported to two decimals in its source. NR denotes an unverified summary for LR/conf=0.0, not zero performance. Other rows are read from their JSON records.

<a id="table-f2"></a>
### Table F.2. v2固定Strong权重的输入可用性 / v2 input availability with fixed Strong weights

| Input | conf | Mean 3D@0.3 | Mean 3D@0.5 | Mean BEV@0.5 | Δ mean 3D@0.3 vs CLR |
| --- | --- | --- | --- | --- | --- |
| C+L+R | 0.3 | 66.91 | 43.05 | 60.93 | +0.00 |
| C+L+R | 0.0 | 69.41 | 43.81 | 63.23 | +0.00 |
| L+R | 0.3 | 66.02 | 41.81 | 59.93 | -0.89 |
| L+R | 0.0 | 68.96 | 42.77 | 62.74 | -0.46 |
| C+L | 0.3 | 64.08 | 41.17 | 57.80 | -2.83 |
| C+L | 0.0 | 65.13 | 41.16 | 58.53 | -4.28 |
| C+R | 0.3 | 34.25 | 16.99 | 29.97 | -32.66 |
| C+R | 0.0 | 34.73 | 16.82 | 29.89 | -34.68 |
| L | 0.3 | 59.39 | 32.36 | 53.45 | -7.53 |
| L | 0.0 | 62.33 | 33.47 | 54.75 | -7.08 |
| R | 0.3 | 30.51 | 13.59 | 26.28 | -36.40 |
| R | 0.0 | 31.63 | 13.45 | 26.70 | -37.79 |
| C | 0.3 | 0.01 | 0.00 | 0.01 | -66.90 |
| C | 0.0 | 0.01 | 0.00 | 0.01 | -69.40 |
| C* | 0.3 | 0.01 | 0.01 | 0.01 | -66.90 |
| C* | 0.0 | 0.01 | 0.01 | 0.00 | -69.40 |
| C*+L+R | 0.3 | 66.93 | 42.98 | 60.91 | +0.01 |
| C*+L+R | 0.0 | 69.40 | 43.73 | 63.19 | -0.01 |
| C+L*+R | 0.3 | 27.99 | 14.11 | 25.01 | -38.92 |
| C+L*+R | 0.0 | 34.70 | 15.51 | 30.76 | -34.71 |

**中文。** 13,727帧，Sedan与Bus/Truck等权平均；每个conf的差值均对应该conf下的完整输入。星号表示F节定义的本地损坏输入。

**English.** Equal class means over Sedan and Bus/Truck on 13,727 frames. Deltas use the full-input result at the same confidence filter. Stars denote the locally defined corruptions in Appendix F.

<a id="table-g1"></a>
### Table G.1. 空间粒度与完整预算结果 / Spatial granularity and full-budget results

| Method | Sensors | Grid (m) | Best epoch | Val mean 3D | Test Vehicle | Test Pedestrian | Test Cyclist | Test mean 3D | Test mean BEV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Concat | C+L+R | 0.4 | 75 | 74.31 | 81.52 | 65.81 | 79.98 | 75.77 | 81.26 |
| ASF-style | C+L+R | 0.4 | 75 | 72.76 | 78.57 | 58.93 | 79.02 | 72.17 | 78.21 |
| ObjDec 4×4 | C+L+R | 0.4 | 80 | 71.31 | 78.82 | 58.75 | 79.09 | 72.22 | 78.76 |
| ObjDec 2×2 | C+L+R | 0.4 | 80 | 74.19 | 80.73 | 62.36 | 78.99 | 74.03 | 80.26 |
| Concat | C+L+R | 0.16 | 75 | 81.46 | 84.81 | 76.84 | 84.05 | 81.90 | 86.47 |
| ASF-style | C+L+R | 0.16 | 80 | 81.03 | 84.54 | 76.17 | 83.18 | 81.30 | 85.72 |
| ObjDec 2×2 | C+L+R | 0.16 | 70 | 81.41 | 84.06 | 75.94 | 84.13 | 81.38 | 86.27 |
| L4DR | L+R | 0.16 | 80 | 77.19 | 83.17 | 73.25 | 78.31 | 78.24 | 82.56 |
| ObjDec-LR 2×2 | L+R | 0.16 | 75 | 79.12 | 83.87 | 74.84 | 80.24 | 79.65 | 83.81 |

**中文。** 均为80轮预算下按val选择的best，Moderate AP_R40；旧0.4m组补充正文0.16m表。Val与test分别列出，不用训练期val替代test。

**English.** Best checkpoints are selected by validation under an 80-epoch budget, using Moderate AP_R40. The 0.4 m group supplements the main 0.16 m comparison. Validation and test results are reported separately.

<a id="table-g2"></a>
### Table G.2. 已完成0.16m组的BEV及末轮补充 / BEV and last-checkpoint results for completed 0.16 m runs

| Method | Checkpoint | Epoch | BEV Vehicle | BEV Pedestrian | BEV Cyclist | Mean BEV | Mean 3D |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Concat | best | 75 | 92.12 | 80.66 | 86.64 | 86.47 | 81.90 |
| Concat | last | 80 | 92.02 | 80.70 | 86.69 | 86.47 | 81.97 |
| ASF-style | best | 80 | 90.95 | 80.41 | 85.80 | 85.72 | 81.30 |
| ASF-style | last | 80 | 90.95 | 80.41 | 85.80 | 85.72 | 81.30 |
| ObjDec 2×2 | best | 70 | 90.91 | 80.88 | 87.02 | 86.27 | 81.38 |
| ObjDec 2×2 | last | 80 | 90.84 | 81.16 | 87.07 | 86.35 | 81.55 |
| L4DR | best | 80 | 89.74 | 76.60 | 81.35 | 82.56 | 78.24 |
| L4DR | last | 80 | 89.74 | 76.60 | 81.35 | 82.56 | 78.24 |
| ObjDec-LR 2×2 | best | 75 | 90.02 | 78.34 | 83.08 | 83.81 | 79.65 |
| ObjDec-LR 2×2 | last | 80 | 90.10 | 78.21 | 83.09 | 83.80 | 79.75 |

**中文。** 去重test。best按val选择；last为第80轮，报告其结果不改变选模规则。五组0.16m实验的best/last均已完成。

**English.** Deduplicated test results. Best is selected by validation, whereas last is epoch 80. Reporting last does not change the selection rule. Best/last evaluations are complete for all five 0.16 m runs.

<a id="table-g3a"></a>
### Table G.3a. VoD整体标注区域 / VoD Entire Annotated Area (EAA)

| Method | Source | Epoch | Car | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- | --- | --- |
| PP-Concat (historical) | Local | 80 | 66.88 | 63.38 | 79.39 | 69.88 |
| ObjDec (warm-start, historical) | Local | 79 | 67.50 | 63.66 | 79.38 | 70.18 |
| ObjDec (2×2 + local) | Local | 75 | 68.72 | 65.59 | 79.38 | 71.23 |
| ObjDec (+ adapted anchors) | Local | 80 | 66.93 | 65.28 | 83.89 | 72.03 |
| L4DR | Local | 99 | 68.69 | 65.35 | 78.98 | 71.00 |
| InterFusion | Reported | — | 66.50 | 64.50 | 78.50 | 69.83 |
| L4DR | Reported | — | 69.10 | 66.20 | 82.80 | 72.70 |

**中文。** 所有方法输入均为L+R，无额外人工雾；官方VoD 11点3D AP，类别IoU为0.5/0.25/0.25。本地结果为1,296帧验证集；EAA与DC的同名行使用同一权重。两组近期ObjDec按EAA选模，训练及历史参照差异见G.4。Reported两行取自L4DR正式论文表3 [L4DR]，Mean为其公开类别值的算术平均；Local均值保留原评分输出。

**English.** All methods use L+R without added synthetic fog. Official VoD 11-point 3D AP uses class IoUs of 0.5/0.25/0.25. Local results use 1,296 validation frames, with the same checkpoint for each method across EAA and DC. The two recent ObjDec runs select checkpoints by EAA; training and historical-reference differences are detailed in G.4. Reported rows are from Table 3 of the published L4DR paper [L4DR], with means computed from its class values. Local means retain the evaluator output.

<a id="table-g3b"></a>
### Table G.3b. VoD驾驶走廊 / VoD Driving Corridor (DC)

| Method | Source | Epoch | Car | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- | --- | --- |
| PP-Concat (historical) | Local | 80 | 90.77 | 71.09 | 89.53 | 83.80 |
| ObjDec (warm-start, historical) | Local | 79 | 90.59 | 71.02 | 89.76 | 83.79 |
| ObjDec (2×2 + local) | Local | 75 | 90.74 | 73.23 | 90.09 | 84.69 |
| ObjDec (+ adapted anchors) | Local | 80 | 89.44 | 73.02 | 88.83 | 83.76 |
| L4DR | Local | 99 | 90.51 | 75.13 | 88.90 | 84.84 |
| InterFusion | Reported | — | 90.70 | 72.00 | 88.70 | 83.80 |
| L4DR | Reported | — | 90.80 | 76.10 | 95.50 | 87.47 |

**中文。** 所有方法输入均为L+R，无额外人工雾；官方VoD 11点3D AP，类别IoU为0.5/0.25/0.25。本地结果为1,296帧验证集；EAA与DC的同名行使用同一权重。两组近期ObjDec按EAA选模，训练及历史参照差异见G.4。Reported两行取自L4DR正式论文表3 [L4DR]，Mean为其公开类别值的算术平均；Local均值保留原评分输出。

**English.** All methods use L+R without added synthetic fog. Official VoD 11-point 3D AP uses class IoUs of 0.5/0.25/0.25. Local results use 1,296 validation frames, with the same checkpoint for each method across EAA and DC. The two recent ObjDec runs select checkpoints by EAA; training and historical-reference differences are detailed in G.4. Reported rows are from Table 3 of the published L4DR paper [L4DR], with means computed from its class values. Local means retain the evaluator output.

<a id="table-g4"></a>
### Table G.4. VoD补充难度指标 / Supplementary KITTI difficulty metrics on VoD

| Configuration | Epoch | Metric | Easy mean | Moderate mean | Hard mean |
| --- | --- | --- | --- | --- | --- |
| ObjDec (2×2 + local) | 75 | 3D | 83.43 | 78.64 | 72.23 |
| ObjDec (+ adapted anchors) | 80 | 3D | 83.06 | 78.35 | 72.02 |
| ObjDec (2×2 + local) | 75 | BEV | 85.47 | 80.55 | 74.56 |
| ObjDec (+ adapted anchors) | 80 | BEV | 85.33 | 80.92 | 75.02 |

**中文。** 与表G.3相同的EAA选中权重，三类等权平均；3D/BEV的IoU均为0.5/0.25/0.25。此表使用KITTI难度过滤及AP_R40，与官方EAA/DC的区域过滤和11点AP不同，不混用两套数值。

**English.** Equal class means for the same EAA-selected checkpoints as Table G.3, using 3D/BEV IoUs of 0.5/0.25/0.25. KITTI difficulty filtering and AP_R40 differ from the region filtering and 11-point AP of official EAA/DC, so the two sets of scores are not interchangeable.

<a id="table-h1"></a>
### Table H.1. 延迟分布 / Latency distributions

| Model | Execution | Mean ms | Median ms | P95 ms | Std ms | 1000 / mean ms |
| --- | --- | --- | --- | --- | --- | --- |
| ASF | Eager | 84.00 | 82.63 | 93.26 | 5.34 | 11.91 |
| ASF | CUDA Graph | 59.30 | 59.10 | 64.82 | 2.83 | 16.86 |
| ObjDec | Eager | 84.69 | 84.50 | 89.98 | 3.01 | 11.81 |
| ObjDec | CUDA Graph | 59.57 | 59.23 | 65.93 | 2.92 | 16.79 |

**中文。** 每种模型/路径100个不同计时帧、重复两轮；最后一列为计时路径吞吐，不包含读盘。标准差描述计时变异，不是多种子检测误差。

**English.** Each model/path uses 100 distinct timed frames repeated twice. The final column is the reciprocal of measured latency, excluding disk loading. Standard deviations describe timing variation rather than multi-seed detection uncertainty.

## 四、附图及中英文图注 / Supplementary figures and captions

2026-09-26：现行编排为E.1全天气PCA、E.2余弦分布、E.3帧级对照、E.4七天气gate、E.5全量gate统计、E.6检测对照、E.7雪天及反例。完整英文图注与插图以`objdec_latex_260924/figures/`为准。下方保留可复用的已有中英文图注；候选全集只作归档。

### Figure E.1. 全天气帧均值PCA / Frame-mean PCA across all weather groups

图稿（2026-09-23蓝／绿／紫配色）：[PDF](../analysis_exports/objdec_visuals_blue_green_purple_260923/fulltest/objdec_fulltest_frame_pca_all_weather.pdf) · [PNG](../analysis_exports/objdec_visuals_blue_green_purple_260923/fulltest/objdec_fulltest_frame_pca_all_weather.png)。建议按4行＋3行分为续图，两页沿用相同坐标与图例。原始数据与显示样本不变。

**中文图注。** K-Radar v1全测试集的帧级表征分布。各行表示天气组，各列分别为输入、共享与模态特有表征。每个点是一帧内GT前景位置的均值向量，经该列固定的加权PCA投影；蓝色圆、绿色三角与紫色方块分别表示相机、LiDAR与四维雷达。每天气最多显示400帧，阴天显示全部383帧；黑色轮廓的大标记与密度轮廓使用该组全部帧，n表示完整组大小。同一列共享投影基和坐标范围，不同列独立拟合。二维分布保留的模态差异与表E.1所示高维余弦一致性描述不同属性。

**English caption.** Frame-level representation distributions over the complete K-Radar v1 test set. Rows indicate weather groups; columns show input, shared, and modality-specific representations. Each point is a frame's mean vector over GT foreground locations, projected using the fixed weighted PCA basis for its column. Blue circles, green triangles, and purple squares denote camera, LiDAR, and 4D radar. Up to 400 frames are displayed per group, including all 383 overcast frames. Large outlined markers and density contours use all frames, and n denotes the full group size. Each column shares its basis and axis ranges across weather; columns are fitted independently. Residual modality structure in these projections and high-dimensional cosine consistency in Table E.1 characterize different properties.

### Figure E.2. 高维余弦的逐帧分布 / Frame-level distributions of high-dimensional cosine similarity

图稿：[PDF](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_distributions.pdf) · [PNG](../analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_distributions.png)。与正文紧凑均值／热图互补，保留正常与大雪对照。

**中文图注。** 正常天气与大雪条件下，三对传感器在原始256维空间中的余弦分布。每个观测是同一帧中匹配前景patch余弦的均值，纳入两组全部4,309与1,098帧。灰、绿、黄分别对应输入、共享和模态特有表征。小提琴为经验密度，白点为中位数，粗线和细线为25–75%与5–95%分位范围，不是估计均值的置信区间。共享表征集中于较高一致性区域，特有表征的分布随模态对与天气变化；图中不使用PCA坐标计算相似度。

**English caption.** Cosine-similarity distributions in the original 256-dimensional space for three sensor pairs under normal weather and heavy snow. Each observation is the mean matched-foreground-patch cosine within a frame, including all 4,309 and 1,098 frames. Gray, green, and yellow indicate input, shared, and modality-specific representations. Violins show empirical density, white points show medians, and thick/thin intervals span the 25th–75th/5th–95th percentiles, rather than confidence intervals for estimated means. Shared features concentrate at high similarity, while specific-feature distributions vary by modality pair and weather. Similarities are not computed from PCA coordinates.

### Figure E.7. 额外雪天案例与反例 / Additional snow examples and a counterexample

图稿：[PDF](../analysis_exports/objdec_fig4_fig5_260919/fig5_snow_and_counterexample.pdf) · [PNG](../analysis_exports/objdec_fig4_fig5_260919/fig5_snow_and_counterexample.png)。两行可放在同页。

**中文图注。** 官方ASF权重与ObjDec的额外成对检测案例。绿色虚线为GT，橙色实线为score>0.3的预测，两模型使用相同相机投影和局部放大范围。大雪案例中所示目标的最大几何3D IoU由0.095提高至0.728；小雪案例中则由0.354降至0.223。小雪案例同时出现在正文gate图中，其局部较高gate与较差定位并存，表明前景相关响应不能代替最终框回归。所列IoU用于说明选定目标的几何重合，不是AP。

**English caption.** Additional paired detections from the released ASF checkpoint and ObjDec. Green dashed boxes are GT and orange solid boxes are predictions with score>0.3; both methods use identical camera projections and detail windows. The selected heavy-snow object's maximum geometric 3D IoU increases from 0.095 to 0.728, whereas the light-snow object's decreases from 0.354 to 0.223. The latter also appears in the seven-weather appendix gate visualization, where locally high foreground response coexists with poorer localization. Foreground-related activation does not replace final box regression. Displayed IoUs describe selected-object overlap rather than AP.

### 归档图册（不插入论文PDF）. 全部成对候选 / Complete paired candidate set

图稿：[五页PDF](../analysis_exports/objdec_fig4_fig5_260919/fig5_all_candidates.pdf)。PDF附录篇幅紧张时可作为单独匿名补充图册，E节保留其索引。

**中文图注。** 固定候选池的全部20帧检测对照，包含改善、相近和较差案例。两模型采用相同输入和显示阈值。该候选池来自gate可视化选例，存在选择偏差，不能用于估计总体AP或天气平均性能；完整定量结果见附录C。候选页用于核对附图E.6及E.7在同一池中的选取范围。

**English caption.** All 20 paired detection candidates from the fixed visualization pool, including improved, similar, and poorer cases. Inputs and display thresholds are identical across models. The pool originates from gate-visualization candidates and is selected rather than representative; it does not estimate overall AP or weather-specific performance. Complete quantitative results are provided in Appendix C. The contact sheets document the selection pool for Figure E.6 and Figure E.7.

### Figure G.1. 完整训练轨迹 / Complete training trajectories — 待补 / Pending

**排版与数据要求。** 两个面板分别比较0.16m C+L+R的Concat／ASF-style／ObjDec，以及L+R的L4DR／ObjDec-LR。横轴为epoch，纵轴为去重val的严格Moderate Mean AP3D；只连接实际已评测节点，标出按预定规则选中的best。五组均已完成80轮，验证记录齐全；本图仍待由真实记录制成图稿。

**中文图注草案。** 相同训练预算下的验证轨迹。左图为共同底座上的三模态融合对照，右图为L+R架构对照。各点为实际验证结果，标记表示验证集选中的checkpoint；曲线不包含test分数，也不将各类跨轮最优值合成一个分数。

**English caption draft.** Validation trajectories under the matched training budget. Left: three-sensor fusion with a common backbone. Right: L+R architectural comparisons. Points are actual validation evaluations, and highlighted markers indicate checkpoints selected on validation. Curves contain no test scores and do not combine class-wise maxima from different epochs.
