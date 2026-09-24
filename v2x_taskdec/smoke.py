"""Bounded batch-one GPU forward/backward, gradient and inference checks."""
import argparse
import json
import os
from pathlib import Path
import time
import torch
from .dataset import V2XDataset,collate,to_device
from .model import V2XDetector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis_exports/v2x_taskdec_260916'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variant',default='taskdec',choices=['taskdec','patch','concat'])
    args=parser.parse_args()
    cfg=json.loads((OUT/'engineering_config.json').read_text())
    assert json.loads((OUT/'data_preparation_status.json').read_text())['stage']=='complete'
    assert not json.loads((OUT/'point_schema_audit.json').read_text())['errors']
    torch.set_num_threads(4)
    torch.cuda.set_per_process_memory_fraction(.40)
    torch.manual_seed(cfg['seed'])
    torch.cuda.reset_peak_memory_stats()
    # These are train representatives, chosen from geometry audit before model output.
    ids=['000006','009041','009004']
    dataset=V2XDataset(cfg,'train',training=False,ids=ids)
    model=V2XDetector(cfg,args.variant).cuda()
    optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4,weight_decay=.01)
    reports=[]
    for i,frame in enumerate(ids):
        batch=to_device(collate([dataset[i]]),'cuda')
        model.train();optimizer.zero_grad(set_to_none=True)
        start=time.monotonic();output=model(batch);output['loss'].backward()
        gradients={}
        for key in ['encoders.camera','encoders.lidar','encoders.radar','neck','head','fuser']:
            values=[p.grad for n,p in model.named_parameters() if n.startswith(key) and p.grad is not None]
            assert all(torch.isfinite(v).all() for v in values),key
            gradients[key]=sum(float(v.abs().sum()) for v in values)
            if frame!='009004':assert gradients[key]>0,(frame,key)
        norm=torch.nn.utils.clip_grad_norm_(model.parameters(),10.)
        assert torch.isfinite(norm) and torch.isfinite(output['loss'])
        optimizer.step();torch.cuda.synchronize()
        record=dict(frame=frame,loss=float(output['loss'].detach()),detection_loss=float(output['det_loss'].detach()),
                    auxiliary_loss=float(output['aux_loss'].detach()),gradient_l1=gradients,
                    step_seconds=time.monotonic()-start,peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
                    peak_reserved_gib=torch.cuda.max_memory_reserved()/2**30)
        model.eval()
        with torch.no_grad():pred=model(batch)[0]
        assert torch.isfinite(pred).all()
        record['predictions']=len(pred)
        reports.append(record);print(json.dumps(record),flush=True)
    report=dict(status='passed',variant=args.variant,device=os.environ.get('CUDA_VISIBLE_DEVICES'),batch_size=1,cases=reports,
                parameters=sum(p.numel() for p in model.parameters()),note='Three debugging updates only, not a trained result or stable throughput')
    (OUT/('smoke_'+args.variant+'.json')).write_text(json.dumps(report,indent=2))


if __name__=='__main__':main()
