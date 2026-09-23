#!/usr/bin/env python3
"""Bind the pinned purefill -> RZ keepout -> text-normalized candidate chain.

This creates an immutable selection manifest. It does not regenerate geometry;
each transformation has separately passed record-exact regeneration checks.
"""
import argparse
import json
from pathlib import Path
import current_bindings as predecessor
import current_rz_bindings as b

TOP='placed_core_NOT_CONNECTED_FULLCHIP'
MAP_SHA='201612db70b2b611e8360188c363fccb810b4d76b77c194e8c74da0e8a4dd899'
def data(spec):return json.loads(b.bound(spec).read_text())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bondmap',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and b.sha(a.bondmap)==MAP_SHA
    predecessor.validate_inputs()
    for spec in (b.ORIGINAL_SOURCE,b.PUREFILL,b.KEEPOUT,b.CANDIDATE,b.FLAT_REFERENCE,b.STRICT_DB):b.bound(spec)
    pf=data(b.PUREFILL_PROOF);assert pf['status']=='passed exact pure-fill hierarchy projection; native LVS not run'
    assert pf['GDS_sha256']==b.PUREFILL[1]
    ko=data(b.KEEPOUT_PROOF);assert ko['status'].startswith('passed exact-only dummy-fill keepout')
    assert ko['candidate_gds_sha256']==b.KEEPOUT[1] and ko['removed_shapes']==39
    assert ko['removed_layers']=={'1/22':20,'5/22':19}
    tr=data(b.TRANSFORMATION);assert tr['input_gds_sha256']==b.KEEPOUT[1]
    assert tr['output_gds_sha256']==b.CANDIDATE[1]
    assert len(tr['root_external_labels'])==22 and len(tr['text_occurrences_removed'])==86 and len(tr['clones'])==38
    assert tr['paths_sha256']==b.PIN_PATHS[1] and tr['port_overlap_sha256']==b.PORT_OVERLAP[1]
    b.bound(b.PORT_REACH)
    identity=data(b.IDENTITY_PROOF);assert identity['candidate_GDS_sha256']==b.CANDIDATE[1]
    assert identity['flattened_all_layer_nontext_XOR_dbu2']==0
    assert identity['text_occurrences_removed']==86 and identity['root_134_25_text_records_added']==22
    for spec,reference,expected in ((b.KEEPOUT_RECORD_PROOF,b.KEEPOUT[1],6712041),
                                    (b.TEXT_RECORD_PROOF,b.CANDIDATE[1],6719503)):
        r=data(spec);assert r['status']=='passed exact GDS record identity except timestamp payloads'
        assert r['reference_gds_sha256']==reference and r['total_records']==expected
        assert r['all_nondate_records_byte_exact'] and r['other_record_differences']==0
    dummy=data(b.DUMMY_PROOF);assert dummy['status']=='passed independent three-dummy source/native-terminal proof'
    flat=data(b.FLAT_REFERENCE_PROOF);assert flat['status']=='passed exact stock-reader source flatten roundtrip'
    assert flat['output_sha256']==b.FLAT_REFERENCE[1]
    strict=data(b.STRICT_ANALYSIS);assert strict['status']=='passed strict saved comparison'
    assert all(strict['checks'].values())
    top=strict['database']['layout'][TOP]
    assert top['devices']==61684 and top['nets']==31173 and len(top['pins'])==22
    phys={}
    for name,spec in b.PHYSICAL.items():
        j=data(spec);assert j['status'].startswith('passed') and j['GDS_sha256']==b.CANDIDATE[1]
        assert j['inputs_rules_unchanged'];phys[name]=spec[1]
    bond=data(b.BOND_VALIDATION)
    assert bond['status'].startswith('passed exact 24 physical openings and 22 extracted pad-net identities')
    assert bond['candidate_gds_sha256']==b.CANDIDATE[1] and bond['new_map_sha256']==MAP_SHA
    assert len(bond['pads'])==24 and bond['unique_logical_pins']==22
    assert bond['all_pad_openings_exact'] and bond['all_pad_nets_exact']
    result=dict(status='passed pinned current RZ100 physical assembly selection; no geometry regenerated in this invocation',
        top=TOP,canonical_source_sha256=b.ORIGINAL_SOURCE[1],canonical_source_unchanged=True,
        comparison_only_source_sha256=b.FLAT_REFERENCE[1],three_source_only_dummies_proved=True,
        stage_gds_sha256={'purefill':b.PUREFILL[1],'rz_keepout':b.KEEPOUT[1],'root_text':b.CANDIDATE[1]},
        stage_proof_sha256={'purefill':b.PUREFILL_PROOF[1],'keepout':b.KEEPOUT_PROOF[1],
                            'root_text':b.IDENTITY_PROOF[1],'keepout_record_reproduction':b.KEEPOUT_RECORD_PROOF[1],
                            'root_text_record_reproduction':b.TEXT_RECORD_PROOF[1]},
        strict_lvs_analysis_sha256=b.STRICT_ANALYSIS[1],physical_summary_sha256=phys,
        bondmap_sha256=MAP_SHA,bondmap_validation_sha256=b.BOND_VALIDATION[1],
        exact_external_pins=22,physical_bondpads=24,
        prior_bindings_immutable=True,not_run=['full-chip PEX/currentIR/EM','electrical or tape-out adoption'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],candidate_gds_sha256=b.CANDIDATE[1],
                          exact_external_pins=22,physical_bondpads=24)))
if __name__=='__main__':main()
