"""Launch the authorized single-GPU2 VoD experiment after successful checks."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec')
RUN = Path('/home/hongsheng/dec_con_asf/analysis_exports/objdec_vod_patch2_local_260920')
ENTRY = Path('/home/hongsheng/dec_con_asf/scripts/run_objdec_vod_patch2_local_260920.py')
PYTHON = '/home/hongsheng/miniconda3/envs/rl_3dod/bin/python'
CONFIG = 'cfgs/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920.yaml'
TAG = 'objdec_p2_local_mild_b8a2_fp32_ep80_260920_gpu2'
OUTPUT = ROOT / 'output/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920' / TAG
LOG = Path('/home/hongsheng/dec_con_asf/vod_taskdec_native/logs/objdec_vod_patch2_local_gpu2_260920.log')
assert not (RUN/'launch.json').exists(), 'Already launched: inspect existing process, do not duplicate.'
assert not OUTPUT.exists(), 'Output directory already exists; refusing automatic resume.'
assert not LOG.exists(), 'Log already exists.'
smoke = json.loads((RUN/'smoke_b8.json').read_text())
assert smoke['batch_size'] == 8 and smoke['accumulation'] == 2 and smoke['no_gt_inference']
assert smoke['peak_reserved_gib'] < 32
evaluation = json.loads((RUN/'validation/epoch_000/metrics.json').read_text())
assert evaluation['frames'] == 8 and evaluation['official']['entire_area'] and evaluation['official']['roi']
gpu = subprocess.check_output(['nvidia-smi','--id=2','--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],text=True).strip()
uuid, used = [v.strip() for v in gpu.split(',')]
assert uuid == 'GPU-a669257e-8165-eea0-ffa3-c7016159e401'
assert int(used) < 1024, f'GPU2 not idle: {gpu}'
cmd = [PYTHON, '-u', str(ENTRY), '--cfg_file', CONFIG, '--extra_tag', TAG,
       '--batch_size','8','--epochs','80','--workers','4','--fix_random_seed',
       '--ckpt_save_interval','5','--max_ckpt_save_num','16',
       '--ckpt_save_time_interval','900','--logger_iter_interval','20','--wo_gpu_stat']
env = dict(os.environ, CUDA_VISIBLE_DEVICES='2', CUDA_HOME='/usr/local/cuda-11.3',
           OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', MKL_NUM_THREADS='4',
           NUMBA_NUM_THREADS='4', PYTHONUNBUFFERED='1',
           CONDA_PREFIX='/home/hongsheng/miniconda3/envs/rl_3dod')
env['PATH'] = '/home/hongsheng/miniconda3/envs/rl_3dod/bin:' + env.get('PATH','')
sources = [ROOT/'tools'/CONFIG, ROOT/'tools/cfgs/dataset_configs/Vod_fusion.yaml',
           ENTRY, Path(__file__), ROOT/'tools/train.py', ROOT/'tools/train_utils/train_utils.py',
           ROOT/'pcdet/models/backbones_2d/base_bev_backbone_taskdec.py',
           ROOT/'pcdet/models/model_utils/taskdec_fuser/a2_fusion.py',
           ROOT/'pcdet/models/model_utils/taskdec_fuser/patch_dec_a2_fusion.py',
           ROOT/'pcdet/models/model_utils/taskdec_fuser/task_aware_dec_controlled_a2_fusion.py',
           ROOT/'pcdet/datasets/vod_evaluation/kitti_official_evaluate.py',
           ROOT/'pcdet/datasets/vod_evaluation/rotate_iou_cpu.py',
           ROOT/'pcdet/datasets/vod/vod_dataset.py']
data_root = Path('/home/hongsheng/vod/view_of_delft_PUBLIC/rlfusion_5f')
sources += [data_root/'ImageSets/train.txt', data_root/'ImageSets/val.txt',
            data_root/'vod_infos_train.pkl', data_root/'vod_infos_val.pkl']
hashes = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_file()}
shutil.copy2(ROOT/'tools'/CONFIG, RUN/'config.yaml')
with LOG.open('x') as stream:
    stream.write('Launching ObjDec VoD on physical GPU2; batch8 x accumulation2; FP32; from scratch; 80 epochs.\n')
    stream.flush()
    proc = subprocess.Popen(cmd, cwd=ROOT/'tools', env=env, stdout=stream,
                            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            start_new_session=True)
manifest = dict(started=datetime.datetime.now().astimezone().isoformat(), pid=proc.pid,
    gpu=2, gpu_uuid=uuid, command=cmd, log=str(LOG), output=str(OUTPUT),
    initialized_from='scratch', epochs=80, seed=666, batch=8, accumulation=2,
    effective_batch=16, bn_microbatch=8, precision='FP32',
    selection_metric='VoD EAA mAP', evaluation_interval=5, train_frames=5139, val_frames=1296,
    model_changes=['patch2/query4','two 3x3 stride1 Conv-BN-ReLU per modality','TO_EMBED LayerNorm'],
    preserved=['0.16m grid','mild losses','L+R / radar 5 frames','ROI','augmentations','head','score/NMS'],
    source_sha256=hashes, smoke=smoke)
(RUN/'launch.json').write_text(json.dumps(manifest,indent=2)+'\n')
(RUN/'status.json').write_text(json.dumps({'status':'starting','pid':proc.pid},indent=2)+'\n')
print(json.dumps({'pid':proc.pid,'log':str(LOG),'output':str(OUTPUT)}))
