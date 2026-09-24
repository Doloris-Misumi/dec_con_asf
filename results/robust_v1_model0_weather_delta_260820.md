# Robust v1 model_0 weather deltas at conf=0.3

## Sources

- Robust RLC: `logs/exp_260812_232650_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/epoch_0_total/0.3/complete_results.txt`
- Robust LR: `logs/exp_260819_231927_TaskDecControlRobust_v1_0_eval_LR_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/epoch_0_total/0.3/complete_results.txt`
- Official ASF RLC: `/home/hongsheng/K-Radar-main/official_downloads/asf_v1_official_logs_min/exp_250303_200024_A2F_v1_0/test_kitti/none/0.3/complete_results.txt`
- Official ASF LR: `/home/hongsheng/K-Radar-main/logs/exp_260820_203153_ASF_v1_0_local_repro/test_kitti/none/0.3/complete_results.txt`

## Overall

| Mode | BEV@0.3 robust | BEV@0.3 base | Delta | 3D@0.3 robust | 3D@0.3 base | Delta |
|---|---:|---:|---:|---:|---:|---:|
| RLC | 88.84 | 80.78 | +8.06 | 88.36 | 80.31 | +8.04 |
| LR first-stage stdout | 88.87 | 80.78 | +8.10 | 88.37 | 80.31 | +8.06 |
| LR recomputed from saved pred files | 88.45 | 86.35 | +2.10 | 88.06 | 86.02 | +2.04 |

Note: `full_eval_summary.md` for Robust LR reports 3D@0.3 = 88.37. A stale/unstable conditional `complete_results.txt` entry reported 80.30 for `all`, but direct recomputation from the saved `all/preds` and `all/gts` files gives 88.06. For LR, use the first-stage stdout for the historical table, or the recomputed pred-file values for a stricter same-file comparison.

## Weather sample counts

| Weather | Samples |
|---|---:|
| normal | 4309 |
| overcast | 383 |
| fog | 1049 |
| rain | 1317 |
| sleet | 1106 |
| lightsnow | 803 |
| heavysnow | 1098 |

## RLC weather deltas

| Weather | Delta BEV@0.3 | Delta 3D@0.3 | Robust BEV@0.3 | Base BEV@0.3 | Robust 3D@0.3 | Base 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| normal | +0.03 | +8.08 | 88.44 | 88.40 | 87.66 | 79.57 |
| overcast | +0.19 | +0.51 | 90.47 | 90.28 | 90.39 | 89.89 |
| fog | +8.66 | -0.10 | 99.51 | 90.86 | 90.57 | 90.67 |
| rain | +8.00 | +7.93 | 89.22 | 81.22 | 88.90 | 80.97 |
| sleet | +0.24 | +0.22 | 80.72 | 80.48 | 80.42 | 80.20 |
| lightsnow | -0.03 | +8.39 | 89.50 | 89.53 | 89.28 | 80.89 |
| heavysnow | +7.30 | -0.30 | 79.26 | 71.96 | 71.41 | 71.71 |

## LR weather deltas

The following LR table is recomputed directly from saved prediction files for both Robust LR and official ASF LR.

| Weather | Delta BEV@0.3 | Delta 3D@0.3 | Robust BEV@0.3 | Base BEV@0.3 | Robust 3D@0.3 | Base 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| normal | +0.10 | +2.24 | 88.07 | 87.97 | 87.58 | 85.34 |
| overcast | +0.08 | +0.40 | 89.91 | 89.83 | 89.86 | 89.46 |
| fog | -0.14 | -2.53 | 97.28 | 97.42 | 94.53 | 97.06 |
| rain | +2.00 | +1.97 | 88.86 | 86.86 | 88.73 | 86.76 |
| sleet | +2.06 | +1.97 | 81.46 | 79.40 | 81.12 | 79.15 |
| lightsnow | +2.26 | +0.11 | 91.32 | 89.06 | 88.96 | 88.85 |
| heavysnow | +1.36 | +1.30 | 75.87 | 74.51 | 75.47 | 74.17 |

## Takeaway

For RLC, the overall +8 at IoU 0.3 is not uniform. The clearest joint BEV/3D gain is rain. Normal and lightsnow mainly improve 3D@0.3, while fog and heavysnow mainly improve BEV@0.3. For LR under the stricter recomputed-file comparison, the gain is smaller but more broadly positive, with rain, sleet, lightsnow, and heavysnow showing the clearest BEV@0.3 gains, and normal/rain/sleet showing the clearest 3D@0.3 gains. This supports an interpretation that task-aware decoupling improves low-IoU foreground recovery under sensor-degraded weather, especially rain and snow-like conditions, rather than simply lifting every condition evenly.
