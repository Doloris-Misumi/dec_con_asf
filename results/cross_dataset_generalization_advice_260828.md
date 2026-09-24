# Cross-dataset generalization advice for TaskDec Robust

Date: 2026-08-28

## Short verdict

Do not block the paper on a new external dataset. For the current paper, the safer main route is:

1. K-Radar v1.0 main table at `conf_thr=0.3`.
2. K-Radar v2.0 as in-family generalization.
3. Strong ablations, weather breakdown, sensor-availability/R+L evaluation, and protocol sensitivity.

If there is extra time and compute, add View-of-Delft (VoD) as a small external generalization experiment. VoD is the only external dataset that is both conceptually useful and engineering-realistic enough for this project.

## Why external generalization is helpful but not mandatory

TaskDec Robust is an ASF-compatible controller. The central claim is not "a universal detector across all autonomous-driving datasets," but "a task-aware decoupled controller improves availability-aware canonical patch fusion." That claim can be supported convincingly inside K-Radar if the paper includes:

- fair `conf_thr=0.3` protocol comparison,
- K-Radar v2.0 Sedan+Bus generalization,
- sensor-availability evaluation such as C+L+R and L+R,
- weather-condition breakdown,
- ablations isolating PatchDec, foreground gate, sensor reliability scaling, and task context.

An external dataset would mainly answer a likely reviewer question:

> Is the method only exploiting K-Radar-specific radar tensors / labels / ROI / confidence protocol?

So external data is a plus for robustness of the story, not a prerequisite for the main K-Radar SOTA claim.

## Dataset ranking

### 1. K-Radar v2.0

Priority: must-do / already started.

Why:

- Same project ecosystem, same modality family, lowest engineering risk.
- Moves beyond v1.0 Sedan-only to wider ROI and Sedan+Bus.
- Directly tests whether the controller survives more classes and a different evaluation setup.

How to present:

- Put in main paper if results are stable.
- If Bus/Rain remains weak, present v2.0 as appendix or limitation/failure analysis.

### 2. View-of-Delft

Priority: best optional external dataset.

Why:

- VoD has 8600+ synchronized calibrated frames with 64-layer LiDAR, stereo camera, 3+1D radar, and 3D boxes.
- It has an official detection benchmark and devkit.
- Its KITTI-like organization and OpenPCDet guidance make engineering migration more realistic than nuScenes.
- Recent methods such as L4DR, MSSF, RCTDistill, DSFusion, HGSFusion, and SCKD use VoD, so reviewers recognize it.

Main caveat:

- VoD radar is radar point cloud data, not K-Radar RTNH-style 4D tensor input. The current `dec_con_asf` repo has only K-Radar dataset loaders and K-Radar-specific radar preprocessing/encoder code, so this is a real port rather than a config swap.

Recommended scope:

- Start with L+R or C+R/L+R availability, not full C+L+R.
- Use a shared implementation where both baseline and TaskDec use identical VoD encoders and detection head.
- Compare "ASF-like canonical fusion" vs "TaskDec-controlled canonical fusion" under the same split/protocol.
- Treat leaderboard SOTA as context, not as the main target.

Minimum publishable table:

| Dataset | Modality | Baseline | TaskDec | Metric |
|---|---:|---:|---:|---|
| VoD val | L+R or C+R | ASF-like canonical fusion | TaskDec controller | official VoD mAP / AP by class |

This is enough to support "generalizes beyond K-Radar" if the gain is clear.

### 3. TJ4DRadSet

Priority: second optional external dataset, only after VoD.

Why:

- It has 7757 synchronized frames, camera, LiDAR, and 4D radar descriptions, 3D boxes, and KITTI-like organization.
- It is used by several recent radar-camera fusion works together with VoD.

Caveats:

- The official repository says that, due to policy restrictions, the complete released data is currently the 4D radar data; LiDAR status/access/completeness needs to be verified before planning C+L+R or L+R experiments.
- Dataset access and NDA process can delay the paper.

Recommendation:

- Do not choose TJ4DRadSet as the first external generalization target unless the data is already available locally and confirmed complete.

### 4. nuScenes

Priority: not recommended for this paper.

Why:

- nuScenes is excellent for generic availability-aware fusion, but its radar is conventional multi-radar point targets, not the 4D radar setting emphasized by K-Radar/VoD/TJ4DRadSet.
- It requires new dataset pipeline, new radar encoder assumptions, nuScenes metrics, multi-camera handling, and likely a different baseline stack.
- This would become a separate engineering project and dilute the current K-Radar/ASF story.

Recommendation:

- Mention as future work if needed.
- Do not spend current paper time porting TaskDec to nuScenes.

### 5. Astyx HiRes2019 and RaDelft

Priority: not useful as main generalization.

Astyx:

- Has camera, LiDAR, radar, calibration, and 3D ground truth, but only 546 entries.
- Good for sanity checks, too small for a strong generalization claim.

RaDelft:

- Has radar data at different processing levels, synchronized with LiDAR, camera, and odometry.
- More aligned with radar detection/semantic labeling than direct 3D detection AP in the same style as K-Radar.
- Better as future radar-representation work than as a quick TaskDec detector benchmark.

## Practical recommendation

Current writing plan:

1. Finish the paper around K-Radar v1.0/v2.0.
2. Make ablations and protocol transparency very strong.
3. Add VoD only if a minimal baseline+TaskDec pipeline can be completed without delaying the main paper.

If doing VoD, keep the goal small:

- one split,
- one modality setting first, preferably L+R,
- same encoders/head for baseline and TaskDec,
- report relative gains and availability robustness,
- use external VoD SOTA papers only as context.

Do not make external SOTA the target. The target should be "TaskDec improves an ASF-style canonical fusion baseline outside K-Radar."

## Suggested paper wording

If no external dataset is finished:

> We further evaluate on K-Radar v2.0, which expands the original Sedan-only v1.0 setting to a wider ROI and multiple classes, and conduct extensive modality-availability and weather-condition analyses to assess generalization within the 4D-radar all-weather detection setting.

If VoD is finished:

> To examine whether the proposed decoupled controller is tied to K-Radar-specific radar tensors, we additionally instantiate the same canonical-fusion interface on View-of-Delft radar/LiDAR features. Under identical encoders and detection heads, TaskDec improves the ASF-style fusion baseline, indicating that the controller generalizes to radar point-cloud based 3+1D sensing.

## Sources checked

- VoD homepage: https://intelligent-vehicles.org/datasets/view-of-delft/
- VoD sensors/data: https://github.com/tudelft-iv/view-of-delft-dataset/blob/main/docs/SENSORS_AND_DATA.md
- TJ4DRadSet official repository: https://github.com/TJRadarLab/TJ4DRadSet
- nuScenes official overview/detection task: https://www.nuscenes.org/
- RaDelft official repository: https://github.com/RaDelft/RaDelft-Dataset
- L4DR AAAI 2025: https://ojs.aaai.org/index.php/AAAI/article/view/32397
- MSSF repository: https://github.com/EricLiuhhh/MSSF
- RCTDistill ICCV 2025: https://openaccess.thecvf.com/content/ICCV2025/html/Bang_RCTDistill_Cross-Modal_Knowledge_Distillation_Framework_for_Radar-Camera_3D_Object_Detection_ICCV_2025_paper.html
- SCKD AAAI 2025: https://ojs.aaai.org/index.php/AAAI/article/view/32966
- HGSFusion AAAI 2025: https://doi.org/10.1609/aaai.v39i3.32328
