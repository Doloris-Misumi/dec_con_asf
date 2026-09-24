# K-Radar v1.0 Results Ranked by `conf=0.0`

Generated: 2026-08-18

Scope: Sedan, K-Radar v1.0/narrow RoI where available. The main table uses full validation results and ranks by `3D@0.3` under `conf=0.0`, because this was the metric most previous `conf=0.3` discussions focused on. `BEV@0.5` and `3D@0.5` are included because they are more discriminative and align closely with ASF Table 1.

Protocol update on 2026-08-19: this file is now best treated as a `conf=0.0` appendix/protocol-sensitivity table. For a paper-facing comparison against RTNH, 3D-LRF, L4DR, and the released ASF checkpoint under a consistent confidence-filtered protocol, use `results/v1_conf0_3_main_protocol_260819.md`.

## Full Validation Ranking

| Rank | Method / checkpoint | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | 3D@0.3 vs ASF paper baseline |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | TaskDec Robust v1 best-subset `model_0` | 62.63 | 22.02 | 87.18 | 72.83 | 88.84 | 88.06 | +0.66 |
| 2 | ASF local repro `model_2` baseline | 61.57 | 18.68 | 87.41 | 72.96 | 88.80 | 87.96 | +0.56 |
| 3 | TaskDec StrongerControl `model_2` | 63.11 | 18.99 | 87.35 | 73.35 | 88.77 | 87.78 | +0.38 |
| 4 | TaskDec MoreOpenGate `model_2` | 62.22 | 22.06 | 87.24 | 73.46 | 88.85 | 87.77 | +0.37 |
| 5 | TaskDec Balanced v1 final `model_10` | 63.39 | 19.65 | 87.33 | 73.39 | 88.73 | 87.76 | +0.36 |
| 6 | TaskDec Balanced v1 best-subset `model_2` | 62.67 | 21.89 | 87.21 | 73.13 | 88.73 | 87.73 | +0.33 |
| 7 | TaskDec StrongerControl `model_4` | 62.49 | 22.45 | 87.16 | 73.78 | 88.81 | 87.72 | +0.32 |
| 8 | TaskDec MoreOpenGate `model_0` | 62.30 | 21.33 | 86.40 | 72.39 | 88.62 | 87.59 | +0.19 |
| 9 | Official ASF v1 alternative checkpoint `exp250219` | 63.98 | 19.96 | 87.17 | 73.58 | 88.59 | 87.42 | +0.02 |
| 10 | ASF paper Table 1 C+L+R reported | - | - | 87.20 | 73.60 | 88.60 | 87.40 | +0.00 |
| 11 | Official ASF v1 paper-aligned baseline `exp250303` | 62.85 | 18.85 | 86.97 | 72.95 | 88.59 | 87.34 | -0.06 |
| 12 | TaskDec Robust v1 final `model_10` | 62.34 | 22.32 | 86.93 | 72.83 | 88.57 | 87.21 | -0.19 |

Baseline reference for the delta column is the ASF paper Table 1 C+L+R reported value at `3D@0.3 = 87.40`. The paper reports only IoU 0.3/0.5, so IoU 0.7 is left blank for the paper row. The reproduced ASF rows are kept as implementation sanity checks, but paper comparisons should use the paper-reported row.

## Same Full Results Sorted by `3D@0.5`

