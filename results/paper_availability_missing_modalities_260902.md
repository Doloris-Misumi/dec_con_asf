# K-Radar v1.0 Missing-Modality Availability Table

Date: 2026-09-03 01:10:24

Scope: K-Radar v1.0 narrow RoI, Sedan class, C=front camera, L=LiDAR, R=4D radar. All rows use C+L+R-trained checkpoints evaluated with controlled available sensors at inference. Main protocol is `conf_thr=0.3`.

| Method | Available sensors | APBEV@0.5 | AP3D@0.5 | APBEV@0.3 | AP3D@0.3 | AP3D@0.7 | Source |
|---|---|---:|---:|---:|---:|---:|---|
| TaskDec Robust `model_0` | RLC | 88.10 | 67.50 | 88.84 | 88.36 | 22.02 | `/home/hongsheng/dec_con_asf/logs/exp_260812_232650_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.json` |
| Official ASF v1 ckpt | RLC | 80.33 | 67.19 | 80.78 | 80.31 | 18.85 | `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.json` |
| TaskDec Robust `model_0` | LR | 85.45 | 71.68 | 88.45 | 88.06 | - | `results/full_eval_metric_audit_260821.md recompute` |
| Official ASF v1 ckpt | LR | 85.75 | 71.98 | 86.35 | 86.02 | - | `results/full_eval_metric_audit_260821.md recompute` |
| TaskDec Robust `model_0` | RC | 55.52 | 34.59 | 59.35 | 57.62 | 5.38 | `/home/hongsheng/dec_con_asf/logs/exp_260902_075102_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.json` |
| Official ASF v1 ckpt | RC | 57.27 | 41.87 | 67.49 | 65.69 | 14.59 | `/home/hongsheng/K-Radar-main/logs_avail_eval/availability_official_asf_v1_model10_rc_gpu1_260902.log` |
| TaskDec Robust `model_0` | LC | 86.35 | 72.58 | 87.41 | 86.77 | 21.57 | `/home/hongsheng/dec_con_asf/logs/exp_260902_203611_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.json` |
| Official ASF v1 ckpt | LC | 79.77 | 66.38 | 80.29 | 79.89 | 22.75 | `/home/hongsheng/K-Radar-main/logs_avail_eval/availability_official_asf_v1_model10_lc_gpu2_260902.log` |

## Delta: TaskDec - Official ASF

| Available sensors | Delta APBEV@0.5 | Delta AP3D@0.5 | Delta APBEV@0.3 | Delta AP3D@0.3 |
|---|---:|---:|---:|---:|
| RLC | 7.77 | 0.31 | 8.06 | 8.05 |
| LR | -0.30 | -0.30 | 2.10 | 2.04 |
| RC | -1.75 | -7.28 | -8.14 | -8.07 |
| LC | 6.58 | 6.20 | 7.12 | 6.88 |

## Notes

- `LR` uses the saved-prediction recompute values from the prior audit because the historical conditional-all LR block is inconsistent.
- `RC` is accepted because the metric block was written before the post-run native `free(): invalid pointer` exit.
- `LC` did not start because the launcher stopped after the RC post-run exit.
