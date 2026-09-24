"""Fixed-budget controlled training, bounded checkpoints and automatic final AP."""
import argparse
import fcntl
import json
import math
import os
import time
import traceback
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from .dataset import V2XDataset,collate,to_device
from .model import V2XDetector
from .evaluate import Evaluator
from .experiment import (ROOT,FORMAL,atomic_json,save_checkpoint,seed_all,sha,now,
                         verify_sources,worker_seed)


def loader_for(cfg,split,training=False,ids=None,epoch=0):
    gen=torch.Generator();gen.manual_seed(cfg['seed']+epoch)
    return DataLoader(V2XDataset(cfg,split,training=training,ids=ids),batch_size=cfg['batch_size'],
        shuffle=training,num_workers=cfg['workers'],pin_memory=True,drop_last=False,
        collate_fn=collate,worker_init_fn=worker_seed,generator=gen)


@torch.no_grad()
def predict(model,cfg,ids):
    model.eval();result={};started=time.monotonic()
    for batch in loader_for(cfg,'val',ids=ids):
        outputs=model(to_device(batch,'cuda'))
        for frame,pred in zip(batch['frame_ids'],outputs):
            if not torch.isfinite(pred).all():raise FloatingPointError('Nonfinite prediction: '+frame)
            result[frame]=pred.cpu().numpy()
    torch.cuda.synchronize()
    return result,time.monotonic()-started


def finish_evaluation(model,cfg,run):
    evaluator=Evaluator(cfg)
    split_ids={s:(Path(cfg['split_root'])/(s+'.txt')).read_text().split() for s in ['val','test']}
    split_ids.update({s:(FORMAL/(s+'.txt')).read_text().split() for s in ['val_deduplicated','test_deduplicated']})
    final={}
    for tag in ['best','last']:
        report_path=run/('final_'+tag+'.json')
        if report_path.exists():
            final[tag]=json.loads(report_path.read_text());continue
        checkpoint=torch.load(run/(tag+'.pt'),map_location='cpu')
        model.load_state_dict(checkpoint['model'],strict=True)
        records={};inference_seconds=0;metric_seconds=0
        for split in ['val','test']:
            preds,elapsed=predict(model,cfg,split_ids[split]);inference_seconds+=elapsed
            save_checkpoint(run/('predictions_'+tag+'_'+split+'.pt'),preds)
            for name in [split,split+'_deduplicated']:
                start=time.monotonic();records[name]=evaluator.evaluate(preds,split_ids[name]);metric_seconds+=time.monotonic()-start
        report=dict(checkpoint=tag,epoch=checkpoint['epoch'],checkpoint_sha256=sha(run/(tag+'.pt')),
                    results=records,inference_seconds=inference_seconds,metric_seconds=metric_seconds,finished_at=now())
        atomic_json(report_path,report);final[tag]=report
    return final


