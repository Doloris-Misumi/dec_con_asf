# K-Radar v1.0 Inference Efficiency

Date: 2026-09-03 01:20:13

Protocol: batch size 1, same local machine, warmup + measured forward timing.

| Method | Params (M) | Forward latency (ms) | Forward FPS | End-to-end latency (ms) | Peak memory (GB) | Source |
|---|---:|---:|---:|---:|---:|---|
| Official ASF v1 ckpt (C+L+R) | 78.13 | 79.95 | 12.51 | 647.50 | 0.97 | `/home/hongsheng/dec_con_asf/results/efficiency_260902/official_asf_v1_model10_rlc.json` |
| TaskDec Robust model_0 (C+L+R) | 79.47 | 86.45 | 11.57 | 687.56 | 0.98 | `/home/hongsheng/dec_con_asf/results/efficiency_260902/taskdec_robust_v1_model0_rlc.json` |
| L4DR model_34 (L+R, local run) | 55.83 | 78.00 | 12.82 | 856.97 | 0.35 | `/home/hongsheng/dec_con_asf/results/efficiency_260902/l4dr_v1_1_model34_lr_local_sparsecube.json` |
| TaskDec - ASF | +1.34 (+1.7%) | +6.50 (+8.1%) | -0.94 (-7.5%) | +40.06 (+6.2%) | +0.01 (+0.5%) | - |

Notes:

- Forward latency is timed around `network(batch)` only, after 20 warmup iterations and over 100 measured iterations.
- End-to-end latency includes dataset loading/collation and is therefore more IO-sensitive.
- L4DR is an L+R model. This local run uses the released `model_34.pt` with the v1.1 config and reads local `sprdr_*.npy` symlinks that point to `sparse_cube/cube_*.npy`.
