# TaskDec Weather PCA Visualization Notes

Date: 2026-09-09

Model used for export:

`logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt`

Config:

`logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml`

Export directory:

`analysis_exports/taskdec_patch_pca_weather_260909`

## What Was Exported

Weather-balanced sampling was used: 24 frames per weather condition, covering:

`normal`, `overcast`, `fog`, `rain`, `sleet`, `lightsnow`, `heavysnow`.

The export contains 168 frames and 78,588 sampled patch records. The old PCA export used `road_type` as the condition name, so it collapsed everything into `urban`; the exporter has been fixed to prefer the real `climate` field from K-Radar `description.txt`.

## Main Figure Candidates

1. `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_pca_foreground_grid.png`

   Best candidate for the paper or appendix. It shows foreground patch PCA for each weather condition and compares three spaces:

   - raw canonical patch features
   - TaskDec common states
   - TaskDec unique states

   The key visual story is clear: common states reduce cross-sensor spread, while unique states keep strong sensor-specific structure.

2. `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_modality_centroid_distance.png`

   Best quantitative companion figure. It measures mean pairwise sensor-centroid distance in PCA space:

   | Weather | Raw | Common | Unique |
   |---|---:|---:|---:|
   | normal | 19.33 | 4.99 | 20.74 |
   | overcast | 19.44 | 5.02 | 19.98 |
   | fog | 19.26 | 4.49 | 18.41 |
   | rain | 19.35 | 5.13 | 20.01 |
   | sleet | 19.30 | 4.39 | 17.40 |
   | lightsnow | 19.44 | 4.66 | 18.37 |
   | heavysnow | 19.29 | 4.51 | 18.20 |

   This is the strongest evidence that the decoupled representation does what the method claims:

   - `common` is consistently much more sensor-aligned than raw features.
   - `unique` remains close to raw or even more separated in several weather groups.
   - normal, rain, and overcast show the largest unique-state sensor spread.

3. `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_reliability_gate.png`

   Useful as an appendix figure, but it should be phrased carefully. This checkpoint's sensor reliability head is strongly LiDAR-dominant across all weather groups, so it does not support a strong claim that reliability weights visibly switch between camera/LiDAR/radar by weather.

   The foreground gate is more interpretable: foreground gate values are higher under fog, sleet, lightsnow, and heavysnow than under normal/overcast/rain, while background gates stay lower.

## Suggested Paper Wording

Use the PCA result to support the representation-level claim:

> Across weather conditions, TaskDec maps modality-shared foreground evidence into a compact common state while preserving sensor-specific variation in the unique state. This indicates that the controller does not merely reweight fused features, but explicitly separates task-relevant shared cues from modality-dependent residual information.

Avoid saying:

> The learned sensor reliability dynamically switches dominant sensors across weather.

A safer version is:

> In this trained checkpoint, reliability weights are LiDAR-dominant, while the foreground gate shows stronger weather dependence. We therefore use PCA and centroid-distance analysis as the main diagnostic for decoupled representation behavior, and treat reliability visualization as an auxiliary controller readout.

## Generated Files

- `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_pca_foreground_grid.png`
- `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_pca_foreground_grid.svg`
- `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_modality_centroid_distance.png`
- `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_modality_centroid_distance.svg`
- `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_reliability_gate.png`
- `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_weather_reliability_gate.svg`
- `analysis_exports/taskdec_patch_pca_weather_260909/pca_weather_analysis.md`
- `analysis_exports/taskdec_patch_pca_weather_260909/weather_pca_modality_distances.csv`
- `analysis_exports/taskdec_patch_pca_weather_260909/weather_sensor_reliability.md`
