#!/usr/bin/env python3
"""Isolated GPU2 inference and evaluation of six v1 availability settings.

No training imports are executed until after CUDA_VISIBLE_DEVICES is fixed.
Encoders are shared between sequential cases of the SAME frame, in eval mode.
Predictions/GT are stored once in compressed JSONL; no feature or data copies.
"""
import argparse
import copy
import datetime
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16'
CONFIG = EXP / 'config.yml'
CKPT = EXP / 'models/model_0.pt'
CASES = {'c': 'c', 'l': 'l', 'r': 'r', 'c_star': 'c',
         'c_star_lr': 'clr', 'cl_star_r': 'clr'}
WEATHERS = ['normal', 'overcast', 'fog', 'rain', 'sleet', 'lightsnow', 'heavysnow']
OUT = ROOT / 'analysis_exports/taskdec_v1_availability_completion_260918'
REFERENCE = ROOT / 'logs/exp_260902_203611_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/test_kitti/epoch_0_total/0.3'


def now():
    return datetime.datetime.now().astimezone().isoformat()


def write(path, data):
    tmp = path.with_suffix(path.suffix + '.tmp')
    def encode(value):
        if isinstance(value, Path):
            return str(value)
        if hasattr(value, 'tolist'):
            return value.tolist()
        raise TypeError(type(value).__name__)
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=encode) + '\n')
    tmp.replace(path)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def status(out, **values):
    p = out / 'status.json'
    d = json.loads(p.read_text()) if p.exists() else {}
    d.update(values, updated_at=now(), pid=os.getpid(), gpu=2)
    write(p, d)


def prepare(out):
    import torch
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(0.30)
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0
    seqs = sorted([p.name for p in Path('/home/hongsheng/k_radar_dataset').iterdir()
                   if p.name.isdigit() and p.is_dir()], key=int)
    overlay = out / 'inference_config.yml'
    overlay.write_text(f'_BASE_CONFIG_: {str(CONFIG)!r}\n'
                       'GENERAL:\n  LOGGING:\n    IS_LOGGING: False\n'
                       '  RESUME:\n    IS_RESUME: False\n'
                       'VAL:\n  IS_VALIDATE: True\n'
                       f'DATASET:\n  portion: {json.dumps(seqs)}\n'
                       'OPTIMIZER:\n  NUM_WORKERS: 2\n')
    pipe = PipelineDetection_v1_0(path_cfg=str(overlay), mode='test')
    pipe.load_dict_model(str(CKPT), is_strict=True)
    pipe.network.eval()
    assert len(pipe.dataset_test) == 10065, len(pipe.dataset_test)
    assert pipe.cfg.DATASET.label_version == 'v1_0'
    assert list(pipe.cfg.DATASET.roi.xyz) == [0., -6.4, -2., 72., 6.4, 6.]
    pipe.dict_cls_id_to_name = {1: 'Sedan'}
    write(out / 'resolved_config.json', pipe.cfg)
    return pipe


def black_camera(batch, dataset):
    """Raw RGB=0, represented AFTER the dataset's channel normalization."""
    import torch
    cfg = dataset.cam_process
    mean = [0.485, 0.456, 0.406] if cfg.get('is_use_imgnet_mean_std', False) else cfg.mean
    std = [0.229, 0.224, 0.225] if cfg.get('is_use_imgnet_mean_std', False) else cfg.std
    images = batch['camera_imgs']
    shape = [1] * images.ndim
    shape[-3] = 3
    value = -images.new_tensor(mean).reshape(shape) / images.new_tensor(std).reshape(shape)
    result = dict(batch)
    result['camera_imgs'] = value.expand_as(images).clone()
    assert torch.isfinite(result['camera_imgs']).all()
    return result


def encode_cases(pipe, raw):
    import torch
    model = pipe.network
    batch = model.cam(dict(raw))
    batch = model.ldr(batch)
    # With no active sparse voxels, height-compressed sparse output is zero.
    # Keep the learned dense LiDAR backbone and the LiDAR fusion token active.
    # The installed sparse-convolution backend need not accept empty kernels.
    empty = {'spatial_features': torch.zeros_like(batch['spatial_features'])}
    empty = model.ldr.backbone_2d(empty)
    empty_lidar = empty[model.ldr_key]
    batch = model.rdr(batch)
    black = model.cam(black_camera(raw, pipe.dataset_test))[model.cam_key]
    return batch, black, empty_lidar


