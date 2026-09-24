# VoD Native PP-Concat vs TaskDec-PP Comparison

Date: 2026-09-08

Protocol:
- Dataset: View-of-Delft, w/o fog
- Modalities: LiDAR + 4D radar
- Metric: KITTI-style 3D AP_R40
- Main IoU thresholds aligned with L4DR Table 2: Car@0.5, Pedestrian@0.25, Cyclist@0.25
- Training: single GPU, batch size 16, 80 epochs, fixed random seed

Local runs:
- PP-Concat: `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/PP_Concat/native_pp_concat_lr_b16_amp_ep80_260907_gpu2/train_20260907-223434.log`
- TaskDec-PP: `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/TaskDec_PP/native_taskdec_pp_lr_b16_fp32_ep80_260907_gpu3/train_20260907-231606.log`

Note:
- PP-Concat used AMP.
- TaskDec-PP used FP32 because AMP training produced NaN gradients in the TaskDec projection/fusion parameters during the earlier smoke run.
- L4DR official numbers are from AAAI 2025 L4DR paper Table 2 and Table 5: https://ojs.aaai.org/index.php/AAAI/article/view/32397/34552

## 1. Final TaskDec-PP Result

General eval statistics:

| Method | recall@0.3 | recall@0.5 | recall@0.7 | Pred objs/frame | sec/example |
|---|---:|---:|---:|---:|---:|
| TaskDec-PP epoch80 | 0.7451 | 0.6295 | 0.3029 | 13.084 | 0.0582 |

Main AP_R40 3D:

| Class / IoU | Easy | Mod. | Hard |
|---|---:|---:|---:|
| Car @0.5 | 72.77 | 68.06 | 62.57 |
| Pedestrian @0.25 | 66.34 | 64.50 | 59.66 |
| Cyclist @0.25 | 93.56 | 90.36 | 82.87 |
| Mean | 77.55 | 74.30 | 68.37 |

Strict AP_R40 3D:

| Class / IoU | Easy | Mod. | Hard |
|---|---:|---:|---:|
| Car @0.7 | 46.09 | 43.38 | 38.32 |
| Pedestrian @0.5 | 50.25 | 45.69 | 40.88 |
| Cyclist @0.5 | 90.80 | 85.68 | 78.03 |
| Mean | 62.38 | 58.25 | 52.41 |

## 2. Comparison A: TaskDec-PP vs PP-Concat

This is the fairest internal comparison: same native VoD data preparation, same PP-style VFE/scatter/head setting, same batch size and epochs.

Main AP_R40 3D:

| Method | Car@0.5 E/M/H | Ped@0.25 E/M/H | Cyc@0.25 E/M/H | Mean E/M/H |
|---|---|---|---|---|
| PP-Concat | 71.56 / 71.65 / 65.72 | 71.97 / 69.01 / 63.70 | 93.27 / 90.48 / 83.11 | 78.93 / 77.05 / 70.84 |
| TaskDec-PP | 72.77 / 68.06 / 62.57 | 66.34 / 64.50 / 59.66 | 93.56 / 90.36 / 82.87 | 77.55 / 74.30 / 68.37 |
| Delta | +1.20 / -3.59 / -3.14 | -5.63 / -4.51 / -4.04 | +0.28 / -0.12 / -0.25 | -1.38 / -2.74 / -2.48 |

Strict AP_R40 3D:

| Method | Car@0.7 E/M/H | Ped@0.5 E/M/H | Cyc@0.5 E/M/H | Mean E/M/H |
|---|---|---|---|---|
| PP-Concat | 45.60 / 45.36 / 39.25 | 52.96 / 48.21 / 42.95 | 88.58 / 83.71 / 76.16 | 62.38 / 59.09 / 52.79 |
| TaskDec-PP | 46.09 / 43.38 / 38.32 | 50.25 / 45.69 / 40.88 | 90.80 / 85.68 / 78.03 | 62.38 / 58.25 / 52.41 |
| Delta | +0.49 / -1.98 / -0.93 | -2.71 / -2.52 / -2.07 | +2.22 / +1.97 / +1.86 | +0.00 / -0.85 / -0.38 |

Takeaway:
- TaskDec-PP improves Cyclist under stricter IoU and slightly improves Easy Car, but hurts Pedestrian and Moderate/Hard Car.
- The main moderate mAP drops from 77.05 to 74.30, so this first native VoD migration does not yet demonstrate a positive generalization gain over PP-Concat.

## 3. Comparison B: TaskDec-PP vs L4DR Full Method

L4DR Table 2 w/o fog, main AP setting:

| Method | Car@0.5 E/M/H | Ped@0.25 E/M/H | Cyc@0.25 E/M/H | Mean E/M/H |
|---|---|---|---|---|
| L4DR official | 85.00 / 76.60 / 69.40 | 74.40 / 72.30 / 65.70 | 93.40 / 90.40 / 83.00 | 84.27 / 79.77 / 72.70 |
| TaskDec-PP | 72.77 / 68.06 / 62.57 | 66.34 / 64.50 / 59.66 | 93.56 / 90.36 / 82.87 | 77.55 / 74.30 / 68.37 |
| Delta | -12.23 / -8.54 / -6.83 | -8.06 / -7.80 / -6.04 | +0.16 / -0.04 / -0.13 | -6.71 / -5.46 / -4.33 |

Takeaway:
- TaskDec-PP is close on Cyclist but clearly below full L4DR on Car and Pedestrian.
- This is expected to some extent because full L4DR includes MME, FAD, IM2, and MSGF, while our current native TaskDec-PP is a cleaner PP-style migration without L4DR's stronger denoising and multi-scale gated fusion stack.

## 4. Comparison C: TaskDec-PP vs L4DR Feature-Fusion Ablation

L4DR Table 5 reports moderate 3D mAP for different fusion blocks under w/o fog:

| Method | W/o fog 3D mAP |
|---|---:|
| L4DR Table 5 Concat. | 77.90 |
| L4DR Table 5 MSGF | 79.80 |
| Local PP-Concat | 77.05 |
| Local TaskDec-PP | 74.30 |

Takeaway:
- Local PP-Concat is close to L4DR's reported Concat. ablation, which supports that the native VoD pipeline is broadly sane.
- Local TaskDec-PP is below both local PP-Concat and L4DR Concat. in this first implementation.

## Current Interpretation

The VoD migration is valuable as an engineering validation: the TaskDec architecture can run end-to-end on a native VoD L+R pipeline and produces valid detections. However, the current VoD result is not yet a strong paper result for cross-dataset generalization. For the paper, it is safer to keep K-Radar v1.0/v2.0 as the main evidence and treat VoD as an exploratory appendix unless the next TaskDec-VoD version improves over PP-Concat.

Possible next fixes:
- Evaluate intermediate TaskDec checkpoints, because epoch80 may not be the best.
- Try a milder TaskDec configuration for VoD: lower control strength, weaker auxiliary losses, or delayed TaskDec activation.
- Add a denoising/foreground filtering component before TaskDec for radar points, since VoD radar point clouds are noisy and L4DR's strongest gains rely heavily on FAD/MME.
