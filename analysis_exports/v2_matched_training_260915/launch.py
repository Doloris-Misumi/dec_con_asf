"""Launch one validated run in a detached process, retaining exact source hashes."""
import argparse
import datetime
import json
import os
import resource
import subprocess
import sys
from common import HERE, ROOT, save, sha

p=argparse.ArgumentParser()
p.add_argument('--model',choices=['asf','l4dr'],required=True)
p.add_argument('--gpu',type=int,required=True)
a=p.parse_args()
assert json.loads((HERE/(a.model+'_smoke')/'status.json').read_text())['status']=='smoke_complete'
assert not (HERE/a.model/'status.json').exists(), 'Existing run: use explicit resume, do not overwrite'
assert not (HERE/(a.model+'_launch.json')).exists()
used=int(subprocess.check_output(['nvidia-smi','-i',str(a.gpu),'--query-gpu=memory.used',
    '--format=csv,noheader,nounits'],text=True).strip())
assert used<1000, ('GPU is occupied',a.gpu,used)
env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(a.gpu),OPENBLAS_NUM_THREADS='1',
    OMP_NUM_THREADS='4',NUMBA_NUM_THREADS='4')
command=[sys.executable,'-u',str(HERE/'train.py'),'--model',a.model]
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with (HERE/(a.model+'_train.log')).open('x') as log:
    process=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
        stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
record=dict(pid=process.pid,gpu=a.gpu,command=command,started_at=datetime.datetime.now().astimezone().isoformat(),
    source_sha256={x.name:sha(x) for x in sorted(HERE.glob('*.py'))},
    environment={k:env[k] for k in ['CUDA_VISIBLE_DEVICES','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS']})
save(HERE/(a.model+'_launch.json'),record)
print(json.dumps(record))
