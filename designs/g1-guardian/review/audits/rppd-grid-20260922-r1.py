#!/usr/bin/env python3
"""Verify pinned5nm rule and nearest proposed resistor length using in-memory PCells."""
import argparse,hashlib,json,os,re,sys
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
for folder in ('/foss/pdks/ihp-sg13g2/libs.tech/klayout/python','/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python'):sys.path.insert(0,folder)
import pya,sg13g2_pycell_lib
from sg13g2_pycell_lib.ihp.utility_functions import SG13_GRID
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
root=Path('/foss/pdks/ihp-sg13g2');deck=root/'libs.tech/klayout/tech/drc/rule_decks/geometry/3_1_offgrid.drc';tech=root/'libs.tech/klayout/python/sg13g2_pycell_lib/sg13g2_tech.json';code=tech.parent/'ihp/rppd_code.py';utility=code.parent/'utility_functions.py'
assert re.search(r'GRID\s*=\s*5\.nm',deck.read_text())
def declared_grids(value):
    if not isinstance(value,dict):return []
    return ([value['grid']] if 'grid' in value else [])+[grid for child in value.values() for grid in declared_grids(child)]
assert declared_grids(json.loads(tech.read_text()))==[.005]
proposed=Decimal('53.4641998819');grid=Decimal('.005');nearest=(proposed/grid).quantize(Decimal('1'),rounding=ROUND_HALF_UP)*grid
assert nearest==Decimal('53.465')
lib=pya.Library.library_by_name('SG13_dev','sg13g2');ly=pya.Layout();ly.dbu=.001
rows=[]
for length in ('52.5',str(nearest)):
    params={'w':'1u','l':length+'u','b':0};variant=lib.layout().add_pcell_variant(lib.layout().pcell_id('rppd'),params);cell=ly.cell(ly.add_lib_cell(lib,variant));bad=[];count=0
    for index in ly.layer_indexes():
        info=ly.get_info(index)
        for polygon in pya.Region(cell.begin_shapes_rec(index)).each():
            points=list(polygon.each_point_hull())
            for hole in range(polygon.holes()):points.extend(polygon.each_point_hole(hole))
            count+=len(points)
            for point in points:
                if point.x%5 or point.y%5:bad.append({'layer':[info.layer,info.datatype],'point_nm':[point.x,point.y]})
    box=cell.bbox();rows.append({'length_um':float(length),'parameters':params,'bbox_um':[box.left*.001,box.bottom*.001,box.right*.001,box.top*.001],'polygon_vertices':count,'off_5nm_vertices':bad,'all_polygon_vertices_on_5nm_grid':not bad})
result={'status':'passed grid-only check' if all(r['all_polygon_vertices_on_5nm_grid'] for r in rows) else 'failed grid-only check',
    'PDK_commit':(root/'COMMIT').read_text().strip(),'KLayout':pya.__version__,'file_hashes':{str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (deck,tech,code,utility)},
    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'stock_drawing_grid_um':float(grid),'PCell_utility_grid_um':SG13_GRID,'GDS_database_grid_um':ly.dbu,
    'proposed_unrounded_length_um':str(proposed),'nearest_5nm_length_um':str(nearest),'rounding_delta_um':str(nearest-proposed),'relative_rounding_delta_ppm':float((nearest/proposed-1)*1000000),
    'in_memory_PCell_checks':rows,'scope':'No GDS saved or design/source changed. Drawinggrid verified independently of1nmdatabaseunit andcoarserPCellutilitygrid. Allpolygonvertices tested; text omitted. This is not stockfullDRC, LVS, fit, matching, nominalTC/current or sourceadoption approval.'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('file_hashes','in_memory_PCell_checks')},indent=2))
