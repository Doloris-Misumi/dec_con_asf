#!/usr/bin/env python3
"""Traceable real-data gate and paired detection figures; small exports only."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'analysis_exports/taskdec_bev_gate_fig4_260910'
OUT = ROOT / 'analysis_exports/objdec_fig4_fig5_260919'
WEATHERS = ['normal', 'overcast', 'fog', 'rain', 'sleet', 'lightsnow', 'heavysnow']
NAMES = dict(zip(WEATHERS, ['Normal', 'Overcast', 'Fog', 'Rain', 'Sleet', 'Light snow', 'Heavy snow']))
SELECT4 = ['seq20_rdr00628', 'seq13_rdr00146', 'seq39_rdr00582', 'seq25_rdr00154',
           'seq50_rdr00456', 'seq43_rdr00169', 'seq55_rdr00385']
sys.path.insert(0, str(ROOT))


def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1024*1024), b''):
            h.update(part)
    return h.hexdigest()


def frames():
    return json.loads((SOURCE/'manifest.json').read_text())['frames']


def plotting():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.labelsize': 8,
                         'xtick.labelsize': 7, 'ytick.labelsize': 7,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    return plt


def corners(box):
    import numpy as np
    xy = np.array([[1,1], [1,-1], [-1,-1], [-1,1]]) * [box[3]/2, box[4]/2]
    c, s = np.cos(box[6]), np.sin(box[6])
    return xy @ np.array([[c,s],[-s,c]]) + box[:2]


def boxes_bev(ax, boxes, color='#20dfaa', style='-', lw=1.0):
    from matplotlib.patches import Polygon
    import matplotlib.patheffects as pe
    for b in boxes:
        p = Polygon(corners(b), closed=True, fill=False, edgecolor=color, linestyle=style,
                    linewidth=lw, zorder=3)
        p.set_path_effects([pe.Stroke(linewidth=lw+.5, foreground='#12222c'), pe.Normal()])
        ax.add_patch(p)


def figure4(out_dir=None):
    import numpy as np
    from matplotlib.lines import Line2D
    from tools.analysis.export_taskdec_bev_gate import camera_image, lidar_points
    from tools.analysis.objdec_plot_palette import MODALITY_COLORS, MODALITY_INK
    out = Path(out_dir) if out_dir is not None else OUT
    lidar_color = MODALITY_COLORS[1]
    plt = plotting()
    plt.rcParams['svg.fonttype'] = 'none'
    lookup = {f['id']: f for f in frames()}
    selected = [lookup[k] for k in SELECT4]
    out.mkdir(parents=True, exist_ok=True)
    # Seven horizontal rows remain readable as an appendix figure. Per-weather
    # pages are also exported so that the author can rearrange the main figure.
    def make(page, stem, figsize):
        fig = plt.figure(figsize=figsize)
        # A partial gate-path schematic, not a replacement for the architecture
        # figure: GT and prediction meet only at the training loss.
        from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
        strip=fig.add_axes([.055,.895,.93,.10]);strip.axis('off')
        strip.text(0,.98,'Gate control path · train + inference',fontsize=9,fontweight='bold',va='top',color='#254b65')
        centers=[.225,.45,.64,.85];widths=[.20,.15,.15,.19]
        labels=['Shared / specific features','MLP + sigmoid',r'Predicted gate $g$', 'Fusion modulation']
        for cx,w,label in zip(centers,widths,labels):
            strip.add_patch(FancyBboxPatch((cx-w/2,.48),w,.30,boxstyle='round,pad=0.008',
                                          facecolor='#eef5fb',edgecolor='#789db7',linewidth=.9))
            strip.text(cx,.63,label,ha='center',va='center',fontsize=9)
        for i in range(3):
            strip.add_patch(FancyArrowPatch((centers[i]+widths[i]/2+.009,.63),
                                           (centers[i+1]-widths[i+1]/2-.009,.63),
                                           arrowstyle='-|>',mutation_scale=10,color='#385c75',linewidth=1))
        strip.text(.20,.13,'Training only',fontsize=9,color='#9a583d',ha='right',va='center')
        for cx,w,label in [(.40,.19,r'GT boxes $\rightarrow$ labels $y$'),(.64,.15,r'$\mathcal{L}_g(g,y)$')]:
            strip.add_patch(FancyBboxPatch((cx-w/2,.015),w,.25,boxstyle='round,pad=0.008',
                                          facecolor='#fff5ed',edgecolor='#bd8564',linestyle='--',linewidth=.9))
            strip.text(cx,.14,label,ha='center',va='center',fontsize=9,color='#80482f')
        for a,b in [((.503,.14),(.555,.14)),((.64,.465),(.64,.28))]:
            strip.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=10,
                                           color='#ad7754',linestyle='--',linewidth=1))
        gs = fig.add_gridspec(len(page), 4, width_ratios=[1.05,1.3,1.3,1.3],
                             left=.065, right=.985, bottom=.06, top=.846, wspace=.14, hspace=.26)
        heat = None
        for row, f in enumerate(page):
            data = np.load(SOURCE/f['archive'], allow_pickle=False)
            gate, fg, roi, gt = data['gate'], data['foreground_mask'], data['roi_xyz'], data['gt_boxes']
            assert gate.shape == (16,90) and np.isfinite(gate).all()
            assert np.isclose(gate[fg].mean(), f['gate_fg_mean'])
            ax = fig.add_subplot(gs[row,0]); ax.imshow(camera_image(f)); ax.axis('off')
            ax.text(-.055,.5,NAMES[f['weather']], transform=ax.transAxes, rotation=90,
                    ha='right',va='center',fontsize=10,fontweight='bold')
            for col in [1,2,3]:
                bx = fig.add_subplot(gs[row,col]); bx.set_facecolor('#101b2b')
                if col == 1:
                    pts = lidar_points(f,roi)
                    bx.scatter(pts[:,0],pts[:,1],s=.32,c=lidar_color,alpha=.68,linewidths=0,rasterized=True)
                else:
                    heat = bx.imshow(gate,origin='lower',extent=[roi[0],roi[3],roi[1],roi[4]],
                                     interpolation='nearest',cmap='magma',vmin=0,vmax=1,aspect='equal')
                if col in [1,3]:boxes_bev(bx,gt,style='--')
                bx.set(xlim=(roi[0],roi[3]),ylim=(roi[1],roi[4]),aspect='equal',
                       xticks=[0,20,40,60,72],yticks=[-6,0,6])
                bx.tick_params(length=2,pad=2)
                if row == len(page)-1: bx.set_xlabel('Forward x (m)',labelpad=2)
                bx.set_ylabel('y (m)',labelpad=1)
                if col == 3:
                    bx.text(1,1.06,f"GT-region means: FG {f['gate_fg_mean']:.3f} / BG {f['gate_bg_mean']:.3f}",
                            transform=bx.transAxes,ha='right',fontsize=7,color='#4a5461')
            ax.text(.01,.02,f"S{f['seq']} / {f['radar_id']}", transform=ax.transAxes,
                    color='white',fontsize=7,bbox=dict(facecolor='black',alpha=.55,edgecolor='none',pad=2))
            data.close()
        for col, title in enumerate(['Camera reference', 'LiDAR BEV + GT reference', 'Predicted gate $g$', 'Same gate + GT reference']):
            pos = gs[0,col].get_position(fig)
            fig.text((pos.x0+pos.x1)/2,.875,title,ha='center',fontweight='bold',fontsize=10,
                     color=MODALITY_INK[col] if col < 2 else '#202939')
        cax = fig.add_axes([.47,.020,.19,.009 if len(page)>1 else .023])
        cb = fig.colorbar(heat,cax=cax,orientation='horizontal',ticks=[0,.25,.5,.75,1])
        cb.ax.tick_params(labelsize=7,length=2,pad=1)
        fig.text(.455,.02,'Predicted gate',ha='right',va='center',fontsize=8)
        fig.legend(handles=[Line2D([0],[0],color='#13b48a',ls='--',lw=1.5,label='GT overlay: reference only')],
                   loc='lower left',bbox_to_anchor=(.065,.005),frameon=False,fontsize=8)
        fig.text(.985,.02,'Full ROI · 0.8 m patches · shared [0,1] scale',ha='right',fontsize=7)
        for suffix in ['png', 'pdf', 'svg']:
            fig.savefig(out/f'{stem}.{suffix}',dpi=190 if suffix=='png' else 160)
        plt.close(fig)
    make(selected,'fig4_objdec_all_weather', (17,13.5))
    # Reflowable single-weather cards, with a less compressed original layout.
    for f in selected:
        fig = plt.figure(figsize=(7.2,6.9))
        gs=fig.add_gridspec(4,1,height_ratios=[2.5,1,1,1],left=.09,right=.97,bottom=.16,top=.93,hspace=.39)
        ax=fig.add_subplot(gs[0]); ax.imshow(camera_image(f)); ax.axis('off')
        ax.set_title(NAMES[f['weather']],fontsize=12,fontweight='bold')
        with np.load(SOURCE/f['archive']) as d:
            roi=d['roi_xyz']; gt=d['gt_boxes']
            for row in [1,2,3]:
                ax=fig.add_subplot(gs[row]); ax.set_facecolor('#101b2b')
                if row==1:
                    pts=lidar_points(f,roi)
                    ax.scatter(pts[:,0],pts[:,1],s=.5,c=lidar_color,alpha=.7,linewidths=0,rasterized=True)
                else: heat=ax.imshow(d['gate'],origin='lower',extent=[0,72,-6.4,6.4],cmap='magma',vmin=0,vmax=1,interpolation='nearest')
                if row in [1,3]:boxes_bev(ax,gt,style='--')
                ax.set(xlim=(0,72),ylim=(-6.4,6.4),aspect='equal',yticks=[-6,0,6],xticks=[0,20,40,60,72])
                ax.set_ylabel('y (m)'); ax.set_title({1:'LiDAR BEV + GT reference',2:'Predicted gate g (from features)',3:'Same gate + GT reference'}[row],fontsize=9,loc='left',pad=2)
                if row==1: ax.title.set_color(MODALITY_INK[1])
                if row==3:ax.set_xlabel('Forward x (m)',labelpad=1)
        cax=fig.add_axes([.34,.060,.4,.018]); fig.colorbar(heat,cax=cax,orientation='horizontal',ticks=[0,.5,1])
        fig.text(.08,.012,f"{f['id']}   GT-region FG/BG = {f['gate_fg_mean']:.3f}/{f['gate_bg_mean']:.3f}",fontsize=8)
        fig.text(.08,.095,'Dashed green boxes: GT added for reference after gate prediction',fontsize=8,color='#386254')
        for suffix in ['png', 'pdf', 'svg']:
            fig.savefig(out/f"fig4_{f['weather']}.{suffix}",dpi=190 if suffix=='png' else 160)
        plt.close(fig)
    save_json(out/'fig4_selection.json',{'frames':selected,'source_manifest_sha256':sha(SOURCE/'manifest.json'),
              'gate_scale':[0,1], 'smoothing':False,'new_inference':False,
              'display_columns':['Camera reference','LiDAR BEV + GT reference','Predicted gate g','Same gate + GT reference'],
              'paired_gate_panels':'Identical complete gate array; only the last panel overlays GT.',
              'GT_role':'Training labels; at visualization time GT provides overlays and post-inference FG/BG grouping only. Original gate export withheld gt_boxes at the fuser boundary.',
              'selection':'One illustrative frame per weather from the pre-existing 21-frame shortlist; inspect camera readability and localized gate response. Prefer visible road over fully obscured camera for heavy snow and sleet. Exclude unstable seq49_rdr00593.',
              'not_representative_statistics':True})
    save_json(out/'fig4_render_validation.json',{
        'scope':'CPU-only Fig.4 clarification; no inference or Fig.5 changes',
        'script_sha256':sha(Path(__file__)),
        'source_npz_sha256':{f['archive']:sha(SOURCE/f['archive']) for f in selected},
        'raw_and_overlay_gate_arrays_identical':True,'gate_color_range':[0,1],
        'gt_overlay_style':'green dashed','GT_reaches_loss_not_gate_in_schematic':True,
        'modality_colors':dict(zip(['Camera','LiDAR','4D Radar'],MODALITY_COLORS)),
        'gate_colormap':'magma; scalar gate magnitude, not modality identity'})
    print('Figure 4 complete',flush=True)


def export_predictions(args):
    os.environ['CUDA_VISIBLE_DEVICES']=args.gpu
    sys.path.insert(0,str(ROOT/'ops'))
    import random
    import numpy as np
    import torch
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0
    from tools.analysis.benchmark_taskdec_inference_260917 import SOURCES
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(.08)
    src = SOURCES['taskdec' if args.model=='objdec' else 'asf']
    selected=[f for f in frames() if f['id']!='seq49_rdr00593']
    out=OUT/'paired_predictions'/args.model; out.mkdir(parents=True,exist_ok=True)
    cfg=out/'inference_config.yml'
    cfg.write_text(f'_BASE_CONFIG_: {str(src[0])!r}\nGENERAL:\n  LOGGING:\n    IS_LOGGING: False\n  RESUME:\n    IS_RESUME: False\nVAL:\n  IS_VALIDATE: False\nOPTIMIZER:\n  NUM_WORKERS: 0\nDATASET:\n  portion: '+json.dumps(sorted({f['seq'] for f in selected},key=int))+'\n')
    pipe=PipelineDetection_v1_0(path_cfg=str(cfg),mode='test')
    pipe.load_dict_model(str(src[1]),is_strict=True)
    pipe.network.eval()
    dataset=pipe.dataset_test
    index={(str(d['meta']['seq']),str(d['meta']['idx']['rdr'])):i for i,d in enumerate(dataset.list_dict_item)}
    info={'model':args.model,'checkpoint':str(src[1]),'checkpoint_sha256':sha(src[1]),'config':str(src[0]),
          'config_sha256':sha(src[0]),'mode':'eval, FP32, standard eager, R+L+C, batch 1',
          'score_display_threshold':.3,'strict_checkpoint_loading':True,'frames':[],'complete':False}
    def hash_inputs(batch):
        result={}
        for k,v in batch.items():
            if isinstance(v,torch.Tensor):
                a=v.detach().cpu().contiguous().numpy()
                result[k]={'shape':list(a.shape),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
        return result
    with torch.no_grad():
        for n,f in enumerate(selected):
            # Fix sample loading RNG identically for both models.
            seed=260919+n; random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
            idx=index[(f['seq'],f['radar_id'])]
            item=dataset[idx]; batch=dataset.collate_fn([item]); gt=batch['gt_boxes'][0].cpu().numpy().copy()
            gt=gt[(gt[:,3]>0)&(gt[:,4]>0)&(gt[:,7]>0)]
            expected=np.load(SOURCE/f['archive'])['gt_boxes']
            assert gt.shape==expected.shape and np.allclose(gt,expected,atol=1e-5),f['id']
            input_hash=hash_inputs(batch)
            batch['avail_feats']=pipe.infer_mode_to_avail_feats('rlc')
            result=pipe.network(batch)
            pred=result['pred_dicts'][0]
            boxes=pred['pred_boxes'].detach().cpu().numpy().copy()
            scores=pred['pred_scores'].detach().cpu().numpy().copy()
            labels=pred['pred_labels'].detach().cpu().numpy().copy()
            assert np.isfinite(boxes).all() and np.isfinite(scores).all()
            np.savez_compressed(out/f"{f['id']}.npz",boxes=boxes,scores=scores,labels=labels,gt=gt)
            entry={'id':f['id'],'dataset_index_within_portion':idx,'seed':seed,'num_gt':len(gt),
                   'num_predictions_above_03':int(((scores>.3)&(labels==1)).sum()),'input_tensors':input_hash}
            info['frames'].append(entry);info['peak_allocated_mib']=torch.cuda.max_memory_allocated()/2**20
            save_json(out/'manifest.json',info)
            print(f"{args.model} {n+1}/{len(selected)} {f['id']}: GT={len(gt)}, pred@.3={entry['num_predictions_above_03']}",flush=True)
            meta=item['meta']; dataset.list_dict_item[idx]={'meta':meta}
            del result,batch,item
    info['complete']=True; save_json(out/'manifest.json',info)
    print('COMPLETE '+args.model,flush=True)


def paired_analysis():
    import numpy as np
    import cv2
    records=[]; sources={}; tensor_checks=[]
    for model in ['asf','objdec']:
        m=json.loads((OUT/'paired_predictions'/model/'manifest.json').read_text())
        assert m['complete'] and len(m['frames'])==20
        sources[model]=m
    src_frames={k:{f['id']:f for f in m['frames']} for k,m in sources.items()}
    for f in frames():
        if f['id']=='seq49_rdr00593':continue
        ha=src_frames['asf'][f['id']]['input_tensors'];hb=src_frames['objdec'][f['id']]['input_tensors']
        assert ha==hb, ('different input tensors',f['id'],[k for k in set(ha)|set(hb) if ha.get(k)!=hb.get(k)])
        tensor_checks.append({'id':f['id'],'all_input_tensor_hashes_equal':True,'keys':sorted(ha)})
        item={'frame':f,'models':{}}
        for model in ['asf','objdec']:
            with np.load(OUT/'paired_predictions'/model/f"{f['id']}.npz",allow_pickle=False) as d:
                keep=(d['scores']>.3)&(d['labels']==1)
                boxes=d['boxes'][keep];scores=d['scores'][keep];gt=d['gt']
            assert np.isfinite(boxes).all() and np.isfinite(scores).all()
            ious=np.zeros((len(gt),len(boxes)),dtype=float)
            bevs=np.zeros_like(ious)
            for gi,g in enumerate(gt):
                for pi,p in enumerate(boxes):
                    inter=float(cv2.intersectConvexConvex(corners(g).astype('float32'),corners(p).astype('float32'))[0])
                    a,b=g[3]*g[4],p[3]*p[4]
                    bevs[gi,pi]=inter/max(a+b-inter,1e-9)
                    height=max(0,min(g[2]+g[5]/2,p[2]+p[5]/2)-max(g[2]-g[5]/2,p[2]-p[5]/2))
                    volume=inter*height
                    ious[gi,pi]=volume/max(a*g[5]+b*p[5]-volume,1e-9)
            best=ious.max(axis=1) if len(boxes) else np.zeros(len(gt))
            item['models'][model]={'boxes':boxes.tolist(),'scores':scores.tolist(),'gt':gt.tolist(),
                                  'iou3d_matrix':ious.tolist(),'ioubev_matrix':bevs.tolist(),
                                  'best_iou3d_per_gt':best.tolist(),'mean_best_iou3d':float(best.mean()),
                                  'num_predictions':len(boxes)}
        assert np.array_equal(item['models']['asf']['gt'],item['models']['objdec']['gt'])
        item['delta_mean_best_iou3d']=item['models']['objdec']['mean_best_iou3d']-item['models']['asf']['mean_best_iou3d']
        records.append(item)
    save_json(OUT/'fig5_candidate_metrics.json',{'records':records,'input_checks':tensor_checks,
        'metric_note':'Best geometric 3D IoU to any retained Sedan prediction per GT, averaged within the selected frame. Descriptive figure audit, not AP or official TP matching.',
        'confidence':.3,'filter':'scores > 0.3; class=Sedan. No additional model-dependent filtering.',
        'sources':{k:{a:m[a] for a in ['checkpoint','checkpoint_sha256','config','config_sha256','peak_allocated_mib']} for k,m in sources.items()}})
    with (OUT/'fig5_candidate_metrics.csv').open('w') as stream:
        fields=['id','weather','num_gt','asf_predictions','objdec_predictions','asf_mean_best_iou3d','objdec_mean_best_iou3d','delta']
        writer=csv.DictWriter(stream,fields);writer.writeheader()
        for r in records:
            f=r['frame'];a=r['models']['asf'];o=r['models']['objdec']
            writer.writerow(dict(id=f['id'],weather=f['weather'],num_gt=f['num_gt'],asf_predictions=a['num_predictions'],objdec_predictions=o['num_predictions'],asf_mean_best_iou3d=a['mean_best_iou3d'],objdec_mean_best_iou3d=o['mean_best_iou3d'],delta=r['delta_mean_best_iou3d']))
    for r in sorted(records,key=lambda x:-x['delta_mean_best_iou3d']):
        a,o=r['models']['asf'],r['models']['objdec']
        print(r['frame']['id'],r['frame']['weather'],f"GT{len(a['gt'])} Pred{a['num_predictions']}/{o['num_predictions']} IoU {a['mean_best_iou3d']:.3f}/{o['mean_best_iou3d']:.3f} delta={r['delta_mean_best_iou3d']:+.3f}")
    return records


def camera_params(seq):
    import cv2
    import numpy as np
    import pickle
    import zipfile
    import yaml
    with zipfile.ZipFile(ROOT/'resources/cam_calib/calib_seq.zip') as z:
        c=yaml.safe_load(z.read(f'calib_seq/seq_{int(seq):02d}/cam_1.yml'))
    k=np.array([[c['fx'],0,c['px']],[0,c['fy'],c['py']],[0,0,1.]])
    distortion=np.array([c[f'k{i}'] for i in range(1,6)])
    params=pickle.loads((ROOT/f'resources/cam_calib/T_params_seq/{seq}').read_bytes())['front0']
    new,_=cv2.getOptimalNewCameraMatrix(k,distortion,(1280,720),0)
    assert np.allclose(new,params['camera_intrinsics'][:3,:3],atol=1e-6)
    assert np.allclose(params['radar2image'],params['camera_intrinsics']@params['radar2camera'])
    return k,distortion,params['radar2camera']


def box_corners3d(box):
    import numpy as np
    xy=corners(box)
    return np.concatenate([np.column_stack([xy,np.full(4,box[2]-box[5]/2)]),
                           np.column_stack([xy,np.full(4,box[2]+box[5]/2)])])


def camera_boxes(ax, boxes, params, color, style='-',lw=1):
    import numpy as np
    import cv2
    k,distortion,t=params
    edges=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    for b in boxes:
        c=box_corners3d(b)@t[:3,:3].T+t[:3,3]
        for i,j in edges:
            line=c[[i,j]].copy()
            # Clip in camera space before perspective division.
            if (line[:,2]<=.1).all():continue
            if (line[:,2]<=.1).any():
                bad=int(np.argmin(line[:,2]));other=1-bad
                fraction=(.1-line[bad,2])/(line[other,2]-line[bad,2])
                line[bad]+=fraction*(line[other]-line[bad])
            # Sample curved distorted edges, not a rectified-camera projection
            # incorrectly overlaid on the raw image.
            pts=line[0]+np.linspace(0,1,12)[:,None]*(line[1]-line[0])
            uv=cv2.projectPoints(pts,np.zeros(3),np.zeros(3),k,distortion)[0].reshape(-1,2)
            ax.plot(uv[:,0],uv[:,1],color=color,linestyle=style,lw=lw,clip_on=True)


def render5(args):
    import numpy as np
    from matplotlib.lines import Line2D
    from tools.analysis.export_taskdec_bev_gate import camera_image,lidar_points
    from matplotlib.backends.backend_pdf import PdfPages
    plt=plotting()
    records=json.loads((OUT/'fig5_candidate_metrics.json').read_text())['records']
    lookup={r['frame']['id']:r for r in records}
    selected=[lookup[k] for k in args.select.split(',')] if args.select else records
    projection_checks=[]
    # One row = same scene. Camera panels show full front0; BEV is identical
    # across methods, with a shared local detail window below the full ROI.
    def make(page, stem, pdf=None):
        fig=plt.figure(figsize=(15,2.6*len(page)+.85))
        gs=fig.add_gridspec(len(page),4,width_ratios=[1,1,1.06,1.06],
                            left=.055,right=.99,bottom=max(.085,.75/(2.6*len(page)+.85)),
                            top=.90,wspace=.13,hspace=.32)
        for row,r in enumerate(page):
            f=r['frame'];a=r['models']['asf'];o=r['models']['objdec'];gt=np.array(a['gt'])
            params=camera_params(f['seq']);img=camera_image(f)
            pts=lidar_points(f,np.array([0,-6.4,-2,72,6.4,6]))
            aa=np.array(a['best_iou3d_per_gt']);oo=np.array(o['best_iou3d_per_gt'])
            gi=int(np.argmax(np.abs(oo-aa)));g=gt[gi]
            # Shared zoom depends on GT geometry, never shifted to favour a model.
            xl=max(0,float(g[0])-6);xh=min(72,float(g[0])+6)
            yl=max(-6.4,float(g[1])-3);yh=min(6.4,float(g[1])+3)
            for col,model in enumerate(['asf','objdec']):
                data=r['models'][model];boxes=np.asarray(data['boxes']).reshape(-1,7)
                ax=fig.add_subplot(gs[row,col]);ax.imshow(img)
                camera_boxes(ax,boxes,params,'#ff8b21',lw=1.05)
                camera_boxes(ax,gt,params,'#21efb0',style='--',lw=.9)
                ax.set(xlim=(0,1280),ylim=(720,0));ax.axis('off')
                if args.select:
                    import cv2
                    from matplotlib.patches import Rectangle
                    k,dist,t=params
                    gc=box_corners3d(g)@t[:3,:3].T+t[:3,3]
                    if (gc[:,2]>.1).all():
                        uv=cv2.projectPoints(gc,np.zeros(3),np.zeros(3),k,dist)[0].reshape(-1,2)
                        center=(uv.min(axis=0)+uv.max(axis=0))/2
                        width=max(160,float(np.ptp(uv[:,0]))*2,float(np.ptp(uv[:,1]))*2*16/9)
                        width=min(1280,width);height=width*9/16
                        u0=float(np.clip(center[0]-width/2,0,1280-width));v0=float(np.clip(center[1]-height/2,0,720-height))
                        ax.add_patch(Rectangle((u0,v0),width,height,fill=False,color='white',ls=':',lw=.6))
                        inset=ax.inset_axes([.01,.63,.38,.35]);inset.imshow(img)
                        camera_boxes(inset,boxes,params,'#ff8b21',lw=1.0)
                        camera_boxes(inset,gt,params,'#21efb0',style='--',lw=.85)
                        inset.set(xlim=(u0,u0+width),ylim=(v0+height,v0),xticks=[],yticks=[])
                        for sp in inset.spines.values():sp.set_color('white');sp.set_linewidth(.8)
                        inset.text(.03,.04,'Detail',transform=inset.transAxes,fontsize=6,color='white',
                                   bbox=dict(facecolor='black',edgecolor='none',alpha=.6,pad=1))
                ax.text(.015,.025,f"S{f['seq']} / {f['radar_id']}",transform=ax.transAxes,color='white',fontsize=7,
                        bbox=dict(facecolor='black',edgecolor='none',alpha=.65,pad=2))
                if col==0:
                    ax.text(-.05,.5,NAMES[f['weather']],transform=ax.transAxes,rotation=90,
                            ha='right',va='center',fontweight='bold',fontsize=10)
                inner=gs[row,col+2].subgridspec(2,1,height_ratios=[.7,1.3],hspace=.18)
                for sub in [0,1]:
                    bx=fig.add_subplot(inner[sub]);bx.set_facecolor('#101b2b')
                    bx.scatter(pts[:,0],pts[:,1],s=.5 if sub==0 else 1.3,c='#a8b9cd',alpha=.65,linewidths=0,rasterized=True)
                    boxes_bev(bx,boxes,color='#ff8b21',lw=1.1)
                    boxes_bev(bx,gt,color='#21efb0',style='--',lw=1)
                    bx.set(xlim=(0,72) if sub==0 else (xl,xh),ylim=(-6.4,6.4) if sub==0 else (yl,yh),aspect='equal')
                    if sub==0:
                        from matplotlib.patches import Rectangle
                        bx.add_patch(Rectangle((xl,yl),xh-xl,yh-yl,fill=False,color='#d3d9e2',lw=.6,linestyle=':'))
                        bx.set_xticks([0,36,72]);bx.set_yticks([])
                    else:
                        bx.set_xticks([round(xl,1),round(xh,1)]);bx.set_yticks([round(yl,1),round(yh,1)])
                        value=data['best_iou3d_per_gt'][gi]
                        bx.text(.5,-.24,f'Selected GT: best 3D IoU {value:.2f}',transform=bx.transAxes,
                                ha='center',fontsize=8,color='#3c4858')
                    bx.tick_params(labelsize=6,pad=1,length=2)
            projection_checks.append({'id':f['id'],'camera_K_matches_rectified_T_params':True,
                                      'raw_image_distortion_model_applied':True,'zoom_xy':[xl,xh,yl,yh],
                                      'zoom_gt_index':gi})
        titles=['ASF (official) · camera','ObjDec · camera','ASF · BEV / detail','ObjDec · BEV / detail']
        for col,title in enumerate(titles):
            p=gs[0,col].get_position(fig);fig.text((p.x0+p.x1)/2,.954,title,ha='center',fontsize=11,fontweight='bold')
        fig.legend(handles=[Line2D([0],[0],color='#10b887',lw=1.4,ls='--',label='Sedan GT'),
                            Line2D([0],[0],color='#ef841b',lw=1.5,label='Prediction (score > 0.3)')],
                   loc='lower left',bbox_to_anchor=(.06,.01),frameon=False,ncol=2,fontsize=8)
        fig.text(.99,.025,'Same scene, inputs and display threshold · full BEV: x 0–72 m, y ±6.4 m',ha='right',fontsize=8)
        if stem:
            fig.savefig(OUT/f'{stem}.png',dpi=190);fig.savefig(OUT/f'{stem}.pdf',dpi=160)
        if pdf is not None:pdf.savefig(fig,dpi=140)
        plt.close(fig)
    if args.select:
        make(selected,args.stem)
        save_json(OUT/f'{args.stem}_selection.json',{'frames':[r['frame']['id'] for r in selected],
            'projection_checks':projection_checks,'GT_color':'green dashed','prediction_color':'orange',
            'selection_note':'Illustrative selected cases from the fixed gate candidate pool; best 3D IoU is descriptive geometry, not AP. Full candidate contact sheet retained.'})
    else:
        with PdfPages(OUT/'fig5_all_candidates.pdf') as pdf:
            for start in range(0,len(records),4):make(records[start:start+4],f'fig5_candidates_{start//4+1}',pdf)
        save_json(OUT/'fig5_projection_checks.json',projection_checks)
    print('Figure 5 rendered',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['fig4','export','analyze','fig5'])
    ap.add_argument('--model',choices=['asf','objdec']);ap.add_argument('--gpu',default='2')
    ap.add_argument('--select',default='')
    ap.add_argument('--stem',default='fig5_asf_objdec_detection_draft')
    a=ap.parse_args();os.chdir(ROOT)
    if a.mode=='fig4':figure4()
    elif a.mode=='export':export_predictions(a)
    elif a.mode=='analyze':paired_analysis()
    else:render5(a)


if __name__=='__main__':main()
