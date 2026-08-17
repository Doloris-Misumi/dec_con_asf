# K-Radar v1.0 TaskDec Published Comparison

Generated at: 2026-08-12T20:48:31

Scope: K-Radar v1.0 labels, Sedan class, narrow RoI. Our TaskDec rows are C+L+4DR; 3D-LRF/L4DR are L+4DR paper-reported rows and their confidence thresholds are not disclosed.

## Total Metrics
| Method | Modality | Conf | BEV@0.3 | 3D@0.3 | BEV@0.5 | 3D@0.5 | 3D@0.7 |
|---|---|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0.0 | 88.59 | 87.34 | 86.97 | 72.95 | 18.85 |
| TaskDec Balanced v1 conf0.0 | C+L+4DR | 0.0 | 88.73 | 87.76 | 87.33 | 73.39 | 19.65 |
| TaskDec Robust v1 conf0.0 | C+L+4DR | 0.0 | 88.57 | 87.21 | 86.93 | 72.83 | 22.32 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 80.78 | 80.31 | 80.33 | 67.19 | 18.85 |
| TaskDec Balanced v1 conf0.3 | C+L+4DR | 0.3 | 80.93 | 80.59 | 80.48 | 67.45 | 19.65 |
| TaskDec Robust v1 conf0.3 | C+L+4DR | 0.3 | 80.87 | 80.42 | 80.43 | 67.21 | 22.32 |
| 3D-LRF | L+4DR | paper-reported | 84.00 | 74.80 | 73.60 | 45.20 | - |
| L4DR | L+4DR | paper-reported | 79.50 | 78.00 | 77.50 | 53.50 | - |

## Delta On Total Metrics
| Comparison | dBEV@0.3 | d3D@0.3 | dBEV@0.5 | d3D@0.5 | d3D@0.7 |
|---|---:|---:|---:|---:|---:|
| TaskDec Balanced v1 conf0.0 - Official ASF v1 conf0.0 | 0.14 | 0.42 | 0.36 | 0.44 | 0.80 |
| TaskDec Robust v1 conf0.0 - Official ASF v1 conf0.0 | -0.02 | -0.13 | -0.04 | -0.12 | 3.47 |
| TaskDec Balanced v1 conf0.3 - Official ASF v1 conf0.3 | 0.15 | 0.28 | 0.16 | 0.25 | 0.80 |
| TaskDec Robust v1 conf0.3 - Official ASF v1 conf0.3 | 0.10 | 0.11 | 0.10 | 0.01 | 3.47 |
| TaskDec Balanced v1 conf0.3 - L4DR | 1.43 | 2.59 | 2.98 | 13.95 | - |
| TaskDec Balanced v1 conf0.3 - 3D-LRF | -3.07 | 5.79 | 6.88 | 22.25 | - |

## Weather 3D@IoU0.3, conf=0.3
| Method | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.3 | 80.31 | 79.57 | 89.89 | 90.67 | 80.97 | 80.20 | 80.89 | 71.71 |
| TaskDec Balanced v1 conf0.3 | 80.59 | 80.07 | 90.38 | 90.68 | 80.66 | 80.58 | 89.50 | 71.70 |
| TaskDec Robust v1 conf0.3 | 80.42 | 79.89 | 89.89 | 90.75 | 80.72 | 80.50 | 89.24 | 71.78 |
| 3D-LRF | 74.80 | 81.20 | 87.20 | 86.10 | 73.80 | 49.50 | 87.90 | 67.20 |
| L4DR | 78.00 | 77.70 | 80.00 | 88.60 | 79.20 | 60.10 | 78.90 | 51.90 |

## Weather 3D@IoU0.3, paper-like conf=0.0
| Method | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | 87.34 | 86.64 | 89.85 | 90.67 | 88.57 | 79.99 | 88.81 | 77.50 |
| TaskDec Balanced v1 conf0.0 | 87.76 | 87.31 | 90.38 | 90.68 | 87.99 | 80.56 | 89.22 | 77.79 |
| TaskDec Robust v1 conf0.0 | 87.21 | 86.95 | 89.75 | 90.75 | 87.87 | 80.50 | 89.04 | 77.25 |

## Weather Delta vs Official ASF v1, 3D@IoU0.3
| Method | Reference | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TaskDec Balanced v1 conf0.0 | Official ASF v1 conf0.0 | 0.42 | 0.67 | 0.53 | 0.02 | -0.58 | 0.57 | 0.41 | 0.29 |
| TaskDec Robust v1 conf0.0 | Official ASF v1 conf0.0 | -0.13 | 0.30 | -0.10 | 0.08 | -0.70 | 0.51 | 0.23 | -0.25 |
| TaskDec Balanced v1 conf0.3 | Official ASF v1 conf0.3 | 0.28 | 0.50 | 0.49 | 0.02 | -0.31 | 0.38 | 8.61 | -0.01 |
| TaskDec Robust v1 conf0.3 | Official ASF v1 conf0.3 | 0.11 | 0.31 | -0.00 | 0.08 | -0.25 | 0.30 | 8.36 | 0.07 |

## Road/Time Breakdown For Our v1 Runs, 3D@IoU0.3 conf=0.3
| Condition | TaskDec Balanced | TaskDec Robust | Balanced - Robust |
|---|---:|---:|---:|
| urban | 80.76 | 80.81 | -0.06 |
| highway | 88.90 | 88.57 | 0.32 |
| countryside | 79.14 | 78.26 | 0.88 |
| alleyway | 60.75 | 60.28 | 0.47 |
| parkinglots | 72.38 | 72.27 | 0.12 |
| shoulder | 90.64 | 90.68 | -0.03 |
| mountain | 90.80 | 90.86 | -0.06 |
| university | 80.05 | 79.67 | 0.38 |
| day | 80.50 | 80.27 | 0.23 |
| night | 80.78 | 80.74 | 0.05 |

## Notes
- Under the paper-like conf=0.0 setting, TaskDec Balanced slightly exceeds the official ASF v1 log: +0.14 BEV@0.3, +0.42 3D@0.3, +0.36 BEV@0.5, and +0.44 3D@0.5.
- Under the stricter conf=0.3 setting, TaskDec Balanced is still slightly above official ASF v1: +0.15 BEV@0.3 and +0.28 3D@0.3. Robust is also positive but smaller: +0.10 BEV@0.3 and +0.11 3D@0.3.
- Balanced is consistently the better of the two variants on the main Total 3D@0.3 metric. Robust only shows a clear advantage at stricter 3D@0.7, where it is +3.47 over official ASF conf=0.3 and +3.47 over official ASF conf=0.0.
- The biggest weather gain over official ASF is LightSnow, especially under conf=0.3. Rain is flat to slightly lower, so this still does not solve the rain weakness we saw on v2.
- Compared with paper-reported L4DR/3D-LRF, TaskDec Balanced conf=0.3 is higher on Total 3D@0.3, but that comparison has two caveats: C+L+4DR vs L+4DR, and 3D-LRF/L4DR do not disclose confidence threshold.

## Files
- Balanced export: `/home/hongsheng/dec_con_asf/results/exp_260810_221300_TaskDecControlBalanced_v1_final`
- Robust export: `/home/hongsheng/dec_con_asf/results/exp_260810_221258_TaskDecControlRobust_v1_final`
- Published reference table: `/home/hongsheng/dec_con_asf/results/published_k_radar_v1_references.json`
