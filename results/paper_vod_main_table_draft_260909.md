# VoD Main Table Draft

Date: 2026-09-09

Purpose: draft VoD comparison tables for the TaskDec paper. Use the local official EAA/DC rows in Table B for the principal generalization statement, and Table A for the supplementary KITTI AP_R40 comparison. The broader literature rows provide context with sensor modalities explicitly identified.

Writing decision (2026-09-10): emphasize that TaskDec adapts to a native VoD PointPillars-style LiDAR–4D radar backbone and improves the strong PP-Concat baseline on EAA. Here, generalization refers to architecture transfer with training on the target dataset. Report EAA 69.88→70.18 and essentially unchanged DC 83.80→83.79. Keep the mild/warm-start setting, AMP/FP32 difference, and checkpoint selection explicit in the setup; do not describe this as a statistically established gain across training runs.

Discuss L4DR more fully in the K-Radar main comparison and related work, retaining the sensor distinctions. In the VoD generalization paragraph, one sentence acknowledging its stronger absolute performance is enough; retain its row in the comparison table. The fine-grained L4DR discussion below is an internal reference, not a proposed main-text subsection.

Suggested main-text paragraph:

> To assess transfer across data representations and backbones, we adapt TaskDec to a native PointPillars-style LiDAR–4D radar pipeline and train it on VoD. Under the reported warm-start setting, TaskDec improves the strong PP-Concat baseline from 69.88 to 70.18 EAA mAP while maintaining comparable DC mAP (83.79 versus 83.80), supporting its applicability beyond K-Radar. The specialized VoD method L4DR retains higher absolute performance.

## Table A. Same-Protocol VoD KITTI AP_R40

Recommended use: appendix or supplementary generalization table.

Protocol:
- Dataset: View-of-Delft validation split, w/o fog.
- Modalities: LiDAR and/or 4D radar point clouds.
- Metric: KITTI-style 3D AP_R40 from the L4DR VoD-Fog setting.
- Main thresholds: Car@0.5, Pedestrian@0.25, Cyclist@0.25, following L4DR Table 2. In the local OpenPCDet log this appears as `Car AP_R40@0.70, 0.50, 0.50`, `Pedestrian AP_R40@0.50, 0.25, 0.25`, and `Cyclist AP_R40@0.50, 0.25, 0.25`.
- Local runs: single GPU, batch size 16, 80 epochs. PP-Concat uses AMP; TaskDec-PP runs use FP32 because AMP produced NaN gradients in TaskDec projection/fusion parameters.

| Method | Source | Modality | Epoch | Car E/M/H | Ped. E/M/H | Cyc. E/M/H | Mean E/M/H |
|---|---|---|---:|---:|---:|---:|---:|
| PointPillars | L4DR Table 2 | L | - | 84.90 / 73.50 / 67.50 | 62.70 / 58.40 / 53.40 | 85.50 / 79.00 / 72.70 | 77.70 / 70.30 / 64.53 |
| InterFusion | L4DR Table 2 | L+4DR | - | 67.60 / 65.80 / 58.80 | 73.70 / 70.10 / 64.70 | 90.30 / 87.00 / 81.20 | 77.20 / 74.30 / 68.23 |
| PP-Concat | Local reimplementation | L+4DR | 80 | 71.56 / 71.65 / 65.72 | 71.97 / 69.01 / 63.70 | 93.27 / 90.48 / 83.11 | 78.93 / 77.05 / 70.84 |
| TaskDec-PP | Local, first fp32 setting | L+4DR | 73 | 72.79 / 69.36 / 62.76 | 66.64 / 64.40 / 59.57 | 93.41 / 90.36 / 82.81 | 77.62 / 74.71 / 68.38 |
| TaskDec-PP mild | Local, strength 0.5 + aux x0.5 | L+4DR | 70 | 78.36 / 70.60 / 63.19 | 70.73 / 68.34 / 62.13 | 93.38 / 89.68 / 82.35 | 80.82 / 76.21 / 69.22 |
| TaskDec-PP mild + PP-Concat warm start | Local, best Mod. | L+4DR | 73 | 79.69 / 72.72 / 65.14 | 71.01 / 69.45 / 63.34 | 93.46 / 90.08 / 82.80 | 81.39 / 77.42 / 70.43 |
| L4DR | L4DR Table 2 | L+4DR | - | 85.00 / 76.60 / 69.40 | 74.40 / 72.30 / 65.70 | 93.40 / 90.40 / 83.00 | 84.27 / 79.77 / 72.70 |

