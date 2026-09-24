"""Native ASF/L4DR training, matched Strong sample/update budget, automatic final eval."""
import argparse
import ast
import copy
import datetime
import json
import os
import random
import sys
import time
import traceback
import types
from pathlib import Path
from common import HERE, ROOT, L4DR, REFERENCE, STRONG, CLASSES, SEED, EPOCHS, BATCH, records, sha, save

p=argparse.ArgumentParser()
p.add_argument('--model',choices=['asf','l4dr'],required=True)
p.add_argument('--smoke-steps',type=int,default=0)
p.add_argument('--resume',action='store_true')
args=p.parse_args()
outdir=HERE/(args.model+('_smoke' if args.smoke_steps else ''))
outdir.mkdir(exist_ok=True)
assert args.resume or not (outdir/'status.json').exists(),'Do not overwrite an existing run'
code_root=ROOT if args.model=='asf' else L4DR
os.chdir(ROOT)
sys.path[:0]=[str(code_root/'ops'),str(code_root)]
import numpy as np
import torch
import yaml
from easydict import EasyDict
from torch.utils.data import DataLoader, RandomSampler
from models.skeletons import build_skeleton
if args.model=='asf':
    from datasets.kradar_fusion_v1_0 import KRadarFusion_v1_0 as NativeDataset
else:
    from datasets.kradar_detection_v2_0 import KRadarDetection_v2_0 as NativeDataset

cfg=EasyDict(yaml.safe_load((HERE/(args.model+'_config.yml')).read_text()))
preflight=json.loads((HERE/'preflight.json').read_text())
assert preflight['status']=='complete'
assert sha(HERE/(args.model+'_config.yml'))==preflight['configs'][args.model]
all_train=records('train');all_test=records('test')
train_rows=all_train
if args.smoke_steps:
    # Stratify the forward/backward smoke across the complete training index.
    ix=np.linspace(0,len(all_train)-1,args.smoke_steps*BATCH,dtype=int)
    train_rows=[all_train[i] for i in ix]

class CachedDataset(NativeDataset):
    def load_dict_item(self,path_data,split):
        selected=train_rows if split=='train' else all_test
        return [{'meta':copy.deepcopy(row['meta'])} for row in selected]

    def __getitem__(self,index):
        original=self.list_dict_item[index]
        self.list_dict_item[index]={'meta':copy.deepcopy(original['meta'])}
        try:return super().__getitem__(index)
        finally:self.list_dict_item[index]=original

random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED);torch.cuda.manual_seed_all(SEED)
torch.set_num_threads(4)
torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
torch.cuda.reset_peak_memory_stats()
state=dict(status='initializing',model=args.model,mode='smoke' if args.smoke_steps else 'full_training',
    started_at=datetime.datetime.now().astimezone().isoformat(),pid=os.getpid(),
    gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),gpu_name=torch.cuda.get_device_name(),
    seed=SEED,precision='FP32',batch_size=BATCH,epochs=EPOCHS,steps_per_epoch=7193,
    target_steps=args.smoke_steps or 79123,global_step=0,completed_epochs=0,
    training_wall_seconds=0.,step_wall_seconds=0.,failure_count=0,
    config_sha256=sha(HERE/(args.model+'_config.yml')),
    train_manifest_sha256=sha(HERE/'train_manifest.jsonl'),test_manifest_sha256=sha(HERE/'test_manifest.jsonl'),
    checkpoint_selection='fixed final epoch',initialization=preflight['initialization'][args.model])
save(outdir/'status.json',state)

tree=ast.parse((ROOT/'utils/util_pipeline.py').read_text())
fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='dict_datum_to_kitti')
conversion={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),'unaltered_taskdec_serializer','exec'),conversion)
stub=types.SimpleNamespace(val_keyword={CLASSES[0]:'sed',CLASSES[1]:'bus'},dict_cls_id_to_name={1:CLASSES[0],2:CLASSES[1]})

