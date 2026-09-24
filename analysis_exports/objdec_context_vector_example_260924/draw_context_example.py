#!/usr/bin/env python3
"""Editable vector example for the object-context branch of ObjDec."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch

OUT = Path(__file__).resolve().parent
INK = '#23354A'
LINE = '#53667B'
RED = '#BF535B'
CELLS = ['#B6C1CD', '#8294A8', '#A5B3C2', '#6F839B', '#96A7B9', '#BBC5D1']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                     'svg.fonttype': 'none', 'pdf.fonttype': 42,
                     'mathtext.fontset': 'dejavusans'})


def box(ax, x, y, w, h, label='', fc='#F1F5F9', ec=LINE, fontsize=12):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle='round,pad=0.02,rounding_size=1.0',
        facecolor=fc, edgecolor=ec, linewidth=1.1))
    if label:
        ax.text(x+w/2, y+h/2, label, ha='center', va='center',
                color=INK, fontsize=fontsize, linespacing=1.45)


def arrow(ax, a, b, color=LINE, dashed=False):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>',
        mutation_scale=12, linewidth=1.3, color=color,
        linestyle=(0, (3, 3)) if dashed else '-',
        shrinkA=0, shrinkB=0))


def vector(ax, x, y, w, h):
    box(ax, x, y, w, h, fc='#F8FAFC', ec='#687B91')
    pad = w*.04
    gap = w*.019
    cell_w = (w-2*pad-7*gap)/8
    for i in range(8):
        left = x+pad+i*(cell_w+gap)
        if i == 5:
            ax.text(left+cell_w/2, y+h/2, '···', ha='center', va='center',
                    fontsize=13, color=LINE)
        else:
            ax.add_patch(Rectangle((left, y+h*.18), cell_w, h*.64,
                facecolor=CELLS[i % len(CELLS)], edgecolor='none'))


def save(fig, name, transparent=False):
    for ext in ['svg', 'pdf', 'png']:
        fig.savefig(OUT/f'{name}.{ext}', dpi=300, transparent=transparent,
                    facecolor='none' if transparent else 'white')
    plt.close(fig)


def main():
    fig = plt.figure(figsize=(15.2, 5.2))
    ax = fig.add_axes([.015, .035, .97, .93])
    ax.set(xlim=(0, 120), ylim=(0, 45))
    ax.set_axis_off()
    ax.text(2, 42.5, 'Object context generation', fontsize=20,
            fontweight='bold', color=INK)
    ax.text(2, 39, 'K-Radar single-class setting', fontsize=11, color=LINE)

    box(ax, 2, 23, 9, 6, '$h$', fc='#F1F3F6', fontsize=19)
    ax.text(6.5, 19.5, 'Pooled\ndescriptor', ha='center', va='top',
            fontsize=10, color=LINE, linespacing=1.3)
    arrow(ax, (11, 26), (16, 26))
    box(ax, 16, 21.8, 21, 8.4, 'Objectness head\nMLP + sigmoid', fontsize=12)
    arrow(ax, (37, 26), (43.3, 26))
    ax.add_patch(Circle((46, 26), 2.7, facecolor='#EDF1F5', edgecolor=LINE, linewidth=1.2))
    ax.text(46, 26, '$r$', ha='center', va='center', fontsize=20, color=INK)
    ax.text(46, 32.4, 'Object probability', ha='center', fontsize=10.5, color=LINE)
    arrow(ax, (48.7, 26), (55, 26))
    box(ax, 55, 21.8, 18, 8.4, 'Embedding\nLinear + tanh', fontsize=12)
    arrow(ax, (73, 26), (79, 26))
    vector(ax, 79, 23, 22, 6)
    ax.text(90, 32.4, 'Object context $z$', ha='center', fontsize=14,
            fontweight='bold', color=INK)
    ax.text(90, 19, 'One 256-D vector\nper patch', ha='center', va='top',
            fontsize=11, color=LINE, linespacing=1.35)
    arrow(ax, (101, 26), (107.7, 26))
    ax.add_patch(Circle((110, 26), 2.3, facecolor='white', edgecolor=LINE, linewidth=1.2))
    ax.text(110, 26, '×', ha='center', va='center', fontsize=22, color=INK)
    ax.add_patch(Circle((110, 36.5), 2.7, facecolor='#FBEAEC', edgecolor=RED, linewidth=1.2))
    ax.text(110, 36.5, '$g$', ha='center', va='center', fontsize=18, color=INK)
    ax.text(110, 42, 'Foreground gate', ha='center', fontsize=10.5, color=LINE)
    arrow(ax, (110, 33.8), (110, 28.3))
    arrow(ax, (112.3, 26), (119, 26))
    ax.text(115.5, 29.6, '$gz$', ha='center', fontsize=16, color=INK)
    ax.text(110.7, 18.9, 'To query / output\ncontext injection', ha='center', va='top',
            fontsize=10, color=LINE, linespacing=1.35)

    box(ax, 16, 5, 21, 6.5, 'GT foreground labels', fc='#FFF7F7', ec=RED, fontsize=10.5)
    box(ax, 40, 5, 12, 6.5, '$\\mathcal{L}_{\\mathrm{ctx}}$', fc='#FFF7F7', ec=RED, fontsize=17)
    arrow(ax, (37, 8.25), (40, 8.25), RED, True)
    arrow(ax, (46, 23.3), (46, 11.5), RED, True)
    ax.text(55, 8.25, 'Training only: supervise objectness, before embedding.',
            ha='left', va='center', color=RED, fontsize=10.5)
    save(fig, 'objdec_object_context_example')

    # Separate reusable, transparent asset without caption or surrounding operators.
    fig = plt.figure(figsize=(4.4, 1.2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 24), ylim=(0, 7.5))
    ax.set_axis_off()
    vector(ax, 1, .75, 22, 6)
    save(fig, 'objdec_context_vector_asset', transparent=True)
    (OUT/'README.md').write_text(
        '# ObjDec object context示意\n\n'
        '`objdec_object_context_example`：完整示意，含objectness预测、向量映射、gate乘法与训练监督。\n'
        '`objdec_context_vector_asset`：透明背景纯向量条，可直接放入PPT。\n'
        '每组提供SVG、PDF和300 dpi PNG。分段色块仅为向量结构示意，不是实际激活值；'
        '每个patch产生一个256维z，并非多个独立token。\n'
    )
    print(OUT)


if __name__ == '__main__':
    main()
