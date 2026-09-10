#!/usr/bin/env python3
"""Export full TaskDec gate grids and render a small, traceable Figure 4 draft.

No feature tensors, raw camera copies, point-cloud copies, or training logs are
saved. Render mode reads the original data and does not require a GPU.
"""
import argparse
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import types

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ops"))
from tools.analysis.export_taskdec_patch_pca import infer_weather

EXP = ROOT / "logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16"
WEATHERS = ["normal", "overcast", "fog", "rain", "lightsnow", "heavysnow", "sleet"]
NAMES = {"normal": "Normal", "overcast": "Overcast", "fog": "Fog", "rain": "Rain",
         "lightsnow": "Light snow", "heavysnow": "Heavy snow", "sleet": "Sleet"}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def shortlist(csv_path):
    # One record per sampled patch, avoiding duplicate modalities/projections.
    groups = collections.defaultdict(lambda: [[], []])
    with open(csv_path) as stream:
        for row in csv.DictReader(stream):
            if row["feature_type"] == "raw" and row["modality"] == "Camera":
                key = row["weather"], row["seq"], row["sample_id"]
                groups[key][int(row["foreground"])].append(float(row["fg_gate"]))
    chosen = []
    for weather in WEATHERS:
        ranked = []
        for (w, seq, frame), (bg, fg) in groups.items():
            if w == weather and bg and fg:
                ranked.append(dict(weather=w, seq=seq, radar_id=frame,
                                   sampled_gap=float(np.mean(fg) - np.mean(bg))))
        ranked.sort(key=lambda r: (-r["sampled_gap"], int(r["seq"]), r["radar_id"]))
        # Include strong, middle and weaker responses, not only maxima.
        used = set()
        for quantile in [0.0, 0.5, 0.75]:
            index = int(round(quantile * (len(ranked) - 1)))
            if not ranked or index in used:
                continue
            used.add(index)
            chosen.append(dict(ranked[index], shortlist_rank=index + 1,
                               weather_pool_size=len(ranked)))
    return chosen


