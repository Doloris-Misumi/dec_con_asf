"""Detach the authorized eight-case evaluation on idle physical GPU2."""
import json
import os
from pathlib import Path
import resource
import subprocess
from datetime import datetime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PY='/home/hongsheng/miniconda3/envs/rl_3dod/bin/python'
assert json.loads((HERE/'smoke/status.json').read_text())['phase']=='complete'
assert json.loads((HERE/'smoke/audit.json').read_text())['passed']
if (HERE/'launch.json').exists():raise RuntimeError('Already launched; inspect existing process before resuming.')
used=int(subprocess.check_output(['nvidia-smi','--id=2','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True).strip())
assert used<512,('GPU2 busy',used)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='2',CUDA_HOME='/usr/local/cuda-11.3',
         OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',NUMBA_NUM_THREADS='4',PYTHONUNBUFFERED='1')
def setup():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.nice(10)
command=[PY,'-u',str(HERE/'run.py')]
with (HERE/'run.log').open('x') as f:
    proc=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
                          start_new_session=True,preexec_fn=setup)
record=dict(pid=proc.pid,at=datetime.now().astimezone().isoformat(),gpu=2,command=command,
            log=str(HERE/'run.log'),gpu_memory_before_mib=used,detached=True)
(HERE/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
