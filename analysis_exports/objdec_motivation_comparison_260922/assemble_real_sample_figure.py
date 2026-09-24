"""Lay out immutable real-data inserts in an SVG publication document.

The schematic bitmap is produced by imagegen. Observation images are embedded
directly, and scientific prediction plots are embedded without generative edits.
Run with system Python, which provides librsvg/cairo for document rendering.
"""
from pathlib import Path
import base64
import json
import hashlib
import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
import cairo

HERE = Path(__file__).resolve().parent
ASSETS = HERE / 'real_sample_assets'
meta = json.loads((ASSETS / 'provenance.json').read_text())
camera_path = Path(meta['frame']['camera_path'])
template = HERE / 'token_template_v2.png'
WIDTH, HEIGHT = 1904, 826


def url(path):
    return 'data:image/png;base64,' + base64.b64encode(Path(path).read_bytes()).decode('ascii')


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
       f'width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
       '<title>ObjDec motivation: real synchronized K-Radar sample 13/00146</title>',
       '<desc>Parallel projections of a single per-modality token; direct real camera inserts, '
       'calibrated point-cloud projections, and saved ObjDec predictions. '
       'Middle-panel response glyphs and fusion controls are conceptual.</desc>',
       f'<defs><image id="raw-camera" width="2560" height="720" xlink:href="{url(camera_path)}"/></defs>',
       f'<image width="{WIDTH}" height="{HEIGHT}" xlink:href="{url(template)}"/>']


def raw_crop(x, y, w, h, crop):
    a, b, c, d = crop
    svg.append(f'<svg x="{x}" y="{y}" width="{w}" height="{h}" '
               f'viewBox="{a} {b} {c-a} {d-b}" preserveAspectRatio="xMidYMid meet" overflow="hidden">'
               '<use xlink:href="#raw-camera"/></svg>')


def scientific_insert(x, y, w, h, path):
    svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
               f'preserveAspectRatio="xMidYMid meet" xlink:href="{url(path)}"/>')


# Direct original-pixel photograph, cropped in SVG, not regenerated/repainted.
raw_crop(86, 123, 149, 151, meta['common_camera_viewport_xyxy'])
scientific_insert(86, 295, 149, 150, ASSETS / 'lidar_input.png')
scientific_insert(86, 469, 149, 151, ASSETS / 'radar_input.png')
raw_crop(691, 175, 166, 151, meta['middle_background_crop_xyxy'])
raw_crop(691, 453, 166, 152, meta['middle_object_crop_xyxy'])
scientific_insert(1763, 259, 120, 142, ASSETS / 'objdec_camera_crop.png')
svg.append('<text x="1823" y="422" font-family="DejaVu Serif" font-size="13" '
           'fill="#5f5136" text-anchor="middle">Pred. score &gt; 0.3</text>')

# Exact sample ID and distinction between measured data and explanatory glyphs.
svg.append('<rect x="1550" y="772" width="352" height="47" fill="white"/>')
svg.append('<text x="21" y="797" font-family="DejaVu Serif" font-size="15" fill="#435472">'
           'Real inputs and ObjDec predictions: K-Radar S13 / radar 00146</text>')
svg.append('<text x="1880" y="797" font-family="DejaVu Serif" font-size="15" '
           'fill="#435472" text-anchor="end">Representation / control glyphs: schematic</text>')
svg.append('</svg>')
out = HERE / 'objdec_motivation_real_kradar_v3'
out.with_suffix('.svg').write_text('\n'.join(svg))

handle = Rsvg.Handle.new_from_file(str(out.with_suffix('.svg')))
viewport = Rsvg.Rectangle()
viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, WIDTH, HEIGHT
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH * 2, HEIGHT * 2)
ctx = cairo.Context(surface)
ctx.scale(2, 2)
handle.render_document(ctx, viewport)
surface.write_to_png(str(out.with_suffix('.png')))
surface.finish()
pdf = cairo.PDFSurface(str(out.with_suffix('.pdf')), WIDTH / 2, HEIGHT / 2)
ctx = cairo.Context(pdf)
ctx.scale(.5, .5)
handle.render_document(ctx, viewport)
ctx.show_page()
pdf.finish()

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

checks = {
    'source_files_unchanged': all(sha(p) == h for p, h in meta['source_sha256'].items()),
    'embedded_raw_camera_sha256': sha(camera_path),
    'template_sha256': sha(template),
    'model_prediction_source_sha256': meta['prediction_npz_sha256'],
    'sensor_sample_ids': {'sequence': 13, 'radar': '00146', 'lidar': '00107', 'camera': '00321'},
    'raw_camera_is_embedded_directly': True,
    'generated_data_inserts': False,
    'predicted_boxes_drawn_without_changes': meta['displayed_boxes'],
    'tokens': 'Each t_m maps independently to c_m and u_m; original t_m bypass retained.',
    'artifacts': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                  for p in [out.with_suffix(e) for e in ['.svg', '.png', '.pdf']]},
}
assert checks['source_files_unchanged']
(HERE / 'real_sample_validation.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps(checks['artifacts'], indent=2))
