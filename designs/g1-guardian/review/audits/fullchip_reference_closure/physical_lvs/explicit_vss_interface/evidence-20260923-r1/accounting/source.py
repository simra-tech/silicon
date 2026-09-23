#!/usr/bin/env python3
"""Independent saved-discrepancy accounting; never promote tap warnings."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ('preparation','comparison','output'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); assert not a.output.exists()
    prep_path=a.preparation/'summary.json'; prep=json.loads(prep_path.read_text())
    summary_path=a.comparison/'diagnostic/summary.json'; summary=json.loads(summary_path.read_text())
    pairs_path=a.comparison/'diagnostic/comparison.json'; circuits=json.loads(pairs_path.read_text())
    assert prep['original_library_definitions_byte_identical'] and prep['all_library_call_signatures_checked']
    assert summary['actual_comparison_source_sha256']==prep['adapter_sha256']
    assert summary['explicit_body_reader_controls']==dict(reachable_PTAP=386,all_WELL_on_VSS=True,
        no_local_SUB=True,three_other_supply_domains_distinct_from_VSS=True)
    assert summary['strict_actual_pin_pair_identity'] and summary['strict_source_top_pin_set']
    assert not summary['engine_equivalent'] and not summary['all_pairs_strict_Match']
    assert len(circuits)==1
    row=circuits[0]
    assert row['pairs']==dict(device=dict(Mismatch=1,Match=61230,MatchWithWarning=2),
        net=dict(Mismatch=3,Match=30942),pin=dict(Match=22),subcircuit={})
    bad=row['bad']['device']; taps=[v for v in bad if v['status']=='MatchWithWarning']
    assert len(taps)==2 and all(v['layout']['model'].upper()==v['reference']['model'].upper()=='PTAP1' for v in taps)
    dummy,=[v for v in bad if v['status']=='Mismatch']
    assert dummy['layout'] is None and dummy['reference']['model']=='sg13_hv_pmos'
    assert set(dummy['reference']['terminals'].values())=={'VDD'}
    assert {v['reference'] for v in row['bad']['net']}=={'VSS','VDD','IOVSS'}
    assert not row['bad']['pin'] and not row['bad']['subcircuit']
    tap_rows=[]
    for t in taps:
        source=t['reference']; layout=t['layout']
        A=Decimal(str(source['parameters']['A'])); P=Decimal(str(source['parameters']['P']))
        a2=Decimal(str(layout['parameters']['A'])); p2=Decimal(str(layout['parameters']['P']))
        tap_rows.append(dict(source_terminals=source['terminals'],source_AP=source['parameters'],
            native_AP=layout['parameters'],native_minus_source_A_um2=str(a2-A),
            native_minus_source_P_um=str(p2-P),
            conditional_rectangle_formula_source_ohm=str(Decimal(980)/(A+P)),
            conditional_rectangle_formula_native_ohm=str(Decimal(980)/(a2+p2)),
            resistance_scope='Formula illustration only; not qualified native/effective tap resistance; no source or model edit'))
    result=dict(status='passed independent residual accounting; strict comparison FAILED',
        inputs={str(q):sha(q) for q in (prep_path,summary_path,pairs_path,Path(__file__))},
        counts=row['pairs'],actual_22_pin_pairs='passed',explicit_941_body_connections='passed',
        remaining_tap_AP=tap_rows,remaining_combined_all_VDD_dummy=dummy,
        remaining_supply_net_mismatches=row['bad']['net'],
        inherited_metadata_error=dict(field='comparer.physical_pin_or_source_edits',
            observed=summary['comparer']['physical_pin_or_source_edits'],
            disposition='FAILED inherited scope annotation: physical pins unchanged, but source body connections intentionally changed. Exact source hash and intentional_source_interface_change field govern; original report preserved.'),
        checks=dict(source_controls='passed',physical_pin_identity='passed',strict_device_match='failed',
            complete_new_native_extraction='not run',dummy_extraction_reference='not run in this arm',
            power_sequencing_ESD_latchup='not run',tap_model_AP_applicability='failed to establish',
            seed_or_analog_solver='not applicable'))
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
