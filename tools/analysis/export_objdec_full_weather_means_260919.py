#!/usr/bin/env python3
"""Full v1 test-set foreground means, resumable and bounded in disk usage.

Save per-frame 256-D means, scalar scatter and paired cosine statistics only.
No patch feature maps, input data, detections, or checkpoints are copied.
GT defines analysis regions and never changes model inputs or predictions.
"""
import argparse
from collections import Counter
import copy
import datetime
import fcntl
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time
import traceback
import types

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'ops')]
from export_taskdec_patch_pca import DEFAULT_EXP, infer_weather, build_weather_balanced_indices
from plot_objdec_pca_260919 import FEATURES, MODALITIES, WEATHERS


def now():
    return datetime.datetime.now().astimezone().isoformat()


def write_json(path, data):
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    temp.replace(path)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


class Collector:
    def __init__(self):
        self.frame_index = -1
        self.record = None
        self.calls = 0

    def capture(self, fuser, keys, tokens, batch):
        import torch
        import torch.nn.functional as F
        self.calls += 1
        base = [v.squeeze(1) for v in tokens]
        order = [keys.index(k) for k in ['cam_bev_feat','spatial_features_2d','bev_feat']]
        raw = torch.stack([base[i] for i in order])
        common = torch.stack([fuser.patch_common[keys[i]](base[i]) for i in order])
        unique = torch.stack([fuser.patch_unique[keys[i]](base[i]) for i in order])
        states = torch.stack([raw, common, unique])  # feature, modality, patch, channel
        mask, _, nf, _ = fuser._gt_patch_targets(batch,raw.shape[1],raw.device,
                                                num_classes=fuser.dec_control_num_classes)
        if mask is None:
            mask = torch.zeros(raw.shape[1], dtype=torch.bool, device=raw.device)
        assert mask.ndim == 1 and int(mask.sum()) == nf
        means = torch.full((3,3,raw.shape[-1]),float('nan'),device=raw.device)
        scatter = torch.full((3,3),float('nan'),device=raw.device)
        norm_mean = torch.full((3,3),float('nan'),device=raw.device)
        cosine = torch.full((3,3),float('nan'),device=raw.device)
        abs_common_unique = torch.full((3,),float('nan'),device=raw.device)
        if nf:
            x=states[:,:,mask,:].float()
            assert torch.isfinite(x).all()
            means=x.mean(dim=2)
            scatter=((x-means[:,:,None,:])**2).sum(dim=-1).mean(dim=2)
            norm_mean=x.norm(dim=-1).mean(dim=2)
            unit=F.normalize(x,dim=-1,eps=1e-12)
            cosine=torch.stack([(unit[:,a]*unit[:,b]).sum(-1).mean(-1)
                                for a,b in [(0,1),(0,2),(1,2)]],dim=1)
            abs_common_unique=(unit[1]*unit[2]).sum(-1).abs().mean(-1)
        factor=fuser._dec_control_schedule_factor(batch)
        _, gp, _, _, sp, _=fuser._dec_control_scores(
            keys,base,[common[order.index(i)] for i in range(len(keys))],
            [unique[order.index(i)] for i in range(len(keys))],control_factor=factor)
        gate=torch.stack([gp[mask].mean() if nf else gp.new_tensor(float('nan')),
                          gp[~mask].mean() if (~mask).any() else gp.new_tensor(float('nan'))])
        sensor=sp[mask][:,order].mean(0) if nf else sp.new_full((3,),float('nan'))
        meta=batch['meta'][0]
        weather=infer_weather(meta)
        if weather not in WEATHERS: raise ValueError('Unknown weather: '+weather)
        ids=meta.get('idx',{})
        self.record=dict(dataset_index=np.int64(self.frame_index),weather=weather,
            seq=str(meta.get('seq','unknown')),sample_id=str(ids.get('rdr',ids.get('camf',self.frame_index))),
            num_foreground=np.int32(nf),num_patches=np.int32(raw.shape[1]),
            means=means.cpu().numpy(),within_frame_scatter=scatter.cpu().numpy(),
            mean_norm=norm_mean.cpu().numpy(),paired_cosine=cosine.cpu().numpy(),
            common_unique_mean_abs_cos=abs_common_unique.cpu().numpy(),
            gate_fg_bg=gate.cpu().numpy(),sensor_fg=sensor.cpu().numpy())


def flush(out, records):
    if not records:return
    path=out/'chunks'/f"frames_{int(records[0]['dataset_index']):05d}_{int(records[-1]['dataset_index']):05d}.npz"
    if path.exists():raise FileExistsError(path)
    temp=path.with_suffix('.tmp')
    with temp.open('wb') as stream:
        np.savez_compressed(stream,**{k:np.asarray([r[k] for r in records]) for k in records[0]})
    temp.replace(path)
    records.clear()


