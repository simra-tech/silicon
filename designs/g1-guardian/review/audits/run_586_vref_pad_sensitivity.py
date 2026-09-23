#!/usr/bin/env python3
"""Frozen586 BGR / stock AnalogPad DC and declared fixture leakage sensitivity.

Legacy block C-only parasitics and whole-tree route-R sensitivity are explicit,
not the new native physical extraction. No mismatch or physical leakage bound.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BGR = ROOT/'designs/g1-guardian/blocks/g1_bgr/sim/qualification'
AUD = ROOT/'designs/g1-guardian/review/audits'
sys.path.insert(0, str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
from simulation_errors import solver_failure


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    assert not out.exists() and len(os.sched_getaffinity(0)) == 1
    ref = BGR/'runs/bgr_loop24q4_hv06_nominal_20260922_r1'
    qual = json.loads((BGR/'runs/bgr_one_draw_20260922_r1/manifest.json').read_text())
    assert qual['status'] == 'passed harness qualification'
    source = ref/'pex_nominal.spice'; original = (ref/'nominal.cir').read_text()
    assert sha(source) == qual['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    assert sha(ref/'nominal.cir') == qual['nominal_deck_sha256']
    assert sha(ref/'.spiceinit') == qual['init_sha256']
    assert sha(ref/'nominal.dat') == qual['nominal_wave_sha256']
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip() == qual['runtime']['pdk_commit']
    for key, folder, pattern in [('model_sha256','models','*.lib'),('osdi_sha256','osdi','*.osdi')]:
        assert qual['runtime'][key] == {str(f.relative_to(pd)): sha(f) for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    assert subprocess.check_output(['ngspice','--version'], text=True) == qual['ngspice']
    parameters = qual['parameters']; assert len(parameters) == 2842
    assert re.findall(r'^print (.+)$', original, re.M) == parameters+parameters
    oldpad = AUD/'vref-pad-loading-20260922-r2'
    oldprov = json.loads((oldpad/'provenance.json').read_text())
    pad = pd/'libs.ref/sg13g2_io/spice/sg13g2_io.spi'
    assert sha(pad) == oldprov['inputs']['libs.ref/sg13g2_io/spice/sg13g2_io.spi']
    template = (oldpad/'pad_R1_open/fixture.cir').read_text().split('.control')[0]
    start = template.index('.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib')
    pad_network = template[start:]
    assert 'Rroute vref route_end 613.3424975252701\n' in pad_network
    assert pad_network.count('sg13g2_IOPadAnalog') == 1
    assert original.count('.control\n') == 1 and original.count('wrdata nominal.dat ') == 1
    specs = [('baseline', None, None), ('pad_open', 0., None)] + [
        (f'leak_{value:+g}A', value, None) for value in (-1e-10,1e-10,-1e-9,1e-9,-1e-8,1e-8)] + [('input_10Mohm',0.,1e7)]
    out.mkdir(); shutil.copyfile(__file__,out/'source.py')
    record = dict(status='running', scope=__doc__, runtime=qual['runtime'], ngspice=qual['ngspice'],
        source_sha256=sha(source), original_deck_sha256=sha(ref/'nominal.cir'),
        original_wave_sha256=sha(ref/'nominal.dat'), spiceinit_sha256=sha(ref/'.spiceinit'),
        pad_library_sha256=sha(pad), old_pad_fixture_sha256=sha(oldpad/'pad_R1_open/fixture.cir'),
        old_pad_provenance_sha256=sha(oldpad/'provenance.json'), script_sha256=sha(Path(__file__)),
        cases=[], planned_cases=[n for n,_,_ in specs], watchdog_s_per_leaf=120,
        leakage_definition='Positive current sinks from external pad to ideal ground; negative injects. Assumed deterministic sensitivities, not physical package distributions or rated limits.',
        not_run=['new native physical RC/fill qualification','real downstream SENSE/T2F load',
                 'startup/stability/currentIR/EM','process/mismatch ensemble','physical leakage measurements'],
        not_applicable=['mismatch seed distribution; mismatch disabled'])
    def save(): (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    save(); baseline_values = None; baseline_wave = None; open_wave = None
    for name, leakage, resistance in specs:
        leaf = out/name; leaf.mkdir()
        shutil.copyfile(source,leaf/'pex_nominal.spice'); shutil.copyfile(ref/'.spiceinit',leaf/'.spiceinit')
        deck = original
        if leakage is not None:
            addition = pad_network
            if leakage: addition += f'Ifixture pad 0 {leakage:.17g}\n'
            if resistance: addition += f'Rinstrument pad 0 {resistance:.17g}\n'
            deck = deck.replace('.control\n', addition+'.control\n')
            line, = re.findall(r'^wrdata nominal.dat .+$', deck, re.M)
            deck = deck.replace(line+'\n', line+' v(padres) v(pad) i(vmeasure) i(vdigital)\n')
            # Literal inverse verifies only the named fixture/observation additions.
            inverse = deck.replace(addition+'.control\n','.control\n').replace(
                line+' v(padres) v(pad) i(vmeasure) i(vdigital)\n',line+'\n')
            assert inverse == original
        else: assert deck == original
        (leaf/'nominal.cir').write_text(deck)
        with (leaf/'run.log').open('x') as log:
            state = run_bounded(['ngspice','-b','nominal.cir'],log,leaf/'run.json',120,cwd=leaf,
                                env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),interval_s=1)
        text = (leaf/'run.log').read_text()
        row = dict(name=name, status='failed', leakage_A=leakage, resistance_ohm=resistance,
                   deck_sha256=sha(leaf/'nominal.cir'), runtime_state=state,
                   errors=solver_failure(text), warnings=[s for s in text.splitlines() if 'warning' in s.lower() or 'nan' in s.lower()])
        try:
            assert state['status']=='completed' and state['returncode']==0 and not row['errors']
            observed = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)',text,re.M)
            assert [v[0] for v in observed] == parameters+parameters
            assert all(np.isfinite(float(v[1])) for v in observed)
            before,after = observed[:2842],observed[2842:]; assert before == after
            if baseline_values is None: baseline_values = before
            assert before == baseline_values
            data = np.loadtxt(leaf/'nominal.dat',skiprows=1)
            assert data.shape == (34,12 if leakage is None else 16) and np.isfinite(data).all()
            assert np.array_equal(data[:,0],np.arange(-40,126,5))
            if leakage is None:
                assert sha(leaf/'nominal.dat') == sha(ref/'nominal.dat')
                baseline_wave = data
            elif name == 'pad_open': open_wave = data
            tc = float(np.ptp(data[:,1])/data[13,1]/165*1e6)
            row.update(status='passed numerical and parameter checks', parameters_before=before,
                parameters_after=after, waveform_sha256=sha(leaf/'nominal.dat'), rows=data.tolist(),
                TC_ppm_C=tc, TC_50ppm_status='passed' if tc<=50 else 'failed',
                max_abs_VREF_shift_from_no_pad_V=float(np.max(abs(data[:,1]-baseline_wave[:,1]))),
                loading_accuracy_acceptance='not run; no pad/fixture error allocation adopted')
            if open_wave is not None:
                row['max_abs_VREF_shift_from_open_pad_V'] = float(np.max(abs(data[:,1]-open_wave[:,1])))
        except (AssertionError, ValueError, OSError, IndexError) as exc:
            row['analysis_error'] = repr(exc)
        record['cases'].append(row); save()
        print(json.dumps({k:v for k,v in row.items() if k not in ('parameters_before','parameters_after','rows','warnings','runtime_state')}),flush=True)
        if row['status'].startswith('failed'):
            record.update(status='failed scoped campaign; later cases not run',unstarted=[n for n,_,_ in specs[len(record['cases']):]])
            save(); raise SystemExit(1)
    assert sha(source)==record['source_sha256'] and sha(pad)==record['pad_library_sha256']
    record['status']='passed nine scoped nominal pad/leakage numerical controls; full V17 incomplete';save()


if __name__=='__main__': main()
