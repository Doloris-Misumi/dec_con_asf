"""V2X-V local ROI/Vehicle adapter around the pinned official AP_R40 evaluator."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .geometry import read_calibration,camera_box_to_lidar,lidar_box_to_camera,project_points,corners_lidar
from .evaluation.eval import kitti_eval


def annotation(names,dimensions,location,rotation,bbox,score=None,truncated=None,occluded=None,alpha=None):
    n=len(names)
    return dict(name=np.asarray(names,dtype='<U20'),dimensions=np.asarray(dimensions,np.float64).reshape(-1,3),
        location=np.asarray(location,np.float64).reshape(-1,3),rotation_y=np.asarray(rotation,np.float64),
        bbox=np.asarray(bbox,np.float64).reshape(-1,4),score=np.ones(n) if score is None else np.asarray(score,np.float64),
        truncated=np.zeros(n) if truncated is None else np.asarray(truncated,np.float64),
        occluded=np.zeros(n,np.int32) if occluded is None else np.asarray(occluded,np.int32),
        alpha=np.zeros(n) if alpha is None else np.asarray(alpha,np.float64))


class Evaluator:
    def __init__(self,cfg):
        self.cfg=cfg;self.data=Path(cfg['data_root'])/'training';self.gt_cache={}
        self.roi=np.asarray(cfg['point_cloud_range']);self.name_map={'Vehicle':'Car','Pedestrian':'Pedestrian','Cyclist':'Cyclist'}

    def ground_truth(self,frame):
        if frame in self.gt_cache:return self.gt_cache[frame]
        cal=read_calibration(self.data/'calib'/(frame+'.txt'))
        rows=[]
        for line in (self.data/'label_2'/(frame+'.txt')).read_text().splitlines():
            a=line.split()
            if not a:continue
            name=self.cfg['label_map'].get(a[0])
            if name is None:continue
            hwl=np.asarray(a[8:11],float);loc=np.asarray(a[11:14],float);ry=float(a[14])
            box=camera_box_to_lidar(loc,hwl,ry,cal)
            if not ((box[:3]>=self.roi[:3]).all() and (box[:3]<self.roi[3:]).all() and (hwl>0).all()):continue
            rows.append((self.name_map[name],hwl[[2,0,1]],loc,ry,[float(x) for x in a[4:8]],float(a[1]),int(a[2]),float(a[3])))
        if rows:
            ns,ds,ls,rs,bs,ts,os,al=zip(*rows)
            result=annotation(ns,ds,ls,rs,bs,truncated=ts,occluded=os,alpha=al)
        else:result=annotation([],[],[],[],[])
        self.gt_cache[frame]=result;return result

    def predictions(self,frame,predictions):
        cal=read_calibration(self.data/'calib'/(frame+'.txt'))
        with Image.open(next((self.data/'image_2').glob(frame+'.*'))) as image:w,h=image.size
        rows=[]
        for box in predictions:
            if not np.isfinite(box).all() or np.any(box[3:6]<=0):continue
            if not ((box[:3]>=self.roi[:3]).all() and (box[:3]<self.roi[3:]).all()):continue
            location,dim_hwl,ry=lidar_box_to_camera(box,cal)
            if location[2]<=.1:continue
            corners=corners_lidar(box[None,:7])[0];uv,depth=project_points(corners,cal)
            uv=uv[depth>.1]
            if not len(uv):continue
            bbox=np.r_[uv.min(0),uv.max(0)]
            bbox[[0,2]]=np.clip(bbox[[0,2]],0,w-1);bbox[[1,3]]=np.clip(bbox[[1,3]],0,h-1)
            name=self.name_map[self.cfg['class_names'][int(box[8])-1]]
            alpha=(ry-np.arctan2(location[0],location[2])+np.pi)%(2*np.pi)-np.pi
            rows.append((name,dim_hwl[[2,0,1]],location,ry,bbox,box[7],alpha))
        if not rows:return annotation([],[],[],[],[])
        ns,ds,ls,rs,bs,ss,al=zip(*rows)
        return annotation(ns,ds,ls,rs,bs,score=ss,alpha=al)

    def evaluate(self,predictions,ids):
        if set(ids)-set(predictions):raise ValueError('Missing prediction frames')
        gt=[self.ground_truth(i) for i in ids]
        dt=[self.predictions(i,predictions[i]) for i in ids]
        text,metrics=kitti_eval(gt,dt,['Car','Pedestrian','Cyclist'],eval_types=['bev','3d'],metric='R40')
        metrics={k.replace('KITTI/Car_','V2X/Vehicle_').replace('KITTI/','V2X/'):float(v) for k,v in metrics.items()}
        return dict(frames=len(ids),metrics=metrics,table=text.replace('Car AP@','Vehicle AP@'),
                    selection_metric=metrics['V2X/Overall_3D_moderate'],
                    protocol='AP_R40 strict IoU 0.7/0.5/0.5, loose 0.5/0.25/0.25; KITTI difficulties; fixed ego-center ROI; Vehicle merges Car/Truck/Bus')


def check_metric():
    import copy
    gt=annotation(['Car','Pedestrian','Cyclist'],[[4.,1.6,1.8],[.7,1.7,.7],[1.8,1.6,.7]],
                   [[0,1.5,10],[5,1.5,20],[-5,1.5,25]],[0.,.3,-.2],[[0,0,100,100]]*3)
    empty=annotation([],[],[],[],[])
    gts=[empty]+[copy.deepcopy(gt) for _ in range(80)]
    _,perfect=kitti_eval(gts,copy.deepcopy(gts),['Car','Pedestrian','Cyclist'],eval_types=['bev','3d'],metric='R40')
    assert all(abs(v-100)<1e-5 for v in perfect.values()),perfect
    _,missing=kitti_eval(gts,[copy.deepcopy(empty) for _ in gts],['Car','Pedestrian','Cyclist'],eval_types=['bev','3d'],metric='R40')
    assert all(v==0 for v in missing.values()),missing
    report=dict(status='passed',perfect_prediction_ap=100,empty_prediction_ap=0,includes_empty_gt_frame=True,metrics_checked=len(perfect))
    out=Path(__file__).resolve().parents[1]/'analysis_exports/v2x_taskdec_260916/evaluator_check.json'
    out.write_text(json.dumps(report,indent=2));print(report)


if __name__=='__main__':check_metric()
