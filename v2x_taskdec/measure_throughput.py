"""Measure real augmented training loader after validated learning, no checkpoints."""
import argparse,json,time,os
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from .dataset import V2XDataset,collate,to_device
from .model import V2XDetector

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'analysis_exports/v2x_taskdec_260916'


def main():
    p=argparse.ArgumentParser();p.add_argument('--variant',default='taskdec');p.add_argument('--batch-size',type=int,default=2)
    p.add_argument('--steps',type=int,default=220);a=p.parse_args()
    assert json.loads((OUT/'learning_check.json').read_text())['overfit_passed']
    cfg=json.loads((OUT/'engineering_config.json').read_text());torch.set_num_threads(4)
    torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);torch.cuda.set_per_process_memory_fraction(.4)
    torch.cuda.reset_peak_memory_stats();model=V2XDetector(cfg,a.variant).cuda().train()
    optim=torch.optim.AdamW(model.parameters(),lr=1e-4,weight_decay=.01)
    loader=DataLoader(V2XDataset(cfg,'train',training=True),batch_size=a.batch_size,shuffle=True,num_workers=4,
                      collate_fn=collate,pin_memory=True,drop_last=False)
    times=[];previous=time.monotonic()
    for step,batch in enumerate(loader):
        batch=to_device(batch,'cuda');optim.zero_grad(set_to_none=True);output=model(batch)
        output['loss'].backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),10.)
        assert torch.isfinite(norm) and torch.isfinite(output['loss']),(step,float(output['loss']))
        optim.step();torch.cuda.synchronize();now=time.monotonic();times.append(now-previous);previous=now
        if (step+1)%50==0:print(json.dumps(dict(step=step+1,mean_seconds=float(np.mean(times[20:])),loss=float(output['loss'].detach()))),flush=True)
        if step+1>=a.steps:break
    report=dict(status='passed',variant=a.variant,batch_size=a.batch_size,measured_steps=len(times),warmup_excluded=20,
        stable_steps=len(times[20:]),mean_seconds=float(np.mean(times[20:])),median_seconds=float(np.median(times[20:])),
        p95_seconds=float(np.quantile(times[20:],.95)),loader_batches=len(loader),train_frames=len(loader.dataset),
        peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30,
        device=os.environ.get('CUDA_VISIBLE_DEVICES'),parameters=sum(p.numel() for p in model.parameters()),
        note='Fresh initialization, augmented real loader, all-encoder FP32 training; includes I/O and optimizer updates, no validation')
    (OUT/('throughput_'+a.variant+'.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)


if __name__=='__main__':main()
