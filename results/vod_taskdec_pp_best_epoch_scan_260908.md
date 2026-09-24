# VoD TaskDec-PP Checkpoint Scan

Date: 2026-09-08

Protocol:
- Dataset: View-of-Delft, w/o fog
- Modalities: LiDAR + 4D radar
- Metric: KITTI-style 3D AP_R40
- Main metric: mean of Car@0.5, Pedestrian@0.25, Cyclist@0.25, Moderate split
- Evaluated checkpoints: epoch 1-80

Logs:
- Epoch 1-40: `/home/hongsheng/dec_con_asf/vod_taskdec_native/logs/taskdec_eval_ep001_040_gpu2.log`
- Epoch 41-80: `/home/hongsheng/dec_con_asf/vod_taskdec_native/logs/taskdec_eval_ep041_080_gpu3.log`

## Best Checkpoint

Best checkpoint by main Moderate mAP:

| Epoch | Main mAP E/M/H | Car@0.5 M | Ped@0.25 M | Cyc@0.25 M | Strict mAP M | Recall@0.3 |
|---:|---:|---:|---:|---:|---:|---:|
| 73 | 77.62 / 74.71 / 68.38 | 69.36 | 64.40 | 90.36 | 57.80 | 0.7427 |

Checkpoint path:

`/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP/native_taskdec_pp_lr_b16_fp32_ep80_260907_gpu3/ckpt/checkpoint_epoch_73.pth`

Result directory:

`/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP/native_taskdec_pp_lr_b16_fp32_ep80_260907_gpu3/eval/eval_all_default/ep041_080_gpu3/epoch_73/val`

## Top Checkpoints by Main Moderate mAP

| Rank | Epoch | Main mAP E/M/H | Car@0.5 M | Ped@0.25 M | Cyc@0.25 M | Recall@0.3 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 73 | 77.62 / 74.71 / 68.38 | 69.36 | 64.40 | 90.36 | 0.7427 |
| 2 | 70 | 78.12 / 74.46 / 68.59 | 68.70 | 64.61 | 90.08 | 0.7373 |
| 3 | 79 | 77.49 / 74.32 / 68.39 | 68.06 | 64.51 | 90.38 | 0.7450 |
| 4 | 80 | 77.55 / 74.30 / 68.37 | 68.05 | 64.50 | 90.35 | 0.7451 |
| 5 | 74 | 77.30 / 74.24 / 68.36 | 67.63 | 64.48 | 90.61 | 0.7377 |
| 6 | 77 | 77.52 / 74.24 / 68.37 | 68.11 | 64.40 | 90.21 | 0.7423 |
| 7 | 78 | 77.43 / 74.23 / 68.30 | 68.06 | 64.31 | 90.32 | 0.7453 |
| 8 | 76 | 77.13 / 74.07 / 68.24 | 67.59 | 64.55 | 90.09 | 0.7429 |
| 9 | 75 | 76.91 / 73.85 / 67.47 | 66.52 | 64.68 | 90.35 | 0.7354 |
| 10 | 72 | 77.91 / 73.62 / 67.50 | 68.18 | 64.33 | 88.36 | 0.7328 |

## Comparison Against Local PP-Concat and L4DR

Main AP_R40 3D Moderate:

| Method | Epoch | Car@0.5 | Ped@0.25 | Cyc@0.25 | Main mAP |
|---|---:|---:|---:|---:|---:|
| Local PP-Concat | 80 | 71.65 | 69.01 | 90.48 | 77.05 |
| Local TaskDec-PP best | 73 | 69.36 | 64.40 | 90.36 | 74.71 |
| Local TaskDec-PP final | 80 | 68.05 | 64.50 | 90.35 | 74.30 |
| L4DR official full | - | 76.60 | 72.30 | 90.40 | 79.77 |

Deltas:
- TaskDec-PP best vs TaskDec-PP final: +0.41 Moderate mAP.
- TaskDec-PP best vs local PP-Concat: -2.34 Moderate mAP.
- TaskDec-PP best vs L4DR full: -5.06 Moderate mAP.

## Notes

- The best checkpoint appears late, around epoch 70-80, with epoch 73 as the peak.
- TaskDec-PP remains close to L4DR/local PP-Concat on Cyclist but underperforms on Car and Pedestrian.
- VoD still looks like a valid engineering transfer test, but this particular TaskDec-PP configuration is not yet a strong generalization result.
