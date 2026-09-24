# TaskDec v1.0 component ablation at conf=0.3

Date: 2026-09-01

Scope: K-Radar v1.0 Sedan, C+L+R, `conf_thr=0.3`.

## Selection protocol clarification (2026-09-10)

The author clarified that the ablation variants also underwent a 1,000-sample preliminary evaluation before the best comparison results were selected. The different checkpoint indices (`model_0` for the full model and `model_9` in the ablation rows) therefore do not by themselves indicate inconsistent selection. This clarification records the author's experimental procedure; the exact sample IDs, selection metric, and candidate range have not been individually re-audited here and should be documented for reproducibility.

Suggested setup sentence: “The full model and ablated variants undergo preliminary evaluation on 1,000 samples for model selection, followed by full-set evaluation of the selected models.” Specify the actual subset source and selection criterion in the final methods description.

## Selected results from the completed ablation runs

| Variant | Checkpoint | Key change | BEV@0.7 | BEV@0.5 | BEV@0.3 | 3D@0.7 | 3D@0.5 | 3D@0.3 | Delta 3D@0.3 vs full |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Full TaskDec Robust | `model_0` | full model | 62.63 | 88.10 | 88.84 | 22.04 | 67.50 | 88.36 | 0.00 |
| w/o sensor reliability | `model_9` | `DEC_CONTROL_STRENGTH=0.0` | 61.36 | 79.91 | 80.38 | 11.08 | 64.38 | 79.62 | -8.74 |
| w/o task context | `model_9` | no class loss, no query/output context injection | 54.91 | 79.96 | 80.68 | 17.10 | 66.23 | 80.14 | -8.22 |
| w/o decoupling supervision | `model_9` | set `PATCH_DEC_LAMBDA_DECOUPLE`, `PATCH_DEC_LAMBDA_COMMON`, and `PATCH_DEC_LAMBDA_UNIQUE` to `0.0` | 55.71 | 80.04 | 80.65 | 16.49 | 66.16 | 80.23 | -8.13 |
| w/o foreground gate | `model_9` | set `DEC_CONTROL_GATE_MIN=1.0`, `DEC_CONTROL_GATE_MAX=1.0`, and `DEC_CONTROL_GATE_LOSS_WEIGHT=0.0` | 55.49 | 80.12 | 80.65 | 19.41 | 64.80 | 80.00 | -8.36 |

## Source files

| Variant | Config | Experiment directory | Result file |
|---|---|---|---|
| Full TaskDec Robust | `configs/ASF_task_dec_controlled_robust_v1_0.yml` | `logs/exp_260812_232650_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16` | `results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.md` |
| w/o sensor reliability | `configs/ASF_task_dec_controlled_robust_v1_0_wo_sensor_reliability.yml` | `logs/exp_260831_003901_TaskDecAblWoSensorReliability_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16` | `logs/exp_260831_003901_TaskDecAblWoSensorReliability_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt` |
| w/o task context | `configs/ASF_task_dec_controlled_robust_v1_0_wo_task_context.yml` | `logs/exp_260831_003901_TaskDecAblWoTaskContext_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16` | `logs/exp_260831_003901_TaskDecAblWoTaskContext_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt` |
| w/o decoupling supervision | `configs/ASF_task_dec_controlled_robust_v1_0_wo_decoupling_supervision.yml` | `logs/exp_260901_075157_TaskDecAblWoDecouplingSupervision_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16` | `logs/exp_260901_075157_TaskDecAblWoDecouplingSupervision_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt` |
| w/o foreground gate | `configs/ASF_task_dec_controlled_robust_v1_0_wo_foreground_gate.yml` | `logs/exp_260901_075156_TaskDecAblWoForegroundGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16` | `logs/exp_260901_075156_TaskDecAblWoForegroundGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3/complete_results.txt` |

## Interpretation

All four completed ablations substantially reduce loose-IoU 3D detection performance, dropping `AP3D@0.3` from 88.36 to roughly 79.6-80.2. This supports the claim that TaskDec's reliability control, task-context modulation, decoupling supervision, and foreground-aware gate are all functional contributors, not merely auxiliary heads.
