"""Isolated matched ASF-style CLR and ObjDec LR controls at 0.16m."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import torch
from v2x_taskdec import experiment as ex, train as training
from v2x_taskdec.model import V2XDetector

BASE = ROOT / 'analysis_exports/v2x_grid016_260918/matched_80ep'
CASES = {
    'asf_clr': dict(gpu='0', variant='patch', modalities=['camera','lidar','radar']),
    'objdec_lr': dict(gpu='1', variant='taskdec', modalities=['lidar','radar']),
}


def read(path):
    return json.loads(Path(path).read_text())


def formal(case):
    return HERE / (case + '_80ep')


def prepare(case):
    setting = CASES[case]
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == setting['gpu']
    destination = formal(case)
    if destination.exists():
        raise FileExistsError(destination)
    ex.FORMAL = BASE
    ex.verify_sources()
    cfg = copy.deepcopy(read(BASE / 'config.json'))
    cfg.update(modalities=setting['modalities'], memory_fraction=.60, created_at=ex.now())
    fc = cfg['resolved_fuser']
    fc['KEY_FEATS'] = setting['modalities']
    fc['DIM_FEATS'] = [64] * len(setting['modalities'])
    if case == 'asf_clr':
        fc['NAME'] = 'A2Fusion'
        for key in list(fc):
            if key.startswith(('PATCH_DEC_', 'DEC_CONTROL_')):
                del fc[key]
        cfg['patch_dec_weight'] = 0.
    assert cfg['voxel_size'] == [.16,.16,8.]
    assert cfg['batch_size'] == 2 and cfg['accumulation'] == 4
    assert cfg['epochs'] == 80 and cfg['effective_batch_size'] == 8
    assert fc['UCP']['PATCH_SIZE'] == [2,2] and fc['UCP']['N_QUERY'] == 4
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(cfg['memory_fraction'])
    ex.seed_all(cfg['seed'])
    model = V2XDetector(cfg, setting['variant'])
    source = BASE / 'taskdec_initial.pt'
    assert ex.sha(source) == read(BASE / 'initialization.json')['taskdec']['sha256']
    saved = torch.load(source, map_location='cpu')
    fresh = model.state_dict()
    for key in fresh:
        assert key in saved, ('New unpaired tensor', key)
        assert fresh[key].shape == saved[key].shape, key
        fresh[key] = saved[key].clone()
    model.load_state_dict(fresh, strict=True)
    assert list(model.encoders) == setting['modalities']
    assert not model.fuser.is_scl
    if case == 'objdec_lr':
        assert all('camera' not in key for key in fresh)
        assert len(model.fuser.key_feats) == 2
    else:
        assert not hasattr(model.fuser, 'patch_common')
        assert torch.allclose(model.encoders['camera'].voxel_size, torch.tensor([.16,.16,8.]))
    destination.mkdir()
    ex.atomic_json(destination/'config.json', cfg)
    for name in ['val_deduplicated.txt','test_deduplicated.txt']:
        (destination/name).write_bytes((BASE/name).read_bytes())
    path = destination / (setting['variant']+'_initial.pt')
    ex.save_checkpoint(path, fresh)
    common = {k:v for k,v in fresh.items() if not k.startswith('fuser.')}
    manifest = {setting['variant']:dict(file=path.name,sha256=ex.sha(path),
        parameters=sum(p.numel() for p in model.parameters()),
        copied_tensors=len(fresh),removed_tensors=sorted(set(saved)-set(fresh)),
        shared_backbone_head_hash=ex.state_hash(common),
        shared_source_subset_hash=ex.state_hash({k:saved[k] for k in common}),
        common_fuser_hash=ex.state_hash({k:v for k,v in fresh.items() if k.startswith('fuser.')}),
        copied_from=str(source),copied_from_sha256=ex.sha(source),trained_checkpoint_used=False)}
    assert manifest[setting['variant']]['shared_backbone_head_hash'] == manifest[setting['variant']]['shared_source_subset_hash']
    ex.atomic_json(destination/'initialization.json', manifest)
    finish_prepare(case)
    print('PREPARED',case,json.dumps(manifest),flush=True)


def finish_prepare(case):
    """Finish metadata after initialization; refuse an already frozen experiment."""
    setting=CASES[case]
    destination=formal(case)
    if (destination/'provenance.json').exists():raise FileExistsError('Already frozen')
    cfg=read(destination/'config.json')
    manifest=read(destination/'initialization.json')[setting['variant']]
    source=BASE/'taskdec_initial.pt'
    assert manifest['sha256']==ex.sha(destination/manifest['file'])
    assert manifest['copied_from_sha256']==ex.sha(source)
    assert manifest['shared_backbone_head_hash']==manifest['shared_source_subset_hash']
    assert cfg['modalities']==setting['modalities'] and cfg['epochs']==80
    sources = read(BASE/'source_manifest.json')
    sources[str(Path(__file__).resolve().relative_to(ROOT))] = ex.sha(__file__)
    ex.atomic_json(destination/'source_manifest.json', sources)
    inputs = read(BASE/'input_manifest.json')
    for p in [destination/'config.json', destination/'initialization.json',
              destination/'val_deduplicated.txt',destination/'test_deduplicated.txt']:
        inputs[str(p)] = ex.sha(p)
    ex.atomic_json(destination/'input_manifest.json', inputs)
    ex.atomic_json(destination/'provenance.json',dict(created_at=ex.now(),case=case,gpu=setting['gpu'],
        base_config=str(BASE/'config.json'),init_source=str(source),
        architecture='ASF canonical projection + patch attention + PFT; no ObjDec branches' if case=='asf_clr'
                     else 'Complete ObjDec architecture with only LiDAR and Radar encoders, tokens and modality branches',
        alignment='0.16m; 2x2 patches; 4 queries; same ROI, encoders where present, neck/head, train split, augmentations, seed, 80 epochs and effective batch 8',
        scl=False,selection=cfg['selection'],storage='initial + rolling best/last + lightweight metrics/final predictions only',
        gpu_memory_fraction=.60,shared_initial_tensors_exact=True))
    print('FROZEN',case,flush=True)


def run(case, smoke, resume):
    setting=CASES[case]
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == setting['gpu']
    directory=formal(case)
    ex.FORMAL=directory;training.FORMAL=directory
    ex.verify_sources()
    output=directory/('smoke' if smoke else setting['variant'])
    if not smoke:
        assert read(directory/'smoke/status.json')['status']=='smoke_passed'
        assert read(directory/'smoke/geometry_check.json')['passed']
        assert read(directory/'smoke/head_geometry_check.json')['passed']
        assert read(directory/'smoke/modality_check.json')['passed']
    else:
        def checked_model(cfg,variant):
            model=V2XDetector(cfg,variant)
            def input_check(module,args):
                batch=args[0]
                assert ('image' in batch)==('camera' in setting['modalities'])
                assert list(module.encoders)==setting['modalities']
                assert list(module.fuser.key_feats)==setting['modalities']
                ex.atomic_json(output/'modality_check.json',dict(passed=True,modalities=setting['modalities'],
                    camera_in_batch='image' in batch,camera_encoder='camera' in module.encoders,
                    uncluttered_main_path=True,scl=module.fuser.is_scl,at=ex.now()))
                inp.remove()
            inp=model.register_forward_pre_hook(input_check)
            def neck_check(module,args):
                shape=list(args[0]['spatial_features'].shape)
                assert shape==[cfg['batch_size'],128,640,640],shape
                ex.atomic_json(output/'geometry_check.json',dict(passed=True,fused_shape=shape,at=ex.now()))
                neck.remove()
            neck=model.neck.register_forward_pre_hook(neck_check)
            def head_check(module,args):
                shape=list(args[0]['spatial_features_2d'].shape)
                assert shape==[cfg['batch_size'],384,320,320],shape
                ex.atomic_json(output/'head_geometry_check.json',dict(passed=True,shape=shape,at=ex.now()))
                head.remove()
            head=model.head.register_forward_pre_hook(head_check)
            return model
        training.V2XDetector=checked_model
    start=time.monotonic()
    try:
        training.train(SimpleNamespace(variant=setting['variant'],output=str(output),resume=resume,
                                        smoke_steps=100 if smoke else 0))
    finally:
        if output.exists():
            with (output/'attempt_costs.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(case=case,smoke=smoke,gpu=setting['gpu'],pid=os.getpid(),
                    seconds=time.monotonic()-start,at=ex.now()))+'\n')
    if smoke:
        assert read(output/'status.json')['status']=='smoke_passed'
        for name in ['geometry_check','head_geometry_check','modality_check']:
            assert read(output/(name+'.json'))['passed']
        cfg=read(directory/'config.json')
        row=read(output/'status.json')
        epoch=json.loads((output/'epochs.jsonl').read_text().splitlines()[-1])
        assert epoch['samples']==200 and epoch['optimizer_updates']==25
        if case=='asf_clr':assert epoch['aux_loss']==0.
        else:assert epoch['aux_loss']>0.
        receipt={n:dict(bytes=(output/n).stat().st_size,sha256=ex.sha(output/n)) for n in ['best.pt','last.pt']}
        ex.atomic_json(output/'checkpoint_cleanup.json',dict(removed=receipt,
            reason='Only disposable smoke weights; formal training starts from the saved untrained initialization.'))
        for n in receipt:(output/n).unlink()
        print('SMOKE_PASSED',case,'train_seconds',row['train_seconds'],'allocated_gib',row['peak_allocated_gib'],
              'reserved_gib',row['peak_reserved_gib'],flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=['prepare','finish-prepare','smoke','train'])
    ap.add_argument('--case',choices=list(CASES),required=True)
    ap.add_argument('--resume',action='store_true')
    args=ap.parse_args()
    if args.mode=='prepare':prepare(args.case)
    elif args.mode=='finish-prepare':finish_prepare(args.case)
    else:run(args.case,args.mode=='smoke',args.resume)
