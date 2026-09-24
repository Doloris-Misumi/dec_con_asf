# VoD storage and download notes

Date: 2026-08-29

## What is known from official sources

The official VoD documentation does not publicly state one total download size in GB. Access is request-based via the VoD website, and download links/passwords are sent after approval.

Official data facts relevant for storage:

- 8600 synchronized frames.
- Camera: rectified JPG, `1936 x 1216`.
- LiDAR: `.bin`, `Nx4`, `[x, y, z, reflectance]`.
- Radar: `.bin`, `Nx7`, `[x, y, z, RCS, v_r, v_r_compensated, time]`.
- Radar variants: single scan, 3-scan accumulation, 5-scan accumulation.
- KITTI-like folder layout:
  - `lidar`
  - `radar`
  - `radar_3_scans`
  - `radar_5_scans`
- Each sub-dataset layout contains `ImageSets`, `training/calib`, `training/velodyne`, `training/image_2`, `training/label_2`, and corresponding `testing` folders.

## Practical disk estimate

Because official size is not listed publicly, plan with a safety margin.

### Minimum for our first experiment: VoD `L+R`

Need:

- `lidar`
- `radar_5_scans`
- labels/calibration/splits
- no camera training initially

Estimated extracted data:

- LiDAR: about `12-25 GB`, depending on average point count.
- Radar 5-scan point clouds: likely below `1-3 GB`.
- Labels/calibration/ImageSets: below `0.5 GB`.
- Camera images, if bundled or duplicated in the downloaded `lidar`/`radar_5_scans` folders: add about `5-20 GB` per image copy.

Recommended allocation for clean `L+R` work:

> Reserve at least `60-80 GB`.

This should cover extracted data, generated info files, predictions, logs, and several checkpoints.

### Full VoD all-modality local copy

Need:

- `lidar`
- `radar`
- `radar_3_scans`
- `radar_5_scans`
- images/calibration/labels/test folders
- optional duplicated `image_2` folders

Estimated extracted data:

> `60-100 GB` is a reasonable planning range.

Recommended allocation including training artifacts:

> Reserve `150-200 GB`.

This is enough for all raw/extracted VoD data, preprocessing caches, 5-10 experiment folders, and checkpoints.

## Local machine status

Checked on 2026-08-29:

- `/home/hongsheng`: about `5.0 TB` available.
- `/tmp`: about `534 GB` available.
- current `/home/hongsheng/dec_con_asf`: about `72 GB`.

So storage is not the blocker on this machine.

## Devkit clone/download attempt

Attempted:

- `git clone --depth 1 https://github.com/tudelft-iv/view-of-delft-dataset.git third_party/view-of-delft-dataset`

Result:

- First attempt failed due network.
- Escalated attempt revealed a global git proxy pointing to `127.0.0.1:1080`, which was unavailable.
- A temporary no-proxy git clone started but was too slow/stalled and was interrupted.

Attempted fallback:

- Download GitHub source zip with `curl`.

Result:

- Download reached about `49.7 MB` in 90 seconds, then timed out.
- GitHub source zip did not support byte-range resume in this context.
- A partial file remains at `/tmp/view-of-delft-dataset-main.zip` and is not a complete archive.

Conclusion:

- The official devkit should be cloned/downloaded again when shell network is stable.
- For now, official web/raw docs are enough to design the adapter.
- The devkit is also installable as `vod-tudelft`, but installing it should be deferred until the data path is known.

## Storage recommendation for our project

Use this directory convention:

```text
/home/hongsheng/datasets/view_of_delft/
  lidar/
  radar_5_scans/
  devkit/
```

For the first `L+R` experiment, do not download/extract all radar variants unless required.

Priority:

1. `lidar`
2. `radar_5_scans`
3. official devkit
4. camera/images only if moving to `C+L+R`
5. `radar` and `radar_3_scans` only for temporal/scan accumulation ablations

## Sources checked

- VoD official page: https://tudelft-iv.github.io/view-of-delft-dataset/
- Getting started / folder layout: https://tudelft-iv.github.io/view-of-delft-dataset/docs/GETTING_STARTED.html
- Sensors and data: https://tudelft-iv.github.io/view-of-delft-dataset/docs/SENSORS_AND_DATA.html
- Annotation docs: https://tudelft-iv.github.io/view-of-delft-dataset/docs/ANNOTATION.html
- PP-Radar/OpenPCDet guide: https://github.com/tudelft-iv/view-of-delft-dataset/blob/main/PP-Radar.md
