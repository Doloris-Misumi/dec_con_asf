#!/usr/bin/env python3
"""Isolated batch-one deployment benchmark. Never alters training registrations."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    'taskdec': (
        ROOT / 'logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml',
        ROOT / 'logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt'),
    'asf': (Path('/home/hongsheng/K-Radar-main/configs/v1_0/cfg_A2F_scl_final_local.yml'),
            Path('/home/hongsheng/K-Radar-main/pretrained/v1_0_official/A2F_v1_0_model_10.pt')),
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', choices=SOURCES, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--gpu', default='2')
    ap.add_argument('--warmup', type=int, default=20)
    ap.add_argument('--samples', type=int, default=100)
    ap.add_argument('--profile', action='store_true')
    ap.add_argument('--optimization', default='none')
    ap.add_argument('--verify', action='store_true', help='Time both paths on identical inputs, alternating order; compare outputs outside timing.')
    ap.add_argument('--check-adapters', action='store_true', help='Also compare each captured module with eager execution on its exact captured input.')
    ap.add_argument('--only-index', type=int, help='Repeat one dataset index for numerical diagnosis, not a representative benchmark.')
    args = ap.parse_args()
    args.output = args.output.resolve()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu
    os.chdir(ROOT)
    sys.path[:0] = [str(ROOT), str(ROOT / 'ops')]
    import numpy as np
    import torch
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(0.25)
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0
    cfg, ckpt = SOURCES[args.model]
    # The dataset root now also contains shared sparse-radar directories. Select
    # all numeric sequences explicitly; retain the original test split/filters.
    sequences = sorted([p.name for p in Path('/home/hongsheng/k_radar_dataset').iterdir()
                        if p.name.isdigit() and p.is_dir()], key=int)
    overlay = args.output.with_suffix('.yml')
    overlay.write_text(f'_BASE_CONFIG_: {str(cfg)!r}\n'
                       'GENERAL:\n  LOGGING:\n    IS_LOGGING: False\n'
                       '  RESUME:\n    IS_RESUME: False\n'
                       'VAL:\n  IS_VALIDATE: False\n'
                       f'DATASET:\n  portion: {json.dumps(sequences)}\n'
                       'OPTIMIZER:\n  NUM_WORKERS: 0\n')
    pipe = PipelineDetection_v1_0(path_cfg=str(overlay), mode='test')
    pipe.load_dict_model(str(ckpt), is_strict=True)
    model = pipe.network.eval()
    dataset = pipe.dataset_test
    if args.optimization != 'none':
        from tools.analysis.taskdec_inference_optimizations import install
        optimization_info = install(model, args.optimization)
    else:
        optimization_info = {}
    n = args.warmup + args.samples
    indices = ([args.only_index] * n if args.only_index is not None else
               np.linspace(0, len(dataset) - 1, n, dtype=int).tolist())
    if args.only_index is None:
        assert len(set(indices)) == n
    rows, stage_rows, hooks, verification = [], [], [], []
    stage_start, active_stages = {}, {}
    if args.profile:
        stages = {k: getattr(model, k) for k in ['cam', 'ldr', 'rdr', 'fuser', 'head']}
        stages.update({'cam.backbone': model.cam.backbone, 'cam.neck': model.cam.neck,
                       'cam.depthnet': model.cam.depthnet, 'cam.downsample': model.cam.downsample,
                       'ldr.backbone3d': model.ldr.backbone_3d,
                       'ldr.backbone2d': model.ldr.backbone_2d})
        def pre(name):
            def hook(module, inputs):
                torch.cuda.synchronize()
                stage_start[name] = time.perf_counter()
            return hook
        def post(name):
            def hook(module, inputs, output):
                torch.cuda.synchronize()
                active_stages[name] = (time.perf_counter() - stage_start[name]) * 1000
            return hook
        for name, module in stages.items():
            hooks.extend([module.register_forward_pre_hook(pre(name)), module.register_forward_hook(post(name))])
    result = dict(model=args.model, checkpoint=str(ckpt), checkpoint_sha256=digest(ckpt),
                  config=str(cfg), config_sha256=digest(cfg), script_sha256=digest(__file__),
                  optimization=args.optimization, optimization_info=optimization_info,
                  gpu=args.gpu, gpu_name=torch.cuda.get_device_name(), torch_version=torch.__version__,
                  cuda_version=torch.version.cuda, torch_threads=torch.get_num_threads(),
                  cudnn_benchmark=torch.backends.cudnn.benchmark,
                  cudnn_deterministic=torch.backends.cudnn.deterministic,
                  matmul_tf32=torch.backends.cuda.matmul.allow_tf32,
                  cudnn_tf32=torch.backends.cudnn.allow_tf32,
                  precision='FP32, no autocast; TF32 flags above', batch_size=1,
                  params_m=sum(p.numel() for p in model.parameters()) / 1e6,
                  dataset_size=len(dataset), indices=indices, warmup=args.warmup, measured=args.samples,
                  profile=args.profile, paired_verification=args.verify,
                  only_index=args.only_index, check_adapters=args.check_adapters,
                  optimization_source_sha256=digest(ROOT/'tools/analysis/taskdec_inference_optimizations.py'),
                  timing_scope='network(batch), including camera/H2D/point preprocessing, fusion, head decoding/NMS and (unless explicitly disabled) GT recall diagnostics; excludes synchronous data loading, initialization, optimization preparation and output comparison',
                  source_sha256={str(p.relative_to(ROOT)): digest(p) for p in [
                      ROOT/'models/skeletons/fusion_base_integrated.py',ROOT/'models/fuser/a2_fusion.py',
                      ROOT/'models/fuser/patch_dec_a2_fusion.py',ROOT/'models/head/anchor_head_integrated.py']})
    print('READY', args.model, len(dataset), flush=True)
    start_event, end_event = [torch.cuda.Event(enable_timing=True) for _ in range(2)]
    from tools.analysis.taskdec_inference_optimizations import set_enabled, check_graphs

    def timed(batch, enabled):
        set_enabled(model, enabled)
        active_stages.clear()
        torch.cuda.synchronize()
        t1 = time.perf_counter()
        start_event.record()
        with torch.no_grad():
            output = model(batch)
        end_event.record()
        torch.cuda.synchronize()
        return output, (time.perf_counter()-t1)*1000, start_event.elapsed_time(end_event), dict(active_stages)

    def snapshot(output):
        keys = ['cam_bev_feat', 'spatial_features_2d', 'bev_feat', 'fused_feat',
                'batch_cls_preds', 'batch_box_preds']
        values = {k:output[k].detach().cpu().clone() for k in keys}
        for key, value in output['pred_dicts'][0].items():
            values[key] = value.detach().cpu().clone()
        return values

    def compare(actual, expected):
        check = {}
        for key, value in actual.items():
            other = expected[key]
            same_shape = value.shape == other.shape
            check[key] = dict(shape_equal=same_shape,
                exact=bool(same_shape and torch.equal(value, other)),
                allclose=bool(same_shape and torch.allclose(value, other, rtol=1e-5, atol=1e-5)),
                max_abs=float((value-other).abs().max()) if same_shape and value.numel() else (0. if same_shape else None),
                finite=bool(torch.isfinite(value).all()))
        return check

    for i, idx in enumerate(indices):
        t0 = time.perf_counter()
        batch = dataset.collate_fn([dataset[idx]])
        load_ms = (time.perf_counter() - t0) * 1000
        batch['avail_feats'] = ['cam_bev_feat', 'spatial_features_2d', 'bev_feat']
        raw_batch = copy.deepcopy(batch) if args.verify else None
        order = ['eager', 'optimized'] if i % 2 == 0 else ['optimized', 'eager']
        if args.verify:
            for variant in order:
                if variant == 'optimized':
                    out, wall, cuda_ms, opt_stages = timed(batch, True)
                    actual = snapshot(out)
                else:
                    reference_out, ref_wall, ref_cuda, _ = timed(copy.deepcopy(raw_batch), False)
                    expected = snapshot(reference_out)
                    reference_out = None
        else:
            out, wall, cuda_ms, opt_stages = timed(batch, True)
        if args.verify:
            check = dict(index=idx, tensors=compare(actual, expected))
            if not all(t['exact'] for t in check['tensors'].values()):
                repeat_out, _, _, _ = timed(copy.deepcopy(raw_batch), False)
                repeat = snapshot(repeat_out)
                check['eager_repeat'] = compare(repeat, expected)
                repeat_out = repeat = None
            if args.check_adapters:
                check['adapters'] = check_graphs(model)
            set_enabled(model, True)
            verification.append(check)
            raw_batch = actual = expected = None
        if i >= args.warmup:
            meta = batch['meta'][0]
            rows.append(dict(index=idx, seq=str(meta['seq']), radar_id=str(meta['idx']['rdr']),
                             weather=meta['desc']['climate'], load_ms=load_ms,
                             forward_wall_ms=wall, forward_cuda_ms=cuda_ms,
                             prediction_count=len(out['pred_dicts'][0]['pred_boxes'])))
            if args.verify:
                rows[-1].update(reference_wall_ms=ref_wall, reference_cuda_ms=ref_cuda, execution_order=order)
            stage_rows.append(opt_stages)
        if i == args.warmup - 1:
            torch.cuda.reset_peak_memory_stats()
        if (i+1) % 10 == 0 or i+1 == n:
            print(f'PROGRESS {i+1}/{n} forward={wall:.2f}ms', flush=True)
        # Avoid retaining tensors through the raw point-cloud pointer dictionary.
        for entry in batch.get('pointer', []):
            for key in list(entry):
                if key != 'meta': entry[key] = None
        out = batch = None
    for hook in hooks: hook.remove()
    def stats(values):
        a = np.asarray(values)
        return dict(mean=float(a.mean()), median=float(np.median(a)), p95=float(np.percentile(a,95)),
                    min=float(a.min()), max=float(a.max()), std=float(a.std()))
    result.update(rows=rows, stages=stage_rows,
                  verification=verification,
                  summary={k:stats([r[k] for r in rows]) for k in
                           ['load_ms','forward_wall_ms','forward_cuda_ms'] +
                           (['reference_wall_ms','reference_cuda_ms'] if args.verify else [])},
                  stage_summary={k:stats([r[k] for r in stage_rows]) for k in stage_rows[0]},
                  peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
                  peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30,
                  completed=True)
    write(args.output, result)
    print('RESULT', json.dumps(result['summary']), flush=True)
    print('STAGES', json.dumps(result['stage_summary']), flush=True)
    print('COMPLETED',args.output, flush=True)


if __name__ == '__main__':
    main()
