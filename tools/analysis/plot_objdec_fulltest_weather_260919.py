#!/usr/bin/env python3
"""CPU-only full-test weather figure candidates with explicit sampling semantics."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from plot_objdec_pca_260919 import (FEATURES,TITLES,MODALITIES,COLORS,MARKERS,
    WEATHERS,LABELS,style,save,limits,density_outline,plt,Line2D,MaxNLocator)

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'analysis_exports/objdec_fulltest_weather_260919'
OUT=SOURCE/'paper_visuals'


def load():
    status=json.loads((SOURCE/'status.json').read_text())
    assert status['phase']=='complete' and status['completed']==10065
    parts=[];paths=sorted((SOURCE/'chunks').glob('frames_*.npz'))
    keys=['dataset_index','weather','seq','means','num_foreground','paired_cosine','within_frame_scatter']
    for path in paths:
        with np.load(path) as z:parts.append({k:z[k] for k in keys})
    data={k:np.concatenate([p[k] for p in parts]) for k in keys}
    order=np.argsort(data['dataset_index']);data={k:v[order] for k,v in data.items()}
    assert np.array_equal(data['dataset_index'],np.arange(10065))
    assert (data['num_foreground']>0).all() and np.isfinite(data['means']).all()
    with np.load(SOURCE/'frame_mean_pca_basis.npz') as z:basis={k:z[k] for k in z.files}
    return data,basis,paths


def plot_frame_grid(data,basis,weathers=None,name='objdec_fulltest_frame_pca_normal_heavysnow'):
    weathers=['normal','heavysnow'] if weathers is None else list(weathers)
    rng=np.random.default_rng(20260919)
    # Preserve the existing normal/heavy-snow selection in both figure versions.
    chosen={w:rng.choice(np.flatnonzero(data['weather']==w),400,replace=False)
            for w in ['normal','heavysnow']}
    for w in weathers:
        if w not in chosen:
            ids=np.flatnonzero(data['weather']==w)
            chosen[w]=np.random.default_rng(20260919+WEATHERS.index(w)).choice(
                ids,min(400,len(ids)),replace=False)
    nrows=len(weathers)
    fig,axes=plt.subplots(nrows,3,figsize=(12.5,2.65*nrows+.9),squeeze=False)
    for j,f in enumerate(FEATURES):
        coords=(data['means'][:,j].astype(float)-basis[f+'_mean'])@basis[f+'_components'].T
        lo,hi=limits(coords[np.isin(data['weather'],weathers)].reshape(-1,2))
        for i,w in enumerate(weathers):
            ax=axes[i,j];ids=np.flatnonzero(data['weather']==w)
            for m,(color,marker) in enumerate(zip(COLORS,MARKERS)):
                all_points=coords[ids,m]
                density_outline(ax,all_points,color)
                ax.scatter(*coords[chosen[w],m].T,s=20,c=color,marker=marker,alpha=.42,
                    edgecolors='white',linewidths=.2,zorder=3)
                mu=all_points.mean(0)
                ax.scatter(*mu,s=100,c=color,marker=marker,edgecolors='#202939',linewidths=1.15,zorder=5)
            ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_aspect('equal',adjustable='box')
            ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(4))
            ax.grid(alpha=.12,linewidth=.5);ax.tick_params(labelsize=8)
            r=basis[f+'_explained']*100
            ax.set_xlabel(f'PC1 ({r[0]:.1f}%)')
            ax.set_ylabel(f'PC2 ({r[1]:.1f}%)')
            if i==0:ax.set_title(TITLES[j],fontsize=11,fontweight='bold',pad=12)
    handles=[Line2D([],[],color=c,marker=m,linestyle='',markersize=7,label=n)
             for n,c,m in zip(MODALITIES,COLORS,MARKERS)]
    handles.append(Line2D([],[],marker='o',color='white',markeredgecolor='#202939',markersize=9,
                          linestyle='',label='All-frame center'))
    fig.legend(handles=handles,ncol=4,loc='upper center',frameon=False,bbox_to_anchor=(.55,.998))
    fig.text(.55,.009,'Each point: one frame mean | Display: up to 400 frames/weather | Centers and contours: all frames',
             ha='center',fontsize=9,color='#475467')
    fig.tight_layout(rect=(.115,.14/fig.get_figheight(),1,1-.45/fig.get_figheight()),h_pad=1.7,w_pad=1.9)
    # A horizontal label for each complete row is easier to read than a rotated y label.
    for i,w in enumerate(weathers):
        p=axes[i,0].get_position()
        fig.text(.012,(p.y0+p.y1)/2,LABELS[WEATHERS.index(w)]+'\n'+f'n = {int((data["weather"]==w).sum()):,}',
                 ha='left',va='center',fontsize=11,fontweight='bold',color='#344054')
    save(fig,OUT,name)
    ids_name='display_frame_ids.npz' if nrows==2 else 'display_frame_ids_all_weather.npz'
    np.savez_compressed(OUT/ids_name,**{w:data['dataset_index'][chosen[w]] for w in weathers})


def cosine_heatmaps(data):
    fig,axes=plt.subplots(1,3,figsize=(10.8,4.5),sharey=True)
    matrices=[]
    for j in range(3):
        matrices.append(np.asarray([data['paired_cosine'][data['weather']==w,j,:].astype(float).mean(0)
                                    for w in WEATHERS]))
    for j,ax in enumerate(axes):
        mat=matrices[j]
        im=ax.imshow(mat,cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
        ax.set_xticks(range(3),['C–L','C–R','L–R'])
        ax.set_yticks(range(7),[f'{label}  ({int((data["weather"]==w).sum()):,})' for w,label in zip(WEATHERS,LABELS)])
        ax.set_title(TITLES[j],fontsize=10,fontweight='bold',pad=10)
        ax.tick_params(length=0)
        for r in range(7):
            for c in range(3):
                ax.text(c,r,f'{mat[r,c]:.3f}',ha='center',va='center',fontsize=10,
                        color='white' if abs(mat[r,c])>.65 else '#202939')
        ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,7,1),minor=True)
        ax.grid(which='minor',color='white',linewidth=1.1);ax.tick_params(which='minor',length=0)
        for spine in ax.spines.values():spine.set_visible(False)
    fig.subplots_adjust(left=.19,right=.92,bottom=.18,top=.86,wspace=.14)
    cax=fig.add_axes([.94,.2,.015,.65]);fig.colorbar(im,cax=cax,label='Cosine similarity')
    fig.text(.54,.055,'256-D foreground patch cosine, averaged per frame then per weather\nC: Camera   L: LiDAR   R: 4D Radar | Parentheses: frame counts',
             ha='center',fontsize=9,color='#475467')
    save(fig,OUT,'objdec_fulltest_weather_cosine_pairs')


def centroid_statistics(data):
    rows=[];centers=[]
    means=data['means'].astype(float)
    for w in WEATHERS:
        mask=data['weather']==w;centers.append(means[mask].mean(0))
    centers=np.array(centers)
    normal=centers[0]
    for wi,w in enumerate(WEATHERS):
        mask=data['weather']==w
        for j,f in enumerate(FEATURES):
            for m,name in enumerate(MODALITIES):
                a,b=normal[j,m],centers[wi,j,m]
                cos=float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
                x=means[mask,j,m]
                rows.append(dict(weather=w,feature=f,modality=name,frames=int(mask.sum()),
                    sequences=len(np.unique(data['seq'][mask])),centroid_norm=float(np.linalg.norm(b)),
                    centroid_L2_from_normal=float(np.linalg.norm(b-a)),centroid_cos_from_normal=cos,
                    centroid_cos_distance_from_normal=max(0.,1-cos),
                    frame_mean_rms_spread=float(np.sqrt(np.mean(np.sum((x-b)**2,axis=1)))),
                    mean_within_frame_scatter=float(data['within_frame_scatter'][mask,j,m].mean())))
    with (OUT/'weather_centroid_statistics.csv').open('w') as stream:
        wr=csv.DictWriter(stream,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
    np.savez_compressed(OUT/'weather_centroids_256d.npz',centers=centers,weather=np.array(WEATHERS),
                        feature=np.array(FEATURES),modality=np.array(MODALITIES))
    mat=np.array([[r['centroid_cos_distance_from_normal']*100 for r in rows
                   if r['weather']=='heavysnow' and r['feature']==f] for f in FEATURES])
    fig,ax=plt.subplots(figsize=(6.0,3.6))
    im=ax.imshow(mat,cmap='Blues',vmin=0,vmax=6,aspect='auto')
    ax.set_xticks(range(3),MODALITIES);ax.set_yticks(range(3),['Input','Shared','Modality-specific'])
    ax.set_title('Normal → heavy snow: centroid angular change',fontweight='bold',fontsize=11,pad=15)
    for i in range(3):
        for j in range(3):
            label=f'{mat[i,j]:.3f}' if mat[i,j]>=.001 else '<0.001'
            ax.text(j,i,label,ha='center',va='center',fontsize=12,color='white' if mat[i,j]>3 else '#202939')
    ax.tick_params(length=0)
    for spine in ax.spines.values():spine.set_visible(False)
    fig.colorbar(im,ax=ax,pad=.04,label='100 × (1 − cosine similarity)')
    fig.text(.5,.02,'Computed in 256-D; normal n=4,309, heavy snow n=1,098\nObservational weather groups; smaller change alone does not establish robustness.',
             ha='center',fontsize=8,color='#475467')
    fig.tight_layout(rect=(0,.12,1,1));save(fig,OUT,'objdec_fulltest_normal_snow_centroid_shift')
    return rows


def main():
    OUT.mkdir(exist_ok=True);style()
    data,basis,paths=load()
    plot_frame_grid(data,basis)
    plot_frame_grid(data,basis,WEATHERS,'objdec_fulltest_frame_pca_all_weather')
    cosine_heatmaps(data);rows=centroid_statistics(data)
    manifest=dict(frames=len(data['weather']),sequences=len(np.unique(data['seq'])),
        foreground_patch_locations=int(data['num_foreground'].sum()),source=str(SOURCE),seed=20260919,
        frame_pca='Existing fixed basis fitted to frame means with equal weather and modality weights; no refitting for appearance.',
        statistics='All foreground patches per frame; equal frame weights within weather. No frame exclusion or outlier clipping.',
        display='Up to 400 randomly selected frames per shown weather (all 383 overcast frames), identical across feature and modality panels; all-frame centers and KDE contours. Normal/heavy-snow selected frame IDs are preserved between figure versions.',
        frame_pca_figures=['objdec_fulltest_frame_pca_normal_heavysnow','objdec_fulltest_frame_pca_all_weather'],
        weather_row_labels={w:dict(label=label,frames=int((data['weather']==w).sum())) for w,label in zip(WEATHERS,LABELS)},
        density='Approximately 80% KDE mass contours, not confidence intervals.',
        main_evidence='Higher cross-modal cosine in common than unique across all weather. LiDAR unique centroid changes more between normal and heavy snow.',
        limitations=['PCA cannot by itself establish semantic disentanglement or detection benefit.',
                    'Camera common/unique vary very little; small weather shifts are not by themselves evidence of useful invariance.',
                    'Weather correlates with sequence, scene and foreground composition; no causal weather attribution.',
                    'Per-frame mean PCA differs from the existing sampled-patch PCA. Cross-column L2 distances have different feature scales.'],
        sources_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in paths+[SOURCE/'frame_mean_pca_basis.npz',SOURCE/'weather_statistics.csv',Path(__file__).resolve()]})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(OUT)


if __name__=='__main__':main()
