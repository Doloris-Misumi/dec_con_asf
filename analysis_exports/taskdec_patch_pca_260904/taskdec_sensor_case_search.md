# TaskDec Sensor Case Search

This file searches the weather-balanced PCA export for local samples whose controller outputs are less LiDAR-default than the weather averages.

## Quick Counts

- Foreground patch triplets: 2964
- LiDAR-dominant foreground patches: 2964
- Radar-dominant foreground patches: 0
- Camera-dominant foreground patches: 0
- Max foreground radar reliability: 0.006563
- Max foreground camera reliability: 0.037350
- Max foreground entropy: 0.177807

## Top Foreground Patches By Radar Reliability

| seq | sample_id | weather | patch_idx | foreground | camera | lidar | radar | dominant | dominance_margin | entropy | fg_gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00185 | urban | 1392 | 1 | 0.036316 | 0.957120 | 0.006563 | L | 0.920804 | 0.177807 | 0.248115 |
| 1 | 00196 | urban | 1357 | 1 | 0.030479 | 0.964065 | 0.005456 | L | 0.933586 | 0.154838 | 0.246374 |
| 1 | 00253 | urban | 855 | 1 | 0.032605 | 0.962072 | 0.005323 | L | 0.929467 | 0.160826 | 0.240417 |
| 1 | 00233 | urban | 763 | 1 | 0.027998 | 0.966932 | 0.005070 | L | 0.938935 | 0.145108 | 0.241230 |
| 1 | 00246 | urban | 856 | 1 | 0.026263 | 0.969025 | 0.004712 | L | 0.942762 | 0.137739 | 0.245622 |
| 1 | 00254 | urban | 1357 | 1 | 0.025310 | 0.970094 | 0.004596 | L | 0.944784 | 0.134031 | 0.263859 |
| 1 | 00255 | urban | 1352 | 1 | 0.029789 | 0.965630 | 0.004581 | L | 0.935841 | 0.148471 | 0.155065 |
| 1 | 00223 | urban | 760 | 1 | 0.031889 | 0.963536 | 0.004575 | L | 0.931646 | 0.155024 | 0.159230 |
| 1 | 00226 | urban | 761 | 1 | 0.026109 | 0.969358 | 0.004533 | L | 0.943249 | 0.136362 | 0.329434 |
| 1 | 00200 | urban | 668 | 1 | 0.027968 | 0.967526 | 0.004507 | L | 0.939558 | 0.142287 | 0.203122 |

## Top Foreground Patches By Camera Reliability

| seq | sample_id | weather | patch_idx | foreground | camera | lidar | radar | dominant | dominance_margin | entropy | fg_gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00230 | urban | 493 | 1 | 0.037350 | 0.958191 | 0.004458 | L | 0.920841 | 0.170980 | 0.109992 |
| 1 | 00185 | urban | 1392 | 1 | 0.036316 | 0.957120 | 0.006563 | L | 0.920804 | 0.177807 | 0.248115 |
| 1 | 00240 | urban | 492 | 1 | 0.033572 | 0.961982 | 0.004447 | L | 0.928410 | 0.159575 | 0.120652 |
| 1 | 00253 | urban | 855 | 1 | 0.032605 | 0.962072 | 0.005323 | L | 0.929467 | 0.160826 | 0.240417 |
| 1 | 00223 | urban | 760 | 1 | 0.031889 | 0.963536 | 0.004575 | L | 0.931646 | 0.155024 | 0.159230 |
| 1 | 00196 | urban | 1357 | 1 | 0.030479 | 0.964065 | 0.005456 | L | 0.933586 | 0.154838 | 0.246374 |
| 1 | 00244 | urban | 1209 | 1 | 0.029808 | 0.966131 | 0.004061 | L | 0.936323 | 0.145969 | 0.126243 |
| 1 | 00255 | urban | 1352 | 1 | 0.029789 | 0.965630 | 0.004581 | L | 0.935841 | 0.148471 | 0.155065 |
| 1 | 00230 | urban | 492 | 1 | 0.028824 | 0.967445 | 0.003731 | L | 0.938621 | 0.141184 | 0.120636 |
| 1 | 00183 | urban | 1399 | 1 | 0.028507 | 0.967672 | 0.003821 | L | 0.939166 | 0.140620 | 0.134872 |

## Most Balanced Foreground Patches

