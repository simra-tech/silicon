#!/usr/bin/env python3
"""Source-mapped digital reference and strict native stock KLayout comparison."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from fullchip_reference_closure.prepare_reference import load_functions, sha
from fullchip_reference_closure.audit_reference import parse_verilog, parse_cdl, check_mapping, canonical_name
from fullchip_reference_closure.physical_lvs.inspect_stock_result_r4 import analyze


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('gds', 'pnl', 'output'):
        p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--gds-sha256', required=True)
    p.add_argument('--pnl-sha256', required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert sha(a.gds) == a.gds_sha256 and sha(a.pnl) == a.pnl_sha256
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    lib = pdk/'libs.ref/sg13g2_stdcell/cdl/sg13g2_stdcell.cdl'
    assembler = Path('${REPOSITORY}/designs/g1-guardian/blocks/g1_padring/flow/lvs/assemble_chip_cdl.py')
    ns = dict(re=re, sys=sys, SAME_CONDUCTOR={})
    load_functions(assembler, ['subckt_pins', 'san', 'verilog_to_subckt'], ns)
    source = lib.read_text()
    pin_order = ns['subckt_pins'](source)
    top, cdl, counts, dangling = ns['verilog_to_subckt'](str(a.pnl), pin_order, {})
    assert top == 'g1_digital'
    module, ports, instances = parse_verilog(a.pnl.read_text())
    assert module == top and len(ports) == 46
    # Independently parsed source masters and every named terminal are required.
    mapping = check_mapping(top, ports, instances, parse_cdl(source+'\n'+cdl), lambda n:n)
    assert mapping['instance_count'] == sum(counts.values()) == len(instances)
    assert mapping['singleton_unconnected_count'] == dangling == 60
    # Restore only the source-declared top port token spelling (e.g. bus[i]).
    # Geometry labels/pin assignments must not change to suit CDL sanitization.
    port_names = {canonical_name(x):x for x in ports if canonical_name(x) != x}
    assert len(port_names) == len(set(port_names.values()))
    assert all(x not in cdl.split() for x in port_names.values())
    source_cdl = re.sub(r'\S+', lambda m:port_names.get(m.group(), m.group()), cdl)
    inverse = {v:k for k,v in port_names.items()}
    assert re.sub(r'\S+', lambda m:inverse.get(m.group(), m.group()), source_cdl) == cdl
    assert parse_cdl(source_cdl)[top]['ports'] == ports
    rules = {str(x):sha(x) for x in (pdk/'libs.tech/klayout/tech/lvs').rglob('*') if x.is_file()}
    inputs = {str(x):sha(x) for x in (a.gds, a.pnl, lib, assembler, Path(__file__))}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    reference = a.output/'g1_digital_source.cdl'
    reference.write_text(source+'\n'+source_cdl)
    (a.output/'mapping.json').write_text(json.dumps(mapping, indent=2)+'\n')
    command = ['timeout', '--kill-after=5', '600', 'python3',
               str(pdk/'libs.tech/klayout/tech/lvs/run_lvs.py'),
               '--layout', str(a.gds), '--netlist', str(reference), '--topcell', top,
               '--run_mode', 'deep', '--top_lvl_pins', '--spice_comments',
               '--run_dir', str(a.output/'reports')]
    record = dict(status='running', command=command, inputs_sha256=inputs,
                  stock_rule_hashes=rules, reference_sha256=sha(reference),
                  source_instance_count=len(instances), unconnected_outputs=dangling,
                  source_top_port_spelling_restoration=port_names,
                  not_run=['Full-chip integration', 'PEX/model reference planes', 'Adoption'],
                  not_applicable=['Statistical seed'])
    def save():
        (a.output/'summary.json').write_text(json.dumps(record, indent=2)+'\n')
    save(); started = time.monotonic()
    try:
        with (a.output/'stock.log').open('x') as log:
            child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        result = analyze(a.output/'reports', child.returncode, top, True, ports, 'deep')
        (a.output/'strict_analysis.json').write_text(json.dumps(result, indent=2)+'\n')
        held = all(sha(Path(x)) == h for x,h in {**inputs, **rules}.items())
        record.update(returncode=child.returncode, inputs_rules_held=held,
                      strict_checks=result['checks'],
                      status='passed strict native stock macro LVS' if held and result['status'].startswith('passed') else 'failed strict native stock macro LVS')
    except Exception as exc:
        record.update(status='failed strict LVS or analysis', error=repr(exc))
        raise
    finally:
        record['wall_s'] = time.monotonic()-started; save()
    raise SystemExit(0 if record['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
