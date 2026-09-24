# VoD experiment design for TaskDec / ASF

Date: 2026-08-28

## Short recommendation

Do a VoD experiment only as an external generalization add-on. The right target is not external leaderboard SOTA. The right target is:

> On View-of-Delft, under identical encoders, detection head, ROI, and evaluation protocol, TaskDec improves an ASF-style canonical fusion baseline.

The best first version is LiDAR + radar (`L+R`) on VoD validation. Add camera only after the `L+R` path is stable.

## Why VoD is worth trying

VoD is a good external test because it changes the radar representation while preserving the multi-sensor 3D detection problem:

- K-Radar uses 4D radar tensor / sparse tensor features.
- VoD provides 3+1D radar point clouds with `[x, y, z, RCS, v_r, v_r_compensated, time]`.
- VoD also has 64-layer LiDAR, camera, calibration, KITTI-like structure, 3D boxes, and an official detection benchmark.

This lets the paper say:

> TaskDec is not tied to K-Radar's RTNH radar tensor encoder; it can control ASF-style canonical fusion when the radar branch is a point-cloud encoder.

## Minimal publishable experiment

Use VoD validation, not the hidden test server, for the first paper table.

| Setting | Baseline | Ours | Purpose |
|---|---|---|---|
| `L` only | VoD LiDAR encoder | same | sanity check |
| `R` only | VoD radar encoder | same | sanity check |
| `L+R` | `A2Fusion` | `TaskAwareDecControlledA2Fusion` | main external generalization |
| `L+R` ablation | `PatchDec`, `DecControlled`, `TaskDec` | same encoders/head | mechanism evidence |
| availability | evaluate `L`, `R`, `L+R` from the same fusion checkpoint | same | availability-aware claim |

Report official VoD metrics:

- AP/mAP for Car, Pedestrian, Cyclist.
- BEV and 3D AP.
- Entire annotated area and driving corridor if the official devkit returns both.

Do not compare heavily against VoD leaderboard SOTA unless the implementation is mature. For this paper, the fair comparison is internal: ASF-like baseline vs TaskDec under the same code path.

## Recommended experiment ladder

### Phase 0: Dataset and metric sanity

Goal: make VoD examples pass through dataloader, visualization, and official evaluation conversion.

Required outputs from `VodFusion` dataloader:

- `ldr64`: LiDAR point cloud, `Nx4`, `[x, y, z, reflectance]`.
- `batch_indices_ldr64`: point-to-batch indices.
- `rdr_sparse`: radar point cloud, `Nx7`, `[x, y, z, RCS, v_r, v_r_comp, time]`.
- `batch_indices_rdr_sparse`: point-to-batch indices.
- `gt_boxes`: `B x M x 8`, `[x, y, z, l, w, h, yaw, class_id]`, in the chosen reference frame.
- `meta`: frame id, split, calibration, original label path.
- Optional camera keys later: `camera_imgs`, `sensor2image`, `camera_intrinsics`, `img_aug_matrix`.

Use the official VoD range:

`POINT_CLOUD_RANGE = [0, -25.6, -3, 51.2, 25.6, 2]`

This range is convenient because it gives a square 51.2 m x 51.2 m BEV.

Sanity checks:

- Draw LiDAR/radar points with GT boxes.
- Project boxes to the camera image.
- Verify yaw direction and box center convention.
- Run evaluation with copied GT as predictions and confirm near-perfect AP.

### Phase 1: Single-modality encoders

Train or validate two VoD encoders before fusion.

LiDAR encoder:

- Reuse `SECONDNet`.
- Set `DATASET.ldr64.n_used = 4`.
- Use ROI `[0, -25.6, -3, 51.2, 25.6, 2]`.
- Use LiDAR voxel size `[0.05, 0.05, 0.1]`; with the existing SECOND stride this should produce a `128 x 128` BEV feature map.
- Output key remains `spatial_features_2d`.

Radar encoder:

- Reuse `RadarBase` with `RadarSparseProcessor` + `RadarSparseBackbone`.
- Set `PRE_PROCESSOR.INPUT_DIM = 7`.
- Feed `rdr_sparse` directly from VoD `radar_5_scans`.
- Start with `DATASET.roi.grid_size = 0.4`, producing a `128 x 128` BEV feature map.
- Output key remains `bev_feat`.

Important radar caveat:

- K-Radar RTNH pretrained weights should not be reused directly. VoD radar is point-cloud style, not the same radar tensor/sparse-cube representation.
- Normalize or standardize non-coordinate radar attributes, especially RCS, Doppler, compensated Doppler, and time.

### Phase 2: ASF-style `L+R` fusion baseline

Create `configs/vod/cfg_A2F_lr.yml`.

Fuser:

