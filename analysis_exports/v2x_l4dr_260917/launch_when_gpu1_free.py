"""Wait for successful Concat completion, then validate and train native L4DR.

Never signal other processes. GPU1's existing policy server is preserved.
The controller is independent of an interactive terminal or this conversation.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from datetime import datetime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
FORMAL=HERE/'matched_80ep'
CONCAT=ROOT/'analysis_exports/v2x_taskdec_260916/controlled_80ep/concat'
PYTHON=ROOT/'v2x_taskdec/.venv/bin/python'


def now(): return datetime.now().astimezone().isoformat()
def read(path): return json.loads(Path(path).read_text())
def save(path,value):
    path=Path(path);tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,indent=2));tmp.replace(path)
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def identity(pid):
    try:
        p=Path('/proc')/str(pid);s=(p/'stat').read_text().rsplit(')',1)[1].split()
        return dict(pid=pid,state=s[0],start_ticks=int(s[19]),
                    command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
    except FileNotFoundError: return None


def report(controller):
    cfg=read(FORMAL/'config.json')
    run=FORMAL/'l4dr';p=run/'status.json';state=read(p) if p.exists() else {}
    lines=['# V2X-Radar-V：L4DR 同训练日程本地适配','',
        '更新时间：'+now(),'','控制器阶段：`'+controller['status']+'`。', '',
        'GPU1 等待 Concat 训练与 best/last 最终评测全部成功完成并退出后接续，保留 PID140935 常驻服务。', '',
        '原生 L+R：PointNet2 前景筛选 → MME 双向点特征交互 → MGF 多尺度融合 → 检测头。全部从头训练。',
        '8391 帧训练、80轮、FP32、micro-batch 2、累积4次、有效batch8；同 AdamW/cosine 日程和选模规则。',
        '保留原生0.16m横向体素及网络宽度，柱高适配为8m；TaskDec为0.4m。L4DR输入L+R，其余现有组为C+L+R，因此是同日程外部架构参照，不是同模态、同预训练或同FLOPs消融。', '',
        '原始和去重val/test统一评测；主指标为1487帧去重val上严格IoU的Moderate三类平均3D AP_R40，test不参与选模。', '',
        '当前训练状态：`'+str(state.get('status','not_started'))+'`；完成轮数：'+str(state.get('completed_epochs',0))+'/80。',
        '最优轮次 / 均值：'+str(state.get('best_epoch'))+' / '+str(state.get('best_metric'))+'。', '',
        '| 轮次 | Vehicle | Pedestrian | Cyclist | 平均3D |','|---|---:|---:|---:|---:|']
    for p in sorted(run.glob('val_epoch_*.json')):
        d=read(p);m=d['metrics']
        v=[m['V2X/'+c+'_3D_moderate_strict'] for c in cfg['class_names']]+[d['selection_metric']]
        lines.append('| %d | %s |'%(d['epoch'],' | '.join('%.2f'%x for x in v)))
    for tag in ['best','last']:
        p=run/('final_'+tag+'.json')
        if p.exists():
            d=read(p);lines.extend(['','**最终 '+tag+'（epoch '+str(d['epoch'])+'）**','',
                '| 划分 | 帧数 | Vehicle | Pedestrian | Cyclist | 平均3D |','|---|---:|---:|---:|---:|---:|'])
            for split,r in d['results'].items():
                v=[r['metrics']['V2X/'+c+'_3D_moderate_strict'] for c in cfg['class_names']]+[r['selection_metric']]
                lines.append('| %s | %d | %s |'%(split,r['frames'],' | '.join('%.2f'%x for x in v)))
    lines.extend(['','配置、适配边界、检查和运行记录：`analysis_exports/v2x_l4dr_260917/matched_80ep/`。',
        '总日志：`analysis_exports/v2x_l4dr_260917/controller.log`；正式训练：`matched_80ep/l4dr/train.log`。',
        '启动记录与解释：[启动说明](taskdec_v2x_l4dr_launch_260917.md)。'])
    if controller.get('error'):lines.extend(['','运行异常：', '```',controller['error'],'```'])
    target=ROOT/'results/taskdec_v2x_l4dr_matched_training_260917.md'
    target.with_suffix('.tmp').write_text('\n'.join(lines)+'\n');target.with_suffix('.tmp').replace(target)


def resource_snapshot():
    raw=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=uuid,memory.free,utilization.gpu',
                                  '--format=csv,noheader,nounits'],text=True)
    uuid,free,util=[x.strip() for x in raw.strip().split(',')]
    raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory',
                                  '--format=csv,noheader,nounits'],text=True)
    apps=[]
    for line in raw.splitlines():
        u,p,m=[x.strip() for x in line.split(',')]
        if u==uuid:apps.append(dict(pid=int(p),memory_mib=int(m)))
    return dict(at=now(),free_mib=int(free),utilization=int(util),apps=apps)


def main():
    lock=open(FORMAL/'.controller.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert read(FORMAL/'checks_cpu.json')['passed']
    assert not (FORMAL/'l4dr/last.pt').exists()
    old=read(CONCAT/'status.json');previous=identity(old['pid'])
    if previous:assert '-m v2x_taskdec.train --variant concat' in previous['command']
    controller=dict(status='waiting_for_concat',pid=os.getpid(),started_at=now(),gpu=1,
        predecessor_pid=old['pid'],predecessor_identity=previous,preserved_gpu1_pid=140935,
        request='User authorized native L4DR after GPU1 Concat completes, with automatic evaluation.')
    save(FORMAL/'controller_status.json',controller);report(controller)
    def update(**kw):
        controller.update(kw,updated_at=now());save(FORMAL/'controller_status.json',controller);report(controller)
    try:
        stable=0
        while stable<2:
            state=read(CONCAT/'status.json');current=identity(old['pid'])
            still_original=bool(current and current['state']!='Z' and
                (previous is None or current['start_ticks']==previous['start_ticks']))
            if state['status']=='failed':raise RuntimeError('Concat failed; automatic successor was not started.')
            complete=state['status']=='complete' and all((CONCAT/('final_'+t+'.json')).exists() for t in ['best','last'])
            snapshot=resource_snapshot()
            ready=complete and not still_original and snapshot['free_mib']>=28000 and snapshot['utilization']<=30 and all(a['pid']==140935 for a in snapshot['apps'])
            stable=stable+1 if ready else 0
            update(predecessor_status=state['status'],predecessor_alive=still_original,resource_snapshot=snapshot,
                   readiness_samples=stable)
            print(now(),'waiting',state['status'],'alive',still_original,'GPU1',snapshot,flush=True)
            if stable<2:time.sleep(30)
        env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='1',CUDA_HOME='/usr/local/cuda-11.3',
            OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',NUMBA_NUM_THREADS='4',
            PYTHONDONTWRITEBYTECODE='1')
        # Each subprocess releases its complete CUDA context before the next stage.
        def stage(name,script,args,log_path):
            log_path.parent.mkdir(exist_ok=True,parents=True)
            command=['nice','-n','10',str(PYTHON),'-u',str(HERE/script)]+args
            with open(log_path,'a') as log:
                child=subprocess.Popen(command,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT,
                                       stdin=subprocess.DEVNULL)
                launch=dict(pid=child.pid,gpu=1,command=command,started_at=now(),controller_pid=os.getpid())
                save(log_path.parent/(name+'_launch.json'),launch)
                update(status=name,child=launch,log=str(log_path))
                print(now(),'START',name,'PID',child.pid,flush=True)
                while child.poll() is None:
                    update();time.sleep(30)
                code=child.returncode
            launch.update(exit_code=code,finished_at=now())
            save(log_path.parent/(name+'_launch.json'),launch)
            print(now(),'END',name,'exit',code,flush=True)
            if code:raise RuntimeError(name+' failed with exit '+str(code)+'; see '+str(log_path))
        stage('initializing','run.py',['initialize'],FORMAL/'initialize.log')
        stage('smoke_training','run.py',['smoke'],FORMAL/'smoke.log')
        stage('gpu_checks','checks.py',['gpu'],FORMAL/'checks_gpu.log')
        assert read(FORMAL/'checks_gpu.json')['passed']
        receipt={n:dict(bytes=(FORMAL/'smoke'/n).stat().st_size,sha256=sha(FORMAL/'smoke'/n)) for n in ['best.pt','last.pt']}
        save(FORMAL/'smoke/checkpoint_cleanup.json',dict(at=now(),removed=receipt,
            reason='Smoke restore and GPU checks passed; formal model resets to initial weights.'))
        for n in receipt:(FORMAL/'smoke'/n).unlink()
        stage('training','run.py',['train'],FORMAL/'l4dr/train.log')
        assert read(FORMAL/'l4dr/status.json')['status']=='complete'
        assert all((FORMAL/'l4dr'/('final_'+t+'.json')).exists() for t in ['best','last'])
        update(status='complete',finished_at=now())
    except BaseException:
        update(status='failed',error=traceback.format_exc(),finished_at=now())
        raise


if __name__=='__main__':main()
