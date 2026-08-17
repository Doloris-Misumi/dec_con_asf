# Published K-Radar v1.0 Reference Results

Scope: Sedan class, narrow RoI K-Radar v1.0 labels. 3D-LRF/L4DR confidence thresholds are not reported in the papers, so they are marked as `paper-reported` rather than assigned a conf value.

Sources:
- 3D-LRF: Chae et al., CVPR 2024. Values below use the K-Radar v1.0 rows reproduced/collected in L4DR arXiv v6 Table 9.
- L4DR: Huang et al., AAAI 2025 / arXiv:2408.03677 v6. Table 1 reports IoU=0.5 on K-Radar; Table 9 additionally reports IoU=0.3 with v1.0 labels.
- Official ASF v1: local downloaded official ASF logs extracted to `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303`.

## 3D@IoU0.3
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0 | 87.3 | 86.6 | 89.8 | 90.7 | 88.6 | 80.0 | 88.8 | 77.5 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 80.3 | 79.6 | 89.9 | 90.7 | 81.0 | 80.2 | 80.9 | 71.7 |
| 3D-LRF | L+4DR | paper-reported | 74.8 | 81.2 | 87.2 | 86.1 | 73.8 | 49.5 | 87.9 | 67.2 |
| L4DR | L+4DR | paper-reported | 78.0 | 77.7 | 80.0 | 88.6 | 79.2 | 60.1 | 78.9 | 51.9 |

## BEV@IoU0.3
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0 | 88.6 | 88.1 | 90.3 | 99.0 | 89.1 | 80.4 | 89.4 | 78.7 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 80.8 | 88.4 | 90.3 | 90.9 | 81.2 | 80.5 | 89.5 | 72.0 |
| 3D-LRF | L+4DR | paper-reported | 84.0 | 83.7 | 89.2 | 95.4 | 78.3 | 60.7 | 88.9 | 74.9 |
| L4DR | L+4DR | paper-reported | 79.5 | 86.0 | 89.6 | 89.9 | 81.1 | 62.3 | 89.1 | 61.3 |

## 3D@IoU0.5
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0 | 72.9 | 64.6 | 86.6 | 79.6 | 73.4 | 67.0 | 77.6 | 66.7 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 67.2 | 64.6 | 79.7 | 79.6 | 67.3 | 67.3 | 77.6 | 61.6 |
| 3D-LRF | L+4DR | paper-reported | 45.2 | 45.3 | 55.8 | 51.8 | 38.3 | 23.4 | 60.2 | 36.9 |
| L4DR | L+4DR | paper-reported | 53.5 | 53.0 | 64.1 | 73.2 | 53.8 | 46.2 | 52.4 | 37.0 |

## BEV@IoU0.5
| Method | Modality | Conf | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official ASF v1 conf0.0 | C+L+4DR | 0 | 87.0 | 86.2 | 90.2 | 90.8 | 88.8 | 78.2 | 88.6 | 71.0 |
| Official ASF v1 conf0.3 | C+L+4DR | 0.3 | 80.3 | 79.6 | 90.2 | 90.8 | 81.1 | 71.0 | 80.8 | 71.0 |
| 3D-LRF | L+4DR | paper-reported | 73.6 | 72.3 | 88.4 | 86.6 | 76.6 | 47.5 | 79.6 | 64.1 |
| L4DR | L+4DR | paper-reported | 77.5 | 76.8 | 88.6 | 89.7 | 78.2 | 59.3 | 80.9 | 53.8 |

## Quick Takeaways
- For the ASF official v1 log, `conf=0.0` reproduces the paper-like Table 1 scale: 3D@0.3 is 87.3 and BEV@0.3 is 88.6.
- At IoU=0.3, L4DR reports higher Total 3D than 3D-LRF (78.0 vs 74.8), but lower BEV (79.5 vs 84.0).
- At IoU=0.5, L4DR is clearly stronger than 3D-LRF on Total 3D (53.5 vs 45.2) and BEV (77.5 vs 73.6).
- These published rows should be compared as paper-reported references, because 3D-LRF/L4DR do not disclose the confidence threshold in the table.
