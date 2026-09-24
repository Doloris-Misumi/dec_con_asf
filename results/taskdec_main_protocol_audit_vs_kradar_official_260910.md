# TaskDec Main Protocol Audit vs. Official K-Radar

Date: 2026-09-10

Update (2026-09-12): the [v2 weather/Total audit](taskdec_v2_l4dr_weather_total_and_eval_protocol_audit_260912.md) identifies a concrete evaluator difference between v2 Strong/ASF (all 41 precision samples; z_center=0.5) and current public L4DR code (11 selected samples; z_center=1.0). Matching confidence thresholds alone does not establish full protocol equivalence. This difference does not automatically apply to the v1 main table: its current config inheritance leaves `is_validation_updated` unset, selecting the legacy evaluator by default. Published rows still require the label/threshold qualifications below.

## Short Conclusion

The current TaskDec main experiment should be described as:

> K-Radar official sensor-fusion benchmark v1.0: narrow RoI, Sedan-only, label v1.0, Camera+LiDAR+4D Radar, official train/test split; we report APBEV/AP3D at IoU 0.3/0.5 under a unified confidence-filtered evaluation with `conf_thr=0.3`.

It is not the official K-Radar v2.0 wide-RoI multi-class protocol. It is also not exactly the same configuration as L4DR v1.1, although L4DR is still a relevant published K-Radar Sedan/narrow-RoI reference row.

## Local TaskDec Main Setting

Primary config:

- `/home/hongsheng/dec_con_asf/configs/ASF_task_dec_controlled_robust_v1_0.yml`
- Base config: `/home/hongsheng/dec_con_asf/configs/v1_0/cfg_A2F_scl_final.yml`
- Main result: `/home/hongsheng/dec_con_asf/results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.md`

Key local evidence:

| Item | Local setting | Evidence |
|---|---|---|
| Dataset loader | `KRadarFusion_v1_0` | base config line 28 |
| Split | `resources/split/train.txt`, `resources/split/test.txt` | base config line 34; override line 11 |
| Label version | `v1_0` | base config line 38; override line 15 |
| Sensors | front camera + 64-line LiDAR + sparse 4D radar | base config lines 39-46 |
| RoI | `[0, -6.4, -2, 72, 6.4, 6.0]` | base config lines 98-105 |
| Classes | Sedan enabled; Bus/Truck and others disabled | base config lines 119-132 |
| Post score threshold | `SCORE_THRESH: 0.1` | base config lines 239-244 |
| Logged eval confidence thresholds | `[0.0, 0.3]` | base config line 282 |
| Logged IoUs | `[0.7, 0.5, 0.3]` | base config line 283 |
| Evaluated class | `['Sedan']` | base config line 297 |
| Main table result | `conf=0.3`, Sedan APBEV/AP3D | summary lines 3 and 7-11 |

TaskDec Robust `model_0` under the paper-facing protocol:

| Class | BEV@0.7 | BEV@0.5 | BEV@0.3 | 3D@0.7 | 3D@0.5 | 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| Sedan | 62.63 | 88.10 | 88.84 | 22.04 | 67.50 | 88.36 |

Implementation note: the override config changes local data paths and some loading modes, e.g. `cam_dir.load: ori` and `ldr64.processed: False`, to match the local dataset layout. These are data-path/loading adaptations, not a change to the benchmark definition. The benchmark-defining fields remain label v1.0, narrow RoI, Sedan-only, and the official split.

## Official K-Radar Comparison

Official source pages:

- Sensor fusion guide: https://github.com/kaist-avelab/K-Radar/blob/main/docs/sensor_fusion.md
- K-Radar README sensor-fusion section: https://github.com/kaist-avelab/K-Radar
- Dataset label revision note: https://github.com/kaist-avelab/K-Radar/blob/main/docs/dataset.md
- Official ASF v2.0 config: https://raw.githubusercontent.com/kaist-avelab/K-Radar/main/configs/ASF_v2_0_final.yml
- Official argument evaluator: https://raw.githubusercontent.com/kaist-avelab/K-Radar/main/main_cond_0_args.py

Official K-Radar docs define:

