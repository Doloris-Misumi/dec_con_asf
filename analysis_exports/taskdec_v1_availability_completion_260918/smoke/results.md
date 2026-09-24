# TaskDec v1 six additional availability settings

SYNTHETIC SMOKE CHECK ONLY: three frames repeated to satisfy the original evaluator partition size; not dataset AP results. C* = raw RGB black frame; L* = no LiDAR returns, zero sparse output followed by the original dense LiDAR backbone. Local corruption protocol, not an exact reproduction of undocumented ASF corruption details.

| Setting | AP3D@0.3 | AP3D@0.5 | APBEV@0.3 | APBEV@0.5 |
|---|---:|---:|---:|---:|
| c | 0.00 | 0.00 | 0.00 | 0.00 |
| l | 81.82 | 61.82 | 81.82 | 81.82 |
| r | 50.91 | 50.91 | 50.91 | 50.91 |
| c_star | 0.00 | 0.00 | 0.00 | 0.00 |
| c_star_lr | 81.82 | 81.82 | 81.82 | 81.82 |
| cl_star_r | 50.91 | 50.91 | 50.91 | 50.91 |
