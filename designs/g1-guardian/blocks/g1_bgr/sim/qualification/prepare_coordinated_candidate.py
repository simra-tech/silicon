#!/usr/bin/env python3
"""Generate only the reviewed, unadopted loop24/Qref4/R2 candidate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE_SHA = '72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77'
NAME = 'bgr_loop24_qref4_r253p465'
GROUPS = {
    'PTAT_MOS': ('XM', [34,35,36,37,38,39,41,45,47,48,50,52,54], 24),
    'PTAT_HBT': ('XQ', [56,62,67,68,69,70,71,72,73,74,75,76], 24),
    'PTAT_RES': ('XR', [16,23,24,25,26,77,78,79,80,81,82,83,84,85,86], 24),
    'QREF_MOS': ('XM', [43,44,51], 4),
    'QREF_HBT': ('XQ', [60], 4),
    'QREF_RES': ('XR', [17,18,19,20,21,22], 4),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    source = HERE.parent/'postlayout/g1_bgr_pex.spice'
    original_bytes = source.read_bytes()
    assert sha(original_bytes) == BASELINE_SHA
    original = original_bytes.decode()
    count_by_name = {prefix+str(i): count for prefix, ids, count in GROUPS.values() for i in ids}
    centered = {'XR'+str(i) for i in range(17,23)}
    additions, lines, mapping, changed, found = [], [], [], [], set()
    for line in original.splitlines():
        fields = line.split()
        if fields and fields[0] in count_by_name:
            name = fields[0]
            found.add(name)
            base = line
            if name in centered:
                assert fields.count('l=52.5u') == 1 and 'w=1u' in fields
                base = line.replace('l=52.5u', 'l=53.465u')
                changed.append({'instance':name, 'before':line, 'after':base})
            line = base
            for n in range(2,count_by_name[name]+1):
                unit = name+'_u'+str(n)
                additions.append(base.replace(name,unit,1))
                mapping.append({'original':name,'new':unit,'group_copies':count_by_name[name]})
        if line.lower().startswith('.ends'):
            lines.extend(additions)
        lines.append(line)
    assert found == set(count_by_name) and len(changed) == 6 and len(additions) == 950
    candidate = '\n'.join(lines)+'\n'
    # Reversing precisely the authorized edits must recover every baseline byte.
    added_names = {row['new'] for row in mapping}
    restored = []
    for line in candidate.splitlines():
        fields = line.split()
        if fields and fields[0] in added_names:
            continue
        if fields and fields[0] in centered:
            line = line.replace('l=53.465u','l=52.5u')
        restored.append(line)
    assert ('\n'.join(restored)+'\n').encode() == original_bytes
    instances = [line.split()[0] for line in lines if line.startswith(('XM','XQ','XR'))]
    assert len(instances) == len(set(instances))
    counts = {kind:sum(name.startswith(kind) for name in instances) for kind in ['XM','XQ','XR']}
    assert counts == {'XM':336,'XQ':301,'XR':399}
    parameters = []
    for line in lines:
        f = line.split()
        if not f: continue
        name = f[0].lower()
        if f[0].startswith('XM'):
            parameters += [f'@n.xbgr.{name}.n{f[5]}[{p}]' for p in ['w','l','delvto','factuo']]
        elif f[0].startswith('XR'):
            parameters += [f'@n.xbgr.{name}.nr1[{p}]' for p in ['nsmm_rsh','nsmm_w','nsmm_l']]
        elif f[0].startswith('XQ'):
            parameters.append(f'@q.xbgr.{name}.qnpn13g2[area]')
    assert len(parameters) == len(set(parameters)) == 2842
    output = HERE/'candidates'/NAME
    output.mkdir(exist_ok=False)
    (output/'baseline_pex.spice').write_bytes(original_bytes)
    (output/(NAME+'.spice')).write_text(candidate)
    (output/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    manifest = {
        'status':'prepared, unadopted; nominal/density/terminal checks not run',
        'baseline_sha256':BASELINE_SHA, 'candidate_sha256':sha(candidate.encode()),
        'generator_sha256':sha(Path(__file__).read_bytes()),
        'mapping_groups':GROUPS, 'added_units':mapping, 'modified_original_lines':changed,
        'original_byte_reconstruction':'passed', 'device_counts':counts,
        'expected_fingerprint_count':2842, 'fingerprint_parameters':parameters,
        'fixed_R2_length_um':'53.465', 'fixed_R2_width_um':'1',
        'fixed_R2_length_ratio':'1.018380952380952380952380952',
        'nominal_source_curve_sha256':'a74da41206c410fb2b4cef21cdc5fcac576940e86beb152ff875dfda5a66cb2c',
        'hypothesis':'PTAT loop24 and Qref branch4 parallel full original units should preserve nominal unit current density. R2 alone has fixed nominal-only centering; actual current, TC and headroom must be measured. No sample fitting.',
        'unchanged':'All original lines other than six XR17-22 lengths, all cards, original HBT Nx=1 geometry, startup/detector/IPTAT output and existing CPEX wiring.',
        'physical_scope':'New native device parasitics modeled, original wiring CPEX retained. New layout/routing/fill/contacts/PEX, whole-floorplan fit and die change not run/adopted.',
        'statistical_scope':'No MC authorized. Separate model-unit draws do not establish spatial independence or manufactured yield.',
    }
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ['candidate_sha256','original_byte_reconstruction','device_counts','expected_fingerprint_count']}))

if __name__ == '__main__':
    main()