| Rank | Method / checkpoint | 3D@0.5 | BEV@0.5 | 3D@0.3 |
|---:|---|---:|---:|---:|
| 1 | TaskDec StrongerControl `model_4` | 73.78 | 87.16 | 87.72 |
| 2 | ASF paper Table 1 C+L+R reported | 73.60 | 87.20 | 87.40 |
| 3 | Official ASF v1 alternative checkpoint `exp250219` | 73.58 | 87.17 | 87.42 |
| 4 | TaskDec MoreOpenGate `model_2` | 73.46 | 87.24 | 87.77 |
| 5 | TaskDec Balanced v1 final `model_10` | 73.39 | 87.33 | 87.76 |
| 6 | TaskDec StrongerControl `model_2` | 73.35 | 87.35 | 87.78 |
| 7 | TaskDec Balanced v1 best-subset `model_2` | 73.13 | 87.21 | 87.73 |
| 8 | ASF local repro `model_2` baseline | 72.96 | 87.41 | 87.96 |
| 9 | Official ASF v1 paper-aligned baseline `exp250303` | 72.95 | 86.97 | 87.34 |
| 10 | TaskDec Robust v1 best-subset `model_0` | 72.83 | 87.18 | 88.06 |
| 11 | TaskDec Robust v1 final `model_10` | 72.83 | 86.93 | 87.21 |
| 12 | TaskDec MoreOpenGate `model_0` | 72.39 | 86.40 | 87.59 |

Takeaway: if the paper table is interpreted through the more discriminative IoU 0.5 metrics, `StrongerControl model_4` is slightly above the paper ASF C+L+R row, while `MoreOpenGate model_2`, `Balanced model_10`, and `StrongerControl model_2` are close behind. `Robust model_0` is best on `3D@0.3`, but not on `3D@0.5`.

## Current 1000-Sample Subset Ranking

These rows are for checkpoint selection only and should not be mixed directly with full validation.

| Run | Top checkpoint by `conf=0.0 3D@0.3` | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---|---|---:|---:|---:|---:|---:|---:|
| ASF local repro baseline | `model_2` | 62.18 | 19.39 | 88.02 | 73.61 | 89.30 | 88.45 |
| TaskDec Stable current GPU2 run | `model_0` | 62.69 | 17.95 | 87.61 | 73.32 | 89.22 | 88.45 |
| TaskDec Robust v1 subset sweep | `model_0` | 62.29 | 19.25 | 88.05 | 72.99 | 89.20 | 88.44 |
| TaskDec Balanced v1 subset sweep | `model_2` | 62.89 | 22.11 | 88.07 | 73.95 | 89.20 | 88.40 |

## Archived / Lower-Score Full Runs

These are kept for completeness, but they are older or less directly useful for the current v1.0 paper comparison.

| Method / run | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| Official ASF v2/RLC result | 44.97 | 11.61 | 74.46 | 52.94 | 82.49 | 79.26 |
| DecControlledASF Strong final | 44.72 | 12.10 | 74.06 | 53.09 | 81.88 | 78.91 |
| DecControlledASF Gentle final | 43.77 | 11.79 | 74.00 | 52.58 | 81.99 | 78.89 |
| TaskDecControlRobust old final | 45.59 | 12.10 | 74.08 | 53.17 | 80.56 | 77.63 |
| K-Radar-main A2FUSION local old run | 43.50 | 11.59 | 73.95 | 52.47 | 81.93 | 77.45 |
| TaskDecControlBalanced old final | 44.09 | 11.67 | 73.81 | 52.19 | 80.42 | 77.39 |

## Source Files

- ASF paper Table 1 C+L+R reported baseline: arXiv `2503.07029v2`, Table 1.
- Official ASF v1 paper-aligned baseline: `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.0.json`
- Official ASF v1 alternative checkpoint: `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250219/summary_conf0.0.json`
- ASF local repro `model_2`: `/home/hongsheng/dec_con_asf/logs/exp_260818_202519_ASF_v1_0_local_repro/full_eval_summary.json`
- Recent MoreOpenGate/StrongerControl full evals: `/home/hongsheng/dec_con_asf/logs/exp_260817_000*/full_eval_summary.json`
- Stable subset sweep: `/home/hongsheng/dec_con_asf/logs/exp_260818_203815_TaskDecControlStable_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/subset_eval_summary.json`
- Earlier Balanced/Robust full summaries: `/home/hongsheng/dec_con_asf/results/*/summary_conf0.0.json`
