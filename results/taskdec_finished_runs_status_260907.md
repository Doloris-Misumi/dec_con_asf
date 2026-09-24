# TaskDec Finished Runs Status

Date: 2026-09-07

Scope: recent K-Radar ablation/hyperparameter runs and the VoD L+R training run. GPU1/WCBR is intentionally ignored.

## Runtime status

- No active `tmux` server was found.
- `ps -C python` showed no active Python training/evaluation processes.
- GPU status after the runs: GPU2 and GPU3 are effectively idle; GPU0 has small resident memory but 0% utilization; GPU1 belongs to WCBR and is not considered here.

## K-Radar v1.0 component ablations

Protocol: K-Radar v1.0 Sedan, C+L+R, full validation, `conf_thr=0.3`.

| Variant | Checkpoint | BEV@0.7 | BEV@0.5 | BEV@0.3 | 3D@0.7 | 3D@0.5 | 3D@0.3 | Delta 3D@0.3 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Full TaskDec Robust | `model_0` | 62.63 | 88.10 | 88.84 | 22.04 | 67.50 | 88.36 | 0.00 |
| w/o sensor reliability | `model_9` | 61.36 | 79.91 | 80.38 | 11.08 | 64.38 | 79.62 | -8.74 |
| w/o task context | `model_9` | 54.91 | 79.96 | 80.68 | 17.10 | 66.23 | 80.14 | -8.22 |
| w/o decoupling supervision | `model_9` | 55.71 | 80.04 | 80.65 | 16.49 | 66.16 | 80.23 | -8.13 |
| w/o foreground gate | `model_9` | 55.49 | 80.12 | 80.65 | 19.41 | 64.80 | 80.00 | -8.36 |

Takeaway: the two newly finished ablations are consistent with the earlier two. Removing decoupling supervision or foreground gating drops AP3D@0.3 by about 8 points, so the ablation story is strong and internally coherent.

## K-Radar v1.0 control strength sweep

Protocol: full validation, `conf_thr=0.3`.

| Variant | Checkpoint | BEV@0.7 | BEV@0.5 | BEV@0.3 | 3D@0.7 | 3D@0.5 | 3D@0.3 | Delta 3D@0.3 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| TaskDec Robust, strength=0.75 | `model_0` | 62.63 | 88.10 | 88.84 | 22.02 | 67.50 | 88.36 | 0.00 |
| TaskDec, strength=0.5 | `model_0` | 62.26 | 80.10 | 88.77 | 19.36 | 66.77 | 88.19 | -0.17 |
| TaskDec, strength=1.0 | `model_0` | 62.82 | 80.29 | 88.79 | 19.97 | 67.31 | 88.33 | -0.03 |
| w/o sensor reliability, strength=0.0 | `model_9` | 61.36 | 79.91 | 80.38 | 11.08 | 64.38 | 79.62 | -8.74 |

Takeaway: `DEC_CONTROL_STRENGTH=0.75` remains the best full-test setting. `1.0` is close, but it does not beat the selected main checkpoint.

## K-Radar v1.0 gate-bias sweep

Training used `DEC_CONTROL_STRENGTH=0.75`.

| Gate init bias | Selection result | Full-test status | Full-test 3D@0.3 |
|---:|---|---|---:|
| -0.6 | subset-best `model_6`, 3D@0.3=88.79 | evaluated full validation | 80.45 |
| -1.8 | subset-best `model_0`, 3D@0.3=88.28 | not full-evaluated | - |
| default/main | `TaskDec Robust model_0` | evaluated full validation | 88.36 |

Takeaway: the -0.6 subset winner did not transfer to full validation, and -1.8 was already below the main setting on the 1000-sample subset. This sweep should live in the appendix, not the main paper table.

## K-Radar v1.0 missing-modality inference

Protocol: C+L+R-trained checkpoints, controlled available sensors at inference, `conf_thr=0.3`.

| Method | Sensors | APBEV@0.5 | AP3D@0.5 | APBEV@0.3 | AP3D@0.3 | AP3D@0.7 |
|---|---|---:|---:|---:|---:|---:|
| TaskDec Robust `model_0` | RLC | 88.10 | 67.50 | 88.84 | 88.36 | 22.02 |
| Official ASF v1 ckpt | RLC | 80.33 | 67.19 | 80.78 | 80.31 | 18.85 |
| TaskDec Robust `model_0` | LR | 85.45 | 71.68 | 88.45 | 88.06 | - |
| Official ASF v1 ckpt | LR | 85.75 | 71.98 | 86.35 | 86.02 | - |
| TaskDec Robust `model_0` | RC | 55.52 | 34.59 | 59.35 | 57.62 | 5.38 |
| Official ASF v1 ckpt | RC | 57.27 | 41.87 | 67.49 | 65.69 | 14.59 |
| TaskDec Robust `model_0` | LC | 86.35 | 72.58 | 87.41 | 86.77 | 21.57 |
| Official ASF v1 ckpt | LC | 79.77 | 66.38 | 80.29 | 79.89 | 22.75 |

