# TaskDec Sensor Case Candidates

Date: 2026-09-09

Goal: search for samples whose TaskDec controller reliability is Radar-dominant, Camera-dominant, or relatively balanced across sensors.

## Exports Checked

1. Main TaskDec Robust `model_0`, RLC inference:

   `analysis_exports/taskdec_patch_pca_weather_260909`

2. Main TaskDec Robust `model_0`, LR inference:

   `analysis_exports/taskdec_patch_pca_weather_lr_260909`

3. TaskDec Balanced `model_2`, RLC inference:

   `analysis_exports/taskdec_patch_pca_balanced_model2_weather_260909`

Older PCA exports were also checked:

- `analysis_exports/taskdec_patch_pca_260904`
- `analysis_exports/taskdec_patch_pca_smoke_260904`

## Main Finding

I did not find a truly Radar-dominant or Camera-dominant patch in the current TaskDec controller reliability output.

For the main Robust `model_0` RLC export:

- all sampled patch groups: 8732
- LiDAR-dominant all sampled patch groups: 8732
- Radar-dominant all sampled patch groups: 0
- Camera-dominant all sampled patch groups: 0
- foreground patch groups: 5708
- LiDAR-dominant foreground patch groups: 5708
- Radar-dominant foreground patch groups: 0
- Camera-dominant foreground patch groups: 0

For LR inference, removing camera still does not make Radar dominate:

- LiDAR-dominant all sampled patch groups: 8732
- Radar-dominant all sampled patch groups: 0
- foreground max Radar reliability: 0.015317

The earlier memory of an R-dominant visualization is therefore probably from another signal, such as R-only availability, a branch-routing statistic, an attention/activation visualization, or another project output, not the current `sensor_prob` reliability head.

## Best Relative Candidates

These are not truly balanced, but they are the least LiDAR-default cases found so far.

### Main Robust RLC, All Sampled Patches

| Rank | seq | frame | weather | patch | fg | Camera | LiDAR | Radar | Note |
|---:|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | 34 | 00175 | rain | 181 | 0 | 0.180190 | 0.795185 | 0.024625 | most balanced overall; background/edge patch |
| 2 | 39 | 00537 | fog | 180 | 0 | 0.104227 | 0.880237 | 0.015537 | second most balanced; background/edge patch |
| 3 | 48 | 00187 | lightsnow | 542 | 0 | 0.071868 | 0.915094 | 0.013038 | background/edge patch |
| 4 | 48 | 00117 | lightsnow | 540 | 0 | 0.065297 | 0.923826 | 0.010876 | background/edge patch |
| 5 | 53 | 00295 | sleet | 919 | 1 | 0.064601 | 0.924678 | 0.010721 | best foreground candidate |

### Main Robust RLC, Foreground Patches Only

| Rank | seq | frame | weather | patch | Camera | LiDAR | Radar | Note |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | 53 | 00295 | sleet | 919 | 0.064601 | 0.924678 | 0.010721 | best foreground balance/Radar candidate |
| 2 | 48 | 00117 | lightsnow | 1266 | 0.048706 | 0.941676 | 0.009618 | foreground |
| 3 | 43 | 00492 | lightsnow | 183 | 0.047685 | 0.943617 | 0.008698 | foreground |
| 4 | 52 | 00229 | sleet | 946 | 0.047942 | 0.943725 | 0.008333 | foreground |
| 5 | 38 | 00204 | fog | 1041 | 0.049793 | 0.942661 | 0.007546 | foreground |

### Main Robust LR, Best Radar Candidates

| Rank | seq | frame | weather | patch | fg | LiDAR | Radar | Note |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | 34 | 00175 | rain | 181 | 0 | 0.960724 | 0.039276 | best LR Radar candidate; background/edge patch |
| 2 | 39 | 00537 | fog | 180 | 0 | 0.975472 | 0.024528 | background/edge patch |
| 3 | 48 | 00187 | lightsnow | 542 | 0 | 0.981659 | 0.018341 | background/edge patch |
| 4 | 53 | 00295 | sleet | 919 | 1 | 0.984683 | 0.015317 | best LR foreground candidate |
| 5 | 48 | 00117 | lightsnow | 540 | 0 | 0.984688 | 0.015312 | background/edge patch |

## Files

- RLC candidate search: `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_sensor_case_search.md`
- RLC patch CSV: `analysis_exports/taskdec_patch_pca_weather_260909/taskdec_sensor_patch_cases.csv`
- LR candidate search: `analysis_exports/taskdec_patch_pca_weather_lr_260909/taskdec_sensor_case_search.md`
- LR patch CSV: `analysis_exports/taskdec_patch_pca_weather_lr_260909/taskdec_sensor_patch_cases.csv`
- Balanced model2 candidate search: `analysis_exports/taskdec_patch_pca_balanced_model2_weather_260909/taskdec_sensor_case_search.md`

## Paper Usage Recommendation

Do not claim that this checkpoint shows sensor-reliability switching among Camera/LiDAR/Radar. The controller's reliability output is sharply LiDAR-dominant.

A safer visualization story is:

- use PCA and modality-centroid distance to show that common states align sensors while unique states preserve sensor-specific variation;
- use foreground gate by weather to show weather-sensitive foreground activation;
- optionally mention in the appendix that the learned reliability head is conservative and LiDAR-dominant in this checkpoint.

If a sensor-switching figure is important, it should be based on a different diagnostic, such as attention contribution, token-scale maps, modality-drop performance, or a checkpoint trained with explicit entropy/balance regularization.
