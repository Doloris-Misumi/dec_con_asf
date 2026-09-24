# TaskDec ablation plan

Date: 2026-08-31

Scope: TaskDec Robust / TaskAwareDecControlledA2Fusion on K-Radar, mainly v1.0 Sedan with `conf_thr=0.3`.

## What the ablation should prove

The ablation should not try to prove every hyperparameter is optimal. It should prove four core claims:

1. The gain is not from changing encoders or the detection head; it comes from the fusion controller on ASF canonical patch tokens.
2. Decoupling matters: separating common target evidence and modality-specific evidence gives useful supervision/control.
3. Control matters: the decoupled features are useful because they control foreground gating, sensor reliability, and task context, not only because they add auxiliary losses.
4. The method remains meaningful under sensor availability changes and difficult weather.

## Main ablation table recommended for the paper

Use K-Radar v1.0, Sedan, C+L+R, `conf_thr=0.3`. Report at least `AP3D@0.3`, `AP3D@0.5`, `APBEV@0.3`, `APBEV@0.5`. If space allows, also show `AP3D@0.7`.

| Row | Variant | Purpose | How to implement / status |
|---|---|---|---|
| 1 | ASF baseline | Base canonical patch fusion without TaskDec | Existing official released checkpoint re-eval: `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.md`. Local ASF repro also exists but is score-calibration sensitive. |
| 2 | + PatchDec only | Tests whether common/unique decomposition itself helps | Existing v2-style development result exists as `PatchDec first`; clean v1.0 full result is not clearly available. Recommended to rerun only if time permits. |
| 3 | + foreground gate | Tests whether object-aware patch selection helps | Existing v2-style `FgGated` / `FgGatedSelective` results exist; clean v1.0 full result is not clearly available. Optional. |
| 4 | + sensor reliability control, no task context | Tests whether decoupled features should control sensor weights | Existing `DecControlledASFStrong/Gentle` on v2-style setting. A clean v1.0 version would be stronger evidence. |
| 5 | + task-aware context, no query/output injection | Tests whether task context supervision alone helps | Partly covered by `KVOnlyStable`, but that run is affected by late-epoch collapse. Better as appendix unless rerun cleanly. |
| 6 | Full TaskDec Robust | Final model | Existing main row: `results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.md`. |

If the paper has room for only one compact component table, use rows 1, 4, 5, 6. Rows 2 and 3 explain development history but are less essential.

## Minimal additional ablations worth running

These are the most efficient clean ablations because most can be done by config toggles.

| Priority | Variant | Config change | What it proves |
|---:|---|---|---|
| 1 | w/o sensor reliability weighting | Set `DEC_CONTROL_STRENGTH: 0.0` | Shows dynamic per-patch sensor weighting is useful beyond adding Dec residual/context. |
| 2 | w/o task context injection | Set `DEC_CONTROL_QUERY_STRENGTH: 0.0`, `DEC_CONTROL_FUSED_RES_STRENGTH: 0.0`; optionally `DEC_CONTROL_CLASS_LOSS_WEIGHT: 0.0` | Shows the task-aware part matters, not just decoupled reliability control. |
| 3 | w/o decoupling supervision | Set `PATCH_DEC_LAMBDA_DECOUPLE: 0.0`, `PATCH_DEC_LAMBDA_COMMON: 0.0`, `PATCH_DEC_LAMBDA_UNIQUE: 0.0` | Shows common/unique losses are not decorative. |
| 4 | w/o foreground gate | Set `DEC_CONTROL_GATE_MIN: 1.0`, `DEC_CONTROL_GATE_MAX: 1.0`, `DEC_CONTROL_GATE_LOSS_WEIGHT: 0.0` | Shows foreground-aware control is better than controlling all patches equally. |
| 5 | w/o Dec residual token | Set `DEC_CONTROL_USE_DEC_TOKEN: False` | Separates "control by scaling/context" from "adding common+unique residual". |
| 6 | query-only vs output-only context | Run one with `FUSED_RES_STRENGTH: 0`, one with `QUERY_STRENGTH: 0` | Shows where task context is most useful. Optional unless reviewers ask. |

Recommended minimal set before submission: priorities 1 to 4. That gives a clean story without exploding the experiment count.

## Existing experiments that can be used as ablations

### 1. ASF vs TaskDec full model

This is the main method-level ablation.

| Method | Sensors | Conf | APBEV@0.3 | AP3D@0.3 | APBEV@0.5 | AP3D@0.5 | Source |
|---|---|---:|---:|---:|---:|---:|---|
| Official ASF released ckpt re-eval | C+L+R | 0.3 | 80.78 | 80.31 | 80.33 | 67.19 | `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.md` |
| TaskDec Robust `model_0` | C+L+R | 0.3 | 88.84 | 88.36 | 88.10 | 67.50 | `results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.md` |

Use this for the main claim, but phrase it as released ASF checkpoint re-evaluated under the same `conf_thr=0.3` protocol.

### 2. TaskDec strength / gate openness sensitivity

These are useful as a parameter/control sensitivity ablation.

