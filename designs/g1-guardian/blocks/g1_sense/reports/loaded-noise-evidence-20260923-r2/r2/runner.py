#!/usr/bin/env python3
"""Source-held, frozen-DC joint SENSE/BGR/TRIP AC/noise diagnostic; no PEX claim."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import numpy as np

SIM = Path(__file__).resolve().parent
TRIP = SIM.parents[1] / 'g1_trip/sim'
sys.path.insert(0, str(TRIP))
from run_bgr_substitution_draw_audit import read_group
from run_bias_observation_probe import quiet_values
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory

REFERENCE = 'joint586-mm-tranqual-20260922-a-enabled'
IMAGE = 'sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'
MANIFEST = 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
SOURCE = 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def table(path, header):
    lines = path.read_text().splitlines()
    assert lines[0].split() == header, 'Exact vector/header identity failed'
    values = np.array([list(map(float, line.split())) for line in lines[1:] if line.strip()])
    assert values.ndim == 2 and values.shape[1] == len(header)
    assert np.isfinite(values).all() and np.all(np.diff(values[:, 0]) > 0)
    return values

def integrate(frequency, psd, lower, upper, duration=0., order=16):
    """Integrate piecewise log-linear positive PSD, optional normalized boxcar."""
    f, s = np.asarray(frequency), np.asarray(psd)
    assert len(f) == len(s) and np.all(f > 0) and np.all(np.diff(f) > 0)
    assert np.all(s > 0) and np.isfinite(s).all()
    assert f[0] <= lower < upper <= f[-1] and duration >= 0
    nodes, weights = np.polynomial.legendre.leggauss(order)
    total = 0.
    for a, b, p, q in zip(f[:-1], f[1:], s[:-1], s[1:]):
        lo, hi = max(a, lower), min(b, upper)
        if lo >= hi:
            continue
        x = (hi-lo)*.5*nodes+(hi+lo)*.5
        value = p*np.exp(np.log(q/p)*np.log(x/a)/np.log(b/a))
        total += (hi-lo)*.5*float(weights @ (value*np.sinc(x*duration)**2))
    assert math.isfinite(total) and total > 0
    return total

def tests():
    f = np.geomspace(1., 1e7, 701)
    results = {}
    for name, psd, expected in [('white', np.ones_like(f)*4e-18, 4e-18*(1e7-1)),
                                ('flicker', 3e-12/f, 3e-12*math.log(1e7))]:
        measured = integrate(f, psd, 1, 1e7)
        assert abs(measured/expected-1) < 1e-12
        results[name] = dict(expected_V2=expected, observed_V2=measured)
    # Independent closed-form integral of sinc(pi*f*T)^2 using scipy's Si.
    from scipy.special import sici
    duration = 200e-9
    def primitive(freq):
        u = math.pi*duration*freq
        return (sici(2*u)[0]-math.sin(u)**2/u)/(math.pi*duration)
    exact = 4e-18*(primitive(1e7)-primitive(1))
    observed = integrate(f, np.ones_like(f)*4e-18, 1, 1e7, duration)
    assert abs(observed/exact-1) < 1e-12
    results['boxcar'] = dict(expected_V2=exact, observed_V2=observed)
    for invalid in [np.zeros_like(f), -np.ones_like(f), np.full_like(f, np.nan)]:
        try:
            integrate(f, invalid, 1, 1e7)
        except AssertionError:
            pass
        else:
            raise AssertionError('Invalid PSD was accepted')
    # ASD must be squared: doubling ASD must quadruple variance.
    assert integrate(f, np.ones_like(f)*16e-18, 1, 1e7) == 4*integrate(f, np.ones_like(f)*4e-18, 1, 1e7)
    results['negative_zero_nonfinite_rejection_and_ASD_units'] = 'passed'
    with tempfile.TemporaryDirectory(prefix='noise-header-control-') as folder:
        path = Path(folder)/'table.dat'
        path.write_text('frequency a b\n1 2 3\n2 4 5\n')
        assert table(path, ['frequency','a','b']).shape == (2,3)
        try:
            table(path, ['frequency','b','a'])
        except AssertionError:
            results['swapped_header_rejected'] = True
        else:
            raise AssertionError('Swapped columns accepted')
    return results

def group_commands(groups, when):
    return ''.join('echo '+name+'_'+when+'_BEGIN\n'+''.join('print '+q+'\n' for q in queries)+
                   'echo '+name+'_'+when+'_END\n' for name, queries in groups.items())

def build_deck(original, out, groups):
    first, rest = original.split('tran 0.2n 1.02u 0 0.2n\n', 1)
    line, = re.findall(r'^Vsh .+$', first, re.M)
    assert line == 'Vsh shp 0 dc 0.025000000000000001'
    first = first.replace(line, line+' ac 1')
    assert first.replace(line+' ac 1', line)+'tran 0.2n 1.02u 0 0.2n\n'+rest == original
    # Preserve original OP, full 11512 before-query order and printed precision.
    suffix = 'set numdgt=17\nset wr_singlescale\nset wr_vecnames\nunset sqrnoise\n'
    suffix += 'ac dec 100 1 10meg\nlet ac_re=real(v(isense))\nlet ac_im=imag(v(isense))\n'
    suffix += 'wrdata '+str(out/'ac.dat')+' ac_re ac_im\n'
    suffix += 'noise v(isense) Vsh dec 100 1 10meg\nsetplot noise1\n'
    suffix += 'wrdata '+str(out/'noise.dat')+' onoise_spectrum inoise_spectrum\n'
    suffix += 'setplot noise2\nprint onoise_total inoise_total\nsetplot op1\nset numdgt=15\n'
    suffix += group_commands(groups, 'AFTER')
    suffix += 'echo LOADED_NOISE_END\nquit 0\n.endc\n.end\n'
    return first+suffix

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    p.add_argument('--test-only', action='store_true')
    p.add_argument('--prepare-only', action='store_true')
    args = p.parse_args()
    control = tests()
    if args.test_only:
        print(json.dumps(control, indent=2)); return
    assert args.output and not args.output.exists()
    if not args.prepare_only:
        assert os.sched_getaffinity(0) == {1}
    ref = TRIP/'qualification'/REFERENCE
    prep = json.loads((ref/'preparation.json').read_text())
    baseline, = json.loads((ref/'summary.json').read_text())
    assert baseline['parameter_wave_contract_status'] == 'passed'
    expected = baseline['phases'][0]['parameters_before']
    assert len(expected) == 11512 and sha(ref/'sense.spice') == SOURCE
    assert all(sha(ref/n) == value for n, value in prep['source_hashes'].items())
    original = (ref/'population_transient.cir').read_text()
    assert sha(ref/'population_transient.cir') == prep['deck_sha256']
    out = args.output
    out.mkdir(parents=True)
    deck = build_deck(original, out, prep['groups'])
    (out/'noise.cir').write_text(deck)
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    contract = dict(status='prepared', reference_run=REFERENCE, source_hashes=prep['source_hashes'],
        reference_summary_sha256=sha(ref/'summary.json'), reference_deck_sha256=sha(ref/'population_transient.cir'),
        deck_sha256=sha(out/'noise.cir'), controls=control,
        scope='Frozen-DC seed73001 TT25C3.3V, BGR586+SENSEgm4+fullTRIP loaded noise. ClockDC0, shunt25mV/negative0: input signal is one-sided differential, common-mode also moves by half. No periodic/cyclostationary noise, fullPEX, corner envelope or allocated noise acceptance.',
        window_scope='20ns is observed decision latency, NOT averaging aperture. Report instantaneous finite-band variance and separately assumed normalized boxcar20ns/200ns/1us sensitivities; no sampler/filter equivalence.',
        prospective_gates=dict(full11512_exact=True, legacy27_exact=True, quiet9OP_exact=True,
            spectrum_rows=701, spectra='finite positive ASD V/sqrt(Hz)', frequency='1Hz..10MHz strictly increasing',
            noise_gain_to_AC_relative_error_max=1e-6, integration_8_vs_16_relative_error_max=1e-6,
            watchdog_s=120, no_absolute_noise_limit=True))
    (out/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    if args.prepare_only:
        print(json.dumps(contract, indent=2)); return
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id_observed_by_host=MANIFEST, pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'], text=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, solver='sparse')
    (out/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,
        OCI_manifest_digest=MANIFEST, OCI_config_digest_checked_by_host_flow=IMAGE,
        identity_note='Legacy electrical image field is OCI manifest, not config. Pinned host flow independently checks config; both identify the same imported image.',
        runtime_exact=runtime == prep['expected_runtime_identity']), indent=2)+'\n')
    assert runtime == prep['expected_runtime_identity']
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice','-b',str(out/'noise.cir')], stream, out/'run.json',120,cwd=TRIP,interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?i)^error|timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',line)]
    result = dict(status='failed', runtime=state, errors=errors,warnings=warning_inventory(log),scope=contract['scope'],window_scope=contract['window_scope'])
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors and 'LOADED_NOISE_END' in log
        before = read_group(log,'NON_BGR_BEFORE',prep['groups']['NON_BGR'])+read_group(log,'BGR_BEFORE',prep['groups']['BGR'])
        after = read_group(log,'NON_BGR_AFTER',prep['groups']['NON_BGR'])+read_group(log,'BGR_AFTER',prep['groups']['BGR'])
        assert before == after == expected and len(before)==11512
        legacy = read_group(log,'LEGACY27_AFTER',prep['groups']['LEGACY27'])
        assert legacy == [[q,dict(expected)[q]] for q in prep['groups']['LEGACY27']]
        op = quiet_values(log)
        assert op == baseline['phases'][0]['quiet_op_V']
        result['parameter_OP_provenance'] = dict(full11512_exact=True,legacy27_exact=True,quiet9OP_exact=True,quiet_op_V=op)
        ac=table(out/'ac.dat',['frequency','ac_re','ac_im'])
        noise=table(out/'noise.dat',['frequency','onoise_spectrum','inoise_spectrum'])
        assert ac.shape==noise.shape==(701,3) and np.array_equal(ac[:,0],noise[:,0])
        assert abs(noise[0,0]-1)<1e-12 and abs(noise[-1,0]/1e7-1)<1e-12 and np.all(noise[:,1:]>0)
        gain=np.hypot(ac[:,1],ac[:,2]); assert np.all(gain>0)
        norm=float(np.max(np.abs(noise[:,1]/noise[:,2]/gain-1)))
        result['AC_ASD_normalization_max_relative_error']=norm
        assert norm <= 1e-6
        result['gain_1Hz_V_per_V']=float(gain[0])
        bands=[]
        for upper in [1e3,1e5,2e6,1e7]:
            for duration in [0.,20e-9,200e-9,1e-6]:
                powers=[integrate(noise[:,0],noise[:,c]**2,1,upper,duration) for c in [1,2]]
                coarse=[integrate(noise[:,0],noise[:,c]**2,1,upper,duration,8) for c in [1,2]]
                err=max(abs(a/b-1) for a,b in zip(coarse,powers)); assert err<=1e-6
                bands.append(dict(lower_Hz=1,upper_Hz=upper,assumed_boxcar_s=duration,
                    output_rms_V=math.sqrt(powers[0]),input_stimulus_referred_rms_V=math.sqrt(powers[1]),
                    quadrature_8_vs_16_relative_error=err))
        result['bands']=bands
        result['ngspice_printed_totals']={k:float(v) for k,v in re.findall(r'^(onoise_total|inoise_total)\s*=\s*(\S+)',log,re.M)}
        result['status']='passed conditional frozen-DC loaded AC/noise audit; no allocated electrical acceptance'
        result['not_run']=['Cyclostationary comparator noise','Physical PEX/model-plane composition','Out-of-band noise bound','Noise corner/mismatch population','Noise acceptance allocation']
    except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:
        result['analysis_error']=repr(error)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)

if __name__=='__main__':
    main()