def export_prediction(output,row,directory):
    pred=output['pred_dicts'][0]
    boxes=pred['pred_boxes'].detach().cpu().numpy();scores=pred['pred_scores'].detach().cpu().numpy()
    labels=pred['pred_labels'].detach().cpu().numpy();keep=scores>.3
    if not (np.isfinite(boxes).all() and np.isfinite(scores).all() and set(labels.tolist()).issubset({1,2})):
        def stats(value):
            a=value.detach().float().cpu().numpy()
            f=a[np.isfinite(a)]
            return dict(shape=list(a.shape),nonfinite=int((~np.isfinite(a)).sum()),
                finite_min=float(f.min()) if f.size else None,finite_max=float(f.max()) if f.size else None)
        diagnostic=dict(index=row['index'],labels=np.unique(labels).tolist(),
            invalid_boxes=int((~np.isfinite(boxes)).any(axis=1).sum()),
            invalid_retained_boxes=int((~np.isfinite(boxes[keep])).any(axis=1).sum()),
            tensors={k:stats(v) for k,v in output.items() if torch.is_tensor(v) and
                ('pred' in k or 'spatial_features' in k)},
            nonfinite_state_keys=[k for k,v in net.state_dict().items() if not bool(torch.isfinite(v).all())])
        save(outdir/'nonfinite_prediction_diagnostic.json',diagnostic)
        raise RuntimeError('Invalid predictions; see nonfinite_prediction_diagnostic.json: '+str(diagnostic))
    gt=[(c,CLASSES.index(c)+1,b,t) for c,b,t,av in row['meta']['label']]
    datum=dict(label=[gt],pp_bbox=[[s]+list(b) for b,s in zip(boxes[keep],scores[keep])],
        pp_cls=labels[keep].tolist(),pp_num_bbox=int(keep.sum()),pp_desc=row['meta']['desc'])
    datum=conversion['dict_datum_to_kitti'](stub,datum)
    name=f"{row['index']:06d}.txt"
    assert '\n'.join(datum['kitti_gt'])==(STRONG/'test_kitti/none/0.3/all/gts'/name).read_text().strip()
    (directory/name).write_text('\n'.join(datum['kitti_pred'])+'\n')
    return int(keep.sum())

def checkpoint(epoch,optimizer,scheduler):
    payload=dict(model_state_dict=net.state_dict(),optimizer_state_dict=optimizer.state_dict(),
        scheduler_state_dict=scheduler.state_dict(),completed_epoch=epoch,
        python_rng=random.getstate(),numpy_rng=np.random.get_state(),torch_rng=torch.get_rng_state(),
        cuda_rng=torch.cuda.get_rng_state_all(),run_state=state)
    tmp=outdir/'checkpoint_last.pt.tmp';torch.save(payload,tmp);tmp.replace(outdir/'checkpoint_last.pt')

