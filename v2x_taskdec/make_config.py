"""Prepare a common engineering config; training budget is locked after timing."""
import json
from pathlib import Path
import numpy as np
import yaml
from .geometry import read_calibration, camera_box_to_lidar

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis_exports/v2x_taskdec_260916'


def main():
    integrity=json.loads((OUT/'data_integrity.json').read_text())
    cfg=dict(data_root=integrity['dataset_root'],split_root=integrity['split_root'],
        point_schema_manifest=str(OUT/'point_schema_manifest.json'),
        modalities=['camera','lidar','radar'],class_names=['Vehicle','Pedestrian','Cyclist'],
        label_map={'Car':'Vehicle','Truck':'Vehicle','Bus':'Vehicle','Pedestrian':'Pedestrian','Cyclist':'Cyclist'},
        point_cloud_range=[0.,-51.2,-5.,102.4,51.2,3.],voxel_size=[.4,.4,8.],
        point_features={'lidar':4,'radar':6},max_voxels=32000,max_points_per_voxel=32,
        image_size=[288,512],depth_bound=[1.,102.,1.],
        image_pretrained='/home/hongsheng/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth',
        augmentation={'rotation':[-.392699,.392699],'scale':[.95,1.05],'flip_probability':.5},
        patch_dec_weight=.12,score_threshold=.001,nms_threshold=.1,max_detections=500,
        seed=260916,precision='fp32',budget_status='pending_real_timing')
    head=yaml.safe_load((ROOT/'vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/TaskDec_PP.yaml').read_text())['MODEL']['DENSE_HEAD']
    dims={key:[] for key in cfg['class_names']};bottoms={key:[] for key in dims}
    data=Path(cfg['data_root'])/'training'
    for frame in (Path(cfg['split_root'])/'train.txt').read_text().split():
        cal=read_calibration(data/'calib'/(frame+'.txt'))
        for line in (data/'label_2'/(frame+'.txt')).read_text().splitlines():
            a=line.split();name=cfg['label_map'].get(a[0]) if a else None
            if name is None:continue
            box=camera_box_to_lidar(np.asarray(a[11:14],float),np.asarray(a[8:11],float),float(a[14]),cal)
            if not ((box[:3]>=np.array(cfg['point_cloud_range'][:3])).all() and
                    (box[:3]<np.array(cfg['point_cloud_range'][3:])).all() and (box[3:6]>0).all()):continue
            dims[name].append(box[3:6]);bottoms[name].append(box[2]-box[5]/2)
    for anchor,name in zip(head['ANCHOR_GENERATOR_CONFIG'],cfg['class_names']):
        anchor['class_name']=name
        anchor['anchor_sizes']=[np.median(dims[name],axis=0).astype(float).tolist()]
        anchor['anchor_bottom_heights']=[float(np.median(bottoms[name]))]
    cfg['head']=head
    cfg['anchor_statistics']={name:dict(count=len(dims[name]),median_dimensions=np.median(dims[name],axis=0).tolist(),
                                        median_bottom=float(np.median(bottoms[name]))) for name in dims}
    (OUT/'engineering_config.json').write_text(json.dumps(cfg,indent=2))
    print(json.dumps(cfg['anchor_statistics'],indent=2))


if __name__=='__main__':main()
