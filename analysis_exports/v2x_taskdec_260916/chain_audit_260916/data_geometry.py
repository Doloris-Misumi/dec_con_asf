"""CPU audit of paired-frame projection and class/ROI contracts."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path('/home/hongsheng/dec_con_asf');sys.path.insert(0,str(ROOT))
from v2x_taskdec.geometry import read_calibration,camera_box_to_lidar,lidar_box_to_camera,augment_world,transform_points
OUT=Path(__file__).parent;F=OUT.parent/'controlled_80ep';cfg=json.loads((F/'config.json').read_text())
root=Path(cfg['data_root'])/'training';roi=np.asarray(cfg['point_cloud_range'])
stats={}
for split in ['train','val']:
    ids=(Path(cfg['split_root'])/(split+'.txt')).read_text().split();chosen=[ids[i] for i in np.linspace(0,len(ids)-1,128,dtype=int)]
    rec={'frames':len(chosen),'gt_counts':[0,0,0],'max_center_roundtrip_m':0.,'max_lift_roundtrip_m':0.,'max_augmented_lift_roundtrip_m':0.,'missing_files':[]}
    for frame in chosen:
        cal=read_calibration(root/'calib'/(frame+'.txt'))
        for group,ext in [('velodyne','bin'),('radar','bin'),('label_2','txt')]:
            if not (root/group/(frame+'.'+ext)).is_file():rec['missing_files'].append(frame+':'+group)
        with Image.open(next((root/'image_2').glob(frame+'.*'))) as im:w,h=im.size
        P=np.eye(4);P[:3]=cal['projection'];P[0]*=cfg['image_size'][1]/w;P[1]*=cfg['image_size'][0]/h
        L=P@cal['lidar_to_camera']
        boxes=[]
        for line in (root/'label_2'/(frame+'.txt')).read_text().splitlines():
            a=line.split();name=cfg['label_map'].get(a[0])
            if name is None:continue
            box=camera_box_to_lidar(np.array(a[11:14],float),np.array(a[8:11],float),float(a[14]),cal)
            if not ((box[:3]>=roi[:3]).all() and (box[:3]<roi[3:]).all()):continue
            ci=cfg['class_names'].index(name);rec['gt_counts'][ci]+=1;boxes.append(np.r_[box,ci+1])
            loc,_,_=lidar_box_to_camera(box,cal)
            rec['max_center_roundtrip_m']=max(rec['max_center_roundtrip_m'],float(np.linalg.norm(loc-np.array(a[11:14],float))))
        if not boxes:continue
        boxes=np.array(boxes);pts=boxes[:,:3];uvz=np.c_[pts,np.ones(len(pts))]@L.T
        # Same pixel/depth representation supplied to camera lift; no camera_box inverse helper.
        uv=uvz[:,:2]/uvz[:,2:3];rays=np.c_[uv*uvz[:,2:3],uvz[:,2],np.ones(len(pts))]
        lifted=rays@np.linalg.inv(L).T
        _,ab,A=augment_world([],boxes,.27,1.03,True)
        lifted_aug=lifted@A.T
        rec['max_lift_roundtrip_m']=max(rec['max_lift_roundtrip_m'],float(np.abs(lifted[:,:3]-pts).max()))
        rec['max_augmented_lift_roundtrip_m']=max(rec['max_augmented_lift_roundtrip_m'],float(np.abs(lifted_aug[:,:3]-ab[:,:3]).max()))
    assert not rec['missing_files']
    assert rec['max_lift_roundtrip_m']<1e-5 and rec['max_augmented_lift_roundtrip_m']<1e-4
    stats[split]=rec
(OUT/'data_geometry.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
