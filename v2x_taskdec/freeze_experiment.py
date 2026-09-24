"""Freeze protocol and matched shared weights before any formal prediction."""
import json
import os
import platform
import subprocess
import sys
import tarfile
import torch
from .experiment import ROOT,OUT,FORMAL,atomic_json,sha,state_hash,seed_all,now
from .model import V2XDetector,fuser_config


def main():
    if FORMAL.exists():raise FileExistsError('Formal directory already exists; inspect, never overwrite')
    for check in ['evaluator_check','evaluator_geometry_check','fuser_contract']:
        assert (OUT/(check+'.json')).exists(),check
    assert json.loads((OUT/'evaluator_check.json').read_text())['status']=='passed'
    assert json.loads((OUT/'evaluator_geometry_check.json').read_text())['status']=='passed'
    cfg=json.loads((OUT/'engineering_config.json').read_text())
    cfg.update(budget_status='locked',epochs=80,batch_size=2,accumulation=4,effective_batch_size=8,
        learning_rate=.001,min_learning_rate=.00001,warmup_epochs=1,weight_decay=.01,
        gradient_clip=10.,optimizer='AdamW',schedule='linear warmup then cosine by optimizer update',
        val_epochs=[1]+list(range(5,81,5)),workers=4,seed=260916,
        selection='maximum deduplicated val strict moderate mean 3D AP_R40; earliest epoch breaks ties',
        initialization='ImageNet ResNet50; all other parameters fresh. Shared tensors copied exactly from one TaskDec initialization; no target-domain warm-start.',
        memory_fraction=.30,created_at=now())
    cfg['resolved_fuser']=dict(fuser_config(cfg))
    FORMAL.mkdir()
    atomic_json(FORMAL/'config.json',cfg)
    for name in ['val_deduplicated','test_deduplicated']:
        (FORMAL/(name+'.txt')).write_bytes((OUT/'evaluation_splits'/(name+'.txt')).read_bytes())
    torch.set_num_threads(4);torch.cuda.set_per_process_memory_fraction(cfg['memory_fraction'])
    seed_all(cfg['seed']);model=V2XDetector(cfg,'taskdec')
    shared={k:v.detach().cpu().clone() for k,v in model.state_dict().items()};del model
    manifest={}
    for variant in ['taskdec','patch','concat']:
        seed_all(cfg['seed']);model=V2XDetector(cfg,variant)
        state=model.state_dict();copied=[]
        for key in state:
            if key in shared and state[key].shape==shared[key].shape:
                state[key]=shared[key];copied.append(key)
        model.load_state_dict(state,strict=True)
        final={k:v.detach().cpu() for k,v in model.state_dict().items()}
        for key in copied:assert torch.equal(final[key],shared[key])
        path=FORMAL/(variant+'_initial.pt');torch.save(final,path)
        manifest[variant]=dict(file=path.name,sha256=sha(path),copied_tensors=len(copied),
            parameters=sum(p.numel() for p in model.parameters()),
            shared_backbone_head_hash=state_hash({k:v for k,v in final.items() if not k.startswith('fuser.')}),
            patch_shared_hash=state_hash({k:v for k,v in final.items() if k.startswith('fuser.') and k in shared}) if variant!='concat' else None)
        if variant=='patch':
            assert manifest[variant]['patch_shared_hash']==state_hash({k:shared[k] for k in final if k.startswith('fuser.')})
        del model
    assert len({v['shared_backbone_head_hash'] for v in manifest.values()})==1
    atomic_json(FORMAL/'initialization.json',manifest)
    source_paths=[]
    for folder,dirs,files in os.walk(ROOT/'v2x_taskdec'):
        dirs[:]=[d for d in dirs if d not in ('.venv','__pycache__')]
        source_paths.extend(__import__('pathlib').Path(folder)/name for name in files if name.endswith('.py'))
    source_paths += [ROOT/'configs/v1_0/cfg_A2F_scl_final.yml',ROOT/'configs/ASF_task_dec_controlled_robust_v1_0.yml']
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path and str(ROOT)+'/' in path:
            path=__import__('pathlib').Path(path)
            if '.venv' not in path.parts and path.is_file():source_paths.append(path)
    source_paths=sorted(set(source_paths))
    atomic_json(FORMAL/'source_manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in source_paths})
    with tarfile.open(FORMAL/'source_snapshot.tar.gz','w:gz') as archive:
        for path in source_paths:archive.add(path,arcname=str(path.relative_to(ROOT)))
    atomic_json(FORMAL/'environment.json',dict(python=platform.python_version(),torch=torch.__version__,
        cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),gpu=torch.cuda.get_device_name(),
        pip_freeze=subprocess.check_output([str(ROOT/'v2x_taskdec/.venv/bin/python'),'-m','pip','freeze'],text=True).splitlines()))
    atomic_json(FORMAL/'input_manifest.json',{str(p):sha(p) for p in [FORMAL/'config.json',
        FORMAL/'val_deduplicated.txt',FORMAL/'test_deduplicated.txt',
        ROOT/'analysis_exports/v2x_taskdec_260916/point_schema_manifest.json',
        ROOT/'analysis_exports/v2x_taskdec_260916/archive_verification.json',
        __import__('pathlib').Path(cfg['image_pretrained']),
        *[__import__('pathlib').Path(cfg['split_root'])/(s+'.txt') for s in ['train','val','test']]]})
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
