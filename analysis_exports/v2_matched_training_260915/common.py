import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
L4DR=Path('/home/hongsheng/L4DR/K-Radar-main-repo')
DATA=Path('/home/hongsheng/k_radar_dataset')
REFERENCE=ROOT/'analysis_exports/l4dr_v2_aligned_260915'
STRONG=ROOT/'logs/exp_260806_000825_DecControlledASFStrong_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16'
CLASSES=['Sedan','Bus or Truck']
WEATHER=['normal','lightsnow','heavysnow','rain','sleet','overcast','fog']
CONDITIONS=['all']+WEATHER+['day','night','urban','highway','countryside','alleyway','parkinglots','shoulder','mountain','university']
SEED=20250215
EPOCHS=11
BATCH=2

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def save(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)

def records(split):
    return [json.loads(x) for x in (HERE/(split+'_manifest.jsonl')).read_text().splitlines()]
