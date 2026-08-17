# DEC v1 Composite Checkpoint Selection and ASF Repro Check

Date: 2026-08-16

## Selection Rule

The previous shortlist over-weighted `3D@0.3`. For full validation selection, the safer rule is to look at all six subset metrics together:

- `BEV@0.7`, `3D@0.7`
- `BEV@0.5`, `3D@0.5`
- `BEV@0.3`, `3D@0.3`

I report two simple scores:

- `mean_all6`: average of all six metrics
- `mean_3d`: average of `3D@0.7/0.5/0.3`

## MoreOpenGate

Top checkpoints by `mean_all6` on the fixed 1000-frame validation subset:

| epoch | mean_all6 | mean_3d | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 70.1300 | 60.1667 | 63.16 | 17.45 | 88.11 | 74.79 | 89.01 | 88.26 |
| 2 | 68.8983 | 58.2500 | 61.12 | 18.02 | 88.38 | 68.06 | 89.14 | 88.67 |
| 7 | 68.2383 | 57.0233 | 61.88 | 16.95 | 87.49 | 66.13 | 88.99 | 87.99 |
| 4 | 68.0267 | 58.8900 | 61.82 | 19.71 | 80.54 | 68.40 | 89.13 | 88.56 |
| 10 | 67.8650 | 58.6467 | 61.58 | 19.05 | 80.41 | 68.14 | 89.26 | 88.75 |

Top checkpoints by `mean_3d`:

| epoch | mean_3d | mean_all6 | 3D@0.7 | 3D@0.5 | 3D@0.3 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 60.1667 | 70.1300 | 17.45 | 74.79 | 88.26 |
| 4 | 58.8900 | 68.0267 | 19.71 | 68.40 | 88.56 |
| 10 | 58.6467 | 67.8650 | 19.05 | 68.14 | 88.75 |
| 2 | 58.2500 | 68.8983 | 18.02 | 68.06 | 88.67 |

Conclusion: MoreOpenGate should prioritize `model_0.pt` for full validation. The earlier `model_2.pt` recommendation came from looking mainly at `3D@0.3`; once `0.7/0.5/0.3` BEV and 3D are considered together, epoch 0 is clearly the most balanced MoreOpenGate checkpoint.

## StrongerControl

Top checkpoints by `mean_all6`:

| epoch | mean_all6 | mean_3d | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 68.5833 | 59.7733 | 62.46 | 22.30 | 80.54 | 68.35 | 89.18 | 88.67 |
| 4 | 68.5550 | 59.6767 | 62.50 | 22.21 | 80.62 | 68.30 | 89.18 | 88.52 |
| 7 | 68.5100 | 58.0667 | 60.65 | 20.90 | 87.38 | 65.78 | 88.83 | 87.52 |
| 0 | 68.3583 | 59.3667 | 62.88 | 22.24 | 80.30 | 67.52 | 88.87 | 88.34 |

Top checkpoints by `mean_3d`:

| epoch | mean_3d | mean_all6 | 3D@0.7 | 3D@0.5 | 3D@0.3 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 59.7733 | 68.5833 | 22.30 | 68.35 | 88.67 |
| 4 | 59.6767 | 68.5550 | 22.21 | 68.30 | 88.52 |
| 0 | 59.3667 | 68.3583 | 22.24 | 67.52 | 88.34 |
| 7 | 58.0667 | 68.5100 | 20.90 | 65.78 | 87.52 |

Conclusion: StrongerControl should prioritize `model_2.pt`, with `model_4.pt` as the closest backup. `model_0.pt` is also healthy, but not quite as strong as epochs 2/4 under either all-six or 3D-only averaging.

## Full Validation Priority

Recommended full-validation queue:

1. MoreOpenGate `model_0.pt`
2. StrongerControl `model_2.pt`
3. StrongerControl `model_4.pt`
4. MoreOpenGate `model_2.pt`

If compute is very limited, run the first two. They represent the best balanced checkpoint for each branch.

## ASF v1.0 Local Reproduction

Comparable ASF reproduction directory:

`/home/hongsheng/K-Radar-main/logs/exp_260814_212832_ASF_v1_0_local_repro`

Status:

- Completed training checkpoints `model_0.pt` through `model_10.pt`
- Completed final full validation at `test_kitti/none/0.3/complete_results.txt`
- Uses `KRadarFusion_v1_0`
- Uses split `./resources/split/train.txt`, `./resources/split/test.txt`
- Uses v1.0 frozen pretrained backbones:
  - `./pretrained/v1_0/CAMERA_MODEL_v1_0_10.pt`
  - `./pretrained/v1_0/SECOND_v1_0_10.pt`
  - `./pretrained/v1_0/RTNH_v1_0_10.pt`
- Single Sedan class in the head

Full validation, condition `all`, class `sed`, confidence threshold `0.3`:

| model | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ASF v1.0 local repro, final epoch | 63.1071 | 22.9513 | 80.4457 | 67.7160 | 89.1450 | 80.4465 |

This is the proper ASF baseline to compare against the current DEC v1.0 experiments. The older directory
`/home/hongsheng/K-Radar-main/logs/exp_260725_230526_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
is not directly comparable because it uses the older pretrained paths and a two-class Sedan/Bus-or-Truck head.

