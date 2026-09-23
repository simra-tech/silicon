#!/usr/bin/env python3
"""Read-only source/native ownership audit of residual IO count deficits."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import pya


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bulk', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0)) == {1}
    assert pya.__version__ == '0.30.9'
    a.output.mkdir(parents=True)
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    gds = a.bulk/'final-native-sealring-20260923-r1/sealed_native.gds'
    stock = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds')
    source = a.bulk/'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl'
    ledger = a.bulk/'fullchip-api-discrepancy-ledger-20260923-r2/summary.json'
    assert sha(gds) == '3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9'
    assert sha(stock) == '4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    assert sha(source) == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
    layout, library = pya.Layout(), pya.Layout()
    layout.read(str(gds)); library.read(str(stock))
    assert layout.dbu == library.dbu == .001
    result = dict(status='running', inputs={str(p):sha(p) for p in (gds,stock,source,ledger)},
                  new_extraction='not run', circuit_or_geometry_changes='not applicable', cells=[])
    text = source.read_text()
    layers = sorted({(i.layer,i.datatype) for ly in (layout,library) for i in ly.layer_infos()})
    for name in ('sg13g2_RCClampResistor','sg13g2_SecondaryProtection','sg13g2_LevelDown','sg13g2_DCNDiode'):
        ca, cb = layout.cell(name), library.cell(name)
        assert ca is not None and cb is not None
        changes, geometry = [], {}
        for layer in layers:
            ra = pya.Region(ca.begin_shapes_rec(layout.layer(*layer))).merged()
            rb = pya.Region(cb.begin_shapes_rec(library.layer(*layer))).merged()
            if not (ra ^ rb).is_empty():
                changes.append(list(layer))
            if layer in ((5,0),(14,0),(30,0),(128,0),(38,0),(1,0),(7,0),(8,0),(6,0),(46,0)):
                geometry[str(layer)] = dict(count=ra.count(),area_um2=ra.area()*1e-6,
                    polygons=[dict(bbox=str(p.bbox()),hull=[[q.x,q.y] for q in p.each_point_hull()],
                                   area_um2=p.area()*1e-6) for p in ra.each()])
        assert not changes, name
        body = re.search(r'(?im)^\.SUBCKT '+re.escape(name)+r'\b.*?^\.ENDS\b[^\n]*',text,re.S).group(0)
        result['cells'].append(dict(name=name,native_stock_all_layer_XOR=changes,geometry=geometry,source_body=body))
    view = json.loads(ledger.read_text())['views']['physical_original']
    bad = [r['pair'] for r in view['bad_devices']]
    selected = {}
    for model in ('rppd','sg13_hv_pmos','dantenna'):
        selected[model] = {side:[r[side] for r in bad if r[side] and r[side]['model'].lower()==model]
                           for side in ('layout','reference')}
    result['saved_mismatch_records'] = selected
    r = selected['rppd']
    counts = {s:Counter((round(d['parameters']['w'],9),round(d['parameters']['l'],9)) for d in ds) for s,ds in r.items()}
    delta = counts['reference']-counts['layout']
    assert delta == Counter({(1.,2.):14,(1.,520.):2})
    result['RPPD_unpaired_dimension_counts'] = {s:[dict(w=k[0],l=k[1],count=v) for k,v in sorted(c.items())] for s,c in counts.items()}
    missing = [r['reference'] for r in bad if r['reference'] and not r['layout'] and r['reference']['model']=='sg13_hv_pmos']
    assert len(missing)==1 and missing[0]['parameters']['W']==13.950000000000001
    assert set(missing[0]['terminals'].values())=={'VDD'}
    result['HVP_unpaired_all_grounded_source_combination'] = missing
    result['DANT_bad_multiplicity_totals'] = {s:sum(d['parameters']['m'] for d in ds) for s,ds in selected['dantenna'].items()}
    assert result['DANT_bad_multiplicity_totals']['layout']==result['DANT_bad_multiplicity_totals']['reference']
    result.update(status='passed read-only count/ownership observations; strict LVS remains failed',
                  script_sha256=sha(Path(__file__)),
                  caveats=['Equal diode multiplicity is not electrical topology or A/P equivalence.',
                           'Saved comparer pair selection is not independent physical instance matching.',
                           'Native/reference source records and all rule/model files remain unchanged.'])
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])


if __name__ == '__main__':
    main()
