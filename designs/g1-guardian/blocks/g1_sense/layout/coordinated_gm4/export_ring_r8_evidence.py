#!/usr/bin/env python3
"""Compact r8 plus intrinsic-attribution evidence, retaining prior milestones."""
from pathlib import Path
from export_ring_evidence import sha

HERE=Path(__file__).resolve().parent


def main():
    original=HERE/'export_ring_evidence.py'
    assert sha(original)=='cef9fd08a5caa897f5924c17371bf68adb7722a823d86d9573fde8228dea9330'
    text=original.read_text()
    start=text.index("    add('sense-ring-routing-20260922-r7a',")
    end=text.index('    assert sum(',start)
    selected="""    add('sense-ring-routing-20260922-r8a','manifest.json builder_snapshot.py g1_sense_physical.gds')
    add('sense-ring-routing-20260922-r8a-preparation','derived_builder.py adapter_snapshot.py bindings.json')
    add('sense-ring-routing-20260922-r8a-r8-adapter','derived_adapter.py r8_adapter_snapshot.py')
    add('sense-ring-reference-20260922-r8a','manifest.json g1_sense_physical.cdl audit_snapshot.py')
    add('sense-ring-stock-20260922-r8a','summary.json drc.log lvs.log drc/g1_sense_physical_g1_sense_physical_full.lyrdb lvs/g1_sense_physical_extracted.cir')
    add('', 'sense-ring-saved-20260922-r8a.json sense-ring-capacity-20260922-r8a.json sense-ring-junction-20260922-r8a.json')
    add('sense-ring-saved-20260922-r8a-preparation','derived_audit.py adapter_snapshot.py')
"""
    text=text[:start]+selected+text[end:]
    assert text.count('9559f0d309f0c14d2f226e56138dfd0283cf2b847f0b536929565e4a739b9b02')==1
    text=text.replace('9559f0d309f0c14d2f226e56138dfd0283cf2b847f0b536929565e4a739b9b02',
                      '8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7')
    text=text.replace('sense-ring-stock-20260922-r7a/summary.json','sense-ring-stock-20260922-r8a/summary.json')
    text=text.replace('frozen r7 and ownership milestone','frozen r8 and intrinsic-attribution milestone')
    namespace={'__file__':str(Path(__file__)),'__name__':'r8_evidence_derivative'}
    exec(compile(text,str(original),'exec'),namespace)
    namespace['SOURCES']=('build_ring_power_revision_r8.py audit_ring_power_revision_r8.py RING_POWER_R8_20260922.md '
        'audit_mos_combination_semantics.py audit_intrinsic_junction_scope.py mos-combiner-semantics-20260922-r1.json '
        'intrinsic-junction-scope-20260922-r1.json INTRINSIC_JUNCTION_SCOPE_20260922.md export_ring_r8_evidence.py').split()
    namespace['main']()


if __name__=='__main__':
    main()
