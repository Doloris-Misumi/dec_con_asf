"""Frozen epoch75 VoD diagnostic. Single forward, three native postprocess settings."""
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import pickle
import sys
import time

ROOT = Path('/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec')
PREV = Path('/home/hongsheng/dec_con_asf/analysis_exports/objdec_vod_patch2_local_260920')
OUT = Path('/home/hongsheng/dec_con_asf/analysis_exports/objdec_vod_postprocess_diagnostic_260921')
CONFIG = ROOT/'tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920.yaml'
CKPT = ROOT/'output/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920/objdec_p2_local_mild_b8a2_fp32_ep80_260920_gpu2/ckpt/best_eaa.pth'
VARIANTS = {'baseline': {'score':0.1,'nms':0.01},
            'score001': {'score':0.01,'nms':0.01},
            'nms010': {'score':0.1,'nms':0.1}}
OUT.mkdir(exist_ok=True, parents=True)
os.chdir(ROOT/'tools')
sys.path[:0] = [str(ROOT/'tools'), str(ROOT)]
import numpy as np
import torch
from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import build_dataloader
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils
from pcdet.datasets.vod_evaluation import kitti_official_evaluate as official
from pcdet.ops.iou3d_nms import iou3d_nms_utils


def dump(path, data):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False,default=float)+'\n')
    tmp.replace(path)


def box_camera(a):
    return np.concatenate([a['location'], a['dimensions'], a['rotation_y'][:,None]],axis=1)


def point_counts(gt, dt, score):
    # Per-frame matrices use exactly the official camera-coordinate 3D IoU.
    overlaps=[official.d3_box_overlap(box_camera(d),box_camera(g)).astype(np.float64) for g,d in zip(gt,dt)]
    result={}
    for region,method in [('EAA',0),('DC',3)]:
        result[region]={}
        for cls,name in enumerate(cfg.CLASS_NAMES):
            gd,dd,ig,idt,dc,_,nvalid=official._prepare_data(gt,dt,cls,0,custom_method=method)
            counts=np.zeros(3,dtype=np.int64)
            for i in range(len(gt)):
                vals=official.compute_statistics_jit(overlaps[i],gd[i],dd[i],ig[i],idt[i],dc[i],2,
                    [0.5,0.25,0.25][cls],thresh=score,compute_fp=True,compute_aos=False)
                counts+=np.asarray(vals[:3],dtype=np.int64)
            tp,fp,fn=map(int,counts)
            result[region][name]=dict(valid_gt=int(nvalid),tp=tp,fp=fp,fn=fn,
                recall=tp/max(nvalid,1),precision=tp/max(tp+fp,1),score_threshold=score)
    return result,overlaps


def recovered_coverage(gt,base,changed,base_iou,changed_iou):
    """Candidate coverage diagnostic, separate from the official one-to-one TP counts."""
    stats={n:dict(newly_covered_gt=0,lost_coverage_gt=0,same_class_suppression_candidates=0,
                  cross_class_suppression_candidates=0,no_higher_score_suppressor=0) for n in cfg.CLASS_NAMES}
    examples=[]
    for i,(g,b,c) in enumerate(zip(gt,base,changed)):
        for cls,name in enumerate(cfg.CLASS_NAMES):
            _,ig,ib,_=official.clean_data(g,b,cls,0)
            _,_,ic,_=official.clean_data(g,c,cls,0)
            valid=np.where(np.asarray(ig)==0)[0]
            bi=np.where(np.asarray(ib)==0)[0];ci=np.where(np.asarray(ic)==0)[0]
            threshold=[0.5,0.25,0.25][cls]
            for j in valid:
                old=(base_iou[i][bi,j]>threshold).any()
                candidates=ci[changed_iou[i][ci,j]>threshold]
                new=len(candidates)>0
                if old and not new:stats[name]['lost_coverage_gt']+=1
                if old or not new:continue
                stats[name]['newly_covered_gt']+=1
                chosen=int(candidates[np.argmax(changed_iou[i][candidates,j])])
                # Strict-NMS baseline survivor with greater score and BEV IoU >.01
                # is evidence of which class suppressed this recovered candidate.
                native_iou=iou3d_nms_utils.boxes_bev_iou_cpu(
                    np.asarray(c['boxes_lidar'][chosen:chosen+1],dtype=np.float32),
                    np.asarray(b['boxes_lidar'],dtype=np.float32)).reshape(-1)
                suppressors=np.where((native_iou>0.01)&(b['score']>=c['score'][chosen]))[0]
                if len(suppressors):
                    sup=int(suppressors[np.argmax(b['score'][suppressors])])
                    other=str(b['name'][sup]);key='same_class_suppression_candidates' if other==name else 'cross_class_suppression_candidates'
                    stats[name][key]+=1
                    entry=dict(frame_id=str(c['frame_id']),gt_index=int(j),class_name=name,
                        score=float(c['score'][chosen]),iou3d=float(changed_iou[i][chosen,j]),
                        suppressor_class=other,suppressor_score=float(b['score'][sup]),
                        suppressor_bev_iou=float(native_iou[sup]))
                    if len([e for e in examples if e['class_name']==name])<20:examples.append(entry)
                else:stats[name]['no_higher_score_suppressor']+=1
    return dict(note='EAA valid GT coverage by any same-class valid prediction at 3D IoU .5/.25/.25; NOT one-to-one recall/AP. Suppressor evidence uses native LiDAR BEV IoU and baseline higher-score survivors.',stats=stats,examples=examples)


