#!/usr/bin/env python3
"""Detach the verified full-test weather-statistics job on physical GPU0."""
import datetime
import json
import os
from pathlib import Path
import resource
import subprocess

root=Path('/home/hongsheng/dec_con_asf')
out=root/'analysis_exports/objdec_fulltest_weather_260919'
smoke=json.loads((out/'smoke_verified/status.json').read_text())
assert smoke['phase']=='complete' and smoke['completed']==7
checks=json.loads((out/'smoke_verified/prediction_invariance.json').read_text())
assert max(checks.values())==0.,checks
if (out/'launch.json').exists():raise RuntimeError('Already launched; inspect before restarting.')
usage=subprocess.check_output(['nvidia-smi','--id=0','--query-gpu=memory.used,utilization.gpu',
                               '--format=csv,noheader,nounits'],text=True)
used,util=[int(x.strip()) for x in usage.strip().split(',')]
if used>10000 or util>10:
    raise RuntimeError(f'GPU0 became busy: {used} MiB, utilization {util}%; refusing launch.')
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',CUDA_HOME='/usr/local/cuda-11.3',
         OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONUNBUFFERED='1')
command=['/home/hongsheng/miniconda3/envs/rl_3dod/bin/python','-u',
         str(root/'tools/analysis/export_objdec_full_weather_means_260919.py'),'--gpu','0']

def setup():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.nice(10)

with (out/'run.log').open('x') as log:
    p=subprocess.Popen(command,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,
                       stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=setup)
record=dict(pid=p.pid,gpu=0,started_at=datetime.datetime.now().astimezone().isoformat(),
            command=command,log=str(out/'run.log'),memory_before_mib=used,detached_session=True)
(out/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
