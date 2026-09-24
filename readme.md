# ObjDec — Decoupling to Fuse

**Decoupling to Fuse: Learning Shared and Modality-Specific Representations
for Multi-Sensor 3D Object Detection**

ObjDec learns shared and modality-specific representations from spatially
corresponding camera, LiDAR, and 4D-radar features, and uses object-related
information to guide their fusion. This research workspace builds on K-Radar /
ASF and contains adaptations to V2X-Radar-V and View-of-Delft (VoD).

The paper method name is **ObjDec**. `TaskDec` remains the engineering name in
classes, configuration files, scripts, and historical experiment records; these
names are preserved to keep existing experiments reproducible.

**Collaboration snapshot: 2026-09-24.** Start with the
[图表与论文协作指南](docs/OBJDEC_COLLABORATION.md). This is an evolving research
workspace with drafts and recorded experiments, rather than a finished paper
release. Historical filenames retain their creation dates even when revised.

## Paper and Figure Entry Points

| Material | Current entry |
| --- | --- |
| Abstract | [Bilingual abstract draft](results/taskdec_abstract_initial_draft_260917.md) |
| Introduction | [Bilingual introduction](results/taskdec_introduction_bilingual_initial_260917.md) |
| Related work | [Bilingual related work](results/taskdec_related_work_bilingual_initial_260917.md) · [Recent BibTeX entries](results/taskdec_recent_references_2025_2026_260917.bib) |
| Method | [Bilingual method](results/taskdec_methods_bilingual_initial_260917.md) |
| Experiments | [Bilingual experiments](results/objdec_experiments_bilingual_initial_260919.md) |
| Appendix | [Bilingual appendix](results/objdec_appendix_bilingual_initial_260920.md) · [Writing plan](results/objdec_appendix_writing_plan_260920.md) |
| Architecture | [Verified signals and wiring](analysis_exports/objdec_architecture_redesign_260922/CENTERED_REVISION.md) · [Current hand-drawn reference](cb40887aca547bfc940ba77ab865ed6e.png) |
| Motivation | [Real K-Radar sample variants](analysis_exports/objdec_motivation_new_samples_260922/README.md) |
| PCA / gate figures | [Blue–green–purple figure collection](analysis_exports/objdec_visuals_blue_green_purple_260923/README.md) |
| Architecture insets | [Points-only PCA assets](analysis_exports/objdec_pca_points_only_260924/README.md) · [Object-context vector example](analysis_exports/objdec_context_vector_example_260924/README.md) |
| Detection examples | [Figure 4/5 notes](analysis_exports/objdec_fig4_fig5_260919/README.md) · [Paired detection preview](analysis_exports/objdec_fig4_fig5_260919/fig5_asf_objdec_detection_draft.png) |

Use the latest result records below when updating draft tables; earlier prose
and intermediate figures can still contain superseded terminology or pending
items. The collaboration guide identifies these boundaries explicitly.

## Highlights

- Object-guided decoupled patch fusion for camera, LiDAR, and 4D radar on
  K-Radar.
- Representation constraints within GT-defined foreground patches during training.
- Predicted spatial gates and bounded modality scaling for patch-level fusion.
- Object-context increments for attention queries and fused tokens.
- K-Radar v1.0 / v2.0 experiment configurations, evaluation utilities, and
  analysis scripts.
- V2X-Radar-V camera/LiDAR/radar and LiDAR/radar adaptations, plus VoD experiments.

## Repository Layout

