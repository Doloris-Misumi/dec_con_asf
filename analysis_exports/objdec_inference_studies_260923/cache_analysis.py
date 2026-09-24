"""Frame-level cached representation diagnostics, no new network inference."""
from common import *
import traceback
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = HERE / 'cache_analysis'
SOURCE = ROOT / 'analysis_exports/objdec_fulltest_weather_260919'
WEATHER = ['normal','overcast','fog','rain','sleet','lightsnow','heavysnow']
FEATURE = ['raw','shared','specific']
PAIRS = [(0,1,'C-L'),(0,2,'C-R'),(1,2,'L-R')]

def cosine(a,b):
    return (a*b).sum(-1)/np.maximum(np.linalg.norm(a,axis=-1)*np.linalg.norm(b,axis=-1),1e-12)

def stats(a):
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    if not len(a): return dict(n=0,mean=None,median=None,p05=None,p95=None)
    return dict(n=len(a),mean=float(a.mean()),median=float(np.median(a)),
                p05=float(np.quantile(a,.05)),p95=float(np.quantile(a,.95)))

def main():
    OUT.mkdir(exist_ok=True)
    status(OUT,'loading')
    paths = sorted((SOURCE/'chunks').glob('*.npz'))
    data = {}
    for p in paths:
        with np.load(p,allow_pickle=False) as z:
            for k in z.files: data.setdefault(k,[]).append(z[k])
    data = {k:np.concatenate(v) for k,v in data.items()}
    order = np.argsort(data['dataset_index']); data={k:v[order] for k,v in data.items()}
    assert np.array_equal(data['dataset_index'],np.arange(10065))
    means = data['means'].astype(np.float64)
    assert means.shape == (10065,3,3,256) and np.isfinite(means).all()
    rows=[]
    for weather in ['all']+WEATHER:
        mask = np.ones(10065,bool) if weather=='all' else data['weather']==weather
        gate=data['gate_fg_bg'][mask].astype(float); seq=data['seq'][mask]
        good=np.isfinite(gate).all(1); gate=gate[good]; seq=seq[good]
        delta=gate[:,0]-gate[:,1]
        row=dict(weather=weather,frames=int(mask.sum()),valid_frames=len(gate),sequences=len(set(seq)))
        for name,values in [('fg',gate[:,0]),('bg',gate[:,1]),('fg_minus_bg',delta)]:
            row.update({name+'_'+k:v for k,v in stats(values).items()})
        row['fg_gt_bg_fraction']=float((delta>0).mean())
        row['sequence_equal_fg_minus_bg']=float(np.mean([delta[seq==s].mean() for s in sorted(set(seq))]))
        rows.append(row)
    csv_write(OUT/'gate_by_weather.csv',rows)
    fig,ax=plt.subplots(1,2,figsize=(12,4),constrained_layout=True)
    x=np.arange(len(WEATHER)); r=rows[1:]
    for name,color,offset in [('fg','#278551',-.12),('bg','#7d8790',.12)]:
        ax[0].plot(x+offset,[a[name+'_mean'] for a in r],'o-',color=color,label=name.upper())
    ax[0].set_ylabel('Frame-mean predicted gate'); ax[0].legend(frameon=False)
    ax[1].boxplot([np.diff(data['gate_fg_bg'][data['weather']==w][:,::-1],axis=1).ravel() for w in WEATHER],
                  positions=x,showfliers=False,widths=.5)
    ax[1].axhline(0,color='#888888',lw=.8); ax[1].set_ylabel('Per-frame FG minus BG gate')
    for a in ax:
        a.set_xticks(x); a.set_xticklabels([w+'\n(n='+str(r[i]['valid_frames'])+')' for i,w in enumerate(WEATHER)],rotation=25,ha='right')
        a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
    fig.savefig(OUT/'gate_all_weather.pdf'); fig.savefig(OUT/'gate_all_weather.png',dpi=180); plt.close(fig)
    status(OUT,'representation_correspondence',frames=10065)
    similarity=[]; spectra=[]; cka=[]
    for weather in ['all']+WEATHER:
        mask=np.ones(10065,bool) if weather=='all' else data['weather']==weather
        val=means[mask]; seq=data['seq'][mask]; w=data['weather'][mask]
        centered=val.copy()
        for group in sorted(set(w)): centered[w==group]-=val[w==group].mean(0,keepdims=True)
        for seed in range(260923,260933):
            rng=np.random.RandomState(seed); perm=np.arange(len(val))
            for group in sorted(set(w)):
                idx=np.flatnonzero(w==group); perm[idx]=rng.permutation(idx)
            valid=seq!=seq[perm]
            if not valid.any(): continue
            for f,name in enumerate(FEATURE):
                for a,b,pair in PAIRS:
                    for cent,label in [(val,'uncentered'),(centered,'weather_centered')]:
                        matched=cosine(cent[valid,f,a],cent[valid,f,b])
                        mismatched=cosine(cent[valid,f,a],cent[perm[valid],f,b])
                        similarity.append(dict(weather=weather,feature=name,pair=pair,centering=label,
                            seed=seed,pairs=int(valid.sum()),matched=float(matched.mean()),
                            mismatched=float(mismatched.mean()),gap=float((matched-mismatched).mean())))
        if weather=='all':
            for f,name in enumerate(FEATURE):
                for m,mod in enumerate(['Camera','LiDAR','Radar']):
                    z=val[:,f,m]-val[:,f,m].mean(0)
                    eigen=np.maximum(np.linalg.eigvalsh(z.T@z),0)[::-1]; p=eigen/max(eigen.sum(),1e-12)
                    spectra.append(dict(feature=name,modality=mod,effective_rank=float(np.exp(-(p*np.log(p+1e-30)).sum())),
                                        centered_total_variance=float(eigen.sum()/(len(z)-1)),top1_fraction=float(p[0]),top10_fraction=float(p[:10].sum())))
                for a,b,pair in PAIRS:
                    for v,label in [(val,'global_centered'),(centered,'weather_centered')]:
                        xx=v[:,f,a]-v[:,f,a].mean(0); yy=v[:,f,b]-v[:,f,b].mean(0)
                        value=np.square(xx.T@yy).sum()/max(np.linalg.norm(xx.T@xx)*np.linalg.norm(yy.T@yy),1e-12)
                        cka.append(dict(feature=name,pair=pair,centering=label,linear_cka=float(value)))
    csv_write(OUT/'frame_correspondence_all_seeds.csv',similarity)
    csv_write(OUT/'centered_spectrum.csv',spectra); csv_write(OUT/'linear_cka.csv',cka)
    write(OUT/'provenance.json',dict(source=str(SOURCE),chunks={p.name:sha(p) for p in paths},
          source_manifest=read(SOURCE/'manifest.json'),scripts={p.name:sha(p) for p in HERE.glob('*.py')},
          interpretation='Frame mean vectors, not patch pairing. Mismatches preserve weather and exclude same-sequence pairs; matched scores use the same retained anchors. Filtering may change pair marginals. Fixed shuffle seeds describe sampling variability, not independent training replicates. No patch-level AUROC available. GT only defines post-hoc FG/BG regions.'))
    report=['# 全量缓存诊断（不重训）','','共10,065帧。GT仅用于事后划分前景/背景。',
            '',f"总体FG/BG均值：{rows[0]['fg_mean']:.4f}/{rows[0]['bg_mean']:.4f}；FG>BG帧占比{rows[0]['fg_gt_bg_fraction']:.2%}。",'',
            '所有天气、错配随机种子和正负差值均保存在CSV。帧均值余弦不等于逐patch余弦；相似度、中心化CKA与谱仅描述表征，不能单独证明检测贡献。']
    (OUT/'report.md').write_text('\n'.join(report))
    status(OUT,'complete',frames=10065,gate_overall=rows[0])

if __name__=='__main__':
    try: main()
    except BaseException:
        status(OUT,'failed',traceback=traceback.format_exc()); raise
