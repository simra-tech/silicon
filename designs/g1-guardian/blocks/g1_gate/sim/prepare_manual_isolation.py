#!/usr/bin/env python3
"""Prepare the bounded, conditional manual load-isolation fixture; no run/adoption."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE_SHA = '697ab21778feeefffa2b8cf147f83edf38c46a53d97a97ce0505f618c53d85db'
PAD_SHA = 'c46e32249a04ed75d25d5f2b4f0b79304c25f7d85ce7628ee5a65b1734f43256'
CORE_SHA = 'e91617f5fcf6f5a0dc721a2ba53b507a05cc226d6dbf0bebaa858a1e7d876765'
FET_SHA = 'c5572438f1a79c8e9f48cfcf5a8d152daafdad8e8ec26ac30f807f0211edf2df'
SEQUENCES = {
    'io_first': ('0 0 1u 0 3u 3.3 16u 3.3', '0 0 5u 0 7u 1.2 16u 1.2'),
    'missing_core': ('0 0 1u 0 3u 3.3 16u 3.3', '0 0 16u 0'),
}
VECTORS = ['v(gate)', 'v(gfet,source)', 'i(vfet)', 'i(lload)', 'v(dfet,source)',
           'i(vig)', 'v(fault_n)', 'v(tripped)', 'v(bus)', 'v(rawbus)',
           'i(vbus)', 'v(vdda_s)', 'i(vdda)', 'v(vdd_s)', 'i(vdd)',
           'v(vdda)', 'v(vdd)', 'v(en_pad)', 'v(en_core)', 'i(ven)',
           'v(source)', 'v(kelvin)', 'v(drain)', 'v(gfet)', 'v(gate_core)']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(raw, pad_path, core_path, fet_path, output, sequence, closed, capacitance):
    assert sha(raw) == TEMPLATE_SHA
    assert sequence in SEQUENCES and capacitance in (.1e-6, 10e-6)
    original = raw.decode()
    assert original.count('.control\n') == 1
    source, old_control = original.split('.control\n')
    changes = []
    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old
        changes.append(dict(old=old,new=new))
        source = source.replace(old,new)
    replace('.include /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice/sg13g2_io.spi',
            '.include '+str(pad_path))
    replace('.include /work/designs/g1-guardian/blocks/g1_gate/sim/postlayout/g1_gate_pex.spice',
            '.include '+str(core_path))
    replace('.incpslt /work/build/g1_gate/vendor/CSD16340Q3.lib', '.incpslt '+str(fet_path))
    pa,pd = SEQUENCES[sequence]
    replace('Vdda vdda_s 0 pwl(0 3.3 5u 3.3 7u 0 16u 0)', 'Vdda vdda_s 0 pwl('+pa+')')
    replace('Vdd vdd_s 0 pwl(0 1.2 10u 1.2 12u 0 16u 0)', 'Vdd vdd_s 0 pwl('+pd+')')
    replace('Ven en_core 0 0',
            'Ven en_pad 0 0\nXPE en_pad en_core vdd 0 vdda 0 0 G1_VSS_DERIVATIVE__sg13g2_IOPadIn')
    for name,instance in [('Out30mA','XPG gate gate_core'), ('Out4mA','XPF fault_n fault_core')]:
        replace(instance+' vdd 0 vdda 0 sg13g2_IOPad'+name,
                instance+' vdd 0 vdda 0 0 G1_VSS_DERIVATIVE__sg13g2_IOPad'+name)
    resistance = .01 if closed else 10e6
    replace('Vbus bus 0 5',
        'Vbus rawbus 0 5\n'+
        '* Conditional manual disconnect: finite resistance, not a clamp.\n'+
        'Rdisconnect rawbus bus '+format(resistance,'.17g')+'\n'+
        'Ccontact rawbus bus 100p\n'+
        'Cbus bus 0 '+format(capacitance,'.17g')+'\n'+
        'Rbleed bus 0 10.5k')
    # The flyback cathode remains downstream of the disconnect. No rail/load
    # source is set to zero to fake an open switch or erase stored bus energy.
    assert 'Dfly drain bus fixture_clamp' in source
    assert 'Rload bus load 5' in source and 'Lload load drain 1e-07' in source
    assert '.option method=gear reltol=0.005 itl4=100 abstol=1e-9 vntol=1e-5 chgtol=1e-13' in source
    restored = source
    for row in reversed(changes):
        assert restored.count(row['new']) == 1
        restored = restored.replace(row['new'],row['old'])
    assert restored+'.control\n'+old_control == original
    control = ('.control\nset num_threads=1\nset numdgt=17\nset wr_singlescale\n'+
        'set wr_vecnames\ntran 1n 16u 0 1n\nwrdata '+str(output/'wave.tsv')+' '+
        ' '.join(VECTORS)+'\necho MANUAL_ISOLATION_END\nquit 0\n.endc\n.end\n')
    report = dict(status='prepared only; electrical acceptance not run',
        sequence=sequence, disconnect='closed negative control' if closed else 'open assumed manual disconnect',
        template_sha256=sha(raw), source_inverse_exact=True, exact_source_changes=changes,
        control_replaced_explicitly=True, original_control_sha256=sha(old_control.encode()),
        child_timeout_s=120, stop_s=16e-6, maximum_step_s=1e-9,
        vectors=['time']+VECTORS,
        assumptions=dict(raw_bus_V=5, load_R_ohm=5, load_L_H=100e-9,
            disconnect_R_ohm=resistance, contact_C_F=100e-12,
            bus_C_F=capacitance, bleed_R_ohm=10500, pulldown_R_ohm=10000),
        prospective_acceptance=dict(initial_bus_abs_max_V=.01,
            initial_load_abs_max_A=.01, all_window_load_abs_max_A=.01,
            load_resistor_energy_max_J=8e-9,
            gate_and_VGS_historical_max_V=1,
            gate_voltage_result_must_remain_separate=True,
            initial_conditions='Simulator OP only; no IC/UIC or forced-zero bus source. Hardware measurement not run.'),
        retained_initial_energy_limit_J=dict(bus_capacitor_max=.5*capacitance*.01**2,
            contact_capacitor_at_5V= .5*100e-12*5**2,
            inductor_at_10mA=.5*100e-9*.01**2),
        scope='Supervised, verified de-energized transitions only. Explicit-body pinned electrical pad derivative; native tap A/P-to-R applicability unresolved. Real FET model unchanged. No automatic brownout protection, SOA, continuous worst-case or hardware verification. This preparation creates no simulation claim.')
    return source+control, report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template',type=Path,required=True)
    p.add_argument('--pad-source',type=Path,required=True)
    p.add_argument('--core-source',type=Path,required=True)
    p.add_argument('--fet-source',type=Path,required=True)
    p.add_argument('--sequence',choices=SEQUENCES,required=True)
    p.add_argument('--closed',action='store_true')
    p.add_argument('--bus-uf',type=float,choices=[.1,10.],default=10.)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); assert not a.output.exists()
    for path,expected in [(a.pad_source,PAD_SHA),(a.core_source,CORE_SHA),(a.fet_source,FET_SHA)]:
        assert sha(path.read_bytes()) == expected
    deck,report=build(a.template.read_bytes(),a.pad_source.resolve(),a.core_source.resolve(),
                     a.fet_source.resolve(),a.output.resolve(),a.sequence,a.closed,{.1:.1e-6,10.:10e-6}[a.bus_uf])
    report['source_hashes'] = dict(pad=PAD_SHA,core=CORE_SHA,fet=FET_SHA)
    report['deck_sha256'] = sha(deck.encode())
    a.output.mkdir(parents=True)
    (a.output/'fixture.cir').write_text(deck)
    (a.output/'contract.json').write_text(json.dumps(report,indent=2)+'\n')
    (a.output/'preparer.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in report.items() if k!='exact_source_changes'},indent=2))


if __name__=='__main__':
    main()
