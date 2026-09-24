# TaskDec：现有 K-Radar v2.0 结果复核（2026-09-12）

依据作者讨论后的新方向：可能撤下 VoD 表，先复核 v2.0 数据；本记录不将该倾向视为已确定删除 VoD 材料。

本轮读取原始结果文本、归档 JSON 和配置，重新计算差值；没有运行 GPU 推理或训练。比较对象为现有官方 ASF v2 RLC 结果，不是所有文献方法的排名。

**核心发现：早期 DecControlled Strong 的两类平均 AP3D@0.3 / @0.5 分别比 ASF 高 0.36 / 1.48 点。另有此前推荐表未列出的 TaskDec Robust 08-08：含 task context，AP3D@0.5 高 1.76 点，但 AP3D@0.3 低 1.95 点。08-21 final 及 model_6/model_8 也纳入核对，不能仅用 final 一次结果概括整个 TaskDec v2 系列。**

口径：C+L+R、label v2_0、宽 ROI [0,-16,-2,72,16,7.6]、Sedan 与 Bus/Truck、conf_thr=0.3。下文平均值均为两类 AP 的算术平均，单位为 AP 百分点；先用原始精度计算，最后保留两位小数。

## 1. 所有已找到的 DecControlled / TaskDec 全量比较

| 运行 | 两类平均 3D@0.3 | Δ ASF | 两类平均 3D@0.5 | Δ ASF |
| --- | --- | --- | --- | --- |
| ASF official RLC | 66.55 | +0.00 | 41.57 | +0.00 |
| DecControlled Gentle 08-06 | 65.49 | -1.07 | 41.75 | +0.18 |
| DecControlled Strong 08-06 | 66.91 | +0.36 | 43.05 | +1.48 |
| TaskDec Balanced 08-08 | 66.46 | -0.09 | 41.35 | -0.22 |
| TaskDec Robust 08-08 | 64.61 | -1.95 | 43.34 | +1.76 |
| TaskDec Robust 08-21 final | 65.21 | -1.34 | 41.26 | -0.32 |
| TaskDec Robust model_6 | 66.30 | -0.26 | 40.92 | -0.66 |
| TaskDec Robust model_8 | 65.28 | -1.27 | 41.40 | -0.17 |
| DecControlled Strong resume model_16 | 66.63 | +0.08 | 42.03 | +0.45 |

## 2. 重点版本的全量分类别指标

| 运行 | 类别 | 3D@0.3 | 3D@0.5 | 3D@0.7 | BEV@0.3 | BEV@0.5 | BEV@0.7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ASF official RLC | sed | 74.98 | 52.09 | 11.85 | 77.85 | 71.70 | 43.21 |
| ASF official RLC | bus | 58.13 | 31.06 | 7.93 | 67.85 | 53.21 | 20.85 |
| DecControlled Strong 08-06 | sed | 74.58 (-0.39) | 52.14 (+0.05) | 12.31 (+0.45) | 77.32 (-0.53) | 71.27 (-0.44) | 44.26 (+1.05) |
| DecControlled Strong 08-06 | bus | 59.24 (+1.12) | 33.97 (+2.91) | 9.92 (+1.98) | 65.14 (-2.72) | 50.59 (-2.61) | 23.13 (+2.27) |
| TaskDec Robust 08-08 | sed | 74.59 (-0.39) | 52.24 (+0.15) | 12.28 (+0.42) | 75.32 (-2.52) | 71.26 (-0.44) | 44.92 (+1.71) |
| TaskDec Robust 08-08 | bus | 54.62 (-3.51) | 34.43 (+3.38) | 7.41 (-0.52) | 63.08 (-4.77) | 51.28 (-1.92) | 20.68 (-0.18) |
| TaskDec Robust 08-21 final | sed | 74.65 (-0.32) | 51.76 (-0.33) | 10.16 (-1.69) | 77.48 (-0.36) | 71.26 (-0.44) | 44.67 (+1.46) |
| TaskDec Robust 08-21 final | bus | 55.77 (-2.36) | 30.75 (-0.30) | 6.36 (-1.57) | 65.09 (-2.77) | 50.47 (-2.74) | 18.97 (-1.88) |

