# K-Radar v1 fixed-weight interventions

Full 10,065-frame test set; Sedan; conf>0.3; original v1 11-point evaluator. Same model_0 for every row. Inference interventions, not retrained ablations.

| Setting | AP3D@0.3 | AP3D@0.5 | AP3D@0.7 | BEV@0.3 | BEV@0.5 | BEV@0.7 |
|---|---:|---:|---:|---:|---:|---:|
| Full ObjDec | 88.3599 | 67.4838 | 22.0603 | 88.8370 | 88.1066 | 62.6532 |
| Frame-mean gate | 53.9015 | 40.2109 | 7.9593 | 54.2623 | 53.1635 | 37.6025 |
| Shuffled gate (260923) | 21.3775 | 17.5284 | 4.7356 | 21.5984 | 21.0439 | 16.6446 |
| Shuffled gate (260924) | 21.2514 | 17.4692 | 6.2176 | 21.5240 | 20.9864 | 16.5998 |
| Shuffled gate (260925) | 21.2448 | 12.9107 | 3.9612 | 21.4998 | 20.9850 | 16.6030 |
| No query increment | 88.3492 | 67.4711 | 22.1068 | 88.8342 | 88.0989 | 62.7320 |
| No output increment | 88.3599 | 67.4833 | 22.0565 | 88.8358 | 88.1066 | 62.6516 |
| No query/output increments | 88.3453 | 67.4742 | 22.1096 | 88.8342 | 88.0980 | 62.7320 |

## Differences relative to baseline

| Setting | AP3D@0.3 | AP3D@0.5 | AP3D@0.7 | BEV@0.3 | BEV@0.5 | BEV@0.7 |
|---|---:|---:|---:|---:|---:|---:|
| Full ObjDec | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| Frame-mean gate | -34.4584 | -27.2729 | -14.1010 | -34.5748 | -34.9431 | -25.0507 |
| Shuffled gate (260923) | -66.9824 | -49.9554 | -17.3247 | -67.2387 | -67.0627 | -46.0086 |
| Shuffled gate (260924) | -67.1085 | -50.0146 | -15.8427 | -67.3130 | -67.1202 | -46.0534 |
| Shuffled gate (260925) | -67.1151 | -54.5731 | -18.0991 | -67.3373 | -67.1216 | -46.0502 |
| No query increment | -0.0107 | -0.0126 | +0.0465 | -0.0029 | -0.0077 | +0.0788 |
| No output increment | +0.0000 | -0.0005 | -0.0038 | -0.0012 | +0.0000 | -0.0016 |
| No query/output increments | -0.0146 | -0.0095 | +0.0493 | -0.0029 | -0.0087 | +0.0788 |

Gate changes preserve the frame mean or value distribution but alter spatial correspondence. They consistently affect token residuals, sensor scaling, and gated context. Removing query/output increments does not change token modulation. Shuffle seeds are intervention replicates, not training replicates. All results, including negative or negligible changes, are retained.

Complete seven-weather metrics: results.json. GT defines scoring only; real GT is held outside network inference. An empty gt_boxes placeholder satisfies the legacy detector API.
