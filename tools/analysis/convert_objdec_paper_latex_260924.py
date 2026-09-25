#!/usr/bin/env python3
"""Convert the existing English manuscript drafts; never recompute experiment results."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/objdec_latex_260924'
SOURCES = {
    'related_work': 'results/taskdec_related_work_bilingual_initial_260917.md',
    'methods': 'results/taskdec_methods_bilingual_initial_260917.md',
    'experiments': 'results/objdec_experiments_bilingual_initial_260919.md',
    'appendix': 'results/objdec_appendix_bilingual_initial_260920.md',
}
texts = {k: (ROOT / v).read_text() for k, v in SOURCES.items()}
for folder in ['sections', 'tables', 'figures', 'assets']:
    (OUT / folder).mkdir(parents=True, exist_ok=True)

CITE = {
    'BEVFusion':'liu2023bevfusion', 'TransFusion':'bai2022transfusion',
    'CMT':'yan2023cmt', 'RCBEVDet':'lin2024rcbevdet', 'MoME':'park2025mome',
    'CCF':'wu2026ccf', 'RobuRCDet':'yue2025roburcdet', '3D-LRF':'chae2024threedlrf',
    'L4DR':'huang2025l4dr', 'DLRFusion':'chae2025dlrfusion', 'WCBR':'li2026wcbr',
    'SRF':'mukhatbekov2026srf', 'ASF':'paek2025asf', 'RAF':'park2026raf',
    'Domain Separation Networks':'bousmalis2016dsn', 'MISA':'hazarika2020misa',
    'FactorCL':'liang2023factorcl', 'DeCUR':'wang2024decur',
    'Liu et al.':'liu2025featurecausality', 'MultiLoReFT':'tonekaboni2026multiloreft',
    'DecAlign':'qian2026decalign', 'SPFD':'wang2026spfd', 'LMD':'park2025lmd',
    'K-Radar':'paek2022kradar', 'V2X-Radar':'yang2025v2xradar',
}

def key(s):
    return s.replace('.', '').lower()

def escape(s):
    m = {'&':r'\&', '%':r'\%', '#':r'\#', '_':r'\_', '$':r'\$',
         '{':r'\{', '}':r'\}', '~':r'\textasciitilde{}', '^':r'\textasciicircum{}',
         '×':r'\(\times\)', '−':r'\(-\)', '±':r'\(\pm\)', '≥':r'\(\ge\)',
         '≤':r'\(\le\)', '→':r'\(\rightarrow\)', 'Δ':r'\(\Delta\)', '–':'--', '—':'---',
         '’':"'", '‘':"'", '“':'``', '”':"''", '…':r'\ldots{}', '\\':r'\textbackslash{}'}
    return ''.join(m.get(c, c) for c in s)

def inline(s):
    saved = []
    def keep(t):
        saved.append(t)
        return f'ZZLATEXPLACEHOLDER{len(saved)-1}ZZ'
    # Preserve mathematical source verbatim, except the unsupported blackboard digit.
    def math(m):
        t = m.group().replace(r'\mathbb 1',r'\mathbf{1}').replace(r'\mathbb{1}',r'\mathbf{1}')
        return keep(t)
    s = re.sub(r'\\\(.*?\\\)', math, s, flags=re.S)
    def link(m):
        name = re.sub(r' \(20\d\d\)$','',m[1])
        if name not in CITE:
            raise ValueError(f'Unmapped reference: {m[0]}')
        return keep((r'\citet{'+CITE[name]+'}') if name == 'Liu et al.' else
                    escape(name)+r'~\citep{'+CITE[name]+'}')
    s = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',link,s)
    def citations(m):
        names = [x.strip() for x in m[1].split(';')]
        if all(x in CITE for x in names):
            return keep(r'\citep{'+','.join(CITE[x] for x in names)+'}')
        return m[0]
    s = re.sub(r'\[([^\]\n]+)\]', citations, s)
    s = re.sub(r'\[(TO COMPLETE|FIGURE TO PREPARE): ([^\]]+)\]',
               lambda m:keep(r'\drafttodo{'+escape(m[2])+'}'),s)
    # These are external table numbers, not labels within this manuscript.
    s = s.replace('Table 4 of the V2X-Radar paper', keep(r'Table~4 of the V2X-Radar paper~\citep{yang2025v2xradar}'))
    s = s.replace('Table 3 of the published L4DR paper', keep(r'Table~3 of the published L4DR paper'))
    s = s.replace('ASF Table 3', keep(r'ASF Table~3'))
    s = s.replace('Appendices G.1/G.2', keep(r'Tables~\ref{tab:g1} and~\ref{tab:g2}'))
    s = s.replace('Tables G.3a/G.3b', keep(r'Table~\ref{tab:g3} (a,b)'))
    s = s.replace('detailed in G.4.', keep(r'detailed in Section~\ref{subsec:g4}.'))
    # Lists of references need an explicit label for every member.
    s = re.sub(r'Appendices ([A-H]) and ([A-H])',
               lambda m:keep(r'Appendices~\ref{app:'+m[1].lower()+r'} and~\ref{app:'+m[2].lower()+'}'),s)
    s = re.sub(r'Tables ([A-H]\.\d+) and ([A-H]\.\d+)',
               lambda m:keep(r'Tables~\ref{tab:'+key(m[1])+r'} and~\ref{tab:'+key(m[2])+'}'),s)
    s = re.sub(r'Appendices (G\.[123])–(G\.[123])',
               lambda m:keep(r'Appendices~\ref{subsec:'+key(m[1])+r'}--\ref{subsec:'+key(m[2])+'}'),s)
    s = re.sub(r'(?:Equation|Eq\.) \(([A-H]\.\d+|\d+)\)',
               lambda m:keep(r'Equation~\eqref{eq:'+key(m[1])+'}'),s)
    s = re.sub(r'\bTables? ([A-H]\.\d+[ab]?|[1-4])(?!\d|\.\d)',
               lambda m:keep(r'Table~\ref{tab:'+key(m[1])+'}'),s)
    s = re.sub(r'\b(?:Figure|Fig\.) ([A-H]\.\d+|[1-5])(?!\d|\.\d)',
               lambda m:keep(r'Figure~\ref{fig:'+key(m[1])+'}'),s)
    def section(m):
        n=m[1]
        target=('app:'+n.lower()) if re.fullmatch('[A-H]',n) else ('subsec:'+key(n)) if '.' in n else 'sec:methods'
        return keep(r'Section~\ref{'+target+'}')
    s = re.sub(r'\bSection ([A-H](?:\.\d+)?|3(?:\.\d+)?)(?!\d|\.\d)',section,s)
    s = re.sub(r'\bAppendix ([A-H](?:\.\d+)?)(?!\d|\.\d)',
               lambda m:keep(r'Appendix~\ref{'+('subsec:' if '.' in m[1] else 'app:')+key(m[1])+'}'),s)
    s = re.sub(r'`([^`]+)`',lambda m:keep(r'\texttt{'+escape(m[1])+'}'),s)
    s = escape(s)
    s = re.sub(r'\*\*(.*?)\*\*', lambda m:r'\textbf{'+m[1]+'}',s)
    for i in range(len(saved)-1,-1,-1):
        s = s.replace(f'ZZLATEXPLACEHOLDER{i}ZZ',saved[i])
    return s

def body(s):
    out=[]; lines=s.splitlines(); i=0
    while i<len(lines):
        line=lines[i]
        if line.startswith('>') or line.strip()=='---':
            i+=1; continue
        if line.strip()==r'\[':
            j=i+1
            while lines[j].strip()!=r'\]': j+=1
            eq='\n'.join(lines[i+1:j]); tag=re.search(r'\\tag\{([^}]+)\}',eq)
            if tag:
                eq=re.sub(r'\\tag\{[^}]+\}',r'\\label{eq:'+key(tag[1])+'}',eq)
            eq=eq.replace(r'\mathbb{1}',r'\mathbf{1}').replace(r'\mathbb 1',r'\mathbf{1}')
            out += [r'\begin{equation}',eq,r'\end{equation}'];i=j+1;continue
        heading=re.match(r'^(###|####) ([A-H]|[234])(?:\.(\d+))?\.? (.+)$',line)
        if heading:
            a,n,title=heading.groups()[1:]
            typ='section' if a.isalpha() and n is None else 'subsection'
            label='app:'+a.lower() if typ=='section' else 'subsec:'+key(a+str(n or ''))
            out += [f'\\{typ}{{{inline(title)}}}',r'\label{'+label+'}'];i+=1;continue
        out.append(inline(line));i+=1
    return '\n'.join(out).strip()+'\n'

def part(text, start, end):
    return text.split(start,1)[1].split(end,1)[0].strip()

rw=part(texts['related_work'],'## 三、English draft','## 四、')
methods=part(texts['methods'],'## English draft','## 图 2')
experiments=part(texts['experiments'],'## 二、English draft','## 三、')
experiments=experiments.replace('Appendix B specifies the subset provenance, candidates, and selection metric [TO COMPLETE: selection records]',
    'Appendix B documents the available selection procedure and the provenance details still to be completed')
app=part(texts['appendix'],'## 二、English appendix','## 三、')
app=app.replace('camera ResNet-50 from ImageNet', 'camera ResNet-50 [ResNet] from ImageNet')
# Additional implementation references, kept outside numerical records.
CITE.update({'ResNet':'he2016resnet','LSS':'philion2020lss','PointPillars':'lang2019pointpillars','VoD':'palffy2022vod'})
app=app.replace('with a learned depth distribution and LSS projection','with a learned depth distribution and LSS [LSS] projection')
app=app.replace('within a native PointPillars detection backbone on VoD,',
                'within a native PointPillars [PointPillars] detection backbone on VoD [VoD],')

# Extract all original numeric table cells without regenerating or rounding values.
def extract_tables(txt, main=False):
    section=txt.split('## 三、',1)[1].split('## 四、',1)[0]
    groups=[]
    for m in re.finditer(r'^### Table ([A-H]?\.?\d+[ab]?)\. ([^\n]*)\n(.*?)(?=^### |\Z)',section,re.M|re.S):
        ident,title,content=m.groups()
        tables=[]
        for block in re.findall(r'(?:^\|[^\n]*\n?)+',content,re.M):
            rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in block.strip().splitlines()]
            rows=[r for r in rows if not all(re.fullmatch(r'[:\- ]+',x) for x in r)]
            assert all(len(r)==len(rows[0]) for r in rows),ident
            tables.append(rows)
        cap=re.search(r'^\*\*English(?: caption)?\.\*\* (.*)$',content,re.M)
        assert tables and cap,ident
        title=title.split(' / ',1)[-1]
        groups.append({'id':ident,'title':title,'tables':tables,'caption':cap[1]})
    return groups

tables=extract_tables(texts['experiments'],True)+extract_tables(texts['appendix'])
audit=[]
def tabular(rows, ident, panel=0):
    n=len(rows[0]); numeric=[]
    for col in range(n):
        numeric.append(all(re.fullmatch(r'[\d.,+−/\-—* %]+|NR|Pending',r[col].replace('**','')) for r in rows[1:]))
    # Allocate wrapping columns proportionally. Numeric columns never shrink below a legible width.
    weights=[0.75 if numeric[c] else min(4.2,max(1.2,max(len(r[c]) for r in rows)/16)) for c in range(n)]
    if ident in ('A.1','A.2','B.1'): weights=[2.9]+[2.0]*(n-1)
    if ident in ('1','2'): weights=[1.95,.60,1.65,.7,.7,.7,.7]
    weights=[round(w*n/sum(weights),5) for w in weights]
    weights[-1]=n-sum(weights[:-1])
    fmt=''.join(r'>{\hsize='+f'{w:.5f}'+r'\hsize\linewidth=\hsize'+(r'\centering' if numeric[i] else r'\raggedright')+r'\arraybackslash}X' for i,w in enumerate(weights))
    out=[r'\begingroup',r'\footnotesize',r'\setlength{\tabcolsep}{3pt}',r'\renewcommand{\arraystretch}{1.22}',
         r'\begin{tabularx}{\linewidth}{@{}'+fmt+r'@{}}',r'\toprule']
    def cell(s,header=False):
        # Standard AP notation; numerical values are otherwise untouched.
        if header:
            ap=re.fullmatch(r'(Mean )?AP(3D|BEV)@([\d.]+)',s)
            if ap:
                return r'\shortstack{'+('Mean'+r'\\' if ap[1] else '')+r'\(\mathrm{AP}_{'+ap[2]+r'}\)\\\(@'+ap[3]+r'\)}'
        t=inline(s)
        if header:
            t=t.replace('Overcast',r'Over\-cast').replace('Sequences','Seqs.').replace('Pedestrian',r'Pedes\-trian')
        t=re.sub(r'AP3D@([\d.]+)',lambda m:r'\(\mathrm{AP}_{3D}@'+m[1]+r'\)',t)
        t=re.sub(r'APBEV@([\d.]+)',lambda m:r'\(\mathrm{AP}_{BEV}@'+m[1]+r'\)',t)
        return r'\textbf{'+t+'}' if header else t
    out += [' & '.join(cell(c,True) for c in rows[0])+r' \\',r'\midrule']
    for rownum,row in enumerate(rows[1:]):
        if (ident=='1' and rownum==8) or (ident=='2' and rownum==2) or (ident=='4' and panel==1 and rownum==2) or (ident.startswith('G.3') and rownum==5):
            out.append(r'\midrule')
        cs=[cell(c) for c in row]
        if ident=='1':
            methodkey={'RTNH':'paek2022kradar','3D-LRF':'chae2024threedlrf','L4DR':'huang2025l4dr','DLRFusion':'chae2025dlrfusion','RAF on L4DR':'park2026raf','AW-MoE':'lin2026awmoe','AW-MoE-LRC':'lin2026awmoe','ASF':'paek2025asf'}.get(row[0])
            if methodkey: cs[0]+=r'~\citep{'+methodkey+'}'
        out.append(' & '.join(cs)+r' \\')
    out += [r'\bottomrule',r'\end{tabularx}',r'\endgroup']
    return '\n'.join(out)

groups={}; byid={x['id']:x for x in tables}
for entry in tables:
    ident=entry['id']
    if ident in ('C.4b','G.3b'):continue
    entries=[entry]
    if ident in ('C.4a','G.3a'):entries.append(byid[ident[:-1]+'b'])
    base=ident[:-1] if len(entries)==2 else ident
    cap=entry['caption']
    if base=='1':
        cap=cap.replace('Published references and project-protocol results are separated into groups in the final layout.','Horizontal rules separate published references from project-protocol results.')
    if base=='4':
        cap=cap.replace('Appendices G.1/G.2','Appendices G.1/G.2')
    title={'C.4':'Weather-wise v2 3D AP','G.3':'VoD region-based 3D detection results'}.get(base,entry['title'])
    blocks=[r'\begin{table}[tbp]',r'\centering',r'\caption['+inline(title)+']{'+r'\textbf{'+inline(title)+'.} '+inline(cap)+'}',r'\label{tab:'+key(base)+'}']
    for en in entries:
        for panel,rows in enumerate(en['tables']):
            paneltitle=None
            if base=='4': paneltitle=['Published validation references (different protocol)','Local deduplicated test; validation-selected weights'][panel]
            elif base=='C.4':paneltitle='IoU '+('0.3' if en['id'].endswith('a') else '0.5')
            elif base=='G.3':paneltitle='Entire Annotated Area (EAA)' if en['id'].endswith('a') else 'Driving Corridor (DC)'
            if paneltitle:
                blocks += [r'\begin{subtable}{\linewidth}',r'\caption{'+inline(paneltitle)+'}',r'\label{tab:'+key(en['id'] if len(entries)>1 else base+chr(97+panel))+'}']
            blocks.append(tabular(rows,en['id'],panel))
            if paneltitle:blocks +=[r'\end{subtable}',r'\par\medskip']
            audit.append({'source':SOURCES['experiments' if base.isdigit() else 'appendix'],'table':en['id'],'panel':panel,'original_cells':rows,'rows':len(rows)-1})
    blocks +=[r'\end{table}']
    path='tables/table_'+key(base)+'.tex';(OUT/path).write_text('\n'.join(blocks)+'\n')
    groups[base]=path

# Bibliography keeps introduction keys stable and adds independently checked entries.
intro_bib=(ROOT/'results/objdec_introduction_references_260924.bib').read_text()
recent=(ROOT/'results/taskdec_recent_references_2025_2026_260917.bib').read_text()
bibparts=[intro_bib]
for k in ['wu2026ccf','mukhatbekov2026srf','tonekaboni2026multiloreft','park2025lmd']:
    bibparts.append(re.search(r'@\w+\{'+k+r',.*?^\}',recent,re.M|re.S)[0])

NEW_REFS=[
('bai2022transfusion','Bai, Xuyang and Hu, Zeyu and Zhu, Xinge and Huang, Qingqiu and Chen, Yilun and Fu, Hongbo and Tai, Chiew-Lan','{TransFusion}: Robust {LiDAR-Camera} Fusion for {3D} Object Detection with Transformers',2022,'CVPR','https://arxiv.org/abs/2203.11496'),
('yan2023cmt','Yan, Junjie and Liu, Yingfei and Sun, Jianjian and Jia, Fan and Li, Shuailin and Wang, Tiancai and Zhang, Xiangyu','Cross Modal Transformer: Towards Fast and Robust {3D} Object Detection',2023,'ICCV','https://openaccess.thecvf.com/content/ICCV2023/html/Yan_Cross_Modal_Transformer_Towards_Fast_and_Robust_3D_Object_Detection_ICCV_2023_paper.html'),
('lin2024rcbevdet','Lin, Zhiwei and Liu, Zhe and Xia, Zhongyu and Wang, Xinhao and Wang, Yongtao and Qi, Shengxiang and Dong, Yang and Dong, Nan and Zhang, Le and Zhu, Ce',"{RCBEVDet}: Radar-camera Fusion in Bird's Eye View for {3D} Object Detection",2024,'CVPR','https://arxiv.org/abs/2403.16440'),
('li2026wcbr','Li, Hongsheng and Zhang, Lingfeng and Yang, Zexian and Li, Liang and Yin, Rong and Hao, Xiaoshuai and Ding, Wenbo','Weather-Conditioned Branch Routing for Robust {LiDAR-Radar} {3D} Object Detection',2026,'arXiv:2604.05405','https://arxiv.org/abs/2604.05405'),
('bousmalis2016dsn','Bousmalis, Konstantinos and Trigeorgis, George and Silberman, Nathan and Krishnan, Dilip and Erhan, Dumitru','Domain Separation Networks',2016,'NeurIPS','https://papers.nips.cc/paper_files/paper/2016/hash/45fbc6d3e05ebd93369ce542e8f2322d-Abstract.html'),
('hazarika2020misa','Hazarika, Devamanyu and Zimmermann, Roger and Poria, Soujanya','{MISA}: Modality-Invariant and -Specific Representations for Multimodal Sentiment Analysis',2020,'MM','https://arxiv.org/abs/2005.03545'),
('wang2024decur','Wang, Yi and Albrecht, Conrad M. and Ait Ali Braham, Nassim and Liu, Chenying and Xiong, Zhitong and Zhu, Xiao Xiang','Decoupling Common and Unique Representations for Multimodal Self-supervised Learning',2024,'ECCV','https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/04236.pdf'),
('lin2026awmoe','Lin, Hongwei and Huang, Xun and Wen, Chenglu and Wang, Cheng','{AW-MoE}: All-Weather Mixture of Experts for Robust Multi-Modal {3D} Object Detection',2026,'arXiv:2603.16261','https://arxiv.org/abs/2603.16261'),
('palffy2022vod','Palffy, Andras and Pool, Ewoud and Baratam, Srimannarayana and Kooij, Julian F. P. and Gavrila, Dariu M.','Multi-class Road User Detection with {3+1D} Radar in the {View-of-Delft} Dataset',2022,'RAL','https://repository.tudelft.nl/record/uuid%3A663863c1-35b8-48a5-9bc7-e775df8d7fac'),
('lang2019pointpillars','Lang, Alex H. and Vora, Sourabh and Caesar, Holger and Zhou, Lubing and Yang, Jiong and Beijbom, Oscar','{PointPillars}: Fast Encoders for Object Detection from Point Clouds',2019,'CVPR','https://arxiv.org/abs/1812.05784'),
('philion2020lss','Philion, Jonah and Fidler, Sanja','Lift, Splat, Shoot: Encoding Images from Arbitrary Camera Rigs by Implicitly Unprojecting to {3D}',2020,'ECCV','https://arxiv.org/abs/2008.05711'),
('he2016resnet','He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian','Deep Residual Learning for Image Recognition',2016,'CVPR','https://arxiv.org/abs/1512.03385'),
]
venues={'CVPR':'Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition','ICCV':'Proceedings of the IEEE/CVF International Conference on Computer Vision','ECCV':'European Conference on Computer Vision','MM':'Proceedings of the ACM International Conference on Multimedia','NeurIPS':'Advances in Neural Information Processing Systems'}
for k,author,title,year,venue,url in NEW_REFS:
    typ='misc' if venue.startswith('arXiv:') else 'article' if venue=='RAL' else 'inproceedings'
    fields=[f'  author = {{{author}}}',f'  title = {{{title}}}',f'  year = {{{year}}}']
    if typ=='misc': fields += [f'  eprint = {{{venue.split(":")[1]}}}', '  archivePrefix = {arXiv}']
    elif typ=='article':fields += ['  journal = {IEEE Robotics and Automation Letters}','  volume = {7}','  number = {2}','  pages = {4961--4968}','  doi = {10.1109/LRA.2022.3147324}']
    else:fields += [f'  booktitle = {{{venues[venue]}}}']
    if k=='bousmalis2016dsn':fields+=['  volume = {29}']
    if k=='yan2023cmt':fields+=['  pages = {18268--18278}']
    fields +=[f'  url = {{{url}}}']
    bibparts.append('@'+typ+'{'+k+',\n'+',\n'.join(fields)+'\n}')
(OUT/'references.bib').write_text('% Unified bibliography; introduction keys are preserved. Verified 2026-09-24.\n\n'+'\n\n'.join(bibparts)+'\n')

# Figures: use existing exported PDFs, never synthesize measured results.
assets=[]
def copy_asset(src,dst):
    src=ROOT/src
    assert src.is_file(),src
    shutil.copy2(src,OUT/'assets'/dst)
    assets.append({'source':str(src.relative_to(ROOT)),'target':'assets/'+dst,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})

def figure(ident,caption,asset=None,todo=None,page=None,height='.67',continued=False):
    result=[r'\begin{figure}[p]',r'\centering']
    if continued:result.append(r'\ContinuedFloat')
    if asset:
        result.append(r'\includegraphics[width=\linewidth,height='+height+r'\textheight,keepaspectratio'+(f',page={page}' if page else '')+']{assets/'+asset+'}')
    else:
        result.append(r'\fbox{\begin{minipage}[c][3cm][c]{0.9\linewidth}\centering\drafttodo{'+escape(todo or 'Insert final figure asset.')+r'}\end{minipage}}')
    result += [r'\caption{'+inline(caption)+'}']
    if not continued:result.append(r'\label{fig:'+key(ident)+'}')
    result.append(r'\end{figure}')
    path='figures/figure_'+key(ident)+(f'_page{page}' if continued else '')+'.tex'
    (OUT/path).write_text('\n'.join(result)+'\n')
    return path

figure('1','Motivation for object-guided shared and modality-specific representation learning and fusion.',todo='Insert the final author-approved motivation figure. This box only reserves its position.')
caption2=re.search(r'^\*\*English\.\*\* (Overview of ObjDec\..*)$',texts['methods'],re.M)[1]
figure('2',caption2,todo='Insert the revised architecture figure; verify bounded modality scaling and the gate/context paths against the method equations.')
figure('3','Frame-mean PCA and matched-foreground cosine similarity in the original feature space. PCA describes frame-level representation distributions; cosine statistics measure local cross-modal agreement. See Appendix E for the statistical units and full weather breakdown.',todo='Compose the full-test frame-mean PCA and original-space cosine statistics. Do not substitute the earlier patch-level or 24-frame visualization without updating the text.')
figreadme=(ROOT/'analysis_exports/objdec_fig4_fig5_260919/README.md').read_text()
for n,src in [(4,'analysis_exports/objdec_visuals_blue_green_purple_260923/gate/fig4_objdec_all_weather.pdf'),(5,'analysis_exports/objdec_fig4_fig5_260919/fig5_asf_objdec_detection_draft.pdf')]:
    dst=f'figure{n}.pdf';copy_asset(src,dst)
    cap=re.search(r'^\*\*Fig\.'+str(n)+r' English:\*\* (.*)$',figreadme,re.M)[1]
    figure(str(n),cap,dst,height='.67')
figspec={
    'E.1':('analysis_exports/objdec_visuals_blue_green_purple_260923/fulltest/objdec_fulltest_frame_pca_all_weather.pdf','pca_all_weather.pdf'),
    'E.2':('analysis_exports/objdec_fulltest_weather_260919/paper_visuals/objdec_fulltest_direct_similarity_distributions.pdf','similarity_distributions.pdf'),
    'E.3':('analysis_exports/objdec_fig4_fig5_260919/fig5_snow_and_counterexample.pdf','snow_counterexample.pdf'),
    'E.4':('analysis_exports/objdec_fig4_fig5_260919/fig5_all_candidates.pdf','all_candidates.pdf'),
}
for ident,(src,dst) in figspec.items():
    copy_asset(src,dst)
    block=re.search(r'^### Figure '+re.escape(ident)+r'\..*?(?=^### Figure|\Z)',texts['appendix'],re.M|re.S)[0]
    cap=re.search(r'^\*\*English caption\.\*\* (.*)$',block,re.M)[1]
    if ident=='E.1':cap=cap.replace('Orange circles, blue triangles, and purple squares','Blue circles, green triangles, and purple squares')
    figure(ident,cap,dst,page=1 if ident=='E.4' else None,height='.69')
    if ident=='E.4':
        for page in range(2,6):figure(ident,f'Complete paired candidate set, continued (page {page} of 5). Inputs, thresholds, and the interpretation of displayed IoUs follow Figure E.4.',dst,page=page,height='.83',continued=True)
gcap=re.search(r'^\*\*English caption draft\.\*\* (.*)$',texts['appendix'],re.M)[1]
figure('G.1',gcap,todo='Prepare all five 80-epoch validation trajectories from existing records. This figure has not yet been generated.')

# Section fragments and appendix. Preserve source numbers via automatic labels.
intro=(ROOT/'results/objdec_introduction_260924.tex').read_text().replace('objdec_introduction_references_260924.bib','references.bib')
intro=intro.replace('over our evaluation of the released ASF checkpoint','over the archived results associated with the released ASF checkpoint')
(OUT/'sections/introduction.tex').write_text(intro+'\n\\input{figures/figure_1}\n')
(OUT/'sections/related_work.tex').write_text(r'\section{Related Work}\label{sec:related-work}'+'\n\n'+body(rw))
(OUT/'sections/methods.tex').write_text(r'\section{Method}\label{sec:methods}'+'\n\n'+body(methods)+'\n\\input{figures/figure_2}\n')
ex=body(experiments)
for ident in ('1','2','3','4'):ex+='\n\\input{'+groups[ident]+'}\n'
for ident in ('3','4','5'):ex+='\n\\input{figures/figure_'+ident+'}\n'
(OUT/'sections/experiments.tex').write_text(r'\section{Experiments}\label{sec:experiments}'+'\n\n'+ex)
appbody=body(app)
sections=re.split(r'(?=\\section\{)',appbody)
for sec in sections:
    if not sec.strip():continue
    letter=re.search(r'\\label\{app:([a-h])\}',sec)[1]
    for ident,path in groups.items():
        if ident.lower().startswith(letter+'.'):sec+='\n\\input{'+path+'}\n'
    if letter=='a':sec+='\n\\input{tables/algorithm_a1}\n'
    if letter=='e':
        for ident in ('e1','e2','e3','e4'):sec+='\n\\input{figures/figure_'+ident+'}\n'
        for page in range(2,6):sec+=f'\n\\input{{figures/figure_e4_page{page}}}\n'
    if letter=='g':sec+='\n\\input{figures/figure_g1}\n'
    (OUT/f'sections/appendix_{letter}.tex').write_text(sec)

algorithm=part(texts['appendix'],'```text','```')
steps=algorithm.splitlines()[1:]
alg=[r'\begin{algorithm}[tbp]',r'\caption{Forward computation and training supervision}',r'\label{alg:a1}',r'\small',r'\textbf{Input:} available sensor observations, model variant, and optional training GT.',r'\begin{enumerate}[leftmargin=2.4em,label=\arabic*.,itemsep=2pt]']
for s in steps:
    match=re.match(r'\d+ +(.*)',s)
    if match:
        step=match[1].replace('from c and u.','from tokens and their shared/specific representations.')
        alg.append(r'\item '+inline(step))
alg +=[r'\end{enumerate}',inline(re.search(r'^\*\*English\.\*\* (The pseudocode.*)$',texts['appendix'],re.M)[1]),r'\end{algorithm}']
(OUT/'tables/algorithm_a1.tex').write_text('\n'.join(alg)+'\n')

(OUT/'appendix.tex').write_text(r'''% Insert after the bibliography in the full manuscript.
\appendix
\numberwithin{equation}{section}
\numberwithin{table}{section}
\numberwithin{figure}{section}
'''+'\n'.join('\\input{sections/appendix_'+letter+'}\n\\FloatBarrier' for letter in 'abcdefgh')+'\n')
(OUT/'preamble.tex').write_text(r'''% Add these packages only when they are not already supplied by your template.
\usepackage{amsmath,amssymb}
\usepackage{graphicx,booktabs,tabularx,array}
\usepackage{caption,subcaption}
\usepackage{enumitem,placeins,xcolor}
\usepackage{float}
\floatstyle{ruled}
\newfloat{algorithm}{tbp}{loa}[section]
\floatname{algorithm}{Algorithm}
\usepackage[round,authoryear]{natbib}
\usepackage{xurl}
\usepackage[hidelinks]{hyperref}
\newcommand{\drafttodo}[1]{\textcolor{red!70!black}{\textbf{[TO COMPLETE: #1]}}}
\captionsetup{font=small,labelfont=bf}
''')
(OUT/'preview.tex').write_text(r'''% Reading/compilation preview, NOT the ICLR submission template.
\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=1in]{geometry}
\usepackage{microtype}
\input{preamble}
\input{glyphtounicode}
\pdfgentounicode=1
\setlength{\emergencystretch}{2em}
\title{Decoupling to Fuse: Learning Shared and Modality-Specific Representations for Multi-Sensor 3D Object Detection}
\author{Local manuscript draft}
\date{September 24, 2026}
\begin{document}
\maketitle
\input{sections/introduction}
\FloatBarrier
\input{sections/related_work}
\FloatBarrier
\input{sections/methods}
\FloatBarrier
\input{sections/experiments}
\FloatBarrier
\bibliographystyle{plainnat}
\bibliography{references}
\clearpage
\input{appendix}
\end{document}
''')

manifest={'sources':{v:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for v in SOURCES.values()},
          'assets':assets,'table_blocks':audit,'bibliography_entries':len(re.findall(r'^@', (OUT/'references.bib').read_text(),re.M)),
          'scope':'English body and existing tables/captions. No new experiment results. No GitHub push.'}
(OUT/'conversion_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'table_blocks':len(audit),'table_data_rows':sum(x['rows'] for x in audit),'bib_entries':manifest['bibliography_entries'],'assets':len(assets)},indent=2))
