"""Freeze VoD anchor priors from original training labels, before augmentation."""
import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import sys
from types import SimpleNamespace

ROOT = Path('/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec')
OUT = Path('/home/hongsheng/dec_con_asf/analysis_exports/objdec_vod_adapted_anchors_260921')
BASE = ROOT/'tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920.yaml'
DEST = ROOT/'tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Anchors_260921.yaml'
os.chdir(ROOT/'tools')
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
import yaml
from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.utils import box_utils, calibration_kitti, common_utils
from pcdet.datasets.processor.data_processor import DataProcessor


def main():
    assert not DEST.exists(), 'Frozen config already exists; do not overwrite.'
    torch.set_num_threads(4)
    cfg_from_yaml_file(str(BASE), cfg)
    raw = yaml.safe_load(BASE.read_text())
    data = Path(cfg.DATA_CONFIG.DATA_PATH)
    source = data/'vod_infos_train.pkl'
    infos = pickle.load(source.open('rb'))
    ids = [str(i['point_cloud']['lidar_idx']) for i in infos]
    assert len(infos) == 5139 and ids == (data/'ImageSets/train.txt').read_text().split()
    # Match the class selection, coordinate conversion and actual range processor.
    processor_cfg = cfg.DATA_CONFIG.DATA_PROCESSOR[0]
    assert processor_cfg.NAME == 'mask_points_and_boxes_outside_range'
    processor = SimpleNamespace(point_cloud_range=np.asarray(cfg.DATA_CONFIG.POINT_CLOUD_RANGE), training=True)
    samples = {n: [] for n in cfg.CLASS_NAMES}
    calib_hash = hashlib.sha256()
    max_meta_difference = 0.0
    counts_before_roi = {n: 0 for n in cfg.CLASS_NAMES}
    for info in infos:
        frame = str(info['point_cloud']['lidar_idx'])
        path = data/'training/calib'/f'{frame}.txt'
        calib_hash.update(frame.encode()+b'\0'+path.read_bytes())
        calib = calibration_kitti.Calibration(path)
        a = common_utils.drop_info_with_name(copy.deepcopy(info['annos']), name='DontCare')
        cam = np.concatenate([a['location'], a['dimensions'], a['rotation_y'][:,None]],axis=1).astype(np.float32)
        boxes = box_utils.boxes3d_kitti_camera_to_lidar(cam, calib)
        assert np.isfinite(boxes).all() and (boxes[:,3:6]>0).all()
        if 'gt_boxes_lidar' in a and len(a['gt_boxes_lidar']) == len(boxes):
            max_meta_difference = max(max_meta_difference, float(np.abs(boxes-a['gt_boxes_lidar']).max(initial=0)))
        for name in cfg.CLASS_NAMES:
            selected = boxes[a['name']==name]
            counts_before_roi[name] += len(selected)
            filtered = DataProcessor.mask_points_and_boxes_outside_range(
                processor, {'gt_boxes':selected.copy()}, processor_cfg)['gt_boxes']
            samples[name].append(filtered)
    report = dict(frames=len(infos), source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        calibration_sha256=calib_hash.hexdigest(), config_source=str(BASE), config_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
        fitting_data='original training annotations, pre-augmentation; no validation data read',
        label_pipeline=['drop DontCare','camera-to-LiDAR via native calibration and float32 camera boxes',
                        'select Car/Pedestrian/Cyclist','native training range processor'],
        use_center_to_filter=processor_cfg.get('USE_CENTER_TO_FILTER',True),
        fov_note='FOV filters points, not GT boxes in the native dataset.',
        augmentation_note='DB sampling, flip, rotation and scale remain enabled for training; priors use original labels, not a random augmented realization.',
        roi=list(cfg.DATA_CONFIG.POINT_CLOUD_RANGE), max_abs_difference_from_metadata_boxes=max_meta_difference,
        rounding_decimals=2, classes={})
    changed = copy.deepcopy(raw)
    for anchor in changed['MODEL']['DENSE_HEAD']['ANCHOR_GENERATOR_CONFIG']:
        name = anchor['class_name']
        boxes = np.concatenate(samples[name],axis=0)
        assert len(boxes)>1000
        lwh = np.median(boxes[:,3:6],axis=0)
        bottom = boxes[:,2]-boxes[:,5]/2
        z = float(np.median(bottom))
        report['classes'][name] = dict(before_roi=counts_before_roi[name], after_roi=len(boxes),
            median_lwh=lwh.tolist(), median_bottom_z=z,
            lwh_q10_q90=np.quantile(boxes[:,3:6],[.1,.9],axis=0).tolist(),
            bottom_z_q10_q90=np.quantile(bottom,[.1,.9]).tolist(),
            old_sizes=anchor['anchor_sizes'],old_bottom_heights=anchor['anchor_bottom_heights'],
            new_sizes=[[round(float(v),2) for v in lwh]], new_bottom_heights=[round(z,2)])
        anchor['anchor_sizes'] = report['classes'][name]['new_sizes']
        anchor['anchor_bottom_heights'] = report['classes'][name]['new_bottom_heights']
    # Verify only these six fields change; rotations, match thresholds, count unchanged.
    reset = copy.deepcopy(changed)
    diffs = []
    for new, old in zip(reset['MODEL']['DENSE_HEAD']['ANCHOR_GENERATOR_CONFIG'],raw['MODEL']['DENSE_HEAD']['ANCHOR_GENERATOR_CONFIG']):
        for field in ['anchor_sizes','anchor_bottom_heights']:
            diffs.append(dict(class_name=new['class_name'], field=field, old=old[field], new=copy.deepcopy(new[field])))
            new[field]=old[field]
    assert reset == raw
    report['config_changes']=diffs
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'anchor_statistics.json').write_text(json.dumps(report,indent=2)+'\n')
    DEST.write_text('# ObjDec VoD: only anchor sizes and bottom heights adapted from 5139 training frames.\n'
        '# 0.16m, patch2/local, mild losses, batch8 x2, FP32, scratch80 unchanged.\n'
        '# Use scripts/run_objdec_vod_adapted_anchors_260921.py.\n'+yaml.safe_dump(changed,sort_keys=False))
    print(json.dumps(report['classes'],indent=2))
    print('CONFIG',DEST)


if __name__=='__main__':
    main()