| Variant | Key change | APBEV@0.3 | AP3D@0.3 | APBEV@0.5 | AP3D@0.5 | Note |
|---|---|---:|---:|---:|---:|---|
| MoreOpenGate `model_2` | gate init bias `-0.9` | 89.00 | 88.51 | 80.35 | 67.80 | strongest loose AP3D row among TaskDec variants |
| Robust `model_0` | balanced strong control | 88.84 | 88.36 | 88.10 | 67.50 | best main-table choice because BEV@0.5 is strong |
| StrongerControl `model_4` | stronger control/context | 89.06 | 80.51 | 80.42 | 68.06 | best strict AP3D@0.5, weaker AP3D@0.3 |
| Stable `model_0` | scheduled/weaker late control | 88.98 | 88.54 | 80.30 | 67.24 | good AP3D@0.3 but not stronger than main row overall |

Interpretation: control strength affects the tradeoff between loose foreground recovery and strict localization. This should be appendix or a short sensitivity paragraph, not the main component ablation.

### 3. Query/output context ablation

`TaskDecControlKVOnlyStable_v1_0` disables task-context query/output injection:

- `DEC_CONTROL_QUERY_STRENGTH: 0.0`
- `DEC_CONTROL_FUSED_RES_STRENGTH: 0.0`

Existing final result:

| Variant | APBEV@0.3 | AP3D@0.3 | APBEV@0.5 | AP3D@0.5 | Source |
|---|---:|---:|---:|---:|---|
| TaskDec Stable final | 86.74 | 81.26 | 83.61 | 40.82 | `results/exp_260817_212526_TaskDecControlStable_v1_final/summary_conf0.3.md` |
| KVOnlyStable final | 84.55 | 78.27 | 72.38 | 35.44 | `results/exp_260817_212746_TaskDecControlKVOnlyStable_v1_final/summary_conf0.3.md` |

Use cautiously: it supports that query/output task context helps, but both late checkpoints show training collapse. A clean early-checkpoint or rerun would be more defensible.

### 4. Sensor availability ablation: C+L+R vs L+R inference

This is a strong appendix table because it matches the ASF availability-aware story.

| Method | Inference sensors | APBEV@0.3 | AP3D@0.3 | APBEV@0.5 | AP3D@0.5 | Source |
|---|---|---:|---:|---:|---:|---|
| Official ASF ckpt | L+R | 86.35 | 86.02 | 85.75 | 71.98 | `results/v1_lr_conf0_3_sota_comparison_260828.md` |
| TaskDec Robust `model_0` | L+R | 88.45 | 88.06 | 85.45 | 71.68 | `results/v1_lr_conf0_3_sota_comparison_260828.md` |

Recommended wording: this is an "availability evaluation" from C+L+R-trained checkpoints with camera unavailable at inference, not a pure L+R-trained detector.

### 5. Weather / condition analysis

Existing file: `results/robust_v1_model0_weather_delta_260820.md`.

Useful message:

- RLC gains are clearest in rain for both BEV and 3D.
- LR gains are smaller but more broadly positive across normal, rain, sleet, lightsnow, and heavysnow.
- Do not claim every weather condition improves uniformly.

### 6. Protocol sensitivity

Existing file: `results/asf_v1_conf_protocol_audit_260828.md`.

Use as appendix, not as a method ablation. It explains why the main table uses `conf_thr=0.3` and why ASF paper/default numbers should not be mixed directly with confidence-filtered rows.

## Experiments that are useful but not necessary

| Experiment | Value | Why optional |
|---|---|---|
| C+L, C+R, L+R, single-modality inference | Strong availability story | More eval jobs, but no retraining needed if ASF availability path works. |
| v2.0 component ablation | Shows multi-class/wider-ROI behavior | v2.0 Bus behavior is noisier; better appendix. |
| VoD external dataset | Generalization | Engineering cost is high and not needed for the core K-Radar/ASF claim. |
| Random/energy patch selection vs GT foreground selection | Tests training target design | Interesting, but less central than the four minimal toggles above. |
| Parameter/FLOPs/runtime | Shows overhead is small | Useful reviewer-friendly table; can be measured once from model summary. |

## Suggested paper table layout

### Main paper table: Component ablation

Columns:

- Variant
- Decoupling loss
- Foreground gate
- Sensor reliability
- Task context
- APBEV@0.3
- AP3D@0.3
- APBEV@0.5
- AP3D@0.5

Rows:

1. ASF
2. w/o decoupling supervision
3. w/o foreground gate
4. w/o sensor reliability
5. w/o task context
6. Full TaskDec Robust

### Appendix table A: Control sensitivity

Rows: Balanced, Robust, MoreOpenGate, StrongerControl, Stable.

### Appendix table B: Availability

Rows: C+L+R, L+R, optionally C+L, C+R, L, R.

### Appendix table C: Weather

Rows: normal, overcast, fog, rain, sleet, lightsnow, heavysnow.

## Bottom line

The current local experiments are enough to write a convincing main result and several appendix analyses. For a clean ablation section, however, the most defensible extra work is a small set of controlled v1.0 toggles around the final Robust config:

1. `DEC_CONTROL_STRENGTH=0`
2. no query/output task context
3. no decoupling losses
4. gate fixed to one

That set directly tests the four claims behind TaskDec without turning the paper into a hyperparameter diary.
