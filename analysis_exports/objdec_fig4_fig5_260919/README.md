# ObjDec Fig.4 / Fig.5 初稿

**2026-09-23配色更新：** Fig.4的七天气组合及各天气独立PNG/PDF/SVG已从相同缓存重绘，使用Camera蓝／LiDAR绿／Radar紫；PCA与高维相似度图同步更新。最新文件见[统一配色完整索引](../objdec_visuals_blue_green_purple_260923/README.md)。本目录保留旧版图与原始来源说明；下文Fig.4图注、样本选择及数值仍适用于新版，Fig.5未变。

日期：2026-09-19。所有照片、点云、gate和检测框来自真实数据或真实模型输出。没有生成或修饰道路场景，没有移动框或人为修改gate。

Fig.4机制说明更新：2026-09-20。新增预测路径与训练监督示意，并将无框gate和后叠加GT的同一gate并列；本次仅CPU重绘，沿用原始预测数值。

## 交付文件及两图分工

- **Fig.4：模型在什么位置产生较高的前景gate？** [七天气PNG](fig4_objdec_all_weather.png)、[七天气PDF](fig4_objdec_all_weather.pdf)。每行一种天气，四列为相机参照、LiDAR BEV+GT参照、预测gate、同一gate+GT参照。上方蓝色实线路径在训练与推理时均运行，橙色虚线表示仅训练时使用的标签与gate损失。
- **Fig.5：两模型在相同场景的检测输出有什么差异？** [正文初稿PNG](fig5_asf_objdec_detection_draft.png)、[PDF](fig5_asf_objdec_detection_draft.pdf)。三行分别为正常天气、阴天、雨夜；四列为ASF相机投影、ObjDec相机投影、ASF BEV及局部放大、ObjDec BEV及局部放大。
- [大雪案例与小雪反例PNG](fig5_snow_and_counterexample.png)、[PDF](fig5_snow_and_counterexample.pdf)。可作为附录备选，不将大雪完全模糊的相机画面作为正文主要视觉素材。
- [Fig.5全部20帧候选PDF](fig5_all_candidates.pdf)，以及`fig5_candidates_1`至`5`的PNG/PDF；保留改善、相近与较差案例。
- Fig.4每种天气另有单独可排版PDF：`fig4_normal.pdf`、`fig4_overcast.pdf`、`fig4_fog.pdf`、`fig4_rain.pdf`、`fig4_sleet.pdf`、`fig4_lightsnow.pdf`、`fig4_heavysnow.pdf`。

两张图不能互相替代：局部较高gate不等于检测正确，检测改善也不能只凭单帧归因到gate。

## Fig.4：七天气选帧

原稿确实仅有阴天seq13、雨夜seq25两帧。此次沿用之前完成并核查的21帧完整gate候选，按相机可读性、目标分布与局部gate响应选择七帧；没有重新导出全测试集gate。

| 天气 | 样本 | FG均值 | BG均值 | 选择依据 |
|---|---|---:|---:|---|
| Normal | seq20_rdr00628 | 0.3154 | 0.1208 | 晴朗道路、远处单目标的局部gate较清楚 |
| Overcast | seq13_rdr00146 | 0.2995 | 0.1112 | 同帧两个不同距离目标，沿用原稿 |
| Fog | seq39_rdr00582 | 0.2942 | 0.1078 | 相机能见度差，约37m目标位置gate清楚 |
| Rain | seq25_rdr00154 | 0.2882 | 0.1181 | 雨夜多个目标，保留较弱目标响应，沿用原稿 |
| Sleet | seq50_rdr00456 | 0.2913 | 0.1179 | 比完全模糊候选更能辨认道路与旁车；近远两处目标 |
| Light snow | seq43_rdr00169 | 0.3711 | 0.1103 | 有转向目标，gate覆盖形状便于辨认；保留框外响应 |
| Heavy snow | seq55_rdr00385 | 0.2817 | 0.1186 | 有积雪且道路仍可辨认，未选FG差值最大的全模糊图 |

天气名称使用数据集元数据；不根据照片重新猜测天气。原`seq49_rdr00593`因历史重复推理差异尚未解释，继续排除。七天气各一帧是定性选例，不是无偏天气性能统计。这里的“明显”指展示对象与空间响应可辨认，不保证每个目标都检测正确。

