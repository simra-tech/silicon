#!/usr/bin/env python3
"""Audit completed frozen586 draws without rewriting any run or acceptance."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from run_586_mc_screen import seed_deck
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--campaigns',nargs='+',required=True);p.add_argument('--seed-stop',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 ref=HERE/'runs/bgr_one_draw_20260922_r1';m=json.loads((ref/'manifest.json').read_text());base=m['cases'][0];original=(ref/'enabled/nominal.cir').read_text()
 records=[{'seed':44001,'numeric_status':base['status'],'tc_status':base['tc_status'],'tc_ppm_C':base['tc_ppm_C'],'run':str(ref.relative_to(ROOT))+'/enabled','scope':'Literal priorqualified enabled draw, not rerun;repeat/reverse notindependent.'}]
 fingerprints={tuple(tuple(row) for row in base['parameters_before'])};artifacts=[];wall=0
 for campaign in a.campaigns:
  run=HERE/campaign;rows=json.loads((run/'summary.json').read_text());prov=json.loads((run/'provenance.json').read_text())
  assert prov['runtime']==m['runtime'] and prov['source_sha256']==m['source_sha256']
  assert prov['qualified_reference_manifest_sha256']==sha(ref/'manifest.json')
  assert [row['seed'] for row in rows]==prov['seeds']
  for row in rows:
   leaf=run/('s%d'%row['seed']);assert (leaf/'nominal.cir').read_text()==seed_deck(original,row['seed'])
   assert sha(leaf/'nominal.cir')==row['deck_sha256']
   for name,value in prov['source_snapshot_sha256'].items():assert sha(leaf/name)==value
   record={'seed':row['seed'],'numeric_status':row['status'],'tc_status':row['tc_status'],'tc_ppm_C':row.get('tc_ppm_C'),'run':str(leaf.relative_to(ROOT)),'wall_s':row['wall_s']}
   if row['status']=='passed':
    assert row['parameters_before']==row['parameters_after'] and len(row['parameters_before'])==2842
    assert [key for key,value in row['parameters_before']]==m['parameters']
    fingerprint=tuple(tuple(pair) for pair in row['parameters_before']);assert fingerprint not in fingerprints;fingerprints.add(fingerprint)
    assert sha(leaf/'nominal.dat')==row['waveform_sha256']
    data=np.loadtxt(str(leaf/'nominal.dat'),skiprows=1);assert data.shape==(34,12) and np.isfinite(data).all() and np.array_equal(data[:,0],np.arange(-40,126,5))
    tc=float(np.ptp(data[:,1])/data[13,1]/165*1e6);assert tc==row['tc_ppm_C'] and row['tc_status']==('passed' if tc<=50 else 'failed')
   records.append(record);wall+=row['wall_s']
  for file in sorted(run.rglob('*')):
   if file.is_file():artifacts.append({'logical_path':str(file.relative_to(ROOT)),'bytes':file.stat().st_size,'sha256':sha(file)})
 assert sorted(row['seed'] for row in records)==list(range(44001,a.seed_stop))
 output={'status':'passed complete source/seed/runtime/parameter/data audit','samples':len(records),'numerical_failures':sum(r['numeric_status']!='passed' for r in records),
         'tc_failures':sum(r['tc_status']=='failed' for r in records),'maximum_tc_ppm_C':max(r['tc_ppm_C'] for r in records if r['tc_ppm_C'] is not None),
         'distinct_full_parameter_vectors':len(fingerprints),'new_core_seconds':wall,'new_retained_bytes':sum(r['bytes'] for r in artifacts),
         'runtime':m['runtime'],'nominal_source_sha256':m['source_sha256'],'reference_manifest_sha256':sha(ref/'manifest.json'),
         'records':records,'artifacts':artifacts,'scope':'Standalone nominalprocessBGR586 mismatch TC<=50ppm/C,34temps/2842fullparameters. Oldbaseline/candidatefailures unchanged. Not actualSENSE/T2Floading, supply/processqualification, physicalPEX, modelvalidity or chipyield.'}
 with a.output.open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
 print(json.dumps({key:output[key] for key in ['samples','numerical_failures','tc_failures','maximum_tc_ppm_C','distinct_full_parameter_vectors','new_core_seconds','new_retained_bytes']},indent=2))
if __name__=='__main__':main()
