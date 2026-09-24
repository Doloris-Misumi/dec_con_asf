"""Cache ObjDec-LR validation predictions while the official weather IDs are missing.

This is preparation, not an official adverse-weather benchmark result.
Existing training source, checkpoints and configurations are read-only inputs.
"""
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMAL = ROOT / 'analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep'
OUT = HERE / 'objdec_lr_val_cache'
sys.path.insert(0, str(ROOT))


def main():
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '2':
        raise RuntimeError('This preparation job is restricted to physical GPU2')
    import numpy as np
    import torch
    from v2x_taskdec import experiment as ex
    from v2x_taskdec.dataset import V2XDataset, collate, to_device
    from v2x_taskdec.model import V2XDetector
    from torch.utils.data import DataLoader

    OUT.mkdir(exist_ok=True)
    with (OUT / '.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUT / 'status.json').exists():
            raise RuntimeError('An attempt is already recorded; inspect it before retrying')
        state = dict(stage='preparing', pid=os.getpid(), gpu=2, started_at=ex.now(),
                     official_weather_result=False, official_subset_available=False)

        def update(stage, **fields):
            state.update(stage=stage, updated_at=ex.now(), **fields)
            ex.atomic_json(OUT / 'status.json', state)
            print(json.dumps(state), flush=True)

        try:
            update('verifying_sources')
            ex.FORMAL = FORMAL
            ex.verify_sources()
            cfg = json.loads((FORMAL / 'config.json').read_text())
            assert cfg['modalities'] == ['lidar', 'radar']
            assert cfg['batch_size'] == 2 and cfg['precision'] == 'fp32'
            ids = (FORMAL / 'val_deduplicated.txt').read_text().split()
            train_ids = set((Path(cfg['split_root']) / 'train.txt').read_text().split())
            assert len(ids) == 1487 and len(set(ids)) == len(ids)
            assert not set(ids) & train_ids

            # Training replaces best.pt atomically. A single open descriptor gives
            # a consistent snapshot even if a later best is saved concurrently.
            snapshot = OUT / 'checkpoint_snapshot.pt'
            with (FORMAL / 'taskdec/best.pt').open('rb') as src, snapshot.open('xb') as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            checkpoint = torch.load(snapshot, map_location='cpu')
            epoch = int(checkpoint['epoch'])
            reference_path = FORMAL / ('taskdec/val_epoch_%03d.json' % epoch)
            reference = json.loads(reference_path.read_text())
            assert abs(reference['selection_metric'] - checkpoint['metric']) < 1e-8
            (OUT / 'val_deduplicated.txt').write_text('\n'.join(ids) + '\n')
            ex.atomic_json(OUT / 'config.json', cfg)
            ex.atomic_json(OUT / 'reference_validation.json', reference)
            ex.atomic_json(OUT / 'provenance.json', dict(
                checkpoint_source=str(FORMAL / 'taskdec/best.pt'), epoch=epoch,
                checkpoint_sha256=ex.sha(snapshot), config_sha256=ex.sha(FORMAL / 'config.json'),
                split_sha256=ex.sha(FORMAL / 'val_deduplicated.txt'), frames=len(ids),
                source_manifest=str(FORMAL / 'source_manifest.json'),
                source_manifest_sha256=ex.sha(FORMAL / 'source_manifest.json'),
                cache_script_sha256=ex.sha(__file__), selected_by='existing full validation best',
                protocol='Existing local ROI, decoder, thresholds and val deduplication unchanged',
                purpose='Preparation for a future explicitly sourced weather subset; not Table 6 reproduction',
                prediction_columns=['x', 'y', 'z', 'dx', 'dy', 'dz', 'yaw', 'score', 'class_id'],
                created_at=ex.now()))

            torch.set_num_threads(4)
            torch.cuda.set_per_process_memory_fraction(.45)
            torch.backends.cudnn.benchmark = False
            ex.seed_all(cfg['seed'])
            model = V2XDetector(cfg, 'taskdec').cuda().eval()
            model.load_state_dict(checkpoint['model'], strict=True)
            del checkpoint
            assert list(model.encoders) == ['lidar', 'radar']
            generator = torch.Generator().manual_seed(cfg['seed'])
            loader = DataLoader(V2XDataset(cfg, 'val', ids=ids, training=False),
                                batch_size=cfg['batch_size'], shuffle=False, num_workers=2,
                                pin_memory=True, collate_fn=collate,
                                worker_init_fn=ex.worker_seed, generator=generator)
            predictions = {}
            started = time.monotonic()
            update('inference', epoch=epoch, frames_done=0, frames_total=len(ids))
            with torch.no_grad():
                for index, batch in enumerate(loader):
                    assert 'image' not in batch
                    device_batch = to_device(batch, 'cuda')
                    if index == 0:
                        reference_outputs = model(device_batch)
                    device_batch.pop('gt_boxes', None)
                    outputs = model(device_batch)
                    if index == 0:
                        for a, b in zip(reference_outputs, outputs):
                            torch.testing.assert_close(a, b, rtol=1e-5, atol=1e-6)
                        ex.atomic_json(OUT / 'input_check.json', dict(
                            passed=True, camera_input=False, camera_encoder=False,
                            prediction_gt_input=False, matches_existing_eval_path=True,
                            frames=batch['frame_ids']))
                        del reference_outputs
                    for frame, pred in zip(batch['frame_ids'], outputs):
                        if pred.ndim != 2 or pred.shape[1] != 9 or not torch.isfinite(pred).all():
                            raise ValueError('Invalid predictions: ' + frame)
                        predictions[frame] = pred.cpu().numpy()
                    if index == 0 or (index + 1) % 50 == 0:
                        update('inference', frames_done=len(predictions),
                               elapsed_seconds=time.monotonic() - started,
                               peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30)
                    del outputs, device_batch
            torch.cuda.synchronize()
            assert list(predictions) == ids
            update('saving_predictions', frames_done=len(predictions))
            temporary = OUT / 'predictions.tmp.npz'
            np.savez_compressed(temporary, **predictions)
            temporary.replace(OUT / 'predictions.npz')
            with np.load(OUT / 'predictions.npz', allow_pickle=False) as saved:
                assert saved.files == ids
                for frame in ids:
                    np.testing.assert_array_equal(saved[frame], predictions[frame])
            update('cache_complete_waiting_official_subset', frames_done=len(ids),
                   inference_seconds=time.monotonic() - started,
                   predictions_bytes=(OUT / 'predictions.npz').stat().st_size,
                   predictions_sha256=ex.sha(OUT / 'predictions.npz'),
                   next_requirement='Official adverse-weather frame IDs and data-version mapping',
                   gpu_work_complete=True)
        except Exception as exc:
            update('failed', error=repr(exc), traceback=traceback.format_exc())
            raise


if __name__ == '__main__':
    main()
