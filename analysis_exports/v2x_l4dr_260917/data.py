"""V2X geometry/schema shared with TaskDec; native L4DR single-sweep input."""
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from cumm import tensorview as tv
from v2x_taskdec.dataset import V2XDataset
from v2x_taskdec.geometry import read_calibration, augment_world
from v2x_taskdec.experiment import worker_seed


def sample_radar(points, count, rng):
    """Native near/far sampling and repetition, with explicit empty-frame mask."""
    if not len(points):
        return np.zeros((count, 7), np.float32), np.zeros(count, bool)
    if count < len(points):
        far = np.where(np.linalg.norm(points[:, :3], axis=1) >= 40.)[0]
        near = np.where(np.linalg.norm(points[:, :3], axis=1) < 40.)[0]
        if count > len(far):
            choice = np.concatenate([rng.choice(near, count-len(far), replace=False), far])
        else:
            choice = rng.choice(len(points), count, replace=False)
    else:
        choice = np.arange(len(points))
        while len(choice) < count:
            choice = np.concatenate([choice, rng.choice(choice, min(count-len(choice), len(points)), replace=False)])
    rng.shuffle(choice)
    return points[choice], np.ones(count, bool)


class L4DRDataset(V2XDataset):
    def __getitem__(self, idx):
        frame = self.ids[idx]
        cal = read_calibration(self.data / 'calib' / (frame + '.txt'))
        points = [self.read_points(frame, key, cal) for key in ['lidar', 'radar']]
        boxes = self.read_boxes(frame, cal)
        if self.training:
            p = self.cfg['augmentation']
            points, boxes, _ = augment_world(points, boxes,
                np.random.uniform(*p['rotation']), np.random.uniform(*p['scale']),
                np.random.rand() < p['flip_probability'])
        roi = np.asarray(self.cfg['point_cloud_range'], dtype=np.float32)
        boxes = boxes[((boxes[:, :3] >= roi[:3]) & (boxes[:, :3] < roi[3:])).all(1)]
        points = [p[((p[:, :3] >= roi[:3]) & (p[:, :3] < roi[3:])).all(1)] for p in points]
        lidar, radar = points
        # Append genuine single-sweep relative time 0. The first six fields are
        # exactly the audited TaskDec radar fields, not invented Doppler values.
        radar = np.pad(radar, ((0, 0), (0, 1)))
        if self.training:
            np.random.shuffle(lidar)
            np.random.shuffle(radar)
        rng = np.random if self.training else np.random.RandomState((self.cfg['seed'] + int(frame)) % (2**32))
        sampled, valid = sample_radar(radar, self.cfg['l4dr']['radar_sample_points'], rng)
        vox, coords, nums = self.voxelizers['lidar'].point_to_voxel(tv.from_numpy(np.ascontiguousarray(lidar)))
        return dict(frame_id=frame, gt_boxes=boxes,
            lidar=(vox.numpy().copy(), coords.numpy().copy(), nums.numpy().copy()),
            radar_points=sampled, radar_valid=valid, raw_point_counts=[len(lidar), len(radar)])


def collate(batch):
    result = dict(frame_ids=[b['frame_id'] for b in batch])
    boxes = np.zeros((len(batch), max(1, max(len(b['gt_boxes']) for b in batch)), 8), np.float32)
    for i, b in enumerate(batch):
        boxes[i, :len(b['gt_boxes'])] = b['gt_boxes']
    result['gt_boxes'] = torch.from_numpy(boxes)
    vox, coords, nums, points = [], [], [], []
    for i, b in enumerate(batch):
        v, c, n = b['lidar']
        vox.append(v); coords.append(np.pad(c, ((0, 0), (1, 0)), constant_values=i)); nums.append(n)
        points.append(np.pad(b['radar_points'], ((0, 0), (1, 0)), constant_values=i))
    result['lidar'] = tuple(torch.from_numpy(np.concatenate(x)) for x in [vox, coords, nums])
    result['radar_points'] = torch.from_numpy(np.concatenate(points))
    result['radar_valid'] = torch.from_numpy(np.concatenate([b['radar_valid'] for b in batch]))
    result['raw_point_counts'] = torch.tensor([b['raw_point_counts'] for b in batch])
    return result


def loader_for(cfg, split, training=False, ids=None, epoch=0):
    gen = torch.Generator(); gen.manual_seed(cfg['seed'] + epoch)
    return DataLoader(L4DRDataset(cfg, split, training=training, ids=ids),
        batch_size=cfg['batch_size'], shuffle=training, num_workers=cfg['workers'],
        pin_memory=True, drop_last=False, collate_fn=collate,
        worker_init_fn=worker_seed, generator=gen)