def load_chunks(out):
    chunks=[]
    for path in sorted((out/'chunks').glob('frames_*.npz')):
        with np.load(path) as z: chunks.append({k:z[k] for k in z.files})
    if not chunks:return {}
    data={k:np.concatenate([c[k] for c in chunks]) for k in chunks[0]}
    ids=data['dataset_index']; assert len(np.unique(ids))==len(ids)
    order=np.argsort(ids)
    return {k:v[order] for k,v in data.items()}


def summarize(out, expected, is_smoke):
    import csv
    from plot_objdec_pca_260919 import style, save, plt, COLORS, MARKERS, TITLES, LABELS, limits, Line2D
    data=load_chunks(out)
    assert len(data['dataset_index'])==expected
    valid=data['num_foreground']>0
    rows=[]
    for w in WEATHERS:
        mask=(data['weather']==w)&valid
        if not mask.any():continue
        for j,f in enumerate(FEATURES):
            cos=data['paired_cosine'][mask,j,:].astype(np.float64)
            pair_mean=cos.mean(0)
            patch_mean=np.average(cos.mean(1),weights=data['num_foreground'][mask])
            seqs=np.unique(data['seq'][mask])
            seq_mean=np.mean([cos[data['seq'][mask]==s].mean() for s in seqs])
            rows.append(dict(weather=w,feature=f,frames=int(mask.sum()),
                frames_without_foreground=int(((data['weather']==w)&~valid).sum()),
                sequences=len(seqs),foreground_patches=int(data['num_foreground'][mask].sum()),
                cosine_CL=pair_mean[0],cosine_CR=pair_mean[1],cosine_LR=pair_mean[2],
                frame_equal_cosine=float(pair_mean.mean()),patch_equal_cosine=float(patch_mean),
                sequence_equal_cosine=float(seq_mean)))
    with (out/'weather_statistics.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    style()
    basis={}
    fig,axes=plt.subplots(1,3,figsize=(12,4.1))
    weather=data['weather'][valid]; means=data['means'][valid].astype(np.float64)
    present=np.unique(weather)
    weights=np.array([1/(len(present)*np.sum(weather==w)*3) for w in weather])
    weights=np.repeat(weights,3)
    rng=np.random.default_rng(20260919)
    for j,ax in enumerate(axes):
        x=means[:,j].reshape(-1,means.shape[-1]); center=np.sum(x*weights[:,None],axis=0)
        centered=x-center; cov=(centered*weights[:,None]).T@centered
        values,vectors=np.linalg.eigh(cov); order=np.argsort(values)[::-1]
        components=vectors[:,order[:2]].T
        # Deterministic signs make regeneration directly comparable.
        for k in range(2):
            if components[k,np.argmax(abs(components[k]))]<0:components[k]*=-1
        coords=(centered@components.T).reshape(-1,3,2)
        ratio=values[order[:2]]/max(values.sum(),1e-12)
        basis[FEATURES[j]+'_mean']=center
        basis[FEATURES[j]+'_components']=components
        basis[FEATURES[j]+'_explained']=ratio
        centers={}
        for wi,w in enumerate(['normal','heavysnow']):
            ids=np.flatnonzero(weather==w)
            if not len(ids):continue
            chosen=rng.choice(ids,min(350,len(ids)),replace=False)
            for m,(c,marker) in enumerate(zip(COLORS,MARKERS)):
                ax.scatter(*coords[chosen,m].T,s=13,marker=marker,
                           facecolors=c if wi==0 else 'none',edgecolors=c,linewidths=.55,alpha=.28)
                mu=coords[ids,m].mean(0); centers[w,m]=mu
                ax.scatter(*mu,s=110,marker=marker,facecolors=c if wi==0 else 'white',
                           edgecolors=c,linewidths=1.6,zorder=5)
        for m,c in enumerate(COLORS):
            if ('normal',m) in centers and ('heavysnow',m) in centers:
                ax.annotate('',xy=centers['heavysnow',m],xytext=centers['normal',m],
                            arrowprops=dict(arrowstyle='->',color=c,lw=1.4),zorder=6)
        shown=coords[np.isin(weather,['normal','heavysnow'])].reshape(-1,2)
        lo,hi=limits(shown);ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_aspect('equal',adjustable='box')
        ax.set_title(TITLES[j],fontweight='bold',fontsize=10)
        ax.set_xlabel(f'PC1 ({100*ratio[0]:.1f}%)');ax.set_ylabel(f'PC2 ({100*ratio[1]:.1f}%)');ax.grid(alpha=.12)
    handles=[Line2D([],[],color=c,marker=m,linestyle='',label=n) for n,c,m in zip(MODALITIES,COLORS,MARKERS)]
    handles += [Line2D([],[],color='gray',marker='o',linestyle='',label='Normal'),
                Line2D([],[],color='gray',marker='o',markerfacecolor='white',linestyle='',label='Heavy snow')]
    fig.legend(handles=handles,ncol=5,loc='upper center',frameon=False)
    count_text='; '.join(f'{w}: {int(((weather==w)).sum())} valid frames' for w in ['normal','heavysnow'])
    fig.text(.5,.008,count_text+' | Large markers: means of all valid frames',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.055,1,.89));save(fig,out,'objdec_fulltest_weather_frame_means')
    np.savez_compressed(out/'frame_mean_pca_basis.npz',**basis)
    lines=['# ObjDec full-test weather representation analysis','',
           f'- Complete frames: {expected}; valid foreground frames: {int(valid.sum())}.',
           '- Smoke only.' if is_smoke else '- Full v1 test split; all 10,065 frames processed.',
           '- Each frame mean uses ALL GT-foreground patches, with the original foreground mask and configured margin.',
           '- Main weather means give equal weight to each valid frame; empty-foreground frames are counted and excluded.',
           '- PCA here is fitted to frame-mean vectors, balancing weather groups and modalities; one fixed basis per representation.',
           '- This PCA describes between-frame-mean variation, unlike the existing patch-scatter PCA. Do not directly compare axes between figures.',
           '- Plot points may be subsampled for readability; large centers and tables use all valid frames.',
           '- Sequence-equal and patch-equal cosine summaries are provided as sensitivity checks, not significance tests.',
           '- Weather is observational and confounded with sequence/scene; neither causality nor semantic disentanglement is established by PCA alone.','',
           '| Weather | Valid frames | Sequences | Input cosine | Common cosine | Unique cosine |',
           '|---|---:|---:|---:|---:|---:|']
    for w in WEATHERS:
        selected=[r for r in rows if r['weather']==w]
        if not selected:continue
        vals={r['feature']:r['frame_equal_cosine'] for r in selected};r=selected[0]
        lines.append(f"| {w} | {r['frames']} | {r['sequences']} | {vals['raw']:.4f} | {vals['common']:.4f} | {vals['unique']:.4f} |")
    (out/'analysis.md').write_text('\n'.join(lines)+'\n')
    return rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--gpu',type=int,default=0)
    ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--out-dir',type=Path,default=ROOT/'analysis_exports/objdec_fulltest_weather_260919')
    args=ap.parse_args();out=args.out_dir.resolve();out.mkdir(parents=True,exist_ok=True);(out/'chunks').mkdir(exist_ok=True)
    os.environ['CUDA_VISIBLE_DEVICES']=str(args.gpu)
    lock=(out/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    import torch
    from torch.utils.data import Subset
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0
    logging.getLogger('fontTools').setLevel(logging.WARNING)
    torch.set_num_threads(4);torch.cuda.set_per_process_memory_fraction(.28)
    started=time.monotonic();records=[]
    def status(phase,**kw):
        write_json(out/'status.json',dict(phase=phase,pid=os.getpid(),gpu=args.gpu,
            updated_at=now(),elapsed_seconds=round(time.monotonic()-started,1),**kw))
    try:
        status('loading')
        config=DEFAULT_EXP/'config.yml';ckpt=DEFAULT_EXP/'models/model_0.pt'
        identity=dict(checkpoint=str(ckpt),checkpoint_sha256=sha(ckpt),config=str(config),config_sha256=sha(config),
                      script_sha256=sha(__file__),smoke=args.smoke)
        manifest=out/'manifest.json'
        if manifest.exists():
            old=json.loads(manifest.read_text())
            for key,value in identity.items():assert old[key]==value,('Resume identity changed',key)
        seqs=sorted([p.name for p in Path('/home/hongsheng/k_radar_dataset').iterdir() if p.name.isdigit() and p.is_dir()],key=int)
        overlay=out/'inference_config.yml'
        overlay.write_text(f'_BASE_CONFIG_: {str(config)!r}\nGENERAL:\n  LOGGING:\n    IS_LOGGING: False\n  RESUME:\n    IS_RESUME: False\nVAL:\n  IS_VALIDATE: True\nDATASET:\n  portion: {json.dumps(seqs)}\nOPTIMIZER:\n  NUM_WORKERS: 2\n')
        pipe=PipelineDetection_v1_0(path_cfg=str(overlay),mode='test')
        pipe.load_dict_model(str(ckpt),is_strict=True);pipe.network.eval()
        assert len(pipe.dataset_test)==10065
        assert pipe.cfg.DATASET.label_version=='v1_0'
        assert list(pipe.cfg.DATASET.roi.xyz)==[0.,-6.4,-2.,72.,6.4,6.]
        indices=list(range(len(pipe.dataset_test)))
        if args.smoke:indices,_=build_weather_balanced_indices(pipe.dataset_test,WEATHERS,1)
        write_json(manifest,dict(**identity,dataset_size=10065,target_frames=len(indices),created_at=now(),
             gpu=args.gpu,memory_fraction=.28,precision='FP32, no autocast',
             feature_order=FEATURES,modality_order=MODALITIES,cosine_pair_order=['CL','CR','LR'],
             mask='Original GT-foreground patch mask, including configured margin; all foreground patches retained in statistics.',
             storage='Compressed per-frame means and scalar statistics, chunks of 100. No full patch feature dump.',
             weighting='Main means: equal frame weights within weather. PCA: equal weather, frame within weather, and modality weights.'))
        old=load_chunks(out);done=set(old.get('dataset_index',[]).tolist()) if old else set()
        weather_counts=Counter(old['weather'].tolist()) if old else Counter()
        remaining=[i for i in indices if i not in done]
        if not done.issubset(set(indices)):raise ValueError('Unexpected frame indices in resume data')
        loader=pipe.build_dataloader(Subset(pipe.dataset_test,remaining),batch_size=1,shuffle=False,
                                     collate_fn=pipe.dataset_test.collate_fn)
        collector=Collector();fuser=pipe.network.fuser;original=fuser._apply_patch_dec
        def hooked(self,keys,tokens,batch):
            collector.capture(self,keys,tokens,batch)
            return original(keys,tokens,batch)
        fuser._apply_patch_dec=types.MethodType(hooked,fuser)
        print(f'[start] gpu={args.gpu} target={len(indices)} resumed={len(done)}',flush=True)
        with torch.no_grad():
            for position,batch in enumerate(loader):
                index=remaining[position];collector.frame_index=index;collector.record=None;collector.calls=0
                batch['avail_feats']=pipe.infer_mode_to_avail_feats('rlc')
                if args.smoke and position==0:
                    fuser._apply_patch_dec=original
                    ref=pipe.network(copy.deepcopy(batch))['pred_dicts'][0]
                    reference={k:ref[k].detach().clone() for k in ['pred_boxes','pred_scores','pred_labels']}
                    del ref
                    fuser._apply_patch_dec=types.MethodType(hooked,fuser)
                output=pipe.network(batch)
                assert collector.calls==1 and collector.record is not None
                if args.smoke and position==0:
                    pred=output['pred_dicts'][0];checks={}
                    for k,v in reference.items():
                        assert pred[k].shape==v.shape
                        delta=float((pred[k]-v).abs().max()) if v.numel() else 0.
                        assert torch.allclose(pred[k],v,rtol=1e-5,atol=1e-6),(k,delta)
                        checks[k]=delta
                    write_json(out/'prediction_invariance.json',checks)
                    del reference
                records.append(collector.record);done.add(index);weather_counts[collector.record['weather']]+=1
                del output,batch
                if len(records)>=100:flush(out,records)
                if len(done)%20==0 or args.smoke or len(done)==len(indices):
                    elapsed=time.monotonic()-started
                    status('running',completed=len(done),target=len(indices),weather_counts=dict(weather_counts),
                           max_memory_allocated_mib=round(torch.cuda.max_memory_allocated()/2**20,1))
                    print(f'[progress] {len(done)}/{len(indices)} frame={index} weather={collector.record["weather"]} '
                          f'elapsed={elapsed:.1f}s peak_allocated={torch.cuda.max_memory_allocated()/2**20:.0f}MiB',flush=True)
        flush(out,records);fuser._apply_patch_dec=original
        status('summarizing',completed=len(done),target=len(indices),weather_counts=dict(weather_counts))
        # Release GPU tensors before the CPU-only summary and plotting.
        del loader,pipe,fuser,original,collector;torch.cuda.empty_cache()
        rows=summarize(out,len(indices),args.smoke)
        status('complete',completed=len(done),target=len(indices),weather_counts=dict(weather_counts),
               output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
        print('[complete] '+str(out),flush=True)
    except BaseException as exc:
        flush(out,records)
        status('failed',error=repr(exc));traceback.print_exc();raise


if __name__=='__main__':
    main()
    # Match the existing patch exporter: this legacy CUDA extension stack can
    # abort in native interpreter teardown after every output has been closed.
    # Exceptions in main still propagate normally; only successful runs exit here.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
