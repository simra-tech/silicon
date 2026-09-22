#!/usr/bin/env python3
"""Output-only six-input PSP metadata/internal-node availability with exact OP parity."""
import argparse
import difflib
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRIP=HERE.parents[2]/'g1_trip/sim'
sys.path.insert(0,str(TRIP))
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wave(path):
    if path.exists():return path.read_bytes()
    with gzip.open(str(path)+'.gz','rb') as stream:return stream.read()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert os.sched_getaffinity(0)=={7} and not a.output.exists()
    a.reference=a.reference.resolve();a.output=a.output.resolve()
    prior=json.loads((a.reference/'summary.json').read_text())[0]
    assert prior['status'].startswith('passed accounted characterization')
    provenance=json.loads((a.reference/'provenance.json').read_text())
    runtime=provenance['runtime_identity']
    pd=Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert subprocess.check_output(['ngspice','--version'],text=True)==runtime['ngspice_version']
    for name,digest in runtime['model_sha256'].items():assert sha(pd/name)==digest,name
    psp=json.loads((HERE/'psp-junction-source-equations-20260922-r1.json').read_text())
    expected_osdi={n:h for n,h in psp['file_hashes'].items() if n.endswith('.osdi')}
    assert len(expected_osdi)==2
    for name,digest in expected_osdi.items():assert sha(pd/name)==digest,name
    runtime['observed_osdi_sha256']={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/osdi').glob('*.osdi'))}
    runtime['PSP_OSDI_prior_hashes_exact']=True
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    original=(a.reference/'probe.cir').read_text()
    old='qualification/'+a.reference.name
    assert old in original and original.count('echo POPULATION_OP_END\n')==1
    text=original.replace(old,str(a.output))
    text,n=re.subn(r'^(\.save .+)$',lambda m:m[1]+' all',text,flags=re.M)
    assert n==1
    devices=['n.xs.'+block+'.'+name+'.nsg13_hv_pmos' for block in ('xota','xbuf','xref') for name in ('xm1','xm2')]
    commands='echo SHARED_METADATA_BEGIN\ndisplay\n'
    for name in devices:
        commands+='echo DEVICE_BEGIN_'+name+'\nshow '+name+'\necho DEVICE_END_'+name+'\n'
    commands+='write '+str(a.output/'all_op.raw')+' all\necho SHARED_METADATA_END\n'
    text=text.replace('echo POPULATION_OP_END\n',commands+'echo POPULATION_OP_END\n')
    a.output.mkdir(parents=True)
    for name in ('sense.spice','trip.spice','bgr.spice'):
        (a.output/name).write_bytes((a.reference/name).read_bytes())
    (a.output/'.spiceinit').write_bytes((TRIP/'.spiceinit').read_bytes())
    (a.output/'probe.cir').write_text(text)
    (a.output/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'contract.md').write_bytes((HERE/'SHARED_JUNCTION_DIAGNOSTIC_CONTRACT_20260922.md').read_bytes())
    (a.output/'output_only.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='reference',tofile='output-only')))
    binding=dict(source_sha256=sha(source),reference_deck_sha256=sha(a.reference/'probe.cir'),
        candidate_deck_sha256=sha(a.output/'probe.cir'),reference_provenance_sha256=sha(a.reference/'provenance.json'),
        sources={n:sha(a.output/n) for n in ('sense.spice','trip.spice','bgr.spice')},runtime=runtime,
        runner_sha256=sha(Path(__file__)),contract_sha256=sha(a.output/'contract.md'))
    (a.output/'bindings.json').write_text(json.dumps(binding,indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:
        state=run_bounded(['ngspice','-b','probe.cir'],log,a.output/'run.json',120,cwd=a.output,interval_s=1)
    result=dict(status='failed',runtime=state,bindings_sha256=sha(a.output/'bindings.json'),intrinsic_applicability='not run',model_change='not run')
    try:
        assert state['status']=='completed' and state['returncode']==0
        log=(a.output/'run.log').read_text();oldlog=(a.reference/'run.log').read_text()
        assert 'SHARED_METADATA_END' in log and 'POPULATION_OP_END' in log
        assert not re.search(r'^Error|no such device|no such vector|no such parameter|analysis aborted|Timestep too small',log,re.M)
        values=lambda s:re.findall(r'^(@[^\s]+)\s*=\s*(\S+)',s,re.M)
        assert values(log)==values(oldlog) and len(values(log))==2*(11512+27)
        result['complete_original_parameters_and_legacy_exact']=True
        result['original_wave_exact']={n:wave(a.output/n)==wave(a.reference/n) for n in ('op0.dat','currents.dat','monitor_voltages.dat')}
        assert all(result['original_wave_exact'].values())
        result['warnings']=warning_inventory(log)
        result['reference_warnings']=warning_inventory(oldlog)
        result['metadata']={}
        for name in devices:
            matches=re.findall('^DEVICE_BEGIN_'+re.escape(name)+r'\n(.*?)^DEVICE_END_'+re.escape(name)+'$',log,re.M|re.S)
            assert len(matches)==1 and 'PSP103VA' in matches[0]
            result['metadata'][name]=matches[0]
        raw=(a.output/'all_op.raw').read_text()
        variable_section=raw.split('Variables:\n',1)[1].split('Values:\n',1)[0]
        variables=[line.split()[1:] for line in variable_section.splitlines() if line.strip()]
        result['selected_internal_variables']=[row for row in variables if any(device in row[0] for device in devices)]
        result['raw_variables']=len(variables)
        result['all_op_raw_sha256']=sha(a.output/'all_op.raw')
        assert sum(f.stat().st_size for f in a.output.rglob('*') if f.is_file())<=32*2**20
        result['status']='passed output-only OP parity and availability inspection; applicability not qualified'
    except (AssertionError,ValueError,IndexError,OSError) as exc:
        result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('metadata','warnings','reference_warnings')},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__=='__main__':
    main()
