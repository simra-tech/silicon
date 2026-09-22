#!/usr/bin/env python3
"""Instantiate isolated unchanged PCells for a SENSE candidate footprint screen."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
for d in ['/foss/pdks/ihp-sg13g2/libs.tech/klayout/python','/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python']:sys.path.insert(0,d)
import pya,sg13g2_pycell_lib
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False)
gds=ROOT/'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds';geom=ROOT/'designs/g1-guardian/blocks/g1_sense/sim/qualification/mc-gm3-matching16-comp2p5-smoke-20260922-a/geometry_comparison.json';net=geom.parent/'sense_substrate_tied.spice';ly=pya.Layout();ly.read(str(gds));dbu=ly.dbu
box=lambda b:[b.left*dbu,b.bottom*dbu,b.right*dbu,b.top*dbu]
placements=[{'cell':i.cell.name,'bbox_um':box(i.bbox()),'transform':str(i.dcplx_trans)} for i in ly.cell('g1_sense').each_inst() if i.cell.name.startswith('g1_ota')]
lib=pya.Library.library_by_name('SG13_dev','sg13g2');probe=pya.Layout();probe.dbu=.001;top=probe.create_cell('isolated_candidate_PCell_inventory');rows=[]
for q in json.loads(geom.read_text())['devices']:
 name=q['device'];kind='cmim' if name=='XCC' else ('nmosHV' if name in ['XM3','XM4'] else 'pmosHV');r={'device':name,'kind':kind}
 for view in ['baseline','candidate']:
  v=q[view];params={'w':f'{v["w_um"]}u','l':f'{v["l_um"]}u'}
  if kind=='cmim':params['Calculate']='C'
  else:params['ng']=v['fingers']
  pc=lib.layout().add_pcell_variant(lib.layout().pcell_id(kind),params);c=probe.cell(probe.add_lib_cell(lib,pc));b=c.bbox();r[view]={'bbox_um':[b.left*.001,b.bottom*.001,b.right*.001,b.top*.001],'width_um':b.width()*.001,'height_um':b.height()*.001,'bbox_area_um2':b.area()*1e-6,'parameters':params}
  top.insert(pya.CellInstArray(c.cell_index(),pya.Trans(int(len(rows)*1000000),0 if view=='baseline' else 100000)))
 rows.append(r)
probe.write(str(a.output/'isolated_footprint_inventory.gds'))
# Literal single-row widths use same pitch, gaps and side-channel margin as baseline generator.
def width(spec):return sum(n*(l+.38)+.3 for w,l,n in spec)+1.4*(len(spec)-1)
baseN=[(1.6,1,1),(8,1,1),(8,1,1),(80,1,10),(48,1,6),(48,1,6),(80,1,10),(96,1,12)]
candN=[(1.6,1,1),(8,1,1),(8,1,1),(320,4,40),(48,1,6),(48,1,6),(320,4,40),(96,1,12)]
rowwidths={'N_baseline':width(baseN),'N_candidate':width(candN),'PA_baseline':width([(96,1,12)]*4),'PA_candidate':width([(384,4,48)]*4),'input_pair_baseline':32*2.38+.3,'input_pair_candidate':96*2.38+.3}
all_mos=[]
for i in ly.cell('g1_ota').each_inst():
 if i.cell.name.startswith(('nmosHV','pmosHV')):
  b=i.cell.bbox();all_mos.append({'cell':i.cell.name,'bbox_area_um2':b.area()*dbu**2,'width_um':b.width()*dbu,'height_um':b.height()*dbu})
summary={'scope':'Footprint diagnostic only; isolatedPCellGDS is not a circuit/layout candidate and has intentionally separated inventory cells, no interconnect or signoff.','input_hashes':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [gds,geom,net]},'klayout_version':pya.__version__,'main_and_buffer_placements_local':placements,'g1_sense_bbox_local_um':box(ly.cell('g1_sense').bbox()),'g1_ota_bbox_local_um':box(ly.cell('g1_ota').bbox()),'baseline_all_MOS_PCells':all_mos,'baseline_all_MOS_PCell_bbox_sum_um2':sum(r['bbox_area_um2'] for r in all_mos),'changed_devices':rows,'changed_MOS_bbox_sum_baseline_um2':sum(r['baseline']['bbox_area_um2'] for r in rows if r['kind']!='cmim'),'changed_MOS_bbox_sum_candidate_um2':sum(r['candidate']['bbox_area_um2'] for r in rows if r['kind']!='cmim'),'row_widths_um':rowwidths,'local_envelope_um':[727,408,1029,648],'local_envelope_um2':302*240,'limitations':['Candidate needs folding of wide rows and redistributed contacts/dummies/wells/guards/routing. Nativebbox accounting is not a placement or DRC proof.','MIM can overlap transistor rows; do not add capacitorrectangle to MOSfloorplanarea as an absolute packing lowerbound.','Localenvelope bounded bydigitalright727,TRIPbottom648,rightIOinner1029,digitalbottom408; not all empty and existing macro+PDN+routes consume it.','Buffer/refOTA and resistorarray unchanged electrically but could require relocation if mainOTA grows.']}
(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='changed_devices'},indent=2))