```text
configs/                       K-Radar experiment configs
configs/v1_0/                  Original ASF-style K-Radar v1.0 configs
models/fuser/                  ASF and TaskDec fusion modules
models/skeletons/              Integrated detector skeletons and loss routing
pipelines/                     K-Radar train / validation / KITTI-style eval
main_train_patch_dec.py        Main entry for K-Radar TaskDec training
eval_model_full.py             Full validation for a selected checkpoint
eval_ckpt_subset.py            Fast checkpoint sweep on a validation subset
scripts/                       Launchers and result collection helpers
tools/analysis/                Visualization, PCA, gate, and table utilities
paper_figures/                 Figure generation scripts
v2x_taskdec/                    V2X data, geometry, models, training and evaluation
vod_taskdec_lr/                Lightweight VoD L+R TaskDec sandbox
vod_taskdec_native/            Native VoD PP-Concat / TaskDec-PP adaptation
results/                       Manuscript drafts, protocol audits and result tables
analysis_exports/              Selected figures, compact reports and experiment scripts
docs/OBJDEC_COLLABORATION.md    Paper/figure collaboration index
docs/                          Original K-Radar documentation assets
```

This update includes selected rendered figures, compact result summaries, and
experiment scripts. Model weights, raw datasets, numerical feature caches, and
new per-frame prediction dumps remain local. Some older evaluation text files
already exist in repository history.

## Method Overview

The K-Radar pipeline follows the ASF-style sensor fusion skeleton:

1. A camera encoder, LiDAR encoder, and 4D radar encoder produce BEV features.
2. Each feature map is projected into a unified canonical patch space.
3. ASF-style attention fuses modality patches into a shared BEV feature.
4. A detection head predicts 3D bounding boxes.

ObjDec organizes representation learning and fusion in this local patch space:

1. Independent learned projections map the same input token to shared `c` and
   modality-specific `u` representations. There is no `c + u = input` constraint.
2. Foreground representation losses encourage shared agreement, limit excessive
   cross-modal similarity of specific features, and separate `c` from `u`.
3. At each patch, pooling across modalities gives
   `h = concat(mean(c), mean(abs(u)))`. Separate heads predict foreground gate
   `g` and objectness. In the single-class K-Radar model, objectness is embedded
   into a 256-dimensional context vector `z`.
4. Modality scoring uses each modality's input, `c`, `u`, and deviation from the
   shared mean. Softmax contributions `alpha` become bounded scaling factors
   `w`; the controlled token is `w * (t + lambda * g * (c + u))`.
5. Learned queries receive a gated context increment. Cross-modal attention reads
   controlled tokens as K/V, then receives an output context increment before
   feature transformation and BEV reconstruction.

GT-derived labels are used only for training losses; gates and objectness are
predicted from features at both training and inference. The K-Radar training
objective also retains ASF sensor-combination supervision (SCL). Dataset
adaptations and auxiliary objectives are documented separately.

Recent fixed-weight interventions support the importance of spatial gate
correspondence, while query/output context increments have very small inference
effects for the evaluated K-Radar checkpoint. See the
[complete intervention results](results/objdec_kradar_v1_interventions_results_260924.md);
these interventions are distinct from retrained component ablations.

The main implementation lives in:

- `models/fuser/patch_dec_a2_fusion.py`
- `models/fuser/a2_fusion.py`
- `models/skeletons/fusion_base_integrated.py`
- `pipelines/pipeline_detection_v1_0.py`

## K-Radar Experiments

Environment setup is inherited from the upstream projects; see
[detection setup](docs/detection.md) and the
[native VoD environment notes](vod_taskdec_native/L4DR_taskdec/docs/INSTALL.md).
Training requires the relevant licensed datasets, pretrained encoders, and
compiled operators. Existing launchers contain development-machine paths that
must be adapted on another machine.

The main K-Radar v1.0 TaskDec configuration is:

```text
configs/ASF_task_dec_controlled_robust_v1_0.yml
```

Representative ablation and hyper-parameter configs include:

```text
configs/ASF_task_dec_controlled_robust_v1_0_wo_decoupling_supervision.yml
configs/ASF_task_dec_controlled_robust_v1_0_wo_foreground_gate.yml
configs/ASF_task_dec_controlled_robust_v1_0_wo_sensor_reliability.yml
configs/ASF_task_dec_controlled_robust_v1_0_wo_task_context.yml
configs/ASF_task_dec_controlled_robust_v1_0_strength05.yml
configs/ASF_task_dec_controlled_robust_v1_0_strength10.yml
configs/ASF_task_dec_controlled_robust_v1_0_gate_bias_m06.yml
configs/ASF_task_dec_controlled_robust_v1_0_gate_bias_m18.yml
```

