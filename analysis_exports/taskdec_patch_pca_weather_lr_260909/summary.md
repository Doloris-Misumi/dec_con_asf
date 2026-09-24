# TaskDec Patch-State PCA Export

- Config: `logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
- Model: `logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`
- Inference mode: `lr`
- Frames collected: 168 / seen 167
- Feature records: 52392
- Frames per weather target: 24

## PCA Explained Variance

| Feature | PC1 | PC2 |
|---|---:|---:|
| raw | 59.26% | 9.70% |
| common | 71.87% | 13.78% |
| unique | 70.38% | 12.53% |

## Weather Frame Counts

| Weather | Frames |
|---|---:|
| normal | 24 |
| overcast | 24 |
| fog | 24 |
| rain | 24 |
| sleet | 24 |
| lightsnow | 24 |
| heavysnow | 24 |

## Cosine Sanity Checks

| Metric | Mean | Std | N |
|---|---:|---:|---:|
| common_cos_bg_LR | 0.9772 | 0.0036 | 168 |
| common_cos_fg_LR | 0.9616 | 0.0179 | 168 |
| common_unique_abs_cos_bg_L | 0.4478 | 0.1383 | 168 |
| common_unique_abs_cos_bg_R | 0.5253 | 0.0261 | 168 |
| common_unique_abs_cos_fg_L | 0.3736 | 0.1668 | 168 |
| common_unique_abs_cos_fg_R | 0.6594 | 0.0470 | 168 |
| fg_ratio | 0.0434 | 0.0291 | 168 |
| num_fg_patches | 62.4702 | 41.8684 | 168 |
| raw_cos_bg_LR | 0.4152 | 0.0106 | 168 |
| raw_cos_fg_LR | 0.4061 | 0.0251 | 168 |
| unique_cos_bg_LR | 0.4633 | 0.1027 | 168 |
| unique_cos_fg_LR | 0.4275 | 0.1245 | 168 |