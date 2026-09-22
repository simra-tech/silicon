#!/usr/bin/env python3
"""Separate derivative: only original XM31/XM33 L0.5→0.6um, no other edits."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT='bgr_loop24_qref4_r253p465'
NAME=PARENT+'_hv06'
PARENT_SHA='53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    audit_path=HERE/'short_hv_diffusion_20260922_r1.json'
    audit=json.loads(audit_path.read_text())
    assert audit['status']=='passed isolated native diffusion applicability'
    assert audit['normalized_source_and_drain_geometry_identical'] and not audit['errors']
    source=HERE/'candidates'/PARENT/(PARENT+'.spice')
    parent_manifest=source.with_name('manifest.json')
    original=source.read_bytes()
    assert sha(source)==PARENT_SHA
    rows=original.decode().splitlines();changed=[]
    for index,line in enumerate(rows):
        fields=line.split()
        if not fields or fields[0] not in ['XM31','XM33']:continue
        assert fields.count('l=0.5u')==1
        assert all(value in fields for value in ['w=1u','as=0.34p','ad=0.34p','ps=2.68u','pd=2.68u','rfmode=0'])
        rows[index]=line.replace('l=0.5u','l=0.6u')
        changed.append({'instance':fields[0],'line_number':index+1,'before':line,'after':rows[index]})
    assert {r['instance'] for r in changed}=={'XM31','XM33'} and len(changed)==2
    candidate=('\n'.join(rows)+'\n').encode()
    restored=rows.copy()
    for row in changed:restored[row['line_number']-1]=row['before']
    assert ('\n'.join(restored)+'\n').encode()==original
    old=json.loads(parent_manifest.read_text())
    names=[line.split()[0] for line in rows if line.startswith(('XM','XQ','XR'))]
    assert len(names)==len(set(names))==1036
    counts={kind:sum(name.startswith(kind) for name in names) for kind in ['XM','XQ','XR']}
    assert counts==old['device_counts']=={'XM':336,'XQ':301,'XR':399}
    assert len(old['fingerprint_parameters'])==2842
    out=HERE/'candidates'/NAME;out.mkdir(exist_ok=False)
    (out/'parent_candidate.spice').write_bytes(original)
    (out/(NAME+'.spice')).write_bytes(candidate)
    (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    manifest={'status':'prepared, unadopted; electrical controls not run',
              'parent_source_sha256':PARENT_SHA,'parent_manifest_sha256':sha(parent_manifest),
              'candidate_sha256':hashlib.sha256(candidate).hexdigest(),'generator_sha256':sha(Path(__file__)),
              'changes':changed,'reverse_byte_reconstruction':'passed',
              'diffusion_applicability_audit_sha256':sha(audit_path),
              'device_counts':counts,'expected_fingerprint_count':2842,
              'fingerprint_parameters':old['fingerprint_parameters'],
              'unchanged':'All source bytes except two original l=0.5u→0.6u tokens; w1u and explicit diffusion A/P, coreloop24/Qref4, R2=53.465u, cards, wiring CPEX and other original geometry unchanged.',
              'rationale':'Addresses the explicit public HVNMOS LG≥0.6um condition for3.3V@27C, not a lower-voltage rating or3.6V/125C reliability solution.',
              'physical_scope':'Stock isolated diffusion A/P applicability checked; gate area and drain position change. Wholelayout/contacts/routes/fill/newPEX/fullDRC/LVS not run.',
              'remaining_controls':'Only proposed nominal34temps and exact27C3V startup1ms/100ms controls; no simulation authorized by generator. No MC or adoption.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ['candidate_sha256','changes','reverse_byte_reconstruction','device_counts','expected_fingerprint_count']}))

if __name__=='__main__':main()
