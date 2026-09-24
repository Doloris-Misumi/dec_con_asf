"""Audit completed controlled experiments without changing training or protocol.

Run with the experiment venv after controller completion. Incomplete runs produce
an explicitly incomplete receipt and exit code 2; they never get fabricated AP.
"""
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
FORMAL=BASE/'controlled_80ep'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    digest=hashlib.sha256()
    with open(path,'rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def main():
    report=dict(observed_at=datetime.now().astimezone().isoformat(),status='incomplete',checks=[],pending=[])
    def check(label,condition):
        report['checks'].append(dict(check=label,passed=bool(condition)))
        if not condition:raise AssertionError(label)
    try:
        cfg=read(FORMAL/'config.json')
        check('frozen C+L+R, three classes, 80 epochs, FP32, effective batch 8',
              cfg['modalities']==['camera','lidar','radar'] and len(cfg['class_names'])==3 and
              cfg['epochs']==80 and cfg['precision']=='fp32' and cfg['batch_size']==2 and cfg['accumulation']==4)
        states={}
        for name in ['concat','patch','taskdec']:
            path=FORMAL/name/'status.json'
            states[name]=read(path) if path.exists() else {'status':'pending'}
            if states[name]['status']!='complete':report['pending'].append(name+': '+states[name]['status'])
        controller=read(FORMAL/'controller_status.json')
        if controller['status']!='complete':report['pending'].append('controller: '+controller['status'])
        if report['pending']:
            return report
        # Heavy checkpoint reads are intentionally deferred until all jobs finish.
        import torch
        check('all frozen sources unchanged',all(sha(ROOT/path)==expected for path,expected in read(FORMAL/'source_manifest.json').items()))
        check('all frozen protocol/split/input manifests unchanged',all(sha(Path(path))==expected for path,expected in read(FORMAL/'input_manifest.json').items()))
        initialization=read(FORMAL/'initialization.json')
        check('shared initialization hashes match',len({v['shared_backbone_head_hash'] for v in initialization.values()})==1)
        integrity=read(BASE/'data_integrity.json')
        check('official split and modality counts',integrity['split_counts']['train']==8391 and integrity['split_counts']['val']==1498 and integrity['split_counts']['test']==1501 and all(n==11390 for n in integrity['modality_counts'].values()))
        check('metric and independent geometry engineering checks',read(BASE/'evaluator_check.json')['status']=='passed' and read(BASE/'evaluator_geometry_check.json')['status']=='passed' and read(BASE/'near_coincident_evaluator_check.json')['status']=='passed')
        split_ids={s:(Path(cfg['split_root'])/(s+'.txt')).read_text().split() for s in ['val','test']}
        split_ids.update({s:(FORMAL/(s+'.txt')).read_text().split() for s in ['val_deduplicated','test_deduplicated']})
        check('deduplicated split sizes and uniqueness',len(split_ids['val_deduplicated'])==1487 and len(split_ids['test_deduplicated'])==1486 and all(len(ids)==len(set(ids)) for ids in split_ids.values()))
        expected_rows={};costs={};summaries={}
        for name,state in states.items():
            run=FORMAL/name
            check(name+' final budget',state['completed_epochs']==80 and state['optimizer_updates']==83920 and state['config_sha256']==sha(FORMAL/'config.json'))
            check(name+' initial checkpoint provenance',sha(FORMAL/(name+'_initial.pt'))==initialization[name]['sha256']==state['initial_sha256'])
            epochs=[json.loads(line) for line in (run/'epochs.jsonl').read_text().splitlines()]
            check(name+' complete epoch coverage',len(epochs)==80 and [r['epoch'] for r in epochs]==list(range(1,81)))
            check(name+' matched samples and updates',all(r['samples']==8391 and r['optimizer_updates']==r['epoch']*1049 for r in epochs))
            check(name+' finite recorded loss',all(math.isfinite(r[k]) for r in epochs for k in ['loss','det_loss','aux_loss']))
            vals=[read(run/('val_epoch_%03d.json'%epoch)) for epoch in cfg['val_epochs']]
            check(name+' fixed validation schedule',all(r['epoch']==ep and r['frames']==1487 for ep,r in zip(cfg['val_epochs'],vals)))
            best=max(vals,key=lambda r:(r['selection_metric'],-r['epoch']))
            check(name+' validation-only best selection',best['epoch']==state['best_epoch'] and best['selection_metric']==state['best_metric'])
            summaries[name]={}
            for tag in ['best','last']:
                checkpoint=torch.load(run/(tag+'.pt'),map_location='cpu')
                target_epoch=best['epoch'] if tag=='best' else 80
                check(name+' '+tag+' checkpoint epoch',checkpoint['epoch']==target_epoch)
                check(name+' '+tag+' finite state',all(torch.isfinite(v).all().item() for v in checkpoint['model'].values()))
                if tag=='last':
                    check(name+' recoverable optimizer',bool(checkpoint['optimizer']['state']) and checkpoint['state']['completed_epochs']==80 and checkpoint['state']['optimizer_updates']==83920)
                del checkpoint
                final=read(run/('final_'+tag+'.json'))
                check(name+' '+tag+' evaluated checkpoint hash',final['checkpoint_sha256']==sha(run/(tag+'.pt')) and final['epoch']==target_epoch)
                check(name+' '+tag+' complete split results',set(final['results'])==set(split_ids))
                for split in ['val','test']:
                    predictions=torch.load(run/('predictions_'+tag+'_'+split+'.pt'),map_location='cpu')
                    check(name+' '+tag+' '+split+' prediction frame coverage',set(predictions)==set(split_ids[split]))
                    check(name+' '+tag+' '+split+' finite prediction arrays',all(p.ndim==2 and p.shape[1]==9 and bool(__import__('numpy').isfinite(p).all()) for p in predictions.values()))
                    del predictions
                for split,res in final['results'].items():
                    metrics=res['metrics']
                    check(name+' '+tag+' '+split+' full finite AP',res['frames']==len(split_ids[split]) and len(metrics)==42 and all(math.isfinite(v) and 0<=v<=100 for v in metrics.values()))
                    mean=sum(metrics['V2X/'+c+'_3D_moderate_strict'] for c in cfg['class_names'])/3
                    check(name+' '+tag+' '+split+' mean AP',abs(mean-res['selection_metric'])<1e-9 and abs(mean-metrics['V2X/Overall_3D_moderate'])<1e-9)
                    for metric,value in metrics.items():expected_rows[(name,tag,split,metric)]=(target_epoch,value)
                summaries[name][tag]=dict(epoch=target_epoch,test_deduplicated_strict_moderate_3d_ap=final['results']['test_deduplicated']['selection_metric'])
            launch=read(run/'launch.json')
            measured=(datetime.fromisoformat(state['finished_at'])-datetime.fromisoformat(launch['started_at'])).total_seconds()
            attempts=[json.loads(line) for line in (run/'process_costs.jsonl').read_text().splitlines()]
            last_attempt=attempts[-1] if attempts else {}
            adopted_complete=(last_attempt.get('exit_code') is None and
                last_attempt.get('accounting_method')=='adopted_process_exit_and_complete_status' and
                last_attempt.get('completion_status')=='complete' and state['status']=='complete')
            check(name+' process-exit accounting',bool(attempts) and
                  (last_attempt.get('exit_code')==0 or adopted_complete) and last_attempt['pid']==launch['pid'])
            # Polling every five minutes overestimates process duration. Preserve
            # raw upper bound and an interval instead of claiming false precision.
            earlier=attempts[:-1]
            lower=measured+sum(max(0.,a['wall_seconds']-301) for a in earlier)
            upper=sum(a['wall_seconds'] for a in attempts)
            costs[name]=dict(train_gpu_hours=state['train_seconds']/3600,validation_gpu_hours=state['validation_seconds']/3600,
                process_gpu_hours_interval=[lower/3600,max(lower,upper)/3600],attempts=len(attempts),
                definition='Wall time with a GPU process resident, including I/O/CPU evaluation. Last attempt lower bound ends at final status; raw exit observation is an upper bound. Not utilization-integrated compute.')
        rows=list(csv.DictReader((FORMAL/'complete_metrics.csv').open()))
        actual={(r['variant'],r['checkpoint'],r['split'],r['metric']):(int(r['epoch']),float(r['value'])) for r in rows}
        check('paper CSV complete, unique, exact source values',len(rows)==len(actual)==1008 and actual==expected_rows)
        check('paper LaTeX includes all three methods',all((name+' & ') in (FORMAL/'paper_main_table.tex').read_text() for name in states))
        report.update(status='automated_checks_passed_requires_final_review',summaries=summaries,compute=costs,
            limitation='This audit checks artifacts and budget consistency. Final human-facing review must also interpret the architecture provenance, data limitations and positive/negative findings. It does not mark the active goal complete.')
        return report
    except Exception as exc:
        report.update(status='audit_failed',error=repr(exc));return report
    finally:
        (FORMAL/'delivery_audit.json').write_text(json.dumps(report,indent=2,allow_nan=False))


if __name__=='__main__':
    result=main();print(json.dumps(result,indent=2));raise SystemExit(0 if result['status'].startswith('automated_checks_passed') else 2)