Gate采用原始16×90网格，0.8m patch，x=[0,72]、y=[-6.4,6.4]m；不平滑，统一[0,1]色标，不逐帧归一化。第三、四列读取完全相同的gate数组，第四列只额外叠加绿色虚线GT框。绿框为原始Sedan GT，FG统计沿用训练实现的0.7m外扩。相机是原始front0半幅，未提亮、去雾或换背景。数据与选帧来源见[fig4_selection.json](fig4_selection.json)及[历史导出说明](../taskdec_bev_gate_fig4_260910/README.md)。

**前景标签、预测gate与GT参照的区别。** 训练时，GT框的BEV投影及扩张范围用于构建二元标签\(y\)，监督由共享/模态特有表征经MLP与sigmoid得到的连续门控\(g\)。训练前向参与融合的同样是预测\(g\)，标签不替代预测。推理保留该预测与调制路径，无需GT，也无需先生成检测框。common/unique分支在所有patch上计算；低gate减弱新增更新，原始特征仍保留。图中绿色框是在gate生成后添加的空间参照，FG/BG均值也是事后按GT区域统计。历史导出脚本在融合器入口临时移除`gt_boxes`后读取真实预测gate，再恢复GT供其他流程使用；不能把框的叠加误读为gate的输入。

示意条仅解释gate预测和监督的关系，完整模态控制、上下文交互和检测头见方法主图。渲染来源哈希及固定色标记录见[fig4_render_validation.json](fig4_render_validation.json)；原[validation.json](validation.json)仍保留先前成对检测推理的核查记录。

正文可取3–4个可读场景，七天气完整版放附录；若版面允许，也可以整张放正文。先完成全套素材，再决定版式，不必重新推理。

## Fig.5：成对推理和显示口径

ASF使用官方`A2F_v1_0_model_10.pt`；ObjDec使用正式Robust `model_0.pt`，与Fig.4权重SHA-256一致。本次是在本地统一推理实现上对20帧进行的新推理，不把官方汇总AP归档描述为新的本地全量评测。

两模型都严格加载完整checkpoint，eval、FP32、batch 1、C+L+R、标准eager执行。有效DATASET配置及检测HEAD配置相同，20帧全部输入张量逐项哈希相同，GT与历史gate导出也一致。检测头原始SCORE_THRESH=0.1、NMS IoU=0.01，画图统一使用`score > 0.3`，保留全部Sedan预测，不为某个模型单独改阈值或删框。完整的预显示过滤结果保存在40个小型NPZ中。

相机框使用逐序列`radar2camera`，再用原始内参与畸变系数投影到原始front0照片；没有把去畸变投影矩阵直接用在原图上。已核对原始K去畸变后与模型保存的K一致，且`radar2image=K×radar2camera`。近裁剪后对边采样，以绘制畸变后的线段。相机与BEV局部放大窗对两模型完全相同；BEV始终同时保留完整ROI。相机视野宽于当前评测ROI，图中只标当前评测类别与范围内的GT。

绿色虚线为GT，橙色实线为预测；两方法使用同一种预测颜色。相机左上角是原图局部放大，非新图片或图像增强。

| 正文案例 | 对应目标最优3D IoU：ASF → ObjDec | 允许描述 |
|---|---|---|
| Normal，seq20_rdr00628 | 0.572 → 0.719 | 所示远距框与GT的3D几何重合更高 |
| Overcast，seq22_rdr00218 | 0.000 → 0.476 | 在score>0.3下，ASF没有与所示远处GT重合的预测，ObjDec有对应框；0.476未达到3D IoU=0.5，不写成严格0.5下的正确检测 |
| Rain，seq25_rdr00154 | 0.000 → 0.741 | 同阈值下ObjDec保留该目标对应框；仍保留同帧其他目标的所有预测 |

大雪备选seq57_rdr00279为0.095→0.728；小雪反例seq43_rdr00169为0.354→0.223，ObjDec还保留更多预测。这说明较高gate本身不足以推出更好的最终框，也不能把所选改善帧推广到所有雪天。