def predict_case(pipe, base, black, empty_lidar, case):
    import torch
    model = pipe.network
    batch = dict(base)
    batch['avail_feats'] = pipe.infer_mode_to_avail_feats(CASES.get(case, case))
    if case in ['c_star', 'c_star_lr']:
        batch[model.cam_key] = black
    if case == 'cl_star_r':
        batch[model.ldr_key] = empty_lidar
    output = model.head(model.fuser(batch))
    pred = output['pred_dicts'][0]
    for k in ['pred_boxes', 'pred_scores']:
        assert torch.isfinite(pred[k]).all(), (case, k)
    return output


def kitti_lines(pipe, output):
    from utils.util_pipeline import dict_datum_to_kitti
    pred = output['pred_dicts'][0]
    boxes = pred['pred_boxes'].detach().cpu().numpy()
    scores = pred['pred_scores'].detach().cpu().numpy()
    labels = pred['pred_labels'].detach().cpu().numpy()
    # Preserve numpy.float32 string formatting used by the original evaluator.
    rows = [[s] + list(b) for s, b in zip(scores, boxes) if s > 0]
    ids = [int(k) for s, k in zip(scores, labels) if s > 0]
    small = dict(label=output['label'], pp_bbox=rows, pp_cls=ids,
                 pp_num_bbox=len(rows), pp_desc=output['meta'][0]['desc'])
    result = dict_datum_to_kitti(pipe, small)
    return result['kitti_gt'], result['kitti_pred'], result['kitti_desc']


def anno(lines):
    """In-memory version of the existing KITTI label parser; verified in smoke."""
    import numpy as np
    rows = [x.strip().split(' ') for x in lines]
    return dict(name=np.array([x[0] for x in rows]),
                truncated=np.array([float(x[1]) for x in rows]),
                occluded=np.array([int(x[2]) for x in rows]),
                alpha=np.array([float(x[3]) for x in rows]),
                bbox=np.array([[float(v) for v in x[4:8]] for x in rows]).reshape(-1, 4),
                dimensions=np.array([[float(v) for v in x[8:11]] for x in rows]).reshape(-1, 3)[:, [2, 0, 1]],
                location=np.array([[float(v) for v in x[11:14]] for x in rows]).reshape(-1, 3),
                rotation_y=np.array([float(x[14]) for x in rows]),
                score=np.array([float(x[15]) if len(x) == 16 else 0. for x in rows]))


