"""Evaluate a sourced subset from cached predictions, without repeating inference.

Frame IDs must be verified separately against the official dataset version.
The existing local ROI/evaluator is retained; this alone does not align Table 6.
"""
import argparse
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = HERE / 'objdec_lr_val_cache'
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids', required=True, type=Path)
    parser.add_argument('--source-url', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '2':
        raise RuntimeError('Use physical GPU2 when idle for metric computation')
    ids = args.ids.read_text().split()
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('Subset must contain nonempty, unique frame IDs')
    if not args.source_url.startswith(('https://', 'http://')):
        raise ValueError('Record the public source URL of the supplied subset')
    status = json.loads((CACHE / 'status.json').read_text())
    if status['stage'] != 'cache_complete_waiting_official_subset':
        raise RuntimeError('Prediction cache is not complete')
    pool = set((CACHE / 'val_deduplicated.txt').read_text().split())
    missing = set(ids) - pool
    if missing:
        raise ValueError('Subset includes uncached frames; do not silently intersect: ' + str(sorted(missing)))

    import numpy as np
    import torch
    from v2x_taskdec import experiment as ex
    from v2x_taskdec.evaluate import Evaluator
    ex.FORMAL = ROOT / 'analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep'
    ex.verify_sources()
    if ex.sha(CACHE / 'predictions.npz') != status['predictions_sha256']:
        raise ValueError('Prediction cache checksum mismatch')
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(.30)
    cfg = json.loads((CACHE / 'config.json').read_text())
    with np.load(CACHE / 'predictions.npz', allow_pickle=False) as archive:
        predictions = {frame: archive[frame] for frame in ids}
    evaluator = Evaluator(cfg)
    result = evaluator.evaluate(predictions, ids)
    result.update(subset_ids=str(args.ids.resolve()), subset_sha256=ex.sha(args.ids),
                  subset_source_url=args.source_url, checkpoint_epoch=status['epoch'],
                  checkpoint_sha256=ex.sha(CACHE / 'checkpoint_snapshot.pt'),
                  predictions_sha256=status['predictions_sha256'],
                  official_table6_protocol_aligned=False,
                  caveat='Supplied subset, existing local ROI/evaluator; source and version need external verification',
                  evaluated_at=ex.now())
    counts = {key: 0 for key in cfg['class_names']}
    for frame in ids:
        for name in evaluator.ground_truth(frame)['name']:
            counts['Vehicle' if name == 'Car' else str(name)] += 1
    result['gt_counts_within_local_roi'] = counts
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ex.atomic_json(args.output, result)
    print(result['table'])
    print('Saved:', args.output)


if __name__ == '__main__':
    main()
