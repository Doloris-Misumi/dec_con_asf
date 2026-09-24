"""CPU geometry diagnostics of frozen predictions; this is not a new AP protocol."""
from common import *
import argparse
import fcntl
import time
import traceback
import numpy as np
import torch
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
sys.path.insert(0,str(ROOT/'vod_taskdec_native/L4DR_taskdec'))
from pcdet.ops.iou3d_nms.iou3d_nms_utils import boxes_bev_iou_cpu
from v2x_taskdec.evaluate import Evaluator
from v2x_taskdec.geometry import read_calibration,camera_box_to_lidar,transform_points,corners_lidar,project_points
from v2x_taskdec.point_schema import load_points
from PIL import Image

OUT=HERE/'diagnostics'
PAIRS=[('objdec_lr','l4dr'),('objdec_clr','asf')]
CLASSES=['Vehicle','Pedestrian','Cyclist']
THRESHOLDS=[.7,.5,.5]

def ious(a,b):
    a=np.ascontiguousarray(a,dtype=np.float32).reshape(-1,7);b=np.ascontiguousarray(b,dtype=np.float32).reshape(-1,7)
    if not len(a) or not len(b):return np.zeros((len(a),len(b))),np.zeros((len(a),len(b)))
    bev=boxes_bev_iou_cpu(a,b)
    aa=a[:,3]*a[:,4];ab=b[:,3]*b[:,4]
    intersection=bev*(aa[:,None]+ab[None,:])/(1+bev)
    height=np.maximum(0,np.minimum((a[:,2]+a[:,5]/2)[:,None],(b[:,2]+b[:,5]/2)[None,:])-
        np.maximum((a[:,2]-a[:,5]/2)[:,None],(b[:,2]-b[:,5]/2)[None,:]))
    volume=intersection*height
    return bev,volume/np.maximum((aa*a[:,5])[:,None]+(ab*b[:,5])[None,:]-volume,1e-8)

def assign(iou,threshold):
    if not iou.size:return np.array([],int),np.array([],int)
    valid=iou>=threshold;r,c=linear_sum_assignment(np.where(valid,1-iou,1e6));keep=valid[r,c]
    return r[keep],c[keep]

def selfcheck():
    a=np.array([[0,0,0,4,2,2,0]],np.float32);b=a.copy();b[0,0]=1
    assert abs(ious(a,a)[1][0,0]-1)<1e-5 and abs(ious(a,b)[1][0,0]-.6)<1e-5
    b=a.copy();b[0,2]=1;assert abs(ious(a,b)[1][0,0]-1/3)<1e-5
    assert len(assign(np.array([[.9],[.8]]),.7)[0])==1
    pts=np.array([[0,0,0],[1.9,.9,.9],[3,0,0]],np.float32)
    assert inside_counts(pts,a).tolist()==[2]

def inside_counts(points,boxes):
    counts=np.zeros(len(boxes),int)
    if not len(points):return counts
    tree=cKDTree(points[:,:2])
    for i,box in enumerate(boxes):
        idx=tree.query_ball_point(box[:2],float(np.hypot(box[3],box[4])/2+1e-5))
        diff=points[idx,:3]-box[:3];c,s=np.cos(box[6]),np.sin(box[6])
        local=np.column_stack([diff[:,0]*c+diff[:,1]*s,-diff[:,0]*s+diff[:,1]*c,diff[:,2]])
        counts[i]=int((np.abs(local)<=box[3:6]/2+1e-6).all(1).sum())
    return counts

def filtered_predictions(pred,cal,roi,image_size):
    p=np.asarray(pred)
    keep=np.isfinite(p).all(1)&(p[:,3:6]>0).all(1)&(p[:,7]>=.1)&(p[:,8]>=1)&(p[:,8]<=3)
    keep&=((p[:,:3]>=roi[:3])&(p[:,:3]<roi[3:])).all(1);p=p[keep]
    if not len(p):return p
    keep=transform_points(p[:,:3],cal['lidar_to_camera'])[:,2]>.1;p=p[keep]
    if not len(p):return p
    corners=corners_lidar(p[:,:7]);uv,depth=project_points(corners.reshape(-1,3),cal)
    uv=uv.reshape(-1,8,2);valid=depth.reshape(-1,8)>.1
    low=np.where(valid[:,:,None],uv,np.inf).min(1);high=np.where(valid[:,:,None],uv,-np.inf).max(1)
    w,h=image_size;low=np.clip(low,[0,0],[w-1,h-1]);high=np.clip(high,[0,0],[w-1,h-1])
    return p[valid.any(1)&(high[:,1]-low[:,1]>=25)]

