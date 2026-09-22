#!/usr/bin/env python3
"""Generate eight isolated source-bound MOS contact recipes; not DRC/LVS credit."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import pya

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PDK = Path('/foss/pdks/ihp-sg13g2')
for path in [PDK/'libs.tech/klayout/python', PDK/'libs.tech/klayout/python/pycell4klayout-api/source/python']:
    sys.path.insert(0, str(path))
import sg13g2_pycell_lib  # noqa: E402,F401

SOURCE = ROOT/'designs/g1-guardian/blocks/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
SOURCE_SHA = '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
GEN_SHA = 'dee7f8fa5ab94165946e342625ed72c00e6a174592bb47a0af9f9054b8ce171e'
HELPERS = 'um box ring label square pcell cont_row cont_col _cuts via1 via2 via_array m2_v m3_h guard_ring_p ntap_strip mos gate_tab sd_pad sd_strip_x'.split()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def number(s):
    return float(s[:-1])*{'u': 1e-6, 'p': 1e-12}[s[-1]] if s[-1] in 'up' else float(s)


def main():
    assert pya.__version__ == '0.30.9' and (PDK/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    generator = HERE.parent/'g1_bgr_layout.py'
    assert sha(generator) == GEN_SHA and sha(SOURCE) == SOURCE_SHA
    control = ROOT/'build/scratch/bgr-original-generator-20260922-r1/comparison.json'
    assert json.loads(control.read_text())['status'].startswith('passed')
    parsed = ast.parse(generator.read_text())
    selected = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in HELPERS]
    assert {node.name for node in selected} == set(HELPERS)
    helper_code = compile(ast.Module(body=selected, type_ignores=[]), str(generator), 'exec')
    grouped = {}
    for line in SOURCE.read_text().splitlines():
        if not line.startswith('XM'):
            continue
        f = line.split()
        params = dict(part.split('=', 1) for part in f[6:])
        assert 'ng' not in params and f[5] in ['sg13_hv_nmos', 'sg13_hv_pmos']
        key = (f[5], params['w'], params['l'])
        grouped.setdefault(key, []).append((line, f, params))
    assert len(grouped) == 8 and sum(map(len, grouped.values())) == 336
    out = ROOT/'build/scratch/bgr-mos-contact-prototypes-20260922-r2'
    out.mkdir(parents=True, exist_ok=False)
    (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    result = dict(status='generated prototypes; stock checks not run', source_sha256=SOURCE_SHA,
                  helper_source_sha256=GEN_SHA, helper_names=HELPERS,
                  original_reproduction_sha256=sha(control), klayout=pya.__version__,
                  pdk_commit=(PDK/'COMMIT').read_text().strip(), prototypes=[],
                  full_1036_placement='not run', stock_DRC_LVS='not run',
                  current_via_margin='not run', full_macro_guards_feeds='not run')
    lib = pya.Library.library_by_name('SG13_dev', 'sg13g2')
    layers = {'Activ': (1,0), 'GatPoly': (5,0), 'Cont': (6,0), 'pSD': (14,0), 'NWell': (31,0), 'TGO': (44,0),
              'M1': (8,0), 'M1pin': (8,2), 'M1txt': (8,25), 'Via1': (19,0),
              'M2': (10,0), 'M2pin': (10,2), 'M2txt': (10,25), 'Via2': (29,0),
              'M3': (30,0), 'M3pin': (30,2), 'M3txt': (30,25), 'prBoundary': (189,4)}
    for index, ((model, wstr, lstr), examples) in enumerate(grouped.items()):
        line, f, params = examples[0]
        w, length = number(wstr)*1e6, number(lstr)*1e6
        name = 'bgr_mos_proto_%02d' % index
        ly = pya.Layout(); ly.dbu = .001
        top = ly.create_cell(name)
        env = dict(pya=pya, lib=lib, ly=ly, top=top, L={key: ly.layer(*value) for key,value in layers.items()},
                   CONT=.16, CP=.34, VIA=.19, VP=.42, W3=.3, M2_SEGS=[])
        exec(helper_code, env)
        box, label, square = env['box'], env['label'], env['square']
        d = env['mos']('p' if model.endswith('pmos') else 'n', w, length, 10, 10)
        native_bbox = top.bbox()
        native = {key: pya.Region(top.begin_shapes_rec(env['L'][key])).dup() for key in ['Activ','GatPoly','M1','NWell']}
        # Recursive-iterator Regions can retain live shape references even when
        # area() was cached. Materialize BEFORE adding any contacts or wells.
        for snapshot in native.values():
            snapshot.flatten()
        channel = native['Activ'] & native['GatPoly']
        junctions = list((native['Activ']-native['GatPoly']).each_merged())
        assert channel.count() == 1 and len(junctions) == 2
        assert abs(channel.area()*1e-6-w*length) < 1e-9
        assert all(abs(poly.area()*1e-6-number(params[key])*1e12) < 1e-9 for poly,key in zip(junctions,['as','ad']))
        assert all(abs(poly.perimeter()*.001-number(params[key])*1e6) < 1e-9 for poly,key in zip(junctions,['ps','pd']))
        x, y = d['x'], d['y']
        drain, gate, source, bulk = f[1:5]
        gx, gy = env['gate_tab'](d)
        label('M1txt', gx, gy, gate)
        box('M1pin', gx-.15, gy-.25, gx+.15, gy+.25)
        dx, dy = env['sd_pad'](d, 'R', y+w/2)
        label('M1txt', dx, dy, drain)
        box('M1pin', dx-.2, dy-.2, dx+.2, dy+.2)
        if model.endswith('pmos'):
            assert source == bulk
            # Same source-tied cascode recipe, with length-dependent right edge.
            box('NWell', x-.62, y-.62, x+length+1.3, y+w+2.4)
            box('TGO', x-.62, y-1.5, x+length+1.3, y+w+2.4)
            env['ntap_strip'](x+.3, y+w+1.2, x+length+.4, y+w+1.6, source)
            box('M1', x+.07, y+w-.1, x+.23, y+w+1.6)
            box('M1', x+.07, y+w+1.2, x+.3, y+w+1.6)
            box('M1pin', x+.3, y+w+1.2, x+length+.4, y+w+1.6)
        else:
            box('TGO', x-.5, y-1.5, x+d['lf']+.5, y+w+.6)
            ring = env['guard_ring_p'](x-1.8, y-1.8, x+d['lf']+1.8, y+w+1.0, net=bulk)
            if source == bulk:
                sx = env['sd_strip_x'](d, 'L')
                box('M1', sx-.15, y+.3, sx+.15, ring[3]+.13)
            else:
                sx, sy = env['sd_pad'](d, 'L', y+w/2)
                label('M1txt', sx, sy, source)
                box('M1pin', sx-.2, sy-.2, sx+.2, sy+.2)
            box('M1pin', ring[0]-.13, y, ring[0]+.13, y+.3)
        added_activ = pya.Region(top.begin_shapes_rec(env['L']['Activ']))-native['Activ']
        assert added_activ.area() > 0, 'Each prototype must add a separately audited body tie'
        assert added_activ.interacting(native['Activ']).is_empty(), 'Body ties must not grow source/drain diffusion'
        final_bbox = top.bbox()
        reservation = native_bbox.enlarged(2000)
        contained = (pya.Region(final_bbox)-pya.Region(reservation)).is_empty()
        top.shapes(env['L']['prBoundary']).insert(reservation)
        path = out/(name+'.gds'); ly.write(str(path))
        ports = list(dict.fromkeys(f[1:5]))
        cdl = '.subckt '+name+' '+' '.join(ports)+'\nMUNIT '+' '.join(f[1:])+'\n.ends '+name+'\n'
        (out/(name+'.cdl')).write_text(cdl)
        result['prototypes'].append(dict(name=name, source_instance=f[0], source_line=line,
            represented_instances=[fields[0] for _,fields,_ in examples], native_gate_count=1,
            W_um=w, L_um=length, source_drain_area_perimeter_exact=True,
            native_bbox_um=[v*.001 for v in [native_bbox.left,native_bbox.bottom,native_bbox.right,native_bbox.top]],
            contact_well_guard_bbox_um=[v*.001 for v in [final_bbox.left,final_bbox.bottom,final_bbox.right,final_bbox.top]],
            inside_native_plus2um_reservation=contained, added_body_Activ_um2=added_activ.area()*1e-6,
            source_body_equal=source==bulk, gds_sha256=sha(path), cdl_sha256=sha(out/(name+'.cdl')),
            electrical_pin_connectivity='not run; stock LVS required', stock_rules='not run'))
    result['all_contact_bbox_reservations_passed'] = all(r['inside_native_plus2um_reservation'] for r in result['prototypes'])
    result['original_sources_unchanged'] = sha(generator)==GEN_SHA and sha(SOURCE)==SOURCE_SHA
    (out/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
