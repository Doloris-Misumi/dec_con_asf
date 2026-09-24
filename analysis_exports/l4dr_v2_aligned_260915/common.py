import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
L4DR = Path('/home/hongsheng/L4DR/K-Radar-main-repo')
DATA = Path('/home/hongsheng/k_radar_dataset')
STRONG = ROOT/'logs/exp_260806_000825_DecControlledASFStrong_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/none/0.3'
N = 13727
CLASSES = ['Sedan', 'Bus or Truck']
WEATHER = ['normal','overcast','fog','rain','sleet','lightsnow','heavysnow']
CONDITIONS = ['all'] + WEATHER + ['day','night','urban','highway','countryside','alleyway','parkinglots','shoulder','mountain','university']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data, indent=2)+'\n')
    tmp.replace(path)


def records():
    return [json.loads(line) for line in (HERE/'manifest.jsonl').read_text().splitlines()]


def box_lines(labels):
    import numpy as np
    out = []
    for cls, box, track, avail in labels:
        x,y,z,yaw,l,w,h = [np.round(v,2) for v in box]
        out.append(f'{"sed" if cls == "Sedan" else "bus"} 0.00 0 0 50 50 150 150 {h} {w} {l} {y} {z} {x} {yaw}')
    return out
