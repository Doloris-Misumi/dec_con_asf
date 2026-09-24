"""CPU-only, deterministic training-label audit; no models/points/images loaded."""
import json
import sys
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(ROOT))
from v2x_taskdec.geometry import read_calibration, camera_box_to_lidar

cfg = json.loads((BASE / 'controlled_80ep/config.json').read_text())
all_ids = (Path(cfg['split_root']) / 'train.txt').read_text().split()
ids = [all_ids[i] for i in np.linspace(0, len(all_ids)-1, 512, dtype=int)]
data = Path(cfg['data_root']) / 'training'
roi = np.asarray(cfg['point_cloud_range'])
step = np.asarray(cfg['voxel_size'][:2]) * 4
xs = np.arange(roi[0]+step[0]/2, roi[3], step[0])
ys = np.arange(roi[1]+step[1]/2, roi[4], step[1])
gx, gy = np.meshgrid(xs, ys)
centers = np.stack([gx.ravel(), gy.ravel()], axis=1)
margin = cfg['resolved_fuser']['PATCH_DEC_FG_MARGIN']
stats = dict(frames=len(ids), gt_by_class=[0,0,0],foreground_patches=0,
    mixed_class_patches=0, order_dependent_class_patches=0,
    pedestrian_support_patches=0, pedestrian_support_assigned_other=0,
    pedestrian_gt_without_support=0, pedestrian_gt_without_pedestrian_class_target=0)
pedestrian_sizes = []
for frame in ids:
    cal = read_calibration(data / 'calib' / (frame+'.txt'))
    boxes = []
    for line in (data / 'label_2' / (frame+'.txt')).read_text().splitlines():
        fields = line.split()
        mapped = cfg['label_map'].get(fields[0]) if fields else None
        if mapped not in cfg['class_names']:
            continue
        dims = np.asarray(fields[8:11], dtype=np.float32)
        if np.any(dims <= 0):
            continue
        box = camera_box_to_lidar(np.asarray(fields[11:14],dtype=np.float32),dims,float(fields[14]),cal)
        if not ((box[:3]>=roi[:3]).all() and (box[:3]<roi[3:]).all()):
            continue
        cls = cfg['class_names'].index(mapped)
        boxes.append((box, cls))
        stats['gt_by_class'][cls] += 1
        if cls == 1:
            pedestrian_sizes.append(box[3:5].tolist())
    membership = np.zeros((len(centers), 3), dtype=bool)
    first = np.full(len(centers), -1, dtype=int)
    last = first.copy()
    pedestrian_masks = []
    for box, cls in boxes:
        delta = centers - box[:2]
        co, si = np.cos(box[6]), np.sin(box[6])
        lx, ly = delta[:,0]*co+delta[:,1]*si, -delta[:,0]*si+delta[:,1]*co
        mask = (np.abs(lx)<=box[3]/2+margin) & (np.abs(ly)<=box[4]/2+margin)
        membership[mask,cls] = True
        first[mask & (first<0)] = cls
        last[mask] = cls
        if cls == 1:
            pedestrian_masks.append(mask)
    stats['foreground_patches'] += int((last>=0).sum())
    stats['mixed_class_patches'] += int((membership.sum(1)>1).sum())
    stats['order_dependent_class_patches'] += int((first!=last).sum())
    stats['pedestrian_support_patches'] += int(membership[:,1].sum())
    stats['pedestrian_support_assigned_other'] += int((membership[:,1] & (last!=1)).sum())
    for mask in pedestrian_masks:
        stats['pedestrian_gt_without_support'] += int(not mask.any())
        stats['pedestrian_gt_without_pedestrian_class_target'] += int(not (mask & (last==1)).any())
stats.update(pedestrian_median_length_width=np.median(pedestrian_sizes,axis=0).tolist(),
    mixed_class_fraction=stats['mixed_class_patches']/stats['foreground_patches'],
    pedestrian_support_overwritten_fraction=stats['pedestrian_support_assigned_other']/stats['pedestrian_support_patches'],
    patch_physical_size_m=step.tolist(),foreground_margin_m=margin,
    sampling='512 evenly spaced training IDs, selected without model results; unaugmented labels only',
    limitations='NumPy reproduction of target assignment. Does not quantify augmented training or AP causality.',
    frame_ids=ids)
out=BASE/'pedestrian_label_audit_260916.json'
out.write_text(json.dumps(stats,indent=2)+'\n')
print(json.dumps({k:v for k,v in stats.items() if k!='frame_ids'},indent=2))