def groupnames(r):
    return ['all','range:'+r['range_bin'],'lidar:'+r['lidar_bin'],'radar:'+r['radar_bin']]

def mean_error(rows,model,key):
    values=[r[model+'_'+key] for r in rows if r[model+'_hit_3D']]
    return float(np.mean(values)) if values else None

def summarize(records):
    summaries=[];comparisons=[]
    groups=['all','range:0-30','range:30-60','range:60+',
        'lidar:0-5','lidar:6-20','lidar:21-100','lidar:101+',
        'radar:0','radar:1-5','radar:6-20','radar:21+']
    for cls in ['all']+CLASSES:
        for group in groups:
            selected=[r for r in records if (cls=='all' or r['class']==cls) and group in groupnames(r)]
            for model in RUNS:
                row=dict(model=model,cls=cls,group=group,gt=len(selected))
                for mode in ['3D','BEV']:
                    hit=sum(r[model+'_hit_'+mode] for r in selected)
                    row['tp_'+mode]=hit;row['recall_'+mode]=hit/len(selected) if selected else None
                for key in ['xy_m','z_m','size_l1_m','yaw_axis_deg']:row['tp_mean_'+key]=mean_error(selected,model,key)
                summaries.append(row)
            for a,b in PAIRS:
                common=[r for r in selected if r[a+'_hit_3D'] and r[b+'_hit_3D']]
                row=dict(method=a,baseline=b,cls=cls,group=group,gt=len(selected),common_tp_3D=len(common),
                    gained=sum(r[a+'_hit_3D'] and not r[b+'_hit_3D'] for r in selected),
                    lost=sum(r[b+'_hit_3D'] and not r[a+'_hit_3D'] for r in selected))
                for mode in ['3D','BEV']:
                    row['recall_delta_'+mode]=(sum(r[a+'_hit_'+mode]-r[b+'_hit_'+mode] for r in selected)/len(selected)) if selected else None
                for key in ['xy_m','z_m','size_l1_m','yaw_axis_deg']:
                    row['common_tp_'+a+'_'+key]=mean_error(common,a,key)
                    row['common_tp_'+b+'_'+key]=mean_error(common,b,key)
                comparisons.append(row)
    return summaries,comparisons

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
    OUT.mkdir(exist_ok=True);lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    torch.set_num_threads(2);selfcheck()
    cfg=read(RUNS['objdec_clr']/'config.json');evaluator=Evaluator(cfg)
    data=Path(cfg['data_root'])/'training';roi=np.asarray(cfg['point_cloud_range']);schemas=read(cfg['point_schema_manifest'])
    frames=ids()[:4] if args.smoke else ids()
    status(OUT,'loading_predictions',total=len(frames))
    predictions={};provenance={}
    for model,run in RUNS.items():
        file=run/'predictions_best_test.pt';predictions[model]=torch.load(file,map_location='cpu')
        assert not set(frames)-set(predictions[model])
        final=read(run/'final_best.json')
        provenance[model]=dict(run=str(run),epoch=final['epoch'],predictions_sha256=sha(file),checkpoint_sha256=final['checkpoint_sha256'])
    protocol=dict(models=provenance,split=str(SPLIT),split_sha256=sha(SPLIT),frames=len(frames),score=.1,
        matching='Class-wise maximum-cardinality one-to-one matching to Moderate eligible GT; strict IoU .7/.5/.5 in native ego geometry.',
        gt='Pinned evaluator ROI/Vehicle mapping. Height >25, occlusion <=1, truncation <=.3.',
        predictions='Post-NMS cached outputs; same ROI and camera projection filters; score >=.1; projected height >=25.',
        points='Raw released point cloud after frozen schema validation and calibration, within oriented 3D GT boxes before voxelization.',
        distance='Radial xy center distance, fixed 0-30 / 30-60 / >=60 m.',
        errors='Own TP and common TP errors accompanied by recall. Yaw axis error modulo pi; size L1 in metres.',
        limitation='GT-centric geometry diagnostics, NOT official AP, precision, FP rate or KITTI greedy matching. Missing detections remain in recall denominator. All predefined groups retained.',
        sources=sources())
    write(OUT/('smoke_protocol.json' if args.smoke else 'protocol.json'),protocol)
    records=[];start=time.monotonic()
    for pos,frame in enumerate(frames):
        cal=read_calibration(data/'calib'/(frame+'.txt'));ann=evaluator.ground_truth(frame)
        gt=np.array([camera_box_to_lidar(loc,dim[[1,2,0]],yaw,cal) for loc,dim,yaw in
            zip(ann['location'],ann['dimensions'],ann['rotation_y'])],np.float32).reshape(-1,7)
        eligible=(ann['bbox'][:,3]-ann['bbox'][:,1]>25)&(ann['occluded']<=1)&(ann['truncated']<=.3)
        indices=np.flatnonzero(eligible);gt=gt[eligible]
        cls=np.array([{'Car':1,'Pedestrian':2,'Cyclist':3}[name] for name in ann['name'][eligible]])
        counts={}
        for sensor,folder,transform in [('lidar','velodyne','raw_lidar_to_ego'),('radar','radar','radar_to_ego')]:
            pts=load_points(data/folder/(frame+'.bin'),sensor,schemas[frame][sensor])
            xyz=transform_points(pts[:,:3],cal[transform]);counts[sensor]=inside_counts(xyz,gt)
        current=[]
        for i,box in enumerate(gt):
            distance=float(np.linalg.norm(box[:2]));l=int(counts['lidar'][i]);r=int(counts['radar'][i])
            row=dict(frame=frame,gt_index=int(indices[i]),**{'class':CLASSES[cls[i]-1]},distance_m=distance,lidar_points=l,radar_points=r,
                range_bin='0-30' if distance<30 else '30-60' if distance<60 else '60+',
                lidar_bin='0-5' if l<=5 else '6-20' if l<=20 else '21-100' if l<=100 else '101+',
                radar_bin='0' if r==0 else '1-5' if r<=5 else '6-20' if r<=20 else '21+')
            for model in RUNS:
                for mode in ['3D','BEV']:row[model+'_hit_'+mode]=0;row[model+'_iou_'+mode]=None
                for key in ['xy_m','z_m','size_l1_m','yaw_axis_deg']:row[model+'_'+key]=None
            current.append(row)
        with Image.open(next((data/'image_2').glob(frame+'.*'))) as image:image_size=image.size
        for model in RUNS:
            pred=filtered_predictions(predictions[model][frame],cal,roi,image_size)
            if args.smoke:
                reference=evaluator.predictions(frame,predictions[model][frame])
                expected=int(((reference['score']>=.1)&(reference['bbox'][:,3]-reference['bbox'][:,1]>=25)).sum())
                assert len(pred)==expected,(frame,model,len(pred),expected)
            for c,threshold in enumerate(THRESHOLDS,1):
                gi=np.flatnonzero(cls==c);pi=np.flatnonzero(pred[:,8]==c)
                bev,iou=ious(gt[gi],pred[pi,:7])
                for mode,matrix in [('3D',iou),('BEV',bev)]:
                    rr,cc=assign(matrix,threshold)
                    for r,cidx in zip(rr,cc):
                        idx=gi[r];prediction=pred[pi[cidx],:7];row=current[idx]
                        row[model+'_hit_'+mode]=1;row[model+'_iou_'+mode]=float(matrix[r,cidx])
                        if mode=='3D':
                            delta=prediction-gt[idx]
                            row[model+'_xy_m']=float(np.linalg.norm(delta[:2]));row[model+'_z_m']=float(abs(delta[2]))
                            row[model+'_size_l1_m']=float(np.abs(delta[3:6]).sum())
                            row[model+'_yaw_axis_deg']=float(abs((delta[6]+np.pi/2)%np.pi-np.pi/2)*180/np.pi)
        records.extend(current)
        if (pos+1)%32==0 or pos+1==len(frames):status(OUT,'diagnosing',completed=pos+1,total=len(frames),gt=len(records),seconds=time.monotonic()-start)
    if args.smoke:
        write(OUT/'smoke.json',dict(passed=True,frames=len(frames),gt=len(records),geometry_checks=True,prediction_filter_count_checks=True));status(OUT,'smoke_passed');return
    summaries,comparisons=summarize(records)
    csv_write(OUT/'per_gt.csv',records);csv_write(OUT/'group_recall_and_errors.csv',summaries);csv_write(OUT/'paired_comparisons.csv',comparisons)
    write(OUT/'summary.json',dict(frames=len(frames),gt=len(records),all_groups=[r for r in summaries if r['group']=='all'],
        paired_all=[r for r in comparisons if r['group']=='all']))
    status(OUT,'complete',frames=len(frames),gt=len(records),seconds=time.monotonic()-start)

if __name__=='__main__':
    try:main()
    except BaseException:status(OUT,'failed',traceback=traceback.format_exc());raise
