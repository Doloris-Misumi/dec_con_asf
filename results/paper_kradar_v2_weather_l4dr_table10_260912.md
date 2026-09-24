# K-Radar v2：参照 L4DR Table 10 的全天气表

日期：2026-09-12。按作者最新建议，附录天气表直接纳入 L4DR 论文行，与官方 ASF 及 DecControlled Strong 并列展示；文献结果用 † 区分。

布局参照 [L4DR arXiv v6 Table 10](https://arxiv.org/html/2408.03677v6)：Class / Method / Modality / Total / Normal / Light snow / Heavy snow / Rain / Sleet / Overcast / Fog。原表使用 AP3D@0.3；这里另提供同样版式的 AP3D@0.5。

本地对比协议：label v2_0，宽 ROI [0,−16,−2,72,16,7.6]，C+L+R，conf_thr=0.3，使用 ASF revised evaluator（41 个 precision 采样值平均、z_center=0.5）。Strong 指 DecControlled Strong 08-06，是不含 task-context 分支的 Dec 方法家族变体。

† L4DR 来自论文 Table 10，输入 L+R。其公开代码使用旧评测器（41 点网格取 11 个 precision 值平均、z_center=1.0），当前公开配置使用 label v2_1；尚未确认该论文表的完整运行协议。数值可并列对照，但不能视为已统一评测器的排名。详见 [本轮协议与 Total 审计](taskdec_v2_l4dr_weather_total_and_eval_protocol_audit_260912.md)。

Total 是整个评测集直接计算的 AP，不是七种天气 AP 的平均。Fog 的 Bus/Truck 记为“—”：本轮检查该运行 1,445 个 Fog GT 文件，没有该类 GT；原日志中的 0.00 在 CSV 中保留。表内不对无 GT 单元格计算收益。

## AP3D@0.3

| 类别 | 方法 | 模态 | Total | 正常 | 小雪 | 大雪 | 雨 | 雨夹雪 | 阴天 | 雾 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sedan | L4DR (paper) † | L+R | 75.8 | 74.6 | 87.5 | 58.4 | 77.8 | 61.4 | 79.2 | 89.3 |
| Sedan | ASF official | C+L+R | 74.98 | 74.14 | 88.24 | 63.61 | 66.37 | 70.43 | 82.35 | 92.26 |
| Sedan | DecControlled Strong (ours) | C+L+R | 74.58 | 73.51 | 89.56 | 63.57 | 68.11 | 72.52 | 84.30 | 94.46 |
| Bus/Truck | L4DR (paper) † | L+R | 59.7 | 59.4 | 84.4 | 51.9 | 8.1 | 66.1 | 86.4 | — |
| Bus/Truck | ASF official | C+L+R | 58.13 | 53.28 | 88.26 | 68.20 | 7.89 | 59.55 | 75.33 | — |
| Bus/Truck | DecControlled Strong (ours) | C+L+R | 59.24 | 51.63 | 89.56 | 72.34 | 10.08 | 57.47 | 73.82 | — |

Strong − ASF（AP 点，按原始精度计算）：

| 类别 | Total | 正常 | 小雪 | 大雪 | 雨 | 雨夹雪 | 阴天 | 雾 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sedan | -0.39 | -0.62 | +1.32 | -0.03 | +1.74 | +2.09 | +1.95 | +2.20 |
| Bus/Truck | +1.12 | -1.65 | +1.30 | +4.14 | +2.19 | -2.08 | -1.50 | — |

Strong − L4DR 论文值（仅数值差，尚未统一评测器；L4DR 原表精度为一位小数）：

| 类别 | Total | 正常 | 小雪 | 大雪 | 雨 | 雨夹雪 | 阴天 | 雾 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sedan | -1.22 | -1.09 | +2.06 | +5.17 | -9.69 | +11.12 | +5.10 | +5.16 |
| Bus/Truck | -0.46 | -7.77 | +5.16 | +20.44 | +1.98 | -8.63 | -12.58 | — |

## AP3D@0.5

| 类别 | 方法 | 模态 | Total | 正常 | 小雪 | 大雪 | 雨 | 雨夹雪 | 阴天 | 雾 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sedan | ASF official | C+L+R | 52.09 | 49.63 | 59.25 | 49.52 | 46.85 | 44.05 | 53.38 | 80.55 |
| Sedan | DecControlled Strong (ours) | C+L+R | 52.14 | 49.39 | 60.75 | 50.49 | 48.30 | 49.13 | 59.62 | 80.30 |
| Bus/Truck | ASF official | C+L+R | 31.06 | 23.93 | 70.81 | 32.55 | 2.48 | 38.83 | 47.04 | — |
| Bus/Truck | DecControlled Strong (ours) | C+L+R | 33.97 | 23.94 | 75.09 | 39.37 | 5.05 | 38.48 | 49.65 | — |

Strong − ASF（AP 点，按原始精度计算）：

| 类别 | Total | 正常 | 小雪 | 大雪 | 雨 | 雨夹雪 | 阴天 | 雾 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sedan | +0.05 | -0.24 | +1.49 | +0.96 | +1.44 | +5.08 | +6.25 | -0.25 |
| Bus/Truck | +2.91 | +0.00 | +4.28 | +6.82 | +2.57 | -0.35 | +2.61 | — |

## 天气等权平均与 Total 的区别

以下均为 AP3D@0.3。天气均值是复算的诊断统计，不替代基准 Total；Bus/Truck 排除无 GT 的 Fog。跨方法数字仍受上述协议差异限制。

| 类别 | 统计 | L4DR 论文 | Strong | 数值差 |
| --- | --- | --- | --- | --- |
| Sedan | 天气等权平均（7 类天气） | 75.46 | 78.00 | +2.55 |
| Sedan | 全评测集 Total | 75.80 | 74.58 | -1.22 |
| Bus/Truck | 天气等权平均（6 类天气） | 59.38 | 59.15 | -0.23 |
| Bus/Truck | 全评测集 Total | 59.70 | 59.24 | -0.46 |

Total 合并全部帧的检测和 GT、汇总阈值下的 TP/FP/FN 后计算 PR/AP，既不是天气 AP 的等权平均，也不能用天气 AP 按帧数或 GT 数加权精确还原。当前 Sedan GT 的 53.99% 在 Normal、20.19% 在 Rain；Strong 在这两组分别比论文值低 1.09、9.69 点，有助于理解为何多数天气更高不等于 Total 更高，但不能据此量化协议影响。

来源：[L4DR Table 10](https://arxiv.org/html/2408.03677v6)；[官方 v2.1 配置](https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/configs/cfg_PP_L4DR.yml)。其他方法及其协议见 [v2 文献清单](kradar_v2_literature_candidates_260912.md)。

## 读表与附录安排

- @0.3：相对 ASF，Strong 的 Bus/Truck 在雨、小雪、大雪下分别提高 2.19、1.30、4.14 点；正常、阴天、雨夹雪下降。Sedan 在阴天、雾、雨、雨夹雪、小雪下提高，正常与大雪略降。
- @0.5 给出更严格定位结果：Bus/Truck 在雨、小雪、大雪下分别提高 2.57、4.28、6.82 点；Sedan 在阴天和雨夹雪下提高 6.25、5.08 点，但正常与雾略降，Bus/Truck 的雨夹雪也略降。
- 根据最新讨论，完整天气表作为附表：@0.3 面板含 L4DR、ASF、Strong，共 6 个方法行；@0.5 面板保留 ASF、Strong，共 4 行。L4DR Table 10 没有 @0.5 天气值，不从其他表或论文拼接补齐。正文可保留 Total 紧凑表。
- 相对 L4DR 论文，Strong 的 Sedan 在 5/7 种天气数值更高，但 Total 低 1.22 点；Bus/Truck 在 3/6 种有效天气更高，Total 低 0.46 点。不能概括成各项均优，也不按不同评测器的数字标统一最优。
- v2 的结论仍是宽 ROI / 双类别设置下的扩展有效性，天气列进一步展示收益出现在哪些条件中。缺模态鲁棒性仍由 v1 的独立实验承担。

## 本轮 GT 计数核验

计数来自 Strong 运行各天气 gts 目录中导出的评测 GT，表示当前过滤设置下的目标数，不是数据集未经筛选的全部标注。

| 天气 | 帧数 | Sedan GT | Bus/Truck GT |
| --- | --- | --- | --- |
| normal | 5415 | 15988 | 2763 |
| lightsnow | 1103 | 1360 | 540 |
| heavysnow | 1720 | 1611 | 1137 |
| rain | 1424 | 5978 | 120 |
| sleet | 2206 | 1622 | 1132 |
| overcast | 414 | 1107 | 151 |
| fog | 1445 | 1947 | 0 |

- [Strong 原始结果](/home/hongsheng/dec_con_asf/logs/exp_260806_000825_DecControlledASFStrong_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt)
- [ASF 原始结果](/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/raw/complete_results_none_0.3.txt)
- [完整 18 条件、两类、六项指标](paper_kradar_v2_decstrong_asf_comparison_260912.md)
- [本表 CSV](paper_kradar_v2_weather_l4dr_table10_260912.csv)
- [L4DR 文献数值对照 CSV](paper_kradar_v2_weather_l4dr_table10_260912.l4dr_reference.csv)
- [Total 与评测协议审计](taskdec_v2_l4dr_weather_total_and_eval_protocol_audit_260912.md)
- [两个 IoU 版本的 LaTeX](paper_kradar_v2_weather_l4dr_table10_260912.tex)
- [生成脚本](../tools/analysis/export_v2_weather_l4dr_table10_260912.py)

本轮只整理已有结果及读取 GT，没有运行训练或 GPU 推理。