Status:
- The warm-start rescan of epochs 59-79 is complete. Epoch 73 is best by Moderate mean AP_R40; epoch 79 is best by Hard mean AP_R40 with mean AP_R40 E/M/H = 80.50 / 77.25 / 71.09.
- Warm-start epoch 80 is also useful as a final-checkpoint reference: mean AP_R40 E/M/H = 80.54 / 77.22 / 71.06, which improves PP-Concat on all three difficulties.
- Current TaskDec best-Mod checkpoint vs local PP-Concat: +2.45 / +0.37 / -0.41 mean AP_R40 E/M/H.
- Current TaskDec best-Mod checkpoint vs published InterFusion: +4.19 / +3.12 / +2.20 mean AP_R40 E/M/H.
- Current TaskDec best-Mod checkpoint vs L4DR full: -2.88 / -2.35 / -2.27 mean AP_R40 E/M/H.

Suggested paper sentence:

> On VoD, TaskDec can be transferred to a native LiDAR-4D radar PointPillars-style backbone without relying on K-Radar-specific inputs. Under the same local PP-style backbone, TaskDec improves the Moderate mean AP_R40 from 77.05 to 77.42, indicating that the decoupled task-aware fusion mechanism remains usable outside the K-Radar tensor setting.

## L4DR Fine-Grained Comparison

This section answers whether our current VoD results are fully dominated by L4DR. The short answer is no at the class-difficulty level, but yes at the mean and most Car/Pedestrian metrics.

Under the same KITTI-style AP_R40 / w/o fog protocol as Table A:
- L4DR mean AP_R40 E/M/H: 84.27 / 79.77 / 72.70.
- Our best Moderate TaskDec checkpoint, warm-start epoch 73: 81.39 / 77.42 / 70.43, lower than L4DR by -2.88 / -2.35 / -2.27.
- Our best Hard TaskDec checkpoint, warm-start epoch 79: 80.50 / 77.25 / 71.09, lower than L4DR by -3.77 / -2.52 / -1.61.

Class-difficulty entries where a current local result exceeds L4DR:
- PP-Concat epoch 80: Cyclist Moderate 90.48 vs 90.40 (+0.08), Cyclist Hard 83.11 vs 83.00 (+0.11). This is a baseline-side win, not TaskDec-specific.
- TaskDec-PP first fp32 epoch 73: Cyclist Easy 93.41 vs 93.40 (+0.01).
- TaskDec warm-start epoch 73: Cyclist Easy 93.46 vs 93.40 (+0.06).
- TaskDec warm-start epoch 79: Cyclist Easy 93.51 vs 93.40 (+0.11).
- TaskDec warm-start epoch 80: Cyclist Easy 93.51 vs 93.40 (+0.11).

Recommended writing:
- Do not claim TaskDec beats L4DR on VoD.
- It is fair to say TaskDec is not strictly dominated in every fine-grained AP entry, but this is weak evidence because the wins are tiny and concentrated on Cyclist.
- The stronger VoD claim is generalization under a controlled native backbone: TaskDec improves PP-Concat and beats InterFusion mean AP_R40, while L4DR remains a stronger specialized VoD/LiDAR-4DRadar method.

## Table B. VoD Official-Metric Context

Use this table as the official-metric VoD generalization table. It uses VoD official EAA/DC AP, not the KITTI AP_R40 numbers in Table A. Most recent high-profile methods here are R+C, while our local runs are L+4DR.

