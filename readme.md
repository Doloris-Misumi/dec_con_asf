# TaskDec-Controlled ASF

This repository contains research code for task-aware decoupled multimodal
fusion on 3D object detection. The main implementation is built on top of the
K-Radar / ASF codebase and studies how decoupled patch representations can
control sensor fusion in a unified canonical BEV patch space.

The core idea is to use the ASF canonical patch space as a common interface,
then introduce a TaskDec controller that decomposes each modality patch into
shared task information and modality-specific information. The resulting
representations are used to predict foreground gates, sensor reliability
weights, and class context, which dynamically modulate patch-level sensor
fusion.

## Highlights

- Task-aware decoupled patch fusion for camera, LiDAR, and 4D radar on
  K-Radar.
- Foreground-gated decoupling supervision for canonical BEV patches.
- Patch-level sensor reliability control over ASF-style multi-head fusion.
- Class-context modulation for task-aware query and fused-token updates.
- K-Radar v1.0 / v2.0 experiment configurations, evaluation utilities, and
  analysis scripts.
- View-of-Delft LiDAR+Radar adaptation sandboxes for cross-dataset
  generalization experiments.

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
vod_taskdec_lr/                Lightweight VoD L+R TaskDec sandbox
vod_taskdec_native/            Native VoD PP-Concat / TaskDec-PP adaptation
docs/                          Original K-Radar documentation assets
```

Training logs, checkpoints, raw datasets, generated evaluation outputs, and
large analysis exports are intentionally not tracked in this repository.

## Method Overview

The K-Radar pipeline follows the ASF-style sensor fusion skeleton:

1. A camera encoder, LiDAR encoder, and 4D radar encoder produce BEV features.
2. Each feature map is projected into a unified canonical patch space.
3. ASF-style attention fuses modality patches into a shared BEV feature.
4. A detection head predicts 3D bounding boxes.

TaskDec adds a controller between canonical patch projection and patch fusion:

1. Each modality patch token is split into a common component and a unique
   component.
2. Common features are encouraged to align across modalities; unique features
   are encouraged to preserve modality-specific residual information.
3. The decoupled features predict foreground gates and per-modality reliability
   scores.
4. The controller rescales the patch-level key/value tokens and injects class
   context into the fusion process.
5. Detection, SCL, decoupling, foreground gate, and class-context losses are
   combined during training.

The main implementation lives in:

- `models/fuser/patch_dec_a2_fusion.py`
- `models/fuser/a2_fusion.py`
- `models/skeletons/fusion_base_integrated.py`
- `pipelines/pipeline_detection_v1_0.py`

## K-Radar Experiments

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

The main K-Radar v2.0 generalization configuration is:

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
cd /home/hongsheng/dec_con_asf
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
```

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

This repository does not include K-Radar, View-of-Delft, pretrained backbones,
training checkpoints, logs, or evaluation dumps.

Expected local resources in the original development environment included:

```text
/home/hongsheng/K-Radar-main/pretrained
/home/hongsheng/vod/view_of_delft_PUBLIC
```

The root `.gitignore` excludes common training artifacts such as `logs/`,
`output/`, `checkpoints/`, `ckpts/`, `runs/`, `evals/`, `*.pt`, `*.pth`,
`*.ckpt`, `*.npz`, `*.npy`, and `*.pkl`.

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
