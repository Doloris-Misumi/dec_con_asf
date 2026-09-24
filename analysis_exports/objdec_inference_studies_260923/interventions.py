"""Fixed epoch-70 inference interventions. GT never enters the network."""
from common import *
import argparse
import fcntl
import gc
import time
import traceback
import types
import numpy as np
import torch
from v2x_taskdec.model import V2XDetector
from v2x_taskdec.train import loader_for
from v2x_taskdec.dataset import to_device
from v2x_taskdec.evaluate import Evaluator
from v2x_taskdec.experiment import seed_all

OUT=HERE/'interventions'
CASES=['baseline','gate_mean','gate_shuffle_260923','gate_shuffle_260924','gate_shuffle_260925','no_query','no_output']

class Control:
    def __init__(self,fuser):
        self.fuser=fuser;self.original=fuser._dec_control_scores
        self.query=fuser.dec_control_query_strength;self.output=fuser.dec_control_fused_res_strength
        self.case='baseline';self.frames=[];self.audit={}
        fuser._dec_control_scores=types.MethodType(self.call,fuser)

    def select(self,case,frames):
        self.case=case;self.frames=frames
        self.fuser.dec_control_query_strength=0. if case=='no_query' else self.query
        self.fuser.dec_control_fused_res_strength=0. if case=='no_output' else self.output

    def call(self,fuser,keys,base_tokens,common_tokens,unique_tokens,control_factor=1.):
        logits,prob,gate,scores,sensor,scale=self.original(keys,base_tokens,common_tokens,unique_tokens,control_factor)
        if not self.case.startswith('gate_'): return logits,prob,gate,scores,sensor,scale
        b=len(self.frames); assert gate.numel()==b*320*320
        old=gate.reshape(b,-1);new=old.clone()
        for i,frame in enumerate(self.frames):
            if self.case=='gate_mean': new[i]=old[i].mean()
            else:
                seed=int(hashlib.sha256((self.case+':'+frame).encode()).hexdigest()[:15],16)
                generator=torch.Generator(device=gate.device);generator.manual_seed(seed)
                new[i]=old[i][torch.randperm(old.shape[1],device=gate.device,generator=generator)]
        if self.case not in self.audit:
            assert torch.allclose(old.mean(1),new.mean(1),atol=1e-6)
            if self.case!='gate_mean': assert torch.equal(old.sort(1).values,new.sort(1).values)
            self.audit[self.case]=dict(mean_preserved=True,distribution_preserved=self.case!='gate_mean',
                changed_fraction=float((old!=new).float().mean()),patches_per_frame=old.shape[1])
        gate=new.reshape(-1)
        # Update all uses of the spatial gate, including sensor scales.
        prob=(gate-fuser.dec_control_gate_min)/(fuser.dec_control_gate_max-fuser.dec_control_gate_min)
        scale=(1.+fuser.dec_control_strength*float(control_factor)*gate[:,None]*(sensor.shape[1]*sensor-1.)).clamp(
            min=fuser.dec_control_scale_min,max=fuser.dec_control_scale_max)
        return logits,prob,gate,scores,sensor,scale

def encode(model,batch):
    assert 'gt_boxes' not in batch
    state={'batch_size':len(batch['frame_ids'])}
    for key in model.cfg['modalities']:
        if key=='camera': state[key],_=model.encoders[key](batch['image'],batch['lidar_to_image'],batch['world_aug'])
        else: state[key]=model.encoders[key](batch[key],state['batch_size'])
    return state

def from_features(model,features):
    state={k:v.clone() if torch.is_tensor(v) else v for k,v in features.items()}
    assert 'gt_boxes' not in state
    state=model.fuser(state);state['spatial_features']=state['fused_feat']
    state=model.neck(state);state=model.head(state)
    result=[x.detach().cpu().numpy() for x in model.decode(state)]
    assert all(np.isfinite(x).all() for x in result)
    norms={k:float(state[k].abs().max()) for k in ['_dec_control_query_delta','_dec_control_fused_delta']}
    return result,norms

