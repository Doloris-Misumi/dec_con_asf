# K-Radar v2：天气均值、Total 与 L4DR 评测协议复核

日期：2026-09-12。对象：DecControlled Strong 08-06、官方 ASF 归档，以及 L4DR arXiv v6 Table 10。只读取现有结果、GT 和代码，没有运行模型、重算全量 IoU 或改变原始指标。

## 1. 结论

Sedan 的天气等权平均确实高于 L4DR，但 Bus/Truck 的天气等权平均略低；天气均值高也不意味着全评测集 Total AP 高。与此同时，发现了此前仅检查阈值/标签时遗漏的具体协议差异：**本地 v2 Strong 使用 ASF revised evaluator，而 L4DR 当前公开代码使用旧 evaluator，AP 汇总采样和 3D 框高度中心约定都不同。**

因此，附表应加入 L4DR 论文结果并明确来源和协议差异；当前只能说其公开 Total 数值更高，不能把差值全归因于模型性能，也不能声称统一协议后一定反超。本轮已将 L4DR 行加入 [附录天气表](paper_kradar_v2_weather_l4dr_table10_260912.md) 及 [LaTeX](paper_kradar_v2_weather_l4dr_table10_260912.tex)。

## 2. 先核对平均值

以下均为 AP3D@0.3，单位为百分数。Strong 使用原始精度计算；L4DR 仅有论文一位小数，差值精度受其限制。

| 类别 | 统计口径 | L4DR 论文 | Strong | 数值差 |
| --- | --- | --- | --- | --- |
| Sedan | 七种天气 AP 等权平均 | 75.46 | 78.00 | +2.55 |
| Sedan | 全评测集 Total AP | 75.80 | 74.58 | −1.22 |
| Bus/Truck | 六种有效天气 AP 等权平均 | 59.38 | 59.15 | −0.23 |
| Bus/Truck | 全评测集 Total AP | 59.70 | 59.24 | −0.46 |
| 两类 | 两个类别 Total AP 的均值 | 67.75 | 66.91 | −0.84 |

Fog 下本地 1,445 帧没有 Bus/Truck GT，故该类天气平均排除 Fog，不能把原始日志的 0 算进去。L4DR 论文对应位置也是破折号；这里只保留其原表标记，不据此推断对方实际 GT 帧集。

Sedan 在 5/7 种天气数值更高，Bus/Truck 在 3/6 种有效天气数值更高。若“各项平均”指每种天气中 Sedan 与 Bus/Truck 的类别平均，也不是每种天气都高：Normal、Rain、Overcast 更低；Light snow、Heavy snow、Sleet 更高。Fog 只能看 Sedan，不宜直接混入双类别天气均值。

