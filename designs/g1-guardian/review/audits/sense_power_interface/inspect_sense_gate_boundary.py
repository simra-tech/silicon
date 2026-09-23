#!/usr/bin/env python3
"""Read-only evidence separating literal gate-contact geometry from model XGW."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

IMAGE = 'sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'


def digest(data): return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--container', required=True)
    parser.add_argument('--stock-summary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    assert re.fullmatch('[0-9a-f]{12,64}', args.container)
    info = json.loads(subprocess.check_output(['podman', 'inspect', args.container]))[0]
    assert info['Image'] in (IMAGE, IMAGE.split(':')[1])
    stock = json.loads(args.stock_summary.read_text())
    assert stock['status'] == 'passed scoped main and maximal DRC'
    def read(name):
        raw = subprocess.check_output(['podman', 'cp', args.container+':/foss/pdks/ihp-sg13g2/'+name, '-'])
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            members = [m for m in archive.getmembers() if m.isfile()]; assert len(members) == 1
            return archive.extractfile(members[0]).read()
    assert read('COMMIT').decode().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    paths = ['libs.tech/klayout/tech/drc/rule_decks/feol/5_14_cont.drc',
             'libs.tech/klayout/tech/drc/rule_decks/sg13g2_tech_default.json',
             'libs.tech/klayout/python/sg13g2_pycell_lib/sg13g2_tech_mod.json',
             'libs.tech/verilog-a/psp103/PSP103_module.include',
             'libs.tech/ngspice/models/sg13g2_moshv_mod.lib',
             'libs.tech/ngspice/models/sg13g2_moshv_mod_mismatch.lib',
             'libs.tech/ngspice/models/sg13g2_moshv_parm.lib']
    records = {}; texts = {}
    for path in paths:
        raw = read(path); texts[path] = raw.decode()
        if path in stock['stock_rule_hashes']: assert digest(raw) == stock['stock_rule_hashes'][path]
        records[path] = dict(sha256=digest(raw), bytes=len(raw),
                             completed_stock_hash_exact=path in stock['stock_rule_hashes'])
    values = []
    def walk(obj, path):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ('Cnt_a', 'Cnt_e'): values.append(dict(path=path+'/'+key, value=value))
                walk(value, path+'/'+key)
        elif isinstance(obj, list):
            for index, value in enumerate(obj): walk(value, path+'/'+str(index))
    for path in paths[1:3]: walk(json.loads(texts[path]), path)
    assert values and all(float(r['value']) == (.16 if r['path'].endswith('Cnt_a') else .14) for r in values)
    models = '\n'.join(texts[p] for p in paths[4:])
    assert not re.search(r'\bxgw\s*=', models, re.I), 'Unexpected wrapper/model XGW override'
    module = texts[paths[3]]
    assert re.search(r'IPRnb\(XGW\s*,1\.0e-7', module)
    excerpts = {}
    for path, text in texts.items():
        pattern = r'Cnt\.a|Cnt\.e|cnt_e_l|cnt_e_value' if path == paths[0] else r'\bXGW\b|\bngcon\s*='
        excerpts[path] = [dict(line=index, text=line) for index, line in enumerate(text.splitlines(), 1) if re.search(pattern, line, re.I)]
    result = dict(status='passed read-only boundary inventory; model applicability unresolved',
                  image_config_sha256=IMAGE, PDK_commit='84374023ee8b4b126bebbba67fcbada0a9c0ff0b',
                  stock_summary_sha256=digest(args.stock_summary.read_bytes()), script_sha256=digest(Path(__file__).read_bytes()),
                  files=records, rule_values=values, excerpts=excerpts,
                  literal_geometry_um=dict(contact_width=.16, minimum_contact_edge_to_Active=.14,
                                           minimum_contact_center_to_Active=.22,
                                           prototype_contact_edge_to_Active=.25,
                                           prototype_contact_center_to_Active=.33, model_XGW_default=.10),
                  wrapper_or_model_XGW_override_present=False,
                  interpretation='A literal 0.10um drawn gate-contact edge or center distance cannot satisfy Cnt.e. This does not prove that an effective/calibrated compact-model XGW is intended as that literal drawn distance; that convention and RGO ownership remain unqualified.',
                  no_container_process_executed=True, no_source_or_geometry_modified=True,
                  not_run=['Model-card change', 'Geometry relocation', 'Full gate-resistance applicability',
                           'Electrical sensitivity or acceptance waiver'])
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('files', 'excerpts')}, indent=2))


if __name__ == '__main__': main()
