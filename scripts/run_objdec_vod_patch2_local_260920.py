"""Isolated launch adapter: native training, periodic full VoD validation.

No edits to the shared model/training sources. Smoke updates are discarded.
"""
import copy
import json
import math
import os
from pathlib import Path
import pickle
import random
import sys
import time

ROOT = Path('/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec')
RUN = Path('/home/hongsheng/dec_con_asf/analysis_exports/objdec_vod_patch2_local_260920')
CONFIG = 'cfgs/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920.yaml'
RUN.mkdir(parents=True, exist_ok=True)
os.chdir(ROOT / 'tools')
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT)]
import numpy as np
import torch
from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import build_dataloader
from pcdet.models import build_network, load_data_to_gpu, model_fn_decorator
from pcdet.utils import common_utils
from train_utils.optimization import build_optimizer
from train_utils import train_utils as native

torch.set_num_threads(4)
torch.cuda.set_device(0)
torch.cuda.set_per_process_memory_fraction(0.85, 0)
ACCUMULATION = 2


def write_json(path, data):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=float) + '\n')
    tmp.replace(path)


def smoke(batch_size):
    cfg_from_yaml_file(CONFIG, cfg)
    common_utils.set_random_seed(666)
    logger = common_utils.create_logger(RUN / f'smoke_b{batch_size}.log')
    dataset, loader, _ = build_dataloader(cfg.DATA_CONFIG, cfg.CLASS_NAMES,
        batch_size, False, workers=2, training=True, seed=666, logger=logger)
    assert len(dataset) == 5139
    model = build_network(cfg.MODEL, len(cfg.CLASS_NAMES), dataset).cuda().train()
    opt = build_optimizer(model, cfg.OPTIMIZATION)
    fn = model_fn_decorator()
    losses = []
    start = time.monotonic()
    it = iter(loader)
    for step in range(3):
        opt.zero_grad()
        step_loss = 0.0
        for _ in range(ACCUMULATION):
            batch = next(it)
            loss, tb, _ = fn(model, batch)
            assert torch.isfinite(loss), 'non-finite training loss'
            (loss / ACCUMULATION).backward()
            step_loss += float(loss.detach()) / ACCUMULATION
            del batch, loss
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0)
        assert torch.isfinite(grad_norm), 'non-finite gradients'
        opt.step()
        losses.append(step_loss)
        logger.info('SMOKE step=%d batch=%d loss=%.5f grad_norm=%.5f', step+1, batch_size, losses[-1], grad_norm)
    _, val_loader, _ = build_dataloader(cfg.DATA_CONFIG, cfg.CLASS_NAMES,
        2, False, workers=0, training=False, logger=logger)
    batch = next(iter(val_loader))
    batch.pop('gt_boxes', None)
    load_data_to_gpu(batch)
    model.eval()
    with torch.no_grad():
        preds, _ = model(batch)
    for pred in preds:
        assert torch.isfinite(pred['pred_boxes']).all()
        assert torch.isfinite(pred['pred_scores']).all()
    annos = val_loader.dataset.generate_prediction_dicts(batch, preds, cfg.CLASS_NAMES)
    assert len(annos) == 2
    torch.cuda.synchronize()
    result = dict(batch_size=batch_size, accumulation=ACCUMULATION, losses=losses, no_gt_inference=True,
        prediction_conversion=True, train_frames=len(dataset), val_frames=len(val_loader.dataset),
        peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
        peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30,
        seconds=time.monotonic()-start, parameters=sum(p.numel() for p in model.parameters()))
    write_json(RUN / f'smoke_b{batch_size}.json', result)
    logger.info('SMOKE PASSED %s', result)