## 3. 全天气 AP3D@0.5：保留正负结果

格式为 AP（相对 ASF 的差值）。天气帧数是我们各运行目录的预测文件数，不是该类 GT 目标数。Fog 的 Bus/Truck AP 在这些结果中均为 0；本轮没有据此推断该天气没有该类 GT，也不把 0→0 算作收益。

### sed

| 天气 | 帧数 | ASF | DecControlled Strong | TaskDec Robust 08-08 | TaskDec Robust 08-21 |
| --- | --- | --- | --- | --- | --- |
| normal | 5415 | 49.63 | 49.39 (-0.24) | 49.60 (-0.03) | 47.37 (-2.26) |
| overcast | 414 | 53.38 | 59.62 (+6.25) | 59.18 (+5.81) | 58.81 (+5.44) |
| fog | 1445 | 80.55 | 80.30 (-0.25) | 79.68 (-0.87) | 80.08 (-0.47) |
| rain | 1424 | 46.85 | 48.30 (+1.44) | 46.57 (-0.29) | 46.36 (-0.49) |
| sleet | 2206 | 44.05 | 49.13 (+5.08) | 47.66 (+3.61) | 49.40 (+5.36) |
| lightsnow | 1103 | 59.25 | 60.75 (+1.49) | 61.42 (+2.17) | 59.75 (+0.50) |
| heavysnow | 1720 | 49.52 | 50.49 (+0.96) | 50.92 (+1.39) | 51.44 (+1.92) |

### bus

| 天气 | 帧数 | ASF | DecControlled Strong | TaskDec Robust 08-08 | TaskDec Robust 08-21 |
| --- | --- | --- | --- | --- | --- |
| normal | 5415 | 23.93 | 23.94 (+0.00) | 27.83 (+3.89) | 25.44 (+1.51) |
| overcast | 414 | 47.04 | 49.65 (+2.61) | 43.89 (-3.15) | 43.03 (-4.01) |
| fog | 1445 | 0.00 | 0.00 (+0.00) | 0.00 (+0.00) | 0.00 (+0.00) |
| rain | 1424 | 2.48 | 5.05 (+2.57) | 4.41 (+1.93) | 1.37 (-1.11) |
| sleet | 2206 | 38.83 | 38.48 (-0.35) | 35.70 (-3.14) | 36.55 (-2.29) |
| lightsnow | 1103 | 70.81 | 75.09 (+4.28) | 74.26 (+3.45) | 75.04 (+4.23) |
| heavysnow | 1720 | 32.55 | 39.37 (+6.82) | 35.86 (+3.31) | 27.49 (-5.06) |

原推荐表 selected-weather 仅包含 Overcast、Rain、Light snow、Heavy snow，不能称为全部恶劣天气，也不等于 Total AP。该四项平均的精确复算如下：

| 运行 | Sedan 四天气平均 | Bus/Truck 四天气平均 |
| --- | --- | --- |
| ASF official RLC | 52.25 (+0.00) | 38.22 (+0.00) |
| DecControlled Strong 08-06 | 54.79 (+2.54) | 42.29 (+4.07) |
| TaskDec Robust 08-08 | 54.52 (+2.27) | 39.61 (+1.38) |
| TaskDec Robust 08-21 final | 54.09 (+1.84) | 36.73 (-1.49) |

## 4. 模型身份、可比性与写作判断

