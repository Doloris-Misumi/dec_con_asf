"""Frozen, budget-matched native L4DR adaptation on V2X-Radar-V."""
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
import yaml
from v2x_taskdec import experiment as ex, train as training
from v2x_taskdec.evaluate import Evaluator
from model import L4DRDetector
from data import loader_for

ORIGINAL = ex.FORMAL
FORMAL = HERE / 'matched_80ep'
NATIVE = ROOT / 'vod_taskdec_native/L4DR_taskdec'


def read(path):
    return json.loads(Path(path).read_text())


def prepare():
    ex.verify_sources()
    if FORMAL.exists():
        raise FileExistsError('Refusing to overwrite ' + str(FORMAL))
    cfg = read(ORIGINAL / 'config.json')
    cfg.pop('resolved_fuser')
    native_path = NATIVE / 'tools/cfgs/VoD_models/L4DR.yaml'
    native = yaml.safe_load(native_path.read_text())['MODEL']
    native['POINT_HEAD']['TARGET_CONFIG']['BOX_CODER_CONFIG']['mean_size'] = [
        c['anchor_sizes'][0] for c in cfg['head']['ANCHOR_GENERATOR_CONFIG']]
    cfg.update(modalities=['lidar', 'radar'], image_pretrained=None,
        voxel_size=[0.16, 0.16, 8.], point_features=dict(lidar=4, radar=7),
        max_voxels=32000, memory_fraction=.40, created_at=ex.now(),
        initialization='Native L4DR all parameters freshly initialized; no pretrained checkpoint.',
        l4dr=dict(native_model=native, native_yaml=str(native_path),
            radar_sample_points=2048, denoise_threshold=.2,
            radar_fields=['ego_x','ego_y','ego_z','normalized_intensity',
                          'normalized_optional_scalar','optional_scalar_available','single_sweep_time_zero'],
            model_path='PointNet2MSG -> point foreground filter -> MME_PillarVFE -> BaseBEVBackbone_MGF -> AnchorHeadSingle',
            comparison_scope='External L+R architecture under matched data/epochs/effective batch; '
                             'not modality-, FLOPs- or initialization-matched to C+L+R.'))
    FORMAL.mkdir()
    ex.atomic_json(FORMAL / 'config.json', cfg)
    for name in ['val_deduplicated.txt', 'test_deduplicated.txt']:
        (FORMAL / name).write_bytes((ORIGINAL / name).read_bytes())
    sources = read(ORIGINAL / 'source_manifest.json')
    paths = list(HERE.glob('*.py')) + [native_path]
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            p = Path(name).resolve()
            if p.is_file() and str(p).startswith(str(ROOT) + '/') and '.venv' not in p.parts:
                paths.append(p)
    for p in set(paths):
        sources[str(p.relative_to(ROOT))] = ex.sha(p)
    # Include every native pointnet2/roiaware binary used by the adaptation.
    for sub in ['pcdet/ops/pointnet2', 'pcdet/ops/roiaware_pool3d']:
        for p in (NATIVE / sub).rglob('*.so'):
            sources[str(p.relative_to(ROOT))] = ex.sha(p)
    ex.atomic_json(FORMAL / 'source_manifest.json', sources)
    inputs = read(ORIGINAL / 'input_manifest.json')
    for p in [FORMAL / 'config.json', FORMAL / 'val_deduplicated.txt', FORMAL / 'test_deduplicated.txt']:
        inputs[str(p)] = ex.sha(p)
    ex.atomic_json(FORMAL / 'input_manifest.json', inputs)
    ex.atomic_json(FORMAL / 'provenance.json', dict(at=ex.now(), original_protocol=str(ORIGINAL),
        native_yaml_sha256=ex.sha(native_path), native_diff=str(HERE / 'native_mme.diff'),
        adaptations=[
            'V2X audited ego coordinates, field normalization, ROI, class merge, train-only anchors.',
            'Native 0.16m XY voxel resolution retained; pillar height adapted to 8m ROI.',
            'Same six radar fields as TaskDec plus constant single-sweep relative time 0.',
            'Native 2048-point sampling; fixed per-frame RNG in evaluation; explicit invalid mask for empty radar.',
            'Native PointNet2, foreground head, MME and MGF parameter widths retained.',
            'Exact coordinate join replaces quadratic equality matrix; equivalent on nonempty inputs.',
            'Empty-safe MME/scatter and one-element radar BN fallback; no dummy detections or dropped frames.',
            'Point-head labels computed only during training; inference never reads GT.',
            'Shared TaskDec decode/NMS and evaluator for identical comparison protocol.',
            'Native point foreground loss plus detection loss; no TaskDec auxiliary loss.',
            '80-epoch AdamW/cosine/effective-batch8 matched schedule, not original VoD onecycle recipe.'
        ], selection=cfg['selection'], source_files=len(sources)))
    print('PREPARED', FORMAL, flush=True)


