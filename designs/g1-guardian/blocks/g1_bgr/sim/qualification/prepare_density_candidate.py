#!/usr/bin/env python3
"""Physical unit-array/current-density candidate; baseline untouched, no adoption."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;source=HERE.parent/'postlayout/g1_bgr_pex.spice';out=HERE/'candidates/bgr_array4_density';out.mkdir(parents=True,exist_ok=False)
text=source.read_text();base=[];added=[];changed=[];copied=[];keep={'XM41','XM46','XM53'}
for line in text.splitlines():
 p=line.split()
 if p and p[0].startswith('XR'):
  match=re.search(r'\bl=([0-9.]+)u\b',line);assert match
  old=float(match.group(1));line=line.replace(match.group(0),f'l={old/4:g}u');changed.append({'instance':p[0],'original_length_um':old,'candidate_length_um':old/4,'width_unchanged':True})
 if p and ((p[0].startswith('XM') and p[0] not in keep) or (p[0].startswith('XQ') and p[1:4]!=['vss','vss','vss'])):
  for unit in [2,3,4]:added.append(line.replace(p[0],p[0]+f'_u{unit}',1));copied.append({'original':p[0],'new':p[0]+f'_u{unit}'})
 if line.lower().startswith('.ends'):base.extend(added)
 base.append(line)
variant='\n'.join(base)+'\n';assert len(changed)==36 and len(added)==114
(out/'baseline_pex.spice').write_text(text);(out/'bgr_array4_density.spice').write_text(variant)
m={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(variant.encode()).hexdigest(),'changed_resistors':changed,'added_physical_units':copied,'unchanged_output_mirror_instances':sorted(keep),'intent':'Core current4x and activeHBT/MOScoreunitcount4x retain original perunitcurrentdensity and exportedPBIAS/PCASC. IPTAT output mirror retains originalgeometry so outputcurrent should remainnearbaseline. Reference/bias resistors quarterlength preserve intendedvoltage drops at4xcorecurrent. These are designintent, not simulatedresults.','model_effects':'Each newtransistor is a separate physical unitwith originallegalgeometry andintrinsicdiffusionparameters. Resistorwidthunchanged, lengthquartered; contact/end effects prevent exactquarterR, and PDKlocalresistor mismatch scaling changes. No arbitraryrandomdraw orcardedits.','parasitics':'OriginalwireCPEX retained plusadded intrinsicdevicecaps; newwiring/contact/fill/spatialcorrelation NOTextracted ormodeled. Existingbias-outputloading must be checked.','status':'unadopted simulation-only candidate; nominalTC/VREF/IPTAT/bias/power/model-range qualification required before selectedMC; layoutfootprint/DRC/LVS/newPEX notrun.'}
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'added_units':len(added),'shortened_resistors':len(changed),'candidate_sha256':m['candidate_sha256']}))
