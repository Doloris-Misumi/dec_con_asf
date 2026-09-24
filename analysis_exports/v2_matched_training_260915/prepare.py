"""Freeze full configs, verify train/test GT with both native label parsers."""
import copy
import importlib.util
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from common import HERE, ROOT, L4DR, DATA, REFERENCE, STRONG, SEED, EPOCHS, BATCH, sha, save

os.chdir(ROOT);sys.path.insert(0,str(ROOT))
import yaml
from easydict import EasyDict
from utils.util_config import cfg_from_yaml_file
from datasets.kradar_fusion_v1_0 import KRadarFusion_v1_0
spec=importlib.util.spec_from_file_location('matched_l4dr_dataset',L4DR/'datasets/kradar_detection_v2_0.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def plain(x):
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items() if k!='_BASE_CONFIG_'}
    if isinstance(x,(tuple,list)):return [plain(v) for v in x]
    return x

strong=plain(cfg_from_yaml_file(str(STRONG/'config.yml'),EasyDict()))
assert strong['OPTIMIZER']['MAX_EPOCH']==EPOCHS and strong['OPTIMIZER']['BATCH_SIZE']==BATCH
assert strong['MODEL']['FREEZE'] and not strong['MODEL']['FREEZE_BN']
assert not strong['MODEL'].get('LOADED') and not strong['GENERAL']['RESUME']['IS_RESUME']
asf=copy.deepcopy(strong)
asf['GENERAL']['NAME']='ASF_v2_local_matched_Strong_260915'
asf['MODEL']['FUSER']['NAME']='A2Fusion'
for key in list(asf['MODEL']['FUSER']):
    if key.startswith(('PATCH_DEC','DEC_CONTROL')):asf['MODEL']['FUSER'].pop(key)
asf['MODEL']['LOSS'].pop('PATCH_DEC_WEIGHT',None)
asf['GENERAL']['LOGGING'].update(IS_LOGGING=True,IS_SAVE_MODEL=False)
asf['GENERAL']['RESUME']['IS_RESUME']=False
asf['VAL']['IS_VALIDATE']=False
asf['OPTIMIZER']['NUM_WORKERS']=4
asf['DATASET']['portion']=[str(i) for i in range(1,59)]
encoders={}
for kind in ['CAMERA','LIDAR','RADAR']:
    original=copy.deepcopy(asf['MODEL'][kind]);encoders[kind]=original
    sub=yaml.safe_load((ROOT/original['CFG']).read_text())
    if kind=='CAMERA':sub['MODEL']['BACKBONE']['PRETRAINED']=False
    path=HERE/(kind.lower()+'_config.yml')
    path.write_text(yaml.safe_dump(sub,sort_keys=False))
    asf['MODEL'][kind]['CFG']=str(path)
    # Strictly load the complete retained encoder state in the runner.
    asf['MODEL'][kind]['PRETRAINED']=None
save(HERE/'encoder_sources.json',encoders)
l4=yaml.safe_load((L4DR/'configs/cfg_PP_L4DR.yml').read_text())
l4['GENERAL']['NAME']='L4DR_v2_local_matched_Strong_260915'
l4['GENERAL']['SEED']=SEED
l4['GENERAL']['RESUME']['IS_RESUME']=False
l4['GENERAL']['LOGGING'].update(IS_LOGGING=True,IS_SAVE_MODEL=False)
l4['OPTIMIZER']=copy.deepcopy(asf['OPTIMIZER'])
l4['DATASET']['path_data']=copy.deepcopy(asf['DATASET']['path_data'])
l4['DATASET']['label_version']='v2_0'
l4['DATASET']['label']=copy.deepcopy(asf['DATASET']['label'])
l4['DATASET']['calib']=copy.deepcopy(asf['DATASET']['calib'])
l4['DATASET']['roi']['xyz']=copy.deepcopy(asf['DATASET']['roi']['xyz'])
l4['DATASET']['roi']['check_azimuth_for_rdr']=False
# Use exactly the same radar files as Strong/ASF; preserve native sampling and voxelization.
l4['DATASET']['rdr_sparse']['dir']=asf['DATASET']['rdr_sparse']['dir']
l4['MODEL']['POST_PROCESSING']=copy.deepcopy(asf['MODEL']['HEAD']['POST_PROCESSING'])
l4['VAL']['IS_VALIDATE']=False
for name,cfg in [('strong_reference',strong),('asf',asf),('l4dr',l4)]:
    (HERE/(name+'_config.yml')).write_text(yaml.safe_dump(cfg,sort_keys=False))