- Benchmark v1.0: narrow RoI, single class, label v1.0; reported values are AP3D/APBEV at IoU=0.3 for Sedan.
- Benchmark v2.0: wide RoI, multiple classes, label v2.0; reported values are AP3D/APBEV at IoU=0.3 for Sedan and Bus/Truck.
- The official ASF v2.0 config explicitly uses wide RoI `[0, -16, -2, 72, 16, 7.6]`, label `v2_0`, and enables both Sedan and Bus/Truck.
- The dataset document states that v2.0 is a revised label-quality version and that the previous label is v1.0; v2.1 adds visibility discrimination.

Therefore, our main TaskDec table aligns with official K-Radar benchmark v1.0, not v2.0.

## Confidence Threshold Issue

The official K-Radar sensor-fusion guide reports ASF v1.0 only at IoU=0.3. The K-Radar README also reports ASF as 87.4 AP3D@IoU=0.3 and 73.6 AP3D@IoU=0.5, but does not state a confidence threshold.

Local ASF official-log audit:

- `/home/hongsheng/dec_con_asf/results/asf_v1_conf_protocol_audit_260828.md`

The downloaded official ASF logs show:

| Run | conf_thr | BEV@0.5 | BEV@0.3 | 3D@0.5 | 3D@0.3 |
|---|---:|---:|---:|---:|---:|
| Official ASF `exp250219` | 0.0 | 87.17 | 88.59 | 73.58 | 87.42 |
| Official ASF `exp250303` | 0.0 | 86.97 | 88.59 | 72.95 | 87.34 |
| Official ASF `exp250303` | 0.3 | 80.33 | 80.78 | 67.19 | 80.31 |
| TaskDec Robust `model_0` | 0.3 | 88.10 | 88.84 | 67.50 | 88.36 |

Interpretation:

- The official ASF headline values align with the released official logs at `conf_thr=0.0`.
- Our main comparison intentionally uses `conf_thr=0.3`, because RTNH/3D-LRF/L4DR-style K-Radar public evaluations commonly use confidence-filtered evaluation around this threshold.
- This should be framed as a unified evaluation protocol, not as an accusation of intent.

Recommended paper note:

> We evaluate all locally available checkpoints with the same confidence-filtered K-Radar protocol (`conf_thr=0.3`). Since the official ASF table does not explicitly report the confidence threshold and its released logs match the default `conf_thr=0.0` scale, we additionally re-evaluate the released ASF checkpoint at `conf_thr=0.3` for a protocol-consistent baseline.

Do not claim that TaskDec beats the official ASF reported AP3D@0.5=73.6; under `conf_thr=0.0`, TaskDec Robust is stronger at AP3D@0.3 but lower at AP3D@0.5 than the official ASF headline.

## L4DR Boundary

Local L4DR audit:

- `/home/hongsheng/dec_con_asf/results/l4dr_reproduction_status_260910.md`

Important nuance:

- L4DR public `cfg_PP_L4DR_v1.1.yml` uses the same narrow RoI shape `[0, -6.4, -2, 72, 6.4, 6.0]`, Sedan-only evaluation, and `conf_thr=0.3`.
- However, the public config has `label_version: v2_1` and expects processed radar sparse tensors under `sparse_radar_tensor_wide_range/rtnh_wider_1p_1`.
- A forced local run with `label_version=v1_0` and fallback sparse data did not reproduce the public L4DR log, so it should be treated as a protocol-mismatch diagnostic.

Paper-facing implication:

- It is safe to include L4DR as a published/public-log reference.
- It is not safe to say L4DR and TaskDec were re-run under exactly identical local data/label preprocessing unless the matching revised labels and sparse tensors are obtained/regenerated.

## Suggested Main-Table Caption

> Results on the K-Radar official v1.0 sensor-fusion benchmark (narrow RoI, Sedan-only, label v1.0). We report APBEV/AP3D at IoU 0.3 and 0.5 under `conf_thr=0.3`. ASF is evaluated from the released official checkpoint under the same confidence-filtered protocol; other published methods are listed from their public papers/logs when their released code/checkpoints are not protocol-aligned for local re-evaluation.

## Suggested Appendix Protocol Paragraph

> K-Radar contains multiple label and benchmark variants. Following the official sensor-fusion benchmark v1.0, our main K-Radar experiments use label v1.0, a narrow driving-corridor RoI `[0,72] x [-6.4,6.4] x [-2,6]`, and Sedan-only evaluation. This differs from K-Radar benchmark v2.0, which uses a wider RoI and evaluates both Sedan and Bus/Truck using revised label v2.0. We report the full IoU sweep available in our evaluator and use `conf_thr=0.3` as the unified confidence-filtered comparison setting.
