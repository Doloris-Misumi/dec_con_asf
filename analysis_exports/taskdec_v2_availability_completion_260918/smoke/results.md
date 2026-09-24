# Strong v2 availability: nine additional settings and CLR verification

SYNTHETIC SMOKE ONLY; three frames repeated to satisfy evaluator partitions.

C* = normalized raw RGB black frame. L* = zero height-compressed sparse output through the original dense LiDAR backbone. Local input-loss protocol; not an exact ASF corruption implementation. conf=0 retains the original upstream score prefilter 0.1.

| Setting | Sedan 3D@0.3 | Bus 3D@0.3 | Mean | Sedan 3D@0.5 | Bus 3D@0.5 | Mean |
|---|---:|---:|---:|---:|---:|---:|
| r | 1.95 | 14.63 | 8.29 | 0.00 | 14.63 | 7.32 |
| l | 39.02 | 9.76 | 24.39 | 4.88 | 9.76 | 7.32 |
| c | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| c_star | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lr | 39.02 | 9.76 | 24.39 | 24.39 | 9.76 | 17.07 |
| cr | 9.76 | 16.26 | 13.01 | 9.76 | 16.26 | 13.01 |
| cl | 39.02 | 9.76 | 24.39 | 21.95 | 9.76 | 15.85 |
| clr | 39.02 | 19.51 | 29.27 | 24.39 | 19.51 | 21.95 |
| c_star_lr | 39.02 | 19.51 | 29.27 | 24.39 | 19.51 | 21.95 |
| cl_star_r | 9.76 | 9.76 | 9.76 | 9.76 | 9.76 | 9.76 |