def main():
    assert not (OUT/'summary.json').exists(), 'Completed results exist; refuse overwrite'
    torch.set_num_threads(4)
    torch.cuda.set_device(0)
    torch.cuda.set_per_process_memory_fraction(0.5,0)
    common_utils.set_random_seed(666)
    cfg_from_yaml_file(str(CONFIG),cfg)
    logger=common_utils.create_logger(OUT/'diagnostic.log')
    launch=json.loads((PREV/'launch.json').read_text())
    checked={}
    for path,expected in launch['source_sha256'].items():
        if '/pcdet/' in path or '/cfgs/' in path or path.endswith('vod_infos_val.pkl'):
            actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
            assert actual==expected, f'Source/data changed: {path}'
            checked[path]=actual
    state=dict(status='initializing',pid=os.getpid(),gpu=2,started=datetime.datetime.now().astimezone().isoformat())
    dump(OUT/'status.json',state)
    ds,loader,_=build_dataloader(cfg.DATA_CONFIG,cfg.CLASS_NAMES,4,False,
        workers=4,training=False,logger=logger)
    assert len(ds)==1296
    model=build_network(cfg.MODEL,len(cfg.CLASS_NAMES),ds).cuda().eval()
    with CKPT.open('rb') as f:
        ckpt_hash=hashlib.file_digest(f,'sha256').hexdigest() if hasattr(hashlib,'file_digest') else None
        if ckpt_hash is None:
            f.seek(0);h=hashlib.sha256()
            for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
            ckpt_hash=h.hexdigest()
        f.seek(0);saved=torch.load(f,map_location='cpu')
    assert saved['epoch']==75
    model.load_state_dict(saved['model_state'],strict=True)
    del saved
    dump(OUT/'manifest.json',dict(checkpoint=str(CKPT),epoch=75,checkpoint_sha256=ckpt_hash,
        source_sha256=checked,variants=VARIANTS,frames=1296,batch_size=4,precision='FP32',
        gt_used_in_network=False,shared_network_forward=True,evaluator='unchanged native VoD EAA/DC',
        diagnostic_iou=[0.5,0.25,0.25]))
    reference=pickle.load((PREV/'validation/epoch_075/result.pkl').open('rb'))
    expected=[info['point_cloud']['lidar_idx'] for info in ds.vod_infos]
    assert [d['frame_id'] for d in reference]==expected
    annos={k:[] for k in VARIANTS}
    baseline_check=dict(frames=0,name_or_shape_mismatch_frames=0,max_score_difference=0.,max_box_difference=0.)
    started=time.monotonic()
    pp=model.model_cfg.POST_PROCESSING
    for i,batch in enumerate(loader):
        batch.pop('gt_boxes',None)
        load_data_to_gpu(batch)
        with torch.no_grad():
            pp.SCORE_THRESH=.1;pp.NMS_CONFIG.NMS_THRESH=.01
            base_preds,_=model(batch)
            for key,setting in VARIANTS.items():
                if key=='baseline':preds=base_preds
                else:
                    pp.SCORE_THRESH=setting['score'];pp.NMS_CONFIG.NMS_THRESH=setting['nms']
                    preds,_=model.post_processing(batch)
                for pred in preds:
                    assert torch.isfinite(pred['pred_boxes']).all()
                    assert torch.isfinite(pred['pred_scores']).all()
                annos[key].extend(ds.generate_prediction_dicts(batch,preds,cfg.CLASS_NAMES))
            pp.SCORE_THRESH=.1;pp.NMS_CONFIG.NMS_THRESH=.01
        if i%25==0 or i+1==len(loader):
            state.update(status='inference',frames=len(annos['baseline']),seconds=time.monotonic()-started,
                peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30)
            dump(OUT/'status.json',state);logger.info('INFER %d/1296 seconds=%.1f peak=%.2fGiB',state['frames'],state['seconds'],state['peak_allocated_gib'])
        del base_preds,preds,batch
    for b,ref in zip(annos['baseline'],reference):
        baseline_check['frames']+=1
        if not np.array_equal(b['name'],ref['name']):baseline_check['name_or_shape_mismatch_frames']+=1;continue
        if len(b['name']):
            baseline_check['max_score_difference']=max(baseline_check['max_score_difference'],float(np.max(np.abs(b['score']-ref['score']))))
            baseline_check['max_box_difference']=max(baseline_check['max_box_difference'],float(np.max(np.abs(b['boxes_lidar']-ref['boxes_lidar']))))
    dump(OUT/'baseline_prediction_check.json',baseline_check)
    logger.info('BASELINE_CHECK %s',baseline_check)
    for key in VARIANTS:
        assert [d['frame_id'] for d in annos[key]]==expected
        p=OUT/key;p.mkdir(exist_ok=True)
        with (p/'predictions.pkl').open('wb') as f:pickle.dump(annos[key],f,protocol=4)
    # Intermediate feature maps, optimizer, and checkpoint copies are not saved.
    del model,reference
    torch.cuda.empty_cache()
    gt=[copy.deepcopy(info['annos']) for info in ds.vod_infos]
    summary={};overlaps={}
    for key,settings in VARIANTS.items():
        state.update(status='scoring',variant=key);dump(OUT/'status.json',state)
        logger.info('SCORING %s EAA/DC',key);start=time.monotonic()
        ap=official.get_official_eval_result(copy.deepcopy(gt),copy.deepcopy(annos[key]),cfg.CLASS_NAMES)
        ap.update(official.get_official_eval_result(copy.deepcopy(gt),copy.deepcopy(annos[key]),cfg.CLASS_NAMES,custom_method=3))
        if key=='baseline':
            ref_ap=json.loads((PREV/'best_metrics.json').read_text())['official']
            assert ap==ref_ap, f'Baseline AP mismatch: {ap} vs {ref_ap}'
        counts,overlaps[key]=point_counts(gt,annos[key],settings['score'])
        result=dict(settings=settings,official=ap,operating_point=counts,
            detections=sum(len(d['name']) for d in annos[key]),seconds=time.monotonic()-start)
        dump(OUT/key/'metrics.json',result);summary[key]=result
        logger.info('RESULT %s EAA=%s DC=%s seconds=%.1f',key,ap['entire_area']['3d_all'],ap['roi']['3d_all'],result['seconds'])
    coverage=recovered_coverage(gt,annos['baseline'],annos['nms010'],overlaps['baseline'],overlaps['nms010'])
    dump(OUT/'nms_recovered_coverage.json',coverage)
    dump(OUT/'summary.json',summary)
    state.update(status='complete',total_seconds=time.monotonic()-started,baseline_ap_reproduced=True)
    dump(OUT/'status.json',state);logger.info('COMPLETE %s',state)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        dump(OUT/'failure.json',dict(error=repr(exc),time=datetime.datetime.now().astimezone().isoformat()))
        raise
