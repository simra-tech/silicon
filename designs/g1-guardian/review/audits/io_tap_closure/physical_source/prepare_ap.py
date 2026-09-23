#!/usr/bin/env python3
"""Authorized raw-geometry A/P derivative; electrical R remains separate."""
import argparse
import collections
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
AUDITS = HERE.parents[1]
sys.path.insert(0, str(AUDITS/'fullchip_reference_closure/physical_lvs/explicit_vss_interface'))
from prepare import parse, flattened, TOP
sys.path.insert(0, str(HERE.parent))
from audit_pinned_taps import number


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    source = bulk/'fullchip-current-digital-reference-20260923-r2/current_digital_explicit_vss.cdl'
    ownership = bulk/'io-tap-physical-ownership-20260923-r1/analysis.json'
    assert sha(source) == 'febefea51c08ee2432aac512b251aee990f4812dbaee59d9acdc879b18429e74'
    proof = json.loads(ownership.read_text())
    assert proof['status'] == 'failed one or more native ownership mappings'
    assert len(proof['failures']) == 5
    assert all(sha(Path(p)) == h for p,h in proof['inputs'].items())
    raw = source.read_bytes(); lines,cells = parse(raw); original,reached = flattened(cells)
    prefix = 'G1_VSS_DERIVATIVE__'
    used_original = {name[len(prefix):] for name in reached if name.startswith(prefix)}
    assert not {r['cell'].upper() for r in proof['failures']} & used_original
    geometries = {row['cell'].upper():row for row in proof['cells']}
    inputs = {str(p):sha(p) for p in (source,ownership,Path(__file__).resolve(),
        AUDITS/'fullchip_reference_closure/physical_lvs/explicit_vss_interface/prepare.py')}
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running authorized physical A/P source preparation',inputs=inputs)
    edits, ledger = {}, []
    try:
        for name in sorted(reached):
            if not name.startswith(prefix):
                continue
            original_name = name[len(prefix):]
            taps = [i for i in cells[name]['instances'] if i['model'].upper() in ('PTAP1','NTAP1')]
            if not taps:
                continue
            geometry = geometries[original_name]
            assert all(p['passed'] for p in geometry['polygon_mapping'])
            for inst in taps:
                match, = [row for row in geometry['taps'] if row['source']['instance'].upper() == inst['name'].upper()]
                assert match['source']['model'].upper() == inst['model'].upper()
                assert inst['nodes'] == [match['source']['terminals'][0],'G1_EXPLICIT_SUBSTRATE_VSS']
                assert match['owned_polygon_count'] > 0
                assert len(inst['record']['indices']) == 1
                index, = inst['record']['indices']; old = lines[index]
                area, perimeter = Decimal(match['area_um2']),Decimal(match['perimeter_um'])
                assert area > 0 and perimeter > 0
                new, ac = re.subn(r'\bA=\S+', 'A='+format(area,'f')+'p', old, flags=re.I)
                new, pc = re.subn(r'\b(?:P|PERIM)=\S+', 'P='+format(perimeter,'f')+'u', new, flags=re.I)
                assert ac == pc == 1 and new != old
                edits[index] = new
                with localcontext() as ctx:
                    ctx.prec = 50
                    one_p = Decimal(980)/(area+perimeter)
                    two_p = Decimal(980)/(area+2*perimeter)
                ledger.append(dict(cell=name,original_native_cell=original_name,instance=inst['name'],
                    original_record=old,derived_record=new,source_line=index+1,
                    A_um2=str(area),P_um=str(perimeter),owned_geometry=match,
                    original_SPI_R=match['original_electrical']['parameters']['R'],
                    conditional_single_perimeter_R_ohm=str(one_p),conditional_double_perimeter_R_ohm=str(two_p),
                    executable_R_selection='not run; not chosen to force LVS'))
        changed = ''.join(edits.get(i,line) for i,line in enumerate(lines)).encode()
        restored_lines = changed.decode().splitlines(True)
        for row in ledger:
            index = row['source_line']-1
            assert restored_lines[index] == row['derived_record']
            restored_lines[index] = row['original_record']
        assert ''.join(restored_lines).encode() == raw
        _,aftercells = parse(changed); after,after_reached = flattened(aftercells)
        assert reached == after_reached and set(original) == set(after)
        assert cells[TOP]['pins'] == aftercells[TOP]['pins'] and len(cells[TOP]['pins']) == 22
        differences = []
        totals = collections.defaultdict(lambda: [Decimal(0),Decimal(0),0])
        for path,before in original.items():
            now = after[path]
            assert before['nodes'] == now['nodes'] and before['model'] == now['model']
            if before['model'] not in ('PTAP1','NTAP1'):
                assert before == now
                continue
            assert before['params'] != now['params']
            params = dict(t.split('=',1) for t in now['params'])
            assert set(params) == {'A','P'}
            A, P = number(params['A'])*Decimal('1e12'),number(params['P'])*Decimal('1e6')
            key = tuple(now['nodes']); totals[key][0] += A; totals[key][1] += P; totals[key][2] += 1
            differences.append(dict(path=path,original=before,derived=now))
        assert len(differences) == 386
        adapted = []
        prefix_ledger = []
        for line in changed.decode().splitlines(True):
            if re.match(r'^\s*X\S+\s+\S+\s+\S+\s+[pn]tap1\b',line,re.I):
                old_name = line.split()[0]; new_name = 'R_G1_TAP_SYNTAX_'+old_name
                prefix_ledger.append((old_name,new_name)); line = line.replace(old_name,new_name,1)
            adapted.append(line)
        adapted = ''.join(adapted).encode(); inverse = adapted
        for old_name,new_name in prefix_ledger:
            inverse = inverse.replace((new_name+' ').encode(),(old_name+' ').encode())
        assert inverse == changed
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        source_out = a.output/'physical_taps.cdl'; source_out.write_bytes(changed)
        adapter_out = a.output/'physical_taps_reader.cdl'; adapter_out.write_bytes(adapted)
        result.update(status='passed reversible raw-geometry physical A/P derivative; strict validation pending',
            source_sha256=sha(source_out),reader_sha256=sha(adapter_out),local_tap_records=len(ledger),reachable_taps=386,
            changed_records=ledger,flattened_differences=differences,
            independent_geometric_totals=[dict(nodes=list(k),A_um2=str(v[0]),P_um=str(v[1]),instances=v[2]) for k,v in totals.items()],
            reverse_source_exact=True,non_tap_graph_and_parameters_held=True,external22pins_held=True,
            preserved_unused_failures=proof['failures'],unused_failure_applicability='not applicable to current source reachability',
            physical_instanced_XOR='not run',geometry_negative_controls='not run',strict_fullchip_LVS='not run',
            electrical_R_variant='not run',power_sequencing_ESD='not run',model_rule_changes='not applicable',adoption='not run')
    except Exception as exc:
        result.update(status='failed physical A/P source preparation',error=repr(exc))
        raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