图中数值是所选GT对所有保留预测的**最大几何3D IoU**，仅用来核对图中框的差异，不是AP、召回率或官方一对一TP匹配结果。BEV只显示水平框，3D IoU还受高度影响。各帧全部GT的数值与配对矩阵见[JSON](fig5_candidate_metrics.json)、[CSV](fig5_candidate_metrics.csv)。此候选池来自gate选例，有选择偏差；不用于估计总体性能。

## 图注草稿

**Fig.4 中文：** 七种天气下由特征预测的空间前景门控。上方示意中，共享与模态特有表征经MLP与sigmoid生成门控\(g\)，训练和推理均用其调制融合；GT衍生标签\(y\)仅用于训练损失。每行依次展示真实前向相机、LiDAR BEV与GT参照、预测gate，以及叠加GT参照的同一gate。第三、四列的热图数值完全相同；绿色虚线框在预测后添加，不参与gate生成。所有热图使用原始0.8m网格和统一[0,1]色标，不进行平滑或逐帧归一化。FG/BG为预测完成后按GT区域计算的帧内均值。所选场景展示局部响应，不代表各天气总体性能。

**Fig.4 English:** Feature-predicted spatial foreground gating across seven weather conditions. Top: shared and modality-specific representations produce gate \(g\) through an MLP and sigmoid for fusion modulation during both training and inference; GT-derived labels \(y\) enter only the training loss. Each row shows the front camera, LiDAR BEV with GT references, the predicted gate, and the same gate with GT references. The final two heatmaps are numerically identical; green dashed boxes are added after prediction and do not generate the gate. All heatmaps use the original 0.8 m grid and a common [0,1] scale without smoothing or per-frame normalization. FG/BG are frame-level means computed over GT-defined regions after prediction. These selected examples illustrate local responses rather than aggregate weather-specific performance.

**Fig.5 中文：** 官方ASF权重与ObjDec在相同K-Radar v1测试场景中的定性比较。展示3D框在真实相机图像中的标定投影，以及完整LiDAR BEV和相同区域的放大图。绿色虚线表示GT，橙色实线表示预测，两方法均使用score>0.3。图中数字为所选GT对保留预测的最大3D IoU，不是AP。所示正常天气、阴天与雨夜案例展示局部框重合度与目标保留情况的差异；附录提供额外案例及反例。

**Fig.5 English:** Qualitative comparison of the released ASF checkpoint and ObjDec on identical K-Radar v1 test scenes. We show calibrated projections of 3D boxes onto the camera image, complete LiDAR BEV views, and matched detail windows. Green dashed boxes denote ground truth and orange solid boxes denote predictions, using the same score threshold of 0.3 for both models. Values are the maximum 3D IoU between a selected ground-truth box and retained predictions, rather than AP. The selected normal-weather, overcast, and rainy-night examples illustrate differences in box overlap and retained detections; additional examples and counterexamples are provided in the appendix.

## 资源及运行记录

Fig.4仅CPU重绘。Fig.5两模型先后在GPU2各推理20帧，PyTorch峰值allocated分别1000.5/1005.6 MiB，配置上限为整卡8%。没有修改或停止任何训练任务；不复制权重、全量特征、原图或点云。

两次推理均保存20帧和`COMPLETE`标记后，在native退出阶段触发历史`free(): invalid pointer`，exit code 134。保留[ASF日志](asf_export.log)、[ObjDec日志](objdec_export.log)。独立CPU检查确认40个NPZ可读取、数值有限、输入哈希一致、checkpoint匹配和检测配置一致，见[validation.json](validation.json)。不能把这两次执行说成干净退出；当前结果通过文件与数值核查，不代表完整评测或部署稳定性验证。

## 复现

脚本：[make_objdec_fig4_fig5_260919.py](../../tools/analysis/make_objdec_fig4_fig5_260919.py)。CPU重绘：

```bash
cd /home/hongsheng/dec_con_asf
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 /home/hongsheng/miniconda3/envs/rl_3dod/bin/python tools/analysis/make_objdec_fig4_fig5_260919.py fig4
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 /home/hongsheng/miniconda3/envs/rl_3dod/bin/python tools/analysis/make_objdec_fig4_fig5_260919.py fig5 --select seq20_rdr00628,seq22_rdr00218,seq25_rdr00154
```

不需要重做GPU推理即可更换20帧候选中的展示案例。源图片由脚本直接读取，不另存大文件副本。
