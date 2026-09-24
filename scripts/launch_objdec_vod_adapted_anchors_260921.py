"""Launch the authorized VoD anchor-only comparison on idle physical GPU2."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec')
PROJECT = ROOT.parents[1]
RUN = PROJECT/'analysis_exports/objdec_vod_adapted_anchors_260921'
PREV = PROJECT/'analysis_exports/objdec_vod_patch2_local_260920'
ENTRY = PROJECT/'scripts/run_objdec_vod_adapted_anchors_260921.py'
PYTHON = '/home/hongsheng/miniconda3/envs/rl_3dod/bin/python'
CONFIG = 'cfgs/VoD_models/ObjDec_PP_Patch2_Local_Anchors_260921.yaml'
TAG = 'objdec_p2_local_anchors_b8a2_fp32_ep80_260921_gpu2'
OUTPUT = ROOT/'output/VoD_models/ObjDec_PP_Patch2_Local_Anchors_260921'/TAG
LOG = PROJECT/'vod_taskdec_native/logs/objdec_vod_adapted_anchors_gpu2_260921.log'

assert not (RUN/'launch.json').exists(), 'Already launched; do not duplicate.'
assert not OUTPUT.exists(), 'Refusing automatic resume.'
assert not LOG.exists(), 'Existing log must not be overwritten.'
smoke = json.loads((RUN/'smoke_b8.json').read_text())
checks = json.loads((RUN/'anchor_smoke_checks.json').read_text())
evaluation = json.loads((RUN/'validation/epoch_000/metrics.json').read_text())
assert smoke['batch_size']==8 and smoke['accumulation']==2 and smoke['no_gt_inference']
assert smoke['peak_reserved_gib']<32 and smoke['parameters']==18605583
assert all(v>0 for v in checks['positive_anchors_by_class'].values())
assert evaluation['frames']==8 and evaluation['official']['entire_area'] and evaluation['official']['roi']
# Freeze implementation and data against the previous run; only the new YAML differs.
previous=json.loads((PREV/'launch.json').read_text())
hashes={}
for path,expected in previous['source_sha256'].items():
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert actual==expected, f'Previous implementation/data changed: {path}'
    hashes[path]=actual
extra = [ROOT/'tools'/CONFIG, ENTRY, Path(__file__),
         PROJECT/'scripts/prepare_objdec_vod_anchors_260921.py',RUN/'anchor_statistics.json',
         ROOT/'pcdet/datasets/processor/data_processor.py',ROOT/'pcdet/utils/box_utils.py',
         ROOT/'pcdet/utils/calibration_kitti.py',ROOT/'pcdet/models/dense_heads/target_assigner/anchor_generator.py',
         ROOT/'pcdet/models/dense_heads/target_assigner/axis_aligned_target_assigner.py',
         ROOT/'pcdet/utils/box_coder_utils.py']
for path in extra: hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
gpu=subprocess.check_output(['nvidia-smi','--id=2','--query-gpu=uuid,memory.used',
                             '--format=csv,noheader,nounits'],text=True).strip()
uuid,used=[x.strip() for x in gpu.split(',')]
assert uuid=='GPU-a669257e-8165-eea0-ffa3-c7016159e401' and int(used)<1024, f'GPU2 not idle: {gpu}'
cmd=[PYTHON,'-u',str(ENTRY),'--cfg_file',CONFIG,'--extra_tag',TAG,
     '--batch_size','8','--epochs','80','--workers','4','--fix_random_seed',
     '--ckpt_save_interval','5','--max_ckpt_save_num','16','--ckpt_save_time_interval','900',
     '--logger_iter_interval','20','--wo_gpu_stat']
env=dict(os.environ,CUDA_VISIBLE_DEVICES='2',CUDA_HOME='/usr/local/cuda-11.3',
         OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',NUMBA_NUM_THREADS='4',
         PYTHONUNBUFFERED='1',CONDA_PREFIX='/home/hongsheng/miniconda3/envs/rl_3dod')
env['PATH']='/home/hongsheng/miniconda3/envs/rl_3dod/bin:'+env.get('PATH','')
shutil.copy2(ROOT/'tools'/CONFIG,RUN/'config.yaml')
with LOG.open('x') as stream:
    stream.write('ObjDec VoD adapted anchors: GPU2; scratch80; FP32; batch8 x2; native validation every5.\n')
    stream.flush()
    proc=subprocess.Popen(cmd,cwd=ROOT/'tools',env=env,stdout=stream,stderr=subprocess.STDOUT,
                          stdin=subprocess.DEVNULL,start_new_session=True)
manifest=dict(started=datetime.datetime.now().astimezone().isoformat(),pid=proc.pid,gpu=2,gpu_uuid=uuid,
    command=cmd,log=str(LOG),output=str(OUTPUT),initialized_from='scratch',epochs=80,seed=666,
    batch=8,accumulation=2,effective_batch=16,bn_microbatch=8,precision='FP32',
    selection_metric='VoD EAA mAP',evaluation_interval=5,train_frames=5139,val_frames=1296,
    model_changes=['training-derived per-class anchor sizes and bottom heights'],
    preserved=['0.16m grid','patch2/query4','two stride1 local convolutions per modality','token LayerNorm',
               'mild losses','L+R / radar5','ROI','augmentations','anchor count and rotations',
               'target assignment thresholds','optimizer and schedule','score0.1/NMS0.01'],
    source_sha256=hashes,smoke=smoke,anchor_checks=checks,
    anchor_priors=json.loads((RUN/'anchor_statistics.json').read_text())['classes'])
(RUN/'launch.json').write_text(json.dumps(manifest,indent=2)+'\n')
(RUN/'status.json').write_text(json.dumps(dict(status='starting',pid=proc.pid),indent=2)+'\n')
print(json.dumps(dict(pid=proc.pid,log=str(LOG),output=str(OUTPUT)),indent=2))
