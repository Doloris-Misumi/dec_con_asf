"""CPU-only scientific rendering of NEW synchronized K-Radar observations.

Actual photographs are embedded independently in the SVG assembly. No generated
sensor imagery, inference, invented radar bins, or edited prediction boxes.
"""
from pathlib import Path
import sys, json, hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tools.analysis.make_objdec_fig4_fig5_260919 import frames, camera_params, camera_boxes
from tools.analysis.export_taskdec_bev_gate import camera_image, lidar_points

IDS = ['seq22_rdr00484', 'seq20_rdr00628', 'seq9_rdr00347', 'seq7_rdr00272']
PREDS = ROOT/'analysis_exports/objdec_fig4_fig5_260919/paired_predictions/objdec'
FRAMES = {f['id']: f for f in frames()}
ROI = np.array([0, -40, -2, 72, 40, 6])
MODEL = json.loads((PREDS/'manifest.json').read_text())
records = []
pooled = []
radars = {}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def canvas(bg='white', figsize=(8, 4.5)):
    fig = plt.figure(figsize=figsize, dpi=140, facecolor=bg)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=bg)
    ax.axis('off')
    return fig, ax

def save(fig, p):
    fig.savefig(p, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)

for fid in IDS:
    f = FRAMES[fid]
    source = Path('/home/hongsheng/k_radar_dataset')/str(f['seq'])/f"sprdr_{f['radar_id']}.npy"
    points = np.load(source)
    r = np.hypot(points[:, 0], points[:, 1])
    theta = np.arctan2(points[:, 1], points[:, 0])
    valid = ((r > 0) & (r < 72) & (np.abs(theta) < np.deg2rad(53)) &
             (points[:, 2] >= -2) & (points[:, 2] <= 6))
    radars[fid] = (source, points[valid], r[valid], theta[valid])
    pooled.append(np.log10(np.maximum(points[valid, 3], 1e-8)))

vmin, vmax = np.percentile(np.concatenate(pooled), [2, 99.5])
for fid in IDS:
    f = FRAMES[fid]
    out = HERE/'samples'/fid
    out.mkdir(parents=True, exist_ok=True)
    camera = camera_image(f)
    predpath = PREDS/(fid+'.npz')
    pred = np.load(predpath, allow_pickle=False)
    keep = (pred['scores'] > .3) & (pred['labels'] == 1)
    boxes, scores = pred['boxes'][keep], pred['scores'][keep]
    for name, draw in [('camera', False), ('prediction', True)]:
        fig, ax = canvas()
        ax.imshow(camera)
        if draw:
            camera_boxes(ax, boxes, camera_params(f['seq']), '#ffb020', lw=2.0)
        ax.set(xlim=(0, 1280), ylim=(720, 0), aspect='equal')
        save(fig, out/(name+'.png'))

    pts = lidar_points(f, ROI)
    # Orthographic oblique view: a rigid rotation, no height exaggeration.
    # Camera looking from behind the sensor, tilted 60 degrees downward.
    phi = np.deg2rad(60)
    screen_x = -pts[:, 1]
    screen_y = pts[:, 0]*np.sin(phi) + pts[:, 2]*np.cos(phi)
    fig, ax = canvas('black', (8, 5.8))
    ax.scatter(screen_x, screen_y, s=.85, c='white', alpha=.94, linewidths=0)
    ax.set(xlim=(-40, 40), ylim=(-1.5, 67), aspect='equal')
    save(fig, out/'lidar.png')

    source, radar, r, theta = radars[fid]
    # Aggregate measured sparse xyz-power into range/azimuth display bins.
    rbins = np.arange(0, 72.001, .8)
    abins = np.deg2rad(np.arange(-53, 53.001, 1.0))
    ri = np.clip(np.searchsorted(rbins, r, side='right')-1, 0, len(rbins)-2)
    ai = np.clip(np.searchsorted(abins, theta, side='right')-1, 0, len(abins)-2)
    power = np.full((len(rbins)-1, len(abins)-1), -np.inf)
    np.maximum.at(power, (ri, ai), np.log10(np.maximum(radar[:, 3], 1e-8)))
    occupied = np.isfinite(power)
    # Unobserved sparse bins are explicitly colored dark; no interpolation.
    shown = np.where(occupied, power, vmin-1)
    rr, aa = np.meshgrid(rbins, abins, indexing='ij')
    xx, yy = -rr*np.sin(aa), rr*np.cos(aa)
    fig, ax = canvas('white', (8, 5.8))
    cm = plt.get_cmap('turbo').copy()
    cm.set_under('#20143e')
    ax.pcolormesh(xx, yy, shown, cmap=cm, vmin=vmin, vmax=vmax,
                  shading='flat', rasterized=True, edgecolors='none', antialiased=False)
    ax.set(xlim=(-60, 60), ylim=(-2, 74), aspect='equal')
    save(fig, out/'radar.png')

    rec = {
        'id': fid, 'frame': f, 'camera_front0_crop': [0,0,1280,720],
        'lidar_display': {'roi_xyz': ROI.tolist(), 'num_points': len(pts),
            'projection': 'orthographic, screen=(-y, x*sin(60deg)+z*cos(60deg)); no height exaggeration',
            'style': 'all retained points, white on black'},
        'radar_display': {'source': str(source), 'resolved_source': str(source.resolve()),
            'input_type': 'preprocessed sparse xyz-power, NOT dense raw range-azimuth spectrum',
            'range_m': [0,72], 'azimuth_deg': [-53,53], 'height_m': [-2,6],
            'range_bin_m': .8, 'azimuth_bin_deg': 1.0,
            'aggregation': 'max log10(power) per occupied bin',
            'empty_bin_color': '#20143e', 'interpolation': False,
            'common_vmin_vmax': [float(vmin),float(vmax)],
            'num_points': len(radar), 'occupied_bins': int(occupied.sum()),
            'all_bins': int(occupied.size)},
        'prediction': {'source': str(predpath), 'rule': 'ALL Sedan boxes with score > 0.3',
            'boxes': boxes.tolist(), 'scores': scores.tolist(), 'number': len(boxes),
            'checkpoint': MODEL['checkpoint'], 'checkpoint_sha256': MODEL['checkpoint_sha256'],
            'GT_boxes_plotted': False},
        'sha256': {str(p): sha(p) for p in [Path(f['camera_path']), Path(f['lidar_path']), source, predpath]},
        'generated_observations': False, 'GPU_used': False,
    }
    (out/'provenance.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2)+'\n')
    records.append(rec)
    print(fid, 'LiDAR', len(pts), 'radar',len(radar), 'predictions',len(boxes))

(HERE/'candidates.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n')

# Contact sheet of the numeric renders; originals remain in the individual folders.
fig, axes = plt.subplots(len(records), 4, figsize=(16, 3.2*len(records)), facecolor='white')
for i, rec in enumerate(records):
    for j, name in enumerate(['camera','lidar','radar','prediction']):
        axes[i,j].imshow(plt.imread(HERE/'samples'/rec['id']/(name+'.png')))
        axes[i,j].axis('off')
        if i == 0:
            axes[i,j].set_title(['Camera (front0)','LiDAR (oblique view)','4D radar (sparse power)','ObjDec predictions'][j], fontsize=14, pad=12)
        if j == 0:
            axes[i,j].text(0, -.12, rec['id']+'  |  '+rec['frame']['weather'],
                           transform=axes[i,j].transAxes, fontsize=11)
fig.subplots_adjust(left=.015,right=.985,bottom=.06,top=.93,wspace=.045,hspace=.20)
fig.savefig(HERE/'new_sample_candidates.png',dpi=160)
plt.close(fig)
