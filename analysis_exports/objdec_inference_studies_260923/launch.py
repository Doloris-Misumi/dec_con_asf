"""Detach one authorized analysis job on the host, with bounded CPU/GPU usage."""
from common import *
import argparse
import subprocess
import resource

def main():
    p=argparse.ArgumentParser();p.add_argument('job',choices=['cache_analysis','diagnostics','interventions']);args=p.parse_args()
    job=args.job; previous=HERE/(job+'_launch.json')
    if previous.exists():
        old=read(previous)
        try:
            cmd=Path('/proc')/str(old['pid'])/'cmdline'
            if (HERE/(job+'.py')).as_posix().encode() in cmd.read_bytes(): raise RuntimeError('Job already running')
        except FileNotFoundError: pass
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
        NUMBA_NUM_THREADS='2',PYTHONUNBUFFERED='1',CUDA_HOME='/usr/local/cuda-11.3',
        CUDA_VISIBLE_DEVICES='2' if job=='interventions' else '')
    if job=='interventions':
        assert read(HERE/'interventions/smoke.json')['passed']
        usage=subprocess.check_output(['nvidia-smi','--id=2','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True)
        assert int(usage.strip())<500, usage
    def setup():
        resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.nice(10)
    command=[str(ROOT/'v2x_taskdec/.venv/bin/python'),'-u',str(HERE/(job+'.py'))]
    log=HERE/(job+'.log')
    with log.open('a') as f:
        child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,start_new_session=True,preexec_fn=setup)
    record=dict(pid=child.pid,command=command,log=str(log),gpu=env['CUDA_VISIBLE_DEVICES'],at=datetime.now().astimezone().isoformat())
    write(previous,record);print(json.dumps(record))

if __name__=='__main__':main()
