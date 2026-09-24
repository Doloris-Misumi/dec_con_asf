# TaskDec v1.0 control strength comparison

Date: 2026-09-04

Scope: K-Radar v1.0 Sedan, C+L+R, full test unless otherwise noted.

## Full-test results at conf=0.3

| Variant | Checkpoint | Note | BEV@0.7 | BEV@0.5 | BEV@0.3 | 3D@0.7 | 3D@0.5 | 3D@0.3 | Delta 3D@0.3 vs previous best |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Previous best TaskDec Robust | `model_0` | selected main model | 62.63 | 88.10 | 88.84 | 22.02 | 67.50 | 88.36 | 0.00 |
| TaskDec ControlStrength=0.5 | `model_0` | hyperparam ablation | 62.26 | 80.10 | 88.77 | 19.36 | 66.77 | 88.19 | -0.17 |
| TaskDec ControlStrength=1.0 | `model_0` | hyperparam ablation | 62.82 | 80.29 | 88.79 | 19.97 | 67.31 | 88.33 | -0.03 |
| w/o sensor reliability / ControlStrength=0.0 | `model_9` | component ablation | 61.36 | 79.91 | 80.38 | 11.08 | 64.38 | 79.62 | -8.74 |

## Subset-only reference

The original TaskDec Robust `model_9` was found only in a 1000-sample subset evaluation, not a full C+L+R test run:

| Variant | Checkpoint | Protocol | BEV@0.3 | 3D@0.3 |
|---|---|---|---:|---:|
| Original TaskDec Robust | `model_9` | 1000-sample subset, conf=0.3 | 80.94 | 80.20 |

## Source files

| Row | Source |
|---|---|
| Previous best TaskDec Robust | `logs/exp_260812_232650_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.md` |
| ControlStrength=0.5 | `logs/exp_260904_013929_TaskDecControlStrength05_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.md` |
| ControlStrength=1.0 | `logs/exp_260904_013931_TaskDecControlStrength10_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.md` |
| ControlStrength=0.0 / w/o sensor reliability | `results/taskdec_v1_component_ablation_conf0_3_260901.md` |
| Original Robust model_9 subset | `logs/exp_260812_211952_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/subset_eval_summary.md` |

## Takeaway

The two stronger control ablations are close to the previous best but do not exceed it on the full test set. ControlStrength=1.0 is nearly tied with the previous best on AP3D@0.3 (-0.03), while ControlStrength=0.5 is slightly lower (-0.17). Disabling reliability control remains much worse, supporting the importance of the controller.
