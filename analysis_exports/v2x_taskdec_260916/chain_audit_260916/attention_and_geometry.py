"""Independent probes of actual attention, geometry IoU, and small-subset AP."""
import sys,json,time,gc
from pathlib import Path
import numpy as np
import torch
ROOT=Path('/home/hongsheng/dec_con_asf');sys.path.insert(0,str(ROOT))
from v2x_taskdec.model import V2XDetector,iou3d_nms_utils
from v2x_taskdec.dataset import V2XDataset,collate,to_device
from v2x_taskdec.evaluate import Evaluator
from v2x_taskdec.evaluation.eval import d3_box_overlap
from v2x_taskdec.geometry import read_calibration,lidar_box_to_camera
from audit import read_ckpt,OUT,FORMAL
from einops import rearrange

def main():
    torch.set_num_threads(3);torch.cuda.set_per_process_memory_fraction(.16)
    cfg=json.loads((FORMAL/'config.json').read_text());ids=json.loads((OUT/'audit.json').read_text())['frame_ids']
    ds=V2XDataset(cfg,'val',ids=ids);evaluator=Evaluator(cfg);report={'ids':ids,'runs':{}}
    for variant,tag in [('taskdec','best'),('taskdec','last'),('concat','best')]:
        ck,sha=read_ckpt(FORMAL/variant/(tag+'.pt'));m=V2XDetector(cfg,variant).cuda();m.load_state_dict(ck['model']);ep=ck['epoch'];del ck;m.eval()
        rec={'epoch':ep,'sha256':sha,'batches':[]};report['runs'][variant+'_'+tag]=rec
        held={};handles=[]
        if variant=='taskdec':
            orig=m.fuser._dec_control_scores
            def score(*args,**kwargs):
                out=orig(*args,**kwargs);held['prob']=out[4];held['scale']=out[5];return out
            m.fuser._dec_control_scores=score
            handles.append(m.fuser.fuser.register_forward_hook(lambda mod,inp,out:held.__setitem__('attention',out[1])))
        handles.append(m.fuser.register_forward_hook(lambda mod,inp,out:held.__setitem__('fused',out['fused_feat'] if isinstance(out,dict) else out)))
        predictions={};geometry=[];counts=[]
        with torch.no_grad():
            for i in range(0,len(ids),2):
                batch=to_device(collate([ds[i],ds[i+1]]),'cuda');pred=m(batch)
                br={'frames':ids[i:i+2]}
                if variant=='taskdec':
                    fg,_,_,_=m.fuser._gt_patch_targets(batch,len(batch['gt_boxes'])*4096,'cuda',3)
                    a=held['attention'];p=held['prob'];s=held['scale']
                    br.update(controller_mean=p.mean(0).tolist(),controller_fg=p[fg].mean(0).tolist(),
                        attention_mean=a.mean((0,1)).tolist(),attention_fg=a[fg].mean((0,1)).tolist(),
                        fg_fraction=float(fg.float().mean()),scale_fg=s[fg].mean(0).tolist(),
                        attention_fg_query_variation=float(a[fg].std(dim=1).mean()))
                f=rearrange(held['fused'],'b c (y py) (x px) -> (b y x) (py px) c',py=4,px=4)
                per=(f-f.mean(1,keepdim=True)).square().mean((1,2)).sqrt()/(f.square().mean((1,2)).sqrt()+1e-8)
                br['patch_variation_median']=float(per.median())
                if variant=='taskdec':br['fg_patch_variation_median']=float(per[fg].median())
                rec['batches'].append(br)
                for frame,p,gt in zip(batch['frame_ids'],pred,batch['gt_boxes']):
                    predictions[frame]=p.cpu().numpy();g=gt[gt[:,7]>0,:7].contiguous();p=p[p[:,7]>=.1]
                    counts.append({'frame':frame,'gt':len(g),'pred_above_01':len(p),'pred_above_05':int((p[:,7]>=.5).sum())})
                    if i<8 and len(g) and len(p):
                        cal=read_calibration(ds.data/'calib'/(frame+'.txt'))
                        def cam(boxes):
                            out=[]
                            for box in boxes:
                                loc,hwl,ry=lidar_box_to_camera(box,cal);out.append(np.r_[loc,hwl[[2,0,1]],ry])
                            return np.asarray(out)
                        direct=iou3d_nms_utils.boxes_iou3d_gpu(g,p[:,:7].contiguous()).cpu().numpy()
                        camera=d3_box_overlap(cam(g.cpu().numpy()),cam(p[:,:7].cpu().numpy()))
                        geometry.append({'frame':frame,'pairs':direct.size,'max_absolute_iou_error':float(np.abs(direct-camera).max()),
                            'mean_absolute_iou_error':float(np.abs(direct-camera).mean())})
        rec['geometry']=geometry;rec['detection_counts']=counts
        start=time.monotonic();rec['subset_evaluation']=evaluator.evaluate(predictions,ids);rec['evaluation_seconds']=time.monotonic()-start
        print(variant,tag,ep,rec['subset_evaluation']['selection_metric'],'IoU diff',max(x['max_absolute_iou_error'] for x in geometry),flush=True)
        (OUT/'attention_and_geometry.json').write_text(json.dumps(report,indent=2,allow_nan=False))
        for h in handles:h.remove()
        del m,pred,batch,held,f,p,g;gc.collect();torch.cuda.empty_cache()
    report['status']='complete';(OUT/'attention_and_geometry.json').write_text(json.dumps(report,indent=2,allow_nan=False))

if __name__=='__main__':main()
