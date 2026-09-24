"""Generate paper-facing artifacts only from completed measurements."""
import csv
import io
import json
from .experiment import FORMAL,atomic_json,now


def main():
    rows=[];states={}
    for variant in ['concat','patch','taskdec']:
        run=FORMAL/variant
        status=json.loads((run/'status.json').read_text()) if (run/'status.json').exists() else {'status':'pending'}
        if (run/'process_costs.jsonl').exists():
            status['gpu_hours_process']=sum(json.loads(line)['wall_seconds'] for line in (run/'process_costs.jsonl').read_text().splitlines())/3600
        states[variant]=status
        for tag in ['best','last']:
            source=run/('final_'+tag+'.json')
            if not source.exists():continue
            report=json.loads(source.read_text())
            for split,result in report['results'].items():
                for key,value in result['metrics'].items():
                    rows.append(dict(variant=variant,checkpoint=tag,epoch=report['epoch'],split=split,metric=key,value=value))
    atomic_json(FORMAL/'summary_status.json',dict(updated_at=now(),runs=states,completed_metric_rows=len(rows)))
    text=io.StringIO();writer=csv.DictWriter(text,fieldnames=['variant','checkpoint','epoch','split','metric','value'])
    writer.writeheader();writer.writerows(rows);(FORMAL/'complete_metrics.csv').write_text(text.getvalue())
    lines=['# V2X-Radar-V controlled C+L+R results','',
        'Local deduplicated split protocol; AP_R40 strict IoU 0.7/0.5/0.5. Vehicle = Car/Truck/Bus.',
        'Best checkpoint selected on deduplicated validation strict moderate mean 3D AP. Test never selects a checkpoint.',
        'Single seed; no statistical significance claim. Pending runs have no final AP.', '',
        '| Variant | State | Epochs | Best val epoch | Train GPU h | Measured process GPU h |',
        '|---|---|---:|---:|---:|---:|']
    for variant,state in states.items():
        lines.append('| %s | %s | %s | %s | %.3f | %s |'%(variant,state['status'],state.get('completed_epochs',0),
            state.get('best_epoch','—'),state.get('train_seconds',0)/3600,
            '%.3f'%state['gpu_hours_process'] if 'gpu_hours_process' in state else 'pending'))
    lines+=['','| Variant | Checkpoint | Split | Vehicle | Pedestrian | Cyclist | Mean |',
            '|---|---|---|---:|---:|---:|---:|']
    latex=[]
    for variant in states:
        for tag in ['best','last']:
            for split in ['val_deduplicated','test_deduplicated','val','test']:
                values={r['metric']:r['value'] for r in rows if r['variant']==variant and r['checkpoint']==tag and r['split']==split}
                if not values:continue
                ap=[values['V2X/'+c+'_3D_moderate_strict'] for c in ['Vehicle','Pedestrian','Cyclist']]
                mean=values['V2X/Overall_3D_moderate']
                lines.append('| %s | %s | %s | %.2f | %.2f | %.2f | %.2f |'%(variant,tag,split,*ap,mean))
                if tag=='best' and split=='test_deduplicated':
                    latex.append('%s & %.2f & %.2f & %.2f & %.2f \\'%(variant,*ap,mean))
    lines+=['','All classes, difficulties, strict/loose 3D and BEV metrics: `complete_metrics.csv`.','',
        'GPU hours are elapsed time occupying one GPU process (including I/O), not utilization-integrated compute.',
        'Shared GPU services and parallel jobs may affect throughput. Setup, smoke and engineering checks are additional costs.']
    (FORMAL/'results.md').write_text('\n'.join(lines)+'\n')
    (FORMAL/'main_table_rows.tex').write_text('\n'.join(latex)+'\n')


if __name__=='__main__':main()