- `NAME: A2Fusion`
- `KEY_FEATS: ['spatial_features_2d', 'bev_feat']`
- `DIM_FEATS: [512, 768]` if the reused encoders keep current channel counts.
- `TO_EMBED.DIM_COMMON: 256`
- `UCP.PATCH_SIZE: [2, 2]`
- `UCP.N_QUERY: 32`
- `UCP.DIM_PATCH: 256`
- `POST_CHANNEL: True`

This gives fused feature channels:

`DIM_PATCH * (N_QUERY / (patch_y * patch_x)) = 256 * 8 = 2048`

Detection head:

- `INPUT_CHANNELS: 2048`
- `KEY_FEATURES: fused_feat`
- classes: `Car`, `Pedestrian`, `Cyclist`
- anchors from the VoD PP-Radar/OpenPCDet guide:
  - Car: `[3.9, 1.6, 1.56]`, bottom height `-1.78`
  - Pedestrian: `[0.8, 0.6, 1.73]`, bottom height `-0.6`
  - Cyclist: `[1.76, 0.6, 1.73]`, bottom height `-0.6`

Training:

- Start with frozen single-modality encoders and train fuser/head.
- Then optionally unfreeze encoders for a short fine-tune if baseline is too weak.
- Keep SCL enabled. With two sensors, it gives `L`, `R`, and `L+R` supervision from one run.

### Phase 3: TaskDec `L+R`

Create `configs/vod/cfg_TaskDec_lr.yml` by swapping only the fuser and TaskDec parameters.

Fuser:

- `NAME: TaskAwareDecControlledA2Fusion`
- same `KEY_FEATS`, `DIM_FEATS`, UCP, PFT, and head as the A2Fusion baseline.
- `DEC_CONTROL_NUM_CLASSES: 3`
- `DEC_CONTROL_CONTEXT_MODE: class`

Start with conservative Robust-like settings:

- `PATCH_DEC_SELECTION: gt_foreground`
- `PATCH_DEC_FG_MARGIN: 0.5`
- `PATCH_DEC_RES_SCALE: 0.06`
- `PATCH_DEC_LAMBDA_DECOUPLE: 0.08`
- `PATCH_DEC_LAMBDA_COMMON: 0.10`
- `PATCH_DEC_LAMBDA_UNIQUE: 0.01`
- `DEC_CONTROL_STRENGTH: 0.60`
- `DEC_CONTROL_SCALE_MIN: 0.5`
- `DEC_CONTROL_SCALE_MAX: 1.9`
- `DEC_CONTROL_GATE_INIT_BIAS: -1.4`
- `DEC_CONTROL_GATE_LOSS_WEIGHT: 0.15`
- `DEC_CONTROL_CLASS_LOSS_WEIGHT: 0.20`
- `DEC_CONTROL_QUERY_STRENGTH: 0.08`
- `DEC_CONTROL_FUSED_RES_STRENGTH: 0.03`
- `PATCH_DEC_WEIGHT: 0.10`

Only move toward v1 Robust strength after the baseline is stable. VoD has many pedestrians/cyclists and a wider lateral range than K-Radar v1.0, so too aggressive control can overfit Car-dominant foreground patches.

### Phase 4: Optional camera

Do not start with camera.

Camera requires extra adaptation:

- VoD image size is `1936 x 1216`; current K-Radar camera path assumes resized/cropped front image around `704 x 256`.
- `CamBase` expects `camera_imgs` and a `sensor2image` matrix after image augmentation.
- Need image crop/resize calibration update.
- Need either set depth loss to zero or generate LiDAR depth labels for VoD.
- Need align camera BEV to the same `128 x 128` canonical grid.

If camera is added:

- Use front camera only first.
- LSS bounds: `XBOUND: [0.0, 51.2, 0.2]`, `YBOUND: [-25.6, 25.6, 0.2]`, downsample `2`, so camera BEV becomes `128 x 128`.
- Add `cam_bev_feat` to `KEY_FEATS`.
- Then evaluate `C+L+R`, `L+R`, `C+R`, `C+L`, and single-sensor availability.

## Code changes required

### Dataset

Add:

- `datasets/vod_fusion.py`
- registration in `datasets/__init__.py`

Implement:

- split loading from `ImageSets/train.txt`, `val.txt`.
- LiDAR loading from `lidar/training/velodyne`.
- radar loading from `radar_5_scans/training/velodyne`.
- labels from `label_2`.
- calibration parsing.
- class mapping:
  - `Car -> 1`
  - `Pedestrian -> 2`
  - `Cyclist -> 3`
  - ignore other VoD classes at first.

The hardest part is label conversion:

- VoD labels are KITTI-like and provided in the camera frame.
- Current heads expect OpenPCDet-style boxes in BEV/reference coordinates.
- Need carefully convert dimensions/order and yaw.
- Verify by visualization before training.

