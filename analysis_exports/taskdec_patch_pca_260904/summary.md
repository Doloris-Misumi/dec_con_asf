# TaskDec Patch-State PCA Export

- Config: `/home/hongsheng/dec_con_asf/logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
- Model: `/home/hongsheng/dec_con_asf/logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`
- Inference mode: `rlc`
- Frames collected: 80 / seen 79
- Feature records: 43956

## PCA Explained Variance

| Feature | PC1 | PC2 |
|---|---:|---:|
| raw | 63.23% | 21.23% |
| common | 59.41% | 26.38% |
| unique | 57.32% | 30.55% |

## Cosine Sanity Checks

| Metric | Mean | Std | N |
|---|---:|---:|---:|
| common_cos_bg_CL | 0.9648 | 0.0005 | 80 |
| common_cos_bg_CR | 0.9422 | 0.0033 | 80 |
| common_cos_bg_LR | 0.9824 | 0.0017 | 80 |
| common_cos_fg_CL | 0.9412 | 0.0085 | 80 |
| common_cos_fg_CR | 0.9615 | 0.0077 | 80 |
| common_cos_fg_LR | 0.9632 | 0.0089 | 80 |
| common_unique_abs_cos_bg_C | 0.9267 | 0.0001 | 80 |
| common_unique_abs_cos_bg_L | 0.3237 | 0.0216 | 80 |
| common_unique_abs_cos_bg_R | 0.5531 | 0.0121 | 80 |
| common_unique_abs_cos_fg_C | 0.9267 | 0.0002 | 80 |
| common_unique_abs_cos_fg_L | 0.2557 | 0.0448 | 80 |
| common_unique_abs_cos_fg_R | 0.7013 | 0.0214 | 80 |
| fg_ratio | 0.0297 | 0.0115 | 80 |
| num_fg_patches | 42.7750 | 16.5507 | 80 |
| raw_cos_bg_CL | -0.0524 | 0.0027 | 80 |
| raw_cos_bg_CR | -0.3628 | 0.0054 | 80 |
| raw_cos_bg_LR | 0.4164 | 0.0050 | 80 |
| raw_cos_fg_CL | -0.0323 | 0.0100 | 80 |
| raw_cos_fg_CR | -0.3940 | 0.0084 | 80 |
| raw_cos_fg_LR | 0.4127 | 0.0120 | 80 |
| unique_cos_bg_CL | 0.4116 | 0.0174 | 80 |
| unique_cos_bg_CR | 0.6039 | 0.0068 | 80 |
| unique_cos_bg_LR | 0.3776 | 0.0161 | 80 |
| unique_cos_fg_CL | 0.3380 | 0.0391 | 80 |
| unique_cos_fg_CR | 0.6678 | 0.0092 | 80 |
| unique_cos_fg_LR | 0.3462 | 0.0382 | 80 |