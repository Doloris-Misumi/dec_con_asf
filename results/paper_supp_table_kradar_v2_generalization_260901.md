# K-Radar v2.0 supplementary generalization table draft

Date: 2026-09-01

2026-09-12 weather layout update: following the author's preference for L4DR Table 10, a [full seven-weather table](paper_kradar_v2_weather_l4dr_table10_260912.md) now provides both AP3D@0.3 and @0.5 in two class-grouped panels. This is the current expanded table candidate; the compact Total table below remains a space-saving alternative. The new table includes every weather condition, rather than only the earlier selected-weather excerpt.

2026-09-12 latest decision: use **DecControlled Strong (ours)** as the selected Dec-family variant. The recommended table is now the two-class **Total AP3D@0.3 and @0.5** comparison, not the selected-weather excerpt below. See [the complete Strong–ASF comparison](paper_kradar_v2_decstrong_asf_comparison_260912.md), [current LaTeX table](paper_kradar_v2_decstrong_asf_comparison_260912.tex), and [v2 literature results with protocol checks](kradar_v2_literature_candidates_260912.md). Keep a brief footnote identifying the absence of task-context modulation. Missing-modality robustness remains a v1 analysis.

2026-09-12 recheck: see [the complete v2.0 audit](taskdec_v2_existing_results_recheck_260912.md) for eight existing full evaluations, per-class Total metrics, all weather subsets, and exact deltas against the archived official ASF results. This draft only covers the early DecControlled Strong variant; it is not a complete inventory. The 08-08 TaskDec Robust run also contains task context and improves two-class mean AP3D@0.5 by 1.76 points, while reducing AP3D@0.3 by 1.95 points. Keep its identity and tradeoffs separate from the 08-21 final run and the rows below.

Model identity clarification (2026-09-10; naming updated 2026-09-12): all `Ours` rows below refer to the `DecControlledA2Fusion` variant (`DecControlledASFStrong_final`), which does not contain the task-context branch of the full TaskDec model. Label these rows `DecControlled Strong (ours)` in the manuscript and identify it as a Dec-family variant without task-context modulation. These experiments support extension of the decoupled-control approach; they are not results of the full v1.0 TaskDec architecture transferred unchanged. A brief main-text note and a table footnote are sufficient; retain the configuration details in the appendix.

Recommended wording:

K-Radar benchmark v2.0, wide ROI, Sedan and Bus-or-Truck classes. All results below use C+L+R inputs and `conf_thr=0.3`. ASF is the released official checkpoint re-evaluated locally with the same evaluation pipeline. Ove., L.s., and H.s. denote Overcast, Light snow, and Heavy snow.

## Historical weather excerpt: selected adverse weather, AP3D@IoU=0.5

This historical excerpt is retained for supplementary reference. The current recommendation is the full Total table linked above, with all weather results available in the appendix. `Sel. Avg.` averages Ove., Rain, L.s., and H.s.; it excludes Total and does not represent all adverse weather conditions.

| Method | Class | Total | Ove. | Rain | L.s. | H.s. | Sel. Avg. |
|---|---|---:|---:|---:|---:|---:|---:|
| ASF | Sedan | 52.09 | 53.38 | 46.85 | 59.25 | 49.52 | 52.25 |
| ASF | Bus/Truck | 31.06 | 47.04 | 2.48 | 70.81 | 32.55 | 38.22 |
| Ours | Sedan | **52.14** | **59.62** | **48.30** | **60.75** | **50.49** | **54.79** |
| Ours | Bus/Truck | **33.97** | **49.65** | **5.05** | **75.09** | **39.37** | **42.29** |

Direct deltas over ASF:

| Class | Total | Ove. | Rain | L.s. | H.s. | Sel. Avg. |
|---|---:|---:|---:|---:|---:|---:|
| Sedan | +0.05 | +6.25 | +1.44 | +1.49 | +0.96 | +2.54 |
| Bus/Truck | +2.91 | +2.61 | +2.57 | +4.28 | +6.82 | +4.07 |

## Optional ASF-style table: rainy/snowy AP3D@IoU=0.3

ASF's public K-Radar v2.0 report mainly displays AP3D/APBEV at IoU=0.3 by weather. If we want a more ASF-like metric, this smaller rainy/snowy table is usable, but the AP3D@0.5 table above is stronger.

| Method | Class | Total | Rain | L.s. | H.s. | Sel. Avg. |
|---|---|---:|---:|---:|---:|---:|
| ASF | Sedan | 74.98 | 66.37 | 88.24 | 63.61 | 72.74 |
| ASF | Bus/Truck | 58.13 | 7.89 | 88.26 | 68.20 | 54.79 |
| Ours | Sedan | 74.58 | **68.11** | **89.56** | 63.57 | **73.75** |
| Ours | Bus/Truck | **59.24** | **10.08** | **89.56** | **72.34** | **57.33** |

