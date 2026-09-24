#!/usr/bin/env python3
"""Re-render existing numerical figures; preserve observations and PCA bases."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import plot_objdec_pca_260919 as patch
import plot_objdec_fulltest_weather_260919 as full
import plot_objdec_direct_similarity_260919 as similarity
import make_objdec_fig4_fig5_260919 as gate
from objdec_plot_palette import MODALITY_COLORS, MODALITY_INK, REPRESENTATION_COLORS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'analysis_exports/objdec_visuals_blue_green_purple_260923'
PATCH_SOURCE = ROOT/'analysis_exports/taskdec_patch_pca_weather_260909/taskdec_patch_states_pca.npz'
PATCH_OLD = ROOT/'analysis_exports/objdec_pca_redesign_260919'
FULL_OLD = full.OUT
GATE_OLD = gate.OUT


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(2**20), b''):
            h.update(part)
    return h.hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n')


def inset(ax, data, feature, weather):
    """Existing patch-level PCA, with the same frame/patch display selection."""
    chosen = patch.selected_pairs(data, weather, 20260919+patch.WEATHERS.index(weather))
    coords = data[feature+'_pca']
    mask = (data[feature+'_foreground']==1) & (data[feature+'_weather']==weather)
    frames, patches = data[feature+'_frame_idx'], data[feature+'_patch_idx']
    lo, hi = patch.limits(coords[mask])
    for name, color, marker in zip(patch.MODALITIES, MODALITY_COLORS, patch.MARKERS):
        mod_mask = mask & (data[feature+'_modality']==name)
        ids = [int(k) for k in np.flatnonzero(mod_mask)
               if (int(frames[k]), int(patches[k])) in chosen]
        # No recentering by modality, clipping, axis flips, or PCA refitting.
        ax.scatter(*coords[ids].T, c=color, marker=marker, s=18, alpha=.72,
                   edgecolors='white', linewidths=.2)
    ax.set(xlim=(lo[0],hi[0]), ylim=(lo[1],hi[1]), xticks=[], yticks=[])
    ax.set_aspect('equal', adjustable='box')
    for key in ['left','bottom']:
        ax.spines[key].set_color('#AAB2BE');ax.spines[key].set_linewidth(.65)
    ax.set_xlabel('PC1', fontsize=7, labelpad=1)
    ax.set_ylabel('PC2', fontsize=7, labelpad=1)
    symbol = r'$c_m^p$' if feature=='common' else r'$u_m^p$'
    ax.set_title(('Shared  ' if feature=='common' else 'Specific  ')+symbol,
                 fontsize=10, fontweight='bold', pad=6)


def insets(data, out):
    out.mkdir(exist_ok=True)
    files=[]
    for w in ['normal','heavysnow']:
        for f in ['common','unique']:
            fig, ax = plt.subplots(figsize=(2.65,2.1))
            inset(ax,data,f,w)
            fig.tight_layout(pad=.55)
            stem=f'architecture_{f}_pca_{w}'
            for suffix in ['png','pdf','svg']:
                fig.savefig(out/f'{stem}.{suffix}',dpi=300,bbox_inches='tight',transparent=True)
            plt.close(fig);files.append(stem)
        fig, axes = plt.subplots(1,2,figsize=(5.6,2.75))
        for ax,f in zip(axes,['common','unique']):inset(ax,data,f,w)
        handles=[Line2D([],[],c=c,marker=m,linestyle='',markersize=5,label=n)
                 for n,c,m in zip(patch.MODALITIES,MODALITY_COLORS,patch.MARKERS)]
        fig.legend(handles=handles,ncol=3,loc='lower center',bbox_to_anchor=(.5,.005),
                   frameon=False,fontsize=8)
        fig.suptitle(f'{patch.LABELS[patch.WEATHERS.index(w)]} · foreground patch PCA',
                     fontsize=9,color='#475467',y=.99)
        fig.tight_layout(rect=(0,.11,1,.96),pad=.6)
        stem=f'architecture_shared_specific_pca_{w}'
        patch.save(fig,out,stem);files.append(stem)
    write(out/'manifest.json',dict(source=str(PATCH_SOURCE),source_sha256=sha(PATCH_SOURCE),
        statistical_unit='Selected foreground patch, not one physical token in the forward graph.',
        scope='24 sampled frames per weather from the existing 168-frame export; not full-test frame-mean PCA.',
        coordinates='Existing exported PCA coordinates. Separate PCA basis for each representation; no refit or per-modality shifts.',
        selection='Same fixed frame/patch IDs as the recolored patch-PCA figures; up to 6 patches per frame and modality.',
        display='Independent axis limits by representation, all foreground points included in limits; no quantitative cross-panel distance ratio.',
        intended_use='Visualization insets attached with dashed lines to c/u; solid arrows continue to carry high-dimensional c/u.',
        files=files,colors=dict(zip(patch.MODALITIES,MODALITY_COLORS))))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',choices=['all','pca','gate'],default='all')
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    selection={x['id']:x for x in gate.frames()}
    sources=[PATCH_SOURCE,full.SOURCE/'frame_mean_pca_basis.npz']
    sources+=sorted((full.SOURCE/'chunks').glob('frames_*.npz'))
    sources+=[gate.SOURCE/selection[k]['archive'] for k in gate.SELECT4]
    before={str(p.relative_to(ROOT)):sha(p) for p in sources}
    comparisons={}
    if args.only in ['all','pca']:
        print('Rendering sampled-patch PCA...',flush=True)
        target=OUT/'sampled_patch_pca';target.mkdir(exist_ok=True)
        old_args=sys.argv
        sys.argv=[patch.__file__,'--npz',str(PATCH_SOURCE),'--out-dir',str(target)]
        try:patch.main()
        finally:sys.argv=old_args
        name='sampled_high_dimensional_cosine.csv'
        comparisons[name]=(target/name).read_bytes()==(PATCH_OLD/name).read_bytes()
        with np.load(PATCH_SOURCE) as z:data={k:z[k] for k in z.files}
        insets(data,OUT/'architecture_insets');del data
        print('Rendering full-test PCA and high-dimensional summaries...',flush=True)
        full.OUT=OUT/'fulltest';full.main()
        print('Rendering direct similarity figures...',flush=True)
        similarity.OUT=full.OUT;similarity.main()
        for name in ['weather_centroid_statistics.csv','direct_similarity_distribution_statistics.csv']:
            comparisons[name]=(full.OUT/name).read_bytes()==(FULL_OLD/name).read_bytes()
        for name in ['display_frame_ids.npz','display_frame_ids_all_weather.npz']:
            with np.load(full.OUT/name) as a, np.load(FULL_OLD/name) as b:
                comparisons[name]=(set(a.files)==set(b.files) and
                                   all(np.array_equal(a[k],b[k]) for k in a.files))
        for folder,name in [(target,'plot_manifest.json'),(full.OUT,'manifest.json'),
                            (full.OUT,'direct_similarity_manifest.json')]:
            record=json.loads((folder/name).read_text())
            record['render_revision']=dict(date='2026-09-23',
                modality_colors=dict(zip(patch.MODALITIES,MODALITY_COLORS)),
                representation_colors=dict(zip(['Input','Shared','Specific'],REPRESENTATION_COLORS)),
                driver_sha256=sha(Path(__file__).resolve()),
                scope='Presentation only; original cached numerical data and projection are unchanged.')
            write(folder/name,record)
    if args.only in ['all','gate']:
        print('Rendering seven-weather gate panels...',flush=True)
        target=OUT/'gate';gate.figure4(out_dir=target)
        old=json.loads((GATE_OLD/'fig4_selection.json').read_text())
        new=json.loads((target/'fig4_selection.json').read_text())
        comparisons['gate_frames_and_metadata']=new['frames']==old['frames']
        comparisons['gate_scale_and_smoothing']=(new['gate_scale']==old['gate_scale'] and
                                               new['smoothing']==old['smoothing'])
    assert all(comparisons.values()),comparisons
    after={str(p.relative_to(ROOT)):sha(p) for p in sources}
    assert before==after,'Source data changed while rendering'
    artifacts=[p for p in OUT.rglob('*') if p.suffix in ['.png','.pdf','.svg']]
    # Three deliverable formats for each figure, including the individual cards.
    for p in artifacts:
        assert all(p.with_suffix(s).is_file() for s in ['.png','.pdf','.svg']),p
    write(OUT/f'validation_{args.only}.json',dict(passed=True,checks=comparisons,
        source_sha256=before,source_arrays_unchanged=True,new_inference=False,
        pca_refitted=False,artifacts=len(artifacts),figure_groups=len(artifacts)//3,
        artifact_bytes=sum(p.stat().st_size for p in artifacts)))
    write(OUT/'palette.json',dict(reference=str(ROOT/'ChatGPT Image 2026年9月15日 23_53_07.png'),
        note='Flat print colors interpreted from the blue/green/purple reference; not gradient pixel averages.',
        modality_colors=dict(zip(patch.MODALITIES,MODALITY_COLORS)),
        modality_label_colors=dict(zip(patch.MODALITIES,MODALITY_INK)),
        representation_colors=dict(zip(['Input','Shared','Specific'],REPRESENTATION_COLORS)),
        continuous_scales='Cosine, centroid distance, and gate retain their original quantitative color scales.'))
    print(json.dumps(dict(complete=True,checks=comparisons,figure_groups=len(artifacts)//3,
                         artifact_mib=sum(p.stat().st_size for p in artifacts)/2**20)),flush=True)


if __name__=='__main__':main()
