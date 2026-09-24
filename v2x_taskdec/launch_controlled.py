"""One controller, GPU0 TaskDec; GPU1 concat then patch. Never signals other jobs."""
import fcntl
import json
import os
import subprocess
import time
from .experiment import ROOT,FORMAL,atomic_json,now,verify_sources
from .report import main as report


def available(gpu):
    row=subprocess.check_output(['nvidia-smi','-i',str(gpu),
        '--query-gpu=memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
    free,util=[int(v.strip()) for v in row.split(',')]
    return free>=26000 and util<=30,dict(free_mib=free,utilization=util)


def main():
    lock=open(FORMAL/'.controller.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify_sources()
    queues={0:['taskdec'],1:['concat','patch']};active={};ended={};checks={0:0,1:0};logs={};started={}
    controller=dict(pid=os.getpid(),started_at=now(),schedule=queues,status='running')
    while queues[0] or queues[1] or active:
        for gpu,child in list(active.items()):
            if child.poll() is not None:
                name=logs[gpu][0];logs[gpu][1].close();ended[name]=child.returncode;del active[gpu]
                with open(FORMAL/name/'process_costs.jsonl','a') as stream:
                    stream.write(json.dumps(dict(pid=child.pid,exit_code=child.returncode,gpu=gpu,
                        wall_seconds=time.monotonic()-started[gpu],finished_at=now()))+'\n')
                checks[gpu]=0
        for gpu in queues:
            if gpu in active or not queues[gpu]:continue
            name=queues[gpu][0];run=FORMAL/name
            status=json.loads((run/'status.json').read_text()) if (run/'status.json').exists() else {}
            if status.get('status')=='complete':queues[gpu].pop(0);ended[name]=0;continue
            ok,snapshot=available(gpu);controller['gpu%d'%gpu]=snapshot
            checks[gpu]=checks[gpu]+1 if ok else 0
            if checks[gpu]<3:continue
            run.mkdir(exist_ok=True);env=os.environ.copy()
            env.update(CUDA_VISIBLE_DEVICES=str(gpu),CUDA_HOME='/usr/local/cuda-11.3',
                OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
            command=['nice','-n','10',str(ROOT/'v2x_taskdec/.venv/bin/python'),'-u','-m','v2x_taskdec.train','--variant',name]
            if (run/'last.pt').exists():command.append('--resume')
            log=open(run/'train.log','a');child=subprocess.Popen(command,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT)
            active[gpu]=child;logs[gpu]=(name,log);started[gpu]=time.monotonic();queues[gpu].pop(0)
            atomic_json(run/'launch.json',dict(command=command,pid=child.pid,gpu=gpu,started_at=now(),resource_snapshot=snapshot))
            print('Started',name,'GPU',gpu,'PID',child.pid,flush=True)
        controller.update(updated_at=now(),active={str(g):dict(pid=p.pid,variant=logs[g][0]) for g,p in active.items()},ended=ended)
        atomic_json(FORMAL/'controller_status.json',controller);report()
        # Initial resource samples are separated by 20 s. Training monitoring
        # uses five-minute intervals; no repeated full-directory/log scans.
        time.sleep(20 if any(queues[g] and g not in active for g in queues) else 300)
    controller.update(status='complete' if all(v==0 for v in ended.values()) else 'finished_with_failures',finished_at=now())
    atomic_json(FORMAL/'controller_status.json',controller);report()


if __name__=='__main__':main()
