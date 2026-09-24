"""Independent 2x2 TaskDec run, reusing the frozen 80-epoch training pipeline.

Only the experiment artifact directory is rebound. Original sources and runs
are never modified. Preparation copies matching *initial* tensors, not trained
weights. Smoke training is discarded before the formal run starts afresh.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import torch
from v2x_taskdec import experiment, train as training
from v2x_taskdec.model import V2XDetector

ORIGINAL = experiment.FORMAL
DEST = ORIGINAL.parent / 'taskdec_patch2_80ep'


def read(path):
    return json.loads(path.read_text())


def differences(a, b, prefix=''):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(set(a) | set(b)):
            result.extend(differences(a.get(key), b.get(key), prefix + '.' + key if prefix else key))
        return result
    return [] if a == b else [dict(field=prefix, before=a, after=b)]


def prepare():
    experiment.verify_sources()
    if DEST.exists():
        raise FileExistsError('Independent run already exists; refusing to overwrite ' + str(DEST))
    old_cfg = read(ORIGINAL / 'config.json')
    cfg = copy.deepcopy(old_cfg)
    cfg['resolved_fuser']['UCP'].update(PATCH_SIZE=[2, 2], N_QUERY=4)
    changes = differences(old_cfg, cfg)
    assert {x['field'] for x in changes} == {
        'resolved_fuser.UCP.PATCH_SIZE', 'resolved_fuser.UCP.N_QUERY'}
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(cfg['memory_fraction'])
    experiment.seed_all(cfg['seed'])
    model = V2XDetector(cfg, 'taskdec')
    original_initial = ORIGINAL / 'taskdec_initial.pt'
    original_meta = read(ORIGINAL / 'initialization.json')['taskdec']
    assert experiment.sha(original_initial) == original_meta['sha256']
    shared = torch.load(original_initial, map_location='cpu')
    state = model.state_dict()
    assert set(state) == set(shared)
    copied, fresh = [], []
    for key in state:
        if state[key].shape == shared[key].shape:
            state[key] = shared[key]
            copied.append(key)
        else:
            assert key.startswith('fuser.'), key
            fresh.append(dict(name=key, before=list(shared[key].shape), after=list(state[key].shape)))
    model.load_state_dict(state, strict=True)
    final = {k: v.detach().cpu() for k, v in model.state_dict().items()}
    assert all(torch.equal(final[k], shared[k]) for k in copied)
    backbone_hash = experiment.state_hash({k: v for k, v in final.items() if not k.startswith('fuser.')})
    assert backbone_hash == original_meta['shared_backbone_head_hash']
    DEST.mkdir()
    experiment.atomic_json(DEST / 'config.json', cfg)
    for name in ['val_deduplicated.txt', 'test_deduplicated.txt']:
        (DEST / name).write_bytes((ORIGINAL / name).read_bytes())
    initial = DEST / 'taskdec_initial.pt'
    experiment.save_checkpoint(initial, final)
    initialization = dict(file=initial.name, sha256=experiment.sha(initial),
        parameters=sum(p.numel() for p in model.parameters()), copied_tensors=len(copied),
        fresh_shape_changed_tensors=fresh, shared_backbone_head_hash=backbone_hash,
        copied_from=str(original_initial), copied_from_sha256=original_meta['sha256'],
        seed=cfg['seed'], trained_checkpoint_used=False)
    experiment.atomic_json(DEST / 'initialization.json', {'taskdec': initialization})
    source_manifest = read(ORIGINAL / 'source_manifest.json')
    source_manifest[str(Path(__file__).resolve().relative_to(ROOT))] = experiment.sha(__file__)
    experiment.atomic_json(DEST / 'source_manifest.json', source_manifest)
    inputs = read(ORIGINAL / 'input_manifest.json')
    # Keep original protocol inputs verifiable, and additionally freeze new ones.
    for path in [DEST / 'config.json', DEST / 'val_deduplicated.txt',
                 DEST / 'test_deduplicated.txt', DEST / 'initialization.json']:
        inputs[str(path)] = experiment.sha(path)
    experiment.atomic_json(DEST / 'input_manifest.json', inputs)
    experiment.atomic_json(DEST / 'provenance.json', dict(created_at=experiment.now(),
        original_experiment=str(ORIGINAL), actual_config_changes=changes,
        explanation='PATCH_SIZE 4x4 to 2x2; N_QUERY 16 to 4 preserves fused output 128 channels. '
                    'Config created_at is inherited; this provenance records the new creation time.',
        original_source_manifest_sha256=experiment.sha(ORIGINAL / 'source_manifest.json'),
        original_source_snapshot=str(ORIGINAL / 'source_snapshot.tar.gz'),
        original_source_snapshot_sha256=experiment.sha(ORIGINAL / 'source_snapshot.tar.gz'),
        device=torch.cuda.get_device_name(), torch=torch.__version__, cuda=torch.version.cuda,
        initialization=initialization,
        interpretation='Exploratory architecture-granularity follow-up after validation diagnostics; '
                       'compare complete equal-budget runs. Test is not used for selection.'))
    print(json.dumps(dict(status='prepared', directory=str(DEST), changes=changes,
                          initialization=initialization), indent=2), flush=True)


def run(mode, resume=False):
    experiment.FORMAL = DEST
    training.FORMAL = DEST
    experiment.verify_sources()
    output = DEST / ('smoke' if mode == 'smoke' else 'taskdec')
    if mode == 'run':
        assert read(DEST / 'smoke/status.json')['status'] == 'smoke_passed'
        assert read(DEST / 'smoke/fuser_contract.json')['passed']
    else:
        # Observe and assert the actual fuser-to-neck interface once, without
        # changing tensors or training/evaluation logic.
        def smoke_model(cfg, variant):
            model = V2XDetector(cfg, variant)
            def contract(module, args):
                shape = list(args[0]['spatial_features'].shape)
                assert shape == [cfg['batch_size'], 128, 256, 256], shape
                experiment.atomic_json(output / 'fuser_contract.json',
                    dict(passed=True, fused_shape=shape, at=experiment.now()))
                handle.remove()
            handle = model.neck.register_forward_pre_hook(contract)
            return model
        training.V2XDetector = smoke_model
    started = time.monotonic()
    try:
        training.train(SimpleNamespace(variant='taskdec', output=str(output),
                       resume=resume, smoke_steps=100 if mode == 'smoke' else 0))
    finally:
        if output.exists():
            status = read(output / 'status.json') if (output / 'status.json').exists() else {}
            with open(output / 'attempt_costs.jsonl', 'a') as stream:
                stream.write(json.dumps(dict(pid=os.getpid(), gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),
                    mode=mode, status=status.get('status'), wall_seconds=time.monotonic()-started,
                    finished_at=experiment.now())) + '\n')
    if mode == 'smoke':
        status = read(output / 'status.json')
        assert status['status'] == 'smoke_passed' and status['optimizer_updates'] == 25
        # These exact files were just generated by this isolated smoke run.
        # Record verification before removing its disposable ~0.5GB weights.
        checkpoint_receipt = {name: dict(sha256=experiment.sha(output / name),
                                         bytes=(output / name).stat().st_size)
                              for name in ['best.pt', 'last.pt']}
        experiment.atomic_json(output / 'checkpoint_cleanup.json',
            dict(reason='Smoke checkpoint restore passed; formal run starts from initial weights.',
                 verified_and_removed=checkpoint_receipt, at=experiment.now()))
        for name in checkpoint_receipt:
            (output / name).unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'smoke', 'run'])
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '3', 'This experiment is authorized on GPU3 only'
    if args.mode == 'prepare':
        prepare()
    else:
        run(args.mode, args.resume)
