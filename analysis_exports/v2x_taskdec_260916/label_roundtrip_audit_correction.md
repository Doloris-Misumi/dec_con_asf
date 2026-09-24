# Train-label coordinate roundtrip audit

The first `label_roundtrip_audit.json` used OpenCV 4.8.1 polygon intersection as a reference. Its reported near-zero or one-third IoUs for almost coincident rectangles are **not valid evidence of a calibration or model error**. All files are retained to expose this failed reference computation.

The follow-up `label_roundtrip_bounds_audit.json` adds an analytic lower bound that does not depend on any polygon-intersection library. For each rectangle, let `r` be its half-diagonal, `delta` the roundtrip yaw error, `t` the BEV center displacement, and `e` the maximum half-dimension mismatch. Eroding all edges by `m = 2 r sin(|delta|/2) + ||t|| + e + 1e-10` yields a rectangle contained in both the original and restored boxes. Multiplying its area by the exact vertical overlap gives a conservative intersection volume and therefore a lower bound on 3D IoU.

The complete locked training split (8,391 frames) has the following center-ROI labels:

| Class | All ROI boxes | Easy | Moderate | Hard | Minimum guaranteed roundtrip 3D IoU |
|---|---:|---:|---:|---:|---:|
| Vehicle | 31,283 | 15,296 | 26,503 | 27,883 | 0.997670 |
| Pedestrian | 18,880 | 10,870 | 18,243 | 18,413 | 0.998708 |
| Cyclist | 19,436 | 11,471 | 18,480 | 18,662 | 0.999696 |

Difficulty counts overlap. The maximum location error is 4.215e−6 m and maximum yaw error is 0.000220724 radians. No box has a guaranteed IoU below its strict class threshold. This is a geometric consistency check, **not detection AP**, an independent ground-truth calibration measurement, or an assessment of all possible label errors.

The fixed official evaluation kernel was also checked directly on 29 labels from training frames 000419, 000287, 000664 and 009004, including examples where OpenCV failed. Its minimum actual 3D IoU was 0.999956012; see `near_coincident_evaluator_check.json`. The formal evaluator does not use OpenCV, and neither training source nor protocol was changed.

Reproduction of the complete train-label analytic audit:

```bash
cd /home/hongsheng/dec_con_asf
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  v2x_taskdec/.venv/bin/python analysis_exports/v2x_taskdec_260916/audit_label_roundtrip.py
```

The `min_bev_iou`, `min_3d_iou` and `below_strict_iou` fields remaining in the bounds JSON are deliberately retained OpenCV diagnostics. Use `min_guaranteed_3d_iou` and `guaranteed_iou_below_strict` for the analytic conclusion.
