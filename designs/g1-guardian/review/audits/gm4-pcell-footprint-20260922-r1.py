#!/usr/bin/env python3
"""Read exact gm4 source and instantiate unchanged PCells only in memory; save no GDS."""
import argparse,hashlib,json,os,re,sys
from pathlib import Path
for folder in ('/foss/pdks/ihp-sg13g2/libs.tech/klayout/python','/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python'):sys.path.insert(0,folder)
import pya,sg13g2_pycell_lib
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
digest=hashlib.sha256(a.source.read_bytes()).hexdigest();assert digest=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
text=a.source.read_text();candidate=re.search(r'(?ms)^\.subckt g1_ota_main_candidate .*?^\.ends',text).group(0)
baseline=re.search(r'(?ms)^\.subckt g1_ota .*?^\.ends',text).group(0)
lib=pya.Library.library_by_name('SG13_dev','sg13g2');probe=pya.Layout();probe.dbu=.001;rows=[]
for view,block in (('baseline',baseline),('candidate',candidate)):
    for line in block.splitlines():
        if not line.startswith('X'):continue
        words=line.split();models={'sg13_hv_pmos':'pmosHV','sg13_hv_nmos':'nmosHV','rppd':'rppd','cap_cmim':'cmim'}
        matches=[word for word in words if word in models];assert len(matches)==1
        kind=models[matches[0]];params=dict(re.findall(r'\b(w|l|ng)=([^\s]+)',line));params['ng']=int(params['ng']) if 'ng' in params else 1
        if kind in ('cmim','rppd'):params.pop('ng')
        if kind=='cmim':params['Calculate']='C'
        index=lib.layout().add_pcell_variant(lib.layout().pcell_id(kind),params);cell=probe.cell(probe.add_lib_cell(lib,index));box=cell.bbox()
        rows.append({'view':view,'device':words[0],'kind':kind,'source_line':line,'parameters':params,'width_um':box.width()*.001,'height_um':box.height()*.001,'bbox_area_um2':box.area()*1e-6})
totals={view:{'MOS_bbox_sum_um2':sum(row['bbox_area_um2'] for row in rows if row['view']==view and row['kind'] in ('pmosHV','nmosHV')),
    'all_device_bbox_sum_um2':sum(row['bbox_area_um2'] for row in rows if row['view']==view)} for view in ('baseline','candidate')}
old=json.loads(Path(__file__).with_name('sense-candidate-area-20260922-r2').joinpath('summary.json').read_text());ota=old['g1_ota_bbox_local_um'];ota_area=(ota[2]-ota[0])*(ota[3]-ota[1]);overhead=ota_area/totals['baseline']['MOS_bbox_sum_um2']
result={'status':'passed in-memory footprint inventory; layout fit not run','source_sha256':digest,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'KLayout':pya.__version__,
    'devices':rows,'totals':totals,'baseline_OTA_bbox_area_um2':ota_area,'baseline_OTA_over_MOS_bbox_factor':overhead,
    'candidate_main_OTA_by_baseline_overhead_um2':totals['candidate']['MOS_bbox_sum_um2']*overhead,
    'whole_SENSE_estimate_replace_only_main_OTA_um2':252.16*189.25-ota_area+totals['candidate']['MOS_bbox_sum_um2']*overhead,
    'scope':'Exact gm4comp3 source, main OTA only changed; two buffer/ref OTAs unchanged. Native isolatedPCell bbox accounting, not placement. Folded rows, dummies, wells, externalcontacts, guards, routes and matching remain undesigned; MIM can overlap underlying MOS so raw all-device sum is not strict lower bound. No GDS saved or source changed.'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='devices'},indent=2))
