#!/usr/bin/env python3
"""One isolated stacked64 stock gate with strict source and saved-view bindings."""
import collections
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
import pya
from run_stock_native_prototypes import sha, output_bytes, strict_xref


def main():
    here = Path(__file__).resolve().parent
    base = Path('/work/build/scratch/sense-fullmain-20260922-r1')
    reference = Path('/work/build/scratch/sense-fullmain-reference-20260922-r1')
    out = Path('/work/build/scratch/sense-fullmain-stock-20260922-r1')
    assert not out.exists() and os.sched_getaffinity(0) == {7} and pya.__version__ == '0.30.9'
    gds = base / 'g1_ota_main_physical.gds'
    cdl = reference / 'g1_ota_main_physical.cdl'
    source = here.parents[1] / 'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    m = json.loads((base / 'manifest.json').read_text())
    ref = json.loads((reference / 'manifest.json').read_text())
    assert ref['status'] == 'passed complete saved-polygon and exact source reference gate'
    assert sha(source) == ref['source_sha256'] == m['source_sha256'] == 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    assert sha(gds) == ref['GDS_sha256'] == m['GDS_sha256'] == '3d60787621c5f23128643c640cdac7d8ec9d7185e921ddc9b2760037f69dd108'
    assert sha(cdl) == ref['CDL_sha256'] and sha(base / 'manifest.json') == ref['manifest_sha256']
    bindings = {p: sha(p) for p in (source, gds, cdl, base / 'manifest.json', reference / 'manifest.json')}
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    decks = {str(p.relative_to(pdk)): sha(p) for kind in ('drc', 'lvs') for p in (pdk / ('libs.tech/klayout/tech/' + kind)).rglob('*') if p.is_file() and p.suffix in ('.drc', '.lvs', '.lylvs', '.rb', '.json', '.py')}
    out.mkdir()
    result = dict(status='running', source_sha256=sha(source), GDS_sha256=sha(gds), CDL_sha256=sha(cdl),
                  reference_manifest_sha256=sha(reference / 'manifest.json'), script_sha256=sha(Path(__file__)),
                  contract_sha256=sha(here / 'FULLMAIN_CONTRACT_20260922.md'), stock_decks=decks, checks=[],
                  density='not run', antenna='not run', PEX='not run', full_main='not run',
                  stock_junction_applicability='not run', seed='not applicable')
    stopped = False
    for kind in ('drc', 'lvs'):
        if stopped:
            result['checks'].append(dict(kind=kind, status='not run', reason='earlier stock gate failed'))
            continue
        folder = out / kind
        cmd = ['python3', str(pdk / ('libs.tech/klayout/tech/' + kind + '/run_' + kind + '.py')), '--run_mode=deep', '--topcell=g1_ota_main_physical', '--run_dir=' + str(folder)]
        cmd += ['--path=' + str(gds), '--no_density', '--mp=1'] if kind == 'drc' else ['--layout=' + str(gds), '--netlist=' + str(cdl)]
        log = out / (kind + '.log')
        start = time.monotonic()
        with log.open('x') as handle:
            proc = subprocess.run(['timeout', '--kill-after=5', '180'] + cmd, stdout=handle, stderr=subprocess.STDOUT)
        row = dict(kind=kind, status='failed', command=cmd, returncode=proc.returncode, wall_s=time.monotonic() - start, log_sha256=sha(log))
        if kind == 'drc':
            reports = []
            for path in sorted(folder.rglob('*.lyrdb')):
                categories = collections.Counter(item.findtext('category') for item in ET.parse(path).findall('.//items/item'))
                reports.append(dict(path=str(path.relative_to(out)), sha256=sha(path), markers=sum(categories.values()), categories=dict(categories)))
            row['reports'] = reports
            passed = bool(reports) and all(r['markers'] == 0 for r in reports)
        else:
            logs = log.read_text(errors='replace') + '\n' + '\n'.join(p.read_text(errors='replace') for p in folder.rglob('*.log'))
            xrefs = [dict(path=str(p.relative_to(out)), sha256=sha(p), xref=strict_xref(p)) for p in sorted(folder.rglob('*.lvsdb'))]
            row['databases'] = xrefs
            passed = 'Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs and bool(xrefs) and all(r['xref']['status'] == 'passed' for r in xrefs)
        row['output_bytes'] = output_bytes(out)
        if proc.returncode == 0 and passed and row['output_bytes'] < 50 * 2**20:
            row['status'] = 'passed'
        stopped = row['status'] != 'passed'
        result['checks'].append(row)
        (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    result['inputs_unchanged'] = all(sha(p) == h for p, h in bindings.items())
    result['stock_decks_unchanged'] = all(sha(pdk / p) == h for p, h in decks.items())
    result['status'] = 'passed' if result['inputs_unchanged'] and result['stock_decks_unchanged'] and all(r['status'] == 'passed' for r in result['checks']) else 'failed'
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'stock_decks'}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
