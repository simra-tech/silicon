#!/usr/bin/env python3
"""Read-only strict-xref attribution of stock junction fields to source nodes."""
import hashlib
import json
from pathlib import Path
import re
import pya
from audit_junction_defaults import default


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    here = Path(__file__).resolve().parent
    stock = here / 'source-faithful-buffer-stock-20260922-r1'
    output = here / 'source-faithful-buffer-stock-junctions-20260922-r1.json'
    source = here.parents[1] / 'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert not output.exists() and pya.__version__ == '0.30.9'
    assert sha(source) == 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    summary = json.loads((stock / 'summary.json').read_text())
    assert summary['status'] == 'passed'
    block = re.search(r'(?ms)^\.subckt g1_ota .*?^\.ends', source.read_text()).group(0)
    specs = {line.split()[0][1:].upper(): line for line in block.splitlines() if line.startswith(('XM', 'XMB', 'XMT'))}
    assert len(specs) == 19
    path = stock / 'lvs/g1_ota_source_faithful.lvsdb'
    original_hash = sha(path)
    db = pya.LayoutVsSchematic()
    db.read(str(path))
    xref = db.xref()
    circuits = list(xref.each_circuit_pair())
    assert len(circuits) == 1 and circuits[0].status() == pya.NetlistCrossReference.Match
    cp = circuits[0]
    netmap = {}
    for pair in xref.each_net_pair(cp):
        assert pair.status() == pya.NetlistCrossReference.Match
        netmap[pair.first().name] = pair.second().name.lower()
    rows = []
    for pair in xref.each_device_pair(cp):
        assert pair.status() == pya.NetlistCrossReference.Match
        name = pair.second().name.upper()
        if name not in specs:
            assert name in ('RZ', 'CC')
            continue
        line = specs[name]
        words = line.split()
        params = dict(re.findall(r'(\w+)=([^\s]+)', line))
        expected = default(float(params['w'].rstrip('u')), int(params['ng']))
        device = pair.first()
        terminals = {term.name.upper(): netmap[device.net_for_terminal(term.id).name]
                     for term in device.device_class().terminal_definitions()}
        assert terminals['G'] == words[2] and terminals['B'] == words[4]
        assert {terminals['D'], terminals['S']} == {words[1], words[3]}
        values = {name: device.parameter(name) for name in ('AS', 'AD', 'PS', 'PD')}
        by_net = {terminals['S']: (values['AS'], values['PS']), terminals['D']: (values['AD'], values['PD'])}
        actual = dict(as_um2=by_net[words[3]][0], ps_um=by_net[words[3]][1],
                      ad_um2=by_net[words[1]][0], pd_um=by_net[words[1]][1])
        delta = {k: actual[k] - expected[k] for k in expected}
        rows.append(dict(source_name=name, source_line=line, extracted_terminals_source_names=terminals,
                         stock_fields=values, source_node_actual=actual, source_default=expected,
                         delta=delta, status='passed' if all(abs(v) < 1e-8 for v in delta.values()) else 'failed'))
    assert len(rows) == 19 and len({r['source_name'] for r in rows}) == 19
    assert sha(path) == original_hash and sha(source) == summary['source_sha256']
    counts = {status: sum(r['status'] == status for r in rows) for status in ('passed', 'failed')}
    result = dict(status='passed complete read-only attribution audit', per_node_junction_status='failed' if counts['failed'] else 'passed',
                  counts=counts, rows=rows, script_sha256=sha(Path(__file__)), stock_database_sha256=original_hash,
                  stock_summary_sha256=sha(stock / 'summary.json'), source_sha256=sha(source),
                  model_applicability='not run; intrinsic junction equations/internal bias not established by geometry bookkeeping',
                  modifications='none; source, model, decks, database unchanged')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
