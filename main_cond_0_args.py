'''
* Copyright (c) AVELab, KAIST. All rights reserved.
* author: Donghee Paek & Kevin Tirta Wijaya, AVELab, KAIST
* e-mail: donghee.paek@kaist.ac.kr, kevin.tirta@kaist.ac.kr
'''

import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detection Pipeline Evaluation')
    parser.add_argument('--config', type=str, default='./configs/ASF_v2_0_final.yml',
                        help='Path to config file')
    parser.add_argument('--gpu', type=str, default='2',
                        help='CUDA_VISIBLE_DEVICES value')
    parser.add_argument('--model', type=str, default='./pretrained/A2F_v2_0_final_10.pt',
                        help='Path to pretrained model')
    parser.add_argument('--conf_thr', type=float, nargs='+', default=[0.0],
                        help='List of confidence thresholds (e.g., --conf_thr 0.3 0.5 0.7)')
    parser.add_argument('--subset', action='store_true',
                        help='Use subset for validation')
    parser.add_argument('--print_memory', action='store_true',
                        help='Print memory usage')
    from utils.runtime_utils import add_runtime_args, apply_runtime_overrides
    add_runtime_args(parser)
    
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu

    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0
    
    PATH_CONFIG = args.config
    PATH_MODEL = args.model

    pline = PipelineDetection_v1_0(PATH_CONFIG, mode='test')
    apply_runtime_overrides(pline, args)
    pline.load_dict_model(PATH_MODEL)
    
    pline.network.eval()

    # Save the code for identification
    import shutil
    shutil.copy2(os.path.realpath(__file__), os.path.join(pline.path_log, 'executed_code.txt'))
    
    pline.validate_kitti_conditional(
        list_conf_thr=args.conf_thr, 
        is_subset=args.subset, 
        is_print_memory=args.print_memory
    )