| seq | sample_id | weather | patch_idx | foreground | camera | lidar | radar | dominant | dominance_margin | entropy | fg_gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00185 | urban | 1392 | 1 | 0.036316 | 0.957120 | 0.006563 | L | 0.920804 | 0.177807 | 0.248115 |
| 1 | 00230 | urban | 493 | 1 | 0.037350 | 0.958191 | 0.004458 | L | 0.920841 | 0.170980 | 0.109992 |
| 1 | 00253 | urban | 855 | 1 | 0.032605 | 0.962072 | 0.005323 | L | 0.929467 | 0.160826 | 0.240417 |
| 1 | 00240 | urban | 492 | 1 | 0.033572 | 0.961982 | 0.004447 | L | 0.928410 | 0.159575 | 0.120652 |
| 1 | 00223 | urban | 760 | 1 | 0.031889 | 0.963536 | 0.004575 | L | 0.931646 | 0.155024 | 0.159230 |
| 1 | 00196 | urban | 1357 | 1 | 0.030479 | 0.964065 | 0.005456 | L | 0.933586 | 0.154838 | 0.246374 |
| 1 | 00255 | urban | 1352 | 1 | 0.029789 | 0.965630 | 0.004581 | L | 0.935841 | 0.148471 | 0.155065 |
| 1 | 00244 | urban | 1209 | 1 | 0.029808 | 0.966131 | 0.004061 | L | 0.936323 | 0.145969 | 0.126243 |
| 1 | 00233 | urban | 763 | 1 | 0.027998 | 0.966932 | 0.005070 | L | 0.938935 | 0.145108 | 0.241230 |
| 1 | 00200 | urban | 668 | 1 | 0.027968 | 0.967526 | 0.004507 | L | 0.939558 | 0.142287 | 0.203122 |

## Frame-Level Radar-Heavy Candidates

| seq | sample_id | weather | num_fg_patches | camera_mean | lidar_mean | radar_mean | dominant | dominance_margin | entropy_mean | fg_gate_delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00230 | urban | 31 | 0.009881 | 0.988699 | 0.001420 | L | 0.978818 | 0.054496 | 0.191670 |
| 1 | 00237 | urban | 35 | 0.008725 | 0.989937 | 0.001338 | L | 0.981212 | 0.051233 | 0.182485 |
| 1 | 00195 | urban | 48 | 0.007894 | 0.990805 | 0.001301 | L | 0.982910 | 0.047489 | 0.185763 |
| 1 | 00241 | urban | 28 | 0.008359 | 0.990378 | 0.001263 | L | 0.982019 | 0.048518 | 0.201625 |
| 1 | 00196 | urban | 48 | 0.007426 | 0.991323 | 0.001251 | L | 0.983896 | 0.044929 | 0.173911 |
| 1 | 00233 | urban | 35 | 0.008231 | 0.990536 | 0.001233 | L | 0.982305 | 0.047727 | 0.152364 |
| 1 | 00240 | urban | 30 | 0.008392 | 0.990386 | 0.001222 | L | 0.981994 | 0.048236 | 0.181170 |
| 1 | 00244 | urban | 48 | 0.007435 | 0.991426 | 0.001139 | L | 0.983991 | 0.044177 | 0.153509 |
| 1 | 00247 | urban | 48 | 0.007085 | 0.991792 | 0.001123 | L | 0.984707 | 0.042907 | 0.172199 |
| 1 | 00253 | urban | 48 | 0.006591 | 0.992301 | 0.001107 | L | 0.985710 | 0.039910 | 0.246837 |

## Frame-Level Camera-Heavy Candidates