def evaluate(out, pack, revised, smoke=False):
    from utils.kitti_eval.eval import get_official_eval_result
    from utils.kitti_eval.eval_revised import get_official_eval_result_revised
    evaluator = get_official_eval_result_revised if revised else get_official_eval_result
    with gzip.open(pack, 'rt') as stream:
        records = [json.loads(line) for line in stream]
    assert len(records) == (3 if smoke else 10065)
    gt = [anno(r['gt']) for r in records]
    groups = {'all': list(range(len(records)))}
    if not smoke:
        groups.update({w: [i for i, r in enumerate(records) if r['weather'] == w] for w in WEATHERS})
        assert sum(len(groups[w]) for w in WEATHERS) == len(records)
    results = {}
    for case in CASES:
        results[case] = {}
        for conf in ([0.3] if smoke else [0.3, 0.0]):
            dt = [anno([line for line in r['pred'][case]
                        if line.split(' ')[0] != 'dummy' and float(line.split(' ')[-1]) > conf]) for r in records]
            results[case][str(conf)] = {}
            for weather, ids in groups.items():
                if not ids:
                    continue
                status(out, phase='evaluating', case=case, confidence=conf, condition=weather,
                       frames=len(records), evaluation_group_frames=len(ids))
                print(f'[{now()}] EVAL {case} conf={conf} condition={weather} frames={len(ids)}', flush=True)
                # The original evaluator always makes 50 partitions and cannot
                # handle <50 frames. Repeat ONLY the smoke inputs to exercise
                # its CUDA path; these synthetic smoke APs are not paper results.
                eval_ids = ids * ((50 + len(ids) - 1) // len(ids)) if smoke else ids
                metrics, report = evaluator([gt[i] for i in eval_ids], [dt[i] for i in eval_ids], 0, is_return_with_dict=True)
                clean = dict(frames=len(ids), iou=[float(x) for x in metrics['iou']],
                             BEV=[float(x) for x in metrics['bev']], AP3D=[float(x) for x in metrics['3d']])
                if smoke:
                    clean.update(synthetic_smoke_only=True, repeated_evaluation_frames=len(eval_ids))
                results[case][str(conf)][weather] = clean
                with (out / 'metrics.log').open('a') as stream:
                    stream.write(f'\n{case} conf={conf} condition={weather}\n{report}\n')
                write(out / 'results_partial.json', results)
                print(f'[{now()}] RESULT {case} conf={conf} {weather}: {clean}', flush=True)
    write(out / 'results.json', results)
    scope = ('SYNTHETIC SMOKE CHECK ONLY: three frames repeated to satisfy the original evaluator partition size; not dataset AP results.'
             if smoke else 'Same Robust model_0; all 10,065 test frames; original v1 evaluator.')
    lines = ['# TaskDec v1 six additional availability settings', '',
             scope + ' C* = raw RGB black frame; L* = no LiDAR returns, zero sparse output followed by the original dense LiDAR backbone. Local corruption protocol, not an exact reproduction of undocumented ASF corruption details.', '',
             '| Setting | AP3D@0.3 | AP3D@0.5 | APBEV@0.3 | APBEV@0.5 |',
             '|---|---:|---:|---:|---:|']
    for case in CASES:
        d = results[case]['0.3']['all']
        a = {f'{kind}@{iou:g}': v for kind in ['AP3D', 'BEV'] for iou, v in zip(d['iou'], d[kind])}
        lines.append(f'| {case} | {a["AP3D@0.3"]:.2f} | {a["AP3D@0.5"]:.2f} | {a["BEV@0.3"]:.2f} | {a["BEV@0.5"]:.2f} |')
    (out / 'results.md').write_text('\n'.join(lines) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--evaluate-only', action='store_true')
    args = ap.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = '2'
    os.environ.setdefault('CUDA_HOME', '/usr/local/cuda-11.3')
    os.chdir(ROOT)
    sys.path[:0] = [str(ROOT), str(ROOT / 'ops')]
    out = OUT / 'smoke' if args.smoke else OUT
    out.mkdir(parents=True, exist_ok=True)
    lock = (OUT / 'gpu2.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    pack = out / 'predictions.jsonl.gz'
    if (out / 'results.json').exists():
        raise FileExistsError(out / 'results.json')
    try:
        if args.evaluate_only:
            manifest = json.loads((out / 'manifest.json').read_text())
            evaluate(out, pack, manifest['is_validation_updated'], smoke=args.smoke)
        else:
            if pack.exists():
                raise FileExistsError(pack)
            if not args.smoke:
                assert json.loads((OUT / 'smoke/status.json').read_text())['phase'] == 'complete'
            status(out, phase='initializing', started_at=now(), frames=0, total_frames=10065,
                   cases=list(CASES), failure_count=0)
            pipe = prepare(out)
            import torch
            import numpy as np
            manifest = dict(created_at=now(), checkpoint=str(CKPT), checkpoint_sha256=digest(CKPT),
                            config=str(CONFIG), config_sha256=digest(CONFIG), script_sha256=digest(__file__),
                            source_sha256={str(p.relative_to(ROOT)): digest(p) for p in [
                                ROOT/'models/fuser/patch_dec_a2_fusion.py', ROOT/'models/skeletons/fusion_base_integrated.py',
                                ROOT/'utils/util_pipeline.py', ROOT/'utils/kitti_eval/eval.py', ROOT/'utils/kitti_eval/eval_revised.py']},
                            cases=CASES, dataset_size=len(pipe.dataset_test), gpu=2,
                            gpu_name=torch.cuda.get_device_name(), precision='FP32, no autocast',
                            memory_fraction=0.30, confs=[0.3, 0.0],
                            is_validation_updated=bool(pipe.is_validation_updated),
                            camera_corruption='Raw RGB black frame (0,0,0), with original normalization and calibration; camera branch retained.',
                            lidar_corruption='No LiDAR returns in evaluation ROI: zero height-compressed sparse tensor followed by original learned dense LiDAR backbone; LiDAR fusion token retained. Explicit empty-input convention avoids unsupported empty sparse kernels.',
                            corruption_provenance='Local deterministic input-loss protocol; ASF exact corruption-generation implementation not found in inspected public/local sources.',
                            reuse='Within-frame encoders only; fuser/head recomputed per case, checked against original network in smoke.',
                            storage='Compressed final KITTI prediction/GT strings and frame identities only; no features or raw sensor copies.')
            write(out / 'manifest.json', manifest)
            indices = [0, 5000, 10064] if args.smoke else range(len(pipe.dataset_test))
            audits = []
            start = time.monotonic()
            part = out / 'predictions.partial.jsonl.gz'
            with torch.no_grad(), gzip.open(part, 'wt', compresslevel=3) as stream:
                for step, index in enumerate(indices):
                    raw = pipe.dataset_test.collate_fn([pipe.dataset_test[index]])
                    base, black, empty_lidar = encode_cases(pipe, raw)
                    record = dict(index=index, seq=str(raw['meta'][0]['seq']),
                                  sensor_indices=raw['meta'][0]['idx'], pred={})
                    for case in CASES:
                        output = predict_case(pipe, base, black, empty_lidar, case)
                        gt_lines, pred_lines, desc = kitti_lines(pipe, output)
                        record['gt'] = gt_lines
                        record['description'] = desc
                        record['weather'] = desc.splitlines()[-1]
                        record['pred'][case] = pred_lines
                        if args.smoke and case in ['c', 'l', 'r']:
                            reference_batch = copy.deepcopy(raw)
                            reference_batch['avail_feats'] = pipe.infer_mode_to_avail_feats(case)
                            reference = pipe.network(reference_batch)['pred_dicts'][0]
                            actual = output['pred_dicts'][0]
                            for key in ['pred_boxes', 'pred_scores', 'pred_labels']:
                                assert reference[key].shape == actual[key].shape, (case, key)
                                assert torch.allclose(reference[key], actual[key], atol=1e-5, rtol=1e-5), (case, key)
                            audits.append(dict(index=index, case=case, original_network_equivalent=True))
                            del reference_batch, reference
                        del output
                    # Verify the old evaluation frame ordering and GT conversion.
                    old_gt = (REFERENCE / 'gt' / f'{index:06d}.txt').read_text().splitlines()
                    old_desc = (REFERENCE / 'desc' / f'{index:06d}.txt').read_text().strip()
                    assert record['gt'] == old_gt, ('GT/frame ordering mismatch', index)
                    assert record['description'].strip() == old_desc, ('weather/frame mismatch', index)
                    if args.smoke:
                        from utils.kitti_eval.kitti_common import get_label_anno
                        p = out / 'parser_check.txt'
                        for lines in [record['gt'], record['pred']['c'], []]:
                            p.write_text('\n'.join(lines) + ('\n' if lines else ''))
                            old, new = get_label_anno(p), anno(lines)
                            assert all(np.array_equal(old[k], new[k]) for k in old)
                    stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                    if args.smoke or (step + 1) % 50 == 0:
                        stream.flush()
                        elapsed = time.monotonic() - start
                        rate = (step + 1) / elapsed
                        status(out, phase='inference', frames=step + 1, dataset_index=index,
                               elapsed_seconds=elapsed, frames_per_second=rate,
                               peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30)
                        print(f'[{now()}] INFER {step+1}/{len(indices)} frames, six cases/frame; {rate:.3f} frames/s, peak={torch.cuda.max_memory_allocated()/2**30:.2f} GiB', flush=True)
                    del base, black, empty_lidar, raw, record
            part.replace(pack)
            if args.smoke:
                write(out / 'audit.json', audits)
            # Release model allocations before the unchanged CUDA/Numba evaluator.
            del pipe
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            evaluate(out, pack, manifest['is_validation_updated'], smoke=args.smoke)
        status(out, phase='complete', completed_at=now(), failure_count=0)
        print(f'[{now()}] COMPLETE: {out}', flush=True)
    except BaseException:
        status(out, phase='failed', failure_count=1, traceback=traceback.format_exc())
        raise
    finally:
        sys.stdout.flush()
        sys.stderr.flush()


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    # Some installed native extensions crash in interpreter teardown. All
    # files/context managers above are closed before this explicit clean exit.
    os._exit(0)
