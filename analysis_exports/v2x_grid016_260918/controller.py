"""Run TaskDec on GPU3; queue Concat until GPU2's v2 job completes and exits."""
import datetime
import fcntl
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMAL = HERE / 'matched_80ep'
V2 = ROOT / 'analysis_exports/taskdec_v2_availability_completion_260918'


def now():
    return datetime.datetime.now().astimezone().isoformat()


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def write(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n')
    tmp.replace(path)


def free(gpu):
    vals = subprocess.check_output(['nvidia-smi', '-i', str(gpu),
        '--query-gpu=memory.used,memory.free,utilization.gpu', '--format=csv,noheader,nounits'], text=True)
    used, available, util = [int(x.strip()) for x in vals.strip().split(',')]
    return used < 512 and available > 45000 and util <= 30, dict(used_mib=used, free_mib=available, utilization=util)


def setup_child():
    resource.setrlimit(resource.RLIMIT_CORE, (0,0))
    os.nice(10)


def main():
    lock = (HERE / '.controller.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for name in ['taskdec','concat']:
        assert read(FORMAL / ('smoke_' + name) / 'status.json')['status'] == 'smoke_passed'
    queued = {'taskdec':3, 'concat':2}
    active, ended, stable = {}, {}, {'taskdec':0, 'concat':0}
    state = dict(pid=os.getpid(), started_at=now(), status='running', prerequisite=str(V2 / 'status.json'))
    while queued or active:
        for name, entry in list(active.items()):
            child, log, began = entry
            if child.poll() is not None:
                log.close()
                actual = read(FORMAL / name / 'status.json')
                ended[name] = dict(exit_code=child.returncode, status=actual.get('status'),
                                   seconds=time.monotonic()-began, finished_at=now())
                del active[name]
                print('FINISHED', name, ended[name], flush=True)
        for name, gpu in list(queued.items()):
            if read(FORMAL / name / 'status.json').get('status') == 'complete':
                ended[name] = dict(exit_code=0,status='complete');del queued[name];continue
            if name == 'concat':
                previous = read(V2 / 'status.json')
                state['v2_phase'] = previous.get('phase')
                if previous.get('phase') != 'complete':
                    stable[name] = 0
                    continue
                pid = read(V2 / 'launch.json').get('pid')
                if pid and Path('/proc', str(pid)).exists():
                    stable[name] = 0
                    continue
            ok, snapshot = free(gpu)
            state['gpu%d'%gpu] = snapshot
            stable[name] = stable[name] + 1 if ok else 0
            if stable[name] < 2:
                continue
            run = FORMAL / name;run.mkdir(exist_ok=True)
            assert not (run / 'last.pt').exists(), 'Inspect unfinished run before explicit resume.'
            command = [str(ROOT / 'v2x_taskdec/.venv/bin/python'), '-u', str(HERE / 'run.py'),
                       'train', '--variant', name]
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), CUDA_HOME='/usr/local/cuda-11.3',
                       OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='1',
                       PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
            log = (run / 'train.log').open('a')
            child = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True, preexec_fn=setup_child)
            active[name] = (child,log,time.monotonic());del queued[name]
            write(run / 'launch.json', dict(pid=child.pid, gpu=gpu, started_at=now(),
                                            command=command, resource_snapshot=snapshot))
            print('STARTED', name, 'GPU', gpu, 'PID', child.pid, flush=True)
        state.update(updated_at=now(), queued=queued, ended=ended,
            active={name:dict(pid=v[0].pid,gpu=3 if name=='taskdec' else 2) for name,v in active.items()})
        write(HERE / 'controller_status.json', state)
        if queued or active:
            time.sleep(30)
    state.update(status='complete' if all(d['exit_code']==0 and d['status']=='complete' for d in ended.values())
                 else 'finished_with_failures', finished_at=now())
    write(HERE / 'controller_status.json', state)


if __name__ == '__main__':
    main()
