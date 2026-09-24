"""Render deterministic train-frame overlays and verify shared augmentation math."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from .dataset import V2XDataset
from .geometry import read_calibration, project_points, corners_lidar, augment_world, transform_points

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis_exports/v2x_taskdec_260916'


def main():
    cfg=json.loads((OUT/'engineering_config.json').read_text())
    audit=json.loads((OUT/'point_schema_audit.json').read_text())
    assert not audit['errors']
    dataset=V2XDataset(cfg,'train')
    chosen={}
    for frame in dataset.ids:
        s=dataset.schemas[frame]
        signature=tuple((s[key]['width'],s[key]['intensity_divisor']) for key in ['lidar','radar'])
        chosen.setdefault(signature,frame)
    records=[]
    for signature,frame in chosen.items():
        cal=read_calibration(dataset.data/'calib'/(frame+'.txt'))
        pts=[dataset.read_points(frame,k,cal) for k in ['lidar','radar']]
        boxes=dataset.read_boxes(frame,cal)
        roi=np.asarray(cfg['point_cloud_range'])
        boxes=boxes[((boxes[:,:3]>=roi[:3])&(boxes[:,:3]<roi[3:])).all(1)]
        corners=corners_lidar(boxes)
        transformed,ab,A=augment_world(pts,boxes,.3,1.02,True)
        corner_aug=corners_lidar(ab)
        expected=transform_points(corners.reshape(-1,3),A).reshape(corners.shape)
        max_error=0.
        for actual,target in zip(corner_aug,expected):
            max_error=max(max_error,float(np.linalg.norm(actual[:,None]-target[None],axis=-1).min(1).max()))
        assert max_error<1e-4,(frame,max_error)
        before=project_points(pts[0][:200,:3],cal)[0]
        back=transform_points(transformed[0][:200,:3],np.linalg.inv(A))
        after=project_points(back,cal)[0]
        # Restrict numerical check to points in front, not singular projection at z<=0.
        depth=project_points(pts[0][:200,:3],cal)[1]
        mask=depth>2
        projection_error=float(np.max(np.abs(before[mask]-after[mask]))) if mask.any() else 0.
        assert projection_error<.1,(frame,projection_error)
        record=dict(frame=frame,schema=str(signature),gt_in_roi=len(boxes),point_counts=[len(p) for p in pts],
                    augmentation_corner_error_m=max_error,augmentation_projection_error_px=projection_error,
                    ego_rotation=cal['raw_lidar_to_ego'].tolist())
        records.append(record)
        if len(records)>8:continue
        image=np.asarray(Image.open(next((dataset.data/'image_2').glob(frame+'.*'))))
        fig,axs=plt.subplots(1,2,figsize=(13,4.8),dpi=120)
        axs[0].imshow(image)
        uv,depth=project_points(pts[1][:,:3],cal)
        mask=(depth>0)&(uv[:,0]>=0)&(uv[:,0]<image.shape[1])&(uv[:,1]>=0)&(uv[:,1]<image.shape[0])
        axs[0].scatter(uv[mask,0],uv[mask,1],s=1,c='cyan',alpha=.35)
        for cb in corners:
            uv,d=project_points(cb,cal)
            if (d<=.1).any():continue
            for a,b in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:
                axs[0].plot(uv[[a,b],0],uv[[a,b],1],color='lime',lw=.7)
        axs[0].set(xlim=(0,image.shape[1]),ylim=(image.shape[0],0),title='Camera: GT boxes + calibrated radar')
        p=pts[0][::12]
        axs[1].scatter(p[:,0],p[:,1],s=.2,c='gray',alpha=.4)
        axs[1].scatter(pts[1][:,0],pts[1][:,1],s=.5,c='blue',alpha=.3)
        for cb in corners:
            poly=cb[[0,1,2,3,0]];axs[1].plot(poly[:,0],poly[:,1],c='green',lw=1)
        axs[1].set(xlim=(0,102.4),ylim=(-51.2,51.2),xlabel='ego forward x (m)',ylabel='ego left y (m)',title='LiDAR / radar / GT in one ego frame')
        axs[1].set_aspect('equal');fig.suptitle(frame+' '+str(signature));fig.tight_layout()
        fig.savefig(OUT/('geometry_'+frame+'.png'));plt.close(fig)
    report=dict(status='numeric_checks_passed_visual_review_pending',cases=records,
                note='Representatives of every actual format present in train, independent of model output')
    (OUT/'geometry_checks.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
