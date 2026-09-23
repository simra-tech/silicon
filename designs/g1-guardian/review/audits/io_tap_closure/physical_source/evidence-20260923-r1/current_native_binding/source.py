#!/usr/bin/env python3
"""Bind actual current native IO masters/placements to pinned raw geometry."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import pya


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def region(layout,cell,pair):
    return pya.Region(cell.begin_shapes_rec(layout.layer(*pair))).merged()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    gds = bulk/'digital-reroute-streamout-20260923-r1/signal_routed_native.gds'
    tsv = bulk/'fullchip-def-odb-20260922-r5/roundtrip.tsv'
    library = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds')
    assert sha(gds) == '9a52cc71122df8fcc56bbd3ec3e0842958e1f7eec0f73c64ed21a8e2c7ea1805'
    assert sha(tsv) == '43be000677b631983ae7f159d988cc6d1654679caa436e6ab3da62b1df2452fd'
    assert sha(library) == '4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    inputs = {str(p):sha(p) for p in (gds,tsv,library,Path(__file__).resolve())}
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running current IO correspondence',inputs=inputs,matched=[],masters=[])
    try:
        ly = pya.Layout(); ly.read(str(gds)); top = ly.top_cell()
        ref = pya.Layout(); ref.read(str(library))
        orientation = dict(R0=pya.Trans.R0,R90=pya.Trans.R90,R180=pya.Trans.R180,R270=pya.Trans.R270,
            MX=pya.Trans.M0,MY=pya.Trans.M90,MXR90=pya.Trans.M45,MYR90=pya.Trans.M135)
        expected = []
        for line in tsv.read_text().splitlines():
            f = line.split('\t')
            if f[0] != 'INST' or not f[2].startswith('sg13g2_') or ref.cell(f[2]) is None:
                continue
            x1,y1,x2,y2 = map(int,f[4:8]); w,h=x2-x1,y2-y1
            if f[3] in ('R90','R270','MXR90','MYR90'):
                w,h=h,w
            linear=pya.Trans(orientation[f[3]]); rotated=linear*pya.Box(0,0,w,h)
            tr=pya.Trans(x1-rotated.left,y1-rotated.bottom)*linear
            expected.append((f[1],f[2],tr))
        assert len(expected) == 140
        actual=list(top.each_inst()); selected={}
        for name,master,tr in expected:
            found=[inst for inst in actual if inst.trans == tr and inst.cell.name.endswith(master)]
            assert len(found) == 1,(name,master,str(tr),[(i.cell.name,str(i.trans)) for i in actual if i.trans == tr])
            inst,=found; selected[(master,inst.cell.cell_index())]=inst.cell
            result['matched'].append(dict(instance=name,master=master,native_cell=inst.cell.name,transform=str(tr)))
        pairs = [(n,0) for n in (1,5,6,7,14,28,31,40,60,99,111,128,156,240)]+[(1,22),(5,22),(7,21),(46,21),(1,20),(99,31)]
        bundle=pya.Layout();bundle.dbu=.001
        for (master,index),cell in sorted(selected.items()):
            original=ref.cell(master); rows=[]
            for pair in pairs:
                old=region(ref,original,pair); new=region(ly,cell,pair); delta=old^new
                rows.append(dict(layer=list(pair),original_area_dbu2=old.area(),actual_area_dbu2=new.area(),
                    XOR_area_dbu2=delta.area(),XOR_polygons=[str(p.bbox()) for p in delta.each()]))
            result['masters'].append(dict(master=master,native_cell=cell.name,raw_layers=rows))
            copied=bundle.create_cell(master);copied.copy_tree(cell)
            for pair in pairs:
                assert (region(bundle,copied,pair)^region(ly,cell,pair)).is_empty()
        bundle.write(str(a.output/'current_io_masters.gds'))
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        changed=[dict(master=r['master'],layer=q['layer'],area=q['XOR_area_dbu2']) for r in result['masters'] for q in r['raw_layers'] if q['XOR_area_dbu2']]
        result.update(status='passed current140 IO master/placement binding; raw differences reported',
            raw_differences=changed,bundle_sha256=sha(a.output/'current_io_masters.gds'),
            current_raw_equals_pinned='passed' if not changed else 'failed; differences require classification',
            bundle_geometry_XOR='passed all audited raw layers',new_source_parameters='not run',strict_LVS='not run')
    except Exception as exc:
        result.update(status='failed current native binding',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
