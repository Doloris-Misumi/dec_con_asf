# TaskDec Patch-State PCA Export

- Config: `/home/hongsheng/dec_con_asf/logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
- Model: `/home/hongsheng/dec_con_asf/logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`
- Inference mode: `rlc`
- Frames collected: 2 / seen 1
- Feature records: 216

## PCA Explained Variance

| Feature | PC1 | PC2 |
|---|---:|---:|
| raw | 64.52% | 21.46% |
| common | 57.99% | 29.74% |
| unique | 56.52% | 32.06% |

## Cosine Sanity Checks

| Metric | Mean | Std | N |
|---|---:|---:|---:|
| common_cos_bg_CL | 0.9645 | 0.0004 | 2 |
| common_cos_bg_CR | 0.9428 | 0.0024 | 2 |
| common_cos_bg_LR | 0.9822 | 0.0010 | 2 |
| common_cos_fg_CL | 0.9467 | 0.0018 | 2 |
| common_cos_fg_CR | 0.9593 | 0.0018 | 2 |
| common_cos_fg_LR | 0.9567 | 0.0004 | 2 |
| common_unique_abs_cos_bg_C | 0.9268 | 0.0001 | 2 |
| common_unique_abs_cos_bg_L | 0.3074 | 0.0091 | 2 |
| common_unique_abs_cos_bg_R | 0.5573 | 0.0095 | 2 |
| common_unique_abs_cos_fg_C | 0.9266 | 0.0000 | 2 |
| common_unique_abs_cos_fg_L | 0.2920 | 0.0284 | 2 |
| common_unique_abs_cos_fg_R | 0.6638 | 0.0109 | 2 |
| fg_ratio | 0.0472 | 0.0000 | 2 |
| num_fg_patches | 68.0000 | 0.0000 | 2 |
| raw_cos_bg_CL | -0.0513 | 0.0027 | 2 |
| raw_cos_bg_CR | -0.3608 | 0.0016 | 2 |
| raw_cos_bg_LR | 0.4227 | 0.0014 | 2 |
| raw_cos_fg_CL | -0.0310 | 0.0007 | 2 |
| raw_cos_fg_CR | -0.3821 | 0.0013 | 2 |
| raw_cos_fg_LR | 0.4179 | 0.0039 | 2 |
| unique_cos_bg_CL | 0.3991 | 0.0070 | 2 |
| unique_cos_bg_CR | 0.6060 | 0.0051 | 2 |
| unique_cos_bg_LR | 0.3667 | 0.0081 | 2 |
| unique_cos_fg_CL | 0.3715 | 0.0251 | 2 |
| unique_cos_fg_CR | 0.6534 | 0.0049 | 2 |
| unique_cos_fg_LR | 0.3727 | 0.0224 | 2 |