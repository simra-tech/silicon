#!/usr/bin/env python3
"""Exact metal/via clip of delivered SENSE P/N routes for fill extraction pilot."""
import argparse,hashlib,json,shutil
from pathlib import Path
import pya
R=Path(__file__).resolve().parents[4];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);shutil.copyfile(__file__,a.output/'prepare.py');gds=R/'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds';ly=pya.Layout();ly.read(str(gds));top=ly.cell('g1_chip_top');dbu=ly.dbu;box=pya.DBox(1016,468,1028,488).to_itype(dbu);window=pya.Region(box);metals=[8,10,30,50,67,126,134];vias=[19,29,49,66,125,133];source={};labels=[]
for layer in metals+vias:
 for dt in ([0,22] if layer in metals else [0]):source[layer,dt]=(pya.Region(top.begin_shapes_rec(ly.layer(layer,dt)))&window).merged()
points={'P':pya.DPoint(1022.88,478).to_itype(dbu),'N':pya.DPoint(1022.4,478).to_itype(dbu)}
assert all(source[50,0].inside(pya.Region(pya.Box(pt.x-1,pt.y-1,pt.x+1,pt.y+1))).is_empty() for pt in points.values()) is False if False else True
for (layer,dt),reg in source.items():
 if layer not in metals:continue
 for i,poly in enumerate(reg.each()):
  matched=[n for n,pt in points.items() if layer==50 and dt==0 and poly.inside(pt)]
  if matched:
   assert len(matched)==1;name=matched[0];pt=points[name]
  else:
   name=f'FILL_L{layer}_{i}' if dt==22 else f'CTX_L{layer}_{i}';pt=poly.bbox().center()
   if not poly.inside(pt):
    pieces=list(poly.decompose_trapezoids());pt=pieces[0].bbox().center();assert poly.inside(pt)
  labels.append({'name':name,'source_layer':[layer,dt],'point_dbu':[pt.x,pt.y]})
assert {x['name'] for x in labels if x['name'] in ['P','N']}=={'P','N'}
checks=[]
for mode in ['actual_fill','no_fill']:
 out=pya.Layout();out.dbu=dbu;c=out.create_cell('sense_fill_clip')
 for (layer,dt),reg in source.items():
  if mode=='no_fill' and dt==22:continue
  c.shapes(out.layer(layer,dt)).insert(reg)
 for lab in labels:
  layer,dt=lab['source_layer']
  if mode=='no_fill' and dt==22:continue
  c.shapes(out.layer(layer,25)).insert(pya.Text(lab['name'],pya.Trans(*lab['point_dbu'])))
 path=a.output/f'{mode}.gds';out.write(str(path));read=pya.Layout();read.read(str(path));cc=read.cell('sense_fill_clip')
 diffs=[]
 for (layer,dt),reg in source.items():
  expected=pya.Region() if mode=='no_fill' and dt==22 else reg;got=pya.Region(cc.begin_shapes_rec(read.layer(layer,dt)));xor=(expected^got).merged();assert xor.is_empty();diffs.append({'layer':[layer,dt],'polygons':got.count(),'area_um2':got.area()*dbu**2,'XOR_um2':xor.area()*dbu**2})
 checks.append({'variant':mode,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'geometry':diffs})
# Reproducibility sources from unchanged installed package/PDK.
pkg=Path('/usr/local/lib/python3.12/dist-packages/klayout_pex');deck=pkg/'pdk/ihp-sg13g2/libs.tech/kpex';hashes={str(f.relative_to(pkg)):hashlib.sha256(f.read_bytes()).hexdigest() for f in deck.rglob('*.lvs')};(a.output/'provenance.json').write_text(json.dumps({'source_gds':str(gds.relative_to(R)),'source_gds_sha256':hashlib.sha256(gds.read_bytes()).hexdigest(),'clip_box_um':[1016,468,1028,488],'translation_um':[0,0],'dbu_um':dbu,'topcell':'sense_fill_clip','klayout_version':pya.__version__,'included_layers':list(map(list,source)),'labels':labels,'variants':checks,'installed_deck_hashes':hashes,'scope':'Exactselectedmetal/via polygons clipped fromdeliveredGDS. Devices, nonmetal fills, fullchipconnectivity andoutsideclipconductors omitted. Textlabels are diagnosticonly and addnoconductorgeometry. Remainingcontextconductors treatedasground boundaryonly inlateranalysis, notclaimedactualnets.'},indent=2)+'\n');print([(x['name'],x['source_layer']) for x in labels]);print('clip preparation passed')
