# Task Dec Control Comparison 260810

Generated at: 2026-08-10T21:56:33

## Saved Result Directories
- Prev Gentle: `/home/hongsheng/dec_con_asf/results/exp_260806_000821_DecControlledASFGentle_final`
- Prev Strong: `/home/hongsheng/dec_con_asf/results/exp_260806_000825_DecControlledASFStrong_final`
- Task Balanced: `/home/hongsheng/dec_con_asf/results/exp_260808_131759_TaskDecControlBalanced_final`
- Task Robust: `/home/hongsheng/dec_con_asf/results/exp_260808_131759_TaskDecControlRobust_final`

## Main Results, conf=0.3, condition=all
| Run | sed BEV@0.3 | sed 3D@0.3 | bus BEV@0.3 | bus 3D@0.3 | mean BEV@0.3 | mean 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| Prev Gentle | 77.37 | 74.57 | 65.70 | 56.41 | 71.54 | 65.49 |
| Prev Strong | 77.32 | 74.58 | 65.14 | 59.24 | 71.23 | 66.91 |
| Task Balanced | 75.34 | 74.51 | 67.46 | 58.42 | 71.40 | 66.46 |
| Task Robust | 75.32 | 74.59 | 63.08 | 54.62 | 69.20 | 64.61 |

## Main Results, conf=0.0, condition=all
| Run | sed BEV@0.3 | sed 3D@0.3 | bus BEV@0.3 | bus 3D@0.3 | mean BEV@0.3 | mean 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| Prev Gentle | 81.99 | 78.89 | 68.39 | 58.89 | 75.19 | 68.89 |
| Prev Strong | 81.88 | 78.91 | 67.59 | 59.91 | 74.73 | 69.41 |
| Task Balanced | 80.42 | 77.39 | 68.62 | 59.50 | 74.52 | 68.44 |
| Task Robust | 80.56 | 77.63 | 66.16 | 57.47 | 73.36 | 67.55 |

## IoU Profile, conf=0.3, condition=all, mean(sed,bus)
| Run | BEV@0.7 | BEV@0.5 | BEV@0.3 | 3D@0.7 | 3D@0.5 | 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| Task Balanced | 30.98 | 60.59 | 71.40 | 9.60 | 41.35 | 66.46 |
| Task Robust | 32.80 | 61.27 | 69.20 | 9.84 | 43.34 | 64.61 |

## Weather Mean 3D@0.3, conf=0.3, mean(sed,bus)
| Condition | Prev Gentle | Prev Strong | Task Balanced | Task Robust |
|---|---:|---:|---:|---:|
| all | 65.49 | 66.91 | 66.46 | 64.61 |
| normal | 62.40 | 62.57 | 62.01 | 61.27 |
| overcast | 79.18 | 79.06 | 76.70 | 75.75 |
| fog | 46.11 | 47.23 | 47.36 | 47.29 |
| rain | 39.30 | 39.10 | 37.70 | 35.73 |
| sleet | 63.64 | 64.99 | 65.26 | 62.01 |
| lightsnow | 88.19 | 89.56 | 89.13 | 87.24 |
| heavysnow | 65.46 | 67.96 | 65.67 | 64.63 |

## Delta vs Prev Strong, conf=0.3, @IoU0.3
| Run | Condition | mean BEV delta | mean 3D delta | sed 3D delta | bus 3D delta |
|---|---|---:|---:|---:|---:|
| Task Balanced | all | 0.17 | -0.45 | -0.08 | -0.83 |
| Task Balanced | normal | -1.17 | -0.56 | -0.09 | -1.03 |
| Task Balanced | overcast | -1.03 | -2.36 | -2.16 | -2.57 |
| Task Balanced | fog | 0.04 | 0.13 | 0.26 | 0.00 |
| Task Balanced | rain | -1.44 | -1.40 | -1.89 | -0.90 |
| Task Balanced | sleet | 3.15 | 0.26 | -1.22 | 1.74 |
| Task Balanced | lightsnow | 1.70 | -0.43 | 0.57 | -1.42 |
| Task Balanced | heavysnow | 0.08 | -2.28 | -0.31 | -4.26 |
| Task Robust | all | -2.03 | -2.31 | 0.01 | -4.62 |
| Task Robust | normal | -0.05 | -1.31 | -0.15 | -2.46 |
| Task Robust | overcast | -3.59 | -3.32 | -1.88 | -4.75 |
| Task Robust | fog | 0.03 | 0.07 | 0.13 | 0.00 |
| Task Robust | rain | -2.30 | -3.36 | -2.03 | -4.70 |
| Task Robust | sleet | -1.63 | -2.98 | -0.91 | -5.05 |
| Task Robust | lightsnow | 0.10 | -2.32 | -1.43 | -3.20 |
| Task Robust | heavysnow | -3.42 | -3.33 | -0.45 | -6.21 |

