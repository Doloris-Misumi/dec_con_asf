import argparse
import os


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dec-controlled ASF training')
    parser.add_argument('--config', type=str, default='./configs/ASF_dec_controlled.yml')
    parser.add_argument('--gpu', type=str, default='1')
    parser.add_argument('--skip-final-conditional', action='store_true')
    parser.add_argument('--final-conf-thr', default='0.3',
                        help='Comma-separated confidence thresholds for final conditional eval')
    from utils.runtime_utils import add_runtime_args, apply_runtime_overrides
    add_runtime_args(parser)
    args = parser.parse_args()

    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu

    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0

    pline = PipelineDetection_v1_0(path_cfg=args.config, mode='train')
    apply_runtime_overrides(pline, args)

    import shutil
    shutil.copy2(os.path.realpath(__file__), os.path.join(pline.path_log, 'executed_code.txt'))

    pline.train_network()
    if not args.skip_final_conditional:
        final_conf_thr = [float(item.strip()) for item in args.final_conf_thr.split(',') if item.strip()]
        pline.validate_kitti_conditional(list_conf_thr=final_conf_thr, is_subset=False, is_print_memory=False)
