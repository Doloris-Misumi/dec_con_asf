"""CPU-only VoD geometry/capacity audit. Does not change training files."""
from pathlib import Path
import copy
import importlib.util
import json
import pickle
import random
import sys

import numpy as np
import torch
import yaml
from easydict import EasyDict

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PCDET = ROOT / 'vod_taskdec_native/L4DR_taskdec'
DATA = Path('/home/hongsheng/vod/view_of_delft_PUBLIC/rlfusion_5f')


def load_module(name, path, package=False):
    spec = importlib.util.spec_from_file_location(
        name, path, submodule_search_locations=[str(path.parent)] if package else None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    torch.set_num_threads(2)
    torch.manual_seed(260920)
    fuser_module = load_module('vod_audit_fuser', PCDET / 'pcdet/models/model_utils/taskdec_fuser/__init__.py', True)
    calib_module = load_module('vod_audit_calibration', PCDET / 'pcdet/utils/calibration_kitti.py')
    base = yaml.safe_load((PCDET / 'tools/cfgs/VoD_models/TaskDec_PP_MildS05AuxHalf.yaml').read_text())
    checks = []
    for patch, query in [(4, 16), (2, 4)]:
        config = EasyDict(copy.deepcopy(base['MODEL']['BACKBONE_2D']['TASKDEC']))
        config.UCP.PATCH_SIZE = [patch, patch]
        config.UCP.N_QUERY = query
        net = fuser_module.TaskAwareDecControlledA2Fusion(
            config, [8, 8, 1], point_cloud_range=[0, 0, -3, 1.28, 1.28, 2],
            voxel_size=[.16, .16, 4], scl=False).train()
        inputs = {k: torch.randn(1, 64, 8, 8, requires_grad=True) for k in config.KEY_FEATS}
        inputs['gt_boxes'] = torch.tensor([[[.64, .64, -.5, .6, .6, 1.7, 0., 2.]]])
        outputs = net(inputs)
        loss = outputs['fused_feat'].square().mean() + .05 * outputs['patch_dec_loss']
        loss.backward()
        grads = [p.grad for p in net.parameters() if p.grad is not None]
        net.eval()
        with torch.no_grad():
            no_gt = net({k: inputs[k].detach() for k in config.KEY_FEATS})
        checks.append(dict(patch=patch, queries=query, output_shape=list(outputs['fused_feat'].shape),
                           finite_forward=bool(torch.isfinite(outputs['fused_feat']).all()),
                           finite_backward=all(bool(torch.isfinite(g).all()) for g in grads),
                           no_gt_inference_finite=bool(torch.isfinite(no_gt['fused_feat']).all()),
                           parameters=sum(p.numel() for p in net.parameters()),
                           caveat='8x8 synthetic CPU fuser check only; not a full detector or GPU memory benchmark'))
    ids = sorted(random.Random(260920).sample((DATA / 'ImageSets/train.txt').read_text().split(), 32))
    with (DATA / 'vod_infos_train.pkl').open('rb') as handle:
        infos = pickle.load(handle)
    image_shapes = {str(info['image']['image_idx']): info['image']['image_shape'] for info in infos}
    records = []
    lo, hi = np.array([0., -25.6, -3.]), np.array([51.2, 25.6, 2.])
    for frame in ids:
        path = DATA / 'training'
        lc = calib_module.Calibration(path / 'lidar_calib' / (frame + '.txt'))
        rc = calib_module.Calibration(path / 'radar_calib' / (frame + '.txt'))
        c = calib_module.Calibration(path / 'calib' / (frame + '.txt'))
        h, w = image_shapes[frame]
        for modality, folder, fields in [('lidar', 'lidar', 4), ('radar', 'radar_5f', 7)]:
            xyz = np.fromfile(path / folder / (frame + '.bin'), np.float32).reshape(-1, fields)[:, :3]
            if modality == 'radar':
                xyz = lc.rect_to_lidar(rc.lidar_to_rect(xyz))
            uv, depth = c.lidar_to_img(xyz)
            keep = (uv[:, 0] >= 0) & (uv[:, 0] < w) & (uv[:, 1] >= 0) & (uv[:, 1] < h) & (depth >= 0)
            xyz = xyz[keep & ((xyz >= lo) & (xyz < hi)).all(1)]
            for size in [.16, .128, .1, .08]:
                voxel = np.array([size, size, 4.])
                grid = np.rint((hi - lo) / voxel).astype(int)
                coords = np.floor((xyz - lo) / voxel).astype(int)
                coords = coords[((coords >= 0) & (coords < grid)).all(1)]
                active = len(np.unique(coords[:, :2], axis=0))
                records.append(dict(frame=frame, modality=modality, voxel_xy=size,
                                    valid_point_count=len(coords), active_pillars=active))
    summary = []
    for modality in ['lidar', 'radar']:
        for size in [.16, .128, .1, .08]:
            vals = [r['active_pillars'] for r in records if r['modality'] == modality and r['voxel_xy'] == size]
            summary.append(dict(modality=modality, voxel_xy=size, median=float(np.median(vals)),
                                maximum=max(vals), over_train_16000=sum(v > 16000 for v in vals)))
    result = dict(fuser_checks=checks, seed=260920, train_ids=ids, pillar_summary=summary,
                  point_count_records=records,
                  caveats=['Existing native coordinate transform and camera FOV filtering used.',
                           'Native vertical voxel geometry retained; no augmentation or GT sampling.',
                           'Counts do not measure the augmented full training distribution.',
                           'No GPU allocation, training, checkpoint change or AP evaluation.'])
    (OUT / 'cpu_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(fuser_checks=checks, pillar_summary=summary), indent=2))


if __name__ == '__main__':
    main()
