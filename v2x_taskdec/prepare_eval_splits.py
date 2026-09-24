"""Freeze duplicate-aware evaluation IDs before formal training/model selection.

Keep the official train split unchanged. Val excludes byte-identical camera
observations from train; test excludes train and official val. Within each eval
split retain the first identical observation. Original splits remain untouched.
"""
import collections,hashlib,json,zipfile
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1];out=root/'analysis_exports/v2x_taskdec_260916'
    integrity=json.loads((out/'data_integrity.json').read_text());data=Path(integrity['dataset_root'])/'training'
    src=Path(integrity['split_root']);splits={k:(src/(k+'.txt')).read_text().split() for k in ['train','val','test']}
    archive=Path('/home/hongsheng/datasets/V2X-Radar-V/downloads/V2X-Radar-V.zip')
    signatures={}
    with zipfile.ZipFile(archive) as z:
        candidates=collections.defaultdict(list)
        for i in z.infolist():
            if '/image_2/' in i.filename and not i.is_dir():candidates[(i.CRC,i.file_size)].append(Path(i.filename).stem)
    for group in candidates.values():
        if len(group)==1:signatures[group[0]]='unique:'+group[0]
        else:
            for frame in group:signatures[frame]=hashlib.sha256(next((data/'image_2').glob(frame+'.*')).read_bytes()).hexdigest()
    report={'rule':__doc__,'official_counts':{k:len(v) for k,v in splits.items()},'excluded':{},'clean_counts':{}}
    dest=out/'evaluation_splits';dest.mkdir(exist_ok=True)
    for name,earlier in [('val',['train']),('test',['train','val'])]:
        blocked={signatures[i] for prev in earlier for i in splits[prev]};seen=set();kept=[];removed=[]
        for frame in splits[name]:
            sig=signatures[frame]
            if sig in blocked or sig in seen:
                removed.append(dict(frame=frame,reason='duplicate_of_earlier_split' if sig in blocked else 'duplicate_within_split'))
            else:kept.append(frame)
            seen.add(sig)
        p=dest/(name+'_deduplicated.txt');text='\n'.join(kept)+'\n'
        if p.exists() and p.read_text()!=text:raise RuntimeError('Refusing to change an already frozen split')
        p.write_text(text)
        report['excluded'][name]=removed;report['clean_counts'][name]=len(kept)
        report[name+'_sha256']=hashlib.sha256(text.encode()).hexdigest()
    (out/'evaluation_split_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
