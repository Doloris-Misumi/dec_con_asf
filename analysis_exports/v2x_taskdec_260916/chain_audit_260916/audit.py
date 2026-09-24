"""Read-only checkpoint diagnosis; writes only this isolated audit directory."""
import sys,json,hashlib,gc,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
ROOT=Path('/home/hongsheng/dec_con_asf');sys.path.insert(0,str(ROOT))
from v2x_taskdec.model import V2XDetector,iou3d_nms_utils
from v2x_taskdec.dataset import V2XDataset,collate,to_device
from v2x_taskdec.experiment import verify_sources
from einops import rearrange
OUT=Path(__file__).parent
FORMAL=OUT.parent/'controlled_80ep'

def save(d):
    (OUT/'audit.json').write_text(json.dumps(d,indent=2,allow_nan=False))

def read_ckpt(path):
    with open(path,'rb') as f:
        h=hashlib.sha256()
        for c in iter(lambda:f.read(1048576),b''):h.update(c)
        f.seek(0);d=torch.load(f,map_location='cpu')
    return d,h.hexdigest()

def recall(preds,gt,counts,hits):
    for p,g in zip(preds,gt):
        for ci,thr in enumerate([.7,.5,.5]):
            g1=g[g[:,7]==ci+1,:7].contiguous();counts[ci]+=len(g1)
            p1=p[(p[:,8]==ci+1)&(p[:,7]>=.1),:7].contiguous()
            if len(g1) and len(p1):
                best=iou3d_nms_utils.boxes_iou3d_gpu(g1,p1).max(1)[0]
                hits[ci]+=int((best>=thr).sum())

def spread(t):
    p=rearrange(t.detach(),'b c (y py) (x px) -> (b y x) (py px) c',py=4,px=4)
    return float(((p-p.mean(1,keepdim=True))**2).mean().sqrt()/(p.square().mean().sqrt()+1e-8))

def probe(model,batch):
    model.eval();features={};handles=[]
    for k in model.encoders:
        handles.append(model.encoders[k].register_forward_hook(lambda m,i,o,k=k:features.__setitem__(k,(o[0] if isinstance(o,tuple) else o).detach())))
    with torch.no_grad():model(batch)
    for h in handles:h.remove()
    f=model.fuser;gt=batch['gt_boxes'];state=dict(features,batch_size=len(gt),gt_boxes=gt)
    with torch.no_grad():
        f.eval();ev=f(dict(state))['fused_feat']
        wrong=dict(state);wrong['gt_boxes']=gt.clone();wrong['gt_boxes'][:,:,:2]+=30
        shifted=f(wrong)['fused_feat']
        f.train();tr=f(dict(state));tv=tr['fused_feat']
    result={'fuser_train_eval_max_abs':float((ev-tv).abs().max()),
            'fuser_eval_changed_gt_max_abs':float((ev-shifted).abs().max()),
            'logging':tr.get('patch_dec_logging',{}),
            'within_patch_relative_rms':{k:spread(v) for k,v in features.items()}}
    result['within_patch_relative_rms']['fused']=spread(ev)
    # Independently calculate patch foreground targets in numpy.
    px,py=f._patch_centers_xy(gt.device,gt.dtype)
    fg,cl,_,_=f._gt_patch_targets(state,len(gt)*len(px),gt.device,3)
    xy=np.stack([px.cpu().numpy(),py.cpu().numpy()],-1);expected=[]
    for gs in gt.cpu().numpy():
        mask=np.zeros(len(xy),bool)
        for box in gs[gs[:,7]>0]:
            c,s=np.cos(box[6]),np.sin(box[6]);local=(xy-box[:2])@np.array([[c,-s],[s,c]])
            mask|=(np.abs(local)<=box[3:5]/2+f.patch_dec_fg_margin).all(1)
        expected.extend(mask)
    result['foreground_mask_numpy_equal']=bool(np.array_equal(expected,fg.cpu().numpy()))
    # Detection versus weighted auxiliary gradients at encoder/fusion boundary.
    leaves={k:v.clone().requires_grad_(True) for k,v in features.items()}
    fused=f(dict(leaves,batch_size=len(gt),gt_boxes=gt))
    fused['spatial_features']=fused['fused_feat'];model.neck.eval();model.head.train()
    model.head(model.neck(fused));det,_=model.head.get_loss();aux=fused['patch_dec_loss']*model.cfg['patch_dec_weight']
    gd=torch.autograd.grad(det,list(leaves.values()),retain_graph=True)
    ga=torch.autograd.grad(aux,list(leaves.values()))
    result['gradient_probe']={'det_loss':float(det),'weighted_aux_loss':float(aux),'modalities':{}}
    for k,a,b in zip(leaves,gd,ga):
        result['gradient_probe']['modalities'][k]={'det_norm':float(a.norm()),'aux_norm':float(b.norm()),'aux_over_det':float(b.norm()/(a.norm()+1e-12)),
            'cosine':float((a*b).sum()/(a.norm()*b.norm()+1e-12))}
    model.eval();return result

def main():
    torch.set_num_threads(3);torch.cuda.set_per_process_memory_fraction(.16)
    verify_sources();cfg=json.loads((FORMAL/'config.json').read_text())
    allids=(FORMAL/'val_deduplicated.txt').read_text().split()
    ids=[allids[i] for i in np.linspace(0,len(allids)-1,64,dtype=int)]
    report={'purpose':'diagnostic, not AP or checkpoint selection','frame_ids':ids,'source_hash_check':'passed','runs':{}}
    ds=V2XDataset(cfg,'val',ids=ids);save(report)
    for variant,tag in [('taskdec','best'),('taskdec','last'),('concat','best')]:
        ck,h=read_ckpt(FORMAL/variant/(tag+'.pt'));weights=ck['model'];ep=ck['epoch'];del ck
        model=V2XDetector(cfg,variant).cuda();model.load_state_dict(weights,strict=True)
        rec={'epoch':ep,'checkpoint_sha256':h,'modes':{}};report['runs'][variant+'_'+tag]=rec
        if variant=='taskdec':
            batch=to_device(collate([ds[0],ds[1]]),'cuda')
            rec['probe']=probe(model,batch);del batch;save(report)
        for mode in (['eval','control_off','batch_bn'] if variant=='taskdec' else ['eval','batch_bn']):
            model.load_state_dict(weights,strict=True);model.eval()
            if variant=='taskdec':model.fuser.patch_dec_enabled=(mode!='control_off')
            if mode=='batch_bn':
                for m in model.modules():
                    if isinstance(m,nn.modules.batchnorm._BatchNorm):m.train()
            counts=np.zeros(3,int);hits=np.zeros(3,int);start=time.monotonic()
            with torch.no_grad():
                for i in range(0,len(ids),2):
                    b=to_device(collate([ds[i],ds[i+1]]),'cuda');pred=model(b)
                    recall(pred,b['gt_boxes'],counts,hits)
            rec['modes'][mode]={'gt_counts':counts.tolist(),'hits':hits.tolist(),'recall_score_01_strict':(hits/np.maximum(counts,1)).tolist(),
                'seconds':time.monotonic()-start}
            print(variant,tag,ep,mode,rec['modes'][mode],flush=True);save(report)
        del model,weights,b,pred;gc.collect();torch.cuda.empty_cache()
    report['status']='complete';report['peak_cuda_allocated_gib']=torch.cuda.max_memory_allocated()/2**30;save(report)

if __name__=='__main__':main()