def parser(cls,cfg):
    obj=cls.__new__(cls);obj.cfg=EasyDict(cfg['DATASET'])
    for key in ['label','label_version','item','calib','roi']:setattr(obj,key,obj.cfg[key])
    return obj
a=parser(KRadarFusion_v1_0,asf);b=parser(module.KRadarDetection_v2_0,l4)
reference=[json.loads(x) for x in (REFERENCE/'manifest.jsonl').read_text().splitlines()]
summary={}
for split in ['train','test']:
    pairs=[line.split(',') for line in (ROOT/'resources/split'/(split+'.txt')).read_text().splitlines()]
    pairs.sort(key=lambda x:(int(x[0]),x[1]))
    kept=[];counts=Counter()
    for j,(seq,label) in enumerate(pairs):
        item={'meta':dict(header=str(DATA),seq=seq,split=split,
            label_v1_0=str(DATA/seq/'info_label'/label),
            label_v2_0=str(ROOT/'tools/revise_label/kradar_revised_label_v2_0/KRadar_refined_label_by_UWIPL'/seq/label))}
        aa=a.get_label(copy.deepcopy(item));bb=b.get_label(copy.deepcopy(item))
        assert aa['meta']['label']==bb['meta']['label'],(split,seq,label)
        if aa['meta']['num_obj']>0:
            a.get_description(aa);meta=aa['meta'];index=len(kept)
            record=dict(index=index,id=seq+','+label,meta=meta,
                groups=['all',meta['desc']['climate'],meta['desc']['capture_time'],meta['desc']['road_type']])
            if split=='test':
                rr=reference[index]
                assert record['id']==rr['id']
                assert json.loads(json.dumps(meta['label']))==rr['meta']['label']
                assert meta['desc']==rr['meta']['desc']
            radar=Path(asf['DATASET']['rdr_sparse']['dir'])/seq/('sprdr_'+meta['idx']['rdr']+'.npy')
            for path in [radar,Path(meta['path']['ldr64']),Path(meta['path']['front'])]:
                assert path.is_file(),str(path)
            counts.update(c for c,box,track,avail in meta['label'])
            kept.append(record)
        if j%2000==0:print(split,j,len(pairs),'retained',len(kept),flush=True)
    if split=='train':assert len(kept)//BATCH==7193,len(kept)
    else:assert len(kept)==13727,len(kept)
    tmp=HERE/(split+'_manifest.jsonl.tmp')
    with tmp.open('w') as f:
        for row in kept:f.write(json.dumps(row)+'\n')
    tmp.replace(HERE/(split+'_manifest.jsonl'))
    summary[split]=dict(frames=len(kept),gt_objects=dict(counts),
        manifest_sha256=sha(HERE/(split+'_manifest.jsonl')),
        both_native_label_parsers_exact_match=True,all_sensor_paths_exist=True)
    print(split,'COMPLETE',summary[split],flush=True)
train_log=ROOT/'results/exp_260806_000825_DecControlledASFStrong_final/raw/train_dec_control_strong_gpu3.log'
raw=train_log.read_text();epochs=re.findall(r'Training epoch = (\d+/\d+)',raw)
assert epochs==[str(i)+'/10' for i in range(11)]
durations=re.findall(r'7193/7193 \[(\d+:\d+:\d+)<',raw)[::2]
seconds=sum(sum(int(v)*k for v,k in zip(t.split(':'),[3600,60,1])) for t in durations)
save(HERE/'preflight.json',dict(status='complete',datasets=summary,budget=dict(epochs=11,
    batch_size=2,steps_per_epoch=7193,total_steps=79123,training_sample_presentations=158246,
    seed=SEED,precision='FP32',checkpoint_selection='last epoch only; no test-based checkpoint selection',
    optimizer=asf['OPTIMIZER'],historical_strong_training_wall_hours=seconds/3600),
    test_gt_reference_sha256=sha(REFERENCE/'manifest.jsonl'),
    radar_input_directory=asf['DATASET']['rdr_sparse']['dir'],
    initialization=dict(asf='Same pretrained sensor encoders as Strong; new A2Fusion and detection head; freeze=True, freeze_bn=False',
        l4dr='Native complete network randomly initialized; no official full-detector checkpoint loaded'),
    limitations=['Same fusion/detector training schedule, not identical total pretraining cost or FLOPs',
        'L4DR native preprocessing and architecture retained; restricted-budget local training, public configuration defaults to 35 epochs'],
    configs={name:sha(HERE/(name+'_config.yml')) for name in ['strong_reference','asf','l4dr']}))
print('PREPARATION COMPLETE',flush=True)
