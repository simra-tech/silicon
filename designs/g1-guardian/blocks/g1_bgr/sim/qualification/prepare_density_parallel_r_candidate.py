#!/usr/bin/env python3
"""Four physical copies of core units and full-length resistors; outputmirror fixed.
No adopted hardware change: extra unit devices require real layout and new PEX.
"""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;source=HERE.parent/'postlayout/g1_bgr_pex.spice';out=HERE/'candidates/bgr_array4_parallel_r';out.mkdir(exist_ok=False);text=source.read_text();base=[];added=[];mapping=[];keep={'XM40','XM46','XM53'}
for line in text.splitlines():
 p=line.split()
 duplicate=bool(p) and (p[0].startswith('XR') or (p[0].startswith('XM') and p[0] not in keep) or (p[0].startswith('XQ') and p[1:4]!=['vss','vss','vss']))
 if duplicate:
  for unit in [2,3,4]:
   name=p[0]+f'_u{unit}';added.append(line.replace(p[0],name,1));mapping.append({'original':p[0],'new':name,'original_full_unit_geometry_preserved':True})
 if line.lower().startswith('.ends'):base.extend(added)
 base.append(line)
assert len(added)==222
variant='\n'.join(base)+'\n';(out/'baseline_pex.spice').write_text(text);(out/'bgr_array4_parallel_r.spice').write_text(variant)
m={'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(variant.encode()).hexdigest(),'added_physical_units':mapping,'unchanged_output_mirror_instances':sorted(keep),'intent':'Core4x current and4x originalphysicalunitdevices preserve per-unitdensity. Fourparallel originalresistorunits giveR/4 withoriginalend/contactTC insteadquarterlength. IPTAToutputsourcepair/cascode remainunchanged.','area':'Resistoractivebodyarea4xbaseline;75addedMOS39addedHBT108addedR;total308deviceinstances. Legalplacement,guardspacing,routecontacts anddie-fitnotrun.','mismatch':'Eachactualunit gets PDKlocalindependentdraw. Noartificialrandom scaling/cardedit. Spatialcorrelation unknown, so modeledarrayyield isnotphysicalsiliconyield.','parasitics':'BaselinewireCPEXretained; addedintrinsicdevicecaps modeled; newwiring/coupling/fill/contactparasitics notextracted.','status':'prepared; nominal andallphysical/electricalchecks notrun; unadopted'};(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'candidate_sha256':m['candidate_sha256'],'added_units':len(added)}))
