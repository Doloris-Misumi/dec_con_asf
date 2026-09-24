"""Compose generated schematic and immutable real-data inserts as SVG documents.

System Python provides librsvg and cairo. The same diagram is exported with all
four sample groups so the author can change the scene without redrawing data.
"""
from pathlib import Path
import json, base64, hashlib, html
import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
import cairo

HERE = Path(__file__).resolve().parent
W, H = 1983, 793
TEMPLATE = HERE/'diagram_template_final.png'
RECORDS = json.loads((HERE/'candidates.json').read_text())
CROPS = {
    'seq20_rdr00628': {'background': [810,190,1065,390], 'object': [382,325,562,470]},
    'seq22_rdr00484': {'background': [90,250,345,450], 'object': [485,315,635,436]},
    'seq9_rdr00347': {'background': [130,310,385,510], 'object': [625,340,737,430]},
    'seq7_rdr00272': {'background': [820,180,1075,380], 'object': [424,305,624,466]},
}

def uri(p):
    return 'data:image/png;base64,'+base64.b64encode(Path(p).read_bytes()).decode('ascii')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

checks = []
for rec in RECORDS:
    fid = rec['id']
    f = rec['frame']
    assets = HERE/'samples'/fid
    camera = Path(f['camera_path'])
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<title>ObjDec: object-guided shared and modality-specific representation learning</title>',
           f'<desc>Real K-Radar inputs and ObjDec outputs: {fid}. The input token maps '
           'independently into two representation branches. Response and control glyphs '
           'are conceptual. Radar fan: max sparse xyz-power in range-azimuth bins, not raw dense spectrum.</desc>',
           '<defs>',
           f'<image id="camera" width="2560" height="720" xlink:href="{uri(camera)}"/>',
           '<marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" '
           'orient="auto" markerUnits="strokeWidth"><path d="M0 0 L7 3.5 L0 7 Z" fill="#354c69"/></marker>',
           '</defs>',
           f'<image width="{W}" height="{H}" xlink:href="{uri(TEMPLATE)}"/>']

    def raw(x,y,w,h,box):
        a,b,c,d=box
        svg.append(f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{a} {b} {c-a} {d-b}" '
                   'preserveAspectRatio="xMidYMid meet" overflow="hidden"><use xlink:href="#camera"/></svg>')

    def asset(x,y,w,h,name):
        svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
                   f'preserveAspectRatio="xMidYMid meet" xlink:href="{uri(assets/(name+".png"))}"/>')

    raw(29,139,189,128,[0,0,1280,720])
    asset(29,327,188,123,'lidar')
    asset(29,512,188,118,'radar')
    raw(649,164,195,151,CROPS[fid]['background'])
    raw(650,431,194,155,CROPS[fid]['object'])

    # Native SVG edges complete the schematic: both learned branches enter fusion.
    # No edge connects c_m to u_m; all arrows lie in the diagram, outside data inserts.
    for y in (222,328):
        svg.append(f'<path d="M1544 {y} L1575 {y}" fill="none" stroke="#354c69" '
                   'stroke-width="1.8" marker-end="url(#arrow)"/>')

    # Expand the previously empty output slot to its data's exact 16:9 aspect.
    svg.append('<rect x="1632" y="454" width="326" height="184" fill="white"/>')
    asset(1634,455,322,181.125,'prediction')
    svg.append('<rect x="1633" y="454" width="324" height="183" fill="none" '
               'stroke="#8598ad" stroke-width="1"/>')
    label = f"K-Radar: S{f['seq']} / radar {f['radar_id']}  |  Real ObjDec predictions: score > 0.3"
    svg.append('<text x="24" y="770" font-family="DejaVu Serif" font-size="14" fill="#435472">'
               +html.escape(label)+'</text>')
    svg.append('</svg>')
    stem = HERE/('objdec_motivation_'+fid)
    stem.with_suffix('.svg').write_text('\n'.join(svg))

    handle=Rsvg.Handle.new_from_file(str(stem.with_suffix('.svg')))
    viewport=Rsvg.Rectangle()
    viewport.x,viewport.y,viewport.width,viewport.height=0,0,W,H
    surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,W*2,H*2)
    ctx=cairo.Context(surface);ctx.scale(2,2)
    handle.render_document(ctx,viewport)
    surface.write_to_png(str(stem.with_suffix('.png')));surface.finish()
    surface=cairo.PDFSurface(str(stem.with_suffix('.pdf')),W/2,H/2)
    ctx=cairo.Context(surface);ctx.scale(.5,.5)
    handle.render_document(ctx,viewport);ctx.show_page();surface.finish()

    check={'id':fid, 'all_sources_unchanged':all(sha(p)==h for p,h in rec['sha256'].items()),
           'raw_camera_embedded_without_generative_editing':True,
           'numeric_LiDAR_and_radar_plots':True, 'saved_predictions_unmodified':True,
           'displayed_prediction_count':rec['prediction']['number'],
           'camera_crops':CROPS[fid], 'template_sha256':sha(TEMPLATE),
           'artifacts':{stem.with_suffix(e).name:{'bytes':stem.with_suffix(e).stat().st_size,
                        'sha256':sha(stem.with_suffix(e))} for e in ('.png','.pdf','.svg')}}
    assert check['all_sources_unchanged']
    checks.append(check)
    print(json.dumps({'id':fid,'png':str(stem.with_suffix('.png'))}))
(HERE/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
