"""Eight predeclared fixed-checkpoint K-Radar v1 inference interventions.

Same-frame encoders are reused; only runtime fusion controls change. Original
training/model/evaluator sources and checkpoint files are never edited.
"""
import argparse
import copy
import csv
import datetime
import fcntl
import gc
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import types

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'ops'),str(ROOT/'tools/analysis')]
import run_taskdec_v1_availability_completion_260918 as legacy

CASES=['baseline','gate_mean','gate_shuffle_260923','gate_shuffle_260924',
       'gate_shuffle_260925','no_query','no_output','no_query_output']
NAMES={'baseline':'Full ObjDec','gate_mean':'Frame-mean gate',
       'gate_shuffle_260923':'Shuffled gate (260923)','gate_shuffle_260924':'Shuffled gate (260924)',
       'gate_shuffle_260925':'Shuffled gate (260925)','no_query':'No query increment',
       'no_output':'No output increment','no_query_output':'No query/output increments'}
HISTORY=ROOT/'results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/per_condition/all_conf0.3.json'
EXPECTED_SHA='99eb07e8a0b01ec397d3f2ac890091fe539194149a2c542cf41c465c9f02a2d3'

def read(path):return json.loads(Path(path).read_text())
def write(path,value):legacy.write(Path(path),value)
def sha(path):return legacy.digest(path)

def source_hashes():
    paths=list((ROOT/'models').rglob('*.py'))+list((ROOT/'utils/kitti_eval').glob('*.py'))
    paths += [ROOT/'utils/util_pipeline.py',ROOT/'pipelines/pipeline_detection_v1_0.py',
              ROOT/'datasets/kradar_fusion_v1_0.py',Path(legacy.__file__).resolve(),Path(__file__).resolve(),
              ROOT/'configs/v1_0/cfg_A2F_scl_final.yml',ROOT/'resources/split/test.txt',legacy.CONFIG]
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))}

def status(out,phase,**values):
    value=dict(phase=phase,pid=os.getpid(),gpu=2,updated_at=legacy.now(),**values)
    write(out/'status.json',value);print(json.dumps(value,ensure_ascii=False),flush=True)

class Control:
    def __init__(self,fuser):
        self.fuser=fuser;self.original=fuser._dec_control_scores
        self.q=fuser.dec_control_query_strength;self.o=fuser.dec_control_fused_res_strength
        self.case='baseline';self.frame='';self.audit={};self.calls=0
        assert not fuser.training
        fuser._dec_control_scores=types.MethodType(self.scores,fuser)

    def select(self,case,frame):
        self.case=case;self.frame=frame;self.calls=0
        self.fuser.dec_control_query_strength=0. if case in ['no_query','no_query_output'] else self.q
        self.fuser.dec_control_fused_res_strength=0. if case in ['no_output','no_query_output'] else self.o

    def scores(self,fuser,keys,base,common,unique,control_factor=1.):
        import torch
        self.calls+=1
        logits,prob,gate,scores,sensor,scale=self.original(keys,base,common,unique,control_factor)
        assert gate.shape==(fuser.patch_grid_x*fuser.patch_grid_y,)
        assert gate.numel()==1440 and len(keys)==3
        if not self.case.startswith('gate_'):return logits,prob,gate,scores,sensor,scale
        old=gate
        if self.case=='gate_mean':gate=old.mean().expand_as(old)
        else:
            seed=int(hashlib.sha256((self.case+':'+self.frame).encode()).hexdigest()[:15],16)
            generator=torch.Generator(device=gate.device);generator.manual_seed(seed)
            gate=old[torch.randperm(len(old),device=gate.device,generator=generator)]
        if self.case not in self.audit:
            assert torch.allclose(old.mean(),gate.mean(),atol=1e-6)
            if self.case!='gate_mean':assert torch.equal(old.sort().values,gate.sort().values)
            self.audit[self.case]=dict(frame=self.frame,patches=len(old),mean_preserved=True,
                distribution_preserved=self.case!='gate_mean',changed_fraction=float((old!=gate).float().mean()))
        # This returned gate controls token residuals, sensor scales AND context.
        prob=(gate-fuser.dec_control_gate_min)/(fuser.dec_control_gate_max-fuser.dec_control_gate_min)
        scale=(1.+fuser.dec_control_strength*float(control_factor)*gate[:,None]*(len(keys)*sensor-1.)).clamp(
            min=fuser.dec_control_scale_min,max=fuser.dec_control_scale_max)
        return logits,prob,gate,scores,sensor,scale

