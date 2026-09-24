# Inference Efficiency: l4dr_v1_1_model34_lr_local_sparsecube

Date: 2026-09-02 21:25:28

- Repo: `/home/hongsheng/L4DR/K-Radar-main-repo`
- Config: `/home/hongsheng/L4DR/K-Radar-main-repo/configs/cfg_PP_L4DR_v1.1.yml`
- Model: `/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v1.1-model_34.pt`
- Data root: `/home/hongsheng/k_radar_dataset`
- GPU: `3`
- Modality: LiDAR + radar
- Label version for loader: `v1_0`
- Radar source: `sprdr_symlink_to_sparse_cube:120`
- Warmup / measured iters: `20` / `100`

| Metric | Value |
|---|---:|
| Parameters (M) | 55.83 |
| Trainable parameters (M) | 55.83 |
| Mean forward latency (ms) | 78.00 |
| Median forward latency (ms) | 76.19 |
| Forward FPS | 12.82 |
| Mean data load latency (ms) | 777.59 |
| Mean CPU-to-GPU transfer latency (ms) | 1.26 |
| Mean end-to-end latency (ms) | 856.97 |
| End-to-end FPS | 1.17 |
| Model memory after load (GB) | 0.21 |
| Peak allocated memory (GB) | 0.35 |
| Peak reserved memory (GB) | 0.40 |
