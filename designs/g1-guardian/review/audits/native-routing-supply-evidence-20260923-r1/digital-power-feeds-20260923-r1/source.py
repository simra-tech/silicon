#!/usr/bin/env python3
"""Source-held digital TM1 rail extensions with redundant native TV2 geometry."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records, sha, DESIGN
from audit_placed_decap_domains import identity
from flat_metal_connectivity import flat_physical
from build_native_decap_pdn import METALS, CUTS, point

BASE = '88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb'
PIN = {'VDD': [388760, 376000], 'VSS': [394960, 376000]}
ROOT = {'VDD': [395000, 354660], 'VSS': [507000, 334660]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pdn', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    faulthandler.dump_traceback_later(60, repeat=True)
    source = a.pdn/'decap_pdn_core.gds'; meta = json.loads((a.pdn/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source) == meta['GDS_sha256'] == BASE
    lef = DESIGN/'blocks/g1_ctrl/layout/g1_digital.lef'
    assert sha(lef) == '7519083e4154ae9d8487cc8a0268f1e8b013a2a95521d71fb9213b0db5878f82'
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', source_GDS_sha256=sha(source), script_sha256=sha(Path(__file__)),
        LEF_sha256=sha(lef), flat_helper_sha256=sha(Path(__file__).with_name('flat_metal_connectivity.py')),
        exploratory_target_mA=8, target_scope='Prospective branch sizing only; actual digital current envelope not established',
        not_run=['stock DRC', 'all-cut removal sensitivity', 'routed fullnative integration', 'IR/EM and actual-current qualification', 'adoption'])
    receipt = a.output/'analysis.json'
    try:
        ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
        assert ly.dbu == .001
        digital, = [i for i in top.each_inst() if i.cell.name == 'retained_g1_digital']
        assert str(digital.trans) == 'r0 367000,364000'
        # These exact published LEF rail rectangles bind the selected endpoints;
        # actual native metal must cover the whole windows, not only a label.
        windows = {'VDD': pya.Box(387660,375120,389860,715760),
                   'VSS': pya.Box(393860,374710,396060,716170)}
        numbers = METALS+tuple(c[0] for c in CUTS)
        old = {n: region(ly, top, pya.LayerInfo(n, 0)) for n in numbers}
        for name, box in windows.items():
            assert (pya.Region(box)-old[126]).is_empty(), name
            assert box.contains(pya.Point(*PIN[name]))
        network, layers, flat_held = flat_physical(ly, top)
        old_pins = {n: identity(network, layers[126], xy) for n, xy in PIN.items()}
        old_roots = {n: identity(network, layers[134], xy) for n, xy in ROOT.items()}
        assert None not in list(old_pins.values())+list(old_roots.values())
        assert len(set(old_pins.values()) | set(old_roots.values())) == 4
        allowed = {n: {old_pins[n], old_roots[n]} for n in PIN}
        routes = {n: {l: pya.Region() for l in numbers} for n in PIN}
        arrays = []
        for name in PIN:
            x, y = PIN[name]; target_y = ROOT[name][1]
            routes[name][126].insert(pya.Box(x-1100, target_y-1100, x+1100, y+1100))
            cuts = []
            for delta in (-1960, 0, 1960):
                box = [x-450, target_y+delta-450, x+450, target_y+delta+450]
                cuts.append(box); routes[name][133].insert(pya.Box(*box))
            for layer in (126, 134):
                routes[name][layer].insert(pya.Box(x-1100, target_y-3060, x+1100, target_y+3060))
            arrays.append(dict(net=name, layer=133, center_dbu=[x,target_y], cuts=cuts,
                table_mA_per_cut=10, half_table_sum_mA=15, one_cut_removed_half_sum_mA=10,
                current_scope='Equal-sharing arithmetic only; not native-wire or hot-lifetime qualification'))
        errors = []; counts = collections.Counter()
        def inspect(name, layer, polygons, why):
            for poly in polygons.each():
                xy = point(poly); found = identity(network, layers[layer], xy); counts[why] += 1
                if found not in allowed[name]: errors.append(dict(net=name,layer=layer,point=xy,actual=found,reason=why))
        for name, added in routes.items():
            other = 'VSS' if name == 'VDD' else 'VDD'
            for layer in METALS:
                inspect(name, layer, old[layer].interacting(added[layer]), 'new metal touches native metal')
                if not added[layer].interacting(routes[other][layer]).is_empty():
                    errors.append(dict(net=name,layer=layer,reason='opposite new metals touch'))
            for cut, lo, hi in CUTS:
                for layer, opposite in ((lo,hi),(hi,lo)):
                    inspect(name, opposite, old[opposite].interacting(old[cut].interacting(added[layer])), 'new metal touches native cut')
                    inspect(name, layer, old[layer].interacting(added[cut]), 'new cut touches native metal')
                    assert (added[cut]-(old[layer]+added[layer])).is_empty()
                    if not added[cut].interacting(routes[other][layer]).is_empty():
                        errors.append(dict(net=name,layer=layer,reason='new cut touches opposite new metal'))
        (a.output/'contact_gate.json').write_text(json.dumps(dict(status='failed' if errors else 'passed',
            errors=errors,counts=dict(counts),old_pins=old_pins,old_roots=old_roots,arrays=arrays),indent=2)+'\n')
        assert not errors, errors[:10]
        before = {str(i):region(ly,top,i) for i in ly.layer_infos()}
        texts = text_records(ly,top); instances = sorted((i.cell.name,str(i.trans)) for i in top.each_inst())
        overlay = pya.Layout(); overlay.dbu=.001; ot=overlay.create_cell('digital_core_feeds_NOT_ADOPTED')
        for added in routes.values():
            for layer, polys in added.items():
                top.shapes(ly.layer(layer,0)).insert(polys)
                ot.shapes(overlay.layer(layer,0)).insert(polys)
        output=a.output/'candidate_core.gds'; ly.write(str(output)); overlay.write(str(a.output/'power_overlay.gds'))
        saved=pya.Layout(); saved.read(str(output)); st=saved.top_cell()
        assert text_records(saved,st)==texts
        assert sorted((i.cell.name,str(i.trans)) for i in st.each_inst())==instances
        for info in saved.layer_infos():
            expected=before.get(str(info),pya.Region())
            if info.datatype==0 and info.layer in numbers:
                for added in routes.values(): expected += added[info.layer]
            assert (region(saved,st,info)^expected).is_empty(),str(info)
        newnet,newlayers,flat_saved=flat_physical(saved,st)
        probes={}
        for name in PIN:
            probes[name+'_native']=identity(newnet,newlayers[126],PIN[name])
            probes[name+'_root']=identity(newnet,newlayers[134],ROOT[name])
            assert probes[name+'_native']==probes[name+'_root'] and probes[name+'_native'] is not None
        assert probes['VDD_root']!=probes['VSS_root']
        result.update(status='passed source-bound additive digital rail feeds', GDS_sha256=sha(output),
            overlay_sha256=sha(a.output/'power_overlay.gds'), arrays=arrays, probes=probes,
            source_geometry_texts_instances_saved_roundtrip='passed', no_foreign_contact='passed',
            flat_actual_native_to_root_connectivity='passed', native_instances_retained=len(instances),
            TM1_bridge_width_um=2.2, TM1_half_table_mA=16.5)
    except Exception as exc:
        result.update(status='failed digital feed geometry or connectivity',error=repr(exc)); raise
    finally:
        receipt.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2),flush=True)
        faulthandler.cancel_dump_traceback_later()


if __name__=='__main__': main()