def bind():
    ex.FORMAL = FORMAL
    training.FORMAL = FORMAL
    training.V2XDetector = L4DRDetector
    training.loader_for = loader_for
    ex.verify_sources()


def initialize():
    bind()
    cfg = read(FORMAL / 'config.json')
    assert not (FORMAL / 'l4dr_initial.pt').exists()
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(cfg['memory_fraction'])
    ex.seed_all(cfg['seed'])
    model = L4DRDetector(cfg)
    state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
    path = FORMAL / 'l4dr_initial.pt'
    ex.save_checkpoint(path, state)
    ex.atomic_json(FORMAL / 'initialization.json', dict(l4dr=dict(file=path.name,
        sha256=ex.sha(path), parameters=sum(p.numel() for p in model.parameters()),
        state_hash=ex.state_hash(state), pretrained=False, seed=cfg['seed'], at=ex.now())))
    print('INITIALIZED', read(FORMAL / 'initialization.json'), flush=True)


def train(mode, resume=False):
    bind()
    run = FORMAL / ('smoke' if mode == 'smoke' else 'l4dr')
    if mode == 'train':
        assert read(FORMAL / 'checks_cpu.json')['passed']
        assert read(FORMAL / 'checks_gpu.json')['passed']
        assert read(FORMAL / 'smoke/status.json')['status'] == 'smoke_passed'
    class ProgressEvaluator(Evaluator):
        def evaluate(self, predictions, ids):
            start = time.monotonic()
            ex.atomic_json(run / 'evaluation_progress.json', dict(status='evaluating',
                frames=len(ids), started_at=ex.now(), pid=os.getpid()))
            print('EVAL_START', ex.now(), 'frames', len(ids), flush=True)
            result = super().evaluate(predictions, ids)
            ex.atomic_json(run / 'evaluation_progress.json', dict(status='finished',
                frames=len(ids), finished_at=ex.now(), seconds=time.monotonic()-start,
                selection_metric=result['selection_metric']))
            print('EVAL_FINISH', ex.now(), 'mean3d', result['selection_metric'], flush=True)
            return result
    training.Evaluator = ProgressEvaluator
    start = time.monotonic()
    try:
        training.train(SimpleNamespace(variant='l4dr', output=str(run), resume=resume,
                       smoke_steps=200 if mode == 'smoke' else 0))
    finally:
        if run.exists():
            state = read(run / 'status.json') if (run / 'status.json').exists() else {}
            with (run / 'attempt_costs.jsonl').open('a') as f:
                f.write(json.dumps(dict(pid=os.getpid(), gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),
                    mode=mode, status=state.get('status'), wall_seconds=time.monotonic()-start,
                    finished_at=ex.now()))+'\n')
    if mode == 'smoke':
        state = read(run / 'status.json')
        assert state['status'] == 'smoke_passed' and state['optimizer_updates'] == 50
        # Kept briefly for GPU equivalence/empty-input/GT-independence checks;
        # the launcher removes only these disposable weights after all pass.


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare','initialize','smoke','train'])
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.mode == 'prepare': prepare()
    else:
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == '1'
        if args.mode == 'initialize': initialize()
        else: train(args.mode, args.resume)
