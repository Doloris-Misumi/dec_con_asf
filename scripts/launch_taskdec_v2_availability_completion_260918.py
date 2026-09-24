#!/usr/bin/env python3
"""Launch the authorized v2 nine-case plus CLR check evaluation on idle physical GPU2."""
import datetime
import json
import os
from pathlib import Path
import resource
import subprocess

root = Path('/home/hongsheng/dec_con_asf')
out = root / 'analysis_exports/taskdec_v2_availability_completion_260918'
assert json.loads((out / 'smoke/status.json').read_text())['phase'] == 'complete'
if (out / 'launch.json').exists():
    raise RuntimeError('A launch record already exists; inspect it before restarting.')
used = int(subprocess.check_output([
    'nvidia-smi', '--id=2', '--query-gpu=memory.used',
    '--format=csv,noheader,nounits'], text=True).strip())
if used > 512:
    raise RuntimeError(f'GPU2 is occupied ({used} MiB); refusing to overlap jobs.')
env = dict(os.environ, CUDA_VISIBLE_DEVICES='2', CUDA_HOME='/usr/local/cuda-11.3',
           OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4',
           PYTHONUNBUFFERED='1')
command = ['/home/hongsheng/miniconda3/envs/rl_3dod/bin/python', '-u',
           str(root / 'tools/analysis/run_taskdec_v2_availability_completion_260918.py')]

def child_setup():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.nice(10)

with (out / 'run.log').open('x') as log:
    process = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.DEVNULL,
                               stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True, preexec_fn=child_setup)
record = dict(pid=process.pid, started_at=datetime.datetime.now().astimezone().isoformat(),
              gpu=2, command=command, log=str(out / 'run.log'),
              gpu_memory_before_mib=used, detached_session=True)
(out / 'launch.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