try:
    ds=CachedDataset(cfg,split='train')
    cfg.DATASET.NUM=len(all_train)
    net=build_skeleton(cfg).cuda()
    init_checks={}
    if args.model=='asf':
        source=json.loads((HERE/'encoder_sources.json').read_text())
        strong_weights=torch.load(STRONG/'models/model_10.pt',map_location='cpu')
        for kind,name in [('CAMERA','cam'),('LIDAR','ldr'),('RADAR','rdr')]:
            path=ROOT/source[kind]['PRETRAINED']
            weights=torch.load(path,map_location='cpu')
            retained={k:v for k,v in weights.items() if not k.startswith('head.')}
            loaded=getattr(net,name).load_state_dict(retained,strict=True)
            assert not loaded.missing_keys and not loaded.unexpected_keys
            matched=0
            for key,value in retained.items():
                if any(key.endswith(x) for x in ['running_mean','running_var','num_batches_tracked']):continue
                assert torch.equal(value,strong_weights[name+'.'+key]),(name,key)
                matched+=1
            init_checks[name]=dict(path=str(path.resolve()),sha256=sha(path),strict_load=True,
                retained_keys=len(retained),discarded_detection_head_keys=len(weights)-len(retained),
                fixed_nonstat_tensors_equal_to_strong=matched)
        del weights,retained,strong_weights
        assert all(not v.requires_grad for name in ['cam','ldr','rdr'] for v in getattr(net,name).parameters())
    else:
        init_checks=dict(full_detector_checkpoint_loaded=False,all_native_modules_present=True,
            backbone=cfg.MODEL.BACKBONE_2D.NAME)
    state.update(initialization_checks=init_checks,total_parameters=sum(v.numel() for v in net.parameters()),
        trainable_parameters=sum(v.numel() for v in net.parameters() if v.requires_grad))
    optimizer=torch.optim.AdamW(net.parameters(),lr=cfg.OPTIMIZER.LR,betas=tuple(cfg.OPTIMIZER.BETAS),
        weight_decay=cfg.OPTIMIZER.WEIGHT_DECAY)
    scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=7193,eta_min=cfg.OPTIMIZER.MIN_LR)
    # Match Strong's TYPE_TOTAL_ITER='every': scheduler advances every step,
    # is not reset at epoch boundaries, and uses the original 7,193-step T_max.
    start_epoch=0
    if args.resume:
        ck=torch.load(outdir/'checkpoint_last.pt',map_location='cpu')
        net.load_state_dict(ck['model_state_dict'],strict=True)
        optimizer.load_state_dict(ck['optimizer_state_dict']);scheduler.load_state_dict(ck['scheduler_state_dict'])
        random.setstate(ck['python_rng']);np.random.set_state(ck['numpy_rng']);torch.set_rng_state(ck['torch_rng'])
        torch.cuda.set_rng_state_all(ck['cuda_rng'])
        start_epoch=ck['completed_epoch']+1
        state.update(ck['run_state']);state['pid']=os.getpid()
        del ck
    trainable={k:v for k,v in net.named_parameters() if v.requires_grad}
    probe_names=[k for k in trainable if ('conv_cls.weight' in k or 'Conv_LG.0.0.weight' in k)]
    if args.model=='asf':probe_names+=list(k for k in trainable if k.startswith('fuser.'))[:1]
    probes={k:trainable[k].detach().cpu().clone() for k in probe_names}
    net.train();optimizer.zero_grad()
    state['status']='training';save(outdir/'status.json',state)
    epochs_to_run=1 if args.smoke_steps else EPOCHS
    with (outdir/'training_metrics.jsonl').open('a') as metrics:
        for epoch in range(start_epoch,epochs_to_run):
            net.train()
            generator=torch.Generator().manual_seed(SEED+epoch)
            sampler=RandomSampler(ds,generator=generator)
            loader=DataLoader(ds,batch_size=BATCH,sampler=sampler,num_workers=4,collate_fn=ds.collate_fn,
                drop_last=True,generator=generator)
            assert len(loader)==(args.smoke_steps or 7193)
            epoch_start=time.monotonic();loss_sum=0.;loss_min=float('inf');loss_max=0.
            for step,batch in enumerate(loader):
                step_start=time.monotonic()
                output=net(batch);output['epoch']=epoch+1
                loss=net.loss(output)
                assert loss.ndim==0 and bool(torch.isfinite(loss)) and loss.item()>0,('nonfinite/zero loss',epoch,step)
                loss.backward()
                if args.smoke_steps or step==0:
                    grad_count=sum(1 for v in trainable.values() if v.grad is not None)
                    assert grad_count>0
                    assert all(bool(torch.isfinite(v.grad).all()) for v in trainable.values() if v.grad is not None)
                    state['finite_gradient_parameter_tensors']=grad_count
                    if args.model=='asf':
                        assert all(v.grad is None for name in ['cam','ldr','rdr'] for v in getattr(net,name).parameters())
                        state['frozen_encoder_gradients_absent']=True
                optimizer.step();scheduler.step();optimizer.zero_grad()
                loss_value=float(loss.detach());loss_sum+=loss_value;loss_min=min(loss_min,loss_value);loss_max=max(loss_max,loss_value)
                state['global_step']+=1;state['step_wall_seconds']+=time.monotonic()-step_start
                state.update(epoch_index=epoch,step_in_epoch=step+1,last_loss=loss_value,lr=optimizer.param_groups[0]['lr'],
                    peak_cuda_allocated_gib=torch.cuda.max_memory_allocated()/1024**3)
                del loss,output,batch
                if args.smoke_steps or (step+1)%100==0:
                    progress=dict(epoch=epoch,step=step+1,global_step=state['global_step'],loss=loss_value,
                        lr=state['lr'],epoch_elapsed_seconds=time.monotonic()-epoch_start)
                    metrics.write(json.dumps(progress)+'\n');metrics.flush()
                    state['current_epoch_elapsed_seconds']=progress['epoch_elapsed_seconds']
                    save(outdir/'status.json',state)
                    print('TRAIN',json.dumps(progress),flush=True)
            elapsed=time.monotonic()-epoch_start
            state['training_wall_seconds']+=elapsed
            state.update(completed_epochs=epoch+1,gpu_hours_training=state['training_wall_seconds']/3600,
                epoch_mean_loss=loss_sum/len(loader),epoch_min_loss=loss_min,epoch_max_loss=loss_max)
            metrics.write(json.dumps(dict(epoch=epoch,epoch_complete=True,mean_loss=state['epoch_mean_loss'],
                seconds=elapsed,global_step=state['global_step']))+'\n');metrics.flush()
            if not args.smoke_steps:checkpoint(epoch,optimizer,scheduler)
            save(outdir/'status.json',state)
            print('EPOCH COMPLETE',epoch+1,'/',epochs_to_run,'steps',state['global_step'],'mean loss',state['epoch_mean_loss'],'seconds',elapsed,flush=True)
    state['probe_parameter_changes']={k:float((trainable[k].detach().cpu()-v).abs().max()) for k,v in probes.items()}
    assert state['probe_parameter_changes'] and any(v>0 for v in state['probe_parameter_changes'].values())
    if args.smoke_steps:
        save(outdir/'batchnorm_diagnostic.json',{
            name:dict(mean_absmax=float(module.running_mean.abs().max()),
                var_min=float(module.running_var.min()),var_max=float(module.running_var.max()),
                batches=int(module.num_batches_tracked))
            for name,module in net.named_modules() if isinstance(module,torch.nn.modules.batchnorm._BatchNorm)
                and module.track_running_stats})
        net.eval()
        test_ds=CachedDataset(cfg,split='test')
        indices=[0,5000,10000,13726]
        test_loader=DataLoader(torch.utils.data.Subset(test_ds,indices),batch_size=1,shuffle=False,
            num_workers=2,collate_fn=test_ds.collate_fn)
        directory=outdir/'preds';directory.mkdir(exist_ok=True)
        counts=[]
        with torch.no_grad():
            for index,batch in zip(indices,test_loader):
                counts.append(export_prediction(net(batch),all_test[index],directory))
        state.update(smoke_eval_frames=len(indices),smoke_eval_indices=indices,
            smoke_eval_prediction_counts=counts,smoke_kitti_gt_exact_match=True)
        state.update(status='smoke_complete',finished_at=datetime.datetime.now().astimezone().isoformat())
        save(outdir/'status.json',state);print('SMOKE COMPLETE',json.dumps(state),flush=True)
        torch.cuda.synchronize();sys.stdout.flush();sys.stderr.flush()
        os.execv(sys.executable,[sys.executable,'-c','print("Training smoke exited successfully")'])
    assert state['global_step']==79123 and state['completed_epochs']==11
    state.update(status='final_inference',training_finished_at=datetime.datetime.now().astimezone().isoformat())
    save(outdir/'status.json',state)
    net.eval()
    test_ds=CachedDataset(cfg,split='test')
    test_loader=DataLoader(test_ds,batch_size=1,shuffle=False,num_workers=4,collate_fn=test_ds.collate_fn)
    pred_dir=outdir/'preds';pred_dir.mkdir(exist_ok=True)
    infer_start=time.monotonic()
    with torch.no_grad():
        for i,batch in enumerate(test_loader):
            row=all_test[i];output=net(batch)
            export_prediction(output,row,pred_dir)
            state['evaluation_samples']=i+1
            if (i+1)%100==0:save(outdir/'status.json',state);print('FINAL INFERENCE',i+1,len(all_test),flush=True)
            del batch,output
    state.update(status='predictions_complete',inference_wall_seconds=time.monotonic()-infer_start)
    save(outdir/'status.json',state)
    torch.cuda.synchronize();sys.stdout.flush();sys.stderr.flush()
    os.execv(sys.executable,[sys.executable,'-u',str(HERE/'evaluate.py'),'--model',args.model])
except BaseException as error:
    state.update(status='failed',failure_count=state.get('failure_count',0)+1,error=repr(error),
        failed_at=datetime.datetime.now().astimezone().isoformat())
    save(outdir/'status.json',state)
    traceback.print_exc();sys.stdout.flush();sys.stderr.flush()
    # Keep the real failure code while avoiding known native-extension teardown crashes.
    os.execv(sys.executable,[sys.executable,'-c','raise SystemExit(1)'])
