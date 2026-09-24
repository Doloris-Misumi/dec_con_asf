# Full evaluation metric audit

Date: 2026-08-21

This audit checks K-Radar v1.0 full-evaluation runs with 10065 test samples. The main check compares `full_eval_summary.md` / `full_eval_stdout.log` against the `Condition: all` entry in conditional `complete_results.txt` at `conf=0.3`.

Metric order in the tables:

`BEV@0.7 / 3D@0.7 / BEV@0.5 / 3D@0.5 / BEV@0.3 / 3D@0.3`

## Summary-backed full evaluations

| Experiment | Mode | Eval dir | Summary/main value | Conditional all value | Delta 3D@0.3 | Status |
|---|---|---|---:|---:|---:|---|
| `exp_260812_232646_TaskDecControlBalanced_v1_0` | RLC | `epoch_2_total` | 62.67 / 21.89 / 80.38 / 67.59 / 89.01 / 80.37 | 62.69 / 21.90 / 80.38 / 67.57 / 89.01 / 80.37 | +0.00 | OK |
| `exp_260812_232650_TaskDecControlRobust_v1_0` | RLC | `epoch_0_total` | 62.63 / 22.02 / 88.10 / 67.50 / 88.84 / 88.36 | 62.63 / 22.04 / 88.10 / 67.50 / 88.84 / 88.36 | -0.00 | OK |
| `exp_260813_203247_TaskDecControlRobust_v1_0` | RLC | - | 62.63 / 22.03 / 88.09 / 67.50 / 88.84 / 88.36 | - | - | No conditional |
| `exp_260817_000340_TaskDecControlMoreOpenGate_v1_0` | RLC | `epoch_0_total` | 62.30 / 21.33 / 87.77 / 67.21 / 88.62 / 88.08 | 62.30 / 21.31 / 87.77 / 67.20 / 88.62 / 88.09 | +0.01 | OK |
| `exp_260817_000340_TaskDecControlStrongerControl_v1_0` | RLC | `epoch_4_total` | 63.11 / 18.99 / 80.52 / 67.70 / 88.99 / 80.52 | 63.08 / 18.99 / 80.52 / 67.70 / 88.99 / 80.52 | -0.00 | OK |
| `exp_260817_000503_TaskDecControlStrongerControl_v1_0` | RLC | `epoch_2_total` | 62.49 / 22.45 / 80.42 / 68.06 / 89.06 / 80.51 | 62.48 / 22.43 / 80.42 / 68.06 / 89.06 / 80.51 | -0.00 | OK |
| `exp_260817_000507_TaskDecControlMoreOpenGate_v1_0` | RLC | `epoch_2_total` | 62.22 / 22.06 / 80.35 / 67.80 / 89.00 / 88.51 | 62.23 / 22.07 / 80.35 / 67.79 / 89.00 / 88.51 | +0.00 | OK |
| `exp_260818_202519_ASF_v1_0_local_repro` | RLC | `epoch_2_total` | 61.57 / 18.68 / 80.36 / 67.51 / 89.00 / 88.57 | 61.59 / 18.69 / 80.36 / 67.49 / 89.01 / 88.57 | +0.00 | OK |
| `exp_260819_201827_TaskDecControlStable_v1_0` | RLC | `epoch_0_total` | 62.77 / 21.58 / 80.30 / 67.24 / 88.98 / 88.54 | 62.80 / 21.58 / 80.30 / 67.25 / 88.98 / 88.53 | -0.01 | OK |
| `exp_260819_224743_TaskDecControlBalanced_v1_0` | RLC | `epoch_0_total` | 61.89 / 18.73 / 80.02 / 66.99 / 88.63 / 88.18 | 61.89 / 18.73 / 80.02 / 66.99 / 88.63 / 88.18 | +0.00 | OK |
| `exp_260819_231927_TaskDecControlRobust_v1_0_eval_LR` | LR | `epoch_0_total` | 62.30 / 18.22 / 80.09 / 66.87 / 88.87 / 88.37 | 62.30 / 18.22 / 80.09 / 66.88 / 88.87 / 80.30 | -8.07 | Mismatch |

## Corrected LR checks

The only summary-backed mismatch is the LR availability run. Recomputing from the saved prediction files gives:

| Experiment | Source | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---|---|---:|---:|---:|---:|
| Robust v1 `model_0` LR | `all/preds` + `all/gts` recompute | 85.45 | 71.68 | 88.45 | 88.06 |
| Official ASF v1.0 LR | `all/preds` + `all/gts` recompute | 85.75 | 71.98 | 86.35 | 86.02 |

So the `80.30/80.31` LR conditional-all 3D@0.3 entries should not be used as final LR all metrics. They conflict with both first-stage stdout and direct recomputation from saved prediction files. The robust LR result is still in the 88-point range; under strict same-file recomputation the LR advantage over official LR is about +2 AP at BEV@0.3 and 3D@0.3.

## Complete-only full evaluations

These runs have 10065-sample `complete_results.txt` but no paired `full_eval_summary.md`, so the same summary-vs-conditional consistency check cannot be applied.

| Experiment | Eval dir | Complete value | Status |
|---|---|---:|---|
| `exp_260810_221258_TaskDecControlRobust_v1_0` | `none` | 62.34 / 22.32 / 80.43 / 67.21 / 80.87 / 80.42 | complete-only |
| `exp_260810_221300_TaskDecControlBalanced_v1_0` | `none` | 63.39 / 19.65 / 80.48 / 67.45 / 80.93 / 80.59 | complete-only |
| `exp_260813_225556_TaskDecControlMoreOpenGate_v1_0` | `none` | 61.76 / 19.38 / 80.45 / 67.77 / 89.10 / 80.58 | complete-only |
| `exp_260813_225557_TaskDecControlStrongerControl_v1_0` | `none` | 62.97 / 22.78 / 80.46 / 67.86 / 89.00 / 80.52 | complete-only |
| `exp_260817_212526_TaskDecControlStable_v1_0` | `none` | 56.85 / 4.44 / 83.61 / 40.82 / 86.74 / 81.26 | complete-only |
| `exp_260817_212746_TaskDecControlKVOnlyStable_v1_0` | `none` | 29.46 / 3.24 / 72.38 / 35.44 / 84.55 / 78.27 | complete-only |
| `exp_260814_212832_ASF_v1_0_local_repro` | `none` | 63.11 / 22.95 / 80.45 / 67.72 / 89.15 / 80.45 | complete-only |
| `exp_260820_203153_ASF_v1_0_local_repro` | `none` | 62.85 / 18.88 / 80.33 / 67.21 / 80.78 / 80.31 | complete-only; LR conditional all is unsafe per recompute |

## Conclusion

- No summary-backed RLC full evaluation shows the LR-style mismatch. The RLC main candidates are internally consistent.
- The mismatch is localized to LR availability conditional-all metrics. Use `full_eval_summary.md` for the historical LR robust row, or use the recomputed prediction-file values for a stricter same-file LR comparison.
- Weather breakdown for RLC remains usable. LR weather/all values should be regenerated or recomputed from prediction files before being used in the paper.