Takeaway: TaskDec is clearly better than official ASF for RLC, LR at loose IoU, and LC, but RC is weaker. The paper should phrase this as improved availability-aware behavior under most useful sensor combinations, with the RC failure discussed honestly if this table is included.

## K-Radar v2.0 generalization

The existing v2.0 supplementary table remains the right framing:

- Use `DecControlledASFStrong_final` for ours, not the 1000-sample `model_10` subset sweep.
- Use official ASF v2 checkpoint re-evaluated locally at `conf_thr=0.3`.
- Best compact table: AP3D@0.5 under selected adverse weather.

| Method | Class | Total | Overcast | Rain | Light snow | Heavy snow | Selected avg. |
|---|---|---:|---:|---:|---:|---:|---:|
| ASF | Sedan | 52.09 | 53.38 | 46.85 | 59.25 | 49.52 | 52.25 |
| ASF | Bus/Truck | 31.06 | 47.04 | 2.48 | 70.81 | 32.55 | 38.22 |
| Ours | Sedan | 52.14 | 59.62 | 48.30 | 60.75 | 50.49 | 54.79 |
| Ours | Bus/Truck | 33.97 | 49.65 | 5.05 | 75.09 | 39.37 | 42.29 |

Takeaway: this supports cross-version generalization and adverse-weather robustness. It is safer than claiming broad v2.0 SOTA on every metric.

## VoD L+R training

Run directory: `/home/hongsheng/dec_con_asf/vod_taskdec_lr/runs/exp_260905_153718_VoDTaskDecLRAnchor_ep100_gpu3`

Launcher log: `/home/hongsheng/dec_con_asf/vod_taskdec_lr/logs/launcher/vod_taskdec_lr_anchor_ep100_gpu3_260905_153718.log`

Training completed 100 epochs and produced checkpoints `model_0.pt` through `model_99.pt`.

| Selection | Epoch | total_loss | det_loss | rpn_loss_cls | rpn_loss_loc | rpn_loss_dir | patch_dec_loss | gate_loss | class_loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Best by total/det loss | 98 | 2.3313 | 2.2938 | 0.9687 | 1.1923 | 0.1328 | 0.3748 | 1.0544 | 1.0841 |
| Last epoch | 99 | 2.3315 | 2.2941 | 0.9687 | 1.1926 | 0.1328 | 0.3745 | 1.0524 | 1.0841 |

Average epoch time was about 257.6 seconds. Epoch 0 was slower; late epochs were about 240-246 seconds each.

Important caveat: this VoD run currently gives training losses and checkpoints only. It is evidence that the L+R TaskDec pipeline runs on VoD, but it is not yet a detection-performance result. The next required step is to add/run a proper VoD validation mAP evaluation, starting with `model_98.pt` and `model_99.pt`.

## VoD L+R mAP evaluation

Evaluation script: `/home/hongsheng/dec_con_asf/vod_taskdec_lr/eval_taskdec_lr_vod.py`

Metric: L4DR/VoD official 3D AP on the VoD `val` split. L4DR's VoD config maps test mode to `val`, uses `Car/Pedestrian/Cyclist`, and uses `SCORE_THRESH=0.1`; this evaluation follows that default threshold for the main check.

| Checkpoint | Split | Score thresh | Pred/sample | Entire Car | Entire Ped. | Entire Cyc. | Entire mAP | Corridor Car | Corridor Ped. | Corridor Cyc. | Corridor mAP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `model_98.pt` | val | 0.1 | 0.000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `model_99.pt` | val | 0.1 | 0.000 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Diagnostic low-threshold check:

| Checkpoint | Split | Samples | Score thresh | Pred/sample | Entire mAP | Corridor mAP | Note |
|---|---|---:|---:|---:|---:|---:|---|
| `model_98.pt` | val | 64 | 0.01 | 242.000 | 0.00 | 0.00 | all exported scores were about 0.0288 |

Takeaway: the current VoD adaptation is not an effective detection result. Default L4DR-style evaluation outputs no predictions, and low-threshold diagnosis still gives zero AP. This suggests the simplified VoD detector/classification head has not learned useful detection behavior, not merely that the evaluation threshold is too strict.

## Recommendation

- Main K-Radar v1.0 table: keep `TaskDec Robust model_0` as the headline result.
- Main ablation table: include the four component ablations; they are clean and persuasive.
- Appendix hyperparameter table: include control strength and gate-bias sweeps.
- Availability table: include only if space allows, and explicitly note the RC weakness.
- VoD: do not report it as a positive generalization result. The pipeline and evaluator now run, but the current lightweight adaptation gives 0.00 mAP under L4DR-style VoD evaluation.