def prepare():
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='2'
    OUT.mkdir(exist_ok=True)
    torch.set_num_threads(2);torch.cuda.set_per_process_memory_fraction(.55)
    torch.backends.cudnn.benchmark=False
    cfg=read(RUNS['objdec_clr']/'config.json');cfg['workers']=2
    expected=read(RUNS['objdec_clr']/'final_best.json')
    assert sha(RUNS['objdec_clr']/'best.pt')==expected['checkpoint_sha256']
    seed_all(cfg['seed']);model=V2XDetector(cfg,'taskdec').cuda().eval()
    saved=torch.load(RUNS['objdec_clr']/'best.pt',map_location='cpu');assert saved['epoch']==70
    model.load_state_dict(saved['model'],strict=True);del saved
    return model,cfg,expected

@torch.no_grad()
def smoke(model,cfg):
    frame_ids=ids();sample=[frame_ids[i] for i in np.linspace(0,len(frame_ids)-1,8,dtype=int)]
    checks=[];control=None
    for batch in loader_for(cfg,'val',ids=sample):
        batch.pop('gt_boxes',None);batch=to_device(batch,'cuda');frames=batch['frame_ids']
        if control is None:
            features={}
            def capture(module,args):
                assert 'gt_boxes' not in args[0]
                features.update({k:v.clone() if torch.is_tensor(v) else v for k,v in args[0].items()})
            handle=model.fuser.register_forward_pre_hook(capture)
            native=[x.cpu().numpy() for x in model(batch)];handle.remove()
            control=Control(model.fuser);control.select('baseline',frames)
            reproduced,_=from_features(model,features)
            assert all(a.shape==b.shape and np.allclose(a,b,atol=1e-5,rtol=1e-5) for a,b in zip(native,reproduced))
        else:
            features=encode(model,batch);control.select('baseline',frames);native,_=from_features(model,features)
        norms={}
        for case in CASES[1:]:
            control.select(case,frames);pred,norm=from_features(model,features);norms[case]=norm
            if case=='no_query': assert norm['_dec_control_query_delta']==0 and norm['_dec_control_fused_delta']>0
            if case=='no_output': assert norm['_dec_control_fused_delta']==0 and norm['_dec_control_query_delta']>0
        control.select('baseline',frames);restored,_=from_features(model,features)
        assert all(a.shape==b.shape and np.allclose(a,b,atol=1e-5,rtol=1e-5) for a,b in zip(native,restored))
        checks.append(dict(frames=frames,baseline_restored=True,branch_checks=norms))
        status(OUT,'smoke',checked_frames=sum(len(x['frames']) for x in checks),total=8)
    write(OUT/'smoke.json',dict(passed=True,frames=sample,checks=checks,gate_checks=control.audit,
        source_sha256=sources(),peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
        no_gt_in_network=True,same_feature_native_equivalence=True))
    return control

def metric_row(case,result):
    metrics=result['metrics'];row={'case':case}
    for mode in ['3D','BEV']:
        values=[]
        for name in ['Vehicle','Pedestrian','Cyclist']:
            value=metrics['V2X/'+name+'_'+mode+'_moderate_strict'];row[name+'_'+mode]=value;values.append(value)
        row['mean_'+mode]=float(np.mean(values))
    return row