## Full Total metrics check

This table is useful for internal auditing or appendix notes. It shows why the v2.0 claim should be phrased as transfer/generalization and adverse-weather robustness, not as a broad v2.0 SOTA claim.

| Method | Class | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---|---|---:|---:|---:|---:|---:|---:|
| ASF | Sedan | 43.21 | 11.85 | 71.70 | 52.09 | 77.85 | 74.98 |
| ASF | Bus/Truck | 20.85 | 7.93 | 53.21 | 31.06 | 67.85 | 58.13 |
| Ours | Sedan | 44.26 | 12.31 | 71.27 | 52.14 | 77.32 | 74.58 |
| Ours | Bus/Truck | 23.13 | 9.92 | 50.59 | 33.97 | 65.14 | 59.24 |

## Suggested paper text

We further evaluate DecControlled Strong, a variant of our Dec family without task-context modulation, on K-Radar v2.0 with a wider ROI and the additional Bus-or-Truck category. Under the C+L+R setting with a score threshold of 0.3, this variant improves the arithmetic mean of the two class AP3D scores over the official ASF checkpoint by 0.36 and 1.48 points at IoU thresholds of 0.3 and 0.5, respectively. These results support the applicability of decoupled control to the expanded benchmark setting. Full BEV metrics and results for all weather conditions are reported in the appendix.

Conservative claim:

The v2.0 experiment is best positioned as a generalization/robustness supplement. It should not be the main SOTA claim, because full Total AP3D@0.3 for Sedan is slightly below ASF (-0.39), and BEV@0.3 is lower for both classes. The clean headline is: "On K-Radar v2.0, the proposed controller improves strict 3D localization under adverse weather, with +2.54/+4.07 selected-weather AP3D@0.5 gains for Sedan/Bus-or-Truck over the official ASF checkpoint at conf=0.3."

## LaTeX draft

```latex
\begin{table}[t]
\centering
\caption{Generalization on K-Radar v2.0 under selected adverse weather conditions. We report AP$_{\mathrm{3D}}$ at IoU=0.5 with C+L+R inputs and \texttt{conf\_thr=0.3}. ASF is evaluated from the released official checkpoint using the same evaluation pipeline. Ove., L.s., and H.s. denote Overcast, Light snow, and Heavy snow. Sel. Avg. averages Ove., Rain, L.s., and H.s.}
\label{tab:kradar_v2_generalization_weather}
\resizebox{\linewidth}{!}{
\begin{tabular}{llrrrrrr}
\toprule
Method & Class & Total & Ove. & Rain & L.s. & H.s. & Sel. Avg. \\
\midrule
ASF & Sedan & 52.09 & 53.38 & 46.85 & 59.25 & 49.52 & 52.25 \\
ASF & Bus/Truck & 31.06 & 47.04 & 2.48 & 70.81 & 32.55 & 38.22 \\
\midrule
Ours & Sedan & \textbf{52.14} & \textbf{59.62} & \textbf{48.30} & \textbf{60.75} & \textbf{50.49} & \textbf{54.79} \\
Ours & Bus/Truck & \textbf{33.97} & \textbf{49.65} & \textbf{5.05} & \textbf{75.09} & \textbf{39.37} & \textbf{42.29} \\
\bottomrule
\end{tabular}}
\end{table}
```

## Notes

- Use `DecControlledASFStrong_final` for this v2.0 table, not the `model_10` subset sweep. The subset sweep evaluates only 1000 validation samples, so it is not comparable to ASF full validation.
- Sleet is intentionally left out of the compact AP3D@0.5 table: Sedan improves by +5.08, but Bus/Truck is slightly lower (-0.35). If space allows, an expanded appendix can include all weather columns.
- Fog has zero Bus/Truck AP for both methods in the local official ASF and our result files, so it is not very informative for the two-class v2.0 comparison.

## Sources

- Ours: `/home/hongsheng/dec_con_asf/results/exp_260806_000825_DecControlledASFStrong_final/summary_conf0.3.md`
- ASF official checkpoint re-eval: `/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/summary_conf0.3.md`
- ASF public K-Radar v2.0 reporting style: `https://github.com/kaist-avelab/K-Radar/blob/main/docs/sensor_fusion.md`
- ASF NeurIPS paper page: `https://papers.nips.cc/paper_files/paper/2025/hash/80bd5c815cdb033ac23eb27605adaaba-Abstract-Conference.html`
