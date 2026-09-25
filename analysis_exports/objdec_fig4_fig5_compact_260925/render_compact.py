#!/usr/bin/env python3
"""Compact real-data Fig.4/5: contiguous rows, one header, captions outside.

CPU plotting only. Geometry, calibrated camera projection and stored predictions
are reused; no synthetic imagery, image enhancement, or new inference.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SCENE = ROOT / 'analysis_exports/objdec_scene_mechanism_260924'
PAIRED = ROOT / 'analysis_exports/objdec_fig4_fig5_260919'
sys.path[:0] = [str(ROOT), str(ROOT / 'tools/analysis')]

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.lines import Line2D
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from tools.analysis.make_objdec_fig4_fig5_260919 import (
    camera_params, camera_boxes, box_corners3d, corners)
from tools.analysis.export_taskdec_bev_gate import camera_image, lidar_points

spec = importlib.util.spec_from_file_location('objdec_scene_source', SCENE / 'render.py')
scene_source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scene_source)

GT, PRED, BG, INK = '#00D0A1', '#FF9B2B', '#111E2E', '#172B43'
FIG4_IDS = ['seq17_rdr00625', 'seq10_rdr01127', 'seq25_rdr00154']
FIG5_IDS = ['seq20_rdr00628', 'seq22_rdr00218', 'seq25_rdr00154']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                     'pdf.fonttype': 42, 'svg.fonttype': 'none'})


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def axes_inches(fig, rect, background=None):
    fw, fh = fig.get_size_inches()
    x, y, w, h = rect
    ax = fig.add_axes([x/fw, y/fh, w/fw, h/fh])
    if background:
        ax.set_facecolor(background)
    ax.set(xticks=[], yticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def draw_boxes(ax, values, color, style='-', width=1.5):
    for box in values:
        ax.add_patch(Polygon(corners(box), closed=True, fill=False,
                             edgecolor=color, linewidth=width, linestyle=style,
                             zorder=5))


def detail_rect(ax, bounds, width=1.1):
    x0, x1, y0, y1 = bounds
    ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False,
                           edgecolor='white', linestyle=':', linewidth=width,
                           zorder=6))


def draw_camera(ax, img, pred, gt, params):
    ax.imshow(img)
    camera_boxes(ax, pred, params, PRED, lw=1.65)
    camera_boxes(ax, gt, params, GT, style='--', lw=1.4)
    ax.set(xlim=(0, 1280), ylim=(720, 0))
    ax.set_axis_off()


def draw_bev(ax, pts, pred, gt, bounds):
    ax.set_facecolor(BG)
    ax.scatter(pts[:, 0], pts[:, 1], s=.75, c='#D1DED9', alpha=.8,
               linewidths=0, rasterized=True)
    draw_boxes(ax, pred, PRED, width=1.6)
    draw_boxes(ax, gt, GT, '--', 1.4)
    ax.set(xlim=bounds[:2], ylim=bounds[2:], aspect='equal')


def draw_gate(ax, record, bounds, predictions=False):
    ax.imshow(record['data']['gate'], origin='lower', extent=[0,72,-6.4,6.4],
              interpolation='nearest', cmap='magma', vmin=0, vmax=1,
              aspect='equal')
    draw_boxes(ax, record['data']['gt_boxes'], GT, '--', 1.4)
    if predictions:
        draw_boxes(ax, record['pred'], PRED, width=1.6)
    ax.set(xlim=bounds[:2], ylim=bounds[2:])


def header(fig, centers, titles, body_top, gate=False):
    fw, fh = fig.get_size_inches()
    size = 13 if gate else 15
    for center, title in zip(centers, titles):
        fig.text(center/fw, (body_top+.085)/fh, title, ha='center', va='bottom',
                 fontsize=size, fontweight='bold', color=INK)
    handles = [Line2D([], [], color=PRED, lw=2, label='Prediction'),
               Line2D([], [], color=GT, lw=2, ls='--', label='GT'),
               Line2D([], [], color='#687584', lw=1.5, ls=':', label='Detail')]
    fig.legend(handles=handles, ncol=3, frameon=False, loc='center left',
               bbox_to_anchor=(.008, (body_top+.46)/fh), fontsize=11.5 if gate else 13,
               borderaxespad=0, handlelength=2.1, columnspacing=1.4)
    if gate:
        cax = axes_inches(fig, [fw-3.25, body_top+.39, 2.9, .105])
        cb = fig.colorbar(ScalarMappable(Normalize(0,1), 'magma'), cax=cax,
                          orientation='horizontal', ticks=[0,.5,1])
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=10.5, length=2, pad=1)
        fig.text((fw-3.38)/fw, (body_top+.437)/fh, '$g$', fontsize=13,
                 ha='right', va='center', color=INK)


def row_rules(fig, xs, row_h, n, margin):
    # Thin borders distinguish abutting panels without adding whitespace.
    fw, fh = fig.get_size_inches()
    for i in range(1, n):
        y=(margin+i*row_h)/fh
        for left, width in xs:
            fig.add_artist(Line2D([left/fw,(left+width)/fw], [y,y],
                                  transform=fig.transFigure, color='white', lw=.45))


def save(fig, stem, audit):
    text = [t.get_text() for t in fig.findobj(matplotlib.text.Text) if t.get_text()]
    banned = ['normal', 'snow', 'rain', 'overcast', 'seq', 'rdr', 'iou', 'foreground', 'background']
    assert not any(b in t.lower() for t in text for b in banned), text
    fig.canvas.draw()
    # Verify that plot boxes keep x/y metric units at the same physical scale.
    for ax in fig.axes:
        if ax.get_aspect() == 1.0:
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            bbox = ax.get_window_extent()
            px = bbox.width / abs(xlim[1]-xlim[0])
            py = bbox.height / abs(ylim[1]-ylim[0])
            assert abs(px-py) < 1e-6
    audit['visible_text'] = text
    audit['figure_size_inches'] = fig.get_size_inches().tolist()
    audit['equal_spatial_scale_checked'] = True
    for ext in ['pdf', 'svg', 'png']:
        fig.savefig(OUT/f'{stem}.{ext}', dpi=300, facecolor='white')
    plt.close(fig)


def figure4(records):
    margin, gap, row_h = .02, .055, 2.0
    widths = [row_h*16/9, row_h/(2*12.8/72), row_h*14/8.4]
    lefts = [margin]
    for w in widths[:-1]:
        lefts.append(lefts[-1]+w+gap)
    body_top = margin+3*row_h
    fw = 2*margin+sum(widths)+2*gap
    fig = plt.figure(figsize=(fw, body_top+.64))
    header(fig, [x+w/2 for x,w in zip(lefts,widths)],
           ['Camera', 'LiDAR BEV / Gate', 'Gate detail'], body_top, gate=True)
    rows=[]
    for i,r in enumerate(records):
        bottom=margin+(2-i)*row_h
        ax=axes_inches(fig,[lefts[0],bottom,widths[0],row_h])
        draw_camera(ax,r['image'],r['pred'],[r['target_box']],r['params'])
        ax=axes_inches(fig,[lefts[1],bottom+row_h/2,widths[1],row_h/2],BG)
        draw_bev(ax,r['points'],r['pred'],r['data']['gt_boxes'],[0,72,-6.4,6.4])
        detail_rect(ax,r['zoom'])
        ax=axes_inches(fig,[lefts[1],bottom,widths[1],row_h/2])
        draw_gate(ax,r,[0,72,-6.4,6.4])
        detail_rect(ax,r['zoom'])
        ax=axes_inches(fig,[lefts[2],bottom,widths[2],row_h])
        draw_gate(ax,r,r['zoom'],predictions=True)
        rows.append(dict(id=r['frame']['id'],row_bounds_inches=[bottom,bottom+row_h],
                         target_gt_index=r['target_index'],zoom=r['zoom'],
                         gt_count=len(r['data']['gt_boxes']),prediction_count=len(r['pred']),
                         gate_foreground_mean=r['frame']['gate_FG'],
                         gate_background_mean=r['frame']['gate_BG']))
    row_rules(fig,list(zip(lefts,widths)),row_h,3,margin)
    for a,b in zip(rows,rows[1:]):
        assert abs(a['row_bounds_inches'][0]-b['row_bounds_inches'][1])<1e-10
    audit=dict(rows=rows,vertical_row_gap_inches=0,gate_scale=[0,1],gate_interpolation='nearest',
               camera_gt='Only selected target GT, as in the previous scene figure; all predictions retained.',
               full_bev_and_gate_roi=[0,72,-6.4,6.4],all_axes_and_sample_labels_removed=True)
    save(fig,'objdec_fig4_compact',audit)
    return audit


def camera_zoom(target, params):
    k,dist,t=params
    c=box_corners3d(target)@t[:3,:3].T+t[:3,3]
    assert (c[:,2]>.1).all()
    uv=cv2.projectPoints(c,np.zeros(3),np.zeros(3),k,dist)[0].reshape(-1,2)
    center=(uv.min(axis=0)+uv.max(axis=0))/2
    width=min(1280,max(160,float(np.ptp(uv[:,0]))*2,float(np.ptp(uv[:,1]))*2*16/9))
    height=width*9/16
    u=float(np.clip(center[0]-width/2,0,1280-width))
    v=float(np.clip(center[1]-height/2,0,720-height))
    return [u,u+width,v,v+height]


def figure5(records):
    margin,gap,bev_w=.02,.055,3.4
    full_h=bev_w*12.8/72
    detail_h=bev_w*6/12
    row_h=full_h+detail_h
    cam_w=row_h*16/9
    widths=[cam_w,cam_w,bev_w,bev_w]
    lefts=[margin]
    for w in widths[:-1]:lefts.append(lefts[-1]+w+gap)
    body_top=margin+3*row_h
    fig=plt.figure(figsize=(2*margin+sum(widths)+3*gap,body_top+.64))
    header(fig,[x+w/2 for x,w in zip(lefts,widths)],
           ['ASF · Camera','ObjDec · Camera','ASF · BEV','ObjDec · BEV'],body_top)
    rows=[]
    for i,r in enumerate(records):
        bottom=margin+(2-i)*row_h
        f=r['frame'];gt=np.asarray(r['models']['asf']['gt'])
        assert np.array_equal(gt,np.asarray(r['models']['objdec']['gt']))
        params=camera_params(f['seq']);img=camera_image(f)
        points=lidar_points(f,np.array([0,-6.4,-2,72,6.4,6]))
        a=np.asarray(r['models']['asf']['best_iou3d_per_gt'])
        o=np.asarray(r['models']['objdec']['best_iou3d_per_gt'])
        target_index=int(np.argmax(np.abs(o-a)));g=gt[target_index]
        # Same selected target as the previous draft. A fixed 12 x 6 m detail
        # window is translated inside the ROI, identically for both methods.
        x0=float(np.clip(g[0]-6,0,60));y0=float(np.clip(g[1]-3,-6.4,.4))
        bounds=[x0,x0+12,y0,y0+6]
        cam_bounds=camera_zoom(g,params)
        counts={}
        for j,model in enumerate(['asf','objdec']):
            pred=np.asarray(r['models'][model]['boxes']).reshape(-1,7)
            # Check displayed detections against the original inference cache.
            with np.load(PAIRED/'paired_predictions'/model/f"{f['id']}.npz") as d:
                keep=(d['scores']>.3)&(d['labels']==1)
                assert np.array_equal(pred,d['boxes'][keep])
                assert np.array_equal(gt,d['gt'])
            ax=axes_inches(fig,[lefts[j],bottom,widths[j],row_h])
            draw_camera(ax,img,pred,gt,params)
            detail_rect(ax,cam_bounds)
            # Larger inset, no duplicated label: exact raw-image crop with
            # the same calibration and crop bounds for the two methods.
            inset=ax.inset_axes([.012,.538,.45,.45])
            draw_camera(inset,img,pred,gt,params)
            inset.set(xlim=cam_bounds[:2],ylim=(cam_bounds[3],cam_bounds[2]))
            inset.set_axis_on();inset.set(xticks=[],yticks=[])
            for spine in inset.spines.values():
                spine.set_visible(True);spine.set_color('white');spine.set_linewidth(1)
            bx=axes_inches(fig,[lefts[j+2],bottom+detail_h,bev_w,full_h],BG)
            draw_bev(bx,points,pred,gt,[0,72,-6.4,6.4]);detail_rect(bx,bounds)
            bx=axes_inches(fig,[lefts[j+2],bottom,bev_w,detail_h],BG)
            draw_bev(bx,points,pred,gt,bounds)
            counts[model]=len(pred)
        rows.append(dict(id=f['id'],row_bounds_inches=[bottom,bottom+row_h],
                         target_gt_index=target_index,zoom=bounds,camera_zoom_pixels=cam_bounds,
                         prediction_counts=counts,gt_count=len(gt),
                         selected_gt_best_iou3d=dict(asf=float(a[target_index]),objdec=float(o[target_index])),
                         camera_sha256=sha(f['camera_path']),lidar_sha256=sha(f['lidar_path'])))
    row_rules(fig,list(zip(lefts,widths)),row_h,3,margin)
    for a,b in zip(rows,rows[1:]):
        assert abs(a['row_bounds_inches'][0]-b['row_bounds_inches'][1])<1e-10
    audit=dict(rows=rows,vertical_row_gap_inches=0,score_filter='score > 0.3; label = Sedan',
               full_roi=[0,72,-6.4,6.4],detail_size_m=[12,6],camera_inset_fraction=.45,
               paired_predictions_exactly_match_inference_caches=True,
               same_camera_and_bev_crops_for_both_methods=True)
    save(fig,'objdec_fig5_compact',audit)
    return audit


def main():
    paths=[SCENE/'manifest.json',SCENE/'render.py',PAIRED/'fig5_candidate_metrics.json',
           ROOT/'resources/cam_calib/calib_seq.zip']
    paths += [SCENE/'maps'/f'{k}.npz' for k in FIG4_IDS]
    paths += [PAIRED/'paired_predictions'/m/f'{k}.npz' for m in ['asf','objdec'] for k in FIG5_IDS]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    print('Preparing existing scene maps...',flush=True)
    records,source_audit=scene_source.prepare()
    lookup={r['frame']['id']:r for r in records}
    print('Rendering contiguous Fig.4...',flush=True)
    a4=figure4([lookup[k] for k in FIG4_IDS])
    records=json.loads((PAIRED/'fig5_candidate_metrics.json').read_text())['records']
    lookup={r['frame']['id']:r for r in records}
    print('Rendering contiguous Fig.5...',flush=True)
    a5=figure5([lookup[k] for k in FIG5_IDS])
    assert hashes=={str(p.relative_to(ROOT)):sha(p) for p in paths}
    result=dict(new_inference=False,source_arrays_unchanged=True,source_sha256=hashes,
                colors=dict(prediction=PRED,ground_truth=GT),fig4=a4,fig5=a5,
                fig4_source_records=[r for r in source_audit if r['id'] in FIG4_IDS])
    (OUT/'validation_and_provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Complete:',OUT,flush=True)


if __name__=='__main__':main()
