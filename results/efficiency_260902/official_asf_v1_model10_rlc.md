# Inference Efficiency: official_asf_v1_model10_rlc

Date: 2026-09-02 20:39:01

- Repo: `/home/hongsheng/K-Radar-main`
- Config: `/home/hongsheng/K-Radar-main/configs/v1_0/cfg_A2F_scl_final_local.yml`
- Model: `/home/hongsheng/K-Radar-main/pretrained/v1_0_official/A2F_v1_0_model_10.pt`
- GPU: `3`
- Infer mode: `rlc`
- Warmup / measured iters: `20` / `100`

| Metric | Value |
|---|---:|
| Parameters (M) | 78.13 |
| Trainable parameters (M) | 1.83 |
| Mean forward latency (ms) | 79.95 |
| Median forward latency (ms) | 79.24 |
| Forward FPS | 12.51 |
| Mean data load latency (ms) | 567.39 |
| Mean end-to-end latency (ms) | 647.50 |
| End-to-end FPS | 1.54 |
| Model memory after load (GB) | 0.30 |
| Peak allocated memory (GB) | 0.97 |
| Peak reserved memory (GB) | 1.24 |