## Notes
- Task Balanced is competitive but does not beat Prev Strong on the main mean 3D@0.3 metric: 66.46 vs 66.91.
- Task Robust improves stricter IoU means over Task Balanced, especially 3D@0.5, but hurts loose IoU@0.3 and bus recall-like metrics.
- Rain is not fixed by the current task-dec control design; both new runs are below Prev Strong on rain mean 3D@0.3.
- Stronger control appears to over-regularize or suppress bus detections. The next useful direction is class/weather-aware gating or a weaker bus-preserving gate, not simply increasing control strength.

## Broader Context, conf=0.3, condition=all
| Run | mean BEV@0.3 | mean 3D@0.3 | sed 3D@0.3 | bus 3D@0.3 | rain mean 3D@0.3 | heavysnow mean 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| DecCon PrevStrong | 71.23 | 66.91 | 74.58 | 59.24 | 39.10 | 67.96 |
| official_asf_v2_RLC | 72.85 | 66.55 | 74.98 | 58.13 | 37.13 | 65.91 |
| Task Balanced | 71.40 | 66.46 | 74.51 | 58.42 | 37.70 | 65.67 |
| ObjPatch Gentle | 71.14 | 65.32 | 72.54 | 58.09 | 34.47 | 65.06 |
| FgGatedSelective | 70.44 | 65.32 | 74.70 | 55.93 | 36.47 | 67.12 |
| FgGated | 71.47 | 65.24 | 74.48 | 56.00 | 35.23 | 65.80 |
| PatchDec first | 69.96 | 65.03 | 74.48 | 55.58 | 35.18 | 65.39 |
| ASF repro exp260725 | 71.28 | 65.03 | 74.61 | 55.44 | 35.47 | 65.61 |
| ObjPatch Strong | 69.94 | 64.99 | 74.48 | 55.51 | 35.13 | 65.58 |
| Task Robust | 69.20 | 64.61 | 74.59 | 54.62 | 35.73 | 64.63 |

Broad-context takeaway: Task Balanced is close to official ASF v2 RLC but still below DecCon PrevStrong on mean 3D@0.3. Task Robust is mainly hurt by bus and adverse-weather means.

## Published K-Radar v1.0 References

These rows are paper/official-log references for the K-Radar v1.0 Sedan narrow-RoI setting, so they should not be mixed directly with the v2.0 two-class results above. Full per-weather BEV/3D tables are saved in `/home/hongsheng/dec_con_asf/results/published_k_radar_v1_references.md`.

Sources:
- 3D-LRF: Chae et al., CVPR 2024, "Towards Robust 3D Object Detection with LiDAR and 4D Radar Fusion in Various Weather Conditions". The v1.0 values below are the rows reproduced/collected in L4DR arXiv v6 Table 9.
- L4DR: Huang et al., AAAI 2025 / arXiv:2408.03677. Table 1 reports IoU=0.5; Table 9 additionally reports IoU=0.3 with v1.0 labels.
- Official ASF v1: local downloaded official ASF logs, `exp250303`.