def input_without_gt(raw):
    import torch
    batch=dict(raw)
    batch['label']=[[]]
    # Legacy head unconditionally accesses gt_boxes, even in eval; give an empty
    # placeholder. This changes only its unused recall diagnostics, not boxes.
    batch['gt_boxes']=torch.zeros((1,1,8),dtype=raw['gt_boxes'].dtype)
    return batch

def encode(pipe,raw):
    m=pipe.network
    return m.rdr(m.ldr(m.cam(input_without_gt(raw))))

def predict(pipe,base,control,case,frame):
    import torch
    m=pipe.network;control.select(case,frame)
    batch=dict(base)
    for key in m.fuser.key_feats:batch[key]=base[key].clone()
    batch['avail_feats']=pipe.infer_mode_to_avail_feats('rlc')
    assert torch.count_nonzero(batch['gt_boxes'])==0 and not batch['label'][0]
    output=m.head(m.fuser(batch));assert control.calls==1
    pred=output['pred_dicts'][0]
    assert all(torch.isfinite(pred[k]).all() for k in ['pred_boxes','pred_scores'])
    if case in ['no_query','no_query_output']:assert torch.count_nonzero(output['_dec_control_query_delta'])==0
    if case in ['no_output','no_query_output']:assert torch.count_nonzero(output['_dec_control_fused_delta'])==0
    return output

def tensor_predictions(output):
    return {k:v.detach().clone() for k,v in output['pred_dicts'][0].items()}

def assert_predictions(a,b):
    import torch
    checks={}
    for k in ['pred_boxes','pred_scores','pred_labels']:
        assert a[k].shape==b[k].shape,(k,a[k].shape,b[k].shape)
        delta=float((a[k]-b[k]).abs().max()) if a[k].numel() else 0.
        assert torch.allclose(a[k],b[k],atol=1e-5,rtol=1e-5),(k,delta)
        checks[k]=delta
    return checks

def frame_record(pipe,raw,index,control,check=False):
    import torch
    raw['avail_feats']=pipe.infer_mode_to_avail_feats('rlc')
    meta=raw['meta'][0]
    identity=str(meta['seq'])+':'+json.dumps(meta['idx'],sort_keys=True)
    if check:
        control.select('baseline',identity)
        captured={}
        def capture(module,args):
            for key in module.key_feats:captured[key]=args[0][key].detach().clone()
        handle=pipe.network.fuser.register_forward_pre_hook(capture)
        native=tensor_predictions(pipe.network(copy.deepcopy(raw)))
        handle.remove()
        # Check the refactored fusion/head on EXACTLY the native encoder outputs.
        # Separate CUDA voxelization passes may have order-dependent roundoff.
        base=dict(captured,batch_size=1,label=[[]],meta=raw['meta'],
                  gt_boxes=torch.zeros((1,1,8),dtype=raw['gt_boxes'].dtype))
        repeated=tensor_predictions(pipe.network(copy.deepcopy(raw)))
        repeat_check={k:dict(same_shape=tuple(native[k].shape)==tuple(repeated[k].shape),
            max_abs_difference=float((native[k]-repeated[k]).abs().max())
            if native[k].shape==repeated[k].shape and native[k].numel() else None) for k in native}
    else:base=encode(pipe,raw)
    record=dict(index=index,seq=str(meta['seq']),sensor_indices=meta['idx'],pred={})
    audit={'native_repeat_diagnostics':repeat_check} if check else {}
    for case in CASES:
        output=predict(pipe,base,control,case,identity)
        if check:
            audit[case]=dict(query_delta_max=float(output['_dec_control_query_delta'].abs().max()),
                            output_delta_max=float(output['_dec_control_fused_delta'].abs().max()))
            if case=='baseline':
                baseline=tensor_predictions(output)
                audit['native_equivalence_same_features']=assert_predictions(native,baseline)
        # Restore labels ONLY after inference, for the unchanged KITTI exporter.
        export=dict(output);export['label']=raw['label'];export['meta']=raw['meta']
        gt,pred,desc=legacy.kitti_lines(pipe,export)
        record.update(gt=gt,description=desc,weather=desc.splitlines()[-1]);record['pred'][case]=pred
        del output,export
    if check:
        restored=predict(pipe,base,control,'baseline',identity)
        audit['restored_equivalence']=assert_predictions(baseline,restored['pred_dicts'][0])
        # Include an explicit empty-prediction parser check.
        from utils.kitti_eval.kitti_common import get_label_anno
        import numpy as np
        for lines in [record['gt'],record['pred']['baseline'],[]]:
            parser_path=HERE/'smoke/parser_check.txt'
            parser_path.write_text('\n'.join(lines)+('\n' if lines else ''))
            old,new=get_label_anno(parser_path),legacy.anno(lines)
            assert all(np.array_equal(old[k],new[k]) for k in old)
    # Historical sensor-availability archive has identical labels and ordering.
    assert record['gt']==(legacy.REFERENCE/'gt'/f'{index:06d}.txt').read_text().splitlines(),('GT/index mismatch',index)
    assert record['description'].strip()==(legacy.REFERENCE/'desc'/f'{index:06d}.txt').read_text().strip(),('description mismatch',index)
    return record,audit

