"""Score cached predictions against the single verified GT, without duplication."""
import argparse
import datetime
import json
import os
import sys
import time
from common import HERE, ROOT, STRONG, N, CLASSES, CONDITIONS, records, sha, save

parser=argparse.ArgumentParser()
parser.add_argument('--model',choices=['l4dr','strong'],required=True)
parser.add_argument('--legacy',action='store_true')
args=parser.parse_args()
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
from utils.kitti_eval import kitti_common as kitti
from utils.kitti_eval.eval_revised import get_official_eval_result_revised
from utils.kitti_eval.eval import get_official_eval_result

source=STRONG/'all/preds' if args.model=='strong' else HERE/'l4dr_full/preds'
assert sorted(p.name for p in source.glob('*.txt'))==[f'{i:06d}.txt' for i in range(N)]
if args.model=='l4dr':
    s=json.loads((HERE/'l4dr_full/status.json').read_text())
    assert s['status']=='predictions_complete' and s['num_samples']==N
    assert json.loads((HERE/'l4dr_full/evaluated_indices.json').read_text())==list(range(N))
rows=records()
result=dict(status='loading_annotations',model=args.model,num_samples=N,
    started_at=datetime.datetime.now().astimezone().isoformat(),failure_count=0,
    gt_source=str(STRONG/'all/gts'),prediction_source=str(source),
    manifest_sha256=sha(HERE/'manifest.jsonl'),
    evaluator_sha256=sha(ROOT/'utils/kitti_eval/eval_revised.py'),
    protocol=json.loads((HERE/'preflight.json').read_text())['protocol'],metrics={})
outfile=HERE/(args.model+'_evaluation'+('_legacy' if args.legacy else '')+'.json')
assert not outfile.exists(),'Do not overwrite a completed evaluation'
save(outfile,result)
print('Loading annotations',args.model,flush=True)
gt=kitti.get_label_annos(str(STRONG/'all/gts'),list(range(N)))
dt=kitti.get_label_annos(str(source),list(range(N)))
print('Loaded',N,'GT and predictions',flush=True)
scorer=get_official_eval_result if args.legacy else get_official_eval_result_revised
if args.legacy:
    result['protocol']=dict(result['protocol'],z_center=1.0,ap_samples=11)
    result['evaluator_sha256']=sha(ROOT/'utils/kitti_eval/eval.py')
logfile=outfile.with_suffix('.txt')
try:
    with logfile.open('w') as log:
        for group in CONDITIONS:
            ids=[r['index'] for r in rows if group in r['groups']]
            if not ids:continue
            gg=[gt[i] for i in ids];dd=[dt[i] for i in ids]
            result['metrics'][group]=dict(num_samples=len(ids),classes=[])
            for cls in range(2):
                metric,raw=scorer(gg,dd,cls,is_return_with_dict=True)
                value=dict(cls=metric['cls'],iou=list(map(float,metric['iou'])),
                    bev=list(map(float,metric['bev'])),**{'3d':list(map(float,metric['3d']))})
                result['metrics'][group]['classes'].append(value)
                log.write(group+'\n'+raw+'\n');log.flush()
                print(group,len(ids),json.dumps(value),flush=True)
            result['status']='scoring'
            save(outfile,result)
    result.update(status='complete',finished_at=datetime.datetime.now().astimezone().isoformat())
    save(outfile,result)
except BaseException as error:
    result.update(status='failed',error=repr(error),failure_count=1)
    save(outfile,result)
    raise

if args.model=='l4dr' and not args.legacy:
    import subprocess
    try:
        subprocess.run([sys.executable,'-u',str(HERE/'protocol_diagnostic.py'),'--model','l4dr'],check=True)
        subprocess.run([sys.executable,'-u',str(HERE/'make_report.py')],check=True)
    except BaseException as error:
        save(HERE/'completion.json',dict(status='failed_after_evaluation',error=repr(error)))
        raise
