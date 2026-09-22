#!/usr/bin/env python3
"""Bind separate external-terminal current observations to frozen via-only targets."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('capacity','room','hot','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    cap=json.loads(a.capacity.read_text());assert cap['status']=='passed topology inventory'
    assert cap['GDS_sha256']=='8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
    rows=[];inputs={}
    for condition,path in [('room',a.room),('hot',a.hot)]:
        report,=json.loads(path.read_text());assert report['terminal_current_contract_status']=='passed'
        ac=report['accounting'];terms=ac['terminals'];assert len(terms)==102
        lookup={(t['macro'],t['device'],t['terminal'],t['rail']):t for t in terms}
        assert len(lookup)==102
        inputs[condition]=dict(sha256=sha(path),warnings=report['warnings'],
                              original_voltage_comparisons=report['canonical_fixture_voltage_comparison'])
        for rail in cap['rows']:
            for target in rail['per_target_via_only']:
                labels=target['terminals'];members=[];method=None
                if all(s.endswith('/source') for s in labels):
                    for label in labels:
                        parts=label.split('/')
                        macro,device=(parts[0].lower(),parts[1]) if len(parts)==3 else ('top',parts[0])
                        members.append(lookup[(macro,device,'S',rail['net'])])
                    method='sum of individual sampled absolute source-current peaks; conservative within saved samples only'
                elif labels==['XMBI/body']:
                    members=[lookup[('top','XMBI','B',rail['net'])]]
                    method='individual external body current; physical contact sharing not proved'
                elif labels==['Rbank/port','pin/anchor']:
                    members=[lookup[('top','RBANK','VSS_GROUP','vss')]]
                    method='signed resistor-bank aggregate at common access; not individual resistor/contact allocation'
                current=None
                if members:
                    current=sum(t['shunt_subtracted_entering_terminal_windows']['complete']['sampled_abs_peak_A'] for t in members)
                elif rail['net']=='vdd' and len(labels)==1 and labels[0].endswith('/pin/anchor'):
                    macro=labels[0].split('/')[0].lower()
                    current=ac['macro_shunt_subtracted_current_windows']['complete'][macro]['sampled_abs_peak_A']
                    method='accounted sampled macro VDD current at aggregate access'
                entry=dict(condition=condition,rail=rail['net'],metal_component=target['metal_component'],
                           terminals=labels,via_only_50pct_engineering_capacity_mA=target['engineering_50pct_capacity_mA'],
                           current_mapping='passed explicit terminal binding' if current is not None else 'not run: physical partition or aggregate not proved',
                           allocation_method=method,
                           members=[dict(macro=t['macro'],device=t['device'],terminal=t['terminal'],rail=t['rail']) for t in members])
                if current is not None:
                    entry.update(observed_window_upper_A=current,
                                 observed_to_105C_50pct_via_capacity_ratio=current*1e3/target['engineering_50pct_capacity_mA'],
                                 comparison_scope='descriptive screen only; 125C applicability, simultaneous multicommodity flow and wire/contact limits not qualified')
                rows.append(entry)
    bound=[r for r in rows if 'observed_window_upper_A' in r]
    result=dict(status='passed exact terminal-to-target binding for explicitly mapped rows; full current margin not qualified',
                script_sha256=sha(Path(__file__)),capacity_sha256=sha(a.capacity),GDS_sha256=cap['GDS_sha256'],
                inputs=inputs,rows=rows,mapped_rows=len(bound),not_run_rows=len(rows)-len(bound),
                maximum_descriptive_ratio=max(r['observed_to_105C_50pct_via_capacity_ratio'] for r in bound),
                conditions='seed73001, nominal process3.3V, CM0, shunt25mV, room25C/hot125C, 1.02us DC-initialized',
                limits_scope='Stock via limits: 11years105C only. 50% is declared engineering target, not foundry derating.',
                not_run=['full corner/startup envelope','individual shared body-tap allocation','individual resistor currents',
                         'wire/contact current-density assignment','simultaneous graph flow/current-sharing proof','125C lifetime qualification'])
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','inputs')},indent=2))


if __name__=='__main__':main()