### v1.0 3D@IoU0.3
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 | C+L+4DR | 0.0 | 87.3 | 86.6 | 89.8 | 90.7 | 88.6 | 80.0 | 88.8 | 77.5 |
| Official ASF v1 | C+L+4DR | 0.3 | 80.3 | 79.6 | 89.9 | 90.7 | 81.0 | 80.2 | 80.9 | 71.7 |
| 3D-LRF | L+4DR | paper-reported | 74.8 | 81.2 | 87.2 | 86.1 | 73.8 | 49.5 | 87.9 | 67.2 |
| L4DR | L+4DR | paper-reported | 78.0 | 77.7 | 80.0 | 88.6 | 79.2 | 60.1 | 78.9 | 51.9 |

### v1.0 Total Metrics
| Method | Conf | BEV@0.3 | 3D@0.3 | BEV@0.5 | 3D@0.5 |
|---|---:|---:|---:|---:|---:|
| Official ASF v1 | 0.0 | 88.6 | 87.3 | 87.0 | 72.9 |
| Official ASF v1 | 0.3 | 80.8 | 80.3 | 80.3 | 67.2 |
| 3D-LRF | paper-reported | 84.0 | 74.8 | 73.6 | 45.2 |
| L4DR | paper-reported | 79.5 | 78.0 | 77.5 | 53.5 |

Reference takeaway: ASF official v1 Table-1-scale numbers match `conf=0.0`; under a stricter `conf=0.3`, ASF v1 Total 3D@0.3 drops to 80.3, still above the paper-reported 3D-LRF/L4DR totals but by a much smaller margin. 3D-LRF/L4DR do not disclose their confidence threshold in these tables, so they remain `paper-reported` references rather than confirmed `conf=0.3` baselines.

## Our Dec-Controlled ASF v1.0 Runs

Full statistics are saved in `/home/hongsheng/dec_con_asf/results/v1_task_dec_published_comparison_260812.md`.

| Run | Conf | BEV@0.3 | 3D@0.3 | BEV@0.5 | 3D@0.5 |
|---|---:|---:|---:|---:|---:|
| Official ASF v1 | 0.0 | 88.59 | 87.34 | 86.97 | 72.95 |
| TaskDec Balanced v1 | 0.0 | 88.73 | 87.76 | 87.33 | 73.39 |
| TaskDec Robust v1 | 0.0 | 88.57 | 87.21 | 86.93 | 72.83 |
| Official ASF v1 | 0.3 | 80.78 | 80.31 | 80.33 | 67.19 |
| TaskDec Balanced v1 | 0.3 | 80.93 | 80.59 | 80.48 | 67.45 |
| TaskDec Robust v1 | 0.3 | 80.87 | 80.42 | 80.43 | 67.21 |

v1 takeaway: TaskDec Balanced is the best of our two v1 variants. It is slightly above the downloaded official ASF v1 log under both the paper-like `conf=0.0` setting (+0.42 3D@0.3) and the stricter `conf=0.3` setting (+0.28 3D@0.3), but the gain is still small.

## Best-Checkpoint v1.0 Full Eval

Full statistics are saved in `/home/hongsheng/dec_con_asf/results/v1_best_checkpoint_full_comparison_260813.md`.

| Run | Selected ckpt | Conf | BEV@0.3 | 3D@0.3 | BEV@0.5 | 3D@0.5 |
|---|---|---:|---:|---:|---:|---:|
| Official ASF v1 | official | 0.0 | 88.59 | 87.34 | 86.97 | 72.95 |
| Balanced final | model_10 | 0.3 | 80.93 | 80.59 | 80.48 | 67.45 |
| Balanced best-subset | model_2 | 0.3 | 89.01 | 80.37 | 80.38 | 67.57 |
| Robust final | model_10 | 0.3 | 80.87 | 80.42 | 80.43 | 67.21 |
| Robust best-subset | model_0 | 0.3 | 88.84 | 88.36 | 88.10 | 67.50 |

Best-checkpoint takeaway: Balanced `model_2` does not improve full-test 3D@0.3 over final. Robust `model_0`, saved after epoch 0 training, is much stronger under `conf=0.3` and should be sanity-checked with a rerun because it changes the main conclusion substantially.
