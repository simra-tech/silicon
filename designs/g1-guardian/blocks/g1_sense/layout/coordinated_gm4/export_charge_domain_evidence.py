#!/usr/bin/env python3
"""Reuse qualified portable exporter for completed DeltaQ/domain controls only."""
from pathlib import Path
from export_junction_current_evidence import sha

HERE=Path(__file__).resolve().parent


def main():
    original=HERE/'export_junction_current_evidence.py'
    assert sha(original)=='f0df8627b1f06d6583436b8b2232b3785dc4b08a4f96a9aee535cb5a6a78f556'
    text=original.read_text();start=text.index("    for name in ('room-20260922-r1'")
    end=text.index('    def privacy(data):',start)
    selected="""    for case in ('zero','coarse','fine'):
        add('sense-junction-charge-'+case+'-20260922-r1',
            'contract.json run.json run.log probe.cir runner_snapshot.py initial.raw transient.raw analysis_r1.json')
    add('', 'sense-junction-charge-comparison-20260922-r1.json sense-computed-adapter-controls-20260922-r2.json sense-computed-adapter-controls-r1-failed.py')
    add('sense-computed-adapter-20260922-r1','summary.json audit_snapshot.py adapter_snapshot.py')
    add('sense-coupon-domains-20260922-r1','summary.json audit_snapshot.py')
    add('sense-coupon-domains-20260922-r2','audit_snapshot.py')
    add('sense-coupon-domains-20260922-r3','summary.json audit_snapshot.py')
    for receipt in ('sense_computed_adapter_controls_20260922_r1','sense_coupon_domains_20260922_r2'):
        for name in ('check.json','check.log'):
            selected.append((ROOT/'.private/research/verification'/receipt/name,Path('retained-control-failures')/receipt/name))
"""
    text=text[:start]+selected+text[end:]
    text=text.replace('passed portable observations; applicability/charge/completePEX unqualified',
                      'passed portable DeltaQ method and geometry-domain repair; full applicability/completePEX unqualified')
    text=text.replace('frozen observation/current milestone; root owns Git','frozen DeltaQ/domain-repair milestone; root owns Git')
    namespace={'__file__':str(Path(__file__)),'__name__':'charge_domain_export_derivative'}
    exec(compile(text,str(original),'exec'),namespace)
    namespace['SOURCES']=('run_junction_charge_control.py analyze_junction_charge_control.py compare_junction_charge_steps.py '
        'JUNCTION_CHARGE_CONTROL_20260922.md computed_layer_geometry_adapter.py audit_computed_layer_adapter.py '
        'test_computed_layer_adapter.py audit_coupon_field_domains.py COMPUTED_DOMAIN_REPAIR_20260922.md '
        'export_charge_domain_evidence.py').split()
    namespace['main']()


if __name__=='__main__':main()
