# DEC v1 Selected Full Evaluation Results

Date: 2026-08-17

## Runs

- MoreOpenGate_model0: epoch 0, GPU0, exp `/home/hongsheng/dec_con_asf/logs/exp_260817_000340_TaskDecControlMoreOpenGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
- StrongerControl_model2: epoch 2, GPU1, exp `/home/hongsheng/dec_con_asf/logs/exp_260817_000503_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
- StrongerControl_model4: epoch 4, GPU2, exp `/home/hongsheng/dec_con_asf/logs/exp_260817_000340_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
- MoreOpenGate_model2: epoch 2, GPU3, exp `/home/hongsheng/dec_con_asf/logs/exp_260817_000507_TaskDecControlMoreOpenGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`

## Overall AP, conf=0.3

| Run | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | mean_all6 | mean_3d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MoreOpenGate_model2 | 62.22 | 22.06 | 80.35 | 67.80 | 89.00 | 88.51 | 68.32 | 59.46 |
| MoreOpenGate_model0 | 62.30 | 21.33 | 87.77 | 67.21 | 88.62 | 88.08 | 69.22 | 58.87 |
| StrongerControl_model4 | 63.11 | 18.99 | 80.52 | 67.70 | 88.99 | 80.52 | 66.64 | 55.74 |
| StrongerControl_model2 | 62.49 | 22.45 | 80.42 | 68.06 | 89.06 | 80.51 | 67.17 | 57.01 |

## Overall AP, conf=0

| Run | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | mean_all6 | mean_3d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| StrongerControl_model4 | 63.11 | 18.99 | 87.35 | 73.35 | 88.77 | 87.78 | 69.89 | 60.04 |
| MoreOpenGate_model2 | 62.22 | 22.06 | 87.24 | 73.46 | 88.85 | 87.77 | 70.27 | 61.10 |
| StrongerControl_model2 | 62.49 | 22.45 | 87.16 | 73.78 | 88.81 | 87.72 | 70.40 | 61.32 |
| MoreOpenGate_model0 | 62.30 | 21.33 | 86.40 | 72.39 | 88.62 | 87.59 | 69.77 | 60.44 |

## Weather 3D@0.3, conf=0.3

| Run | normal | overcast | fog | rain | sleet | lightsnow | heavysnow | weather_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MoreOpenGate_model0 | 87.33 | 90.34 | 90.34 | 88.95 | 79.71 | 89.18 | 71.13 | 85.28 |
| StrongerControl_model4 | 87.80 | 90.38 | 90.75 | 80.77 | 80.48 | 89.28 | 71.38 | 84.41 |
| MoreOpenGate_model2 | 87.90 | 90.33 | 90.72 | 80.87 | 80.77 | 89.44 | 70.63 | 84.38 |
| StrongerControl_model2 | 88.00 | 90.27 | 90.76 | 80.70 | 80.43 | 89.35 | 71.02 | 84.36 |

## Weather 3D@0.7/0.5/0.3 Details, conf=0.3

### MoreOpenGate_model0
| Condition | 3D@0.7 | 3D@0.5 | 3D@0.3 | BEV@0.3 |
| --- | --- | --- | --- | --- |
| normal | 13.34 | 65.71 | 87.33 | 88.32 |
| overcast | 28.13 | 80.17 | 90.34 | 90.40 |
| fog | 40.92 | 78.86 | 90.34 | 90.72 |
| rain | 22.21 | 74.88 | 88.95 | 89.42 |
| sleet | 13.98 | 57.07 | 79.71 | 80.10 |
| lightsnow | 25.10 | 77.68 | 89.18 | 89.32 |
| heavysnow | 23.28 | 59.83 | 71.13 | 71.32 |

### StrongerControl_model2
| Condition | 3D@0.7 | 3D@0.5 | 3D@0.3 | BEV@0.3 |
| --- | --- | --- | --- | --- |
| normal | 20.54 | 66.75 | 88.00 | 88.62 |
| overcast | 27.85 | 80.11 | 90.27 | 90.42 |
| fog | 45.60 | 79.99 | 90.76 | 90.83 |
| rain | 22.40 | 68.49 | 80.70 | 81.16 |
| sleet | 9.30 | 60.01 | 80.43 | 80.65 |
| lightsnow | 29.95 | 77.68 | 89.35 | 89.45 |
| heavysnow | 23.89 | 60.72 | 71.02 | 71.30 |

### StrongerControl_model4
| Condition | 3D@0.7 | 3D@0.5 | 3D@0.3 | BEV@0.3 |
| --- | --- | --- | --- | --- |
| normal | 14.93 | 65.85 | 87.80 | 88.51 |
| overcast | 24.61 | 80.67 | 90.38 | 90.46 |
| fog | 43.19 | 79.51 | 90.75 | 90.81 |
| rain | 20.01 | 68.83 | 80.77 | 89.37 |
| sleet | 15.87 | 59.20 | 80.48 | 80.80 |
| lightsnow | 29.51 | 76.70 | 89.28 | 89.40 |
| heavysnow | 26.36 | 61.07 | 71.38 | 71.63 |

### MoreOpenGate_model2
| Condition | 3D@0.7 | 3D@0.5 | 3D@0.3 | BEV@0.3 |
| --- | --- | --- | --- | --- |
| normal | 15.17 | 66.22 | 87.90 | 88.62 |
| overcast | 25.90 | 79.90 | 90.33 | 90.45 |
| fog | 46.41 | 79.84 | 90.72 | 90.83 |
| rain | 21.76 | 68.63 | 80.87 | 89.51 |
| sleet | 10.74 | 67.76 | 80.77 | 80.96 |
| lightsnow | 30.87 | 77.73 | 89.44 | 89.51 |
| heavysnow | 25.61 | 60.18 | 70.63 | 70.92 |

## Files

- Overall CSV: `/home/hongsheng/dec_con_asf/analysis_exports/dec_v1_selected_full_overall_260817.csv`
- Conditional CSV: `/home/hongsheng/dec_con_asf/analysis_exports/dec_v1_selected_full_conditional_260817.csv`
- Weather CSV: `/home/hongsheng/dec_con_asf/analysis_exports/dec_v1_selected_full_weather_260817.csv`