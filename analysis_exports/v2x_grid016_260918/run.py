"""Isolated 0.16m TaskDec/Concat, using unchanged frozen training/evaluation."""
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
from v2x_taskdec.dataset import to_device
from v2x_taskdec.model import V2XDetector

ORIGINAL = ex.FORMAL
PATCH2 = ORIGINAL.parent / 'taskdec_patch2_80ep'
FORMAL = HERE / 'matched_80ep'
GEOMETRY = {'encoders.camera.voxel_size'}


def read(path):
    return json.loads(Path(path).read_text())


def config(batch):
    cfg = copy.deepcopy(read(PATCH2 / 'config.json'))
    cfg.update(voxel_size=[.16, .16, 8.], batch_size=batch, accumulation=8 // batch,
               effective_batch_size=8, memory_fraction=.75, created_at=ex.now())
    assert cfg['epochs'] == 80 and cfg['resolved_fuser']['UCP']['PATCH_SIZE'] == [2, 2]
    assert cfg['resolved_fuser']['UCP']['N_QUERY'] == 4
    return cfg


def initialized_model(cfg, variant):
    origin = PATCH2 if variant == 'taskdec' else ORIGINAL
    initial = origin / (variant + '_initial.pt')
    assert ex.sha(initial) == read(origin / 'initialization.json')[variant]['sha256']
    ex.seed_all(cfg['seed'])
    model = V2XDetector(cfg, variant)
    saved = torch.load(initial, map_location='cpu')
    fresh = model.state_dict()
    assert set(saved) == set(fresh)
    for key in fresh:
        assert fresh[key].shape == saved[key].shape, key
        if key not in GEOMETRY:
            fresh[key] = saved[key]
    model.load_state_dict(fresh, strict=True)
    assert torch.allclose(model.encoders['camera'].voxel_size.cpu(), torch.tensor([.16, .16, 8.]))
    assert model.encoders['camera'].grid == [640, 640, 1]
    return model, initial


def probe(batch, steps):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '3'
    cfg = config(batch)
    out = HERE / ('probe_batch%d.json' % batch)
    if out.exists():
        raise FileExistsError(out)
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(cfg['memory_fraction'])
    torch.backends.cudnn.benchmark = False
    model, source = initialized_model(cfg, 'taskdec')
    model.cuda().train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg['learning_rate'] * .1,
                                 weight_decay=cfg['weight_decay'])
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    losses = []
    try:
        for step, batch_data in enumerate(training.loader_for(cfg, 'train', training=True, epoch=0)):
            optimizer.zero_grad(set_to_none=True)
            result = model(to_device(batch_data, 'cuda'))
            loss = result['loss']
            assert torch.isfinite(loss)
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg['gradient_clip'])
            assert torch.isfinite(norm)
            optimizer.step()
            losses.append(float(loss.detach()))
            print('PROBE', batch, step + 1, losses[-1], flush=True)
            if step + 1 >= steps:
                break
        torch.cuda.synchronize()
        ex.atomic_json(out, dict(status='passed', batch_size=batch, steps=steps, losses=losses,
            seconds=time.monotonic() - started, peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
            peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30,
            initial=str(source), no_checkpoint_saved=True, at=ex.now()))
    except BaseException as error:
        ex.atomic_json(out, dict(status='failed', batch_size=batch, steps_completed=len(losses),
            error=repr(error), peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30, at=ex.now()))
        raise


