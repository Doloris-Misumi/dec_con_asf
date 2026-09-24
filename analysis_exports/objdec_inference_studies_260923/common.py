"""Isolated inference studies; never modify training sources or checkpoints."""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
RUNS = {
    'objdec_clr': ROOT / 'analysis_exports/v2x_grid016_260918/matched_80ep/taskdec',
    'objdec_lr': ROOT / 'analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec',
    'asf': ROOT / 'analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch',
    'l4dr': ROOT / 'analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr',
}
SPLIT = ROOT / 'analysis_exports/v2x_grid016_260918/matched_80ep/test_deduplicated.txt'

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False))
    tmp.replace(p)

def status(out, phase, **kwargs):
    value = dict(phase=phase, at=datetime.now().astimezone().isoformat(), pid=os.getpid(), **kwargs)
    write(out / 'status.json', value)
    print(json.dumps(value, ensure_ascii=False), flush=True)

def csv_write(path, rows):
    if not rows: return
    with Path(path).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def ids():
    values = SPLIT.read_text().split()
    assert len(values) == len(set(values)) == 1486
    return values

def sources():
    paths = list((ROOT/'v2x_taskdec').rglob('*.py')) + list(HERE.glob('*.py'))
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}
