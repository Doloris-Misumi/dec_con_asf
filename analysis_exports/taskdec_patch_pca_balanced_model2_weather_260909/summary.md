# TaskDec Patch-State PCA Export

- Config: `logs/exp_260810_221300_TaskDecControlBalanced_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
- Model: `logs/exp_260810_221300_TaskDecControlBalanced_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_2.pt`
- Inference mode: `rlc`
- Frames collected: 168 / seen 167
- Feature records: 74736
- Frames per weather target: 24

## PCA Explained Variance

| Feature | PC1 | PC2 |
|---|---:|---:|
| raw | 52.22% | 26.58% |
| common | 54.05% | 22.41% |
| unique | 60.95% | 24.42% |

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
| common_cos_bg_CL | 0.9838 | 0.0018 | 168 |
| common_cos_bg_CR | 0.9755 | 0.0040 | 168 |
| common_cos_bg_LR | 0.9871 | 0.0020 | 168 |
| common_cos_fg_CL | 0.9705 | 0.0101 | 168 |
| common_cos_fg_CR | 0.9799 | 0.0064 | 168 |
| common_cos_fg_LR | 0.9729 | 0.0084 | 168 |
| common_unique_abs_cos_bg_C | 0.9346 | 0.0017 | 168 |
| common_unique_abs_cos_bg_L | 0.4374 | 0.1231 | 168 |
| common_unique_abs_cos_bg_R | 0.5891 | 0.0375 | 168 |
| common_unique_abs_cos_fg_C | 0.9346 | 0.0039 | 168 |
| common_unique_abs_cos_fg_L | 0.3095 | 0.1561 | 168 |
| common_unique_abs_cos_fg_R | 0.7091 | 0.0467 | 168 |
| fg_ratio | 0.0364 | 0.0248 | 168 |
| num_fg_patches | 52.3690 | 35.7344 | 168 |
| raw_cos_bg_CL | 0.1198 | 0.0122 | 168 |
| raw_cos_bg_CR | -0.4487 | 0.0183 | 168 |
| raw_cos_bg_LR | -0.1125 | 0.0220 | 168 |
| raw_cos_fg_CL | 0.1425 | 0.0409 | 168 |
| raw_cos_fg_CR | -0.4652 | 0.0334 | 168 |
| raw_cos_fg_LR | -0.2123 | 0.0495 | 168 |
| unique_cos_bg_CL | 0.5283 | 0.1162 | 168 |
| unique_cos_bg_CR | 0.6404 | 0.0358 | 168 |
| unique_cos_bg_LR | 0.6044 | 0.0879 | 168 |
| unique_cos_fg_CL | 0.4144 | 0.1445 | 168 |
| unique_cos_fg_CR | 0.7581 | 0.0458 | 168 |
| unique_cos_fg_LR | 0.4856 | 0.1195 | 168 |