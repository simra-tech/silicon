#!/usr/bin/env python3
"""Create real additional unit-device candidate, with explicit extraction limits."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;source=HERE.parent/'postlayout/g1_bgr_pex.spice'
out=HERE/'candidates/bgr_array4';out.mkdir(parents=True,exist_ok=False)
text=source.read_text();lines=text.splitlines();devices={r.split()[0]:r for r in lines if r.startswith('XQ')}
selected=['XQ56','XQ67',*[f'XQ{i}' for i in range(68,75)],'XQ76']
assert len(selected)==10
added=[]
for name in selected:
 row=devices[name];assert 'Nx=1' in row
 for unit in [2,3,4]:added.append(row.replace(name,name+f'_u{unit}',1))
assert len(added)==30
variant=text.replace('.ends g1_bgr','\n'.join(added)+'\n.ends g1_bgr')
assert variant!=text and variant.count('.ends g1_bgr')==1
(out/'baseline_pex.spice').write_text(text);(out/'bgr_array4_schematic_additions.spice').write_text(variant)
manifest={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(variant.encode()).hexdigest(),'added_instances':30,'Q1_units':4,'Q1B_test_mode_units':4,'Q2_units':32,'model_geometry':'Every added device is a separate npn13G2 Nx1 instance, using the existing legal unit geometry. No arbitrary mismatch scaling; no PDK-card changes.','current_policy':'R1, all bias devices and other resistor values unchanged initially. Nominal branch current is intended near baseline, so per-unit Q1/Q2 current density is approximately one quarter. Actual current, VREF, TC and pbias/pcasc must be checked before any mismatch campaign.','test_mode':'Q1B also scaled to4 separate units, preserving the intended r4high area ratio8:32=1:4.','parasitics':'Existing C-PEX retained for unchanged circuit, plus intrinsic models of30 added units. New array wiring, fill, coupling, substrate effects and layout are NOT extracted. This is a schematic-addition candidate, not regenerated PEX or physical sign-off.','spatial_statistics':'Independent unit-local PDK qarea draws omit real spatial correlation; predicted averaging is not a measured silicon-yield claim.','layout_status':'not run: no placement/routing/DRC/LVS or footprint acceptance for the enlarged arrays.'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
