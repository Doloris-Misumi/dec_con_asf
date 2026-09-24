# Draft main table: K-Radar v1.0 Sedan

Date: 2026-09-01

Recommended protocol wording:

K-Radar benchmark v1.0, Sedan class, driving-corridor ROI. We report APBEV and AP3D at IoU thresholds 0.5 and 0.3. For ASF, we use the released official checkpoint re-evaluated locally at `conf_thr=0.3`; for other published methods, we keep the numbers as reported in their papers.

## Main paper table

Rows are sorted by AP3D@0.3. `R` denotes 4D Radar.

| Method | Sensors | Venue / source | APBEV@0.5 | AP3D@0.5 | APBEV@0.3 | AP3D@0.3 |
|---|---|---|---:|---:|---:|---:|
| TaskDec Robust (ours) | C+L+R | local `model_0`, `conf_thr=0.3` | **88.10** | **67.50** | **88.84** | **88.36** |
| AW-MoE-LRC | C+L+R | AW-MoE Table III | - | 61.80 | - | 84.30 |
| AW-MoE | L+R | AW-MoE Table II | 84.20 | 61.50 | 88.20 | 83.90 |
| ASF | C+L+R | released ckpt `exp250303`, local `conf_thr=0.3` | 80.33 | 67.19 | 80.78 | 80.31 |
| L4DR-DA3D | L+R | AW-MoE Table II | 78.50 | 61.90 | 80.40 | 79.30 |
| L4DR | L+R | AW-MoE Table II / public log | 77.50 | 53.50 | 79.50 | 78.00 |
| WCBR | L+R | WCBR Table 1 | 71.50 | 43.50 | 81.20 | 76.80 |
| 3D-LRF | L+R | AW-MoE Table II | 73.60 | 45.20 | 84.00 | 74.80 |
| RTNH, LiDAR input | L | AW-MoE Table II | 66.30 | 37.80 | 76.50 | 72.70 |
| InterFusion | L+R | AW-MoE Table II | 66.10 | 41.70 | 69.50 | 65.60 |
| PointPillars | L | WCBR Table 1 | 49.10 | 22.40 | 51.90 | 47.30 |
| RTNH, Radar input | R | AW-MoE Table II | 36.00 | 14.10 | 41.10 | 37.40 |

## Optional recent rows

These are useful to mention in related work or a footnote, but I would not mix them into the main rank unless the exact same 0.3/0.5 protocol is available.

| Method | Sensors | Available K-Radar metric | Value | Note |
|---|---|---:|---:|---|
| FusionBev | L+R | APBEV@0.5 / AP3D@0.5 | 85.90 / 64.90 | Reports K-Radar Sedan at IoU=0.5 only; no AP@0.3 table in the accessible paper text. |
| DDMDGF | L+R | reported gain over L4DR on K-Radar | +4.9 APBEV / +7.3 AP3D | ScienceDirect abstract reports gains, but the full AP table/protocol should be verified before inclusion. |
| DLRFusion | L+R | K-Radar result reported, exact table pending | - | ICCV 2025 paper exists; exact AP table was not accessible from the quick public scan, so keep out until verified. |

## LaTeX draft

```latex
\begin{table}[t]
\centering
\caption{Comparison on the K-Radar v1.0 Sedan benchmark. We report AP (\%) under IoU thresholds 0.5 and 0.3. For ASF, we evaluate the released official checkpoint at \texttt{conf\_thr=0.3}; other literature results are taken from the corresponding papers.}
\label{tab:kradar_v1_main}
\resizebox{\linewidth}{!}{
\begin{tabular}{lcccccc}
\toprule
Method & Sensors & AP$_{\mathrm{BEV}}^{0.5}$ & AP$_{\mathrm{3D}}^{0.5}$ & AP$_{\mathrm{BEV}}^{0.3}$ & AP$_{\mathrm{3D}}^{0.3}$ \\
\midrule
RTNH (Radar) & R & 36.00 & 14.10 & 41.10 & 37.40 \\
PointPillars & L & 49.10 & 22.40 & 51.90 & 47.30 \\
InterFusion & L+R & 66.10 & 41.70 & 69.50 & 65.60 \\
RTNH (LiDAR) & L & 66.30 & 37.80 & 76.50 & 72.70 \\
3D-LRF & L+R & 73.60 & 45.20 & 84.00 & 74.80 \\
WCBR & L+R & 71.50 & 43.50 & 81.20 & 76.80 \\
L4DR & L+R & 77.50 & 53.50 & 79.50 & 78.00 \\
L4DR-DA3D & L+R & 78.50 & 61.90 & 80.40 & 79.30 \\
ASF & C+L+R & 80.33 & 67.19 & 80.78 & 80.31 \\
AW-MoE & L+R & 84.20 & 61.50 & 88.20 & 83.90 \\
AW-MoE-LRC & C+L+R & - & 61.80 & - & 84.30 \\
\midrule
TaskDec Robust (Ours) & C+L+R & \textbf{88.10} & \textbf{67.50} & \textbf{88.84} & \textbf{88.36} \\
\bottomrule
\end{tabular}}
\end{table}
```

## Source notes

- Ours: `results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.md`.
- ASF: `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.md`.
- AW-MoE Table II reports RTNH, InterFusion, 3D-LRF, L4DR, L4DR-DA3D, and AW-MoE total AP at IoU 0.3/0.5 on K-Radar.
- AW-MoE Table III reports AW-MoE-LRC AP3D at IoU 0.3/0.5.
- WCBR Table 1 reports WCBR and related baselines under the 3D-LRF K-Radar protocol.
- FusionBev reports K-Radar AP at IoU=0.5 only in the accessible text.

## URLs checked

- AW-MoE arXiv: `https://arxiv.org/pdf/2603.16261`
- WCBR arXiv: `https://arxiv.org/pdf/2604.05405`
- L4DR AAAI page: `https://ojs.aaai.org/index.php/AAAI/article/view/32397`
- 3D-LRF CVPR page: `https://openaccess.thecvf.com/content/CVPR2024/html/Chae_Towards_Robust_3D_Object_Detection_with_LiDAR_and_4D_Radar_CVPR_2024_paper.html`
- ASF paper page: `https://www.alphaxiv.org/abs/2503.07029v2`
- FusionBev ScienceDirect: `https://www.sciencedirect.com/science/article/pii/S1566253526001193`
- DDMDGF ScienceDirect: `https://www.sciencedirect.com/science/article/pii/S089360802600897X`
- DLRFusion ICCV page: `https://openaccess.thecvf.com/content/ICCV2025/html/Chae_Doppler-Aware_LiDAR-RADAR_Fusion_for_Weather-Robust_3D_Detection_ICCV_2025_paper.html`
