"""Reuse the previous exact training/validation loop with frozen adapted anchors."""
import json
from pathlib import Path
import sys
import run_objdec_vod_patch2_local_260920 as base

base.RUN = Path('/home/hongsheng/dec_con_asf/analysis_exports/objdec_vod_adapted_anchors_260921')
base.CONFIG = 'cfgs/VoD_models/ObjDec_PP_Patch2_Local_Anchors_260921.yaml'
base.RUN.mkdir(parents=True,exist_ok=True)


def checked_smoke():
    original_build = base.build_network
    original_fn = base.model_fn_decorator
    checks = {'positive_anchors_by_class': {n:0 for n in ['Car','Pedestrian','Cyclist']}, 'anchors':[]}
    def build(*args,**kwargs):
        model = original_build(*args,**kwargs)
        head = model.dense_head
        for spec, anchors in zip(base.cfg.MODEL.DENSE_HEAD.ANCHOR_GENERATOR_CONFIG,head.anchors):
            flat = anchors.reshape(-1,7)
            expected = flat.new_tensor(spec.anchor_sizes[0])
            assert base.torch.allclose(flat[:,3:6],expected.expand_as(flat[:,3:6]))
            bottom = flat[:,2]-flat[:,5]/2
            assert base.torch.allclose(bottom,bottom.new_full(bottom.shape,spec.anchor_bottom_heights[0]))
            # The same adapted anchors must encode/decode residuals consistently.
            ref = flat[:32].clone()
            target = ref.clone(); target[:,0]+=.17; target[:,1]-=.09; target[:,2]+=.08
            target[:,3:6]*=1.05; target[:,6]+=.1
            coded = head.box_coder.encode_torch(target.clone(),ref.clone())
            decoded = head.box_coder.decode_torch(coded,ref.clone())
            error = float((decoded-target).abs().max())
            assert error<1e-5
            checks['anchors'].append(dict(class_name=spec.class_name, count=len(flat),
                size=spec.anchor_sizes[0],bottom_z=spec.anchor_bottom_heights[0],roundtrip_max_abs_error=error))
        assert sum(p.numel() for p in model.parameters())==18605583
        return model
    def decorator():
        fn = original_fn()
        def checked(model,batch):
            result = fn(model,batch)
            labels = model.dense_head.forward_ret_dict['box_cls_labels']
            for k,name in enumerate(base.cfg.CLASS_NAMES,1):
                checks['positive_anchors_by_class'][name] += int((labels==k).sum())
            return result
        return checked
    base.build_network=build; base.model_fn_decorator=decorator
    base.smoke(8)
    assert all(v>0 for v in checks['positive_anchors_by_class'].values())
    base.write_json(base.RUN/'anchor_smoke_checks.json',checks)
    print(json.dumps(checks,indent=2))


if __name__=='__main__':
    if sys.argv[1:]==['--smoke-batch','8']:
        checked_smoke()
    elif sys.argv[1:]==['--smoke-eval']:
        base.cfg_from_yaml_file(base.CONFIG,base.cfg)
        base.common_utils.set_random_seed(666)
        logger=base.common_utils.create_logger(base.RUN/'smoke_eval.log')
        ds,_,_=base.build_dataloader(base.cfg.DATA_CONFIG,base.cfg.CLASS_NAMES,2,False,
            workers=0,training=False,logger=logger)
        model=base.build_network(base.cfg.MODEL,len(base.cfg.CLASS_NAMES),ds).cuda()
        base.validate(model,0,logger,limit=8)
    else:
        base.train()
