"""Render completed frame-level diagnostics without selecting favorable groups."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent
rows=list(csv.DictReader((OUT/'frame_correspondence_all_seeds.csv').open()))
features=['raw','shared','specific'];pairs=['C-L','C-R','L-R']
summaries=[]
fig,axes=plt.subplots(2,3,figsize=(11.4,6),sharey='row',constrained_layout=True)
for j,feature in enumerate(features):
    for i,centering in enumerate(['uncentered','weather_centered']):
        ax=axes[i,j];x=np.arange(3)
        values=[]
        for pair in pairs:
            group=[r for r in rows if r['weather']=='all' and r['feature']==feature and r['pair']==pair and r['centering']==centering]
            rec=dict(feature=feature,pair=pair,centering=centering,seeds=len(group),
                retained_pairs_min=min(int(r['pairs']) for r in group),retained_pairs_max=max(int(r['pairs']) for r in group))
            for name in ['matched','mismatched','gap']:
                v=np.array([float(r[name]) for r in group]);rec[name]=float(v.mean());rec[name+'_min']=float(v.min());rec[name+'_max']=float(v.max())
            summaries.append(rec);values.append(rec)
        for name,offset,color,label in [('matched',-.18,'#22719b','Same frame'),('mismatched',.18,'#b2b7be','Cross-sequence')]:
            mean=np.array([r[name] for r in values]);lo=mean-np.array([r[name+'_min'] for r in values]);hi=np.array([r[name+'_max'] for r in values])-mean
            ax.bar(x+offset,mean,.34,color=color,label=label,yerr=np.stack([lo,hi]),capsize=3,error_kw={'lw':.8})
        ax.set_xticks(x);ax.set_xticklabels(pairs);ax.axhline(0,color='#8b949e',lw=.6)
        ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
        if i==0:ax.set_title(feature.capitalize());ax.set_ylim(-.52,1.05)
        else:ax.set_ylim(-.1,.55)
        if j==0:ax.set_ylabel('Cosine similarity\n'+('Uncentered' if i==0 else 'Weather-centered'))
axes[0,0].legend(frameon=False,fontsize=8)
fig.suptitle('Frame-mean correspondence: matched versus weather-matched cross-sequence pairs',fontsize=12)
fig.savefig(OUT/'frame_correspondence.pdf');fig.savefig(OUT/'frame_correspondence.png',dpi=180);plt.close(fig)
with (OUT/'frame_correspondence_summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
rows=list(csv.DictReader((OUT/'linear_cka.csv').open()))
fig,ax=plt.subplots(1,2,figsize=(8,3.3),constrained_layout=True)
for a,centering in zip(ax,['global_centered','weather_centered']):
    matrix=np.array([[float(next(r['linear_cka'] for r in rows if r['feature']==f and r['pair']==p and r['centering']==centering)) for p in pairs] for f in features])
    im=a.imshow(matrix,vmin=0,vmax=1,cmap='Blues');a.set_xticks(range(3));a.set_xticklabels(pairs);a.set_yticks(range(3));a.set_yticklabels(features);a.set_title(centering.replace('_',' ').capitalize())
    for i in range(3):
        for j in range(3):a.text(j,i,f'{matrix[i,j]:.3f}',ha='center',va='center')
fig.colorbar(im,ax=ax,label='Linear CKA',shrink=.8);fig.savefig(OUT/'frame_linear_cka.pdf');fig.savefig(OUT/'frame_linear_cka.png',dpi=180)
