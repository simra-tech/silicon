#!/usr/bin/env python3
"""Output-only representative device metadata at original nominal OP; no probes."""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from run_586_pvt import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2]/'g1_trip/sim'))
from result_directory import allocate_run
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory

DEVICES = ['n.xbgr.xm27.nsg13_hv_pmos', 'n.xbgr.xm29.nsg13_hv_nmos', 'n.xbgr.xr1.nr1', 'q.xbgr.xq56.qnpn13g2', 'r.xbgr.xq56.rsub', 'c.xbgr.xq56.csub']


def transform(original):
    marker = 'op\n'
    assert original.count(marker) == 1
    commands = '\n'.join('echo TERMINAL_METADATA_BEGIN_'+name+'\nshow '+name+'\necho TERMINAL_METADATA_END_'+name for name in DEVICES)+'\n'
    return original.replace(marker, marker+commands+'wrdata op_observation.dat v(vref) i(vload) i(vdd) v(vbe) v(dvbe) v(pbias) v(pcasc)\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    args = p.parse_args()
    base = HERE/'runs/bgr_one_draw_20260922_r1'
    qm = json.loads((base/'manifest.json').read_text())
    ref = base/'disabled'
    original = (ref/'nominal.cir').read_text()
    assert sha(ref/'pex_nominal.spice') == qm['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip() == qm['runtime']['pdk_commit']
    assert args.image_id == 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
    assert subprocess.check_output(['ngspice', '--version'], universal_newlines=True) == qm['ngspice']
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert qm['runtime'][key] == {str(f.relative_to(pd)): sha(f) for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    out = allocate_run(HERE.parent, args.run_id, relative_parent='qualification/runs')
    for name in ['pex_nominal.spice', '.spiceinit']:
        (out/name).write_bytes((ref/name).read_bytes())
    deck = transform(original)
    (out/'nominal.cir').write_text(deck)
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'declared_terminal_metadata_output.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), deck.splitlines(True), fromfile='qualifiedOriginal', tofile='outputOnlyMetadata')))
    provenance = dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), image_manifest=args.image_id, runtime=qm['runtime'], ngspice=qm['ngspice'], source_sha256=sha(out/'pex_nominal.spice'), deck_sha256=sha(out/'nominal.cir'),
                      reference_manifest_sha256=sha(base/'manifest.json'), original_deck_sha256=sha(ref/'nominal.cir'), original_wave_sha256=sha(ref/'nominal.dat'), devices=DEVICES,
                      scope='Output-only show representative model-instance metadata after unchanged first OP. All original2842beforeafter and full34pointDC waveform must equal originalnominal disabled control. No terminal-current equivalence inferred from intrinsic fields; wrapper external-current mapping requires separate analysis.')
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', 'nominal.cir'], stream, out/'run.json', 120, cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    result = dict(status='failed', runtime=state, warnings=warning_inventory(log), scope=provenance['scope'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0
        assert not re.search(r'^Error|no such device|no such vector|no such parameter|analysis aborted|Timestep too small', log, re.M)
        oldvalues = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', (ref/'run.log').read_text(), re.M)
        values = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log, re.M)
        assert values == oldvalues and [k for k, v in values] == qm['parameters']*2 and values[:2842] == values[2842:]
        result['full2842_before_after_original_exact'] = True
        result['original_dc_decoded_bytes_exact'] = (out/'nominal.dat').read_bytes() == (ref/'nominal.dat').read_bytes()
        result['original_dc_numeric_rows_exact'] = bool(np.array_equal(np.loadtxt(str(out/'nominal.dat'), skiprows=1), np.loadtxt(str(ref/'nominal.dat'), skiprows=1)))
        assert result['original_dc_decoded_bytes_exact'] and result['original_dc_numeric_rows_exact']
        result['representative_metadata'] = {}
        for name in DEVICES:
            section, = re.findall('^TERMINAL_METADATA_BEGIN_'+re.escape(name)+r'\n(.*?)^TERMINAL_METADATA_END_'+re.escape(name)+'$', log, re.M | re.S)
            assert section.strip()
            result['representative_metadata'][name] = section
        result['status'] = 'passed output-only parity; external terminal-current mapping not yet qualified'
    except (AssertionError, ValueError, OSError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['warnings', 'representative_metadata']}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
