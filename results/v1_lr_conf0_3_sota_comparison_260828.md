# K-Radar v1.0 R+L conf=0.3 comparison

Date: 2026-08-28

Scope: K-Radar v1.0 narrow RoI, Sedan class, AP in percent. R means 4D radar, L means LiDAR. The main comparison is at `conf_thr=0.3`.

Important protocol note: the local TaskDec/ASF LR rows are availability-control evaluations from C+L+R-trained ASF-family checkpoints, with only LiDAR and 4D radar available at inference (`infer_mode=lr`, `avail_feats=['spatial_features_2d', 'bev_feat']`). Literature rows are kept as reported by their papers. Some recent papers label the result as L+4DR while still using image/weather condition inputs for routing; those are marked in the notes.

## Main table

Rows are sorted by AP3D@0.3 when that metric is available.

| Rank | Method | Reported / used sensors | Training note | APBEV@0.3 | AP3D@0.3 | APBEV@0.5 | AP3D@0.5 | Protocol note |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | TaskDec Robust `model_0` LR, ours | Inference L+R | C+L+R checkpoint, LR availability eval | 88.45 | 88.06 | 85.45 | 71.68 | Local `conf=0.3`; recomputed from saved `all/preds` + `all/gts` |
| 2 | Official ASF v1.0 ckpt LR | Inference L+R | C+L+R checkpoint, LR availability eval | 86.35 | 86.02 | 85.75 | 71.98 | Local `conf=0.3`; same recompute protocol as ours |
| 3 | AW-MoE | Paper: L+4DR | L+4DR detector; image-guided weather routing in method | 88.20 | 83.90 | 84.20 | 61.50 | AW-MoE Table II |
| 4 | L4DR-DA3D | Paper: L+4DR | L+4DR | 80.40 | 79.30 | 78.50 | 61.90 | AW-MoE Table II |
| 5 | L4DR | L+4DR | L+4DR | 79.49 | 77.96 | 77.54 | 53.50 | Official public log, `conf=0.3` |
| 6 | WCBR | Paper: 4DR+L | Branch-routing method; method text uses visual/semantic condition token | 81.20 | 76.80 | 71.50 | 43.50 | WCBR Table 1 |
| 7 | 3D-LRF | L+4DR | L+4DR | 84.00 | 74.80 | 73.60 | 45.20 | AW-MoE Table II, stronger published baseline |
| 8 | InterFusion | L+4DR | L+4DR | 69.50 | 65.60 | 66.10 | 41.70 | AW-MoE reproduced result |

## Direct deltas

| Comparison | Delta APBEV@0.3 | Delta AP3D@0.3 | Delta APBEV@0.5 | Delta AP3D@0.5 |
|---|---:|---:|---:|---:|
| Ours LR vs official ASF LR, same availability eval | +2.10 | +2.04 | -0.30 | -0.30 |
| Ours LR vs AW-MoE | +0.25 | +4.16 | +1.25 | +10.18 |
| Ours LR vs L4DR-DA3D | +8.05 | +8.76 | +6.95 | +9.78 |
| Ours LR vs L4DR public log | +8.96 | +10.10 | +7.91 | +18.18 |
| Ours LR vs WCBR | +7.25 | +11.26 | +13.95 | +28.18 |

## Recommended wording

Use this claim for the R+L setting:

> Under the K-Radar v1.0 Sedan `conf_thr=0.3` protocol, with only LiDAR and 4D radar available at inference, TaskDec Robust `model_0` achieves the strongest AP3D@IoU=0.3 among R+L and R+L-compatible methods. Compared with the official ASF checkpoint under the same LR availability evaluation, it improves AP3D@0.3 by 2.04 points.

Avoid this stronger claim unless a pure LR-trained TaskDec run is regenerated:

> pure R+L-trained SOTA.

The current strongest local R+L row is better described as an R+L inference / sensor-availability result, because the checkpoint was trained with C+L+R and evaluated with camera unavailable.

## Local evidence

| Item | Evidence |
|---|---|
| Ours LR launcher | `logs/launcher/full_robust_v1_model0_lr_gpu2_260819.log` |
| Ours LR checkpoint | `logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt` |
| Ours LR eval dir | `logs/exp_260819_231927_TaskDecControlRobust_v1_0_eval_LR_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/` |
| Ours LR first-stage summary | `full_eval_summary.md` reports APBEV@0.3 88.87 and AP3D@0.3 88.37 at `conf=0.3` |
| Corrected LR audit | `results/full_eval_metric_audit_260821.md` recommends using saved-pred recompute values: ours 88.45/88.06, ASF 86.35/86.02 at APBEV/AP3D@0.3 |
| Official ASF LR local eval | `/home/hongsheng/K-Radar-main/logs/exp_260820_203153_ASF_v1_0_local_repro/avail_eval_meta.txt` confirms `infer_mode: lr` and `avail_feats: ['spatial_features_2d', 'bev_feat']` |

The stale conditional `complete_results.txt` LR all entry around AP3D@0.3 80.30/80.31 should not be used as the final LR all metric. It conflicts with the first-stage summary and the saved-pred recompute audit.

## Recent R+L context not in the main rank

| Method | Dataset / protocol note | Available comparable value | How to use |
|---|---|---:|---|
| FusionBev | 2026 Information Fusion; LiDAR+4D radar; ScienceDirect preview reports K-Radar mAP but the accessible preview does not expose the full AP table | K-Radar mAP 64.9 | Mention as recent R+L context after verifying the full table/protocol from the paper PDF |
| V2X-R / MDD | Uses K-Radar v2.1 labels and V2X/collaborative settings | Not directly comparable to v1.0 Sedan main table | Keep out of the v1.0 SOTA table |

## K-Radar v2.0 local R+L appendix

These are local v2.0 LR runs in `/home/hongsheng/K-Radar-main`. They use `label_version: v2_0` and `KEY_FEATS: [spatial_features_2d, bev_feat]`, so they should not be mixed with the v1.0 Sedan SOTA table.

| Method | Classes | APBEV@0.3 Sedan | AP3D@0.3 Sedan | APBEV@0.5 Sedan | AP3D@0.5 Sedan | APBEV@0.3 Bus | AP3D@0.3 Bus | APBEV@0.5 Bus | AP3D@0.5 Bus |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ASF_LR_bs4_ep15 | Sedan + Bus | 72.48 | 69.37 | 66.13 | 46.05 | 64.27 | 57.31 | 50.72 | 30.85 |
| DeCU_ASF_LR_bs4_ep15 | Sedan + Bus | 72.47 | 69.28 | 66.11 | 45.88 | 64.56 | 57.43 | 50.92 | 31.82 |
| ASF_LR_bs8_ep30 | Sedan + Bus | 69.94 | 66.68 | 62.44 | 40.33 | 66.29 | 57.15 | 49.38 | 30.38 |

## External sources checked

- AW-MoE arXiv PDF: https://arxiv.org/pdf/2603.16261
- WCBR arXiv PDF: https://arxiv.org/pdf/2604.05405
- L4DR official repository and v1.1 log: https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/logs/v1.1.txt
- K-Radar official ASF sensor-fusion documentation: https://github.com/kaist-avelab/K-Radar/blob/main/docs/sensor_fusion.md
- FusionBev ScienceDirect article preview: https://www.sciencedirect.com/science/article/pii/S1566253526001193
