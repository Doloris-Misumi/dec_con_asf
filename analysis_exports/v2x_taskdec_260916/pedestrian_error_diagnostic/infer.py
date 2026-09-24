"""Paired fixed-validation inference; no training changes or checkpoint copies."""
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import torch
from torch.utils.data import DataLoader

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
from v2x_taskdec.dataset import V2XDataset, collate, to_device
from v2x_taskdec.geometry import read_calibration, camera_box_to_lidar
from v2x_taskdec.model import V2XDetector
from v2x_taskdec.experiment import verify_sources, now

FORMAL = OUT.parent / 'controlled_80ep'


def write(name, value):
    path = OUT / name
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False))
    os.replace(tmp, path)


class DiagnosticDataset(V2XDataset):
    def read_points(self, frame, key, calibration):
        points = super().read_points(frame, key, calibration)
        if key == 'lidar':
            self.raw_lidar = points
        return points

    def __getitem__(self, index):
        sample = super().__getitem__(index)
        frame = sample['frame_id']
        cal = read_calibration(self.data/'calib'/(frame+'.txt'))
        roi = np.asarray(self.cfg['point_cloud_range'])
        boxes, attrs = [], []
        for line in (self.data/'label_2'/(frame+'.txt')).read_text().splitlines():
            a = line.split()
            if not a or a[0] != 'Pedestrian':
                continue
            dims = np.asarray(a[8:11], dtype=np.float32)
            if np.any(dims <= 0):
                continue
            box = camera_box_to_lidar(np.asarray(a[11:14], dtype=np.float32), dims, float(a[14]), cal)
            if not ((box[:3] >= roi[:3]).all() and (box[:3] < roi[3:]).all()):
                continue
            moderate = int(a[2]) <= 1 and float(a[1]) <= .3 and float(a[7])-float(a[5]) > 25
            delta = self.raw_lidar[:, :3]-box[:3]
            co, si = np.cos(box[6]), np.sin(box[6])
            inside = ((np.abs(delta[:, 0]*co+delta[:, 1]*si) <= box[3]/2) &
                      (np.abs(-delta[:, 0]*si+delta[:, 1]*co) <= box[4]/2) &
                      (np.abs(delta[:, 2]) <= box[5]/2))
            boxes.append(box.tolist())
            attrs.append(dict(moderate=bool(moderate), lidar_points=int(inside.sum()),
                              distance_m=float(np.linalg.norm(box[:2])),
                              truncation=float(a[1]), occlusion=int(a[2])))
        check = sample['gt_boxes'][sample['gt_boxes'][:, 7] == 2, :7]
        assert np.array_equal(np.asarray(boxes, np.float32).reshape(-1, 7), check)
        if len(boxes):
            xy = np.asarray(boxes)[:, :2]
            dist = np.linalg.norm(xy[:, None]-xy[None, :], axis=-1)
            np.fill_diagonal(dist, np.inf)
            for attr, nearest in zip(attrs, dist.min(1)):
                attr['nearest_pedestrian_m'] = float(nearest) if np.isfinite(nearest) else None
                attr['crowded'] = bool(nearest < 2.)
        sample['diagnostic'] = dict(boxes=boxes, attributes=attrs)
        self.raw_lidar = None
        return sample


def pack(samples):
    batch = collate(samples)
    batch['diagnostic'] = [s['diagnostic'] for s in samples]
    return batch


def main():
    if (OUT/'inference_complete.json').exists():
        raise RuntimeError('Completed output exists; refusing an accidental repeat')
    verify_sources()
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(.12)
    torch.backends.cudnn.benchmark = False
    cfg = json.loads((FORMAL/'config.json').read_text())
    all_ids = (FORMAL/'val_deduplicated.txt').read_text().split()
    ids = [all_ids[i] for i in np.linspace(0, len(all_ids)-1, 512, dtype=int)]
    protocol = dict(created_at=now(), pid=os.getpid(), gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),
        frame_ids=ids, selection='512 evenly spaced deduplicated validation IDs, before inference',
        purpose='Geometry/recall diagnostic, not official AP or model selection',
        checkpoint_policy='Current best snapshots; epochs differ, explicitly recorded',
        config_sha256=hashlib.sha256((FORMAL/'config.json').read_bytes()).hexdigest(),
        memory_fraction=.12, training_sources_verified=True, runs={})
    write('protocol.json', protocol)
    # Open both files before reading: atomic trainer replacement cannot change
    # the inode being hashed/deserialized. Never copy checkpoint data to disk.
    handles = {n:open(FORMAL/n/'best.pt', 'rb') for n in ['taskdec','concat']}
    models = {}
    for name, handle in handles.items():
        digest = hashlib.sha256()
        for chunk in iter(lambda:handle.read(1048576), b''):
            digest.update(chunk)
        handle.seek(0)
        checkpoint = torch.load(handle, map_location='cpu')
        handle.close()
        model = V2XDetector(cfg, name).cuda()
        model.load_state_dict(checkpoint['model'], strict=True)
        model.eval()
        models[name] = model
        protocol['runs'][name] = dict(epoch=checkpoint['epoch'], sha256=digest.hexdigest(),
            source=str(FORMAL/name/'best.pt'), metric=checkpoint.get('metric'))
        del checkpoint
        write('protocol.json', protocol)
        print('Loaded', name, protocol['runs'][name], flush=True)
    predictions = {n:{} for n in models}
    ground_truth = {}
    dataset = DiagnosticDataset(cfg, 'val', ids=ids)
    loader = DataLoader(dataset, batch_size=2, shuffle=False, num_workers=2,
                        collate_fn=pack, pin_memory=True)
    roi = np.asarray(cfg['point_cloud_range'])
    begin = time.monotonic()
    with torch.no_grad():
        for index, batch in enumerate(loader):
            meta = batch.pop('diagnostic')
            frame_ids = batch['frame_ids']
            ground_truth.update(zip(frame_ids, meta))
            batch = to_device(batch, 'cuda')
            for name, model in models.items():
                outputs = model(batch)
                for frame, pred in zip(frame_ids, outputs):
                    assert torch.isfinite(pred).all()
                    arr = pred.detach().cpu().numpy()
                    keep = ((arr[:, 8] == 2) & ((arr[:, :3] >= roi[:3]) &
                            (arr[:, :3] < roi[3:])).all(1) & (arr[:, 3:6] > 0).all(1))
                    predictions[name][frame] = arr[keep].copy()
                del outputs
            del batch
            if (index+1) % 16 == 0:
                status = dict(status='inference', frames=(index+1)*2, total=512,
                    seconds=time.monotonic()-begin, updated_at=now(),
                    allocated_gib=torch.cuda.max_memory_allocated()/2**30,
                    reserved_gib=torch.cuda.max_memory_reserved()/2**30)
                write('status.json', status)
                print(status, flush=True)
    for name, preds in predictions.items():
        np.savez_compressed(OUT/('predictions_'+name+'.npz'), **preds)
    write('ground_truth.json', ground_truth)
    final = dict(status='complete', frames=len(ground_truth), inference_seconds=time.monotonic()-begin,
        finished_at=now(), peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
        peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30,
        gt_pedestrians=sum(len(x['boxes']) for x in ground_truth.values()),
        moderate_pedestrians=sum(a['moderate'] for x in ground_truth.values() for a in x['attributes']))
    del models, model
    gc.collect()
    torch.cuda.empty_cache()
    write('inference_complete.json', final)
    write('status.json', final)
    print(final, flush=True)


if __name__ == '__main__':
    main()
