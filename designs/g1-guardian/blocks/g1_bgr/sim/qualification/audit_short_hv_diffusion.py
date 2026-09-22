#!/usr/bin/env python3
"""In-memory stock nmosHV W1/L0.5 versus W1/L0.6 diffusion A/P audit."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

PDK=Path('/foss/pdks/ihp-sg13g2')
for folder in [PDK/'libs.tech/klayout/python',PDK/'libs.tech/klayout/python/pycell4klayout-api/source/python']:
    sys.path.insert(0,str(folder))
import pya
import sg13g2_pycell_lib

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert pya.__version__=='0.30.9'
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    lib=pya.Library.library_by_name('SG13_dev','sg13g2')
    layout=pya.Layout();layout.dbu=.001
    rows=[];errors=[];normalized=[]
    for length in [.5,.6]:
        params={'w':'1u','l':str(length)+'u','ng':1}
        index=lib.layout().add_pcell_variant(lib.layout().pcell_id('nmosHV'),params)
        cell=layout.cell(layout.add_lib_cell(lib,index))
        active=pya.Region(cell.begin_shapes_rec(layout.layer(1,0))).merged()
        poly=pya.Region(cell.begin_shapes_rec(layout.layer(5,0))).merged()
        gate=(active & poly).merged();diff=(active-poly).merged()
        components=sorted(list(diff.each()),key=lambda p:p.bbox().left)
        terminals=[];norm=[]
        for polygon in components:
            box=polygon.bbox();region=pya.Region(polygon)
            target=pya.Region(pya.Box(box.left,box.bottom,box.left+340,box.bottom+1000))
            exact=(region ^ target).is_empty()
            terminals.append({'bbox_um':[box.left*.001,box.bottom*.001,box.right*.001,box.top*.001],
                              'area_um2':polygon.area()*1e-6,'perimeter_um':polygon.perimeter()*.001,
                              'exact_0p34_by_1um_rectangle':exact})
            norm.append(region.transformed(pya.Trans(-box.left,-box.bottom)))
            if not exact:errors.append('diffusion shape differs from declared rectangle')
        if len(components)!=2:errors.append('expected exactly two source/drain regions')
        if abs(gate.area()*1e-6-length)>1e-12:errors.append('gate area/length binding failed')
        if abs(active.area()*1e-6-(length+.68))>1e-12:errors.append('active length extension failed')
        grid_errors=[]
        for layer in layout.layer_indexes():
            for polygon in pya.Region(cell.begin_shapes_rec(layer)).each():
                for point in polygon.each_point_hull():
                    if point.x%5 or point.y%5:grid_errors.append([point.x,point.y])
        if grid_errors:errors.append('off5nm polygon vertices')
        box=cell.bbox()
        rows.append({'parameters':params,'bbox_um':[box.left*.001,box.bottom*.001,box.right*.001,box.top*.001],
                     'active_area_um2':active.area()*1e-6,'gate_area_um2':gate.area()*1e-6,
                     'diffusion_terminals':terminals,'off5nm_polygon_vertices':grid_errors})
        normalized.append(norm)
    equivalent=len(normalized[0])==len(normalized[1])==2 and all((a^b).is_empty() for a,b in zip(*normalized))
    if not equivalent:errors.append('source/drain normalized geometry changed with length')
    pcell=PDK/'libs.tech/klayout/python/sg13g2_pycell_lib/ihp/nmosHV_code.py'
    tech=PDK/'libs.tech/klayout/python/sg13g2_pycell_lib/sg13g2_tech.json'
    result={'status':'failed' if errors else 'passed isolated native diffusion applicability',
            'pdk_commit':(PDK/'COMMIT').read_text().strip(),'KLayout':pya.__version__,
            'script_sha256':sha(Path(__file__)),'pcell_sha256':sha(pcell),'technology_sha256':sha(tech),
            'variants':rows,'normalized_source_and_drain_geometry_identical':equivalent,'errors':errors,
            'expected_explicit_junction_parameters':{'as_um2':.34,'ad_um2':.34,'ps_um':2.68,'pd_um':2.68},
            'scope':'Stock isolated ng1 W1um PCell diffusion area/full perimeter remains applicable when only L changes .5→.6um. Includes gate-side boundary as existing extracted A/P does. Drain/body positions and gate capacitance change; old wiring CPEX not new physical extraction. No GDS saved, full DRC/LVS/fit/electrical/reliability not run.'}
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
