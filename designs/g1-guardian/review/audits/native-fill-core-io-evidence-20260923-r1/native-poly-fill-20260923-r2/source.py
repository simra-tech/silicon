#!/usr/bin/env python3
"""Add design-specific stock-sized poly dummy rectangles; never modify decks."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, sha
from streamout_native_signal_routes import text_records


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    source = a.candidate/'filled_native.gds'
    meta = json.loads((a.candidate/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source) == meta['GDS_sha256']
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    rule = pdk/'libs.tech/klayout/tech/drc/rule_decks/sg13g2_tech_default.json'
    rules = json.loads(rule.read_text())
    # Find the actual table without assuming its enclosing key.
    tables = [rules] + [v for v in rules.values() if isinstance(v, dict)]
    table, = [v for v in tables if 'GFil_size_x' in v]
    assert {k: table[k] for k in ('GFil_size_x','GFil_size_y','GFil_c','GFil_d','GFil_e')} == {
        'GFil_size_x':5.0,'GFil_size_y':1.4,'GFil_c':.8,'GFil_d':1.1,'GFil_e':1.1}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    faulthandler.dump_traceback_later(60, repeat=True)
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    assert ly.dbu == .001
    before = {str(i):region(ly,top,i) for i in ly.layer_infos()}
    texts = text_records(ly,top)
    instances = collections.Counter((i.cell.name,str(i.trans)) for i in top.each_inst())
    get = lambda layer,datatype=0: region(ly,top,pya.LayerInfo(layer,datatype))
    interior = get(39).holes()
    assert not interior.is_empty()
    # Stronger-than-minimum exclusions: entire NWell/nBuLay and existing active
    # filler are excluded, not just well edges. Respect both no-fill classes.
    obstacles = pya.Region()
    for layer,datatype in ((1,0),(5,0),(6,0),(14,0),(7,21),(28,0),(31,0),
                           (32,0),(26,0),(1,22)):
        obstacles += get(layer,datatype).sized(1100)
    obstacles += get(5,23) + get(1,23)
    old = get(5,22)
    blocked = (obstacles + old.sized(800)).merged()
    added = pya.Region(); phases=[]
    progress = dict(status='running geometric filtering',source_GDS_sha256=sha(source),
        script_sha256=sha(Path(__file__)),rule_table_sha256=sha(rule),phases=phases)
    (a.output/'analysis.json').write_text(json.dumps(progress,indent=2)+'\n')
    # Each phase has >=0.8um self spacing. Subsequent phases must clear all
    # earlier rectangles too. No functional metal or original filler removed.
    bbox = interior.bbox()
    for dx,dy in ((0,0),(2500,0),(5000,0),(7500,0),(0,1250),(2500,1250),(5000,1250),(7500,1250)):
        tiles = collections.defaultdict(pya.Region)
        for row,y in enumerate(range(bbox.bottom+dy,bbox.top-1400,2500)):
            for x in range(bbox.left+dx+(row%2)*5000,bbox.right-5000,10000):
                tiles[x//100000,y//100000].insert(pya.Box(x,y,x+5000,y+1400))
        legal = pya.Region()
        for key,trial in sorted(tiles.items()):
            # Crop only the obstacle query, with a positive margin around every
            # complete trial rectangle. No candidate is clipped at a tile edge.
            window=pya.Region(trial.bbox().enlarged(5))
            local_blocked=blocked & window
            local_inside=interior & window
            accepted=trial.inside(local_inside).not_interacting(local_blocked)
            if key==sorted(tiles)[0]:
                assert (accepted ^ trial.inside(interior).not_interacting(blocked)).is_empty()
            legal += accepted
        added += legal
        blocked = (blocked + legal.sized(800)).merged()
        phases.append(dict(offset_dbu=[dx,dy],rectangles=legal.count(),added_area_um2=legal.area()*1e-6))
        (a.output/'analysis.json').write_text(json.dumps(progress,indent=2)+'\n')
        if added.area()*1e-6 >= 25000: break
    assert (added & old).is_empty() and (added-interior).is_empty()
    result = dict(status='failed insufficient conservative additional fill', source_GDS_sha256=sha(source),
        script_sha256=sha(Path(__file__)), rule_table_sha256=sha(rule), phases=phases,
        additional_area_um2=added.area()*1e-6, rectangles=added.count(),
        not_run=['stock main/maximal/density/antenna','fill-sensitive PEX and electrical acceptance','adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    assert not added.is_empty(), 'No legal stock-sized rectangles in conservative exclusions'
    top.shapes(ly.layer(5,22)).insert(added)
    output=a.output/'filled_native.gds'; ly.write(str(output))
    overlay=pya.Layout(); overlay.dbu=.001; ot=overlay.create_cell('additional_poly_fill_NOT_ADOPTED')
    ot.shapes(overlay.layer(5,22)).insert(added); overlay.write(str(a.output/'poly_fill_overlay.gds'))
    saved=pya.Layout(); saved.read(str(output)); st=saved.top_cell()
    assert text_records(saved,st)==texts
    assert collections.Counter((i.cell.name,str(i.trans)) for i in st.each_inst())==instances
    for info in saved.layer_infos():
        expected=before.get(str(info),pya.Region())
        if (info.layer,info.datatype)==(5,22): expected += added
        assert (region(saved,st,info)^expected).is_empty(),str(info)
    assert sha(source)==result['source_GDS_sha256'] and sha(rule)==result['rule_table_sha256']
    result.update(status='passed additive stock-sized poly fill geometry only', GDS_sha256=sha(output),
        overlay_sha256=sha(a.output/'poly_fill_overlay.gds'), functional_geometry_texts_instances_held='passed',
        stock_rules_unchanged='passed', conservative_exclusion='passed')
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':main()
