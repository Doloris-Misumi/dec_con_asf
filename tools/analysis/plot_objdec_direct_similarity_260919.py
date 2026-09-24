#!/usr/bin/env python3
"""Display original-space, matched-patch cosine statistics without projection."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from plot_objdec_pca_260919 import style, save, plt, FEATURES, WEATHERS, LABELS
from objdec_plot_palette import REPRESENTATION_COLORS

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'analysis_exports/objdec_fulltest_weather_260919'
OUT = SOURCE / 'paper_visuals'
SHOWN = ['normal', 'heavysnow']
NAMES = ['Input', 'Shared', 'Modality-specific']
MODS = ['Camera', 'LiDAR', '4D Radar']
PAIRS = [(0, 1), (0, 2), (1, 2)]
PAIR_NAMES = ['Camera–LiDAR', 'Camera–4D Radar', 'LiDAR–4D Radar']
REP_COLORS = REPRESENTATION_COLORS


def load():
    status = json.loads((SOURCE / 'status.json').read_text())
    assert status['phase'] == 'complete' and status['completed'] == 10065
    paths = sorted((SOURCE / 'chunks').glob('frames_*.npz'))
    keys = ['dataset_index', 'weather', 'seq', 'paired_cosine', 'num_foreground']
    parts = []
    for path in paths:
        with np.load(path) as z:
            parts.append({k: z[k] for k in keys})
    data = {k: np.concatenate([a[k] for a in parts]) for k in keys}
    assert np.array_equal(np.sort(data['dataset_index']), np.arange(10065))
    assert np.isfinite(data['paired_cosine']).all()
    assert (data['num_foreground'] > 0).all()
    assert np.max(np.abs(data['paired_cosine'])) <= 1 + 1e-6
    return data, paths


def matrices(data):
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.2))
    cmap = plt.get_cmap('RdBu_r').copy()
    cmap.set_bad('#EFF2F6')
    for i, w in enumerate(SHOWN):
        mask = data['weather'] == w
        values = data['paired_cosine'][mask].astype(float).mean(0)
        for j in range(3):
            ax = axes[i, j]
            mat = np.full((3, 3), np.nan)
            for k, (a, b) in enumerate(PAIRS):
                mat[a, b] = mat[b, a] = values[j, k]
            im = ax.imshow(np.ma.masked_invalid(mat), cmap=cmap, vmin=-1, vmax=1)
            ax.set_xticks(range(3), MODS, fontsize=8)
            ax.set_yticks(range(3), MODS, fontsize=8)
            if i == 0:
                ax.set_title(NAMES[j], fontsize=12, fontweight='bold', pad=12)
            for a in range(3):
                for b in range(3):
                    val = mat[a, b]
                    ax.text(b, a, '—' if a == b else f'{val:.3f}', ha='center', va='center',
                            fontsize=12, color='white' if np.isfinite(val) and abs(val) > .65 else '#344054')
            ax.set_xticks(np.arange(-.5, 3, 1), minor=True)
            ax.set_yticks(np.arange(-.5, 3, 1), minor=True)
            ax.grid(which='minor', color='white', linewidth=2)
            ax.tick_params(which='both', length=0)
            for spine in ax.spines.values():
                spine.set_visible(False)
    fig.subplots_adjust(left=.20, right=.89, bottom=.15, top=.91, hspace=.35, wspace=.52)
    for i, w in enumerate(SHOWN):
        pos = axes[i, 0].get_position()
        fig.text(.015, (pos.y0 + pos.y1) / 2,
                 LABELS[WEATHERS.index(w)] + f'\nn = {int((data["weather"] == w).sum()):,}',
                 ha='left', va='center', fontsize=11, fontweight='bold', color='#344054')
    cbax = fig.add_axes([.925, .21, .017, .61])
    fig.colorbar(im, cax=cbax, label='Mean cosine similarity (256-D)')
    fig.text(.53, .035, 'Matched foreground patches → within-frame average → equal-frame weather average\n'
             'No PCA or other dimensionality reduction | Diagonal self-comparisons omitted',
             ha='center', fontsize=9, color='#475467')
    save(fig, OUT, 'objdec_fulltest_direct_similarity_matrices')


def distributions(data):
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.4), sharey=True)
    for i, w in enumerate(SHOWN):
        mask = data['weather'] == w
        for k in range(3):
            ax = axes[i, k]
            groups = [data['paired_cosine'][mask, j, k].astype(float) for j in range(3)]
            vp = ax.violinplot(groups, positions=np.arange(3), widths=.68,
                               showmeans=False, showmedians=False, showextrema=False,
                               points=250, bw_method='scott')
            for body, color in zip(vp['bodies'], REP_COLORS):
                body.set_facecolor(color)
                body.set_edgecolor(color)
                body.set_alpha(.42)
            for j, (x, color) in enumerate(zip(groups, REP_COLORS)):
                p5, q1, median, q3, p95 = np.quantile(x, [.05, .25, .5, .75, .95])
                ax.vlines(j, p5, p95, color=color, linewidth=1.4, zorder=3)
                ax.vlines(j, q1, q3, color=color, linewidth=5.5, zorder=4)
                ax.scatter(j, median, color='white', edgecolors=color, s=27, linewidths=1.5, zorder=5)
            ax.set_xticks(range(3), ['Input', 'Shared', 'Specific'], fontsize=9)
            ax.set_ylim(-1, 1.045)
            ax.set_yticks([-1, -.5, 0, .5, 1])
            ax.grid(axis='y', alpha=.18, linewidth=.6)
            ax.axhline(0, color='#98A2B3', linewidth=.65, zorder=0)
            if i == 0:
                ax.set_title(PAIR_NAMES[k], fontsize=11, fontweight='bold', pad=10)
            if k == 0:
                ax.set_ylabel('Per-frame mean cosine (256-D)')
    fig.subplots_adjust(left=.22, right=.985, bottom=.17, top=.92, hspace=.24, wspace=.14)
    for i, w in enumerate(SHOWN):
        pos = axes[i, 0].get_position()
        fig.text(.015, (pos.y0 + pos.y1) / 2,
                 LABELS[WEATHERS.index(w)] + f'\nn = {int((data["weather"] == w).sum()):,}',
                 ha='left', va='center', fontsize=11, fontweight='bold', color='#344054')
    fig.text(.57, .045, 'Each observation: one frame’s average over matched foreground patches\n'
             'Violin: density | Thick bar: 25–75% | Thin bar: 5–95% | White dot: median\n'
             'All frames included; descriptive distributions, not confidence intervals',
             ha='center', fontsize=9, color='#475467')
    save(fig, OUT, 'objdec_fulltest_direct_similarity_distributions')


def main():
    style()
    OUT.mkdir(exist_ok=True)
    data, paths = load()
    matrices(data)
    distributions(data)
    rows = []
    for w in WEATHERS:
        mask = data['weather'] == w
        for j, feature in enumerate(FEATURES):
            for k, pair in enumerate(PAIR_NAMES):
                x = data['paired_cosine'][mask, j, k].astype(float)
                row = dict(weather=w, feature=feature, pair=pair, frames=len(x),
                           mean=float(x.mean()), min=float(x.min()), max=float(x.max()))
                row.update(zip(['p05', 'p25', 'median', 'p75', 'p95'],
                               map(float, np.quantile(x, [.05, .25, .5, .75, .95]))))
                rows.append(row)
    with (OUT / 'direct_similarity_distribution_statistics.csv').open('w') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    manifest = dict(frames=len(data['weather']), source=str(SOURCE), shown_weather=SHOWN,
                    quantities='256-D cosine for matched foreground patch locations, averaged within frame; matrices then average equally over frames.',
                    distribution_unit='Frame-average patch cosine, not cosine of frame-average features or a distribution of individual patch cosines.',
                    subsampling=False, dimensionality_reduction=False,
                    diagonal='Not displayed; cross-modal comparisons only.',
                    limits='Common high cosine alone does not establish semantic alignment, noncollapse, or detection benefit. Weather/sequence dependence is not an independent-replicate confidence analysis.',
                    source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in paths + [Path(__file__).resolve()]})
    (OUT / 'direct_similarity_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(OUT)
    for row in rows:
        if row['weather'] in SHOWN and row['pair'] == PAIR_NAMES[-1]:
            print(json.dumps(row))


if __name__ == '__main__':
    main()