### Configs

Add a small config family:

- `configs/vod/cfg_VOD_LIDAR_SECOND.yml`
- `configs/vod/cfg_VOD_RADAR_SPARSE.yml`
- `configs/vod/cfg_A2F_lr.yml`
- `configs/vod/cfg_TaskDec_lr.yml`
- optional later: `configs/vod/cfg_A2F_clr.yml`, `configs/vod/cfg_TaskDec_clr.yml`

### Evaluation

Do not rely only on the current K-Radar KITTI eval path.

Add a converter that writes VoD/KITTI-format detection text files and calls the official VoD devkit, or directly uses its Python API.

Evaluation sanity checks:

- GT-as-prediction gives near-perfect AP.
- Empty predictions give zero AP.
- Prediction score ordering is preserved.
- Car/Pedestrian/Cyclist labels match VoD naming.

## Table design for the paper

Main external table:

| Method | C | L | R | Controller | Car 3D | Ped 3D | Cyc 3D | mAP 3D | mAP BEV |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| LiDAR-only |  | yes |  | none |  |  |  |  |  |
| Radar-only |  |  | yes | none |  |  |  |  |  |
| ASF-like |  | yes | yes | A2Fusion |  |  |  |  |  |
| TaskDec |  | yes | yes | decoupled control |  |  |  |  |  |

Ablation table:

| Method | PatchDec | FG gate | reliability scale | class context | mAP 3D |
|---|---:|---:|---:|---:|---:|
| A2Fusion |  |  |  |  |  |
| PatchDec | yes |  |  |  |  |
| DecControlled | yes | yes | yes |  |  |
| TaskDec | yes | yes | yes | yes |  |

Availability table:

| Checkpoint | Eval sensors | mAP 3D | mAP BEV |
|---|---|---:|---:|
| A2Fusion `L+R` | L |  |  |
| A2Fusion `L+R` | R |  |  |
| A2Fusion `L+R` | L+R |  |  |
| TaskDec `L+R` | L |  |  |
| TaskDec `L+R` | R |  |  |
| TaskDec `L+R` | L+R |  |  |

## Expected reviewer value

If TaskDec improves A2Fusion on VoD `L+R`, even by a modest margin, it answers two reviewer concerns:

1. The method is not only a K-Radar confidence-threshold artifact.
2. The decoupled controller works beyond K-Radar RTNH tensor features.

If the VoD result is weak, do not force it into the main paper. The paper can still stand on K-Radar v1/v2 plus stronger ablations.

## Risk list

High risk:

- label/yaw conversion bugs,
- mismatch between local KITTI eval and official VoD eval,
- weak radar-only baseline from a simple sparse backbone,
- class imbalance for Pedestrian/Cyclist,
- camera calibration after image crop/resize.

Medium risk:

- feature map shape mismatch before A2Fusion,
- memory from LiDAR SECOND over a `51.2 x 51.2` range,
- over-strong TaskDec control on small objects.

Low risk:

- TaskDec fuser itself; it only requires same-resolution BEV features.

## Implementation milestone checklist

1. `VodFusion` dataloader returns `ldr64`, `rdr_sparse`, `gt_boxes`, and `meta`.
2. Visualize 20 random frames with GT boxes on LiDAR/radar.
3. Official VoD eval adapter passes GT-as-prediction sanity.
4. Train/eval LiDAR-only.
5. Train/eval radar-only.
6. Train/eval `A2Fusion L+R`.
7. Train/eval `TaskDec L+R`.
8. Run `avail_feats=['spatial_features_2d']`, `['bev_feat']`, and both.
9. Add ablations if the main gain exists.
10. Add camera only after the above is stable.

## Sources checked

- VoD homepage: https://intelligent-vehicles.org/datasets/view-of-delft/
- VoD sensors/data: https://github.com/tudelft-iv/view-of-delft-dataset/blob/main/docs/SENSORS_AND_DATA.md
- VoD annotation docs: https://tudelft-iv.github.io/view-of-delft-dataset/docs/ANNOTATION.html
- VoD getting started: https://github.com/tudelft-iv/view-of-delft-dataset/blob/main/docs/GETTING_STARTED.md
- VoD PP-Radar/OpenPCDet guide: https://github.com/tudelft-iv/view-of-delft-dataset/blob/main/PP-Radar.md
- L4DR AAAI 2025: https://ojs.aaai.org/index.php/AAAI/article/view/32397
- MSSF repository: https://github.com/EricLiuhhh/MSSF
- RCTDistill ICCV 2025: https://openaccess.thecvf.com/content/ICCV2025/html/Bang_RCTDistill_Cross-Modal_Knowledge_Distillation_Framework_for_Radar-Camera_3D_Object_Detection_ICCV_2025_paper.html