def prepare(batch):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '3'
    assert not FORMAL.exists()
    assert read(HERE / ('probe_batch%d.json' % batch))['status'] == 'passed'
    ex.verify_sources()
    cfg = config(batch)
    FORMAL.mkdir()
    ex.atomic_json(FORMAL / 'config.json', cfg)
    for name in ['val_deduplicated.txt', 'test_deduplicated.txt']:
        (FORMAL / name).write_bytes((ORIGINAL / name).read_bytes())
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(cfg['memory_fraction'])
    manifest = {}
    for variant in ['taskdec', 'concat']:
        model, initial = initialized_model(cfg, variant)
        state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
        path = FORMAL / (variant + '_initial.pt')
        ex.save_checkpoint(path, state)
        manifest[variant] = dict(file=path.name, sha256=ex.sha(path),
            parameters=sum(p.numel() for p in model.parameters()),
            shared_backbone_head_hash=ex.state_hash({k: v for k, v in state.items() if not k.startswith('fuser.')}),
            copied_from=str(initial), copied_from_sha256=ex.sha(initial),
            geometry_buffers_recreated=sorted(GEOMETRY), trained_checkpoint_used=False)
        del model, state
    assert len({d['shared_backbone_head_hash'] for d in manifest.values()}) == 1
    ex.atomic_json(FORMAL / 'initialization.json', manifest)
    sources = read(ORIGINAL / 'source_manifest.json')
    sources.update({str(p.relative_to(ROOT)): ex.sha(p) for p in HERE.glob('*.py')})
    ex.atomic_json(FORMAL / 'source_manifest.json', sources)
    inputs = read(ORIGINAL / 'input_manifest.json')
    for p in [FORMAL / 'config.json', FORMAL / 'initialization.json',
              FORMAL / 'val_deduplicated.txt', FORMAL / 'test_deduplicated.txt']:
        inputs[str(p)] = ex.sha(p)
    ex.atomic_json(FORMAL / 'input_manifest.json', inputs)
    ex.atomic_json(FORMAL / 'provenance.json', dict(created_at=ex.now(),
        requested='0.16m grid, 2x2 patch, 80 epochs; TaskDec GPU3 and matched Concat GPU2 after v2 inference.',
        original_config=str(PATCH2 / 'config.json'),
        model_changes={'voxel_size': [[.4,.4,8.],[.16,.16,8.]]},
        training_changes={'batch_size': [2,batch], 'accumulation': [4,8//batch]},
        runtime_changes={'memory_fraction': [.3,.75]},
        geometry='640x640 BEV -> 320x320 detection grid; fresh voxel_size buffer and generated anchors.',
        selection=cfg['selection'], initialization=manifest,
        scope='Exploratory follow-up; final test excluded from parameter/epoch selection.'))
    print('PREPARED', json.dumps(manifest), flush=True)


def bind():
    ex.FORMAL = FORMAL
    training.FORMAL = FORMAL
    ex.verify_sources()


def run(mode, variant, resume):
    bind()
    cfg = read(FORMAL / 'config.json')
    if mode == 'train':
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == ('3' if variant == 'taskdec' else '2')
        for name in ['taskdec', 'concat']:
            assert read(FORMAL / ('smoke_' + name) / 'status.json')['status'] == 'smoke_passed'
        output = FORMAL / variant
    else:
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == '3'
        output = FORMAL / ('smoke_' + variant)
        def checked_model(config, name):
            model = V2XDetector(config, name)
            def geometry_check(module, args):
                state = args[0]
                shape = list(state['spatial_features'].shape)
                assert shape == [config['batch_size'], 128, 640, 640], shape
                assert all(x['feature_map_stride'] == 2 for x in config['head']['ANCHOR_GENERATOR_CONFIG'])
                ex.atomic_json(output / 'geometry_check.json', dict(passed=True, fused_shape=shape,
                    detection_shape=[320,320], voxel_size=[.16,.16,8.], at=ex.now()))
                handle.remove()
            handle = model.neck.register_forward_pre_hook(geometry_check)
            def head_check(module, args):
                shape = list(args[0]['spatial_features_2d'].shape)
                assert shape == [config['batch_size'], 384, 320, 320], shape
                ex.atomic_json(output / 'head_geometry_check.json',
                    dict(passed=True, feature_shape=shape, at=ex.now()))
                head_handle.remove()
            head_handle = model.head.register_forward_pre_hook(head_check)
            return model
        training.V2XDetector = checked_model
    started = time.monotonic()
    try:
        training.train(SimpleNamespace(variant=variant, output=str(output), resume=resume,
                                       smoke_steps=100 if mode == 'smoke' else 0))
    finally:
        if output.exists():
            with (output / 'attempt_costs.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(pid=os.getpid(), gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),
                    mode=mode, seconds=time.monotonic()-started, at=ex.now())) + '\n')
    if mode == 'smoke':
        assert read(output / 'status.json')['status'] == 'smoke_passed'
        assert read(output / 'geometry_check.json')['passed']
        assert read(output / 'head_geometry_check.json')['passed']
        receipt = {n: dict(sha256=ex.sha(output / n), bytes=(output / n).stat().st_size)
                   for n in ['best.pt', 'last.pt']}
        ex.atomic_json(output / 'checkpoint_cleanup.json', dict(removed=receipt,
            reason='Disposable smoke weights; formal training starts again from untrained initial state.'))
        for n in receipt:
            (output / n).unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['probe','prepare','smoke','train'])
    parser.add_argument('--variant', choices=['taskdec','concat'], default='taskdec')
    parser.add_argument('--batch', type=int, choices=[1,2], default=2)
    parser.add_argument('--steps', type=int, default=8)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.mode == 'probe':
        probe(args.batch, args.steps)
    elif args.mode == 'prepare':
        prepare(args.batch)
    else:
        run(args.mode, args.variant, args.resume)
