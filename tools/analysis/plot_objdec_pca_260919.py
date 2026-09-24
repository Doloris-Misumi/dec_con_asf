#!/usr/bin/env python3
"""Readable ObjDec PCA plots; reuse saved coordinates without refitting them."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np
from scipy.stats import gaussian_kde
from objdec_plot_palette import MODALITY_COLORS, color_modality_labels

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ['raw', 'common', 'unique']
TITLES = ['Input representations', 'Shared representations', 'Modality-specific representations']
MODALITIES = ['Camera', 'LiDAR', '4D Radar']
COLORS = MODALITY_COLORS
MARKERS = ['o', '^', 's']
WEATHERS = ['normal', 'overcast', 'fog', 'rain', 'sleet', 'lightsnow', 'heavysnow']
LABELS = ['Normal', 'Overcast', 'Fog', 'Rain', 'Sleet', 'Light snow', 'Heavy snow']


def style():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none',
                         'axes.spines.top': False, 'axes.spines.right': False})


def save(fig, out, name):
    color_modality_labels(fig)
    for suffix in ['png', 'pdf', 'svg']:
        fig.savefig(out / (name + '.' + suffix), dpi=240, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def limits(x):
    lo, hi = np.min(x, axis=0), np.max(x, axis=0)
    span = np.maximum(hi - lo, 1e-4)
    return lo - .10 * span, hi + .10 * span


def density_outline(ax, x, color):
    """Enclose about 80% of KDE mass; never label this a confidence interval."""
    if len(x) < 8:
        return
    eig = np.linalg.eigvalsh(np.cov(x.T))
    if eig[0] < 1e-8 or eig[-1] / eig[0] > 1e5:
        return  # Do not inflate a nearly degenerate camera distribution.
    kde = gaussian_kde(x.T)
    lo, hi = limits(x)
    gx, gy = np.meshgrid(np.linspace(lo[0], hi[0], 80), np.linspace(lo[1], hi[1], 80))
    zz = kde(np.vstack([gx.ravel(), gy.ravel()])).reshape(gx.shape)
    ranked = np.sort(zz.ravel())[::-1]
    threshold = ranked[min(np.searchsorted(np.cumsum(ranked), .8 * ranked.sum()), len(ranked)-1)]
    ax.contour(gx, gy, zz, levels=[threshold], colors=[color], linewidths=.9, alpha=.65)


def selected_pairs(data, weather, seed):
    rng = np.random.default_rng(seed)
    mask = ((data['raw_weather'] == weather) & (data['raw_foreground'] == 1)
            & (data['raw_modality'] == 'Camera'))
    chosen = set()
    for frame in np.unique(data['raw_frame_idx'][mask]):
        ix = np.flatnonzero(mask & (data['raw_frame_idx'] == frame))
        ix = rng.choice(ix, min(6, len(ix)), replace=False)
        chosen.update((int(frame), int(data['raw_patch_idx'][i])) for i in ix)
    return chosen


def plot_grid(data, out, weathers, name):
    fig, axes = plt.subplots(len(weathers), 3, figsize=(11.6, 2.75 * len(weathers) + .6),
                             squeeze=False)
    selection = {w: selected_pairs(data, w, 20260919 + WEATHERS.index(w)) for w in weathers}
    for j, feature in enumerate(FEATURES):
        coords = data[feature + '_pca']
        fg = data[feature + '_foreground'] == 1
        frames = data[feature + '_frame_idx']
        weather = data[feature + '_weather']
        mods = data[feature + '_modality']
        patches = data[feature + '_patch_idx']
        # All points in the displayed weather groups determine the limits, not a percentile crop.
        lo, hi = limits(coords[fg & np.isin(weather, weathers)])
        for i, w in enumerate(weathers):
            ax = axes[i, j]
            for m, color, marker in zip(MODALITIES, COLORS, MARKERS):
                mask = fg & (weather == w) & (mods == m)
                all_ids = np.flatnonzero(mask)
                ids = [k for k in all_ids if (int(frames[k]), int(patches[k])) in selection[w]]
                density_outline(ax, coords[all_ids], color)
                ax.scatter(*coords[ids].T, s=24, c=color, marker=marker, alpha=.66,
                           edgecolors='white', linewidths=.25, zorder=3)
                frame_means = np.array([coords[mask & (frames == fr)].mean(0)
                                        for fr in np.unique(frames[mask])])
                center = frame_means.mean(0)
                ax.scatter(*center, s=96, c=color, marker=marker,
                           edgecolors='#1F2937', linewidths=1.15, zorder=5)
            ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1])
            ax.set_aspect('equal', adjustable='box')
            ax.xaxis.set_major_locator(MaxNLocator(4)); ax.yaxis.set_major_locator(MaxNLocator(4))
            ax.tick_params(labelsize=8, color='#98A2B3')
            ax.grid(alpha=.12, linewidth=.5)
            if i == 0:
                ax.set_title(TITLES[j], fontweight='bold', fontsize=11, pad=12)
            ratio = data[feature + '_pca_explained'] * 100
            ax.set_xlabel(f'PC1 ({ratio[0]:.1f}%)')
            ax.set_ylabel((LABELS[WEATHERS.index(w)] + '\n' if j == 0 else '') + f'PC2 ({ratio[1]:.1f}%)')
    handles = [Line2D([], [], color=c, marker=m, linestyle='', markersize=7, label=n)
               for n,c,m in zip(MODALITIES,COLORS,MARKERS)]
    handles += [Line2D([], [], color='white', marker='o', markeredgecolor='#1F2937',
                       markersize=9, linestyle='', label='Frame-balanced center')]
    fig.legend(handles=handles, ncol=4, loc='upper center', bbox_to_anchor=(.53, 1.015), frameon=False)
    fig.text(.5, .004, 'Foreground patches | 24 frames per weather | Shared axes across weather within each column',
             ha='center', color='#475467', fontsize=9)
    fig.tight_layout(rect=(0,.025,1,.965), h_pad=1.6, w_pad=2)
    save(fig, out, name)
    return {w: len(selection[w]) for w in weathers}


def metrics(data, out):
    rows = []
    for f in FEATURES:
        for w in WEATHERS:
            base = (data[f+'_weather'] == w) & (data[f+'_foreground'] == 1)
            frame_values = []
            for fr in np.unique(data[f+'_frame_idx'][base]):
                xs, ids = [], []
                for m in MODALITIES:
                    ix = np.flatnonzero(base & (data[f+'_frame_idx'] == fr) & (data[f+'_modality'] == m))
                    ix = ix[np.argsort(data[f+'_patch_idx'][ix])]
                    ids.append(data[f+'_patch_idx'][ix])
                    x = data[f+'_features'][ix].astype(np.float64)
                    xs.append(x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12))
                assert all(np.array_equal(ids[0], v) for v in ids[1:])
                frame_values.append([np.sum(xs[a]*xs[b], axis=1).mean() for a,b in [(0,1),(0,2),(1,2)]])
            means = np.mean(frame_values, axis=0)
            rows.append(dict(weather=w, feature=f, frames=len(frame_values),
                             cosine_CL=means[0], cosine_CR=means[1], cosine_LR=means[2],
                             cosine_mean=means.mean()))
    with (out/'sampled_high_dimensional_cosine.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--npz', type=Path, default=ROOT/'analysis_exports/taskdec_patch_pca_weather_260909/taskdec_patch_states_pca.npz')
    ap.add_argument('--out-dir', type=Path, default=ROOT/'analysis_exports/objdec_pca_redesign_260919')
    args = ap.parse_args(); args.out_dir.mkdir(parents=True, exist_ok=True); style()
    with np.load(args.npz) as archive:
        data = {k: archive[k] for k in archive.files}
    for f in ['common','unique']:
        for field in ['weather','foreground','modality','frame_idx','patch_idx']:
            assert np.array_equal(data['raw_'+field], data[f+'_'+field]), (f,field)
    counts = plot_grid(data,args.out_dir,['normal','heavysnow'],'objdec_pca_normal_heavysnow')
    plot_grid(data,args.out_dir,WEATHERS,'objdec_pca_all_weather_appendix')
    rows = metrics(data,args.out_dir)
    (args.out_dir/'plot_manifest.json').write_text(json.dumps(dict(
        source=str(args.npz), seed=20260919, sampled_patches_per_modality=counts,
        pca='Original exported PCA coordinates; separate basis per representation, shared across all weather. Original fitting included foreground and sampled background.',
        density='Approximate 80% KDE mass contour when covariance is nonsingular; not a confidence interval.',
        centers='Equal-weight average of per-frame means of exported foreground patches.',
        limitations='168 sampled frames only. This is not the full-test mean analysis. Cross-column distances use different feature scales.',
        full_dimensional_metrics=rows),indent=2)+'\n')
    print(args.out_dir)


if __name__ == '__main__':
    main()