| Method | Venue / paper | Modality | EAA mAP | DC / RoI mAP | FPS | Source |
|---|---|---|---:|---:|---:|---|
| PointPillars | baseline | R | 45.18 | 67.48 | 113.9 | R4Det Table 2 |
| RadarPillarNet | IROS 2024 | R | 46.01 | 65.86 | 98.8 | R4Det Table 2 |
| SMURF | T-IV 2023/2024 | R | 50.97 | 69.72 | - | R4Det Table 2 |
| RCFusion | radar-camera baseline | R+C | 49.65 | 69.23 | 9.0 | R4Det Table 2 |
| LXL | T-IV 2023 | R+C | 56.31 | 72.93 | 6.1 | R4Det Table 2 / CVFusion Table 1 |
| HGSFusion | AAAI 2025 | R+C | 58.96 | 79.46 | - | HGSFusion Table 1 |
| SGDet3D | recent R+C baseline | R+C | 59.75 | 77.42 | 9.2 | R4Det Table 2 |
| CVFusion | ICCV 2025 | R+C | 65.41 | 82.42 | 5.4 | CVFusion Table 1 / R4Det Table 2 |
| R4Det | CVPR 2026 | R+C | 66.69 | 83.68 | 8.3 | R4Det Table 2 |
| RPGFusion | CVPR 2026 | R+C | 69.31* | 86.20* | - | CVF page + secondary paper note* |
| PointPillars | L4DR Table 3 | L | 65.53 | 81.83 | - | L4DR Table 3 |
| PP-Concat | Local official eval, epoch 80 | L+4DR | 69.88 | 83.80 | - | Local `VOD_EVA=True` from saved `result.pkl` |
| TaskDec-PP mild + PP-Concat warm start | Local official eval, epoch 79 | L+4DR | 70.18 | 83.79 | - | Local `VOD_EVA=True` from saved `result.pkl` |
| InterFusion | L4DR Table 3 | L+4DR | 69.83 | 83.80 | - | L4DR Table 3 |
| L4DR | AAAI 2025 | L+4DR | 72.70 | 87.47 | - | L4DR Table 3 |

Local official-eval class breakdown:

| Method | Epoch | EAA Car / Ped. / Cyc. / mAP | DC Car / Ped. / Cyc. / mAP |
|---|---:|---:|---:|
| PP-Concat | 80 | 66.88 / 63.38 / 79.39 / 69.88 | 90.77 / 71.09 / 89.53 / 83.80 |
| TaskDec-PP warm mild | 73 | 62.72 / 63.76 / 79.16 / 68.55 | 90.78 / 70.76 / 89.69 / 83.74 |
| TaskDec-PP warm mild | 79 | 67.50 / 63.66 / 79.38 / 70.18 | 90.59 / 71.02 / 89.76 / 83.79 |
| TaskDec-PP warm mild | 80 | 67.52 / 63.66 / 79.35 / 70.18 | 90.57 / 70.98 / 89.73 / 83.76 |

Interpretation:
- The official `VOD_EVA=True` eval logs generated predictions successfully but stopped before logging the final dict; the numbers above were computed offline from their saved `result.pkl` files with the same `VodDataset.evaluation()` official evaluator.
- For official EAA/DC, TaskDec epoch 79 is better than the AP_R40 best-Mod epoch 73. Epoch 79 gives 70.18 / 83.79, while epoch 80 gives 70.18 / 83.76.
- TaskDec improves local PP-Concat on EAA by +0.30 and is essentially tied on DC (-0.01).
- TaskDec is slightly above InterFusion on EAA (+0.35) and essentially tied on DC (-0.01), but it is still below full L4DR by -2.52 EAA and -3.68 DC.
- The most defensible VoD official-metric claim is: TaskDec transfers beyond K-Radar and improves a controlled native PP-Concat L+4DR baseline on EAA, while L4DR remains the stronger specialized VoD fusion method.
- `*` RPGFusion's existence and CVPR 2026 venue are confirmed from the CVF Open Access page, but the exact EAA/DC numbers were only available from a secondary paper-note page in this pass because the CVF PDF/table could not be fetched by the browser. Verify the primary PDF before using this row in the camera-ready paper.

## Source Notes

- VoD official dataset page: https://tudelft-iv.github.io/view-of-delft-dataset/
- L4DR AAAI 2025 paper: https://ojs.aaai.org/index.php/AAAI/article/view/32397/34552
- L4DR official code: https://github.com/ylwhxht/L4DR
- HGSFusion arXiv: https://arxiv.org/abs/2412.11489
- CVFusion arXiv: https://arxiv.org/abs/2507.04587
- R4Det arXiv: https://arxiv.org/abs/2603.11566
- RPGFusion CVF page: https://openaccess.thecvf.com/content/CVPR2026/html/Qiu_RPGFusion_4D_Radar_Prior-Guided_Multi-Modal_Fusion_for_3D_Detection_CVPR_2026_paper.html
- RPGFusion secondary note used only for tentative metric row: https://m0rtzz.github.io/paper-notes/CVPR2026/autonomous_driving/rpgfusion_4d_radar_prior-guided_multi-modal_fusion_for_3d_detection/
