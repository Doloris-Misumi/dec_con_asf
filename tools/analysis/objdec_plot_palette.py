"""Modality colors matched to the author's blue/green/purple reference figure."""

MODALITY_COLORS = ['#4A9EEB', '#58B77A', '#9672D0']
MODALITY_INK = ['#267FC3', '#2E8B52', '#7650B2']
MODALITY_NAMES = ['Camera', 'LiDAR', '4D Radar']
REPRESENTATION_COLORS = ['#8994A5', '#DE7777', '#E6AD55']


def color_modality_labels(fig):
    """Categorical text uses modality colors; quantitative color scales stay intact."""
    colors = dict(zip(MODALITY_NAMES, MODALITY_INK))
    for ax in fig.axes:
        for text in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
            if text.get_text() in colors:
                text.set_color(colors[text.get_text()])
    for legend in fig.legends:
        for text in legend.get_texts():
            if text.get_text() in colors:
                text.set_color(colors[text.get_text()])
