# K-Radar v1 Best-Checkpoint Full Evaluation

Generated at: 2026-08-13T20:17:04

Scope: K-Radar v1.0 labels, Sedan class, narrow RoI. 3D-LRF/L4DR rows are paper-reported L+4DR references with undisclosed confidence threshold.

## Selected Checkpoints
| Variant | Selected epoch | Reason |
|---|---:|---|
| Balanced | 2 | Best 1000-frame subset `conf=0.3 3D@0.3` |
| Robust | 0 | Best 1000-frame subset `conf=0.3 3D@0.3` |

## Total Metrics
| Method | Conf | BEV@0.3 | 3D@0.3 | BEV@0.5 | 3D@0.5 | 3D@0.7 |
|---|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | 0.0 | 88.59 | 87.34 | 86.97 | 72.95 | 18.85 |
| Balanced final model10 conf0.0 | 0.0 | 88.73 | 87.76 | 87.33 | 73.39 | 19.65 |
| Balanced best-subset model2 conf0.0 | 0.0 | 88.73 | 87.73 | 87.21 | 73.13 | 21.89 |
| Robust final model10 conf0.0 | 0.0 | 88.57 | 87.21 | 86.93 | 72.83 | 22.32 |
| Robust best-subset model0 conf0.0 | 0.0 | 88.84 | 88.06 | 87.18 | 72.83 | 22.02 |
| Official ASF v1 conf0.3 | 0.3 | 80.78 | 80.31 | 80.33 | 67.19 | 18.85 |
| Balanced final model10 conf0.3 | 0.3 | 80.93 | 80.59 | 80.48 | 67.45 | 19.65 |
| Balanced best-subset model2 conf0.3 | 0.3 | 89.01 | 80.37 | 80.38 | 67.57 | 21.90 |
| Robust final model10 conf0.3 | 0.3 | 80.87 | 80.42 | 80.43 | 67.21 | 22.32 |
| Robust best-subset model0 conf0.3 | 0.3 | 88.84 | 88.36 | 88.10 | 67.50 | 22.04 |
| 3D-LRF | paper-reported | 84.00 | 74.80 | 73.60 | 45.20 | - |
| L4DR | paper-reported | 79.50 | 78.00 | 77.50 | 53.50 | - |

## Key Deltas
| Comparison | dBEV@0.3 | d3D@0.3 | dBEV@0.5 | d3D@0.5 | d3D@0.7 |
|---|---:|---:|---:|---:|---:|
| Balanced model2 - Balanced final, conf0.3 | 8.08 | -0.22 | -0.10 | 0.12 | 2.25 |
| Robust model0 - Robust final, conf0.3 | 7.97 | 7.93 | 7.67 | 0.29 | -0.28 |
| Robust model0 conf0.3 - Official ASF conf0.3 | 8.06 | 8.04 | 7.77 | 0.31 | 3.19 |
| Robust model0 conf0.3 - Official ASF conf0.0 | 0.25 | 1.02 | 1.12 | -5.45 | 3.19 |
| Robust model0 conf0.3 - L4DR | 9.34 | 10.36 | 10.60 | 14.00 | - |
| Robust model0 conf0.3 - 3D-LRF | 4.84 | 13.56 | 14.50 | 22.30 | - |

## Weather 3D@IoU0.3, conf=0.3
| Method | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.3 | 80.31 | 79.57 | 89.89 | 90.67 | 80.97 | 80.20 | 80.89 | 71.71 |
| Balanced final model10 conf0.3 | 80.59 | 80.07 | 90.38 | 90.68 | 80.66 | 80.58 | 89.50 | 71.70 |
| Balanced best-subset model2 conf0.3 | 80.37 | 87.71 | 90.40 | 90.73 | 80.86 | 80.39 | 89.53 | 71.62 |
| Robust final model10 conf0.3 | 80.42 | 79.89 | 89.89 | 90.75 | 80.72 | 80.50 | 89.24 | 71.78 |
| Robust best-subset model0 conf0.3 | 88.36 | 87.66 | 90.39 | 90.57 | 88.90 | 80.42 | 89.28 | 71.41 |
| 3D-LRF | 74.80 | 81.20 | 87.20 | 86.10 | 73.80 | 49.50 | 87.90 | 67.20 |
| L4DR | 78.00 | 77.70 | 80.00 | 88.60 | 79.20 | 60.10 | 78.90 | 51.90 |

## Notes
- Balanced `model_2` did not transfer from subset to full test: full `conf=0.3 3D@0.3` is 80.37, below Balanced final model10 at 80.59.
- Robust `model_0` is the real surprise: full `conf=0.3 3D@0.3` is 88.36, far above Robust final model10 at 80.42 and above official ASF v1 conf0.0 at 87.34.
- Robust `model_0` also strongly improves rain under conf=0.3: 88.90 vs official ASF conf0.3 at 80.97, and vs Robust final at 80.72.
- This result is promising but should be sanity-checked because epoch 0 being best is unusual and the subset sweep had an 88/80 AP jump pattern. At minimum, rerun Robust model0 full once or inspect whether model_0 is saved before/after epoch-0 training.

## Exported Result Directories
- Balanced model2: `/home/hongsheng/dec_con_asf/results/exp_260812_232646_TaskDecControlBalanced_v1_model2_full`
- Robust model0: `/home/hongsheng/dec_con_asf/results/exp_260812_232650_TaskDecControlRobust_v1_model0_full`
