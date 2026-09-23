#!/usr/bin/env python3
"""Independent raw-mask hierarchical tap derivation, before device extraction."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import pya

HERE=Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    current=bulk/'digital-reroute-streamout-20260923-r1/signal_routed_native.gds'
    binding=bulk/'io-current-native-20260923-r1/analysis.json'
    j=json.loads(binding.read_text())
    assert sha(current)=='9a52cc71122df8fcc56bbd3ec3e0842958e1f7eec0f73c64ed21a8e2c7ea1805'
    assert j['status']=='passed current140 IO master/placement binding; raw differences reported'
    assert j['inputs'][str(current)]==sha(current)
    pdk=Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    rules=pdk/'libs.tech/klayout/tech/lvs/rule_decks'
    definitions=rules/'layers_definitions.lvs'
    source=HERE/'audit_dimensions_r2.py'
    assert sha(source)=='835beb602aa89fd75e0316b473047586336b58f6b6b594cd30bc84758c6d8965'
    scope={'__file__':str(source),'__name__':'analytical_arithmetic'}
    text=source.read_text();exec(compile(text[:text.index('\noriginal = Path')],str(source),'exec'),scope)
    measure=scope['polygon_record']
    inputs={str(p):sha(p) for p in (current,binding,source,Path(__file__).resolve(),definitions,
        rules/'general_derivations.lvs',rules/'tap_derivations.lvs',rules/'tap_extraction.lvs')}
    layers={m[1]:(int(m[2]),int(m[3])) for m in re.finditer(r'(?m)^(\w+)\s*=\s*get_polygons\((\d+),\s*(\d+)\)',definitions.read_text())}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running independent raw deep geometry',inputs=inputs)
    try:
        ly=pya.Layout();ly.read(str(current));top=ly.top_cell();assert ly.dbu==.001
        expected={(r['native_cell'],r['transform']) for r in j['matched']};assert len(expected)==140
        found=set()
        for inst in list(top.each_inst()):
            key=(inst.cell.name,str(inst.trans))
            if key in expected:
                assert key not in found;found.add(key)
            else:
                inst.delete()
        assert found==expected
        # This scoped view removes no native IO shape. Non-IO top-level geometry
        # is irrelevant only if none is a direct input to the tap derivation.
        required=['activ_drw','activ_filler','psd_drw','nwell_drw','pwell_block','digisub_drw',
            'substrate_drw','nsd_block','gatpoly_drw','gatpoly_filler','nsd_drw','trans_drw',
            'emwind_drw','emwihv_drw','salblock_drw','polyres_drw','extblock_drw','res_drw',
            'activ_mask','recog_diode','ind_drw','ind_pin']
        assert all(top.shapes(ly.layer(*layers[n])).is_empty() for n in required)
        assert top.shapes(ly.layer(63,0)).is_empty()
        dss=pya.DeepShapeStore();dss.threads=1
        regs={n:pya.Region(top.begin_shapes_rec(ly.layer(*layers[n])),dss) for n in required}
        # The chip extent encloses all actual IO cells. No physical shape added.
        extent_layer=ly.layer(300,0);top.shapes(extent_layer).insert(top.bbox())
        extent=pya.Region(top.begin_shapes_rec(extent_layer),dss)
        active=regs['activ_drw']+regs['activ_filler'];nw=regs['nwell_drw'];psd=regs['psd_drw']
        gap=regs['digisub_drw']-regs['digisub_drw'].sized(-1)
        pwell=extent-regs['pwell_block']-nw-gap
        labels={k:pya.Region(top.begin_shapes_rec(ly.layer(63,0)),dss,pattern,True,1)
            for k,pattern in [('ptap1','[sS][uU][bB]!'),('ntap1','[wW][eE][lL][lL]')]}
        markers={'ptap1':(regs['substrate_drw']&pwell).interacting(labels['ptap1']),
                 'ntap1':nw.interacting(labels['ntap1'])}
        excluded=regs['gatpoly_drw']+regs['gatpoly_filler']
        for n in ('nsd_drw','trans_drw','emwind_drw','emwihv_drw','salblock_drw','polyres_drw',
                  'extblock_drw','res_drw','activ_mask','recog_diode','ind_drw','ind_pin'):
            excluded+=regs[n]
        derived={'ptap1':((active&psd)&markers['ptap1'])-nw-excluded,
            'ntap1':((active-psd-regs['nsd_block'])&markers['ntap1'])-pwell-psd-excluded}
        out=pya.Layout();out.dbu=ly.dbu;ot=out.create_cell(top.name)
        outputs={}
        for n,(kind,reg) in enumerate(derived.items()):
            assert reg.is_deep()
            layer=out.layer(301+n,0);reg.insert_into(out,ot.cell_index(),layer)
            projected=pya.Region(ot.begin_shapes_rec(layer))
            assert (projected^reg).is_empty()
            outputs[kind]=dict(flat_area_dbu2=reg.area(),flat_perimeter_dbu=reg.perimeter(),
                direct_cells=[dict(cell=c.name,polygons=[measure(p) for p in pya.Region(c.shapes(layer)).each()])
                    for c in out.each_cell() if not c.shapes(layer).is_empty()],
                exported_raw_XOR='passed',device_extraction='not run')
        out.write(str(a.output/'derived_tap_masks.gds'))
        assert all(sha(Path(p))==h for p,h in inputs.items())
        result.update(status='passed scoped140-IO raw hierarchical Boolean derivation; source ownership pending',
            outputs=outputs,geometry_sha256=sha(a.output/'derived_tap_masks.gds'),
            original_native_cells_unchanged='passed; only in-memory top instance selection',
            fullchip_nonIO_context='not run; scoped IO subset',source_AP_changes='not run',
            device_extraction='not run',strict_LVS='not run',electrical_R='not run')
    except Exception as exc:
        result.update(status='failed raw deep geometry control',error=repr(exc));raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
