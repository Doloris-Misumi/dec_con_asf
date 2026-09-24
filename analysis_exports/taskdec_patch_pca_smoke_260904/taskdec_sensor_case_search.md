# TaskDec Sensor Case Search

This file searches the weather-balanced PCA export for local samples whose controller outputs are less LiDAR-default than the weather averages.

## Quick Counts

- Foreground patch triplets: 16
- LiDAR-dominant foreground patches: 16
- Radar-dominant foreground patches: 0
- Camera-dominant foreground patches: 0
- Max foreground radar reliability: 0.002189
- Max foreground camera reliability: 0.016863
- Max foreground entropy: 0.092044

## Top Foreground Patches By Radar Reliability

| seq | sample_id | weather | patch_idx | foreground | camera | lidar | radar | dominant | dominance_margin | entropy | fg_gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00182 | urban | 1040 | 1 | 0.016863 | 0.980948 | 0.002189 | L | 0.964085 | 0.092044 | 0.118458 |
| 1 | 00183 | urban | 578 | 1 | 0.011509 | 0.986627 | 0.001864 | L | 0.975119 | 0.069524 | 0.263334 |
| 1 | 00183 | urban | 492 | 1 | 0.007926 | 0.990812 | 0.001262 | L | 0.982886 | 0.050894 | 0.182324 |
| 1 | 00182 | urban | 1404 | 1 | 0.008637 | 0.990167 | 0.001195 | L | 0.981530 | 0.053586 | 0.128988 |
| 1 | 00182 | urban | 402 | 1 | 0.003668 | 0.995666 | 0.000667 | L | 0.991998 | 0.027098 | 0.233362 |
| 1 | 00183 | urban | 306 | 1 | 0.004998 | 0.994404 | 0.000598 | L | 0.989406 | 0.033224 | 0.128941 |
| 1 | 00182 | urban | 487 | 1 | 0.002089 | 0.997588 | 0.000323 | L | 0.995498 | 0.016293 | 0.297660 |
| 1 | 00183 | urban | 309 | 1 | 0.001580 | 0.998177 | 0.000243 | L | 0.996596 | 0.012778 | 0.201858 |
| 1 | 00182 | urban | 1315 | 1 | 0.001442 | 0.998320 | 0.000238 | L | 0.996879 | 0.011919 | 0.226125 |
| 1 | 00182 | urban | 1132 | 1 | 0.001031 | 0.998832 | 0.000137 | L | 0.997800 | 0.008628 | 0.168261 |

## Top Foreground Patches By Camera Reliability

| seq | sample_id | weather | patch_idx | foreground | camera | lidar | radar | dominant | dominance_margin | entropy | fg_gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00182 | urban | 1040 | 1 | 0.016863 | 0.980948 | 0.002189 | L | 0.964085 | 0.092044 | 0.118458 |
| 1 | 00183 | urban | 578 | 1 | 0.011509 | 0.986627 | 0.001864 | L | 0.975119 | 0.069524 | 0.263334 |
| 1 | 00182 | urban | 1404 | 1 | 0.008637 | 0.990167 | 0.001195 | L | 0.981530 | 0.053586 | 0.128988 |
| 1 | 00183 | urban | 492 | 1 | 0.007926 | 0.990812 | 0.001262 | L | 0.982886 | 0.050894 | 0.182324 |
| 1 | 00183 | urban | 306 | 1 | 0.004998 | 0.994404 | 0.000598 | L | 0.989406 | 0.033224 | 0.128941 |
| 1 | 00182 | urban | 402 | 1 | 0.003668 | 0.995666 | 0.000667 | L | 0.991998 | 0.027098 | 0.233362 |
| 1 | 00182 | urban | 487 | 1 | 0.002089 | 0.997588 | 0.000323 | L | 0.995498 | 0.016293 | 0.297660 |
| 1 | 00183 | urban | 309 | 1 | 0.001580 | 0.998177 | 0.000243 | L | 0.996596 | 0.012778 | 0.201858 |
| 1 | 00182 | urban | 1315 | 1 | 0.001442 | 0.998320 | 0.000238 | L | 0.996879 | 0.011919 | 0.226125 |
| 1 | 00182 | urban | 1132 | 1 | 0.001031 | 0.998832 | 0.000137 | L | 0.997800 | 0.008628 | 0.168261 |

## Most Balanced Foreground Patches

