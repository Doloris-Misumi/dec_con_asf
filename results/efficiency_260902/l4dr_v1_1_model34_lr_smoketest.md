# Inference Efficiency: l4dr_v1_1_model34_lr_smoketest

Date: 2026-09-02 21:23:16

- Repo: `/home/hongsheng/L4DR/K-Radar-main-repo`
- Config: `/home/hongsheng/L4DR/K-Radar-main-repo/configs/cfg_PP_L4DR_v1.1.yml`
- Model: `/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v1.1-model_34.pt`
- Data root: `/home/hongsheng/k_radar_dataset`
- GPU: `3`
- Modality: LiDAR + radar
- Label version for loader: `v1_0`
- Radar source: `sprdr:5`
- Warmup / measured iters: `2` / `3`

| Metric | Value |
|---|---:|
| Parameters (M) | 55.83 |
| Trainable parameters (M) | 55.83 |
| Mean forward latency (ms) | 75.70 |
| Median forward latency (ms) | 76.07 |
| Forward FPS | 13.21 |
| Mean data load latency (ms) | 844.20 |
| Mean CPU-to-GPU transfer latency (ms) | 1.31 |
| Mean end-to-end latency (ms) | 921.34 |
| End-to-end FPS | 1.09 |
| Model memory after load (GB) | 0.21 |
| Peak allocated memory (GB) | 0.35 |
| Peak reserved memory (GB) | 0.40 |