def validate(model, epoch, logger, limit=None):
    from pcdet.datasets.vod_evaluation.kitti_official_evaluate import get_official_eval_result
    dataset, loader, _ = build_dataloader(cfg.DATA_CONFIG, cfg.CLASS_NAMES,
        4, False, workers=4, training=False, logger=logger)
    assert len(dataset) == 1296
    result_dir = RUN / 'validation' / f'epoch_{epoch:03d}'
    result_dir.mkdir(parents=True, exist_ok=True)
    model.eval()
    annos = []
    start = time.monotonic()
    for i, batch in enumerate(loader):
        # GT remains only in the dataset for scoring, never fed to the network.
        batch.pop('gt_boxes', None)
        load_data_to_gpu(batch)
        with torch.no_grad():
            preds, _ = model(batch)
        for pred in preds:
            assert torch.isfinite(pred['pred_boxes']).all()
            assert torch.isfinite(pred['pred_scores']).all()
        annos.extend(dataset.generate_prediction_dicts(batch, preds, cfg.CLASS_NAMES))
        if i % 50 == 0 or i+1 == len(loader):
            logger.info('VAL epoch=%d inference=%d/%d', epoch, len(annos), len(dataset))
        del preds, batch
        if limit is not None and len(annos) >= limit:
            break
    expected = [info['point_cloud']['lidar_idx'] for info in dataset.vod_infos[:len(annos)]]
    assert [a['frame_id'] for a in annos] == expected
    assert limit is not None or len(annos) == len(dataset)
    with (result_dir / 'result.pkl').open('wb') as f:
        pickle.dump(annos, f, protocol=4)
    gt = [copy.deepcopy(info['annos']) for info in dataset.vod_infos[:len(annos)]]
    logger.info('VAL epoch=%d scoring official EAA/DC', epoch)
    official = get_official_eval_result(gt, copy.deepcopy(annos), cfg.CLASS_NAMES)
    official.update(get_official_eval_result(gt, copy.deepcopy(annos), cfg.CLASS_NAMES, custom_method=3))
    from pcdet.datasets.vod.kitti_object_eval_python import eval as kitti_eval
    logger.info('VAL epoch=%d scoring KITTI 3D/BEV', epoch)
    kitti_text, kitti_metrics = kitti_eval.get_official_eval_result(gt, copy.deepcopy(annos), cfg.CLASS_NAMES)
    (result_dir / 'kitti.txt').write_text(kitti_text)
    result = dict(epoch=epoch, frames=len(annos), official=official, kitti=kitti_metrics,
        validation_seconds=time.monotonic()-start, gt_used_in_network=False,
        selection_metric='official.entire_area.3d_all')
    write_json(result_dir / 'metrics.json', result)
    logger.info(kitti_text)
    logger.info('VAL_RESULT epoch=%d EAA=%s DC=%s seconds=%.1f', epoch,
        official['entire_area']['3d_all'], official['roi']['3d_all'], result['validation_seconds'])
    return result


def accumulated_epoch(model, optimizer, train_loader, model_func, **kw):
    """FP32 updates with batch8 x2; preserve native optimizer and 80-epoch schedule."""
    model.train()
    iteration = kw['accumulated_iter']
    logger = kw['logger']
    start = time.monotonic()
    total = len(train_loader)
    cumulative_loss = 0.0
    seen = 0
    saved_at = start
    for i, batch in enumerate(train_loader):
        group_start = i // ACCUMULATION * ACCUMULATION
        group_samples = min(ACCUMULATION * train_loader.batch_size,
                            len(train_loader.dataset) - group_start * train_loader.batch_size)
        if i % ACCUMULATION == 0:
            optimizer.zero_grad()
            kw['lr_scheduler'].step(iteration, kw['cur_epoch'])
        samples = batch['batch_size']
        loss, tb, _ = model_func(model, batch)
        if not torch.isfinite(loss):
            raise RuntimeError(f'Nonfinite loss at epoch {kw["cur_epoch"]+1}, batch {i}')
        (loss * (samples / group_samples)).backward()
        value = float(loss.detach())
        cumulative_loss += value * samples
        seen += samples
        del loss, batch
        if (i+1) % ACCUMULATION == 0 or i+1 == total:
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), kw['optim_cfg'].GRAD_NORM_CLIP)
            if not torch.isfinite(norm):
                raise RuntimeError('Nonfinite gradient norm')
            optimizer.step()
            iteration += 1
            if kw['tb_log'] is not None:
                kw['tb_log'].add_scalar('train/loss_microbatch', value, iteration)
                for key, val in tb.items():
                    kw['tb_log'].add_scalar('train/'+key, val, iteration)
            if iteration % 20 == 0 or i < ACCUMULATION or i+1 == total:
                logger.info('Train: %d/%d microbatch=%d/%d update=%d loss=%.4f mean_loss=%.4f lr=%.3e elapsed=%.1fs mem_peak=%.2fGiB',
                    kw['cur_epoch']+1, kw['total_epochs'], i+1, total, iteration, value,
                    cumulative_loss/seen, float(optimizer.lr), time.monotonic()-start,
                    torch.cuda.max_memory_allocated()/2**30)
            if time.monotonic()-saved_at >= kw['ckpt_save_time_interval']:
                native.save_checkpoint(native.checkpoint_state(model, optimizer, kw['cur_epoch'], iteration),
                    filename=kw['ckpt_save_dir']/'latest_model')
                saved_at = time.monotonic()
    return iteration