def train(args):
    attempt_started=time.monotonic()
    cfg=json.loads((FORMAL/'config.json').read_text());verify_sources()
    run=Path(args.output) if args.output else FORMAL/args.variant
    run.mkdir(parents=True,exist_ok=True)
    lock=open(run/'.run.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (run/'status.json').exists() and json.loads((run/'status.json').read_text()).get('status')=='complete':
        raise RuntimeError('Already complete; refusing a duplicate run')
    if (run/'last.pt').exists() and not args.resume:raise RuntimeError('Checkpoint exists; pass --resume explicitly')
    torch.set_num_threads(4);torch.cuda.set_per_process_memory_fraction(cfg['memory_fraction'])
    seed_all(cfg['seed']);torch.backends.cudnn.benchmark=False
    model=V2XDetector(cfg,args.variant).cuda()
    initial=FORMAL/(args.variant+'_initial.pt')
    expected=json.loads((FORMAL/'initialization.json').read_text())[args.variant]['sha256']
    assert sha(initial)==expected
    model.load_state_dict(torch.load(initial,map_location='cpu'),strict=True)
    optimizer=torch.optim.AdamW(model.parameters(),lr=.1*cfg['learning_rate'],weight_decay=cfg['weight_decay'])
    val_ids=(FORMAL/'val_deduplicated.txt').read_text().split();evaluator=Evaluator(cfg)
    state=dict(status='starting',variant=args.variant,pid=os.getpid(),gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),
        started_at=now(),config_sha256=sha(FORMAL/'config.json'),initial_sha256=expected,
        completed_epochs=0,optimizer_updates=0,best_metric=-1.,best_epoch=None,
        train_seconds=0.,validation_seconds=0.,checkpoint_seconds=0.,failure_count=0)
    if args.resume:
        saved=torch.load(run/'last.pt',map_location='cpu');model.load_state_dict(saved['model'])
        optimizer.load_state_dict(saved['optimizer']);state=saved['state']
        state.update(pid=os.getpid(),gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),resumed_at=now())
    samples=8391;steps=math.ceil(samples/cfg['batch_size']);updates=math.ceil(steps/cfg['accumulation'])
    total_updates=cfg['epochs']*updates;warmup=cfg['warmup_epochs']*updates
    state.update(epochs=cfg['epochs'],steps_per_epoch=steps,updates_per_epoch=updates,
                 parameters=sum(p.numel() for p in model.parameters()),precision=cfg['precision'],
                 batch_size=cfg['batch_size'],effective_batch_size=cfg['effective_batch_size'])
    atomic_json(run/'config.json',dict(cfg,variant=args.variant,smoke_steps=args.smoke_steps))
    start_epoch=state['completed_epochs'];torch.cuda.reset_peak_memory_stats()
    try:
        for epoch in range(start_epoch,cfg['epochs']):
            seed_all(cfg['seed']+epoch)
            loader=loader_for(cfg,'train',training=True,epoch=epoch)
            assert len(loader.dataset)==samples and len(loader)==steps
            model.train();optimizer.zero_grad(set_to_none=True)
            start=time.monotonic();total_loss=0.;total_det=0.;total_aux=0.;seen=0
            for step,batch in enumerate(loader):
                b=len(batch['frame_ids']);group_start=(step//cfg['accumulation'])*cfg['accumulation']*cfg['batch_size']
                group_samples=min(cfg['effective_batch_size'],samples-group_start)
                output=model(to_device(batch,'cuda'));loss=output['loss']
                if not torch.isfinite(loss):raise FloatingPointError('Nonfinite loss')
                (loss*b/group_samples).backward()
                is_update=(step+1)%cfg['accumulation']==0 or step+1==steps
                if is_update:
                    norm=torch.nn.utils.clip_grad_norm_(model.parameters(),cfg['gradient_clip'])
                    if not torch.isfinite(norm):raise FloatingPointError('Nonfinite gradient')
                    u=state['optimizer_updates']
                    if u<warmup:lr=cfg['learning_rate']*(.1+.9*(u+1)/warmup)
                    else:lr=cfg['min_learning_rate']+.5*(cfg['learning_rate']-cfg['min_learning_rate'])*(1+math.cos(math.pi*(u-warmup)/(total_updates-warmup)))
                    for group in optimizer.param_groups:group['lr']=lr
                    optimizer.step();optimizer.zero_grad(set_to_none=True);state['optimizer_updates']+=1
                total_loss+=float(loss.detach())*b;total_det+=float(output['det_loss'].detach())*b
                total_aux+=float(output['aux_loss'].detach())*b;seen+=b
                if (step+1)%100==0 or step==0:
                    state.update(status='training',epoch=epoch+1,step=step+1,loss=total_loss/seen,
                        lr=optimizer.param_groups[0]['lr'],epoch_elapsed_seconds=time.monotonic()-start,
                        peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
                        peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30,updated_at=now())
                    atomic_json(run/'status.json',state)
                    print(json.dumps({k:state[k] for k in ['epoch','step','loss','lr','epoch_elapsed_seconds']}),flush=True)
                if args.smoke_steps and step+1>=args.smoke_steps:break
            torch.cuda.synchronize();elapsed=time.monotonic()-start;state['train_seconds']+=elapsed
            state['completed_epochs']=epoch+1
            state.update(step=step+1,loss=total_loss/seen,lr=optimizer.param_groups[0]['lr'],
                epoch_elapsed_seconds=elapsed,peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
                peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30,updated_at=now())
            record=dict(epoch=epoch+1,samples=seen,loss=total_loss/seen,det_loss=total_det/seen,
                        aux_loss=total_aux/seen,train_seconds=elapsed,optimizer_updates=state['optimizer_updates'])
            if epoch+1 in cfg['val_epochs'] or args.smoke_steps:
                state.update(status='validating',updated_at=now());atomic_json(run/'status.json',state)
                before=time.monotonic();ids=val_ids[:8] if args.smoke_steps else val_ids
                preds,inference_seconds=predict(model,cfg,ids)
                evaluation=evaluator.evaluate(preds,ids)
                evaluation.update(epoch=epoch+1,inference_seconds=inference_seconds,evaluation_seconds=time.monotonic()-before)
                state['validation_seconds']+=evaluation['evaluation_seconds']
                atomic_json(run/('val_epoch_%03d.json'%(epoch+1)),evaluation)
                record['val_selection_metric']=evaluation['selection_metric']
                if evaluation['selection_metric']>state['best_metric']:
                    state.update(best_metric=evaluation['selection_metric'],best_epoch=epoch+1)
                    before=time.monotonic()
                    save_checkpoint(run/'best.pt',dict(model=model.state_dict(),epoch=epoch+1,metric=state['best_metric']))
                    state['checkpoint_seconds']+=time.monotonic()-before
            before=time.monotonic()
            save_checkpoint(run/'last.pt',dict(model=model.state_dict(),optimizer=optimizer.state_dict(),epoch=epoch+1,state=state))
            state['checkpoint_seconds']+=time.monotonic()-before
            with open(run/'epochs.jsonl','a') as stream:stream.write(json.dumps(record)+'\n')
            atomic_json(run/'status.json',state)
            if args.smoke_steps:
                # Exercise checkpoint deserialization and exact model restore.
                saved=torch.load(run/'last.pt',map_location='cpu');model.load_state_dict(saved['model'],strict=True)
                state.update(status='smoke_passed',finished_at=now());atomic_json(run/'status.json',state);return
        state.update(status='final_evaluation',updated_at=now());atomic_json(run/'status.json',state)
        before=time.monotonic();finish_evaluation(model,cfg,run);state['final_evaluation_seconds']=time.monotonic()-before
        state.update(status='complete',finished_at=now(),gpu_hours_training=state['train_seconds']/3600,
            gpu_hours_process=(state['train_seconds']+state['validation_seconds']+state['checkpoint_seconds']+state['final_evaluation_seconds'])/3600)
        state['attempt_wall_seconds']=time.monotonic()-attempt_started
        atomic_json(run/'status.json',state)
    except BaseException:
        state.update(status='failed',error=traceback.format_exc(),updated_at=now());state['failure_count']+=1
        state['attempt_wall_seconds']=time.monotonic()-attempt_started
        atomic_json(run/'status.json',state);raise


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['concat','patch','taskdec'],required=True)
    parser.add_argument('--resume',action='store_true');parser.add_argument('--smoke-steps',type=int,default=0)
    parser.add_argument('--output');args=parser.parse_args()
    if args.smoke_steps and not args.output:raise ValueError('Smoke requires independent --output')
    train(args)


if __name__=='__main__':main()
