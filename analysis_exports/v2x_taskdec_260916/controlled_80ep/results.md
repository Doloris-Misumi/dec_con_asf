# V2X-Radar-V controlled C+L+R results

Local deduplicated split protocol; AP_R40 strict IoU 0.7/0.5/0.5. Vehicle = Car/Truck/Bus.
Best checkpoint selected on deduplicated validation strict moderate mean 3D AP. Test never selects a checkpoint.
Single seed; no statistical significance claim. Pending runs have no final AP.

| Variant | State | Epochs | Best val epoch | Train GPU h | Measured process GPU h |
|---|---|---:|---:|---:|---:|
| concat | complete | 80 | 75 | 11.904 | 17.107 |
| patch | complete | 80 | 75 | 16.932 | 22.073 |
| taskdec | complete | 80 | 80 | 19.669 | 24.999 |

| Variant | Checkpoint | Split | Vehicle | Pedestrian | Cyclist | Mean |
|---|---|---|---:|---:|---:|---:|
| concat | best | val_deduplicated | 81.53 | 62.03 | 79.36 | 74.31 |
| concat | best | test_deduplicated | 81.52 | 65.81 | 79.98 | 75.77 |
| concat | best | val | 81.54 | 62.17 | 79.37 | 74.36 |
| concat | best | test | 81.52 | 65.72 | 79.94 | 75.73 |
| concat | last | val_deduplicated | 81.38 | 61.97 | 79.34 | 74.23 |
| concat | last | test_deduplicated | 81.61 | 65.70 | 79.99 | 75.77 |
| concat | last | val | 81.40 | 62.10 | 79.36 | 74.29 |
| concat | last | test | 81.61 | 65.61 | 79.96 | 75.73 |
| patch | best | val_deduplicated | 80.39 | 58.91 | 78.97 | 72.76 |
| patch | best | test_deduplicated | 78.57 | 58.93 | 79.02 | 72.17 |
| patch | best | val | 80.37 | 59.05 | 78.99 | 72.80 |
| patch | best | test | 78.54 | 58.84 | 79.01 | 72.13 |
| patch | last | val_deduplicated | 79.74 | 58.40 | 78.66 | 72.27 |
| patch | last | test_deduplicated | 78.54 | 59.09 | 79.02 | 72.22 |
| patch | last | val | 79.69 | 58.53 | 78.69 | 72.30 |
| patch | last | test | 78.51 | 59.01 | 79.03 | 72.18 |
| taskdec | best | val_deduplicated | 80.19 | 55.72 | 78.03 | 71.31 |
| taskdec | best | test_deduplicated | 78.82 | 58.75 | 79.09 | 72.22 |
| taskdec | best | val | 79.86 | 55.86 | 78.03 | 71.25 |
| taskdec | best | test | 78.79 | 58.61 | 79.10 | 72.17 |
| taskdec | last | val_deduplicated | 80.19 | 55.72 | 78.03 | 71.31 |
| taskdec | last | test_deduplicated | 78.82 | 58.75 | 79.09 | 72.22 |
| taskdec | last | val | 79.86 | 55.86 | 78.03 | 71.25 |
| taskdec | last | test | 78.79 | 58.61 | 79.10 | 72.17 |

All classes, difficulties, strict/loose 3D and BEV metrics: `complete_metrics.csv`.

GPU hours are elapsed time occupying one GPU process (including I/O), not utilization-integrated compute.
Shared GPU services and parallel jobs may affect throughput. Setup, smoke and engineering checks are additional costs.