def train():
    import train as entry
    scheduler_builder = entry.build_scheduler
    def build_accumulated_scheduler(optimizer, total_iters_each_epoch, **kw):
        return scheduler_builder(optimizer, math.ceil(total_iters_each_epoch / ACCUMULATION), **kw)
    entry.build_scheduler = build_accumulated_scheduler
    state = {'best_eaa': -1.0, 'training_seconds': 0.0, 'validation_seconds': 0.0}
    def epoch_with_eval(*args, **kwargs):
        start = time.monotonic()
        iteration = accumulated_epoch(*args, **kwargs)
        state['training_seconds'] += time.monotonic()-start
        epoch = kwargs['cur_epoch'] + 1
        model, optimizer, train_loader = args[:3]
        assert len(train_loader.dataset) == 5139
        logger = kwargs['logger']
        state.update(status='training', completed_epoch=epoch, iteration=iteration,
            peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
            peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30)
        write_json(RUN / 'status.json', state)
        if epoch % 5 == 0 or epoch == kwargs['total_epochs']:
            state['status'] = 'validating'
            write_json(RUN / 'status.json', state)
            # Validation must not alter subsequent training RNG progression.
            rng = (random.getstate(), np.random.get_state(), torch.get_rng_state(), torch.cuda.get_rng_state())
            result = validate(model, epoch, logger)
            random.setstate(rng[0]); np.random.set_state(rng[1])
            torch.set_rng_state(rng[2]); torch.cuda.set_rng_state(rng[3])
            state['validation_seconds'] += result['validation_seconds']
            eaa = float(result['official']['entire_area']['3d_all'])
            if eaa > state['best_eaa']:
                state.update(best_eaa=eaa, best_epoch=epoch, best_dc=float(result['official']['roi']['3d_all']))
                target = kwargs['ckpt_save_dir'] / 'best_eaa.pth'
                tmp = target.with_suffix('.tmp')
                torch.save(native.checkpoint_state(model, optimizer, epoch, iteration), tmp)
                tmp.replace(target)
                write_json(RUN / 'best_metrics.json', result)
                logger.info('BEST_EAA epoch=%d EAA=%.2f DC=%.2f', epoch, eaa, state['best_dc'])
            state['status'] = 'training'
            write_json(RUN / 'status.json', state)
            model.train()
        return iteration
    native.train_one_epoch = epoch_with_eval
    # Full validation is already performed synchronously at epoch 80.
    entry.repeat_eval_ckpt = lambda *a, **kw: None
    try:
        entry.main()
    except BaseException as exc:
        state.update(status='failed', error=repr(exc))
        write_json(RUN / 'status.json', state)
        raise
    state['status'] = 'complete'
    write_json(RUN / 'status.json', state)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-batch':
        smoke(int(sys.argv[2]))
    elif sys.argv[1:] == ['--smoke-eval']:
        cfg_from_yaml_file(CONFIG, cfg)
        common_utils.set_random_seed(666)
        logger = common_utils.create_logger(RUN / 'smoke_eval.log')
        ds, _, _ = build_dataloader(cfg.DATA_CONFIG, cfg.CLASS_NAMES, 2, False,
            workers=0, training=False, logger=logger)
        model = build_network(cfg.MODEL, len(cfg.CLASS_NAMES), ds).cuda()
        validate(model, 0, logger, limit=8)
    else:
        train()
