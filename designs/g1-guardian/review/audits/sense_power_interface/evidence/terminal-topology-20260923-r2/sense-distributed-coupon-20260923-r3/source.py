#!/usr/bin/env python3
"""Prepare passive diagnostic coupons, never choose weights for a SENSE device."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(data): return hashlib.sha256(data).hexdigest()


def prepare(name, voltage_form='weighted'):
    """All cases use the same load and prescribed periodic source voltage."""
    direct = name == 'direct-zero-r'
    unequal = name == 'unequal-voltage'
    wrong = name == 'wrong-current-sign'
    distributed = name in ('distributed-r', 'wrong-current-sign')
    lines = ['* Conditional distributed-terminal implementation coupon; no PDK models.',
             '.options reltol=1e-9 abstol=1e-14 vntol=1e-10 rshunt=1e12 numdgt=17',
             'Vdrive a 0 PWL(0 0 0.2u 1 0.4u 0 0.6u -1 0.8u 0 1u 1 1.2u 0)',
             'Rload m 0 1000', 'Cload m 0 10p']
    if direct:
        lines += ['Vmeasure a m 0']
        observations = ['v(a)', 'v(m)', 'i(Vdrive)', 'i(Vmeasure)']
    else:
        if unequal:
            lines += ['Vwire0 a p0 0',
                      'Vdrive1 p1 0 PWL(0 0 0.2u -0.5 0.4u 0 0.6u 0.5 0.8u 0 1u -0.5 1.2u 0)']
        elif distributed:
            lines += ['Rleft a p0 2', 'Rright a p1 3']
        else:
            lines += ['Vwire0 a p0 0', 'Vwire1 a p1 0']
        average = ('Eaverage av 0 POLY(2) p0 0 p1 0 0 {1/3} {2/3}' if voltage_form == 'weighted'
                   else 'Eaverage av 0 POLY(2) p0 0 p1 p0 0 1 {2/3}')
        lines += ['Xattach m p0 p1 terminal_diagnostic',
                  '.subckt terminal_diagnostic m p0 p1',
                  average,
                  'Vmeasure av m 0',
                  'Vport0 p0 f0 0', 'Vport1 p1 f1 0',
                  'Fcontact0 f0 0 Vmeasure '+('{-1/3}' if wrong else '{1/3}'),
                  'Fcontact1 f1 0 Vmeasure {2/3}', '.ends terminal_diagnostic']
        observations = ['v(a)', 'v(m)', 'v(p0)', 'v(p1)', 'i(Vdrive)',
                        'i(v.xattach.vmeasure)', 'i(v.xattach.vport0)',
                        'i(v.xattach.vport1)', 'v(xattach.av)',
                        'v(xattach.f0)', 'v(xattach.f1)']
    lines += ['.control', 'set noaskquit', 'set numdgt=17', 'set wr_singlescale', 'set wr_vecnames',
              'save all', 'tran 1n 1.2u 0 1n',
              'wrdata waveform.dat '+' '.join(observations), 'quit', '.endc', '.end']
    return '\n'.join(lines)+'\n', observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--voltage-form', choices=['weighted', 'differential'], default='weighted')
    args = parser.parse_args(); assert not args.output.exists()
    args.output.mkdir(parents=True); records = []
    cases = ('direct-zero-r', 'adapter-zero-r', 'distributed-r', 'unequal-voltage', 'wrong-current-sign')
    for name in cases:
        text, observations = prepare(name, args.voltage_form); target = args.output/name
        target.mkdir(); (target/'coupon.cir').write_text(text)
        records.append(dict(name=name, deck_sha256=digest(text.encode()), columns=['time']+observations,
                            expected='failed signed-current gate' if name == 'wrong-current-sign' else 'passed prospective coupon gates',
                            runtime='not run'))
    result = dict(status='prepared conditional passive coupon; no simulation run',
                  script_sha256=digest(Path(__file__).read_bytes()), cases=records,
                  fixed_diagnostic_weights=['1/3', '2/3'], actual_SENSE_weights='not selected',
                  voltage_form=args.voltage_form,
                  expression_identity='v0/3+2*v1/3 = v0+2*(v1-v0)/3; output source remains av-to-ground, current weights unchanged',
                  original_SENSE_source_or_models_changed=False,
                  prospective_gates=dict(child_watchdog_s=30, finite_all_vectors=True,
                      header_identity='Exact ordered vector identity; only case and explicit name#branch to i(name) normalization.',
                      simulator_log='Fatal/error/no-such-vector/unknown-vector/device/parameter/aborted/failed-analysis/timestep/segfault/singular-matrix lines fail independently of exit0; all warning lines retained.',
                      required_final_time_s=1.2e-6, voltage_identity_abs_V=5e-11,
                      signed_current_identity_abs_A=1e-12, power_identity_abs_W=1e-12,
                      branch_shunt_conductance_S=1e-12,
                      shunt_accounting='Vport_i includes its f_i node shunt; subtract v(f_i)*1e-12 before comparing weighted current. Vmeasure includes the m node shunt, which is retained in both direct and adapter controls.',
                      zero_R_model_voltage='Exact timestamp and voltage arrays compared; any mismatch retained, not replaced by interpolation.',
                      negative_control='The wrong Fcontact0 sign MUST fail signed-current and power gates.'),
                  boundary='Passive RC coupon only; no PDK compact-model applicability, full11512 parity, actual distributed-current weighting or electrical acceptance claim.',
                  not_run=['All five ngspice coupons', 'Actual SENSE adapter',
                           'Full parameter/wave parity', 'Positive metal-R extraction',
                           'Intrinsic gate/body/junction and MIM ownership qualification'])
    (args.output/'contract.json').write_text(json.dumps(result, indent=2)+'\n')
    (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
