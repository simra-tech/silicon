#!/usr/bin/env python3
"""Enumerate frozen source terminal slots and existing native witnesses, selecting no injection plane."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
DESIGN=HERE.parents[2]
GM4=DESIGN/'blocks/g1_sense/layout/coordinated_gm4'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    source=DESIGN/'blocks/g1_sense/reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    refpath=GM4/'ring-r8-evidence-20260922-r1/sense-ring-reference-20260922-r8a/manifest.json'
    gds=GM4/'ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    native_manifest=gds.parent/'manifest.json';native=json.loads(native_manifest.read_text())
    assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    assert sha(gds)=='8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
    assert native['GDS_sha256']==sha(gds)
    ref=json.loads(refpath.read_text());assert ref['source_sha256']==sha(source)and ref['GDS_sha256']==sha(gds)
    assert ref['terminal_audit']['status']=='passed'
    blocks={s.split()[1]:s for s in re.findall(r'(?ms)^\.subckt .*?^\.ends[^\n]*',source.read_text())}
    ports=blocks['g1_sense'].splitlines()[0].split()[2:];devices=[]
    roles={'sg13_hv_nmos':['D','G','S','B'],'sg13_hv_pmos':['D','G','S','B'],
           'rppd':['1','2','BN'],'cap_cmim':['TOP','BOTTOM']}
    def collect(block,prefix,pmap):
        def net(n):return pmap.get(n,n if n=='0'else prefix+n)
        for line in blocks[block].splitlines():
            if not line.startswith('X'):continue
            words=line.split();name=prefix+words[0]
            if words[-1]in blocks:
                sub=words[-1];subports=blocks[sub].splitlines()[0].split()[2:]
                assert len(subports)==len(words)-2
                collect(sub,name+'/',dict(zip(subports,[net(n)for n in words[1:-1]])))
            else:
                model=next(q for q in words if q in roles)
                assert words[len(roles[model])+1]==model
                devices.append(dict(device=name,model=model,source_line=line,
                    terminal_nets=dict(zip(roles[model],[net(n)for n in words[1:len(roles[model])+1]]))))
    collect('g1_sense','',dict(zip(ports,ports)))
    assert len(devices)==159 and {d['device']for d in devices}==set(ref['source_lines'])
    assert all(d['source_line']==ref['source_lines'][d['device']]for d in devices)
    probes=ref['terminal_audit']['probes'];assert len(probes)==2011
    source_nets=set(ports)|{n for d in devices for n in d['terminal_nets'].values()}
    assert len(source_nets)==134 and source_nets=={r['net']for r in probes}
    slots=[]
    for device in devices:
        name=device['device'];model=device['model']
        for role,net in device['terminal_nets'].items():
            row=dict(device=name,model=model,terminal=role,source_net=net,
                selected_injection_point=None,model_boundary_qualified=False,
                external_metal_contact_site_enumeration='not run')
            own=[r for r in probes if r['device']==name and r['net']==net]
            if role=='G':
                witnesses=[r for r in own if r['terminal']=='gate'];assert witnesses
                row.update(evidence_kind='owned channel gate witnesses, not metal pads',witnesses=witnesses,
                    channel_count=len(witnesses),boundary_issue='Trace each actual gate-poly contact to metal; do not relabel channel center as M1')
            elif role in('D','S'):
                strips=[r for r in ref['strips']if r['net']==net and name in r['adjacent_owners']]
                assert strips
                row.update(evidence_kind='adjacent-gate-owned diffusion strips, not chosen metal injection',
                    strips=strips,strip_count=len(strips),
                    shared_with_other_logical_devices=sum(len(r['adjacent_owners'])>1 for r in strips),
                    boundary_issue='Multiple distributed contacts; no ideal joining, finger splitting or single-point selection authorized')
            elif role=='B':
                witnesses=[r for r in probes if r['net']==net and r['terminal']in('body','well_tap','substrate_tap')]
                row.update(evidence_kind='shared-net tap witnesses only; per-device well/substrate path unassigned',
                    shared_tap_witnesses=witnesses,
                    boundary_issue='Shared voltage name does not establish device-local spreading/metal attachment')
            elif role=='BN':
                row.update(evidence_kind='source-defined substrate terminal without localized metal plane',
                    boundary_issue='Do not silently bind resistor BN to a chosen VSS mesh point or fit compact-model end resistance')
            else:
                terms=('end0','end1','end')if model=='rppd'else(role.lower(),)
                witnesses=[r for r in own if r['terminal']in terms];assert len(witnesses)==1,(name,role,witnesses)
                row.update(evidence_kind='existing source-bound external-metal witness; no new geometric extraction',
                    witnesses=witnesses,boundary_issue='Actual head/electrode model deembedding not established')
            slots.append(row)
    for port in ports:
        changed=[r['new']for r in native['external_port_map']if r['net']==port]
        assert len(changed)<=1
        layer=changed[0]['layer']if changed else 50
        found=[r for r in probes if r['device']=='pin'and r['terminal']=='anchor'and r['net']==port and r['layer']==layer]
        assert len(found)==1
        if changed:assert found[0]['point_um']==changed[0]['point_um']
        else:assert found[0]['point_um'][0]==384.0
        slots.append(dict(device='PORT',terminal=port,source_net=port,witnesses=found,
            evidence_kind='exact r8 external port anchor',selected_injection_point=None,
            model_boundary_qualified=False,external_metal_contact_site_enumeration='not run'))
    assert len(slots)==541 and len({(r['device'],r['terminal'])for r in slots})==541
    counts=collections.Counter(r['terminal']if r['device']!='PORT'else'PORT'for r in slots)
    result=dict(status='prepared source-bound 541-slot witness ledger; metal attachment/model boundary not qualified',
        source_sha256=sha(source),GDS_sha256=sha(gds),reference_manifest_sha256=sha(refpath),
        native_manifest_sha256=sha(native_manifest),
        script_sha256=sha(Path(__file__)),source_net_count=134,source_nets=sorted(source_nets),
        primitive_count=159,slot_count=541,slot_counts=dict(counts),devices=devices,slots=slots,
        no_source_or_geometry_written=True,no_circuit_or_extraction_launched=True,
        not_run=['new saved-GDS contact/pin-plane enumeration','distributed multifinger/body/BN boundary qualification',
                 'positive-metal extraction','zero-R fullparameter/wave parity','nonzero-R electrical sensitivity','adoption'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in('devices','slots','source_nets')},indent=2))


if __name__=='__main__':main()
