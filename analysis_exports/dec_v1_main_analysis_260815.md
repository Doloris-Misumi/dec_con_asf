# Dec v1 Main Experiment Export and Analysis

Date: 2026-08-15

Scope:
- MoreOpenGate main training: `logs/exp_260813_225556_TaskDecControlMoreOpenGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
- StrongerControl main training: `logs/exp_260813_225557_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
- Subset evaluation: fixed 1000 validation frames, `conf=0.3`, `num_workers=0`
- Exported CSV: `analysis_exports/dec_v1_main_subset_results_260815.csv`

Note: the subset script table keeps bus columns, but these runs only produced `sed` metrics. Ranking below uses `sed 3D@0.3`.

## Completion Check

- GPU2/GPU3 main training finished; both final logs reached full validation output.
- The original GPU1 chained subset job completed MoreOpenGate epoch 9/10, then aborted with `free(): invalid pointer` before StrongerControl.
- Missing StrongerControl subset runs were re-run on GPU2/GPU3:
  - epochs 0-5: `logs/exp_260815_115940_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
  - epochs 6-10: `logs/exp_260815_120021_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
- Both re-runs wrote `subset_eval_summary.json/md`; the final exit code was 134 from the known post-write `free(): invalid pointer`.

## MoreOpenGate Subset

| epoch | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 63.16 | 17.45 | 88.11 | 74.79 | 89.01 | 88.26 |
| 1 | 49.64 | 10.51 | 87.52 | 64.23 | 89.11 | 88.33 |
| 2 | 61.12 | 18.02 | 88.38 | 68.06 | 89.14 | 88.67 |
| 3 | 61.99 | 10.17 | 80.49 | 65.53 | 89.31 | 88.55 |
| 4 | 61.82 | 19.71 | 80.54 | 68.40 | 89.13 | 88.56 |
| 5 | 55.12 | 19.60 | 80.47 | 65.15 | 81.07 | 80.48 |
| 6 | 60.91 | 17.41 | 80.41 | 67.69 | 89.13 | 88.61 |
| 7 | 61.88 | 16.95 | 87.49 | 66.13 | 88.99 | 87.99 |
| 8 | 62.29 | 19.04 | 80.46 | 68.06 | 89.28 | 80.63 |
| 9 | 55.71 | 11.39 | 80.00 | 64.30 | 88.77 | 79.99 |
| 10 | 61.58 | 19.05 | 80.41 | 68.14 | 89.26 | 88.75 |

Top by 3D@0.3: epoch 10 = 88.75, epoch 2 = 88.67, epoch 6 = 88.61, epoch 4 = 88.56, epoch 3 = 88.55.

Epoch 10 full validation, `condition=all`, `conf=0.3`:

| BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---:|---:|---:|---:|---:|---:|
| 61.76 | 19.38 | 80.45 | 67.77 | 89.10 | 80.58 |

## StrongerControl Subset

| epoch | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 62.88 | 22.24 | 80.30 | 67.52 | 88.87 | 88.34 |
| 1 | 51.68 | 9.78 | 87.70 | 63.89 | 89.14 | 88.00 |
| 2 | 62.46 | 22.30 | 80.54 | 68.35 | 89.18 | 88.67 |
| 3 | 61.09 | 15.82 | 80.60 | 64.94 | 89.25 | 80.56 |
| 4 | 62.50 | 22.21 | 80.62 | 68.30 | 89.18 | 88.52 |
| 5 | 53.73 | 11.29 | 80.29 | 62.67 | 88.98 | 80.33 |
| 6 | 62.55 | 22.75 | 80.55 | 68.06 | 89.21 | 80.61 |
| 7 | 60.65 | 20.90 | 87.38 | 65.78 | 88.83 | 87.52 |
| 8 | 61.99 | 22.53 | 80.43 | 68.01 | 89.24 | 80.52 |
| 9 | 63.21 | 21.83 | 80.26 | 67.65 | 88.44 | 80.18 |
| 10 | 62.77 | 21.93 | 80.58 | 68.23 | 89.17 | 80.57 |

Top by 3D@0.3: epoch 2 = 88.67, epoch 4 = 88.52, epoch 0 = 88.34, epoch 1 = 88.00, epoch 7 = 87.52.

Epoch 10 full validation, `condition=all`, `conf=0.3`:

| BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---:|---:|---:|---:|---:|---:|
| 62.97 | 22.78 | 80.46 | 67.86 | 89.00 | 80.52 |

## Interpretation

The late-epoch drop is real at fixed `conf=0.3`, but it is not monotonic. Both variants have alternating high and low checkpoints:

- MoreOpenGate high: 0, 1, 2, 3, 4, 6, 10; low: 5, 8, 9.
- StrongerControl high: 0, 1, 2, 4, 7; low: 3, 5, 6, 8, 9, 10.

The drop is mainly in `3D@0.3`, while `BEV@0.3` often stays near 89. This suggests the failure mode is not simply missing detections; it is more likely score-threshold interaction plus 3D localization/height-depth quality under the fixed `conf=0.3` cut.

StrongerControl improves the high-IoU 3D numbers in many epochs: its `3D@0.7` is often around 22, while MoreOpenGate is usually around 17-20. But that does not guarantee stable `3D@0.3` after thresholding.

## Full-Test Recommendation

Recommended new full validation order:

1. StrongerControl `model_2.pt`
   - Best StrongerControl subset checkpoint: `3D@0.3=88.67`.
   - Also has strong `3D@0.7=22.30` and `3D@0.5=68.35`.
   - This is the best single candidate for a method result.

2. MoreOpenGate `model_2.pt`
   - Best early MoreOpenGate checkpoint: `3D@0.3=88.67`.
   - Useful to compare against StrongerControl epoch 2 under the same full split.

3. StrongerControl `model_4.pt`
   - Second StrongerControl high point: `3D@0.3=88.52`.
   - Similar high-IoU behavior to epoch 2, so it is a good stability check if compute allows.

Already full-validated final checkpoints:

- MoreOpenGate `model_10.pt`: full `3D@0.3=80.58`.
- StrongerControl `model_10.pt`: full `3D@0.3=80.52`.

So if compute is limited, do not spend the next full test on epoch 10 again. Use epoch 2 first.
