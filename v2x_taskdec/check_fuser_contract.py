"""CPU interface checks of the exact formal TaskDec snapshot, not detection results."""
import json
from pathlib import Path

import torch
import yaml
from easydict import EasyDict

from v2x_taskdec.fuser import A2Fusion, TaskAwareDecControlledA2Fusion


ROOT = Path(__file__).resolve().parents[1]


def check(n_modalities):
    torch.manual_seed(260916)
    base = yaml.safe_load((ROOT / 'configs/v1_0/cfg_A2F_scl_final.yml').read_text())['MODEL']['FUSER']
    overlay = yaml.safe_load((ROOT / 'configs/ASF_task_dec_controlled_robust_v1_0.yml').read_text())['MODEL']['FUSER']
    base.update(overlay)
    base.update(KEY_FEATS=['camera', 'lidar', 'radar'][-n_modalities:],
                DIM_FEATS=[16] * n_modalities, DEC_CONTROL_NUM_CLASSES=3,
                DEC_CONTROL_CONTEXT_MODE='class')
    cfg = EasyDict(base)
    kwargs = dict(grid_size=[8, 8, 1], point_cloud_range=[0, -4, -2, 8, 4, 2],
                  voxel_size=[1, 1, 4], scl=False)
    full = TaskAwareDecControlledA2Fusion(cfg, **kwargs)
    patch = A2Fusion(cfg, **kwargs)
    shared = {k: v for k, v in full.state_dict().items() if k in patch.state_dict()}
    patch.load_state_dict(shared, strict=True)
    batch = {k: torch.randn(2, 16, 8, 8, requires_grad=True) for k in cfg.KEY_FEATS}
    batch['gt_boxes'] = torch.tensor([[[3., 0., 0., 3., 2., 1.5, .2, 1.]],
                                      [[5., 1., 0., 2., 2., 1.6, -.4, 3.]]])
    out = full(dict(batch))
    assert out['fused_feat'].shape == (2, 2048, 8, 8)
    assert 'patch_dec_loss' in out
    loss = out['fused_feat'].square().mean() + .12 * out['patch_dec_loss']
    loss.backward()
    groups = ['patch_common', 'patch_unique', 'dec_control_fg_gate', 'dec_control_score',
              'dec_control_class_head', 'dec_control_class_context', 'fuser']
    gradients = {}
    for group in groups:
        values = [p.grad for name, p in full.named_parameters() if group in name and p.grad is not None]
        gradients[group] = sum(float(v.abs().sum()) for v in values)
        assert values and all(torch.isfinite(v).all() for v in values), group
        assert gradients[group] > 0, (group, gradients)
    for key in cfg.KEY_FEATS:
        assert batch[key].grad is not None and torch.isfinite(batch[key].grad).all()
        assert batch[key].grad.abs().sum() > 0
    full.eval(); patch.eval()
    without_gt = {k: batch[k].detach() for k in cfg.KEY_FEATS}
    with torch.no_grad():
        predicted = full(dict(without_gt))['fused_feat']
        changed_gt = dict(without_gt, gt_boxes=batch['gt_boxes'] * 3)
        assert torch.equal(predicted, full(changed_gt)['fused_feat']), 'GT leaked into inference'
        full.patch_dec_enabled = False
        assert torch.equal(full(dict(without_gt))['fused_feat'], patch(dict(without_gt))['fused_feat']), 'patch control mismatch'
    return dict(modalities=list(cfg.KEY_FEATS), output_shape=list(predicted.shape),
                parameters_full=sum(p.numel() for p in full.parameters()),
                parameters_patch=sum(p.numel() for p in patch.parameters()),
                auxiliary_loss=float(out['patch_dec_loss'].detach()), gradient_l1=gradients,
                inference_independent_of_gt=True, disabled_control_equals_shared_patch=True)


if __name__ == '__main__':
    torch.set_num_threads(2)
    rows = [check(2), check(3)]
    result = dict(status='passed', device='cpu', scope='Synthetic fuser contract only; no dataset or detector tested', cases=rows)
    out = ROOT / 'analysis_exports/v2x_taskdec_260916/fuser_contract.json'
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
