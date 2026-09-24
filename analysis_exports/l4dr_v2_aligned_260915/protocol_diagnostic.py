"""Hold predictions fixed; separate AP sampling from vertical IoU convention."""
import argparse
import datetime
import json
import os
import sys
from common import HERE, ROOT, STRONG, N, save, sha

p=argparse.ArgumentParser()
p.add_argument('--model',choices=['l4dr','strong'],required=True)
a=p.parse_args()
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
import numpy as np
from utils.kitti_eval import kitti_common as kitti
from utils.kitti_eval.eval_revised import eval_class, get_mAP_v2
from utils.kitti_eval.eval import get_official_eval_result

reference=json.loads((HERE/(a.model+'_evaluation.json')).read_text())
assert reference['status']=='complete'
outfile=HERE/(a.model+'_protocol_diagnostic.json')
assert not outfile.exists()
source=STRONG/'all/preds' if a.model=='strong' else HERE/'l4dr_full/preds'
result=dict(status='loading',model=a.model,num_samples=N,scope='Total only; same GT, predictions, confidence and NMS',
    started_at=datetime.datetime.now().astimezone().isoformat(),settings=[],
    evaluator_sha256=sha(ROOT/'utils/kitti_eval/eval_revised.py'))
save(outfile,result)
gt=kitti.get_label_annos(str(STRONG/'all/gts'),list(range(N)))
dt=kitti.get_label_annos(str(source),list(range(N)))
ious=[.7,.5,.3]
overlaps=np.array([np.full((3,2),v) for v in ious])
bev_precision=None
for center in [.5,1.0]:
    precision={}
    for name,metric in [('bev',1),('3d',2)]:
        if name=='bev' and bev_precision is not None:
            precision[name]=bev_precision
            continue
        raw=eval_class(gt,dt,[0,1],[0],metric,overlaps,z_axis=1,z_center=center)
        precision[name]=raw['precision'][:,0,:,:]
        if name=='bev':bev_precision=precision[name]
    for samples in [41,11]:
        settings=dict(z_center=center,ap_samples=samples,classes=[])
        values={}
        for name,pr in precision.items():
            # Sum in evaluator order, preserving its floating point convention.
            selected=range(41) if samples==41 else range(0,41,4)
            total=0
            for i in selected:total=total+pr[...,i]
            values[name]=total/samples*100
        for cls,label in enumerate(['sed','bus']):
            row=dict(cls=label,iou=ious,bev=values['bev'][cls].tolist(),**{'3d':values['3d'][cls].tolist()})
            settings['classes'].append(row)
            if center==.5 and samples==41:
                ref=next(x for x in reference['metrics']['all']['classes'] if x['cls']==label)
                for name in ['bev','3d']:assert np.allclose(row[name],ref[name],rtol=0,atol=1e-9),(row,ref)
        result['settings'].append(settings)
        print(json.dumps(settings),flush=True)
    result['status']='scoring'
    save(outfile,result)
# Cross-check old corner against the unmodified legacy public API.
legacy=next(x for x in result['settings'] if x['z_center']==1 and x['ap_samples']==11)
for cls in [0,1]:
    old,_=get_official_eval_result(gt,dt,cls,difficultys=[0],is_return_with_dict=True)
    for name in ['bev','3d']:
        assert np.allclose(old[name],legacy['classes'][cls][name],rtol=0,atol=1e-9)
result.update(status='complete',revised_api_verified=True,legacy_api_verified=True,
    finished_at=datetime.datetime.now().astimezone().isoformat())
save(outfile,result)
print('PROTOCOL DIAGNOSTIC COMPLETE',a.model,flush=True)
