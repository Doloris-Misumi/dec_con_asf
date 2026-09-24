"""Launch authorized controls, each as an independent persistent process."""
import argparse
import datetime
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CASES={'asf_clr':('0','patch'),'objdec_lr':('1','taskdec')}


def launch(case):
    gpu,variant=CASES[case]
    formal=HERE/(case+'_80ep')
    smoke=json.loads((formal/'smoke/status.json').read_text())
    assert smoke['status']=='smoke_passed'
    for name in ['geometry_check','head_geometry_check','modality_check']:
        assert json.loads((formal/'smoke'/(name+'.json')).read_text())['passed']
    out=formal/variant;out.mkdir(exist_ok=True)
    if (out/'launch.json').exists():raise RuntimeError('Already launched: '+case)
    info=subprocess.check_output(['nvidia-smi','--id='+gpu,
        '--query-gpu=memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True)
    used,total,util=[int(x.strip()) for x in info.strip().split(',')]
    if total-used<34000 or used>11000 or util>30:
        raise RuntimeError(f'GPU{gpu} is busy: {used}/{total} MiB, {util}%; no process will be stopped.')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu,CUDA_HOME='/usr/local/cuda-11.3',
        OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONUNBUFFERED='1',
        PYTHONDONTWRITEBYTECODE='1')
    command=[str(ROOT/'v2x_taskdec/.venv/bin/python'),'-u',str(HERE/'run.py'),'train','--case',case]
    def setup():
        resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.nice(10)
    with (out/'train.log').open('x') as log:
        p=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,
            stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=setup)
    record=dict(pid=p.pid,case=case,gpu=gpu,variant=variant,started_at=datetime.datetime.now().astimezone().isoformat(),
        command=command,log=str(out/'train.log'),gpu_memory_before_mib=used,detached=True)
    (out/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case',choices=list(CASES),required=True)
    launch(ap.parse_args().case)
