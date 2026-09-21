#!/usr/bin/env python3
"""Export actual GDS geometry using KLayout; run via flow/run.sh python3.
Display-only filtering does not modify GDS, decks or extraction models.
"""
import hashlib,json,pathlib,xml.etree.ElementTree as ET
import pya
ROOT=pathlib.Path('/work')
OUT=ROOT/'designs/g1-guardian/review/layouts'
PDK=pathlib.Path('/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp')
BLOCK=ROOT/'designs/g1-guardian/blocks'
physical={1,5,6,8,10,19,29,30,36,49,50,66,67,125,126,129,133,134,128,3,13,33,35,55,90,91,101,139,156,152}
root=ET.parse(PDK)
legend=[]
for node in root.getroot():
 source=node.findtext('source','')
 try:layer,datatype=map(int,source.split('@')[0].split('/'))
 except ValueError:continue
 visible=layer in physical and datatype==0
 v=node.find('visible')
 if v is not None:v.text='true' if visible else 'false'
 if visible:legend.append({'layer':source,'name':node.findtext('name'),'color':node.findtext('fill-color')})
style=OUT/'review_display.lyp';root.write(style,encoding='utf-8',xml_declaration=True)
items=[('chip','g1_padring/flow/runs/assembly-1350/final/gds/g1_chip_top.gds','g1_chip_top',None),
('chip_core','g1_padring/flow/runs/assembly-1350/final/gds/g1_chip_top.gds','g1_chip_top',(355,355,995,995)),
('digital','g1_ctrl/layout/g1_digital.gds','g1_digital',None),
('bgr','g1_bgr/layout/g1_bgr.gds','g1_bgr',None),
('t2f','g1_t2f/layout/g1_t2f.gds','g1_t2f',None),
('osc','g1_osc/layout/g1_osc.gds','g1_osc',None),
('sense','g1_sense/layout/g1_sense_filled.gds','g1_sense',None),
('trip','g1_trip/layout/g1_trip.gds','g1_trip',None),
('gate','g1_gate/layout/g1_gate_filled.gds','g1_gate',None),
('dose','g1_dose/layout/g1_dose_macro.gds','g1_dose_macro',None),
('dut','g1_dut/layout/g1_dut_macro.gds','g1_dut_macro',None),
('level_shifter','g1_ctrl/ls/layout/g1_ls_up.gds','g1_ls_up',None)]
records=[]
for name,rel,cellname,box in items:
 path=BLOCK/rel
 if not path.exists():raise FileNotFoundError(path)
 view=pya.LayoutView()
 view.set_config('background-color','#101820');view.set_config('grid-visible','false');view.set_config('text-visible','false')
 view.set_config('cell-box-visible','false');view.set_config('cell-label-visible','false')
 idx=view.load_layout(str(path),False)
 cv=view.cellview(idx);cv.cell=cv.layout().cell(cellname)
 view.max_hier_levels=100
 view.load_layer_props(str(style),idx,False)
 bounds=cv.cell.dbbox()
 frame=pya.DBox(*box) if box else bounds
 dx,dy=frame.width()*.02,frame.height()*.02
 frame=pya.DBox(frame.left-dx,frame.bottom-dy,frame.right+dx,frame.top+dy)
 w,h=(2200,2200) if name.startswith('chip') else (2000,max(700,round(2000*frame.height()/frame.width())))
 if h>2200:w=round(w*2200/h);h=2200
 view.save_image_with_options(str(OUT/f'{name}.png'),w,h,0,2,0,frame,False)
 record={'name':name,'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cell':cellname,'bbox_um':[bounds.left,bounds.bottom,bounds.right,bounds.top],'crop_um':box,'pixel_size':[w,h],'orientation':'+x right, +y up; original GDS orientation, no rotation or reflection'}
 records.append(record);print(json.dumps(record),flush=True)
 view.destroy()
(OUT/'layout_manifest.json').write_text(json.dumps({'pdk_layer_properties_sha256':hashlib.sha256(PDK.read_bytes()).hexdigest(),'klayout_python_version':pya.__version__,'rendering':'PDK colors/patterns, dark background; selected physical drawing layers only; text, fill datatype22, no-fill, wells, implants and recognition/outline layers hidden; hierarchy expanded; 2x supersampling; source geometry unchanged','legend':legend,'layouts':records},indent=2)+'\n')
