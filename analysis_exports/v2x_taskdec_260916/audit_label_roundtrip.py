"""Train-only label audit: camera -> horizontal ego boxes -> camera.

No learned predictions, validation/test selection, GPU use or protocol changes.
"""
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
sys.path.insert(0,str(ROOT))
from v2x_taskdec.geometry import read_calibration,camera_box_to_lidar,lidar_box_to_camera


def polygon(location,dimensions,angle):
    h,w,length=dimensions
    return cv2.boxPoints(((float(location[0]),float(location[2])),
                         (float(length),float(w)),float(-angle*180/np.pi)))


def main():
    started=time.monotonic()
    cfg=json.loads((BASE/'controlled_80ep/config.json').read_text())
    root=Path(cfg['data_root'])/'training'
    ids=(Path(cfg['split_root'])/'train.txt').read_text().split()
    roi=np.asarray(cfg['point_cloud_range'])
    stats={name:dict(count=0,difficulty_counts=[0,0,0],min_bev_iou=1.,min_3d_iou=1.,
                    below_strict_iou=0,max_yaw_error_radians=0.,max_location_error_m=0.,worst_frame=None,
                    min_guaranteed_3d_iou=1.,guaranteed_iou_below_strict=0,opencv_bound_violations=0)
           for name in cfg['class_names']}
    failures=[]
    for frame in ids:
        cal=read_calibration(root/'calib'/(frame+'.txt'))
        for line in (root/'label_2'/(frame+'.txt')).read_text().splitlines():
            row=line.split()
            if not row:continue
            name=cfg['label_map'].get(row[0])
            if name not in stats:continue
            hwl=np.array(row[8:11],float);location=np.array(row[11:14],float);yaw=float(row[14])
            box=camera_box_to_lidar(location,hwl,yaw,cal)
            if not ((hwl>0).all() and (box[:3]>=roi[:3]).all() and (box[:3]<roi[3:]).all()):continue
            loc2,dim2,yaw2=lidar_box_to_camera(box,cal)
            intersection=float(cv2.intersectConvexConvex(polygon(location,hwl,yaw),polygon(loc2,dim2,yaw2))[0])
            area1=hwl[1]*hwl[2];area2=dim2[1]*dim2[2]
            intersection=max(0.,min(intersection,area1,area2))
            bev=intersection/max(1e-12,area1+area2-intersection)
            height=max(0.,min(location[1],loc2[1])-max(location[1]-hwl[0],loc2[1]-dim2[0]))
            inter3=intersection*height
            iou3=inter3/max(1e-12,np.prod(hwl)+np.prod(dim2)-inter3)
            angle_error=abs((yaw2-yaw+np.pi)%(2*np.pi)-np.pi)
            location_error=float(np.linalg.norm(loc2-location))
            # A rotation moves any point in the source rectangle by at most
            # 2*r*sin(|delta|/2). Add translation and half-dimension mismatch.
            # Eroding each edge by this margin gives an axis-aligned rectangle
            # guaranteed to lie in BOTH boxes, independently of polygon code.
            radius=np.hypot(hwl[1],hwl[2])/2
            margin=(2*radius*np.sin(angle_error/2)+np.linalg.norm((loc2-location)[[0,2]])+
                    np.max(np.abs(dim2[[1,2]]-hwl[[1,2]]))/2+1e-10)
            guaranteed_area=max(0.,hwl[1]-2*margin)*max(0.,hwl[2]-2*margin)
            guaranteed_inter=guaranteed_area*height
            guaranteed_iou=guaranteed_inter/max(1e-12,np.prod(hwl)+np.prod(dim2)-guaranteed_inter)
            st=stats[name];st['count']+=1
            for i,(minimum_height,maximum_occlusion,maximum_truncation) in enumerate(zip([40,25,25],[0,1,2],[.15,.3,.5])):
                if (float(row[7])-float(row[5])>minimum_height and int(row[2])<=maximum_occlusion and float(row[1])<=maximum_truncation):
                    st['difficulty_counts'][i]+=1
            st['min_bev_iou']=float(min(st['min_bev_iou'],bev))
            if iou3<st['min_3d_iou']:st['min_3d_iou']=float(iou3);st['worst_frame']=frame
            st['max_yaw_error_radians']=float(max(st['max_yaw_error_radians'],angle_error))
            st['max_location_error_m']=max(st['max_location_error_m'],location_error)
            threshold=.7 if name=='Vehicle' else .5
            st['min_guaranteed_3d_iou']=float(min(st['min_guaranteed_3d_iou'],guaranteed_iou))
            st['guaranteed_iou_below_strict']+=int(guaranteed_iou<=threshold)
            st['opencv_bound_violations']+=int(iou3+1e-5<guaranteed_iou)
            if iou3<=threshold:
                st['below_strict_iou']+=1
                failures.append(dict(frame=frame,label_class=row[0],iou3d=float(iou3),yaw_error=float(angle_error)))
    result=dict(scope='all official train labels within locked center ROI; no validation/test labels or model predictions',
                frames=len(ids),classes=stats,opencv_below_strict_iou_case_count=len(failures),
                elapsed_seconds=time.monotonic()-started,
                note='Use min_guaranteed_3d_iou for conclusions. The earlier min_3d_iou/min_bev_iou fields are OpenCV diagnostics, invalid where they violate the analytic lower bound. Geometric roundtrip only, not detector AP; difficulty counts overlap.')
    (BASE/'label_roundtrip_bounds_audit.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
