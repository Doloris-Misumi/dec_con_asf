"""Opt-in, eval-only deployment adapters for the original loaded checkpoints.

CUDA graphs replay all operators on each new input; no image/BEV features or
predictions are cached across frames. Original modules and state_dict weights
remain intact. Training entry points never import this file.
"""
import torch
from torch import nn


def capture(function):
    stream = torch.cuda.Stream()
    stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(stream), torch.no_grad():
        for _ in range(3):
            function()
    torch.cuda.current_stream().wait_stream(stream)
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph), torch.no_grad():
        output = function()
    graph.replay()
    return graph, output


class TensorGraph(nn.Module):
    """Single CUDA tensor input, fixed-shape tensor/tree output, serial inference."""
    def __init__(self, original):
        super().__init__()
        self.original = original
        self.enabled = True
        self.graph = None
        self.training = False

    def forward(self, x):
        if self.original.training or torch.is_grad_enabled():
            raise RuntimeError('Deployment adapter requires eval() and no_grad().')
        if not self.enabled:
            return self.original(x)
        if self.graph is None:
            self.static = x.clone()
            self.graph, self.output = capture(lambda: self.original(self.static))
        if x.shape != self.static.shape or x.dtype != self.static.dtype or x.device != self.static.device:
            return self.original(x)
        self.static.copy_(x)
        self.graph.replay()
        return self.output


class FusionGraph(nn.Module):
    """Capture the full fusion, including all TaskDec controls and query/PFT."""
    def __init__(self, original):
        super().__init__()
        self.original = original
        self.enabled = True
        self.graph = None
        self.training = False

    def forward(self, batch):
        original = self.original
        if original.training or torch.is_grad_enabled():
            raise RuntimeError('Deployment adapter requires eval() and no_grad().')
        keys = tuple(k for k in original.key_feats if k in batch.get('avail_feats', original.key_feats))
        if (not self.enabled or any(k in batch for k in ['get_att_maps', 'get_feats_to_vis', 'feat_indiv'])):
            return original(batch)
        if self.graph is None:
            self.keys = keys
            self.static = {k: batch[k].clone() for k in keys}
            self.static['avail_feats'] = list(keys)
            self.graph, self.output = capture(lambda: original(self.static))
            self.output_keys = tuple(k for k in self.output if k not in keys and k != 'avail_feats')
        if keys != self.keys or any(batch[k].shape != self.static[k].shape or
                                   batch[k].dtype != self.static[k].dtype or
                                   batch[k].device != self.static[k].device for k in keys):
            return original(batch)
        for key in keys:
            self.static[key].copy_(batch[key])
        self.graph.replay()
        for key in self.output_keys:
            batch[key] = self.output[key]
        return batch


def install(model, name):
    if model.training:
        raise ValueError('Call eval and load the checkpoint before installation.')
    if name not in ['graph_fusion', 'graph_camera', 'graph_both']:
        raise ValueError(name)
    if name in ['graph_fusion', 'graph_both']:
        model.fuser = FusionGraph(model.fuser)
    if name in ['graph_camera', 'graph_both']:
        model.cam.backbone = TensorGraph(model.cam.backbone)
    return dict(name=name, weights_changed=False, operators_removed=False,
                precision_changed=False, gt_recall_preserved=True,
                dynamic_inputs='New images and BEV features copied and recomputed per frame',
                preparation='Three side-stream warmups and one capture per selected module; outside measurement',
                fallback='Unseen shape or modality subset uses original eager execution',
                concurrency='Single in-flight frame per model instance')


def set_enabled(model, enabled):
    for module in model.modules():
        if isinstance(module, (TensorGraph, FusionGraph)):
            module.enabled = enabled


@torch.no_grad()
def check_graphs(model):
    """Diagnostic only: eager and graph see exactly the same module inputs."""
    def leaves(value, prefix='output'):
        if torch.is_tensor(value):
            return {prefix: value.detach().cpu().clone()}
        if isinstance(value, (tuple, list)):
            return {k: v for i, item in enumerate(value) for k, v in leaves(item, f'{prefix}.{i}').items()}
        if isinstance(value, dict):
            return {k: v for name, item in value.items() for k, v in leaves(item, f'{prefix}.{name}').items()}
        return {}
    result = {}
    for name, module in model.named_modules():
        if not isinstance(module, (TensorGraph, FusionGraph)) or module.graph is None:
            continue
        if isinstance(module, TensorGraph):
            actual = leaves(module.output)
            expected = leaves(module.original(module.static))
        else:
            actual = leaves({k: module.output[k] for k in module.output_keys})
            # original mutates its batch dictionary, so never pass the captured
            # output dictionary here (that would replace graph buffer references).
            fresh = {k: module.static[k] for k in module.keys}
            fresh['avail_feats'] = list(module.keys)
            expected_batch = module.original(fresh)
            expected = leaves({k: expected_batch[k] for k in module.output_keys})
        result[name] = {k: dict(exact=torch.equal(v, expected[k]),
                               max_abs=float((v-expected[k]).abs().max()) if v.numel() else 0.)
                        for k, v in actual.items()}
    return result
