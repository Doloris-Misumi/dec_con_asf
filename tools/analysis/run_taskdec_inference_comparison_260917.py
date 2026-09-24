#!/usr/bin/env python3
"""Serial ABBA benchmark on GPU2. Logs native exit status as well as JSON integrity."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis_exports/inference_optimization_260917'
statuses = []
for model, repeat in [('taskdec', 1), ('asf', 1), ('asf', 2), ('taskdec', 2)]:
    stem = f'{model}_paired_r{repeat}'
    result = OUT / f'{stem}.json'
    log = OUT / f'{stem}.log'
    if result.exists() or log.exists():
        raise FileExistsError(stem)
    command = [sys.executable, '-u', str(ROOT/'tools/analysis/benchmark_taskdec_inference_260917.py'),
               '--gpu', '2', '--model', model, '--optimization', 'graph_both',
               '--verify', '--check-adapters', '--warmup', '20', '--samples', '100',
               '--output', str(result)]
    print('START', stem, time.strftime('%Y-%m-%d %H:%M:%S'), flush=True)
    start = time.time()
    with log.open('w') as stream:
        process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    record = dict(model=model, repeat=repeat, returncode=process.returncode,
                  elapsed_s=time.time()-start, command=command, result=str(result), log=str(log))
    if result.exists():
        data = json.loads(result.read_text())
        record['complete_result'] = bool(data.get('completed') and len(data.get('rows', [])) == 100
                                        and len(data.get('verification', [])) == 120)
        record['summary'] = data.get('summary')
    else:
        record['complete_result'] = False
    statuses.append(record)
    (OUT/'comparison_process_status.json').write_text(json.dumps(statuses, indent=2)+'\n')
    print('DONE', json.dumps(record), flush=True)
    if not record['complete_result']:
        raise RuntimeError(f'{stem}: incomplete result; inspect {log}')
    if process.returncode:
        print('WARNING: native process exit was nonzero after writing a complete result; retained for audit.', flush=True)
print('ALL_COMPLETED', flush=True)