| seq | sample_id | weather | patch_idx | foreground | camera | lidar | radar | dominant | dominance_margin | entropy | fg_gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00182 | urban | 1040 | 1 | 0.016863 | 0.980948 | 0.002189 | L | 0.964085 | 0.092044 | 0.118458 |
| 1 | 00183 | urban | 578 | 1 | 0.011509 | 0.986627 | 0.001864 | L | 0.975119 | 0.069524 | 0.263334 |
| 1 | 00182 | urban | 1404 | 1 | 0.008637 | 0.990167 | 0.001195 | L | 0.981530 | 0.053586 | 0.128988 |
| 1 | 00183 | urban | 492 | 1 | 0.007926 | 0.990812 | 0.001262 | L | 0.982886 | 0.050894 | 0.182324 |
| 1 | 00183 | urban | 306 | 1 | 0.004998 | 0.994404 | 0.000598 | L | 0.989406 | 0.033224 | 0.128941 |
| 1 | 00182 | urban | 402 | 1 | 0.003668 | 0.995666 | 0.000667 | L | 0.991998 | 0.027098 | 0.233362 |
| 1 | 00182 | urban | 487 | 1 | 0.002089 | 0.997588 | 0.000323 | L | 0.995498 | 0.016293 | 0.297660 |
| 1 | 00183 | urban | 309 | 1 | 0.001580 | 0.998177 | 0.000243 | L | 0.996596 | 0.012778 | 0.201858 |
| 1 | 00182 | urban | 1315 | 1 | 0.001442 | 0.998320 | 0.000238 | L | 0.996879 | 0.011919 | 0.226125 |
| 1 | 00182 | urban | 1132 | 1 | 0.001031 | 0.998832 | 0.000137 | L | 0.997800 | 0.008628 | 0.168261 |

## Frame-Level Radar-Heavy Candidates

| seq | sample_id | weather | num_fg_patches | camera_mean | lidar_mean | radar_mean | dominant | dominance_margin | entropy_mean | fg_gate_delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00182 | urban | 8 | 0.004217 | 0.995190 | 0.000594 | L | 0.990973 | 0.026201 | 0.130495 |
| 1 | 00183 | urban | 8 | 0.003405 | 0.996076 | 0.000519 | L | 0.992671 | 0.022209 | 0.191144 |

## Frame-Level Camera-Heavy Candidates

| seq | sample_id | weather | num_fg_patches | camera_mean | lidar_mean | radar_mean | dominant | dominance_margin | entropy_mean | fg_gate_delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00182 | urban | 8 | 0.004217 | 0.995190 | 0.000594 | L | 0.990973 | 0.026201 | 0.130495 |
| 1 | 00183 | urban | 8 | 0.003405 | 0.996076 | 0.000519 | L | 0.992671 | 0.022209 | 0.191144 |

## Frame-Level Balanced Candidates

| seq | sample_id | weather | num_fg_patches | camera_mean | lidar_mean | radar_mean | dominant | dominance_margin | entropy_mean | fg_gate_delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00182 | urban | 8 | 0.004217 | 0.995190 | 0.000594 | L | 0.990973 | 0.026201 | 0.130495 |
| 1 | 00183 | urban | 8 | 0.003405 | 0.996076 | 0.000519 | L | 0.992671 | 0.022209 | 0.191144 |

## Frame-Level Gate-Response Candidates

| seq | sample_id | weather | num_fg_patches | camera_mean | lidar_mean | radar_mean | dominant | dominance_margin | entropy_mean | fg_gate_delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00183 | urban | 8 | 0.003405 | 0.996076 | 0.000519 | L | 0.992671 | 0.022209 | 0.191144 |
| 1 | 00182 | urban | 8 | 0.004217 | 0.995190 | 0.000594 | L | 0.990973 | 0.026201 | 0.130495 |

## Per-Weather Best Radar/Balance Candidates

### normal

Radar-heavy foreground patches:

_No candidates found._

Most balanced foreground patches:

_No candidates found._

### overcast

Radar-heavy foreground patches:

_No candidates found._

Most balanced foreground patches:

_No candidates found._

### fog

Radar-heavy foreground patches:

_No candidates found._

Most balanced foreground patches:

_No candidates found._

### rain

Radar-heavy foreground patches:

_No candidates found._

Most balanced foreground patches:

_No candidates found._

### sleet

Radar-heavy foreground patches:

_No candidates found._

Most balanced foreground patches:

_No candidates found._

### lightsnow

Radar-heavy foreground patches:

_No candidates found._

Most balanced foreground patches:

_No candidates found._

### heavysnow

Radar-heavy foreground patches:

_No candidates found._

Most balanced foreground patches:

_No candidates found._
