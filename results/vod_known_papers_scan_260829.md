# VoD known papers scan

Date: 2026-08-29

## Short verdict

VoD is not an obscure dataset. Since 2025, it has become one of the main public benchmarks for 4D radar point-cloud 3D detection, especially radar-camera (`R+C`) and radar-only (`R`) settings. There are already CVPR, ICCV, AAAI, RA-L, and T-ITS papers reporting on it.

However, most strong VoD papers are not `C+L+R` availability-aware fusion papers. They are mainly:

- radar-camera fusion,
- radar-only detection,
- LiDAR-radar weather robustness.

So VoD is useful if we want to answer "does TaskDec generalize beyond K-Radar?" It is not necessary if the paper's main claim stays on K-Radar + ASF.

## Important papers using VoD

| Paper / method | Venue | Main modality on VoD | Why it matters |
|---|---|---|---|
| View-of-Delft dataset / PP-Radar baseline | RA-L 2022, ICRA 2022 presentation | R, L, C available; radar-only focus | Dataset foundation; establishes VoD as multi-class 3+1D radar benchmark. |
| L4DR | AAAI 2025 Oral | L+R | Directly relevant to our LiDAR-radar / weather robustness story; uses VoD with simulated fog and K-Radar real weather. |
| SCKD | AAAI 2025 | R student, L+R teacher | Strong radar-only distillation paper; claims VoD SOTA among radar-only methods. |
| HGSFusion | AAAI 2025 | R+C | Strong radar-camera fusion; public code/model zoo; reports VoD and TJ4DRadSet. |
| RaCFormer | CVPR 2025 | R+C | Query-based radar-camera fusion; reports nuScenes and VoD; top-tier visibility. |
| CVFusion | ICCV 2025 | R+C | Very strong VoD/TJ4DRadSet radar-camera paper; reports large mAP gains on VoD. |
| ZFusion | CVPRW 2025 | R+C | Workshop paper, but directly on 4D radar-camera VoD. |
| MAFF-Net | RA-L 2025 | R-only | Strong radar-only baseline with public repo/model zoo; useful if we do radar branch sanity. |
| MSSF | IEEE T-ITS 2025 | R+C | Strong journal paper; reports VoD and TJ4DRadSet. |
| R4Det | CVPR 2026 | R+C | New high-profile radar-camera SOTA on VoD/TJ4DRadSet. |
| RPGFusion | CVPR 2026 | R+C | New high-profile radar-prior guided fusion; reports SOTA on VoD/TJ4DRadSet. |
| RaGS | CVPR 2026 | R+C | Uses 3D Gaussian representation for 4D radar + monocular cue; reports VoD/TJ4DRadSet/OmniHD-Scenes. |

## What this means for us

If we do a quick `L+R` VoD experiment:

- It can compare conceptually with L4DR.
- It can show external generalization for TaskDec under radar point-cloud input.
- But it will not directly compete with the newest CVPR/ICCV VoD leaderboard, because the hottest VoD track is `R+C`, not `L+R`.

If we do a serious VoD experiment:

- We would probably need `R+C` or `C+L+R`.
- That means adapting camera calibration, image preprocessing, LSS/depth, and VoD evaluation.
- The competition is already quite strong: CVFusion, R4Det, RPGFusion, RaGS.

Therefore:

> Do not do VoD just because the dataset exists. Do it only if we can reuse/stand up a clean VoD baseline quickly and report TaskDec-vs-ASF-like gains under identical encoders.

## Recommendation

For the current paper:

1. Do not make VoD mandatory.
2. If time remains, do a small VoD `L+R` validation experiment as an appendix.
3. Do not chase VoD SOTA unless we are willing to build a serious `R+C` pipeline.
4. In the main text, cite VoD papers only to show that external 4D radar point-cloud fusion is active and nontrivial.

Suggested sentence:

> Although recent 4D radar-camera works such as CVFusion, R4Det, RPGFusion, and RaGS have made VoD an increasingly competitive benchmark, their focus is radar-camera fusion under point-cloud radar inputs. Our main evaluation therefore focuses on K-Radar, where ASF provides a direct availability-aware C+L+R baseline; we leave broader VoD-style radar point-cloud generalization as future work.

## Official leaderboard note

The active VoD detection leaderboard page is reachable, but the current crawled page shows only the table header and submission link, not a populated public leaderboard. Many papers report VoD validation numbers in their own tables rather than relying on the public leaderboard page.

## Sources checked

- VoD official page and benchmark: https://intelligent-vehicles.org/datasets/view-of-delft/
- VoD active detection leaderboard: https://viewofdelft-dataset.tudelft.nl/challenge/leaderboard/detection/
- Original VoD/PP-Radar paper: https://repository.tudelft.nl/record/uuid%3A663863c1-35b8-48a5-9bc7-e775df8d7fac
- L4DR AAAI 2025: https://ojs.aaai.org/index.php/AAAI/article/view/32397
- L4DR code: https://github.com/ylwhxht/L4DR
- SCKD AAAI 2025: https://ojs.aaai.org/index.php/AAAI/article/view/32966
- HGSFusion AAAI 2025: https://doi.org/10.1609/aaai.v39i3.32328
- HGSFusion code: https://github.com/garfield-cpp/HGSFusion
- RaCFormer CVPR 2025: https://openaccess.thecvf.com/CVPR2025?day=2025-06-14
- CVFusion ICCV 2025: https://openaccess.thecvf.com/content/ICCV2025/html/Zhong_CVFusion_Cross-View_Fusion_of_4D_Radar_and_Camera_for_3D_ICCV_2025_paper.html
- ZFusion CVPRW 2025: https://cvpr.thecvf.com/virtual/2025/35800
- MAFF-Net RA-L 2025 code: https://github.com/TRV-Lab/MAFF-Net
- MSSF T-ITS 2025: https://trid.trb.org/View/2561903
- R4Det CVPR 2026: https://openaccess.thecvf.com/content/CVPR2026/html/Xia_R4Det_4D_Radar-Camera_Fusion_for_High-Performance_3D_Object_Detection_CVPR_2026_paper.html
- RPGFusion CVPR 2026: https://openaccess.thecvf.com/content/CVPR2026/html/Qiu_RPGFusion_4D_Radar_Prior-Guided_Multi-Modal_Fusion_for_3D_Detection_CVPR_2026_paper.html
- RaGS CVPR 2026: https://openaccess.thecvf.com/content/CVPR2026/html/Bai_RaGS_Unleashing_3D_Gaussian_Splatting_from_4D_Radar_and_Monocular_CVPR_2026_paper.html
