#!/usr/bin/env python3
"""Independent electrode-to-pad proof for three comparator-reported DUTs."""
import argparse
import json
from pathlib import Path
import pya
from prepare_saved_workers import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('database', 'ports', 'source', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists()
    assert sha(a.database) == '3ed5cd2b78b3d4f4ed724730fcba2388148340d6442249e143c17a9f7ac99f04'
    assert sha(a.source) == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
    ports = json.loads(a.ports.read_text())
    assert ports['status'].startswith('passed read-only 24 physical ports / 22 distinct')
    assert sha(a.database) in ports['inputs'].values()
    records = [
        ('HBT', 'npn13g2', 'Q1 HBT_C HBT_B HBT_E vss npn13G2 le=900e-9 we=70.0n Nx=1',
         'Xi_core_u_dut HBT_C HBT_B HBT_E VSS / g1_dut_macro', dict(C='HBT_C', B='HBT_B', E='HBT_E', S='VSS')),
        ('HV_DOSE', 'sg13_hv_nmos', 'MHV D_ELT G_SHARED vss vss sg13_hv_nmos w=3.98u l=0.45u ng=1 m=1',
         'Xi_core_u_dose D_ELT D_STD G_SHARED VSS / g1_dose_macro', dict(D='D_ELT', G='G_SHARED', S='VSS', B='VSS')),
        ('LV_DOSE', 'sg13_lv_nmos', 'MLV D_STD G_SHARED vss vss sg13_lv_nmos w=3.98u l=0.13u ng=1 m=1',
         'Xi_core_u_dose D_ELT D_STD G_SHARED VSS / g1_dose_macro', dict(D='D_STD', G='G_SHARED', S='VSS', B='VSS'))]
    source_lines = a.source.read_text().splitlines()
    for _, _, record, instance, _ in records:
        assert source_lines.count(record) == source_lines.count(instance) == 1
    db = pya.LayoutVsSchematic(); db.read(str(a.database)); nl = db.netlist().dup()
    top = nl.circuit_by_name('placed_core_NOT_CONNECTED_FULLCHIP'); assert top
    for pin, (circuit_name, cluster) in ports['logical_bindings'].items():
        assert circuit_name == top.name
        matching = [n for n in top.each_net() if n.cluster_id == cluster]; assert len(matching) == 1
        matching[0].set_property('G1_INDEPENDENT_PHYSICAL_PORT', pin)
    nl.flatten(); top = nl.circuit_by_name(top.name)
    rows = []
    for label, model, record, instance, expected in records:
        matches = []
        for device in top.each_device():
            klass = device.device_class()
            if klass.name.lower() != model:
                continue
            observed = {t.name: device.net_for_terminal(t.name).property('G1_INDEPENDENT_PHYSICAL_PORT') for t in klass.terminal_definitions()}
            if observed == expected:
                matches.append(dict(name=device.expanded_name(), terminals=observed,
                                    parameters={q.name: device.parameter(q.name) for q in klass.parameter_definitions()}))
        assert len(matches) == 1, (label, len(matches))
        rows.append(dict(design_instance=label, original_source_record=record, original_parent_call=instance,
                         unique_actual_native_device=matches[0], scoped_electrode_incidence='passed',
                         complete_parameter_model_applicability='not run'))
    result = dict(status='passed independent unique DUT/dose electrode-to-physical-pad incidence',
                  inputs={str(q): sha(q) for q in (a.database, a.ports, a.source)},
                  script_sha256=sha(Path(__file__)), devices=rows,
                  not_run=['global strict LVS acceptance', 'MOS written-zero/native-positive junction A/P applicability',
                           'electrical or ESD qualification'],
                  preserved_failure='All three remain in actual global comparator mismatch ledger; no same-net hint was used.')
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
