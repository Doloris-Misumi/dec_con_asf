"""Recover summary export from completed per-GT records, without rerunning geometry.

The first run's paired table had pair-dependent columns; its fixed-header CSV
writer rejected the second pair. Use the union of columns for the full table.
"""
from pathlib import Path
import sys
import csv
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import diagnostics as diag
from common import read,write,status,sha

OUT=Path(__file__).resolve().parent
if (OUT/'status.json').exists() and not (OUT/'export_failure.json').exists():
    write(OUT/'export_failure.json',read(OUT/'status.json'))
with (OUT/'per_gt.csv').open() as f: records=list(csv.DictReader(f))
text_fields={'frame','class','range_bin','lidar_bin','radar_bin'}
for r in records:
    for key,value in list(r.items()):
        if key in text_fields:continue
        if value=='':r[key]=None
        elif key in ['gt_index','lidar_points','radar_points'] or '_hit_' in key:r[key]=int(value)
        else:r[key]=float(value)
summaries,comparisons=diag.summarize(records)
for name,rows in [('group_recall_and_errors.csv',summaries),('paired_comparisons.csv',comparisons)]:
    columns=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(rows)
protocol=read(OUT/'protocol.json')
assert protocol['frames']==1486
write(OUT/'summary.json',dict(frames=protocol['frames'],gt=len(records),
    all_groups=[r for r in summaries if r['group']=='all'],paired_all=[r for r in comparisons if r['group']=='all']))
write(OUT/'export_recovery.json',dict(source='per_gt.csv',per_gt_sha256=sha(OUT/'per_gt.csv'),
    script_sha256=sha(Path(__file__)),reason='Pair-dependent column names require union headers; no prediction, matching or geometry changes.'))
status(OUT,'complete',frames=1486,gt=len(records),export_recovered=True)