@torch.no_grad()
def infer(model,cfg,control,cases):
    frames=ids();records={case:{} for case in cases};started=time.monotonic()
    for batch in loader_for(cfg,'test',ids=frames):
        batch.pop('gt_boxes',None);batch=to_device(batch,'cuda');features=encode(model,batch)
        for case in cases:
            control.select(case,batch['frame_ids']);pred,_=from_features(model,features)
            records[case].update(zip(batch['frame_ids'],pred))
        completed=len(records[cases[0]])
        if completed%32==0 or completed==len(frames):
            status(OUT,'inference',cases=cases,completed=completed,total=len(frames),seconds=time.monotonic()-started,
                   peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30)
    for case in cases:
        assert set(records[case])==set(frames)
        np.savez_compressed(OUT/('predictions_'+case+'.npz'),**records[case])
    return records

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not args.smoke: assert read(OUT/'smoke.json')['passed']
    started=time.monotonic();before=sources()
    model,cfg,expected=prepare()
    if args.smoke:
        smoke(model,cfg);status(OUT,'smoke_passed');return
    # Verify scripts/model sources have not changed since the successful smoke.
    smoke_sources=read(OUT/'smoke.json')['source_sha256']
    assert all(before[k]==v for k,v in smoke_sources.items())
    control=Control(model.fuser)
    write(OUT/'protocol.json',dict(checkpoint=str(RUNS['objdec_clr']/'best.pt'),epoch=70,
        checkpoint_sha256=expected['checkpoint_sha256'],split=str(SPLIT),split_sha256=sha(SPLIT),frames=1486,
        cases=CASES,config=cfg,sources=before,gpu='2',memory_fraction=.55,
        baseline_max_allowed_ap_difference=.05,selection='Predeclared test interventions; no tuning or new deployment selection',
        interpretation='Inference interventions, not retrained component ablations. Gate changed consistently in token residuals, sensor scales, query and output context. Background/GT masks are not used.'))
    evaluator=Evaluator(cfg);all_results={}
    baseline_file=OUT/'result_baseline.json'
    if baseline_file.exists(): baseline=read(baseline_file)
    else:
        base=infer(model,cfg,control,['baseline'])['baseline']
        status(OUT,'scoring',case='baseline',frames=1486)
        baseline=evaluator.evaluate(base,ids());write(baseline_file,baseline);del base
    old=metric_row('baseline',expected['results']['test_deduplicated']);new=metric_row('baseline',baseline)
    difference={k:new[k]-old[k] for k in new if k!='case'}
    passed=max(abs(x) for x in difference.values())<=.05
    write(OUT/'baseline_verification.json',dict(passed=passed,differences=difference,expected=old,reproduced=new))
    assert passed, 'Baseline AP mismatch; remaining interventions not run'
    all_results['baseline']=baseline
    todo=[c for c in CASES[1:] if not (OUT/('predictions_'+c+'.npz')).exists()]
    if todo: infer(model,cfg,control,todo)
    write(OUT/'gate_audit.json',control.audit)
    del control,model;gc.collect();torch.cuda.empty_cache()
    for case in CASES[1:]:
        target=OUT/('result_'+case+'.json')
        if target.exists(): all_results[case]=read(target);continue
        status(OUT,'scoring',case=case,frames=1486,completed_cases=len(all_results),total_cases=len(CASES))
        with np.load(OUT/('predictions_'+case+'.npz')) as z:pred=dict(z)
        result=evaluator.evaluate(pred,ids());write(target,result);all_results[case]=result;del pred
    rows=[metric_row(c,all_results[c]) for c in CASES]
    for row in rows:
        for mode in ['3D','BEV']:row['delta_'+mode]=row['mean_'+mode]-rows[0]['mean_'+mode]
    csv_write(OUT/'comparison.csv',rows)
    shuffle=[r for r in rows if r['case'].startswith('gate_shuffle')]
    write(OUT/'shuffle_summary.json',{m:dict(mean=float(np.mean([r['mean_'+m] for r in shuffle])),
        minimum=min(r['mean_'+m] for r in shuffle),maximum=max(r['mean_'+m] for r in shuffle)) for m in ['3D','BEV']})
    assert sources()==before
    assert sha(RUNS['objdec_clr']/'best.pt')==expected['checkpoint_sha256']
    status(OUT,'complete',cases=len(rows),seconds=time.monotonic()-started,comparison=rows)

if __name__=='__main__':
    try:main()
    except BaseException:
        status(OUT,'failed',traceback=traceback.format_exc());raise
