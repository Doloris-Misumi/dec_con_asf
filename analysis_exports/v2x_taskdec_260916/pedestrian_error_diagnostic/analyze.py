"""CPU native-box diagnostics. These metrics are not official KITTI AP."""
import csv
import json
import math
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
import torch

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'vod_taskdec_native/L4DR_taskdec'))
from pcdet.ops.iou3d_nms.iou3d_nms_utils import boxes_bev_iou_cpu
torch.set_num_threads(2)


def ious(a,b):
    a=np.ascontiguousarray(a,dtype=np.float32).reshape(-1,7)
    b=np.ascontiguousarray(b,dtype=np.float32).reshape(-1,7)
    if not len(a) or not len(b):
        z=np.zeros((len(a),len(b)),np.float32)
        return z,z
    bev=boxes_bev_iou_cpu(a,b)
    area=a[:,3]*a[:,4];area_b=b[:,3]*b[:,4]
    overlap=bev*(area[:,None]+area_b[None,:])/(1+bev)
    top=np.minimum((a[:,2]+a[:,5]/2)[:,None],(b[:,2]+b[:,5]/2)[None,:])
    bottom=np.maximum((a[:,2]-a[:,5]/2)[:,None],(b[:,2]-b[:,5]/2)[None,:])
    inter=overlap*np.maximum(0,top-bottom)
    iou3d=inter/np.maximum(1e-8,(area*a[:,5])[:,None]+(area_b*b[:,5])[None,:]-inter)
    return bev,iou3d


def assign(cost,valid):
    if not cost.size:
        return np.empty(0,int),np.empty(0,int)
    r,c=linear_sum_assignment(np.where(valid,cost,1e6))
    good=valid[r,c]
    return r[good],c[good]


def summary(vals):
    vals=np.asarray(vals,float)
    if not len(vals):return None
    return dict(n=len(vals),mean=float(vals.mean()),median=float(np.median(vals)),p90=float(np.quantile(vals,.9)))


def groups(attr):
    d=attr['distance_m'];n=attr['lidar_points']
    return ['all','range_'+('0_20' if d<20 else '20_40' if d<40 else '40_plus'),
            'points_'+('0_5' if n<=5 else '6_20' if n<=20 else '21_100' if n<=100 else '101_plus'),
            'crowded' if attr['crowded'] else 'isolated']


