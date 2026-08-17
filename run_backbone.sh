#!/bin/bash
# Train ASF sensor backbones on K-Radar (edits PATH_CONFIG in main_train_0.py)

ENV_PYTHON=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
ASF_DIR=/home/hongsheng/K-Radar-main
LOG_DIR=/tmp
MAIN_FILE=$ASF_DIR/main_train_0.py
MAIN_BAK=$ASF_DIR/main_train_0.py.bak

case "$1" in
  rtnh)
    GPU=0
    CFG=./configs/cfg_RTNH_local.yml
    LOG=$LOG_DIR/train_rtnh.log
    ;;
  second)
    GPU=1
    CFG=./configs/cfg_SECOND_local.yml
    LOG=$LOG_DIR/train_second.log
    ;;
  camera)
    GPU=2
    CFG=./configs/cfg_CAMERA_MODEL_Base_local.yml
    LOG=$LOG_DIR/train_camera.log
    ;;
  all)
    GPU=0
    CFG=./configs/ASF_v2_0_final.yml
    LOG=$LOG_DIR/train_asf_fusion.log
    ;;
  *)
    echo "Usage: $0 {rtnh|second|camera}"
    exit 1
    ;;
esac

cd $ASF_DIR

# Backup original main file
if [ ! -f "$MAIN_BAK" ]; then
  cp "$MAIN_FILE" "$MAIN_BAK"
fi

# Patch: GPU and config path
sed -i "s|os.environ\['CUDA_VISIBLE_DEVICES'\]= .*|os.environ['CUDA_VISIBLE_DEVICES']= '$GPU'|" "$MAIN_FILE"
sed -i "s|PATH_CONFIG = .*|PATH_CONFIG = '$CFG'|" "$MAIN_FILE"

echo "Launching $1 on GPU $GPU"
echo "Config: $CFG"
echo "Log:    $LOG"
echo "---"

CUDA_VISIBLE_DEVICES=$GPU HF_HUB_OFFLINE=1 PYTHONPATH="ops:$PYTHONPATH" nohup $ENV_PYTHON "$MAIN_FILE" > "$LOG" 2>&1 &
echo "PID=$!"
echo "tail -f $LOG"