def export(args):
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu
    import torch
    from pipelines.pipeline_detection_v1_0 import PipelineDetection_v1_0

    torch.set_num_threads(4)
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    candidates = shortlist(args.sampled_csv)
    if args.select:
        by_id = {f"seq{r['seq']}_rdr{r['radar_id']}": r for r in candidates}
        candidates = [by_id[key] for key in args.select.split(",")]
    if args.limit:
        candidates = candidates[:args.limit]
    write_json(out / "shortlist.json", candidates)
    # Disable the pipeline's source-copying logger before it is constructed.
    overlay = out / "inference_config.yml"
    overlay.write_text(
        f"_BASE_CONFIG_: '{args.config}'\n"
        "GENERAL:\n  LOGGING:\n    IS_LOGGING: False\n"
        "  RESUME:\n    IS_RESUME: False\n"
        "VAL:\n  IS_VALIDATE: False\n"
        "OPTIMIZER:\n  NUM_WORKERS: 0\n"
        f"DATASET:\n  portion: {json.dumps(sorted({r['seq'] for r in candidates}, key=int))}\n"
    )
    pline = PipelineDetection_v1_0(path_cfg=str(overlay), mode="test")
    pline.load_dict_model(str(args.model), is_strict=True)
    pline.network.eval()
    fuser = pline.network.fuser
    shape = (fuser.patch_grid_y, fuser.patch_grid_x)
    count = int(np.prod(shape))
    xs, ys = fuser._patch_centers_xy(torch.device("cpu"), torch.float32)
    x_centers = xs.numpy().reshape(shape)[0].copy()
    y_centers = ys.numpy().reshape(shape)[:, 0].copy()
    roi = np.asarray(fuser.point_cloud_range, dtype=np.float32)
    dx = fuser.patch_x * fuser.voxel_size[0]
    dy = fuser.patch_y * fuser.voxel_size[1]
    assert np.isclose(len(x_centers) * dx, roi[3] - roi[0])
    assert np.isclose(len(y_centers) * dy, roi[4] - roi[1])
    captured = []
    original_scores = fuser._dec_control_scores
    original_forward = fuser.forward

    def capture_scores(self, *positional, **keyword):
        result = original_scores(*positional, **keyword)
        captured.append((result[1].detach().cpu().numpy().copy(),
                         result[2].detach().cpu().numpy().copy()))
        return result

    fuser._dec_control_scores = types.MethodType(capture_scores, fuser)

    def forward_without_gt(self, batch_dict):
        # SECOND's preprocessor requires this key even in eval mode. Withhold
        # it specifically at the fuser boundary and restore it for the head.
        head_gt = batch_dict.pop("gt_boxes")
        try:
            return original_forward(batch_dict)
        finally:
            batch_dict["gt_boxes"] = head_gt

    fuser.forward = types.MethodType(forward_without_gt, fuser)
    index = {(str(item["meta"]["seq"]), str(item["meta"]["idx"]["rdr"])): i
             for i, item in enumerate(pline.dataset_test.list_dict_item)}
    digest = hashlib.sha256()
    with args.model.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    manifest = dict(
        config=str(args.config), checkpoint=str(args.model), checkpoint_sha256=digest.hexdigest(),
        checkpoint_load_strict=True, infer_mode="rlc", label_version="v1_0", split="test",
        gate_source="actual _dec_control_scores return[2] from network.eval(); gt_boxes withheld from fuser input",
        grid_shape_yx=list(shape), patch_size_xy_m=[dx, dy], roi_xyz=roi.tolist(),
        flatten_order="batch, y, x (x fastest)", foreground_margin_m=fuser.patch_dec_fg_margin,
        shortlist_source=str(args.sampled_csv),
        shortlist_rule="Within each of 7 weather pools (24 existing sampled frames each), descending sampled FG-BG gap ranks at quantiles 0, 0.5, 0.75. Illustrative shortlist, not an unbiased evaluation sample.",
        storage="float32 full gate and probability, GT boxes, bool FG mask and grid centers only; raw data referenced",
        frames=[],
    )
    print(f"Full gate grid: {shape}, {count} patches/frame; {len(candidates)} frames", flush=True)
    try:
        with torch.no_grad():
            for number, candidate in enumerate(candidates):
                dataset_index = index[(candidate["seq"], candidate["radar_id"])]
                item = pline.dataset_test[dataset_index]
                batch = pline.dataset_test.collate_fn([item])
                meta = batch["meta"][0]
                gt = batch["gt_boxes"].clone()
                # A separate reference is used only after the model has predicted gate.
                batch["avail_feats"] = pline.infer_mode_to_avail_feats("rlc")
                captured.clear()
                pline.network(batch)
                assert len(captured) == 1, f"Expected one gate call, got {len(captured)}"
                probability, gate = captured[0]
                assert gate.size == count and np.isfinite(gate).all()
                assert probability.size == count and np.isfinite(probability).all()
                assert gate.min() >= 0 and gate.max() <= 1
                mask, _, _, _ = fuser._gt_patch_targets(
                    {"gt_boxes": gt}, count, torch.device("cpu"), fuser.dec_control_num_classes)
                assert mask is not None
                mask = mask.numpy().reshape(shape)
                boxes = gt[0].cpu().numpy()
                boxes = boxes[(boxes[:, 3] > 0) & (boxes[:, 4] > 0) & (boxes[:, 7] > 0)]
                gate = gate.reshape(shape).astype(np.float32)
                basename = f"seq{meta['seq']}_rdr{meta['idx']['rdr']}"
                np.savez_compressed(
                    out / f"{basename}.npz", gate=gate,
                    gate_probability=probability.reshape(shape).astype(np.float32),
                    gt_boxes=boxes.astype(np.float32), foreground_mask=mask,
                    x_centers=x_centers, y_centers=y_centers, roi_xyz=roi,
                )
                fg_mean, bg_mean = float(gate[mask].mean()), float(gate[~mask].mean())
                frame = dict(candidate, id=basename, archive=f"{basename}.npz",
                             camera_id=meta["idx"]["camf"], lidar_id=meta["idx"]["ldr64"],
                             weather=infer_weather(meta), camera_path=meta["path"]["front"],
                             lidar_path=meta["path"]["ldr64"], label_path=meta["label_v1_0"],
                             lidar_calibration=meta["calib"], num_gt=len(boxes),
                             foreground_patches=int(mask.sum()), full_patches=count,
                             gate_fg_mean=fg_mean, gate_bg_mean=bg_mean, gate_gap=fg_mean-bg_mean,
                             gate_max=float(gate.max()), gate_p99=float(np.quantile(gate, .99)))
                manifest["frames"].append(frame)
                manifest["peak_allocated_gpu_mib"] = torch.cuda.max_memory_allocated() / 2**20
                write_json(out / "manifest.json", manifest)
                print(f"[{number+1}/{len(candidates)}] {basename} {frame['weather']} "
                      f"GT={len(boxes)} FG={fg_mean:.3f} BG={bg_mean:.3f}", flush=True)
                # The dataset stores each loaded item; release raw data in RAM too.
                pline.dataset_test.list_dict_item[dataset_index] = {"meta": meta}
                del batch, item
    finally:
        fuser._dec_control_scores = original_scores
        fuser.forward = original_forward
    fields = ["id", "weather", "num_gt", "shortlist_rank", "foreground_patches", "full_patches",
              "gate_fg_mean", "gate_bg_mean", "gate_gap", "gate_max", "camera_id", "lidar_id"]
    with (out / "frame_metrics.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(manifest["frames"])
    print(f"Finished. Export directory: {sum(p.stat().st_size for p in out.iterdir() if p.is_file()) / 2**20:.2f} MiB")


def camera_image(frame):
    from PIL import Image
    with Image.open(frame["camera_path"]) as img:
        # front0 is the left 1280-pixel half of the stereo image used by this model.
        result = img.crop((0, 0, 1280, 720)).convert("RGB")
        return np.asarray(result)


def lidar_points(frame, roi):
    points = np.loadtxt(frame["lidar_path"], skiprows=13, usecols=(0, 1, 2), dtype=np.float32)
    keep = (np.abs(points[:, 0]) > .01) | (np.abs(points[:, 1]) > .01)
    points = points[keep] + np.asarray(frame["lidar_calibration"], dtype=np.float32)
    keep = ((points >= roi[:3]) & (points <= roi[3:])).all(axis=1)
    return points[keep]


def draw_boxes(ax, boxes, numbered=False):
    from matplotlib.patches import Polygon
    import matplotlib.patheffects as pe
    for index, box in enumerate(boxes):
        x, y, _, length, width, _, theta = box[:7]
        local = np.array([[1, 1], [1, -1], [-1, -1], [-1, 1]]) * [length/2, width/2]
        c, s = np.cos(theta), np.sin(theta)
        corners = local @ np.array([[c, s], [-s, c]]) + [x, y]
        patch = Polygon(corners, closed=True, fill=False, edgecolor="#51ffcf", linewidth=1.1)
        patch.set_path_effects([pe.Stroke(linewidth=1.8, foreground="#132b30"), pe.Normal()])
        ax.add_patch(patch)
        if numbered:
            ax.text(x, y+width/2+.5, str(index+1), fontsize=6, ha="center", color="white",
                    path_effects=[pe.withStroke(linewidth=1.3, foreground="black")], clip_on=True)


def gate_panel(ax, data, frame, labels=True):
    roi = data["roi_xyz"]
    heat = ax.imshow(data["gate"], origin="lower", extent=[roi[0], roi[3], roi[1], roi[4]],
                     interpolation="nearest", cmap="magma", vmin=0, vmax=1, aspect="equal")
    draw_boxes(ax, data["gt_boxes"])
    ax.set_xlim(roi[0], roi[3])
    ax.set_ylim(roi[1], roi[4])
    ax.set_xticks([0, 20, 40, 60, 72])
    ax.set_yticks([-6, 0, 6])
    if labels:
        ax.set_xlabel("Forward x (m)", labelpad=2)
        ax.set_ylabel("y (m)", labelpad=2)
    return heat


def render(args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.backends.backend_pdf import PdfPages

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.titlesize": 10, "axes.labelsize": 8, "xtick.labelsize": 7,
                         "ytick.labelsize": 7, "pdf.fonttype": 42, "ps.fonttype": 42})
    out = args.out_dir
    manifest = json.loads((out / "manifest.json").read_text())
    frames = manifest["frames"]
    if args.contact_sheet:
        with PdfPages(out / "candidate_contact_sheet.pdf") as pdf:
            for start in range(0, len(frames), 7):
                page = frames[start:start+7]
                fig, axes = plt.subplots(len(page), 2, figsize=(10, 1.7*len(page)), squeeze=False,
                                         gridspec_kw={"width_ratios": [1, 1.3]})
                for row, frame in enumerate(page):
                    with np.load(out / frame["archive"]) as data:
                        axes[row, 0].imshow(camera_image(frame))
                        axes[row, 0].axis("off")
                        axes[row, 0].set_title(f"{NAMES[frame['weather']]}  |  {frame['id']}", fontsize=8)
                        gate_panel(axes[row, 1], data, frame)
                        axes[row, 1].set_title(
                            f"GT {frame['num_gt']}  |  FG {frame['gate_fg_mean']:.3f}  "
                            f"BG {frame['gate_bg_mean']:.3f}  |  fixed scale [0,1]", fontsize=8)
                fig.subplots_adjust(left=.055, right=.975, top=.978, bottom=.035,
                                    wspace=.25, hspace=.55)
                fig.savefig(out / f"candidate_contact_sheet_{start//7+1}.png", dpi=130)
                pdf.savefig(fig, dpi=130)
                plt.close(fig)
    if not args.select:
        return
    lookup = {frame["id"]: frame for frame in frames}
    selected = [lookup[key] for key in args.select.split(",")]
    ncols = len(selected)
    fig = plt.figure(figsize=(5*ncols, 5.6))
    grid = fig.add_gridspec(3, ncols, height_ratios=[2.7, .9, .9],
                           left=.055, right=.98, top=.91, bottom=.16, hspace=.34, wspace=.13)
    for column, frame in enumerate(selected):
        with np.load(out / frame["archive"]) as data:
            camera = fig.add_subplot(grid[0, column])
            camera.imshow(camera_image(frame))
            camera.set_axis_off()
            camera.set_title(f"({chr(97+column)}) {NAMES[frame['weather']]}  |  Sequence {frame['seq']}, frame {frame['radar_id']}",
                             fontsize=10, fontweight="bold", pad=7)
            camera.text(.018, .035, "Front camera", transform=camera.transAxes, color="white", fontsize=8,
                        bbox=dict(facecolor="#16202d", edgecolor="none", alpha=.75, pad=3))
            points_ax = fig.add_subplot(grid[1, column])
            roi = data["roi_xyz"]
            points = lidar_points(frame, roi)
            points_ax.set_facecolor("#101c2c")
            points_ax.scatter(points[:, 0], points[:, 1], s=.35, c="#b9c9dd", alpha=.65,
                              linewidths=0, rasterized=True)
            draw_boxes(points_ax, data["gt_boxes"])
            points_ax.set(xlim=(roi[0], roi[3]), ylim=(roi[1], roi[4]), aspect="equal")
            points_ax.set_xticks([0, 20, 40, 60, 72])
            points_ax.tick_params(labelbottom=False)
            points_ax.set_yticks([-6, 0, 6])
            points_ax.set_ylabel("y (m)", labelpad=2)
            points_ax.set_title("LiDAR BEV + GT", loc="left", fontsize=9, pad=4)
            gate_ax = fig.add_subplot(grid[2, column])
            heat = gate_panel(gate_ax, data, frame)
            gate_ax.set_title("Predicted foreground gate + GT", loc="left", fontsize=9, pad=4)
    cax = fig.add_axes([.35, .053, .31, .018])
    cb = fig.colorbar(heat, cax=cax, orientation="horizontal", ticks=[0, .25, .5, .75, 1])
    cb.ax.tick_params(labelsize=7, pad=2, length=2)
    cb.set_label("Gate value (shared scale)", fontsize=8, labelpad=2)
    fig.legend(handles=[Line2D([0], [0], color="#35b994", lw=1.5, label="Sedan GT")],
               loc="lower left", bbox_to_anchor=(.055, .035), frameon=False, fontsize=8)
    fig.text(.98, .052, "0.8 m patches · no smoothing", ha="right", fontsize=7, color="#45515d")
    stem = out / "paper_fig4_taskdec_bev_gate_draft"
    fig.savefig(stem.with_suffix(".png"), dpi=220)
    fig.savefig(stem.with_suffix(".pdf"), dpi=180)
    plt.close(fig)
    write_json(out / "selected_frames.json", dict(
        frames=args.select.split(","), shared_gate_color_range=[0, 1], interpolation="nearest",
        view="full x/y model ROI, x-forward to right; camera shows original front0 field of view",
        caption=("Spatial foreground gating on K-Radar v1.0 test scenes. Each column shows the front camera, "
                 "calibrated LiDAR BEV, and the predicted TaskDec foreground gate. Green outlines denote Sedan "
                 "ground truth and are used only for reference. Gate values are read from the R+L+C model "
                 "forward pass with GT boxes withheld from the fuser, displayed on the complete 0.8 m patch grid with a shared "
                 "[0, 1] scale and no smoothing. Camera views provide scene context and cover a wider field "
                 "of view than the BEV evaluation ROI. These selected scenes illustrate spatial responses; "
                 "they are not an aggregate performance comparison.")))
    print(f"Rendered {stem}; directory {sum(p.stat().st_size for p in out.iterdir() if p.is_file()) / 2**20:.2f} MiB")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["export", "render"])
    parser.add_argument("--out-dir", type=Path, default=ROOT / "analysis_exports/taskdec_bev_gate_fig4_260910")
    parser.add_argument("--config", type=Path, default=EXP / "config.yml")
    parser.add_argument("--model", type=Path, default=EXP / "models/model_0.pt")
    parser.add_argument("--sampled-csv", type=Path,
                        default=ROOT / "analysis_exports/taskdec_patch_pca_weather_260909/taskdec_patch_states_pca.csv")
    parser.add_argument("--gpu", default="3")
    parser.add_argument("--limit", type=int, default=0, help="Optional smoke-run frame limit")
    parser.add_argument("--contact-sheet", action="store_true")
    parser.add_argument("--select", default="", help="Comma-separated shortlist frame IDs to export or render")
    args = parser.parse_args()
    os.chdir(ROOT)
    args.out_dir = args.out_dir.resolve()
    (export if args.mode == "export" else render)(args)


if __name__ == "__main__":
    main()
