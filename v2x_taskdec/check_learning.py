"""Fixed train-subset overfit and timed real-loader steps before budget lock."""
import argparse,json,os,time
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from .dataset import V2XDataset,collate,to_device
from .model import V2XDetector,iou3d_nms_utils

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis_exports/v2x_taskdec_260916'


def main():
    p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=300);p.add_argument('--batch-size',type=int,default=2)
    p.add_argument('--timing-steps',type=int,default=220);args=p.parse_args()
    cfg=json.loads((OUT/'engineering_config.json').read_text());torch.set_num_threads(4)
    torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);torch.cuda.set_per_process_memory_fraction(.4)
    torch.cuda.reset_peak_memory_stats();model=V2XDetector(cfg,'taskdec').cuda()
    dataset=V2XDataset(cfg,'train',training=False,ids=['000006','000978','006151','009041'])
    batches=[to_device(collate([dataset[j] for j in range(i,min(i+args.batch_size,len(dataset)))]),'cuda')
             for i in range(0,len(dataset),args.batch_size)]
    optim=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.01)
    records=[];started=time.monotonic()
    for step in range(args.steps):
        model.train();optim.zero_grad(set_to_none=True);output=model(batches[step%len(batches)])
        output['loss'].backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),10.)
        assert torch.isfinite(norm) and torch.isfinite(output['loss']),step
        optim.step();records.append(float(output['loss'].detach()))
        if (step+1)%25==0:
            print(json.dumps(dict(stage='overfit',step=step+1,loss=np.mean(records[-25:]),elapsed_s=time.monotonic()-started,
                                  peak_gib=torch.cuda.max_memory_allocated()/2**30)),flush=True)
    model.eval();recalls=[]
    with torch.no_grad():
        for batch in batches:
            predictions=model(batch)
            for pred,gt in zip(predictions,batch['gt_boxes']):
                gt=gt[gt[:,7]>0];score=pred[:,7]>.1;pred=pred[score]
                matches=torch.zeros(len(gt),device='cuda')
                if len(pred):
                    iou=iou3d_nms_utils.boxes_iou3d_gpu(gt[:,:7].contiguous(),pred[:,:7].contiguous())
                    iou*=gt[:,7,None]==pred[None,:,8]
                    matches=iou.max(1).values
                recalls.extend(matches.cpu().tolist())
    report=dict(overfit_initial_mean=float(np.mean(records[:20])),overfit_final_mean=float(np.mean(records[-20:])),
                overfit_recall_iou03=float(np.mean(np.array(recalls)>=.3)),overfit_recall_iou05=float(np.mean(np.array(recalls)>=.5)),
                gt_count=len(recalls),overfit_steps=args.steps,loss_history=records)
    report['overfit_passed']=(report['overfit_final_mean']<report['overfit_initial_mean']*.45 and report['overfit_recall_iou05']>.65)
    (OUT/'learning_check.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='loss_history'}),flush=True)
    if not report['overfit_passed']:raise RuntimeError('Overfit acceptance failed; inspect before formal training')
    # Throughput uses real augmented train input, with no full-feature cache.
    loader=DataLoader(V2XDataset(cfg,'train',training=True),batch_size=args.batch_size,shuffle=True,
                      num_workers=4,collate_fn=collate,pin_memory=True,drop_last=False)
    model.train();times=[];previous=time.monotonic()
    for step,batch in enumerate(loader):
        batch=to_device(batch,'cuda');optim.zero_grad(set_to_none=True);output=model(batch)
        output['loss'].backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),10.)
        assert torch.isfinite(norm);optim.step();torch.cuda.synchronize()
        now=time.monotonic();times.append(now-previous);previous=now
        if (step+1)%50==0:print(json.dumps(dict(stage='timing',steps=step+1,seconds_per_microbatch=float(np.mean(times[20:])))),flush=True)
        if step+1>=args.timing_steps:break
    report['timing']=dict(batch_size=args.batch_size,measured_steps=len(times),warmup_excluded=20,
        stable_steps=len(times[20:]),mean_seconds=float(np.mean(times[20:])),median_seconds=float(np.median(times[20:])),
        p95_seconds=float(np.quantile(times[20:],.95)),loader_batches=len(loader),train_frames=len(loader.dataset),
        peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30,
        note='Engineering overfit weights, all-encoder training FP32; timing includes input loading and update, not validation')
    report['status']='passed';(OUT/'learning_check.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report['timing']),flush=True)


if __name__=='__main__':main()