来源：[L4DR Table 10](https://arxiv.org/html/2408.03677v6)；[Strong 与 ASF 原始精度对照](paper_kradar_v2_decstrong_asf_comparison_260912.csv)。

## 3. 为什么天气平均高，Total 仍可低

本地 [条件评测调用](../pipelines/pipeline_detection_v1_0.py:1029) 对 `all` 和各天气分别读取预测、GT 并计算 AP。Total 汇集整个评测集，在共同分数阈值下汇总 TP、FP、FN，再构造 PR 曲线并计算 AP；它不是条件 AP 的平均。

两种统计回答不同问题：天气等权平均让每种天气占相同比重；Total 评估所有目标和检测合并后的表现，受目标数量及跨天气置信度排序共同影响。即使改为按帧数或 GT 数对天气 AP 加权，也不能精确恢复 Total，因为每个天气独立计算 AP 后已经丢掉了跨天气分数关系。

当前实际 GT 分布为：

| 天气 | 评测帧数 | Sedan GT | Bus/Truck GT |
| --- | --- | --- | --- |
| Normal | 5415 | 15988 | 2763 |
| Light snow | 1103 | 1360 | 540 |
| Heavy snow | 1720 | 1611 | 1137 |
| Rain | 1424 | 5978 | 120 |
| Sleet | 2206 | 1622 | 1132 |
| Overcast | 414 | 1107 | 151 |
| Fog | 1445 | 1947 | 0 |
| 合计 | 13727 | 29613 | 5843 |

Sedan 的 Normal 占 GT 的 53.99%，Rain 占 20.19%；Strong 在这两组相对 L4DR 论文分别低 1.09、9.69 点，而若干更高的天气目标较少。这提供了理解 Total 较低的分布背景，**并非已证明当前 −1.22 点的因果分解**：对方实际 GT 尚未核验，评测器也不同。

K-Radar 官方仓库的 [issue #28](https://github.com/kaist-avelab/K-Radar/issues/28) 曾提出几乎同样的“Total 为什么不等于条件平均或样本加权平均”问题；这里只将其作为历史背景，解释依据是当前代码的数据汇总路径。

## 4. 已确认的评测器差异

| 项目 | 本地 v2 Strong / ASF 路径 | L4DR 当前公开路径 | 影响 |
| --- | --- | --- | --- |
| evaluator 选择 | `is_validation_updated: True`，调用 revised | 直接调用旧 `get_official_eval_result` | 并非只要 conf 相同就完全对齐 |
| precision 网格长度 | 41 | 41 | 二者都有 41 点数组 |
| AP 最终汇总 | 41 个 precision 值全部平均 | 取索引 0、4、…、40，共 11 个值平均 | 相同 PR 数组也可得到不同 AP |
| 3D IoU 高度中心 | `z_center=0.5` | `z_center=1.0` | 改变竖直方向交集，可能改变 TP 匹配 |
| 导出框坐标 | 中心坐标 `(yc, zc, xc)`，未作半高平移 | 相同导出形式，未作半高平移 | 高度中心差异没有在导出阶段被抵消 |

本地证据链：

- [Strong 归档配置](../logs/exp_260806_000825_DecControlledASFStrong_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml:1) 继承 [gentle 基础配置](../configs/ASF_obj_patch_dec_gentle.yml:26)，后者开启 revised evaluator。
- [pipeline 默认开关](../pipelines/pipeline_detection_v1_0.py:95) 与 [实际条件评测分支](../pipelines/pipeline_detection_v1_0.py:1044)。
- [旧 AP 汇总](../utils/kitti_eval/eval.py:606)、[revised AP 汇总](../utils/kitti_eval/eval_revised.py:606)、[revised 入口高度中心](../utils/kitti_eval/eval_revised.py:723)。
- [本地导出坐标](../utils/util_pipeline.py:322) 与 [L4DR 导出坐标](/home/hongsheng/L4DR/K-Radar-main-repo/utils/util_pipeline.py:334)。
- [官方 ASF v2 配置](/home/hongsheng/K-Radar-main/configs/ASF_v2_0_final.yml:26) 同样开启 revised；ASF 行来自现有官方结果归档，没有在本轮重算。

公开证据：[L4DR evaluator](https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/utils/kitti_eval/eval.py)、[L4DR pipeline](https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/pipelines/pipeline_detection_v1_0.py)、[K-Radar revised evaluator](https://github.com/kaist-avelab/K-Radar/blob/main/utils/kitti_eval/eval_revised.py)。高度中心问题亦见官方仓库 [issue #36](https://github.com/kaist-avelab/K-Radar/issues/36)，其说明预测框与 GT 高度不同时会影响 AP3D，而不影响 BEV 的几何交集。

注意措辞：本地 revised 的实现是 **41 个值平均**，不能直接写成标准 KITTI AP_R40。旧/新 AP 的变化方向取决于 PR 曲线；高度中心变化也可能增加或减少匹配。尚未对同一批预测切换评测器，因此这里不估计“能涨几分”。

证据边界：已核对当前代码和配置继承，不等于持有 L4DR Table 10 的原始运行环境。该表没有给出完整 evaluator commit / 预测归档，不能把“当前公开代码如此”写成“已复现论文评测设置”。Strong 的归档配置引用当前基础配置，也不是包含所有依赖版本的不可变环境快照。

## 5. 标签、ROI、split 与阈值核查

| 项目 | 本地 v2 Strong | L4DR 当前公开配置/代码 | 判断 |
| --- | --- | --- | --- |
| 标签版本 | v2_0 | v2_1 | 确有配置差异，实际 GT 几何差异未核验 |
| ROI | `[0,-16,-2,72,16,7.6]` | 相同 | 当前没有 ROI 不一致证据 |
| 评测类别 | Sedan、Bus/Truck | 相同 | 一致 |
| `onlyR` | False | False | 都未按该开关仅保留雷达可见目标 |
| `consider_roi` / `remove_0_obj` | True / True | True / True | 主要标签过滤开关一致 |
| 标定 z 偏移 | 0.7 | 0.7 | 一致；这不是上节的框高度中心参数 |
| 原始 test split | 官方 test.txt | 本地两份 L4DR clone 的 test.txt | 文件 SHA-256 完全相同 |
| 实际评测帧集 | 13727 个已导出预测/GT 帧 | Table 10 实际帧 ID 未公开核验 | 不能由 split 相同推断过滤后帧集相同 |
| 结果置信度阈值 | 本表 0.3 | 配置列 0.3/0.5/0.7，公开 v2.1 日志有 0.3 | Table 10 的具体运行仍待确认 |
| 输入 | C+L+R | L+R | 已在表中写明；是模型输入差异 |

三个本地 test.txt 的 SHA-256 均为 `47c8c1883acf65ea2939db5b92588a5d5f66bc56471e6ba80a1c94a9961d1d2c`，分别来自本项目、`/home/hongsheng/L4DR/K-Radar-main-repo`、本项目内 L4DR clone。

[官方标签说明](https://github.com/kaist-avelab/K-Radar/blob/main/docs/dataset.md) 将 v2.1 的更新描述为增加可见性区分。两边 `onlyR=False`，所以不能仅凭 v2.0/v2.1 的名称差异就断言这是 Total 落后的原因；需要比较真实 GT 和过滤后的帧 ID。当前本地没有完整可用的 v2.1 标签供逐框核验。

[L4DR 官方配置](https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/configs/cfg_PP_L4DR.yml) 和 [公开 v2.1 日志](https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/logs/v2.1.txt) 也不能直接绑定到 Table 10：公开日志的 Sedan AP3D@0.3 约为 77.95，而表中是 75.8，不能擅自替换。

## 6. 主表与附表应如何处理

v1 主表已经加入 L4DR，是 v2 附表也纳入其文献结果的合理理由。已经执行：@0.3 天气面板每类列 L4DR (paper) †、ASF official、DecControlled Strong (ours)；@0.5 保留 ASF 与 Strong，因为 L4DR Table 10 没有对应天气值。完整正负结果和 Total 都保留，不以天气平均替换 Total。

表注应写清 L4DR 是论文引用值，本地方法使用 revised evaluator；在评测器未统一前不作跨三方法的统一最优加粗。天气均值可以作为讨论诊断统计，若进入论文必须另列定义，并对所有方法采用相同缺失值处理。

v1 与本次发现的关系也已核对：[主模型配置](../configs/ASF_task_dec_controlled_robust_v1_0.yml:1) 继承 [v1 基础配置](../configs/v1_0/cfg_A2F_scl_final.yml:1)，二者没有开启 `is_validation_updated`；按当前 pipeline 默认 False，它走旧 evaluator。因此，**不能把 v2 的“新旧 evaluator 不一致”直接套到 v1 主表上**。v1 的标签 v1.0 / L4DR v1.1、实际阈值等边界仍按原审计说明。

目前最有信息量的后续实验是固定 Strong 现有预测和 GT，交叉计算 11/41 点 AP 与 `z_center=1.0/0.5` 的四种组合：先复现当前 revised 数字，再分别量化采样和高度中心的影响，最后看完整旧评测器下的 Total/天气。这样不需要重新训练或模型前向，也不需要复制预测目录。若要完成严格方法对比，仍需 L4DR 的 v2 预测或正确 checkpoint，并统一 GT、帧集与 evaluator。

本轮没有启动该复评：现有旋转框 IoU 实现仍依赖 CUDA，不能把“不需要模型推理”误写为现成脚本已完全支持 CPU。当前先完成数值和代码审计；CPU 适配或 GPU 空闲时的 IoU 复评属于下一步，实际分数影响尚无测量结果。
