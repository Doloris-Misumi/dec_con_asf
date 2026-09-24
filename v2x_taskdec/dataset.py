"""Paired camera/LiDAR/radar dataset using explicitly configured binary fields."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset
from spconv.utils import Point2VoxelCPU3d
from cumm import tensorview as tv
from .geometry import read_calibration, camera_box_to_lidar, augment_world, transform_points
from .point_schema import load_points


class V2XDataset(Dataset):
    def __init__(self, cfg, split, training=False, ids=None):
        self.cfg = cfg
        self.data = Path(cfg['data_root']) / 'training'
        self.ids = ids if ids is not None else (Path(cfg['split_root'])/(split+'.txt')).read_text().split()
        self.training = training
        self.schemas=json.loads(Path(cfg['point_schema_manifest']).read_text())
        self.voxelizers = {}
        for key in ['lidar','radar']:
            self.voxelizers[key] = Point2VoxelCPU3d(vsize_xyz=cfg['voxel_size'],
                coors_range_xyz=cfg['point_cloud_range'], num_point_features=cfg['point_features'][key],
                max_num_voxels=cfg['max_voxels'], max_num_points_per_voxel=cfg['max_points_per_voxel'])

    def __len__(self):
        return len(self.ids)

    def read_points(self, frame, key, calibration):
        group = 'velodyne' if key=='lidar' else 'radar'
        points = load_points(self.data/group/(frame+'.bin'),key,self.schemas[frame][key])
        transform=calibration['raw_lidar_to_ego'] if key=='lidar' else calibration['radar_to_ego']
        points[:,:3]=transform_points(points[:,:3],transform)
        return points

    def read_boxes(self, frame, calibration):
        boxes=[]
        for line in (self.data/'label_2'/(frame+'.txt')).read_text().splitlines():
            fields=line.split()
            mapped=self.cfg['label_map'].get(fields[0]) if fields else None
            if mapped not in self.cfg['class_names']:continue
            hwl=np.asarray(fields[8:11],dtype=np.float32)
            if np.any(hwl<=0):continue
            box=camera_box_to_lidar(np.asarray(fields[11:14],dtype=np.float32),hwl,float(fields[14]),calibration)
            boxes.append(np.r_[box,self.cfg['class_names'].index(mapped)+1])
        return np.asarray(boxes,dtype=np.float32).reshape(-1,8)

    def __getitem__(self, idx):
        frame=self.ids[idx]
        calibration=read_calibration(self.data/'calib'/(frame+'.txt'))
        points=[self.read_points(frame,key,calibration) for key in ['lidar','radar']]
        boxes=self.read_boxes(frame,calibration)
        augmentation=np.eye(4,dtype=np.float32)
        if self.training:
            params=self.cfg['augmentation']
            points,boxes,augmentation=augment_world(points,boxes,
                np.random.uniform(*params['rotation']),np.random.uniform(*params['scale']),
                np.random.rand()<params['flip_probability'])
        roi=np.array(self.cfg['point_cloud_range'],dtype=np.float32)
        valid=((boxes[:,:3]>=roi[:3]) & (boxes[:,:3]<roi[3:])).all(1)
        boxes=boxes[valid]
        result=dict(frame_id=frame,gt_boxes=boxes,world_aug=augmentation)
        for key,pts in zip(['lidar','radar'],points):
            if self.training:
                np.random.shuffle(pts)
            vox,coords,num=self.voxelizers[key].point_to_voxel(tv.from_numpy(np.ascontiguousarray(pts)))
            result[key]=(vox.numpy().copy(),coords.numpy().copy(),num.numpy().copy())
        if 'camera' in self.cfg['modalities']:
            image_path=next((self.data/'image_2').glob(frame+'.*'))
            with Image.open(image_path) as src:
                src=src.convert('RGB');w,h=src.size
                target_h,target_w=self.cfg['image_size']
                image=np.asarray(src.resize((target_w,target_h),Image.BILINEAR),dtype=np.float32)/255.
            image=(image-np.asarray([.485,.456,.406],np.float32))/np.asarray([.229,.224,.225],np.float32)
            projection=np.eye(4,dtype=np.float32)
            projection[:3]=calibration['projection']
            projection[0]*=target_w/w
            projection[1]*=target_h/h
            result['image']=image.transpose(2,0,1).copy()
            result['lidar_to_image']=(projection@calibration['lidar_to_camera']).astype(np.float32)
        return result


def collate(batch):
    result={'frame_ids':[item['frame_id'] for item in batch]}
    count=max(1,max(len(item['gt_boxes']) for item in batch))
    boxes=np.zeros((len(batch),count,8),np.float32)
    for i,item in enumerate(batch):boxes[i,:len(item['gt_boxes'])]=item['gt_boxes']
    result['gt_boxes']=torch.from_numpy(boxes)
    for key in ['lidar','radar']:
        vox,coords,nums=[],[],[]
        for i,item in enumerate(batch):
            v,c,n=item[key];vox.append(v);nums.append(n)
            coords.append(np.pad(c,((0,0),(1,0)),constant_values=i))
        result[key]=tuple(torch.from_numpy(np.concatenate(a)) for a in [vox,coords,nums])
    for key in ['image','lidar_to_image','world_aug']:
        if key in batch[0]:result[key]=torch.from_numpy(np.stack([x[key] for x in batch]))
    return result


def to_device(batch,device):
    # DataLoader pin_memory converts tuples to lists on torch 1.10.
    def move(value):
        if isinstance(value,torch.Tensor):return value.to(device,non_blocking=True)
        if isinstance(value,(tuple,list)):return type(value)(move(x) for x in value)
        if isinstance(value,dict):return {k:move(v) for k,v in value.items()}
        return value
    return move(batch)
