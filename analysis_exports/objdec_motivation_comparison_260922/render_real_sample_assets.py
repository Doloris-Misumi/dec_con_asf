"""Render scientific inserts from synchronized K-Radar data and saved predictions.

No inference, generated observations, box changes, or image enhancement.
"""
from pathlib import Path
import json
import hashlib
import sys
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tools.analysis.make_objdec_fig4_fig5_260919 import frames, camera_params, camera_boxes, boxes_bev
from tools.analysis.export_taskdec_bev_gate import camera_image, lidar_points

OUT = HERE / 'real_sample_assets'
OUT.mkdir(exist_ok=True)
FRAME_ID = 'seq13_rdr00146'
frame = next(f for f in frames() if f['id'] == FRAME_ID)
pred_dir = ROOT / 'analysis_exports/objdec_fig4_fig5_260919/paired_predictions/objdec'
pred_path = pred_dir / (FRAME_ID + '.npz')
pred = np.load(pred_path, allow_pickle=False)
keep = (pred['scores'] > 0.3) & (pred['labels'] == 1)
boxes, scores = pred['boxes'][keep], pred['scores'][keep]
camera = camera_image(frame)
params = camera_params(frame['seq'])
roi = np.array([0, -20, -2, 72, 20, 6])
lidar = lidar_points(frame, roi)
radar_path = Path('/home/hongsheng/k_radar_dataset/13/sprdr_00146.npy')
radar_all = np.load(radar_path, allow_pickle=False)
radar = radar_all[((radar_all[:, :3] >= roi[:3]) & (radar_all[:, :3] <= roi[3:])).all(1)]
crop = [540, 240, 820, 520]  # common detail window; includes both retained predictions


def figure(bg='white', shape=(5, 5)):
    fig = plt.figure(figsize=shape, dpi=120, facecolor=bg)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=bg)
    ax.axis('off')
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / (name + '.png'), dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)


def point_projection(points):
    k, dist, t = params
    q = points[:, :3] @ t[:3, :3].T + t[:3, 3]
    visible = q[:, 2] > .1
    uv = cv2.projectPoints(q[visible], np.zeros(3), np.zeros(3), k, dist)[0].reshape(-1, 2)
    return uv, points[visible]


projected_counts = {}
for name, points in [('lidar_input', lidar), ('radar_input', radar)]:
    uv, values = point_projection(points)
    inside = ((uv[:, 0] >= crop[0]) & (uv[:, 0] <= crop[2]) &
              (uv[:, 1] >= crop[1]) & (uv[:, 1] <= crop[3]))
    uv, values = uv[inside], values[inside]
    fig, ax = figure('#08111c')
    if name == 'lidar_input':
        colors = values[:, 2]
        ax.scatter(uv[:, 0], uv[:, 1], c=colors, cmap='turbo', vmin=-2, vmax=3,
                   s=2.4, alpha=.95, linewidths=0)
    else:
        colors = np.log10(np.maximum(values[:, 3], 1e-8))
        ax.scatter(uv[:, 0], uv[:, 1], c=colors, cmap='plasma',
                   vmin=np.log10(np.percentile(radar_all[:, 3], 5)),
                   vmax=np.log10(np.percentile(radar_all[:, 3], 99.8)),
                   s=3.1, alpha=.92, linewidths=0)
    ax.set(xlim=(crop[0], crop[2]), ylim=(crop[3], crop[1]), aspect='equal')
    save(fig, name)
    projected_counts[name] = len(uv)

# Full camera observation and same-frame prediction overlay for independent review.
for name, draw in [('camera_full', False), ('objdec_camera_full', True)]:
    fig, ax = figure(shape=(8, 4.5))
    ax.imshow(camera)
    if draw:
        camera_boxes(ax, boxes, params, '#ffb020', lw=1.7)
    ax.set(xlim=(0, 1280), ylim=(720, 0), aspect='equal')
    save(fig, name)

# Project real predicted cuboids onto the identical camera viewport.
fig, ax = figure()
ax.imshow(camera)
camera_boxes(ax, boxes, params, '#ffb020', lw=2.0)
ax.set(xlim=(crop[0], crop[2]), ylim=(crop[3], crop[1]), aspect='equal')
save(fig, 'objdec_camera_crop')

# A complementary real BEV output, using all retained model predictions.
fig, ax = figure('#08111c', shape=(6, 4.2))
pts = lidar_points(frame, np.array([0, -6.4, -2, 72, 6.4, 6]))
ax.scatter(-pts[:, 1], pts[:, 0], c='#b4c9dc', s=.8, linewidths=0, alpha=.75)
# Plot same box coordinates with x forward as vertical and -y as horizontal.
from tools.analysis.make_objdec_fig4_fig5_260919 import corners
from matplotlib.patches import Polygon
for b in boxes:
    c = corners(b)
    ax.add_patch(Polygon(np.column_stack([-c[:, 1], c[:, 0]]), closed=True,
                         fill=False, edgecolor='#ffb020', linewidth=1.5))
ax.set(xlim=(-6.4, 6.4), ylim=(5, 68), aspect='auto')
save(fig, 'objdec_bev_all_predictions')

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

model_manifest = json.loads((pred_dir / 'manifest.json').read_text())
record = {
    'frame': frame, 'camera_front0_pixels': [0, 0, 1280, 720],
    'common_camera_viewport_xyxy': crop,
    'middle_object_crop_xyxy': [665, 325, 780, 440],
    'middle_background_crop_xyxy': [865, 260, 1015, 410],
    'radar_source': str(radar_path), 'radar_resolved_source': str(radar_path.resolve()),
    'point_display_roi_xyz': roi.tolist(), 'projected_point_counts': projected_counts,
    'lidar_color': 'height z, turbo, fixed [-2,3] m',
    'radar_color': 'log10 power, plasma, source-frame 5th to 99.8th percentile',
    'point_sampling': 'all points inside display ROI and camera viewport; no added points',
    'projection': 'sequence-13 radar2camera; raw camera intrinsics plus distortion',
    'prediction_npz': str(pred_path), 'prediction_npz_sha256': digest(pred_path),
    'checkpoint': model_manifest['checkpoint'],
    'checkpoint_sha256': model_manifest['checkpoint_sha256'],
    'prediction_rule': 'all Sedan predictions with score > 0.3, no GT overlays',
    'displayed_boxes': boxes.tolist(), 'displayed_scores': scores.tolist(),
    'all_predictions_preserved': bool(keep.all()),
    'source_sha256': {str(p): digest(p) for p in [Path(frame['camera_path']),
                       Path(frame['lidar_path']), radar_path, pred_path]},
    'generated_images_used_as_observations_or_predictions': False,
    'training_or_inference_launched': False,
}
(OUT / 'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'frame': FRAME_ID, 'predictions': len(boxes), 'scores': scores.tolist(),
                  'projected_point_counts': projected_counts, 'output': str(OUT)}))