K-Radar v2.0 contains both TaskDec configurations and the earlier DecControlled
Strong variant used in the supplementary table. They are separate model variants:

```text
configs/ASF_task_dec_controlled_robust_v2_0.yml
configs/ASF_deccontrolled_strong_v2_0_resume20.yml
```

Example training command:

```bash
python main_train_patch_dec.py \
  --config ./configs/ASF_task_dec_controlled_robust_v1_0.yml \
  --gpu 0 \
  --num-workers 0 \
  --final-conf-thr 0.0,0.3
```

Fast checkpoint sweep:

```bash
python eval_ckpt_subset.py \
  --config ./configs/ASF_task_dec_controlled_robust_v1_0.yml \
  --exp-dir ./logs/YOUR_EXPERIMENT_DIR \
  --gpu 0 \
  --num-subset 1000 \
  --confs 0.3 \
  --epochs all \
  --num-workers 0
```

Full validation:

```bash
python eval_model_full.py \
  --config ./configs/ASF_task_dec_controlled_robust_v1_0.yml \
  --model ./logs/YOUR_EXPERIMENT_DIR/models/model_0.pt \
  --gpu 0 \
  --epoch 0 \
  --confs 0.0,0.3 \
  --conditional \
  --num-workers 0
```

## View-of-Delft Adaptation

Two VoD workspaces are included.

`vod_taskdec_lr/` is a lightweight LiDAR+Radar sandbox. It is useful for smoke
tests and quick checks that TaskDec can be moved away from K-Radar-specific
inputs.

```bash
# Run from the repository root after configuring local data paths.
CUDA_VISIBLE_DEVICES=0 python -u -m vod_taskdec_lr.train_taskdec_lr_detection \
  --config vod_taskdec_lr/configs/taskdec_lr_anchor_train.yml \
  --gpu 0
```

`vod_taskdec_native/L4DR_taskdec/` is the native OpenPCDet-style VoD adaptation
used for PP-Concat and TaskDec-PP comparisons. The key model configs are:

```text
vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/PP_Concat.yaml
vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/TaskDec_PP.yaml
vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/TaskDec_PP_MildS05AuxHalf.yaml
vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/TaskDec_PP_WarmPPConcat_MildS05AuxHalf.yaml
vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920.yaml
vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Anchors_260921.yaml
```

Latest VoD results and the distinction between official EAA/DC and KITTI AP_R40
are recorded in the [VoD result tables](results/objdec_vod_current_tables_260922.md).
VoD is currently planned as appendix evidence.

## V2X-Radar-V Adaptation

- [Core code](v2x_taskdec/): data loading, sensor geometry, detector, training,
  and evaluation.
- [0.16 m matched experiments](analysis_exports/v2x_grid016_260918/run.py):
  ObjDec and Concat, 2×2 patches and an 80-epoch budget.
- [Fusion controls](analysis_exports/v2x_grid016_controls_260919/run.py):
  ASF-style C+L+R and ObjDec-LR.
- [Local L4DR adaptation](analysis_exports/v2x_l4dr_260917/).
- [Final local result table](results/objdec_v2x_current_total_table_260923.md)
  and [paper table organization](results/objdec_v2x_paper_comparison_260923.md).

Local experiments use 8,391 training frames, 1,487 deduplicated validation
frames, and 1,486 deduplicated test frames. Selection uses validation mean
strict Moderate 3D AP, with final AP_R40 on the test split; class IoUs are
0.7/0.5/0.5. Public paper results use a different evaluation collection/protocol
and are kept in a separate reference panel; see the
[comparability audit](results/objdec_v2x_public_protocol_comparability_260919.md).

