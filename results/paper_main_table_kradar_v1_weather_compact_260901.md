# Compact main table: K-Radar v1.0 Sedan with weather breakdown

Date: 2026-09-01

Protocol wording:

K-Radar benchmark v1.0, Sedan class, driving-corridor ROI. `R` denotes 4D Radar. ASF is the released official checkpoint re-evaluated locally at `conf_thr=0.3`; other published methods use the numbers reported in their papers.

## Recommended compact summary table

| Method | Sensors | Source | APBEV@0.5 | AP3D@0.5 | APBEV@0.3 | AP3D@0.3 |
|---|---|---|---:|---:|---:|---:|
| RTNH | R | K-Radar / AW-MoE Table II | 36.00 | 14.10 | 41.10 | 37.40 |
| 3D-LRF | L+R | CVPR 2024 / AW-MoE Table II | 73.60 | 45.20 | 84.00 | 74.80 |
| L4DR | L+R | AAAI 2025 / AW-MoE Table II | 77.50 | 53.50 | 79.50 | 78.00 |
| ASF | C+L+R | official ckpt, local `conf_thr=0.3` | 80.33 | 67.19 | 80.78 | 80.31 |
| AW-MoE | L+R | AW-MoE Table II | 84.20 | 61.50 | 88.20 | 83.90 |
| AW-MoE-LRC | C+L+R | AW-MoE Table III | - | 61.80 | - | 84.30 |
| TaskDec Robust (ours) | C+L+R | local `model_0`, `conf_thr=0.3` | **88.10** | **67.50** | **88.84** | **88.36** |

## ASF-style weather table: AP3D@IoU=0.3

This is the recommended main weather table because AP3D@0.3 is the primary SOTA claim and all selected methods have values for it.

| Method | Sensors | Total | Nor. | Ove. | Fog | Rain | Sle. | L.s. | H.s. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RTNH | R | 37.40 | 37.60 | 42.00 | 41.20 | 29.20 | 49.10 | 63.90 | 43.10 |
| 3D-LRF | L+R | 74.80 | 81.20 | 87.20 | 86.10 | 73.80 | 49.50 | 87.90 | 67.20 |
| L4DR | L+R | 78.00 | 77.70 | 80.00 | 88.60 | 79.20 | 60.10 | 78.90 | 51.90 |
| ASF | C+L+R | 80.31 | 79.57 | 89.89 | 90.67 | 80.97 | 80.20 | 80.89 | **71.71** |
| AW-MoE | L+R | 83.90 | 84.20 | 90.00 | **95.30** | 84.40 | 72.90 | **90.20** | 64.00 |
| AW-MoE-LRC | C+L+R | 84.30 | 84.70 | **91.00** | **95.30** | 84.00 | 72.90 | 89.60 | 63.70 |
| TaskDec Robust (ours) | C+L+R | **88.36** | **87.66** | 90.39 | 90.57 | **88.90** | **80.42** | 89.28 | 71.41 |

## Optional weather table: AP3D@IoU=0.5

Use this either below the main AP3D@0.3 table or in the appendix. It is useful because ASF's original main text emphasizes IoU=0.5.

| Method | Sensors | Total | Nor. | Ove. | Fog | Rain | Sle. | L.s. | H.s. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RTNH | R | 14.10 | 19.70 | 20.50 | 15.90 | 13.00 | 13.50 | 21.00 | 6.36 |
| 3D-LRF | L+R | 45.20 | 45.30 | 55.80 | 51.80 | 38.30 | 23.40 | 60.20 | 36.90 |
| L4DR | L+R | 53.50 | 53.00 | 64.10 | 73.20 | 53.80 | 46.20 | 52.40 | 37.00 |
| ASF | C+L+R | 67.19 | 64.56 | 79.71 | 79.57 | 67.33 | **67.28** | 77.63 | **61.61** |
| AW-MoE | L+R | 61.50 | 59.00 | 67.20 | 85.70 | 63.50 | 43.30 | 70.10 | 53.10 |
| AW-MoE-LRC | C+L+R | 61.80 | 60.20 | 70.40 | **85.80** | 63.40 | 43.70 | 69.90 | 52.80 |
| TaskDec Robust (ours) | C+L+R | **67.50** | **65.98** | **80.26** | 79.71 | **74.92** | 57.60 | **78.33** | 60.51 |

## LaTeX draft for the main weather table

```latex
\begin{table*}[t]
\centering
\caption{AP$_{\mathrm{3D}}$ comparison on the K-Radar v1.0 Sedan benchmark under IoU=0.3. ASF is evaluated from the released checkpoint with \texttt{conf\_thr=0.3}; other literature results are taken from the corresponding papers. Nor., Ove., Sle., L.s., and H.s. denote Normal, Overcast, Sleet, Light snow, and Heavy snow, respectively.}
\label{tab:kradar_v1_weather_ap3d_03}
\resizebox{\textwidth}{!}{
\begin{tabular}{lcccccccccc}
\toprule
Method & Sensors & Total & Nor. & Ove. & Fog & Rain & Sle. & L.s. & H.s. \\
\midrule
RTNH & R & 37.40 & 37.60 & 42.00 & 41.20 & 29.20 & 49.10 & 63.90 & 43.10 \\
3D-LRF & L+R & 74.80 & 81.20 & 87.20 & 86.10 & 73.80 & 49.50 & 87.90 & 67.20 \\
L4DR & L+R & 78.00 & 77.70 & 80.00 & 88.60 & 79.20 & 60.10 & 78.90 & 51.90 \\
ASF & C+L+R & 80.31 & 79.57 & 89.89 & 90.67 & 80.97 & 80.20 & 80.89 & \textbf{71.71} \\
AW-MoE & L+R & 83.90 & 84.20 & 90.00 & \textbf{95.30} & 84.40 & 72.90 & \textbf{90.20} & 64.00 \\
AW-MoE-LRC & C+L+R & 84.30 & 84.70 & \textbf{91.00} & \textbf{95.30} & 84.00 & 72.90 & 89.60 & 63.70 \\
\midrule
TaskDec Robust (Ours) & C+L+R & \textbf{88.36} & \textbf{87.66} & 90.39 & 90.57 & \textbf{88.90} & \textbf{80.42} & 89.28 & 71.41 \\
\bottomrule
\end{tabular}}
\end{table*}
```

## Notes

- This compact set keeps one original radar baseline, two canonical L+R fusion baselines, the direct ASF baseline, the strongest recent AW-MoE family row, and ours.
- I would not include PointPillars, InterFusion, WCBR, and L4DR-DA3D in the main table unless space is generous. They can stay in an appendix or related-work paragraph.
- The weather table should not claim uniform per-weather dominance. The clean claim is strongest total AP3D@0.3, with clear gains in Normal, Rain, and Sleet; ASF/AW-MoE remain stronger in a few individual weather subsets.

## Sources

- Ours: `results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.md`.
- ASF: `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.md`.
- AW-MoE: `https://arxiv.org/pdf/2603.16261`.
- WCBR scan / backup comparison: `https://arxiv.org/pdf/2604.05405`.
- ASF paper page: `https://www.alphaxiv.org/abs/2503.07029v2`.
