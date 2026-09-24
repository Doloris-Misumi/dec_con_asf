# Inference Efficiency: taskdec_robust_v1_model0_rlc

Date: 2026-09-02 20:40:44

- Repo: `/home/hongsheng/dec_con_asf`
- Config: `/home/hongsheng/dec_con_asf/logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`
- Model: `/home/hongsheng/dec_con_asf/logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`
- GPU: `3`
- Infer mode: `rlc`
- Warmup / measured iters: `20` / `100`

| Metric | Value |
|---|---:|
| Parameters (M) | 79.47 |
| Trainable parameters (M) | 3.18 |
| Mean forward latency (ms) | 86.45 |
| Median forward latency (ms) | 85.54 |
| Forward FPS | 11.57 |
| Mean data load latency (ms) | 600.91 |
| Mean end-to-end latency (ms) | 687.56 |
| End-to-end FPS | 1.45 |
| Model memory after load (GB) | 0.30 |
| Peak allocated memory (GB) | 0.98 |
| Peak reserved memory (GB) | 1.25 |
