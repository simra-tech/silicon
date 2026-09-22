#!/usr/bin/env python3
"""Bounded eight-device source-faithful assembly; no adoption or PEX credit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

from build_native_prototypes import lib, pya, snapshot, measure_native, probe_record, pin, sha
from build_source_faithful_buffer import full_nets

HERE = Path(__file__).resolve().parent
NAMES = ('XM1', 'XM2', 'XM3', 'XM4', 'XM14', 'XM11', 'XM15', 'XM12')
ADDITIONS = [('XM3', 'nmosHV', 320, 40, 27.25, 21.5),
             ('XM4', 'nmosHV', 320, 40, 27.25, 89.),
             ('XM14', 'pmosHV', 384, 48, 9.73, 35.),
             ('XM11', 'pmosHV', 384, 48, 9.73, 75.5),
             ('XM15', 'pmosHV', 384, 48, 9.73, 48.5),
             ('XM12', 'pmosHV', 384, 48, 9.73, 62.)]
EXTRA_TRUNKS = dict(vbn=6.8, mir=8., vbpc=9.2, pc1=10.4, pc2=11.6, out1=12.8)


def derive(output):
    path = HERE / 'build_stacked_pair.py'
    assert sha(path) == 'edc0919bdbf991f5191764936bbf741f25d2a4fb0613333659714830395fd289'
    text = path.read_text()
    changes = [
        ("if name in ('XM1','XM2'):continue", 'if name in '+repr(NAMES)+':continue'),
        ('assert len(rows)==19', 'assert len(rows)==13'),
        ('passed same-layer zero-overlap with19 other native cells',
         'passed same-layer zero-overlap with13 excluded native cells'),
        ("        ring=D.tap_ring(m.x0-1.45,m.y0-3.05,m.x1+1.45,m.y0+9.05,ptype=True)\n"
         "        y=m.y0+3;D.stack(ring[2],y,'M1','M2');exit_m2('vss',ring[2],y);probe_record(probes,'body','substrate_tap','vss',501,ring[2],y)\n", ''),
        ('    for net,x in TRUNKS.items():\n',
         "    ring=D.tap_ring(1.,4.5,229.,114.5,ptype=True)\n"
         "    for sy in (18.5,32.5,86.,99.5):\n"
         "        D.tap_strip(.7,229.3,sy,ptype=True,inset=.6)\n"
         "        probe_record(probes,'body','substrate_tap','vss',501,100.,sy)\n"
         "    D.stack(ring[2],12.,'M1','M2');exit_m2('vss',ring[2],12.)\n"
         "    probe_record(probes,'body','substrate_tap','vss',501,ring[2],12.)\n"
         '    for net,x in TRUNKS.items():\n')]
    for old, new in changes:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    (output / 'derived_pair_generator.py').write_text(text)
    namespace = dict(__file__=str(path), __name__='core8_pair_derivative')
    exec(compile(text, str(path), 'exec'), namespace)
    return namespace, hashlib.sha256(text.encode()).hexdigest()


def source_lines(source):
    block = re.search(r'(?ms)^\.subckt g1_ota_main_candidate .*?^\.ends', source.read_text()).group(0)
    lines = {line.split()[0]: line for line in block.splitlines() if line.startswith('X')}
    assert len(lines) == 21
    return lines


def assemble(ly, output, source, pack):
    pair, derived_sha = derive(output)
    cell, original = pair['build'](ly, source, pack)
    cell.name = 'g1_main_core8'
    D = lib.Draw(ly, cell)
    probes = original['terminal_audit']['probes']
    trunks = dict(pair['TRUNKS'], **EXTRA_TRUNKS)
    points = {net: [] for net in trunks}
    for q in probes:
        if q['device'] == 'pin':
            points[q['net']].append(q['point_um'])
    specs = source_lines(source)
    native = [(name, lib.Mos(D, kind, w, 4, nf, x, y))
              for name, kind, w, nf, x, y in ADDITIONS]
    before = {layer: snapshot(cell, layer) for layer in (1, 5)}
    assert (before[1] & before[5]).count() == 400
    rows = []

    def exit_m2(net, x, y):
        tx = trunks[net]
        D.hwire('M2', x, tx, y, .4)
        D.stack(tx, y, 'M2', 'M3')
        points[net].append((tx, y))

    for name, m in native:
        words = specs[name].split()
        params = dict(re.findall(r'(\w+)=([^\s]+)', specs[name]))
        assert float(params['w'].rstrip('u')) == m.w and params['l'] == '4u'
        assert int(params['ng']) == m.nf and params['m'] == '1'
        assert words[5] == ('sg13_hv_pmos' if m.is_p else 'sg13_hv_nmos')
        assert words[4] == ('vdd' if m.is_p else 'vss')
        assert not set(params) & {'as', 'ad', 'ps', 'pd', 'rfmode'}
        strips, measured = measure_native(m, before)
        m.end_dummies()
        m.gate_bar('bot')
        exit_m2(words[2], m.gx(0), m.yd('bot', .33))
        for parity, side, terminal, net in ((1, 'bot', 'drain', words[1]),
                                            (0, 'top', 'source', words[3])):
            m.rail(side, m.strips(parity))
            x, y = m.sx(parity), m.yd(side, 1.03)
            D.stack(x, y, 'M1', 'M2')
            exit_m2(net, x, y)
        for k in range(m.nf):
            probe_record(probes, name, 'gate', words[2], 5, m.gx(k), m.y0 + m.wf / 2)
        for k, polygon in enumerate(strips):
            probe_record(probes, name, 'drain' if k % 2 else 'source',
                         words[1] if k % 2 else words[3], 501, m.sx(k), m.y0 + m.wf / 2)
        rows.append(dict(device=name, source_line=specs[name], native=measured,
                         diffusion_strips=len(strips), Activ_origin_um=[m.x0, m.y0]))
    D.box('NWell', 9.11, 34.38, 220.89, 84.12)
    for y in (45.75, 59.25, 72.75):
        D.tap_strip(9.73, 220.27, y, ptype=False)
        D.stack(100., y, 'M1', 'M2')
        exit_m2('vdd', 100., y)
        probe_record(probes, 'body', 'well_tap', 'vdd', 501, 100., y)
    for net, x in trunks.items():
        ys = [p[1] for p in points[net]]
        assert ys, net
        D.vwire('M3', x, min(ys), max(ys), .4)
        if net in EXTRA_TRUNKS:
            pin(D, probes, net, 'M3', x, min(ys))
    gds = output / 'g1_main_core8.gds'
    ly.write(str(gds))
    saved = pya.Layout()
    saved.read(str(gds))
    top = saved.cell('g1_main_core8')
    after = {layer: snapshot(top, layer) for layer in (1, 5)}
    channel_delta = (before[1] & before[5]) ^ (after[1] & after[5])
    result = dict(derived_pair_sha256=derived_sha, pair_preassembly=original,
                  added_native_devices=rows, source_lines={name: specs[name] for name in NAMES},
                  GDS_sha256=sha(gds), native_channel_XOR_um2=channel_delta.area()*1e-6,
                  native_Activ_removed_um2=(before[1]-after[1]).area()*1e-6,
                  channels=(after[1] & after[5]).count(), diffusion_strips=130+sum(r['diffusion_strips'] for r in rows))
    (output / 'preaudit.json').write_text(json.dumps(result, indent=2)+'\n')
    assert channel_delta.is_empty() and (before[1]-after[1]).is_empty()
    assert result['channels'] == 400 and result['diffusion_strips'] == 408
    graph = full_nets(top, probes)
    result['terminal_audit'] = graph
    (output / 'terminal_audit.json').write_text(json.dumps(graph, indent=2)+'\n')
    assert graph['status'] == 'passed', dict(opens=graph['opens'], shorts=graph['shorts'])
    assert len({q['net'] for q in graph['probes']}) == 13
    result['obstacles'] = pair['native_obstructions'](saved, top, pack, source)
    bbox = top.bbox()
    assert bbox.left >= 0 and bbox.bottom >= 0 and bbox.right <= 230000 and bbox.top <= 164000
    result['bbox_um'] = [v*.001 for v in (bbox.left, bbox.bottom, bbox.right, bbox.top)]
    vertices = 0
    for li in saved.layer_indexes():
        it = top.begin_shapes_rec(li)
        while not it.at_end():
            shape = it.shape()
            if shape.is_text():
                p = it.trans()*shape.text.trans.disp
                assert p.x % 5 == 0 and p.y % 5 == 0
            else:
                polygon = shape.polygon.transformed(it.trans())
                for p in polygon.each_point_hull():
                    assert p.x % 5 == 0 and p.y % 5 == 0
                    vertices += 1
                for hole in range(polygon.holes()):
                    for p in polygon.each_point_hole(hole):
                        assert p.x % 5 == 0 and p.y % 5 == 0
                        vertices += 1
            it.next()
    result.update(status='passed bounded saved core8 preparation', grid_vertices=vertices,
                  stock_DRC_LVS='not run', full_main_and_SENSE='not run', PEX='not run',
                  shared_junction_intrinsic_applicability='not run', matching_current_IR='not run',
                  density_antenna='not run', adoption='not run', seed='not applicable')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and pya.__version__ == '0.30.9'
    assert os.sched_getaffinity(0) == {7}
    assert sha(args.pack) == 'd70eeefb4a31de454c785a2f92a2320fc2d457ecf8a5b50f8a27abfb5adb2f56'
    source = HERE.parents[1] / 'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source) == 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    args.output.mkdir(parents=True)
    for name in ('build_core8.py', 'CORE8_ASSEMBLY_CONTRACT_20260922.md'):
        (args.output/name).write_bytes((HERE/name).read_bytes())
    result = dict(source_sha256=sha(source), pack_sha256=sha(args.pack),
                  builder_sha256=sha(Path(__file__)), KLayout=pya.__version__)
    try:
        ly = pya.Layout()
        ly.dbu = .001
        result.update(assemble(ly, args.output, source, json.loads(args.pack.read_text())))
    except Exception as exc:
        result.update(status='failed core8 preparation', exception_type=type(exc).__name__,
                      detail=str(exc), stock_checks='not run', adoption='not run')
        (args.output/'failure.json').write_text(json.dumps(result, indent=2)+'\n')
        raise
    (args.output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in
                     ('pair_preassembly', 'terminal_audit', 'obstacles', 'source_lines', 'added_native_devices')}, indent=2))


if __name__ == '__main__':
    main()
