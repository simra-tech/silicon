#!/usr/bin/env python3
"""Independent stock IO active/implant geometry versus stock tap CDL parameters."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import pya

p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('--cells',nargs='+',default=['sg13g2_SecondaryProtection','sg13g2_Clamp_N20N0D','sg13g2_Clamp_P20N0D','sg13g2_DCNDiode','sg13g2_DCPDiode']);a=p.parse_args()
if a.report.exists():raise FileExistsError('Preserve prior evidence')
pdk=Path('/foss/pdks/ihp-sg13g2');gds=pdk/'libs.ref/sg13g2_io/gds/sg13g2_io.gds';cdl=pdk/'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'
layout=pya.Layout();layout.read(str(gds));source=cdl.read_text();rows=[]
scale={'p':1e-12,'f':1e-15,'u':1e-6,'n':1e-9}
def value(token):return float(token[:-1])*scale[token[-1]]
for name in a.cells:
    cell=layout.cell(name)
    def region(number):return pya.Region(cell.begin_shapes_rec(layout.layer(number,0))).merged()
    # Active P+ outside nwell and excluding gates/resistors. These simple IO
    # cells have no HBT/inductor/ESD-recognition bodies in this candidate region.
    tap=(region(1)&region(14))-region(31)-region(5)-region(28)-region(111)-region(128)
    area=tap.area()*layout.dbu**2;perimeter=sum(poly.perimeter() for poly in tap.each())*layout.dbu
    body=re.search(r'\.SUBCKT '+name+r'\b(.*?)\.ENDS',source,re.S).group(1)
    line=next(ln for ln in body.splitlines() if 'ptap1' in ln)
    area_cdl=value(re.search(r'\bA=(\S+)',line)[1])*1e12
    perimeter_cdl=value(re.search(r'\bP=(\S+)',line)[1])*1e6
    rows.append({'cell':name,'stock_cdl':line,'cdl_area_um2':area_cdl,'cdl_perimeter_um':perimeter_cdl,
                 'equivalent_square_perimeter_um':4*math.sqrt(area_cdl),
                 'geometry_area_um2':area,'geometry_perimeter_um':perimeter,'geometry_polygons':tap.count(),
                 'geometry_polygon_details':[{'bbox_um':[poly.bbox().left*layout.dbu,poly.bbox().bottom*layout.dbu,poly.bbox().right*layout.dbu,poly.bbox().top*layout.dbu],'area_um2':poly.area()*layout.dbu**2,'perimeter_um':poly.perimeter()*layout.dbu,'is_box':poly.is_box()} for poly in tap.each()],
                 'geometry_minus_cdl_area_pct':100*(area/area_cdl-1),
                 'geometry_to_cdl_perimeter_ratio':perimeter/perimeter_cdl})
result={'scope':'Independent raw geometry arithmetic, not extracted-netlist reference generation and not LVS closure',
        'formula':'(Activ/0 AND pSD/0) minus NWell/0,GatPoly/0,SalBlock/0,EXTBlock/0,PolyRes/0',
        'gds_sha256':hashlib.sha256(gds.read_bytes()).hexdigest(),'cdl_sha256':hashlib.sha256(cdl.read_bytes()).hexdigest(),
        'pdk_commit':(pdk/'COMMIT').read_text().strip(),'klayout_version':pya.__version__,'rows':rows}
a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
