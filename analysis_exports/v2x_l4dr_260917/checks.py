"""Meaningful preflight checks for the native L4DR dataset adaptation."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from easydict import EasyDict
from v2x_taskdec import experiment as ex
from v2x_taskdec.dataset import V2XDataset, to_device
from data import L4DRDataset, collate, sample_radar
from model import L4DRDetector
from native_mme import match_coords

FORMAL = HERE / 'matched_80ep'


def cpu():
    cfg = json.loads((FORMAL / 'config.json').read_text())
    original = json.loads((ex.FORMAL / 'config.json').read_text())
    for key in ['data_root','split_root','class_names','label_map','point_cloud_range','head',
                'augmentation','epochs','batch_size','effective_batch_size','accumulation',
                'learning_rate','min_learning_rate','warmup_epochs','weight_decay','seed',
                'val_epochs','selection','score_threshold','nms_threshold','max_detections']:
        assert cfg[key] == original[key], key
    rng = np.random.RandomState(74)
    for n in [0,1,7,2048,5000]:
        points = rng.normal(size=(n,7)).astype(np.float32)
        sampled, valid = sample_radar(points,2048,np.random.RandomState(123))
        assert sampled.shape == (2048,7) and valid.all() == bool(n)
        assert np.isfinite(sampled).all()
    for n, m in [(0,9),(9,0),(1,1),(137,99)]:
        left = torch.from_numpy(rng.randint(0,20,size=(n,4))).int()
        right = torch.from_numpy(rng.randint(0,20,size=(m,4))).int()
        if n and m: right[:min(n,m,7)] = left[:min(n,m,7)]
        assert len(torch.unique(right,dim=0)) == len(right)
        a,b = match_coords(left,right)
        x,y = torch.where(((left[:,None].long()-right.long())**2).sum(2)==0)
        assert torch.equal(a,x) and torch.equal(b,y)
    ids = (FORMAL/'val_deduplicated.txt').read_text().split()
    schemas = json.loads(Path(cfg['point_schema_manifest']).read_text())
    selected = ids[:8] + ids[::max(1,len(ids)//12)]
    selected += [next(i for i in ids if schemas[i][sensor]['empty'])
                 for sensor in ['lidar','radar'] if any(schemas[i][sensor]['empty'] for i in ids)]
    selected = list(dict.fromkeys(selected))
    data = L4DRDataset(cfg,'val',ids=selected)
    ref = V2XDataset(original,'val',ids=selected)
    rows=[]
    for i,frame in enumerate(selected):
        a=data[i];b=data[i];r=ref[i]
        assert np.array_equal(a['gt_boxes'],r['gt_boxes']), frame
        assert np.array_equal(a['radar_points'],b['radar_points']), frame
        assert np.all(a['radar_points'][:,-1]==0)
        assert a['lidar'][0].shape[1:]==(32,4)
        rows.append(dict(frame=frame,gt=len(a['gt_boxes']),points=a['raw_point_counts'],
                         lidar_voxels=len(a['lidar'][0]),sampled_valid=int(a['radar_valid'].sum())))
    batch=collate([data[0],data[1]])
    assert batch['radar_points'].shape==(4096,8)
    out=dict(passed=True,at=ex.now(),matched_protocol_fields=True,
             exact_coordinate_join=True,sampler_cases=5,matched_gt_and_deterministic_eval=rows,
             radar_feature_semantics=cfg['l4dr']['radar_fields'])
    ex.atomic_json(FORMAL/'checks_cpu.json',out)
    print(json.dumps(out,indent=2),flush=True)


def gpu():
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='1'
    from pcdet.models.backbones_3d.vfe.pillar_vfe import MME_PillarVFE as NativeMME
    from pcdet.models.backbones_2d.map_to_bev.pointpillar_scatter import PointPillarScatter
    cfg=json.loads((FORMAL/'config.json').read_text())
    torch.set_num_threads(4);torch.cuda.set_per_process_memory_fraction(cfg['memory_fraction'])
    ex.seed_all(cfg['seed']);model=L4DRDetector(cfg).cuda()
    # Equivalence of the only adapted native arithmetic: coordinate matching,
    # output shape safety and explicit-batch scatter; include gradients.
    native=NativeMME(EasyDict(cfg['l4dr']['native_model']['VFE']),[4,7],cfg['voxel_size'],cfg['point_cloud_range']).cuda()
    native.load_state_dict(model.vfe.state_dict(),strict=True)
    fake={}
    for key,dim in [('lidar',4),('radar',8)]:
        counts=torch.tensor([4,2,3,1,3,2],device='cuda',dtype=torch.int32)
        values=torch.randn(6,32,dim,device='cuda')
        values[torch.arange(32,device='cuda')[None]>=counts[:,None]]=0
        if key=='radar': values[:,:,-2]=0
        fake[key+'_voxels']=values
        fake[key+'_voxel_num_points']=counts
        fake[key+'_voxel_coords']=torch.tensor([[0,0,5,5],[0,0,7,8],[0,0,10,20],[1,0,5,5],[1,0,7,8],[1,0,10,20]],device='cuda',dtype=torch.int32)
    fake['radar_voxel_coords'][2,3]+=1
    fake['batch_size']=2
    native.train();model.vfe.train()
    a=native(copy.deepcopy(fake));b=model.vfe(copy.deepcopy(fake));diff={}
    for key in ['lidar_pillar_features','radar_pillar_features']:
        torch.testing.assert_close(a[key],b[key],rtol=1e-5,atol=1e-6)
        diff[key]=float((a[key]-b[key]).abs().max())
    sum(a[k].square().sum() for k in diff).backward()
    sum(b[k].square().sum() for k in diff).backward()
    for (name,x),(name2,y) in zip(native.named_parameters(),model.vfe.named_parameters()):
        assert name==name2
        torch.testing.assert_close(x.grad,y.grad,rtol=1e-5,atol=1e-6)
    scatter=PointPillarScatter(EasyDict(NUM_BEV_FEATURES=[64,64]),model.grid)
    sa=scatter(dict(a));sb=model.scatter(dict(b))
    for key in ['lidar_spatial_features','radar_spatial_features']:
        torch.testing.assert_close(sa[key],sb[key],rtol=0,atol=0)
    del native,scatter,a,b,sa,sb,fake
    model.zero_grad(set_to_none=True)
    smoke=torch.load(FORMAL/'smoke/last.pt',map_location='cpu')
    assert smoke['state']['optimizer_updates']==50
    model.load_state_dict(smoke['model'],strict=True);del smoke
    model.eval()
    ids=(FORMAL/'val_deduplicated.txt').read_text().split()
    data=L4DRDataset(cfg,'val',ids=ids[:2])
    batch=to_device(collate([data[0],data[1]]),'cuda')
    original_gt=batch.pop('gt_boxes')
    with torch.no_grad():
        no_gt=model(batch)
        batch['gt_boxes']=original_gt*0+12345.
        changed_gt=model(batch)
    for a,b in zip(no_gt,changed_gt):
        assert torch.isfinite(a).all()
        torch.testing.assert_close(a,b,rtol=0,atol=0)
    del batch['gt_boxes']
    empty_cases=[]
    for empty in ['lidar','radar','both']:
        test=dict(batch)
        if empty in ['lidar','both']: test['lidar']=tuple(t[:0] for t in batch['lidar'])
        if empty in ['radar','both']:
            test['radar_valid']=torch.zeros_like(batch['radar_valid'])
            test['radar_points']=torch.zeros_like(batch['radar_points'])
            test['radar_points'][:,0]=batch['radar_points'][:,0]
        with torch.no_grad(): preds=model(test)
        assert len(preds)==2 and all(torch.isfinite(p).all() for p in preds)
        empty_cases.append(dict(empty=empty,prediction_counts=[len(p) for p in preds],counts=model.last_counts))
    # Empty radar and empty LiDAR must also admit a finite training/backward path.
    model.train();test['gt_boxes']=original_gt
    out=model(test);assert torch.isfinite(out['loss'])
    out['loss'].backward()
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    result=dict(passed=True,at=ex.now(),native_mme_max_error=diff,
        native_mme_gradients_equivalent=True,native_scatter_exact=True,
        inference_without_gt_and_with_corrupted_gt_exact=True,empty_cases=empty_cases,
        all_empty_train_loss=float(out['loss'].detach()),empty_backward_finite=True,
        peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
        peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30)
    ex.atomic_json(FORMAL/'checks_gpu.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['cpu','gpu'])
    args=parser.parse_args()
    cpu() if args.mode=='cpu' else gpu()
