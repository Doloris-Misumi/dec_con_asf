# Published K-Radar v1.0 Reference Results

Scope: Sedan class, narrow RoI K-Radar v1.0 labels. Earlier notes marked 3D-LRF/L4DR confidence thresholds as `paper-reported`, but public code/logs now make the practical evaluation protocol clearer: RTNH and 3D-LRF evaluate with `conf_thr=0.3`, and L4DR publishes its v1.1 result log under `Conf thr: 0.3`.

Sources:
- RTNH: K-Radar public `main_cond_0.py` calls `validate_kitti_conditional(list_conf_thr=[0.3, 0.5, 0.7])`.
- 3D-LRF: Chae et al., CVPR 2024. Its official `RL_3DOD/main_cond_0.py` calls `validate_kitti_conditional(..., list_conf_thr=[0.3], ...)`.
- L4DR: Huang et al., AAAI 2025 / arXiv:2408.03677. Its K-Radar evaluator includes `list_conf_thr=[0.1, 0.2, 0.3]`; the public v1.1 result log is headed `Conf thr: 0.3`.
- Official ASF v1: local downloaded official ASF logs extracted to `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303`. ASF Table 1 aligns with the `conf=0.0` log; for protocol-consistent comparison against RTNH/3D-LRF/L4DR, use the same released checkpoint evaluated at `conf=0.3`.

## 3D@IoU0.3
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0 | 87.3 | 86.6 | 89.8 | 90.7 | 88.6 | 80.0 | 88.8 | 77.5 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 80.3 | 79.6 | 89.9 | 90.7 | 81.0 | 80.2 | 80.9 | 71.7 |
| 3D-LRF | L+4DR | 0.3/public eval | 74.8 | 81.2 | 87.2 | 86.1 | 73.8 | 49.5 | 87.9 | 67.2 |
| L4DR | L+4DR | 0.3/public log | 78.0 | 77.7 | 80.0 | 88.6 | 79.2 | 60.1 | 78.9 | 51.9 |

## BEV@IoU0.3
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0 | 88.6 | 88.1 | 90.3 | 99.0 | 89.1 | 80.4 | 89.4 | 78.7 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 80.8 | 88.4 | 90.3 | 90.9 | 81.2 | 80.5 | 89.5 | 72.0 |
| 3D-LRF | L+4DR | 0.3/public eval | 84.0 | 83.7 | 89.2 | 95.4 | 78.3 | 60.7 | 88.9 | 74.9 |
| L4DR | L+4DR | 0.3/public log | 79.5 | 86.0 | 89.6 | 89.9 | 81.1 | 62.3 | 89.1 | 61.3 |

## 3D@IoU0.5
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0 | 72.9 | 64.6 | 86.6 | 79.6 | 73.4 | 67.0 | 77.6 | 66.7 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 67.2 | 64.6 | 79.7 | 79.6 | 67.3 | 67.3 | 77.6 | 61.6 |
| 3D-LRF | L+4DR | 0.3/public eval | 45.2 | 45.3 | 55.8 | 51.8 | 38.3 | 23.4 | 60.2 | 36.9 |
| L4DR | L+4DR | 0.3/public log | 53.5 | 53.0 | 64.1 | 73.2 | 53.8 | 46.2 | 52.4 | 37.0 |

## BEV@IoU0.5
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0 | 87.0 | 86.2 | 90.2 | 90.8 | 88.8 | 78.2 | 88.6 | 71.0 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 80.3 | 79.6 | 90.2 | 90.8 | 81.1 | 71.0 | 80.8 | 71.0 |
| 3D-LRF | L+4DR | 0.3/public eval | 73.6 | 72.3 | 88.4 | 86.6 | 76.6 | 47.5 | 79.6 | 64.1 |
| L4DR | L+4DR | 0.3/public log | 77.5 | 76.8 | 88.6 | 89.7 | 78.2 | 59.3 | 80.9 | 53.8 |

## Quick Takeaways
- For the ASF official v1 log, `conf=0.0` reproduces the paper-like Table 1 scale: 3D@0.3 is 87.3 and BEV@0.3 is 88.6.
- At IoU=0.3, L4DR reports higher Total 3D than 3D-LRF (78.0 vs 74.8), but lower BEV (79.5 vs 84.0).
- At IoU=0.5, L4DR is clearly stronger than 3D-LRF on Total 3D (53.5 vs 45.2) and BEV (77.5 vs 73.6).
- The paper-facing comparison should use the official ASF released checkpoint at `conf=0.3`, not the ASF Table 1 `conf=0.0` row, when comparing against RTNH/3D-LRF/L4DR.
