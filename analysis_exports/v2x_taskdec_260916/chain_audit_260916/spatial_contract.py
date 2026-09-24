"""Check actual CUDA pooling/scatter and patch inverse with an off-diagonal impulse."""
import sys,json
from pathlib import Path
import torch
from torch import nn
ROOT=Path('/home/hongsheng/dec_con_asf');sys.path.insert(0,str(ROOT))
from v2x_taskdec.model import PillarEncoder,bev_pool,fuser_config,A2Fusion
from einops import rearrange
OUT=Path(__file__).parent;F=OUT.parent/'controlled_80ep'
cfg=json.loads((F/'config.json').read_text());torch.set_num_threads(2)
torch.cuda.set_per_process_memory_fraction(.05)
class StubVFE(nn.Module):
    def forward(self,d):
        d['pillar_features']=d['voxels'][:,0,:];return d
enc=PillarEncoder(cfg,4).cuda();enc.vfe=StubVFE();enc.stem=nn.Identity()
vals=torch.arange(1,65,device='cuda',dtype=torch.float32)[None]
coords=torch.tensor([[3,7,0,0]],device='cuda',dtype=torch.int32)
cam=bev_pool(vals,coords,1,1,256,256)[:,:,0].transpose(-1,-2).contiguous()
pc=enc((vals[:,None],torch.tensor([[0,0,7,3]],device='cuda',dtype=torch.int32),torch.tensor([1],device='cuda')),1)
assert torch.equal(pc,cam)
assert torch.equal(cam[0,:,7,3],vals[0])
assert not bool(cam[0,:,3,7].any())
f=A2Fusion(fuser_config(cfg),[256,256,1])
test=torch.arange(256*256*128,dtype=torch.float32).reshape(1,128,256,256)
tokens=rearrange(test,'b c (y py) (x px) -> (b y x) (py px) c',py=4,px=4)
assert torch.equal(f.to_fused_feat(tokens),test)
report={'status':'passed','impulse_xyz':[3,7,0],'expected_output_yx':[7,3],
    'camera_pool_equals_pillar_scatter':True,'patch_unpatch_exact':True}
(OUT/'spatial_contract.json').write_text(json.dumps(report,indent=2));print(report)
