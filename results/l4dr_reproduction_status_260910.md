# L4DR Reproduction Status, 2026-09-10

## K-Radar Local Check

Local released-checkpoint evaluation completed, but the result should be treated as a protocol-mismatch diagnostic rather than a valid L4DR reproduction.

- Script: `/home/hongsheng/dec_con_asf/tools/analysis/eval_l4dr_kradar_v1_conditional.py`
- Output: `/home/hongsheng/dec_con_asf/results/l4dr_kradar_v1_local_eval_260910/summary.md`
- Checkpoint: `/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v1.1-model_34.pt`
- Local run setting: `label_version=v1_0`, fallback radar sparse source from `/home/hongsheng/k_radar_dataset/*/sparse_cube/cube_*.npy`
- Local result, `conf=0.3`, all condition:
  - APBEV@0.7/0.5/0.3: `12.27 / 32.06 / 32.98`
  - AP3D@0.7/0.5/0.3: `0.55 / 12.37 / 24.80`
- L4DR public log, `conf=0.3`, all condition:
  - APBEV@0.7/0.5/0.3: `53.15 / 77.54 / 79.49`
  - AP3D@0.7/0.5/0.3: `17.01 / 53.50 / 77.96`

Diagnosis:

- L4DR public `cfg_PP_L4DR_v1.1.yml` has `label_version: v2_1` despite the v1.1 filename/version string.
- The public config also expects processed radar sparse tensors under `sparse_radar_tensor_wide_range/rtnh_wider_1p_1`, which are not present under the local K-Radar root.
- Therefore the local K-Radar run is not protocol-aligned with the public log. For paper comparison, keep using the L4DR public log unless the matching revised labels and processed sparse tensors are regenerated/downloaded.

## VoD Reproduction

Started an official L4DR VoD training run from scratch because no local official VoD checkpoint was found.

- Repo/copy: `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec`
- Config: `tools/cfgs/VoD_models/L4DR.yaml`
- Dataset config: `tools/cfgs/dataset_configs/Vod_fusion.yaml`
- Data root: `/home/hongsheng/vod/view_of_delft_PUBLIC/rlfusion_5f`
- GPUs: `CUDA_VISIBLE_DEVICES=2,3`
- Training setting: distributed 2-GPU, `batch_size=8` per GPU, `epochs=100`, `sync_bn=True`, `workers=4`, final-epoch evaluation enabled by `--num_epochs_to_eval 1`
- Extra tag: `l4dr_vod_repro_ep100_g23_260910`
- Output dir: `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/L4DR/l4dr_vod_repro_ep100_g23_260910`
- Main wrapper log: `/home/hongsheng/dec_con_asf/logs/launcher/l4dr_vod_repro_g23_260910.log`
- OpenPCDet train log: `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/L4DR/l4dr_vod_repro_ep100_g23_260910/train_20260910-074827.log`
- tmux session: `taskdec_l4dr_vod_repro_260910`

Current launch sanity:

- Environment fixed to `/home/hongsheng/miniconda3/envs/rl_3dod/bin/python`.
- Dataloader created successfully, with `Total samples for VoD dataset: 5139`.
- Model: `PointPillarMask` with `BaseBEVBackbone_MGF`, matching the L4DR VoD config.
- Training has entered epoch `1/100`; first logged loss is `4.613`.
- Initial GPU memory is approximately GPU2 `35.5GB`, GPU3 `30.5GB`, with no OOM at startup.

Useful commands:

```bash
tail -f /home/hongsheng/dec_con_asf/logs/launcher/l4dr_vod_repro_g23_260910.log
tail -f /home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/L4DR/l4dr_vod_repro_ep100_g23_260910/train_20260910-074827.log
tmux attach -t taskdec_l4dr_vod_repro_260910
nvidia-smi
```
