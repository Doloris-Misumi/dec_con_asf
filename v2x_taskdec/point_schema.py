"""Detect and normalize actual released mixed point formats, with audit records."""
import json
from pathlib import Path
import numpy as np


def identify(raw, key):
    if not len(raw) or np.all(raw == 0):
        return dict(width=0, empty=True, intensity_divisor=1.)
    if key == 'lidar':
        # Six-field records have an epoch timestamp and integer ring at fixed columns.
        six = raw[:min(len(raw)//6, 512)*6].reshape(-1,6)
        six_field = len(raw)%6==0 and np.mean((six[:,5]>1e9)&(six[:,5]<3e9))>.99
        width=6 if six_field else 4
        if len(raw)%width:
            raise ValueError('LiDAR width failed: '+str(len(raw)))
        sample=raw.reshape(-1,width)
        sample=sample[np.isfinite(sample).all(1)]
        divisor=255. if len(sample) and np.max(sample[:,3])>1.01 else 1.
        return dict(width=width,empty=False,intensity_divisor=divisor)
    candidates=[]
    for width in [4,5]:
        if len(raw)%width:continue
        v=raw.reshape(-1,width)
        v=v[np.isfinite(v).all(1)]
        if not len(v):continue
        # Four-field release is xyz plus [0,1] intensity; no Doppler field.
        scalar_ok=(v[:,3]>=0)&(v[:,3]<=(1.01 if width==4 else 256))
        xyz_ok=(np.abs(v[:,:3])<400).all(1)&(np.abs(v[:,2])<80)&(v[:,1]>=0)
        score=float(np.mean(scalar_ok & xyz_ok))
        candidates.append((score,width))
    candidates.sort(reverse=True)
    if not candidates or candidates[0][0]<.98:
        raise ValueError('Unrecognized radar layout: '+str(candidates))
    if len(candidates)>1 and candidates[0][0]-candidates[1][0]<.1:
        raise ValueError('Ambiguous radar layout: '+str(candidates))
    width=candidates[0][1]
    points=raw.reshape(-1,width)
    finite=points[np.isfinite(points).all(1)]
    divisor=255. if np.max(finite[:,3])>1.01 else 1.
    return dict(width=width,empty=False,intensity_divisor=divisor,layout_scores=candidates)


def load_points(path,key,schema):
    raw=np.fromfile(path,dtype=np.float32)
    target_width=4 if key=='lidar' else 6
    if schema['empty']:
        return np.zeros((0,target_width),np.float32)
    width=schema['width'];points=raw.reshape(-1,width)
    valid=np.isfinite(points).all(1) & (np.linalg.norm(points[:,:3],axis=1)>1e-5)
    points=points[valid]
    out=np.zeros((len(points),target_width),np.float32)
    out[:,:4]=points[:,:4]
    out[:,3]/=schema['intensity_divisor']
    if key=='radar' and width==5:
        out[:,4]=points[:,4]/30.
        out[:,5]=1. # observed Doppler availability, no GT dependence
    return out


def audit_all():
    from collections import Counter
    root=Path(__file__).resolve().parents[1]
    out=root/'analysis_exports/v2x_taskdec_260916'
    integrity=json.loads((out/'data_integrity.json').read_text())
    data=Path(integrity['dataset_root'])/'training'
    manifest={};counts=Counter();errors=[];nonfinite=Counter()
    ids=sorted(p.stem for p in (data/'calib').glob('*.txt'))
    for i,frame in enumerate(ids):
        entry={}
        for key,group in [('lidar','velodyne'),('radar','radar')]:
            raw=np.fromfile(data/group/(frame+'.bin'),np.float32)
            try:schema=identify(raw,key)
            except ValueError as e:
                errors.append(dict(frame=frame,sensor=key,error=str(e)));continue
            if schema['width']:
                v=raw.reshape(-1,schema['width'])
                schema['nonfinite_rows']=int((~np.isfinite(v).all(1)).sum())
                schema['raw_points']=len(v)
                nonfinite[key]+=schema['nonfinite_rows']
            entry[key]=schema
            counts[key+'_w'+str(schema['width'])+'_div'+str(schema['intensity_divisor'])]+=1
        manifest[frame]=entry
        if (i+1)%1000==0:print('schema frames',i+1,'errors',len(errors),flush=True)
    report=dict(frames=len(manifest),counts=dict(counts),nonfinite_rows=dict(nonfinite),errors=errors,
                scope='Binary format and input validity audit; no model predictions used')
    (out/'point_schema_audit.json').write_text(json.dumps(report,indent=2))
    (out/'point_schema_manifest.json').write_text(json.dumps(manifest,separators=(',',':')))
    print(json.dumps(report,indent=2))
    if errors:raise RuntimeError('Unresolved schemas; training must not start')


if __name__=='__main__':audit_all()
