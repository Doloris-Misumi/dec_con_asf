"""Launch the authorized prediction export only on an idle physical GPU2."""
import datetime
import json
import os
from pathlib import Path
import resource
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'objdec_lr_val_cache'


def main():
    if (OUT / 'launch.json').exists() or (OUT / 'status.json').exists():
        raise RuntimeError('Existing attempt found; refusing duplicate launch')
    info = subprocess.check_output(['nvidia-smi', '--id=2',
        '--query-gpu=uuid,memory.used,memory.total,utilization.gpu',
        '--format=csv,noheader,nounits'], text=True).strip().split(',')
    uuid = info[0].strip()
    used, total, util = [int(v.strip()) for v in info[1:]]
    processes = subprocess.check_output(['nvidia-smi',
        '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True)
    if used > 512 or total - used < 28000 or util > 10 or uuid in processes:
        raise RuntimeError('GPU2 is no longer idle; no existing process will be stopped')
    OUT.mkdir(exist_ok=True)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='2', CUDA_HOME='/usr/local/cuda-11.3',
               OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4',
               PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
    command = [str(ROOT / 'v2x_taskdec/.venv/bin/python'), '-u', str(HERE / 'cache_objdec_lr.py')]

    def setup():
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.nice(10)

    with (OUT / 'inference.log').open('x') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True, preexec_fn=setup)
    record = dict(pid=process.pid, gpu=2, gpu_uuid=uuid, detached=True, command=command,
                  started_at=datetime.datetime.now().astimezone().isoformat(),
                  gpu_memory_before_mib=used, purpose='Prediction cache, official subset pending')
    (OUT / 'launch.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
