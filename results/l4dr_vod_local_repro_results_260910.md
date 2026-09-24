# L4DR VoD Local Reproduction Results

Date: 2026-09-10

## Run

- Repo: `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec`
- Config: `tools/cfgs/VoD_models/L4DR.yaml`
- Tag: `l4dr_vod_repro_ep100_g23_260910`
- Output: `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/L4DR/l4dr_vod_repro_ep100_g23_260910`
- Launcher log: `/home/hongsheng/dec_con_asf/logs/launcher/l4dr_vod_repro_g23_260910.log`
- Train log: `/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec/output/VoD_models/L4DR/l4dr_vod_repro_ep100_g23_260910/train_20260910-074827.log`
- Setting: 2 GPUs, total batch size 16, 100 epochs, `sync_bn=True`, `USE_FOG=0`, `VOD_EVA=False` during default train-time evaluation.
- Status: finished normally, exit code 0.

## Final KITTI AP_R40

Main VoD/L4DR thresholds:

- Car: `AP_R40@0.70, 0.50, 0.50`
- Pedestrian: `AP_R40@0.50, 0.25, 0.25`
- Cyclist: `AP_R40@0.50, 0.25, 0.25`

| Epoch | Car E/M/H | Ped. E/M/H | Cyc. E/M/H | Mean E/M/H |
|---:|---:|---:|---:|---:|
| 99 | 78.63 / 74.07 / 68.84 | 73.45 / 70.14 / 65.01 | 92.95 / 90.27 / 82.78 | 81.68 / 78.16 / 72.21 |
| 100 | 78.60 / 74.19 / 68.96 | 72.97 / 69.66 / 64.57 | 93.20 / 90.38 / 82.89 | 81.59 / 78.08 / 72.14 |

Strict thresholds:

- Car: `AP_R40@0.70, 0.70, 0.70`
- Pedestrian: `AP_R40@0.50, 0.50, 0.50`
- Cyclist: `AP_R40@0.50, 0.50, 0.50`

| Epoch | Car E/M/H | Ped. E/M/H | Cyc. E/M/H | Mean E/M/H |
|---:|---:|---:|---:|---:|
| 99 | 48.94 / 48.91 / 42.52 | 58.65 / 54.74 / 48.45 | 92.18 / 86.94 / 77.88 | 66.59 / 63.53 / 56.28 |
| 100 | 48.82 / 48.89 / 42.50 | 58.50 / 54.40 / 48.23 | 92.58 / 87.30 / 78.22 | 66.63 / 63.53 / 56.32 |

## Offline Official VoD EAA/DC

Computed from the saved `result.pkl` files using `pcdet.datasets.vod_evaluation.kitti_official_evaluate.get_official_eval_result`.

| Epoch | EAA Car / Ped. / Cyc. / mAP | DC Car / Ped. / Cyc. / mAP |
|---:|---:|---:|
| 99 | 68.69 / 65.35 / 78.98 / 71.00 | 90.51 / 75.13 / 88.90 / 84.84 |
| 100 | 68.91 / 64.83 / 78.99 / 70.91 | 90.56 / 74.55 / 88.86 / 84.65 |

Epoch 99 is the best final checkpoint by both main AP_R40 mean and official EAA/DC mAP.

## Comparison to Existing VoD Table

From `/home/hongsheng/dec_con_asf/results/paper_vod_main_table_draft_260909.md`:

| Method | Source | KITTI AP_R40 Mean E/M/H | EAA mAP | DC mAP |
|---|---|---:|---:|---:|
| PP-Concat | local epoch 80 | 78.93 / 77.05 / 70.84 | 69.88 | 83.80 |
| TaskDec-PP warm mild | local epoch 79 official / epoch 73 AP_R40 | 81.39 / 77.42 / 70.43 | 70.18 | 83.79 |
| L4DR | paper Table 2/3 | 84.27 / 79.77 / 72.70 | 72.70 | 87.47 |
| L4DR | local reproduction epoch 99 | 81.68 / 78.16 / 72.21 | 71.00 | 84.84 |

Takeaways:

- The local L4DR reproduction is below the L4DR paper row: `-2.59 / -1.61 / -0.49` AP_R40 mean E/M/H, `-1.70` EAA, and `-2.63` DC.
- The local L4DR reproduction is still above the current TaskDec-PP warm/mild result: `+0.29 / +0.74 / +1.78` AP_R40 mean E/M/H, `+0.82` EAA, and `+1.05` DC.
- This makes the VoD story more nuanced: TaskDec still improves the controlled PP-Concat baseline on EAA, but a locally reproduced full L4DR remains stronger on VoD.

## Recommended Paper Use

Keep the published L4DR row as the external specialized-method reference, and optionally add the local reproduction as an appendix sanity row. Do not claim TaskDec beats L4DR on VoD. The safer wording is:

> On VoD, TaskDec improves a controlled native PP-Concat L+4DR baseline on EAA, while full L4DR remains stronger both in the published results and in our local reproduction.
