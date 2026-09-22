#!/usr/bin/env python3
"""Bounded unchanged stock checks with explicit missing/timed-out failure."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[6]
    base = root/'build/scratch/bgr-mos-contact-prototypes-20260922-r2'
    assert json.loads((base/'revision-comparison.json').read_text())['status'] == 'passed'
    manifest = json.loads((base/'manifest.json').read_text())
    out = root/'build/scratch/bgr-mos-stock-20260922-r1'
    out.mkdir(parents=True, exist_ok=False)
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    deck_files = sorted(p for kind in ['drc','lvs'] for p in (pdk/('libs.tech/klayout/tech/'+kind)).rglob('*')
                        if p.is_file() and p.suffix in ['.drc','.lylvs','.rb','.json','.py'])
    deck_hashes = {str(p.relative_to(pdk)): sha(p) for p in deck_files}
    result = dict(status='running', prototype_manifest_sha256=sha(base/'manifest.json'),
                  contract_sha256=sha(Path(__file__).with_name('STOCK_PROTOTYPE_CONTRACT_20260922.md')),
                  script_sha256=sha(Path(__file__)), checks=[], density='not run', antenna='not run',
                  random_seed='not applicable', full_macro_qualification='not run', stock_deck_hashes=deck_hashes)
    for item in manifest['prototypes']:
        name = item['name']
        assert sha(base/(name+'.gds')) == item['gds_sha256']
        assert sha(base/(name+'.cdl')) == item['cdl_sha256']
        for kind in (['drc','lvs'] if name in ['bgr_mos_proto_00','bgr_mos_proto_03'] else ['drc']):
            runner = pdk/('libs.tech/klayout/tech/'+kind+'/run_'+kind+'.py')
            run_dir = out/(name+'-'+kind)
            args = ['python3', str(runner), '--run_mode=deep', '--topcell='+name, '--run_dir='+str(run_dir)]
            if kind == 'drc':
                args += ['--path='+str(base/(name+'.gds')), '--no_density', '--mp=1']
            else:
                args += ['--layout='+str(base/(name+'.gds')), '--netlist='+str(base/(name+'.cdl'))]
            started = time.monotonic()
            log = out/(name+'-'+kind+'.log')
            with log.open('w') as handle:
                proc = subprocess.run(['timeout','--kill-after=5','180']+args, stdout=handle, stderr=subprocess.STDOUT)
            entry = dict(name=name, kind=kind, command=args, wrapper_sha256=sha(runner),
                         returncode=proc.returncode, wall_s=time.monotonic()-started, log_sha256=sha(log))
            if kind == 'drc':
                reports = []
                for report in sorted(run_dir.rglob('*.lyrdb')):
                    tree = ET.parse(report)
                    reports.append(dict(path=str(report.relative_to(out)), sha256=sha(report),
                                        markers=len(tree.findall('.//items/item'))))
                entry['reports'] = reports
                entry['status'] = 'passed' if proc.returncode==0 and reports and all(r['markers']==0 for r in reports) else 'failed'
            else:
                logs = '\n'.join(p.read_text(errors='replace') for p in run_dir.rglob('*.log'))
                passed = 'Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
                entry['status'] = 'passed' if proc.returncode==0 and passed else 'failed'
                entry['explicit_match_signature'] = passed
            result['checks'].append(entry)
            (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
            print(json.dumps(entry), flush=True)
    result['status'] = 'passed' if all(x['status']=='passed' for x in result['checks']) else 'failed'
    result['stock_decks_unchanged'] = all(sha(pdk/p)==digest for p,digest in deck_hashes.items())
    assert result['stock_decks_unchanged']
    (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], completed=len(result['checks']))))


if __name__ == '__main__':
    main()
