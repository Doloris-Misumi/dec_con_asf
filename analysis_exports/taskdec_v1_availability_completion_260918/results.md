# TaskDec v1 six additional availability settings

Same Robust model_0; all 10,065 test frames; original v1 evaluator. C* = raw RGB black frame; L* = no LiDAR returns, zero sparse output followed by the original dense LiDAR backbone. Local corruption protocol, not an exact reproduction of undocumented ASF corruption details.

| Setting | AP3D@0.3 | AP3D@0.5 | APBEV@0.3 | APBEV@0.5 |
|---|---:|---:|---:|---:|
| c | 0.86 | 0.16 | 0.88 | 0.21 |
| l | 79.58 | 60.05 | 87.77 | 77.96 |
| r | 49.81 | 26.64 | 59.04 | 46.80 |
| c_star | 0.00 | 0.00 | 0.00 | 0.00 |
| c_star_lr | 88.36 | 67.41 | 88.84 | 88.09 |
| cl_star_r | 50.26 | 34.83 | 51.59 | 49.27 |
