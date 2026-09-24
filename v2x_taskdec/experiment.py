"""Shared reproducibility and atomic artifact utilities for this experiment only."""
import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis_exports/v2x_taskdec_260916'
FORMAL = OUT / 'controlled_80ep'


def now():
    return datetime.now(timezone.utc).astimezone().isoformat()


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def atomic_json(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False));os.replace(tmp,path)


def save_checkpoint(path,value):
    path=Path(path);tmp=path.with_suffix('.tmp');torch.save(value,tmp);os.replace(tmp,path)


def seed_all(seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)


def state_hash(state):
    h=hashlib.sha256()
    for key,tensor in sorted(state.items()):
        h.update(key.encode());h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def verify_sources():
    manifest=json.loads((FORMAL/'source_manifest.json').read_text())
    for path,expected in manifest.items():
        if sha(ROOT/path)!=expected:raise RuntimeError('Frozen source changed: '+path)
    for path,expected in json.loads((FORMAL/'input_manifest.json').read_text()).items():
        if sha(path)!=expected:raise RuntimeError('Frozen input changed: '+path)


def worker_seed(worker_id):
    value=torch.initial_seed()%2**32;np.random.seed(value);random.seed(value)
