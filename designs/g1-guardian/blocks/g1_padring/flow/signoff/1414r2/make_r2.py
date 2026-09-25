"""Build g1_chip_top_1414_r2.gds from the r1 GDS of record. Metadata-only changes:
 (a) the two seal-ring registration TEXTs on 63/0 in the top cell get correct strings
     (position, layer, size/magnification, orientation, font and alignment kept);
 (b) cells whose names are listed in RENAME are renamed (modified stock-named cells).
Written without timestamps so the bytes are reproducible.
Run in the pinned container: klayout -b -r make_r2.py -rd src=<r1.gds> -rd dst=<r2.gds> [-rd rename=old:new,...]"""
import pya, hashlib, json
SRC_SHA = '629d303abf594ec90593f1d28a8d9ad19673ea6662780ba428a6d9c5685986ba'
PDK = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
assert hashlib.sha256(open(src, 'rb').read()).hexdigest() == SRC_SHA
try: rename
except NameError: rename = 'sg13g2_LevelDown:g1_LevelDown_polyres'
RENAME = dict(p.split(':') for p in rename.split(',') if p)
ly = pya.Layout(); ly.read(src)
top, = ly.top_cells(); assert top.name == 'g1_chip_top'
dbu = ly.dbu
# registration size and area from the EdgeSeal boundary 39/4
eb = pya.Region(top.begin_shapes_rec(ly.find_layer(39, 4))).merged()
assert eb.count() == 1 and eb.bbox() == pya.Box(0, 0, 1414000, 1414000), str(eb.bbox())
w, h = eb.bbox().width() * dbu, eb.bbox().height() * dbu
area_mm2 = eb.area() * dbu * dbu * 1e-6
REG = f'Device registration size: x={w:.1f} um ; y={h:.1f} um\nCalculated area: {area_mm2:.6f} sq mm'
assert REG == 'Device registration size: x=1414.0 um ; y=1414.0 um\nCalculated area: 1.999396 sq mm', REG
VER = f'PDK version: IHP-Open-PDK {PDK}'
li = ly.find_layer(63, 0)
changed = []
for s in list(top.shapes(li).each(pya.Shapes.STexts)):
    t = s.text; old = t.string
    if old.startswith('Device registration size:'): new = REG
    elif old.startswith('PDK version:'): new = VER
    else: continue
    before = (t.x, t.y, t.size, t.font, t.halign, t.valign, str(t.trans))
    t2 = t.dup(); t2.string = new; s.text = t2
    after = (s.text.x, s.text.y, s.text.size, s.text.font, s.text.halign, s.text.valign, str(s.text.trans))
    assert before == after
    changed.append(dict(old=old, new=new, x_um=t.x * dbu, y_um=t.y * dbu, size_dbu=t.size, trans=str(t.trans)))
assert len(changed) == 2, changed
for old, new in RENAME.items():
    assert ly.has_cell(old) and not ly.has_cell(new), (old, new)
    ly.cell(old).name = new
opt = pya.SaveLayoutOptions(); opt.format = 'GDS2'; opt.gds2_write_timestamps = False
ly.write(dst, opt)
print(json.dumps(dict(dst=dst, dst_sha256=hashlib.sha256(open(dst, 'rb').read()).hexdigest(), cells=ly.cells(),
                      edgeseal_boundary=str(eb.bbox()), area_mm2=area_mm2, texts=changed, renamed=RENAME), indent=1))