def flush(out,records):
    if not records:return
    target=out/'chunks'/f"frames_{records[0]['index']:05d}_{records[-1]['index']:05d}.jsonl.gz"
    assert not target.exists()
    tmp=target.with_suffix('.tmp')
    with gzip.open(tmp,'wt',compresslevel=3) as f:
        for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    tmp.replace(target);records.clear()

def load_records(out):
    result=[]
    for p in sorted((out/'chunks').glob('frames_*.jsonl.gz')):
        with gzip.open(p,'rt') as f:result.extend(json.loads(line) for line in f)
    result.sort(key=lambda r:r['index'])
    assert len({r['index'] for r in result})==len(result)
    return result

def evaluate_one(gt,dt,indices,smoke=False):
    from utils.kitti_eval.eval import get_official_eval_result
    use=indices*((50+len(indices)-1)//len(indices)) if smoke else indices
    metrics,text=get_official_eval_result([gt[i] for i in use],[dt[i] for i in use],0,is_return_with_dict=True)
    result=dict(frames=len(indices),iou=[float(x) for x in metrics['iou']],
                AP3D=[float(x) for x in metrics['3d']],BEV=[float(x) for x in metrics['bev']])
    if smoke:result.update(synthetic_smoke_only=True,repeated_evaluation_frames=len(use))
    return result,text

def evaluate(out,smoke=False):
    records=load_records(out)
    assert len(records)==(8 if smoke else 10065)
    if not smoke:assert [r['index'] for r in records]==list(range(10065))
    gt=[legacy.anno(r['gt']) for r in records]
    groups={'all':list(range(len(records)))}
    if not smoke:
        groups.update({w:[i for i,r in enumerate(records) if r['weather']==w] for w in legacy.WEATHERS})
        assert sum(len(groups[w]) for w in legacy.WEATHERS)==10065
    results=read(out/'results_partial.json') if (out/'results_partial.json').exists() else {}
    for case in (['baseline'] if smoke else CASES):
        dt=[legacy.anno([s for s in r['pred'][case] if s.split()[0]!='dummy' and float(s.split()[-1])>.3]) for r in records]
        results.setdefault(case,{})
        # Baseline ALL is evaluated before any intervention; stop on mismatch.
        for weather,indices in groups.items():
            if weather not in results[case]:
                status(out,'evaluating',case=case,condition=weather,frames=len(indices),confidence=.3,
                       completed_groups=sum(len(v) for v in results.values()),total_groups=len(groups)*(1 if smoke else 8))
                value,text=evaluate_one(gt,dt,indices,smoke)
                results[case][weather]=value
                with (out/'metrics.log').open('a') as f:f.write(f'\n{case} {weather} conf>0.3\n{text}\n')
                write(out/'results_partial.json',results)
                print('RESULT',case,weather,json.dumps(value),flush=True)
            if not smoke and case=='baseline' and weather=='all':
                old=read(HISTORY)['sed'];d=results[case]['all'];difference={}
                for metric,name in [('3D','AP3D'),('BEV','BEV')]:
                    for iou,value in zip(d['iou'],d[name]):difference[f'{metric}@{iou:g}']=value-old[metric][f'{iou:g}']
                passed=max(abs(x) for x in difference.values())<=.05
                write(out/'baseline_verification.json',dict(passed=passed,max_tolerance_pp=.05,differences=difference,historical_source=str(HISTORY)))
                assert passed, 'Baseline AP differs from historical results; intervention scoring stopped'
    write(out/'results.json',results)
    if not smoke:make_tables(out,results)
    return results

def make_tables(out,results):
    import numpy as np
    rows=[]
    for case in CASES:
        r={'case':case};d=results[case]['all'];base=results['baseline']['all']
        for metric in ['AP3D','BEV']:
            for iou,value in zip(d['iou'],d[metric]):
                name=f'{metric}@{iou:g}';r[name]=value
                r['delta_'+name]=value-base[metric][base['iou'].index(iou)]
        rows.append(r)
    with (out/'comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    keys=['AP3D@0.3','AP3D@0.5','AP3D@0.7','BEV@0.3','BEV@0.5','BEV@0.7']
    sh=[r for r in rows if 'shuffle' in r['case']]
    write(out/'shuffle_summary.json',{k:dict(mean=float(np.mean([r[k] for r in sh])),
        min=min(r[k] for r in sh),max=max(r[k] for r in sh),mean_delta=float(np.mean([r['delta_'+k] for r in sh]))) for k in keys})
    lines=['# K-Radar v1 fixed-weight interventions','','Full 10,065-frame test set; Sedan; conf>0.3; original v1 11-point evaluator. Same model_0 for every row. Inference interventions, not retrained ablations.','',
        '| Setting | '+' | '.join(keys)+' |','|---|'+'---:|'*len(keys)]
    for r in rows:lines.append('| '+NAMES[r['case']]+' | '+' | '.join(f'{r[k]:.4f}' for k in keys)+' |')
    lines+=['','## Differences relative to baseline','','| Setting | '+' | '.join(keys)+' |','|---|'+'---:|'*len(keys)]
    for r in rows:lines.append('| '+NAMES[r['case']]+' | '+' | '.join(f'{r["delta_"+k]:+.4f}' for k in keys)+' |')
    lines+=['','Gate changes preserve the frame mean or value distribution but alter spatial correspondence. They consistently affect token residuals, sensor scaling, and gated context. Removing query/output increments does not change token modulation. Shuffle seeds are intervention replicates, not training replicates. All results, including negative or negligible changes, are retained.','',
        'Complete seven-weather metrics: results.json. GT defines scoring only; real GT is held outside network inference. An empty gt_boxes placeholder satisfies the legacy detector API.']
    (out/'results.md').write_text('\n'.join(lines)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true');p.add_argument('--evaluate-only',action='store_true');args=p.parse_args()
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='2'
    os.chdir(ROOT);out=HERE/'smoke' if args.smoke else HERE
    out.mkdir(exist_ok=True);(out/'chunks').mkdir(exist_ok=True)
    lock=(HERE/'gpu2.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (out/'results.json').exists():raise RuntimeError('Results already complete; refusing overwrite')
    assert sha(legacy.CKPT)==EXPECTED_SHA
    identity=dict(checkpoint_sha256=EXPECTED_SHA,config_sha256=sha(legacy.CONFIG),source_sha256=source_hashes(),smoke=args.smoke)
    if (out/'manifest.json').exists():
        old=read(out/'manifest.json')
        for key in identity:assert old[key]==identity[key],('Resume identity mismatch',key)
    elif args.evaluate_only:raise RuntimeError('Missing inference manifest')
    if not args.smoke:
        verified=read(HERE/'smoke/audit.json');assert verified['passed']
        assert verified['source_sha256']==identity['source_sha256']
    start=time.monotonic();pending=[]
    try:
        if not args.evaluate_only:
            status(out,'initializing',cases=CASES)
            pipe=legacy.prepare(out)
            import torch
            assert not pipe.is_validation_updated and bool(pipe.cfg.cfg_eval_ver2)
            assert not pipe.network.training
            control=Control(pipe.network.fuser)
            write(out/'manifest.json',dict(**identity,created_at=legacy.now(),checkpoint=str(legacy.CKPT),config=str(legacy.CONFIG),
                cases=CASES,dataset_size=10065,gpu=2,memory_fraction=.30,precision='FP32, eval, no autocast',
                confidence=.3,metric='Original v1 11-point AP; unchanged IoU/z-center/label conversion',
                historical_result=str(HISTORY),historical_sha256=sha(HISTORY),
                reuse='Only current-frame camera/LiDAR/radar encoded features; fuser/head states independent.',
                gt_handling='Real labels held outside inference; zero gt_boxes placeholder for legacy head API. Labels restored after prediction solely for evaluation export.',
                gate_intervention='Mean/permutation within current frame; recompute sensor scales and propagate changed gate to residuals and context.',
                failure_policy='Do not replace failed frames with empty predictions. Stop on baseline metric mismatch >0.05 pp.',
                frame_selection='All 10065 fixed test frames. Smoke indices evenly spaced, not selected by model performance.'))
            indices=[0,1437,2875,4313,5750,7188,8626,10064] if args.smoke else list(range(10065))
            existing=load_records(out);done={r['index'] for r in existing};del existing
            assert done.issubset(set(indices));remaining=[i for i in indices if i not in done]
            from torch.utils.data import Subset
            loader=pipe.build_dataloader(Subset(pipe.dataset_test,remaining),batch_size=1,shuffle=False,collate_fn=pipe.dataset_test.collate_fn)
            audits=[];inference_start=time.monotonic();initial_done=len(done)
            with torch.no_grad():
                for index,raw in zip(remaining,loader):
                    record,audit=frame_record(pipe,raw,index,control,check=args.smoke)
                    pending.append(record);done.add(index)
                    if args.smoke:audits.append(dict(index=index,checks=audit))
                    if len(pending)>=100:flush(out,pending)
                    if len(done)%25==0 or args.smoke or len(done)==len(indices):
                        elapsed=time.monotonic()-inference_start
                        status(out,'inference',completed=len(done),total=len(indices),cases_per_frame=8,
                            frames_per_second=(len(done)-initial_done)/max(elapsed,.001),elapsed_seconds=elapsed,
                            peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30)
                    del record,raw
            flush(out,pending)
            write(out/'gate_audit.json',control.audit)
            if args.smoke:
                write(out/'audit.json',dict(passed=True,frames=indices,checks=audits,source_sha256=identity['source_sha256'],
                    gate_checks=control.audit,real_gt_removed_from_inference=True,parser_verified=True,
                    peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30))
            # Release native model before CUDA/Numba evaluation.
            control.fuser._dec_control_scores=control.original
            del control,pipe,loader;gc.collect();torch.cuda.empty_cache()
        evaluate(out,smoke=args.smoke)
        assert source_hashes()==identity['source_sha256']
        assert sha(legacy.CKPT)==EXPECTED_SHA
        status(out,'complete',completed_frames=8 if args.smoke else 10065,cases=8,
               synthetic_metric_smoke_only=args.smoke,seconds=time.monotonic()-start,
               output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    except BaseException:
        flush(out,pending)
        status(out,'failed',traceback=traceback.format_exc());raise

if __name__=='__main__':
    try:main()
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
    # Native extension teardown is known to fail after completed exports. All
    # context-managed outputs close before this success-only explicit exit.
    sys.stdout.flush();sys.stderr.flush();os._exit(0)
