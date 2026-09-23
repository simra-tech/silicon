#!/usr/bin/env python3
"""One matched KPEX OP comparison, including actual PTAT terminal drops."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'coordinated_signal_remedy_20260923'))
from compare_bias_op import whole,sha


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('baseline-prepared','candidate-prepared','baseline-run','candidate-run','source','output'):
        ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    assert sha(a.source)=='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    ids=[];reference_ids=[]
    for line in a.source.read_text().splitlines():
        f=line.split()
        if f and f[0].startswith('XQ') and f[3]=='dvbe':ids.append(f[0])
        if f and f[0].split('_')[0]=='XQ56':reference_ids.append(f[0])
    assert Counter(n.split('_')[0] for n in ids)=={n:24 for n in ('XQ68','XQ69','XQ70','XQ71','XQ72','XQ73','XQ74','XQ76')}
    assert len(ids)==192 and len(reference_ids)==24
    old=whole(a.baseline_prepared/'kpex',a.baseline_run)
    new=whole(a.candidate_prepared/'kpex',a.candidate_run)
    assert old['summary']['parameter_before']==new['summary']['parameter_before']
    inputs={**old['inputs'],**new['inputs'],str(a.source):sha(a.source),str(Path(__file__)):sha(Path(__file__)),
            str(HERE.parent/'coordinated_signal_remedy_20260923/compare_bias_op.py'):sha(HERE.parent/'coordinated_signal_remedy_20260923/compare_bias_op.py')}
    def observations(view):
        devices={r['source_id']:r for r in view['analysis']['devices']}
        r16=devices['XR16']['terminal_voltage_V'];q56=devices['XQ56']['terminal_voltage_V']
        return dict(VREF_V=view['analysis']['actual_macro_ports']['vref']['voltage_V'],
                    whole_net_ranges=view['ranges'],XR16_terminal_V=r16,Q56_terminal_V=q56,
                    all24_Q56_reference_emitters=[dict(source_id=name,E_V=devices[name]['terminal_voltage_V']['E'],
                         E_minus_XR16_1_V=devices[name]['terminal_voltage_V']['E']-r16['1']) for name in reference_ids],
                    DVBE_emitters=[dict(source_id=name,E_V=devices[name]['terminal_voltage_V']['E'],
                         E_minus_XR16_2_V=devices[name]['terminal_voltage_V']['E']-r16['2']) for name in ids],
                    Q56_E_minus_XR16_1_V=q56['E']-r16['1'],
                    metal_interior_KCL_max_A=view['analysis']['metal_interior_KCL_max_A'],
                    inferred_MOS_HBT_KCL_max_A=view['analysis']['inferred_MOS_HBT_point_KCL_max_A'],
                    exact_maximum_principle=view['exact_discrete_maximum_principle_all55'],
                    maximum_principle_excursion_V=view['maximum_interior_excursion_V'],
                    supply_current_A=view['analysis']['actual_macro_ports']['vdd']['current_into_metal_A'])
    before,after=observations(old),observations(new)
    zero=new['analysis']['source_net_voltage_ranges']['vref']['zero_R_V']
    assert all(sha(Path(p))==h for p,h in inputs.items())
    result=dict(status='passed matched saved KPEX comparison; conditional not qualified',inputs=inputs,
                before=before,after=after,zero_R_VREF_V=zero,delta_VREF_V=after['VREF_V']-before['VREF_V'],
                remaining_VREF_error_V=after['VREF_V']-zero,all2842_parameters_exact=True,
                source_devices=1036,source_net_components=55,DVBE_source_emitters=192,reference_source_emitters=24,
                positive_edges=new['analysis']['positive_edges'],
                nonzero_runtime_s=new['summary']['runtime']['wall_s'],warnings=new['summary']['warnings'],
                not_run=['LEF nonlinear OP','complete resistor BN/contact/substrate model boundary','new CC coverage',
                         'PVT/startup/stability/MC/electrical adoption','final chip integration'])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','delta_VREF_V','remaining_VREF_error_V','positive_edges','nonzero_runtime_s')},indent=2))


if __name__=='__main__':main()