def main():
    # Analytic geometry and one-to-one sanity checks.
    a=np.array([[0,0,0,4,2,2,0]],np.float32)
    b=a.copy();b[0,0]=1
    assert abs(float(ious(a,a)[1][0,0])-1)<1e-5
    assert abs(float(ious(a,b)[1][0,0])-.6)<1e-5
    b=a.copy();b[0,2]=1
    assert abs(float(ious(a,b)[1][0,0])-1/3)<1e-5
    r,c=assign(np.array([[.1],[.2]]),np.ones((2,1),bool))
    assert len(r)==len(c)==1 and r[0]==0
    truth=json.loads((OUT/'ground_truth.json').read_text())
    protocol=json.loads((OUT/'protocol.json').read_text())
    ids=protocol['frame_ids']
    pred={n:dict(np.load(OUT/('predictions_'+n+'.npz'))) for n in ['taskdec','concat']}
    records={};denom={};cache={n:{} for n in pred}
    for frame in ids:
        gt=np.asarray(truth[frame]['boxes'],np.float32).reshape(-1,7)
        attributes=truth[frame]['attributes']
        eligible=np.array([a['moderate'] for a in attributes],bool)
        for i,attr in enumerate(attributes):
            if not attr['moderate']:continue
            key=frame+':'+str(i)
            records[key]=dict(frame=frame,index=i,box=gt[i],attribute=attr)
            for group in groups(attr):denom[group]=denom.get(group,0)+1
        for name in pred:
            p=pred[name][frame]
            bev,box_iou=ious(gt,p[:,:7])
            xy=np.linalg.norm(gt[:,None,:2]-p[None,:,:2],axis=-1)
            cache[name][frame]=(gt,p,eligible,bev,box_iou,xy)
    # Fixed score gates and near-matched FP/frame: maximum-cardinality IoU
    # matching, with unmatched detections overlapping ignored GT excluded.
    thresholds=[i/100 for i in range(1,100)]
    performance={n:{} for n in pred};fp_targets={n:{} for n in pred}
    subgroup={n:{} for n in pred}
    for name in pred:
        for threshold in thresholds:
            total={str(i):dict(tp=0,fp=0,ignored_predictions=0) for i in [.25,.5]}
            for frame in ids:
                gt,p,eligible,bev,io,xy=cache[name][frame]
                gidx=np.flatnonzero(eligible);pidx=np.flatnonzero(p[:,7]>=threshold)
                for bound in [.25,.5]:
                    cur=io[np.ix_(gidx,pidx)]
                    rr,cc=assign(1-cur,cur>=bound)
                    hit_gt=gidx[rr];hit_pred=pidx[cc]
                    unmatched=np.setdiff1d(pidx,hit_pred,assume_unique=True)
                    ignored=0
                    if (~eligible).any() and len(unmatched):
                        ignored=int((io[np.ix_(np.flatnonzero(~eligible),unmatched)].max(0)>=bound).sum())
                    value=total[str(bound)]
                    value['tp']+=len(rr);value['fp']+=len(unmatched)-ignored
                    value['ignored_predictions']+=ignored
                    if abs(threshold-.1)<1e-8:
                        for idx in hit_gt:
                            for group in groups(truth[frame]['attributes'][idx]):
                                counts=subgroup[name].setdefault(group,{'hits_025':0,'hits_05':0})
                                counts['hits_025' if bound==.25 else 'hits_05']+=1
            for counts in total.values():
                counts.update(gt=len(records),recall=counts['tp']/len(records),
                    fp_per_frame=counts['fp']/len(ids),precision=counts['tp']/max(1,counts['tp']+counts['fp']))
            performance[name][f'{threshold:.2f}']=total
        for bound in [.25,.5]:
            fp_targets[name][str(bound)]={}
            for budget in [.25,.5,1.]:
                options=[(thr,row[str(bound)]) for thr,row in performance[name].items() if row[str(bound)]['fp_per_frame']<=budget]
                best=max(options,key=lambda x:(x[1]['recall'],-x[1]['fp_per_frame'])) if options else None
                fp_targets[name][str(bound)][str(budget)]=None if best is None else dict(score_threshold=float(best[0]),**best[1])
    for name in pred:
        for group,n in denom.items():
            row=subgroup[name].setdefault(group,{'hits_025':0,'hits_05':0})
            row.update(gt=n,recall_025=row['hits_025']/n,recall_05=row['hits_05']/n)
    # Geometry pairing minimizes center distance within 1 m. Pairing includes
    # all pedestrian GT first, then reports only eligible Moderate GT.
    # Thus ignored/crowded GT cannot simply be claimed by several boxes.
    geometry={};paired={};oracles={};matching={}
    error_names=['xy_m','radial_abs_m','tangential_abs_m','z_abs_m',
                 'length_abs_m','width_abs_m','height_abs_m','yaw_deg',
                 'length_bias_m','width_bias_m','height_bias_m','iou3d','iou_bev','score']
    for threshold in [.05,.1,.3]:
        current={n:{} for n in pred}
        for name in pred:
            for frame in ids:
                gt,p,eligible,bev,io,xy=cache[name][frame]
                pidx=np.flatnonzero(p[:,7]>=threshold)
                dist=xy[:,pidx]
                rr,cc=assign(dist,dist<=1.)
                for gi,ci in zip(rr,cc):
                    if not eligible[gi]:continue
                    pi=pidx[ci];g=gt[gi];q=p[pi];delta=q[:2]-g[:2]
                    unit=g[:2]/max(float(np.linalg.norm(g[:2])),1e-9)
                    angle=abs(float((q[6]-g[6]+np.pi/2)%np.pi-np.pi/2))
                    key=frame+':'+str(gi)
                    current[name][key]=dict(xy_m=float(xy[gi,pi]),
                        radial_abs_m=float(abs(delta@unit)),tangential_abs_m=float(abs(delta@np.array([-unit[1],unit[0]]))),
                        z_abs_m=float(abs(q[2]-g[2])),length_abs_m=float(abs(q[3]-g[3])),
                        width_abs_m=float(abs(q[4]-g[4])),height_abs_m=float(abs(q[5]-g[5])),
                        yaw_deg=float(np.rad2deg(angle)),length_bias_m=float(q[3]-g[3]),
                        width_bias_m=float(q[4]-g[4]),height_bias_m=float(q[5]-g[5]),
                        iou3d=float(io[gi,pi]),iou_bev=float(bev[gi,pi]),score=float(q[7]),
                        prediction=q[:7].copy(),prediction_index=int(pi))
        common=sorted(set(current['taskdec'])&set(current['concat']))
        geometry[str(threshold)]={n:{k:summary([current[n][key][k] for key in common]) for k in error_names} for n in pred}
        matching[str(threshold)]=dict(gt=len(records),common_matches=len(common),
            matched={n:len(current[n]) for n in pred},
            taskdec_only=len(set(current['taskdec'])-set(current['concat'])),
            concat_only=len(set(current['concat'])-set(current['taskdec'])))
        if threshold==.1:
            paired=current;common_keys=common
    columns={
        'original':[], 'xy':[0,1], 'length_width':[3,4], 'yaw':[6],
        'z':[2], 'height':[5], 'z_height':[2,5],
        'xy_length_width':[0,1,3,4], 'xy_length_width_yaw':[0,1,3,4,6],
    }
    for name in pred:
        oracles[name]={}
        for mode,cols in columns.items():
            result=[]
            for key in common_keys:
                p=paired[name][key]['prediction'].copy();g=records[key]['box']
                p[cols]=g[cols]
                result.append(float(ious(g[None],p[None])[1][0,0]))
            orig=np.asarray([paired[name][key]['iou3d'] for key in common_keys])
            result=np.asarray(result)
            oracles[name][mode]=dict(n=len(result),mean_iou=float(result.mean()),
                strict_hits=int((result>=.5).sum()),strict_fraction=float((result>=.5).mean()),
                rescued=int(((orig<.5)&(result>=.5)).sum()),
                newly_failed=int(((orig>=.5)&(result<.5)).sum()))
    group_geometry={}
    for group in denom:
        keys=[key for key in common_keys if group in groups(records[key]['attribute'])]
        group_geometry[group]=dict(gt=denom[group],paired=len(keys),
            **{n:{k:summary([paired[n][key][k] for key in keys]) for k in error_names} for n in pred})
    csv_rows=[]
    for key in common_keys:
        attr=records[key]['attribute']
        row=dict(gt_key=key,**attr)
        for name in pred:
            row.update({name+'_'+k:paired[name][key][k] for k in error_names})
        row['xy_error_taskdec_minus_concat']=row['taskdec_xy_m']-row['concat_xy_m']
        csv_rows.append(row)
    with (OUT/'paired_errors.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(csv_rows[0]));w.writeheader();w.writerows(csv_rows)
    cases=[]
    for row in sorted(csv_rows,key=lambda r:r['xy_error_taskdec_minus_concat'],reverse=True)[:8]:
        key=row['gt_key']
        cases.append(dict(**row,ground_truth=records[key]['box'].tolist(),
            taskdec_box=paired['taskdec'][key]['prediction'].tolist(),
            concat_box=paired['concat'][key]['prediction'].tolist()))
    result=dict(status='complete',frames=len(ids),moderate_gt=len(records),
        checkpoints=protocol['runs'],
        metric_note='Native ego 3D boxes; Moderate GT inclusion, ROI detections. Diagnostic matching, not KITTI AP. No image-height filtering of predictions. Different checkpoint epochs.',
        performance=performance,fp_budget_comparisons=fp_targets,
        geometry_matching=matching,geometry_common_gt=geometry,
        subgroups_at_score_01=subgroup,subgroup_geometry_common_gt=group_geometry,
        oracle_common_gt_score_01=oracles,
        oracle_note='One-to-one center-distance associations held fixed, on GT matched by both models at score>=0.1; fractions are conditional IoU success, not achievable AP/recall gains.',
        examples_largest_xy_error_gap=cases,
        sanity_checks='identity/translation/height IoU and one-to-one matching passed')
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    concise={k:result[k] for k in ['status','frames','moderate_gt','checkpoints','geometry_matching','oracle_common_gt_score_01']}
    concise['geometry_01']=geometry['0.1']
    concise['performance_01']={n:performance[n]['0.10'] for n in pred}
    concise['fp_matched']=fp_targets
    print(json.dumps(concise,indent=2))


if __name__=='__main__':main()
