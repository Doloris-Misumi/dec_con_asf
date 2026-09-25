#!/usr/bin/env python3
"""Check original table values, manuscript references, and the compiled LaTeX log."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess
import csv

ROOT = Path(__file__).resolve().parents[2]
P = ROOT/'results/objdec_latex_260924'
manifest=json.loads((P/'conversion_manifest.json').read_text())
errors=[]
for name,digest in manifest['sources'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
        errors.append('Source changed after conversion: '+name)

def numbers(s):
    s=re.sub(r'\\cite[pt]\{[^}]+\}','',s)
    s=s.replace('**','').replace('−','-').replace('–','--').replace(r'\(-\)','-')
    return re.findall(r'(?<![A-Za-z])[-+]?\d+(?:[,.]\d+)*',s)

all_rows={}
for f in (P/'tables').glob('table_*.tex'):
    chunks=re.findall(r'\\begin\{tabularx\}.*?\\midrule\s*(.*?)\\bottomrule',f.read_text(),re.S)
    rows=[]
    for chunk in chunks:
        data=[]
        for line in chunk.splitlines():
            if not line.rstrip().endswith(r'\\'):continue
            data.append(line.rstrip()[:-2].strip().split(' & '))
        rows.append(data)
    all_rows[f.stem.replace('table_','')]=rows

checked_cells=0;checked_rows=0
for entry in manifest['table_blocks']:
    ident=entry['table'];base=ident.lower().replace('.','');panel=entry['panel']
    if ident in ('C.4a','C.4b','G.3a','G.3b'):
        panel=int(ident.endswith('b'));base=base[:-1]
    source=entry['original_cells'][1:];target=all_rows[base][panel]
    if len(source)!=len(target):errors.append(f'Row count mismatch {ident}');continue
    for i,(r1,r2) in enumerate(zip(source,target)):
        if len(r1)!=len(r2):errors.append(f'Column count mismatch {ident}/{i}');continue
        for col,(a,b) in enumerate(zip(r1,r2)):
            if numbers(a)!=numbers(b):errors.append(f'Numeric mismatch {ident}/{i}/{col}: {a} vs {b}')
            if a in ('NR','Pending','—') and b!= {'NR':'NR','Pending':'Pending','—':'---'}[a]:
                errors.append(f'Missing-value marker mismatch {ident}/{i}/{col}')
            checked_cells+=1
        checked_rows+=1

def reachable_tex(start):
    """Validate the compiled manuscript, excluding archived/unused figure templates."""
    found=[]
    def visit(path):
        if path in found:return
        if not path.exists():
            errors.append('Missing LaTeX input: '+str(path));return
        found.append(path)
        active=re.sub(r'(?<!\\)%[^\n]*','',path.read_text())
        for name in re.findall(r'\\input\{([^}]+)\}',active):
            if name=='glyphtounicode':continue  # TeX distribution resource.
            child=P/name
            if not child.suffix:child=child.with_suffix('.tex')
            visit(child)
    visit(start)
    return found
texfiles=reachable_tex(P/'preview.tex')
tex='\n'.join(re.sub(r'(?<!\\)%[^\n]*','',f.read_text()) for f in texfiles)
labels=re.findall(r'\\label\{([^}]+)\}',tex)
duplicates=[k for k,n in Counter(labels).items() if n>1]
refs=set(re.findall(r'\\(?:ref|eqref)\{([^}]+)\}',tex))
missingrefs=sorted(refs-set(labels))
keys=re.findall(r'^@\w+\{([^,]+),',(P/'references.bib').read_text(),re.M)
citations={k for group in re.findall(r'\\cite[pt](?:\[[^\]]*\])?\{([^}]+)\}',tex) for k in group.split(',')}
missingcites=sorted(citations-set(keys))
errors += ['Duplicate label: '+x for x in duplicates]
errors += ['Missing label: '+x for x in missingrefs]
errors += ['Missing citation: '+x for x in missingcites]
if len(set(keys))!=len(keys):errors.append('Duplicate bibliography key')
if re.search(r'ZZLATEXPLACEHOLDER|https?://|^> |^###|\\tag\{',tex,re.M):errors.append('Unconverted markup in manuscript')
body='\n'.join(f.read_text() for f in texfiles if f.parent.name in ['sections','tables','figures'])
if re.search('[\u4e00-\u9fff]',body):errors.append('Chinese editorial text in English manuscript')
if 'TaskDec' in body:errors.append('Outdated method name in paper body')

log=(P/'preview.log').read_text()
critical=re.findall(r'^.*(?:undefined|multiply defined|LaTeX Error|Fatal error|Overfull|Float too large).*$' ,log,re.M)
errors.extend(critical)
if 'Output written on preview.pdf' not in log:errors.append('No successful LaTeX output')
if 'Warning' in (P/'build-bibtex.log').read_text():errors.append('BibTeX warning')
candidate_info=subprocess.check_output(['pdfinfo',str(P/'assets/all_candidates.pdf')],text=True)
if not re.search(r'Pages:\s+5\b',candidate_info):errors.append('Candidate PDF should have five pages')
main_figure_files=[f for f in texfiles if re.fullmatch(r'figure_[1-9]\.tex',f.name)]
if {f.name for f in main_figure_files}!={f'figure_{n}.tex' for n in range(1,5)}:
    errors.append('Expected exactly four main-text figure inputs')
if 'fig:5' in refs:errors.append('Obsolete main-text Figure 5 reference')
if any(f.name.startswith('figure_e4') for f in texfiles):
    errors.append('Candidate atlas must remain archived, not inserted into the manuscript')
for item in manifest['assets']:
    asset=P/item['target']
    if not asset.exists() or hashlib.sha256(asset.read_bytes()).hexdigest()!=item['sha256']:
        errors.append('Asset hash mismatch: '+item['target'])
for name in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',tex):
    if not (P/name).exists():errors.append('Missing graphic: '+name)

# The new table was added after the original Markdown conversion. Check it
# against all eight paired evaluations and the unrounded shuffle average.
src=ROOT/'analysis_exports/objdec_kradar_v1_interventions_260923/reporting_260924/all_conditions_metrics.csv'
with src.open() as handle: records=list(csv.DictReader(handle))
cases=list(dict.fromkeys(r['case'] for r in records if r['condition']=='all'))
metrics=[('AP3D','0.3'),('AP3D','0.5'),('AP3D','0.7'),('BEV','0.3'),('BEV','0.5'),('BEV','0.7')]
expected=[]
for case in cases:
    expected.append([next(float(r['AP']) for r in records if r['condition']=='all' and r['case']==case and (r['metric'],r['iou'])==metric) for metric in metrics])
shuffle=[row for case,row in zip(cases,expected) if case.startswith('gate_shuffle_')]
expected.append([sum(row[i] for row in shuffle)/len(shuffle) for i in range(6)])
table=(P/'tables/table_d2.tex').read_text().split(r'\midrule',1)[1].split(r'\bottomrule',1)[0]
actual=[[cell.strip() for cell in line.rstrip()[:-2].split(' & ')[1:]] for line in table.splitlines() if line.rstrip().endswith(r'\\')]
if actual!=[[f'{v:.4f}' for v in row] for row in expected]:
    errors.append('New paired intervention table does not match source CSV')

# Paste-ready and assembled chapters should differ only in includes/comments.
def prose(path):
    text=path.read_text()
    text=re.sub(r'(?m)^%[^\n]*\n?','',text)
    text=re.sub(r'\\input\{[^}]+\}','',text)
    return re.sub(r'\s+',' ',text).strip()
for name,date in [('introduction','260924'),('related_work','260925'),('methods','260925'),('experiments','260925'),('conclusion','260925')]:
    if prose(ROOT/f'results/objdec_{name}_{date}.tex')!=prose(P/f'sections/{name}.tex'):
        errors.append('Standalone/assembled chapter mismatch: '+name)
if (ROOT/'results/objdec_introduction_references_260924.bib').read_bytes()!=(P/'references.bib').read_bytes():
    errors.append('Standalone/assembled bibliography mismatch')
for n in range(1,5):
    if (ROOT/f'results/objdec_tables_260925/table_{n}.tex').read_bytes()!=(P/f'tables/table_{n}.tex').read_bytes():
        errors.append('Standalone/assembled main table mismatch: '+str(n))
report={'pass':not errors,'errors':errors,'table_blocks':len(manifest['table_blocks']),
        'data_rows_checked':checked_rows,'table_cells_checked':checked_cells,
        'numeric_tokens_and_missing_markers_preserved':not any('mismatch' in e.lower() for e in errors),
        'bibliography_entries':len(keys),'cited_entries':len(citations),'missing_citations':missingcites,
        'cross_reference_labels':len(labels),'missing_cross_references':missingrefs,
        'numbered_equations':len(re.findall(r'\\begin\{equation\}',body)),
        'main_figures':len(main_figure_files),
        'appendix_e_figures':sum(f.parent.name=='figures' and f.name.startswith('figure_e') for f in texfiles),
        'candidate_atlas_preserved_as_archive':True,
        'paired_intervention_rows_checked':len(expected),
        'remaining_visible_todo_instances':len(re.findall(r'\\drafttodo\{',body)),
        'layout_note':'Generic article preview; remaining underfull alignment notices do not indicate clipped content. Not an ICLR submission layout.'}
(P/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
