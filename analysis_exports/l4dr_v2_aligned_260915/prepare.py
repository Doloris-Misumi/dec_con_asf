"""Build an exact frame/GT manifest and isolated model evaluation configurations."""
import copy
import datetime
import json
import os
import sys
from collections import Counter
from pathlib import Path

from common import HERE, ROOT, L4DR, DATA, STRONG, N, sha, save, box_lines

os.chdir(ROOT)
sys.path.insert(0,str(L4DR))
import yaml
from easydict import EasyDict
from datasets.kradar_detection_v2_0 import KRadarDetection_v2_0


class TestMetadata(KRadarDetection_v2_0):
    def load_dict_item(self, path_data, split):
        assert split == 'test'
        pairs = [line.split(',') for line in (ROOT/'resources/split/test.txt').read_text().splitlines()]
        pairs.sort(key=lambda x:(int(x[0]),x[1]))
        output=[]
        for j,(seq,label) in enumerate(pairs):
            item={'meta':dict(header=str(DATA),seq=seq,split='test',
                label_v1_0=str(DATA/seq/'info_label'/label),
                label_v2_0=str(ROOT/'tools/revise_label/kradar_revised_label_v2_0/KRadar_refined_label_by_UWIPL'/seq/label))}
            item=self.get_label(item)
            if item['meta']['num_obj']>0:
                output.append(item)
            if j%2000==0:
                print('metadata',j,len(pairs),'retained',len(output),flush=True)
        return output


def main():
    cfg=yaml.safe_load((L4DR/'configs/cfg_PP_L4DR.yml').read_text())
    cfg['GENERAL']['NAME']='L4DR_v2_aligned_TaskDec_260915'
    cfg['GENERAL']['LOGGING'].update(IS_LOGGING=False,IS_SAVE_MODEL=False)
    cfg['DATASET']['path_data']['list_dir_kradar']=[str(DATA)]
    cfg['DATASET']['label_version']='v2_0'
    cfg['DATASET']['rdr_sparse']['dir']=str(DATA/'sparse_radar_tensor_wide_range/rtnh_wider_1p_1')
    # Native L4DR postprocessing reads MODEL.POST_PROCESSING, not DENSE_HEAD's copy.
    strong_cfg=yaml.safe_load((ROOT/'configs/ASF_obj_patch_dec_gentle.yml').read_text())
    post=copy.deepcopy(strong_cfg['MODEL']['HEAD']['POST_PROCESSING'])
    assert post['NMS_CONFIG']['NMS_THRESH']==.01 and post['SCORE_THRESH']==.1
    cfg['MODEL']['POST_PROCESSING']=post
    assert cfg['MODEL']['BACKBONE_2D']['NAME']=='BaseBEVBackbone_MGF'
    assert cfg['MODEL']['PRE_PROCESSING']['DENOISE_T']==.1
    (HERE/'l4dr_config.yml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    assert sha(ROOT/'resources/split/test.txt')==sha(L4DR/'resources/split/test.txt')
    ds=TestMetadata(EasyDict(cfg),split='test')
    assert len(ds)==N,(len(ds),N)
    expected_names=[f'{i:06d}.txt' for i in range(N)]
    for sub in ('gts','preds','desc'):
        assert sorted(p.name for p in (STRONG/'all'/sub).glob('*.txt'))==expected_names,sub
    print('Loading Strong archived GT and weather metadata for exact verification',flush=True)
    old_gts=[(STRONG/'all/gts'/name).read_text().strip() for name in expected_names]
    old_desc=[(STRONG/'all/desc'/name).read_text().strip().splitlines() for name in expected_names]
    weather=Counter();classes=Counter();records=[]
    for i,item in enumerate(ds.list_dict_item):
        meta=item['meta']
        actual='\n'.join(box_lines(meta['label']))
        if actual!=old_gts[i]:
            save(HERE/'gt_mismatch.json',dict(index=i,meta=meta,actual=actual,expected=old_gts[i]))
            raise AssertionError('GT mismatch; see gt_mismatch.json')
        ds.get_description(item)
        desc=meta['desc']
        assert [desc[k] for k in ('capture_time','road_type','climate')]==old_desc[i],i
        radar=Path(cfg['DATASET']['rdr_sparse']['dir'])/meta['seq']/f"sprdr_{meta['idx']['rdr']}.npy"
        assert radar.is_file() and not radar.is_symlink(),str(radar)
        assert Path(meta['path']['ldr64']).is_file()
        weather[desc['climate']]+=1
        classes.update(x[0] for x in meta['label'])
        records.append(dict(index=i,id=meta['seq']+','+Path(meta['label_v1_0']).name,meta=meta,
            groups=['all',desc['climate'],desc['capture_time'],desc['road_type']]))
        if i%2000==0:print('GT verified',i,N,flush=True)
    assert classes=={'Sedan':29613,'Bus or Truck':5843},classes
    part=HERE/'manifest.jsonl.tmp'
    with part.open('w') as f:
        for r in records:f.write(json.dumps(r)+'\n')
    part.replace(HERE/'manifest.jsonl')
    save(HERE/'preflight.json',dict(status='complete',time=datetime.datetime.now().astimezone().isoformat(),
        num_samples=N,gt_exact_match=True,all_radar_paths_verified=True,all_lidar_paths_verified=True,
        weather_counts=dict(weather),class_gt_counts=dict(classes),manifest_sha256=sha(HERE/'manifest.jsonl'),
        split_sha256=sha(ROOT/'resources/split/test.txt'),l4dr_config_sha256=sha(HERE/'l4dr_config.yml'),
        revised_evaluator_sha256=sha(ROOT/'utils/kitti_eval/eval_revised.py'),
        protocol=dict(labels='v2_0',roi=[0,-16,-2,72,16,7.6],confidence=.3,
            nms=post['NMS_CONFIG'],score_pre_filter=.1,z_center=.5,ap_samples=41),
        checkpoint_training_protocol='author release v2.1; not claimed identical training protocol',
        strong_prediction_root=str(STRONG/'all/preds')))
    print('PREFLIGHT COMPLETE',N,dict(weather),dict(classes),flush=True)


if __name__=='__main__':
    main()