- DecControlled Gentle / Strong / resume 使用 DecControlledA2Fusion，没有 task-context 分支。TaskDec Balanced / Robust 使用 TaskAwareDecControlledA2Fusion，包含任务上下文；不能将所有早期运行都称为“没有 task context”。
- 08-08 Robust 与 08-21 Robust 的配置不完全相同，例如 DEC_CONTROL_CLASS_POS_WEIGHT_MAX 分别为 12 和 4，且基础配置不同。这些跨运行差异不能解释为单一组件的因果效应。
- 本轮找到的 8 份全量条件评测，每份 all/preds 均为 13,727 个文件，文件名集合一致，全天气帧数也一致；这核查了目录覆盖范围，未逐文件比较 GT 内容。1000 样本的 subset 扫描未混入全量表。
- 原始文本与 5 份已有运行 JSON 及 ASF JSON 完全相符，共核对 1296 个 AP 值。ASF 数值来自现有官方结果归档，本轮未重跑 ASF 或另行核验其逐帧预测。
- 如果撤下 VoD，v2 可提供同数据集内更宽 ROI、修订标签与额外类别的扩展证据，但不承担跨数据集泛化结论。
- 若使用完整任务控制架构的 v2 结果，应同时报告其 AP3D@0.3 与 BEV 退化；不能把不同运行按列拼成一条 Ours。若沿用 DecControlled Strong，保留 early variant 表注。
- 建议以全量两类结果为主，全天气结果为补充。原推荐表四天气均值有正收益，但不能用它代替全量表现。现有数据支持严格 IoU 下的部分 3D 收益，不支持 v2 全指标领先。

## 5. 源文件与复现

- **ASF official RLC**：[原始结果](/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/raw/complete_results_none_0.3.txt)
- **DecControlled Gentle 08-06**：[原始结果](/home/hongsheng/dec_con_asf/logs/exp_260806_000821_DecControlledASFGentle_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt)；[配置](/home/hongsheng/dec_con_asf/logs/exp_260806_000821_DecControlledASFGentle_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml)
- **DecControlled Strong 08-06**：[原始结果](/home/hongsheng/dec_con_asf/logs/exp_260806_000825_DecControlledASFStrong_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt)；[配置](/home/hongsheng/dec_con_asf/logs/exp_260806_000825_DecControlledASFStrong_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml)
- **TaskDec Balanced 08-08**：[原始结果](/home/hongsheng/dec_con_asf/logs/exp_260808_131759_TaskDecControlBalanced_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt)；[配置](/home/hongsheng/dec_con_asf/logs/exp_260808_131759_TaskDecControlBalanced_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml)
- **TaskDec Robust 08-08**：[原始结果](/home/hongsheng/dec_con_asf/logs/exp_260808_131759_TaskDecControlRobust_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt)；[配置](/home/hongsheng/dec_con_asf/logs/exp_260808_131759_TaskDecControlRobust_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml)
- **TaskDec Robust 08-21 final**：[原始结果](/home/hongsheng/dec_con_asf/logs/exp_260821_002150_TaskDecControlRobust_v2_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt)；[配置](/home/hongsheng/dec_con_asf/logs/exp_260821_002150_TaskDecControlRobust_v2_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml)
- **TaskDec Robust model_6**：[原始结果](/home/hongsheng/dec_con_asf/logs/exp_260824_221613_TaskDecControlRobust_v2_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/epoch_6_total/0.3/complete_results.txt)；[配置](/home/hongsheng/dec_con_asf/logs/exp_260824_221613_TaskDecControlRobust_v2_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml)
- **TaskDec Robust model_8**：[原始结果](/home/hongsheng/dec_con_asf/logs/exp_260824_221632_TaskDecControlRobust_v2_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/epoch_8_total/0.3/complete_results.txt)；[配置](/home/hongsheng/dec_con_asf/logs/exp_260824_221632_TaskDecControlRobust_v2_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml)
- **DecControlled Strong resume model_16**：[原始结果](/home/hongsheng/dec_con_asf/logs/exp_260827_212019_DecControlledASFStrong_v2_0_resume20_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/epoch_16_total/0.3/complete_results.txt)；[配置](/home/hongsheng/dec_con_asf/logs/exp_260827_212019_DecControlledASFStrong_v2_0_resume20_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml)

复现脚本：[audit_taskdec_v2_results_260912.py](../tools/analysis/audit_taskdec_v2_results_260912.py)。同名 CSV 保存全部 18 个条件、两类、六个指标的原始数值及差值；sources.json 保存输入路径和摘要。
