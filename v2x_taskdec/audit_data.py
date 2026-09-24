"""CPU audit of actual V2X-V fields/calibration before choosing model inputs."""
import collections
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .geometry import read_calibration, camera_box_to_lidar, project_points, corners_lidar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis_exports/v2x_taskdec_260916'


def main():
    integrity = json.loads((OUT / 'data_integrity.json').read_text())
    data = Path(integrity['dataset_root']) / 'training'
    splits = Path(integrity['split_root'])
    train_ids = (splits / 'train.txt').read_text().split()
    sampled = [train_ids[i] for i in np.linspace(0, len(train_ids)-1, 12).astype(int)]
    report = dict(split_counts=integrity['split_counts'], modality_fields={}, samples=[], train_classes={})
    for key in ['velodyne', 'radar']:
        files = sorted((data / key).glob('*.bin'))
        # Divisibility across every file identifies possible float32 widths.
        candidates = [n for n in range(3, 17) if all(p.stat().st_size % (n * 4) == 0 for p in files)]
        report['modality_fields'][key] = dict(float32_width_candidates=candidates, files=len(files))
    classes = collections.Counter()
    for frame in train_ids:
        for line in (data/'label_2'/(frame+'.txt')).read_text().splitlines():
            if line.strip():
                classes[line.split()[0]] += 1
    report['train_classes'] = dict(classes)
    for frame in sampled:
        cal = read_calibration(data/'calib'/(frame+'.txt'))
        image_path = next((data/'image_2').glob(frame+'.*'))
        with Image.open(image_path) as img:
            image_size = img.size
        info = dict(frame=frame, image_size=list(image_size), calibration={k:v.tolist() for k,v in cal['values'].items()}, points={}, boxes=[])
        for key in ['velodyne','radar']:
            values = np.fromfile(data/key/(frame+'.bin'), dtype=np.float32)
            candidates = report['modality_fields'][key]['float32_width_candidates']
            info['points'][key] = {}
            for n in candidates:
                points = values.reshape(-1,n)
                info['points'][key][str(n)] = dict(count=len(points), finite=bool(np.isfinite(points).all()),
                    quantiles=np.quantile(points,[0,.01,.5,.99,1],axis=0).tolist())
        for line in (data/'label_2'/(frame+'.txt')).read_text().splitlines():
            a=line.split()
            if not a or a[0]=='DontCare': continue
            hwl=np.array(a[8:11],float);loc=np.array(a[11:14],float);ry=float(a[14])
            if np.any(hwl<=0):continue
            box=camera_box_to_lidar(loc,hwl,ry,cal)
            uv,depth=project_points(corners_lidar(box[None])[0],cal)
            rect=np.r_[uv.min(0),uv.max(0)]
            info['boxes'].append(dict(category=a[0], lidar_box=box.tolist(), bbox_label=[float(x) for x in a[4:8]],
                                      bbox_projected=rect.tolist(), all_corners_in_front=bool((depth>0).all())))
        report['samples'].append(info)
    (OUT/'data_geometry_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
    print('Saved 12 train-sample field distributions and calibration/box projections. Semantics require inspection.')


if __name__=='__main__':main()
