"""Author dual-class checkpoint, native inputs, exact Strong test manifest."""
import argparse
import ast
import copy
import datetime
import json
import os
import random
import sys
import time
import types
from collections import Counter
from pathlib import Path

from common import HERE, ROOT, L4DR, STRONG, N, CLASSES, WEATHER, records, sha, save

parser = argparse.ArgumentParser()
parser.add_argument('--smoke', action='store_true')
args = parser.parse_args()
outdir = HERE/('l4dr_smoke' if args.smoke else 'l4dr_full')
outdir.mkdir(exist_ok=True)
(outdir/'preds').mkdir(exist_ok=True)
assert not (outdir/'status.json').exists(), 'Use a new directory; do not overwrite an earlier run'
os.chdir(L4DR)
sys.path[:0] = [str(L4DR/'ops'), str(L4DR)]
import numpy as np
import torch
import yaml
from easydict import EasyDict
from datasets.kradar_detection_v2_0 import KRadarDetection_v2_0
from models.skeletons import build_skeleton
from torch.utils.data import DataLoader

all_records = records()
assert len(all_records) == N
selected = all_records
if args.smoke:
    indices = set()
    for weather in WEATHER:
        candidates = [r for r in all_records if weather in r['groups']]
        indices.add(candidates[0]['index'])
        buses = [r for r in candidates if any(x[0] == CLASSES[1] for x in r['meta']['label'])]
        indices.add((buses or candidates)[-1]['index'])
    selected = [all_records[i] for i in sorted(indices)]

class CachedDataset(KRadarDetection_v2_0):
    def load_dict_item(self, path_data, split):
        assert split == 'test'
        return [{'meta':r['meta']} for r in selected]

    def __getitem__(self, index):
        # The native loader mutates list_dict_item, retaining each full point
        # cloud indefinitely. Keep metadata cached but release sensor arrays.
        original = self.list_dict_item[index]
        self.list_dict_item[index] = {'meta':copy.deepcopy(original['meta'])}
        try:
            return super().__getitem__(index)
        finally:
            self.list_dict_item[index] = original

cfg = EasyDict(yaml.safe_load((HERE/'l4dr_config.yml').read_text()))
seed = cfg.GENERAL.SEED
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
torch.set_num_threads(4)
checkpoint = Path('/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v2.1-model_30.pt')
state = dict(status='building_model',started_at=datetime.datetime.now().astimezone().isoformat(),
    num_samples=0,expected_samples=len(selected),failure_count=0,seed=seed,
    gpu=os.environ.get('CUDA_VISIBLE_DEVICES'),checkpoint=str(checkpoint),checkpoint_sha256=sha(checkpoint),
    config_sha256=sha(HERE/'l4dr_config.yml'),manifest_sha256=sha(HERE/'manifest.jsonl'),
    nms_source_sha256=sha(L4DR/'models/model_utils/model_nms_utils.py'),
    serializer_source_sha256=sha(ROOT/'utils/util_pipeline.py'),confidence=.3)
save(outdir/'status.json',state)
try:
    assert json.loads((HERE/'preflight.json').read_text())['status'] == 'complete'
    assert sha(L4DR/'models/model_utils/model_nms_utils.py') == sha(ROOT/'models/model_utils/model_nms_utils.py')
    ds = CachedDataset(cfg,split='test')
    net = build_skeleton(cfg).cuda().eval()
    weights = torch.load(str(checkpoint),map_location='cpu')
    print('Checkpoint head shapes:',{k:list(v.shape) for k,v in weights.items() if k in
        ['dense_head.conv_cls.weight','dense_head.conv_box.weight','dense_head.conv_dir_cls.weight']},flush=True)
    loaded = net.load_state_dict(weights,strict=True)
    assert not loaded.missing_keys and not loaded.unexpected_keys
    state.update(strict_checkpoint_load=True,checkpoint_keys=len(weights),excluded_keys=[],
        backbone=cfg.MODEL.BACKBONE_2D.NAME,denoise_threshold=cfg.MODEL.PRE_PROCESSING.DENOISE_T,
        postprocessing=dict(cfg.MODEL.POST_PROCESSING))
    del weights
    tree = ast.parse((ROOT/'utils/util_pipeline.py').read_text())
    fn = next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='dict_datum_to_kitti')
    ns = {'np':np}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'original_taskdec_serializer','exec'),ns)
    convert = ns['dict_datum_to_kitti']
    stub = types.SimpleNamespace(val_keyword={CLASSES[0]:'sed',CLASSES[1]:'bus'},
        dict_cls_id_to_name={1:CLASSES[0],2:CLASSES[1]})
    state.update(status='inferencing')
    save(outdir/'status.json',state)
    dl = DataLoader(ds,batch_size=1,shuffle=False,num_workers=4,collate_fn=ds.collate_fn)
    started = time.monotonic()
    counts = Counter()
    with torch.no_grad():
        for j,batch in enumerate(dl):
            r = selected[j]
            out = net(batch)
            pred = out['pred_dicts'][0]
            boxes = pred['pred_boxes'].detach().cpu().numpy()
            scores = pred['pred_scores'].detach().cpu().numpy()
            labels = pred['pred_labels'].detach().cpu().numpy()
            assert np.isfinite(boxes).all() and np.isfinite(scores).all()
            assert set(labels.tolist()).issubset({1,2})
            keep = scores > .3
            bbox = [[s]+list(b) for b,s in zip(boxes[keep],scores[keep])]
            cls = labels[keep].tolist()
            counts.update(cls)
            gt = [(c,CLASSES.index(c)+1,box,track) for c,box,track,av in r['meta']['label']]
            datum = dict(label=[gt],pp_bbox=bbox,pp_cls=cls,pp_num_bbox=len(bbox),pp_desc=r['meta']['desc'])
            converted = convert(stub,datum)
            assert '\n'.join(converted['kitti_gt']) == (STRONG/'all/gts'/f"{r['index']:06d}.txt").read_text().strip()
            (outdir/'preds'/f"{r['index']:06d}.txt").write_text('\n'.join(converted['kitti_pred'])+'\n')
            state.update(num_samples=j+1,prediction_counts=dict(counts),elapsed_seconds=time.monotonic()-started,
                last_index=r['index'],last_frame=r['id'])
            if args.smoke or (j+1)%100 == 0:
                save(outdir/'status.json',state)
                print('PROGRESS',j+1,len(selected),'seconds',round(state['elapsed_seconds'],1),'detections',dict(counts),flush=True)
    save(outdir/'evaluated_indices.json',[r['index'] for r in selected])
    state.update(status='predictions_complete',finished_at=datetime.datetime.now().astimezone().isoformat())
    save(outdir/'status.json',state)
    print('PREDICTIONS COMPLETE',json.dumps(state),flush=True)
    torch.cuda.synchronize()
    sys.stdout.flush()
    sys.stderr.flush()
    # Replace the CUDA process after all output is closed: avoids the native
    # extension invalid-free during Python shutdown seen in prior local L4DR runs.
    if args.smoke:
        os.execv(sys.executable,[sys.executable,'-c','print("SMOKE COMPLETE")'])
    os.execv(sys.executable,[sys.executable,'-u',str(HERE/'evaluate.py'),'--model','l4dr'])
except BaseException as error:
    state.update(status='failed',error=repr(error),failure_count=1)
    save(outdir/'status.json',state)
    raise