These scripts preserve experiment-specific configuration and hash checks.
They require local datasets, upstream dependencies and initialization artifacts;
cloning this repository alone does not reproduce a full training run.

## Current Result Records

| Evidence | Authoritative local record |
| --- | --- |
| K-Radar v1 main comparison | [Main table](results/paper_main_table_kradar_v1_conf0_3_draft_260901.md) · [Protocol audit](results/taskdec_main_protocol_audit_vs_kradar_official_260910.md) |
| K-Radar v1 inference interventions | [Eight cases, overall and all-weather results](results/objdec_kradar_v1_interventions_results_260924.md) |
| K-Radar v2 matched training | [Training and results](results/taskdec_v2_matched_training_260915.md) |
| Missing modalities / sensor degradation | [v1 completion](analysis_exports/taskdec_v1_availability_completion_260918/results.md) · [v2 comparison](results/taskdec_v2_availability_vs_asf_table3_260918.md) |
| V2X inference studies | [Results and interpretation](results/objdec_inference_only_results_and_paper_value_260923.md) |
| VoD | [Official EAA/DC tables](results/objdec_vod_current_tables_260922.md) |

Compare checkpoints and methods only within the stated protocol. In particular,
K-Radar AP11, V2X AP_R40, and VoD EAA/DC are different evaluation settings.

## Analysis Utilities

Useful analysis scripts include:

```text
tools/analysis/export_taskdec_patch_pca.py
tools/analysis/plot_taskdec_weather_pca.py
tools/analysis/export_taskdec_bev_gate.py
tools/analysis/find_taskdec_sensor_cases.py
tools/analysis/make_taskdec_paper_visuals.py
tools/analysis/eval_l4dr_kradar_v1_conditional.py
```

Efficiency and availability scripts:

```text
benchmark_inference_speed.py
benchmark_l4dr_inference_speed.py
scripts/collect_availability_table_260902.py
scripts/collect_efficiency_table_260902.py
scripts/launch_taskdec_availability_eval_260902.sh
scripts/launch_official_asf_availability_eval_260902.sh
```

## Data and Checkpoints

This synchronization does not upload datasets, pretrained backbones, training
checkpoints, raw prediction caches, or feature arrays. Selected paper figures
contain rendered dataset examples with provenance notes alongside them.

Expected local resources in the original development environment included:

```text
/home/hongsheng/K-Radar-main/pretrained
/home/hongsheng/vod/view_of_delft_PUBLIC
```

The root `.gitignore` excludes common training artifacts such as `logs/`,
`output/`, `checkpoints/`, `ckpts/`, `runs/`, `evals/`, `*.pt`, `*.pth`,
`*.ckpt`, `*.npz`, `*.npy`, and `*.pkl`.

On a fresh clone, collaborators can read the drafts and edit existing SVG/PNG/PDF
figures without a GPU. Regenerating data-driven PCA/gate/detection figures
requires the original caches; their sources are recorded in figure READMEs and
manifests. The object-context schematic can be regenerated without those caches:

```bash
python analysis_exports/objdec_context_vector_example_260924/draw_context_example.py
```

Some historical notes link absolute paths on the development machine. Use the
relative links in this README and the collaboration guide for browser navigation.

## Acknowledgements

This repository is a research adaptation of the K-Radar / ASF codebase and also
contains a VoD adaptation workspace based on OpenPCDet/L4DR-style components.
Please cite and acknowledge the original K-Radar, ASF, OpenPCDet, and L4DR
projects when using the corresponding code paths, datasets, or baselines.

Key upstream resources:

- K-Radar: 4D Radar Object Detection for Autonomous Driving in Various Weather
  Conditions.
- Availability-aware Sensor Fusion via Unified Canonical Space.
- OpenPCDet.
- L4DR / LiDAR-4D radar fusion code and VoD evaluation components.

## License

This repository inherits code from multiple research codebases. Check the
corresponding upstream licenses before redistribution or commercial use. Dataset
licenses and access restrictions are governed by the original K-Radar and
View-of-Delft providers.
