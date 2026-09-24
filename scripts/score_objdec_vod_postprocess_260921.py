"""CPU-only cached scoring; official rules, per-frame overlap partitions.

The standard scorer builds cross-frame overlaps and discards the off-diagonal
blocks. num_parts=N avoids those unused pairs; baseline and pair checks verify
the change. No source evaluator is edited.
"""
import datetime
import json
import pickle
import time
import numpy as np
import torch
import diagnose_objdec_vod_postprocess_260921 as d


def main():
    torch.set_num_threads(4)
    d.cfg_from_yaml_file(str(d.CONFIG),d.cfg)
    logger=d.common_utils.create_logger(d.OUT/'scoring.log')
    source=d.Path(d.cfg.DATA_CONFIG.DATA_PATH)/'vod_infos_val.pkl'
    infos=pickle.load(source.open('rb'));gt=[i['annos'] for i in infos]
    expected=[i['point_cloud']['lidar_idx'] for i in infos]
    annos={k:pickle.load((d.OUT/k/'predictions.pkl').open('rb')) for k in d.VARIANTS}
    assert len(infos)==1296
    for a in annos.values():assert [i['frame_id'] for i in a]==expected
    checks={}
    # Check exact diagonal overlap equality against the original batching.
    for metric in [0,1,2]:
        old=d.official.calculate_iou_partly(annos['baseline'][:12],gt[:12],metric,num_parts=1)[0]
        new=d.official.calculate_iou_partly(annos['baseline'][:12],gt[:12],metric,num_parts=12)[0]
        equal=all(np.array_equal(x,y) for x,y in zip(old,new))
        assert equal, f'Overlap partition mismatch for metric {metric}'
        checks[str(metric)]=dict(frames=12,bitwise_identical=True)
    original=d.official.eval_class
    def per_frame(*args,**kw):
        n=len(args[0] if args else kw['gt_annotations'])
        if len(args)>7:
            args=list(args);args[7]=n
        else:kw['num_parts']=n
        return original(*args,**kw)
    d.official.eval_class=per_frame
    start=time.monotonic();summary={};overlaps={}
    state=json.loads((d.OUT/'status.json').read_text())
    state.update(status='scoring_cached',scoring_pid=d.os.getpid(),scoring_device='CPU',
        overlap_partition='one frame per part; official rules unchanged')
    d.dump(d.OUT/'status.json',state)
    for key,settings in d.VARIANTS.items():
        state['variant']=key;d.dump(d.OUT/'status.json',state)
        logger.info('SCORING %s',key);t=time.monotonic()
        ap=d.official.get_official_eval_result(gt,annos[key],d.cfg.CLASS_NAMES)
        ap.update(d.official.get_official_eval_result(gt,annos[key],d.cfg.CLASS_NAMES,custom_method=3))
        if key=='baseline':
            expected_ap=json.loads((d.PREV/'best_metrics.json').read_text())['official']
            assert ap==expected_ap, f'Baseline AP mismatch {ap}'
            checks['baseline_full_ap_bitwise_dict_equal']=True
            slow=d.OUT/'baseline/metrics.json'
            if slow.exists():
                assert ap==json.loads(slow.read_text())['official']
                checks['matches_diagnostic_original_partition']=True
            d.dump(d.OUT/'partition_verification.json',checks)
        counts,overlaps[key]=d.point_counts(gt,annos[key],settings['score'])
        result=dict(settings=settings,official=ap,operating_point=counts,
            detections=sum(len(a['name']) for a in annos[key]),seconds=time.monotonic()-t,
            overlap_partition='one_frame',evaluator_rules_unchanged=True)
        d.dump(d.OUT/key/'metrics.json',result);summary[key]=result
        logger.info('RESULT %s EAA=%s DC=%s seconds=%.1f',key,ap['entire_area']['3d_all'],ap['roi']['3d_all'],result['seconds'])
    coverage=d.recovered_coverage(gt,annos['baseline'],annos['nms010'],overlaps['baseline'],overlaps['nms010'])
    d.dump(d.OUT/'nms_recovered_coverage.json',coverage)
    d.dump(d.OUT/'summary.json',summary)
    state.update(status='complete',scoring_seconds=time.monotonic()-start,
        baseline_ap_reproduced=True,completed_at=datetime.datetime.now().astimezone().isoformat())
    d.dump(d.OUT/'status.json',state)
    logger.info('COMPLETE %s',state)


if __name__=='__main__':
    try:main()
    except BaseException as e:
        d.dump(d.OUT/'scoring_failure.json',dict(error=repr(e)))
        raise
