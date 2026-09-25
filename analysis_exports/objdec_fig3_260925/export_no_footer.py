#!/usr/bin/env python3
"""Re-export the selected empirical Fig.3 with only its footer removed."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'analysis_exports/objdec_visuals_blue_green_purple_260923/fulltest'
sys.path.insert(0, str(ROOT / 'tools/analysis'))
import numpy as np
import plot_objdec_fulltest_weather_260919 as full


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    full.style()
    data, basis, chunks = full.load()
    source_paths = chunks + [full.SOURCE / 'frame_mean_pca_basis.npz']
    before = {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    original_save = full.save
    audit = {}

    def save_without_footer(fig, out, name):
        footers = [t for t in fig.texts if t.get_text().startswith('Each point: one frame mean |')]
        assert len(footers) == 1
        audit['removed_footer'] = footers[0].get_text()
        footers[0].remove()
        audit['retained_figure_text'] = [t.get_text() for t in fig.texts]
        audit['axis_labels'] = [(a.get_xlabel(), a.get_ylabel()) for a in fig.axes]
        # The plotting function, projection, sampling, axes, colors, and layout
        # are otherwise unchanged. Tight export removes unused outer space.
        original_save(fig, out, name)

    full.OUT = OUT
    full.save = save_without_footer
    full.plot_frame_grid(data, basis, name='objdec_fig3_pca_normal_heavysnow_no_footer')
    with np.load(OLD / 'display_frame_ids.npz') as old, np.load(OUT / 'display_frame_ids.npz') as new:
        assert set(old.files) == set(new.files)
        assert all(np.array_equal(old[k], new[k]) for k in old.files)
        audit['display_frames_per_weather'] = {k: len(new[k]) for k in new.files}
    assert before == {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    audit.update(
        source_figure=str(OLD / 'objdec_fulltest_frame_pca_normal_heavysnow.pdf'),
        only_change='Remove bottom explanation; tight output bounds adapt automatically.',
        source_data_unchanged=True, projection_unchanged=True,
        selected_frames_unchanged=True, new_inference=False,
        frames=int(len(data['weather'])),
        frames_by_displayed_weather={w: int((data['weather'] == w).sum()) for w in ['normal', 'heavysnow']},
        dimensions=int(data['means'].shape[-1]),
        explained_variance_percent={f: (basis[f+'_explained']*100).tolist() for f in full.FEATURES},
        sources_sha256=before,
    )
    (OUT / 'validation.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({k: v for k, v in audit.items() if k != 'sources_sha256'}, indent=2))


if __name__ == '__main__':
    main()
