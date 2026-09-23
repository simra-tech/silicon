#!/usr/bin/env python3
"""Bind saved antenna markers, native pad observations, source and API control."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def items(path):
    result = []
    for item in ET.parse(path).findall('.//items/item'):
        values = [v.text for v in item.findall('./values/value')]
        polygon, = [v for v in values if v.startswith('polygon:')]
        coords = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', polygon)]
        box = [min(coords[::2]), min(coords[1::2]), max(coords[::2]), max(coords[1::2])]
        props = {}
        for v in values:
            match = re.fullmatch(r'\[#([^]]+)\] float: (.*)', v)
            if match: props[match[1]] = float(match[2])
        result.append(dict(category=item.findtext('category').strip("'"), bbox_um=box, properties=props))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--bulk', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists(); a.output.mkdir(parents=True)
    root = Path(__file__).resolve().parents[5]
    pdk = Path('/foss/pdks/ihp-sg13g2')
    paths = dict(PNL=root/'designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top.pnl.v',
        roundtrip=a.bulk/'fullchip-def-odb-20260922-r5/roundtrip.tsv',
        library=pdk/'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl',
        native_GDS=pdk/'libs.ref/sg13g2_io/gds/sg13g2_io.gds',
        stock_report=a.bulk/'native-sealed-antenna-20260923-r1/antenna.lyrdb',
        stock_summary=a.bulk/'native-sealed-antenna-20260923-r1/summary.json',
        native_probe=a.bulk/'antenna-native-supply-audit-20260923-r2/summary.json',
        api_control=a.bulk/'antenna-evaluate-control-20260923-r1/control.lyrdb',
        antenna_deck=pdk/'libs.tech/klayout/tech/drc/rule_decks/antenna.drc')
    expected = dict(PNL='3ee42e820cbec6d7b0f04eb55c847eaa613daddb93423593197a51fa21df5d9a',
        roundtrip='43be000677b631983ae7f159d988cc6d1654679caa436e6ab3da62b1df2452fd',
        library='7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4',
        native_GDS='4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825',
        stock_report='e6395e21d52fa14ad4c471b6b8f797b35912b271a204b30df2aca88d852aaec8',
        antenna_deck='e3e925d918d2d4e2067751326122fd1a9be9bc3cb4fa10a8aca2fc9349975362')
    hashes = {key: sha(path) for key, path in paths.items()}
    assert all(hashes[key] == value for key, value in expected.items())
    native = json.loads(paths['native_probe'].read_text())
    assert native['status'].startswith('passed') and len(native['stages']) == 7
    assert all(o['same_net'] for stage in native['stages'] for row in stage['observations'] for o in row['vdd_annotation_probes'])
    source = paths['library'].read_text()
    body = re.search(r'^\.SUBCKT sg13g2_LevelDown .*?^\.ENDS', source, re.M|re.S)[0]
    record = 'MP0 vdd vdd vdd vdd sg13_hv_pmos m=1 w=4.65u l=450.00n ng=1'
    assert record in body
    match = [r for r in body.splitlines() if r.startswith('M') and 'w=4.65u l=450.00n' in r]
    assert match == [record]
    pad = re.search(r'^\.SUBCKT sg13g2_IOPadIn .*?^\.ENDS', source, re.M|re.S)[0]
    assert 'XI0 p2c pad iovdd iovss vdd vss / sg13g2_LevelDown' in pad
    observations = items(paths['stock_report'])
    assert len(observations) == 9
    boxes = dict(pad12_en=[1106.73,956.54,1111.38,956.99],
                 pad14_sclk=[508.54,1106.73,508.99,1111.38],
                 pad15_sdi=[620.54,1106.73,620.99,1111.38])
    netmap = {'pad12_en': ('en_i','EN'), 'pad14_sclk': ('i_core.sclk_i','SCLK'), 'pad15_sdi': ('i_core.sdi_i','SDI')}
    pnl = paths['PNL'].read_text(); odb = paths['roundtrip'].read_text().splitlines()
    for name, box in boxes.items():
        found = [row for row in observations if row['bbox_um'] == box]
        assert sorted(row['category'] for row in found) == ['Ant.e_Metal5','Ant.e_TopMetal1','Ant.e_TopMetal2']
        assert all(row['properties']['has_diode'] == 1 for row in found)
        block = re.search(r'\bsg13g2_IOPadIn\s+'+name+r'\s*\((.*?)\);', pnl, re.S)[1]
        assert re.search(r'\.vdd\(VDD\)', block) and re.search(r'\.vss\(VSS\)', block)
        assert re.search(r'\.iovdd\(IOVDD\)', block) and re.search(r'\.iovss\(IOVSS\)', block)
        assert 'CONN\tVDD\t'+name+'\tvdd' in odb
        for row in found: row.update(instance=name, source_hierarchy=name+'.XI0.MP0', gate_net='VDD', input_signal_not_gate=netmap[name][1])
    control = items(paths['api_control'])
    before = sorted(row['properties']['ratio'] for row in control if row['category']=='BEFORE')
    after = [row['properties']['ratio'] for row in control if row['category']=='AFTER']
    assert len(before)==len(after)==2 and abs(before[0]-8/3)<1e-10 and before[1]==4 and after==[3,3]
    props = observations[0]['properties']
    residual = 20000-props['sum_m1_m4']
    result = dict(status='passed bounded source/native/marker/API binding; antenna remains failed',
        input_hashes=hashes, PDK_commit=(pdk/'COMMIT').read_text().strip(),
        marked_source_record=record, source_cell_excerpt=body, IO_cell_excerpt=pad,
        markers=observations, API_timing_control=dict(before=before,after=after,conclusion='Immediate stage-specific evaluation; later joins do not retroactively change earlier ratios'),
        threshold_diagnostic=dict(M4_prefix=props['sum_m1_m4'], M5_ratio=props['m5_ratio'], M5_headroom=residual,
            minimum_gate_area_multiplier_if_only_M5_join_and_no_new_metal=props['m5_ratio']/residual,
            warning='Necessary illustrative bound only. Actual joined metal area and subsequent stages must also pass.'),
        checks=dict(source_native_gate_binding='passed', native_VDD_connectivity='passed', API_stage_control='passed',
            original_stock_antenna='failed: nine markers', fullchip_flat_ratio_reproduction='failed: timeout',
            ring_only_ratio_reproduction='failed: timeout', current_join_remedy_stock_check='not run',
            shared_geometry_changes='not run', electrical_survival_claim='not run', stochastic_seed='not applicable'))
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_cell_excerpt','IO_cell_excerpt','markers')},indent=2))


if __name__ == '__main__': main()
