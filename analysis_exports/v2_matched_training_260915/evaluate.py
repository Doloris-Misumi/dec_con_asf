import argparse
import datetime
import json
import os
import subprocess
import sys
from common import HERE, ROOT, REFERENCE, STRONG, CONDITIONS, records, sha, save

p=argparse.ArgumentParser();p.add_argument('--model',choices=['asf','l4dr'],required=True);a=p.parse_args()
os.chdir(ROOT);sys.path.insert(0,str(ROOT))
from utils.kitti_eval import kitti_common as kitti
from utils.kitti_eval.eval_revised import get_official_eval_result_revised

outdir=HERE/a.model
state=json.loads((outdir/'status.json').read_text())
assert state['status']=='predictions_complete' and state['evaluation_samples']==13727
assert state['global_step']==79123 and state['completed_epochs']==11 and state['failure_count']==0
assert sorted(x.name for x in (outdir/'preds').glob('*.txt'))==[f'{i:06d}.txt' for i in range(13727)]
rows=records('test')
result=dict(status='scoring',model=a.model,num_samples=13727,failure_count=0,training=state,metrics={},
    evaluator_sha256=sha(ROOT/'utils/kitti_eval/eval_revised.py'),
    protocol=dict(label_version='v2_0',roi=[0,-16,-2,72,16,7.6],confidence=.3,
        score_pre_filter=.1,nms_threshold=.01,z_center=.5,ap_samples=41))
save(outdir/'evaluation.json',result)
try:
    gt=kitti.get_label_annos(str(STRONG/'test_kitti/none/0.3/all/gts'),list(range(13727)))
    dt=kitti.get_label_annos(str(outdir/'preds'),list(range(13727)))
    with (outdir/'evaluation.txt').open('w') as raw:
        for group in CONDITIONS:
            indices=[r['index'] for r in rows if group in r['groups']]
            assert indices
            gg=[gt[i] for i in indices];dd=[dt[i] for i in indices]
            result['metrics'][group]=dict(num_samples=len(indices),classes=[])
            for cls in [0,1]:
                metric,text=get_official_eval_result_revised(gg,dd,cls,is_return_with_dict=True)
                value=dict(cls=metric['cls'],iou=list(map(float,metric['iou'])),bev=list(map(float,metric['bev'])),
                    **{'3d':list(map(float,metric['3d']))})
                result['metrics'][group]['classes'].append(value)
                raw.write(group+'\n'+text+'\n');raw.flush()
                print(group,json.dumps(value),flush=True)
            save(outdir/'evaluation.json',result)
    result.update(status='complete',finished_at=datetime.datetime.now().astimezone().isoformat())
    save(outdir/'evaluation.json',result)
    state.update(status='complete',finished_at=result['finished_at'])
    save(outdir/'status.json',state)
    subprocess.run([sys.executable,str(HERE/'report.py')],check=True)
except BaseException as error:
    state.update(status='failed_during_evaluation',failure_count=1,error=repr(error))
    save(outdir/'status.json',state);raise