| seq | sample_id | weather | num_fg_patches | camera_mean | lidar_mean | radar_mean | dominant | dominance_margin | entropy_mean | fg_gate_delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00230 | urban | 31 | 0.009881 | 0.988699 | 0.001420 | L | 0.978818 | 0.054496 | 0.191670 |
| 1 | 00237 | urban | 35 | 0.008725 | 0.989937 | 0.001338 | L | 0.981212 | 0.051233 | 0.182485 |
| 1 | 00240 | urban | 30 | 0.008392 | 0.990386 | 0.001222 | L | 0.981994 | 0.048236 | 0.181170 |
| 1 | 00241 | urban | 28 | 0.008359 | 0.990378 | 0.001263 | L | 0.982019 | 0.048518 | 0.201625 |
| 1 | 00233 | urban | 35 | 0.008231 | 0.990536 | 0.001233 | L | 0.982305 | 0.047727 | 0.152364 |
| 1 | 00195 | urban | 48 | 0.007894 | 0.990805 | 0.001301 | L | 0.982910 | 0.047489 | 0.185763 |
| 1 | 00205 | urban | 25 | 0.007825 | 0.991146 | 0.001029 | L | 0.983321 | 0.044834 | 0.095616 |
| 1 | 00244 | urban | 48 | 0.007435 | 0.991426 | 0.001139 | L | 0.983991 | 0.044177 | 0.153509 |
| 1 | 00196 | urban | 48 | 0.007426 | 0.991323 | 0.001251 | L | 0.983896 | 0.044929 | 0.173911 |
| 1 | 00236 | urban | 35 | 0.007424 | 0.991508 | 0.001069 | L | 0.984084 | 0.044576 | 0.126025 |

## Frame-Level Balanced Candidates

| seq | sample_id | weather | num_fg_patches | camera_mean | lidar_mean | radar_mean | dominant | dominance_margin | entropy_mean | fg_gate_delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00230 | urban | 31 | 0.009881 | 0.988699 | 0.001420 | L | 0.978818 | 0.054496 | 0.191670 |
| 1 | 00237 | urban | 35 | 0.008725 | 0.989937 | 0.001338 | L | 0.981212 | 0.051233 | 0.182485 |
| 1 | 00241 | urban | 28 | 0.008359 | 0.990378 | 0.001263 | L | 0.982019 | 0.048518 | 0.201625 |
| 1 | 00240 | urban | 30 | 0.008392 | 0.990386 | 0.001222 | L | 0.981994 | 0.048236 | 0.181170 |
| 1 | 00233 | urban | 35 | 0.008231 | 0.990536 | 0.001233 | L | 0.982305 | 0.047727 | 0.152364 |
| 1 | 00195 | urban | 48 | 0.007894 | 0.990805 | 0.001301 | L | 0.982910 | 0.047489 | 0.185763 |
| 1 | 00196 | urban | 48 | 0.007426 | 0.991323 | 0.001251 | L | 0.983896 | 0.044929 | 0.173911 |
| 1 | 00205 | urban | 25 | 0.007825 | 0.991146 | 0.001029 | L | 0.983321 | 0.044834 | 0.095616 |
| 1 | 00236 | urban | 35 | 0.007424 | 0.991508 | 0.001069 | L | 0.984084 | 0.044576 | 0.126025 |
| 1 | 00244 | urban | 48 | 0.007435 | 0.991426 | 0.001139 | L | 0.983991 | 0.044177 | 0.153509 |

## Frame-Level Gate-Response Candidates

| seq | sample_id | weather | num_fg_patches | camera_mean | lidar_mean | radar_mean | dominant | dominance_margin | entropy_mean | fg_gate_delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 00252 | urban | 48 | 0.005246 | 0.993885 | 0.000868 | L | 0.988639 | 0.033071 | 0.262631 |
| 1 | 00227 | urban | 24 | 0.003556 | 0.995913 | 0.000531 | L | 0.992358 | 0.022869 | 0.258255 |
| 1 | 00228 | urban | 24 | 0.005779 | 0.993372 | 0.000850 | L | 0.987593 | 0.035942 | 0.252745 |
| 1 | 00192 | urban | 48 | 0.004017 | 0.995351 | 0.000632 | L | 0.991335 | 0.025434 | 0.249806 |
| 1 | 00253 | urban | 48 | 0.006591 | 0.992301 | 0.001107 | L | 0.985710 | 0.039910 | 0.246837 |
| 1 | 00215 | urban | 24 | 0.005064 | 0.994148 | 0.000788 | L | 0.989084 | 0.032006 | 0.245909 |
| 1 | 00250 | urban | 48 | 0.004546 | 0.994737 | 0.000716 | L | 0.990191 | 0.028604 | 0.244449 |
| 1 | 00257 | urban | 24 | 0.003602 | 0.995827 | 0.000572 | L | 0.992225 | 0.024323 | 0.242208 |
| 1 | 00216 | urban | 24 | 0.005273 | 0.993893 | 0.000834 | L | 0.988620 | 0.033340 | 0.240855 |
| 1 | 00189 | urban | 48 | 0.004102 | 0.995227 | 0.000671 | L | 0.991126 | 0.026702 | 0.238189 |

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
