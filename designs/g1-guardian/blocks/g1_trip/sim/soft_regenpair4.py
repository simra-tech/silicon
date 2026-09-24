"""Controlled SOFT regenerative XM3/4 area4; input XM1/2 explicitly unchanged."""
from run_regenpair4_diagnostic import trip_transform as hard_transform,rounding_relation,CAP,scale_interval


def trip_transform(original):
    hard=hard_transform(original)
    old='XCS icmp vth_soft cmp_clk cmp_soft cmp_soft_n vdd vss g1_cmp\n'
    new=old.replace('g1_cmp\n','g1_cmp_regenpair4\n')
    assert hard.count(old)==1 and hard.count(new)==0
    result=hard.replace(old,new)
    assert result.replace(new,old)==hard
    return result


def parameter_gate(before,after,old,legacy,oldlegacy):
    assert len(before)==len(after)==len(old)==11512 and before==after
    assert [r[0] for r in before]==[r[0] for r in old] and len(dict(before))==11512
    b,o=dict(before),dict(old);changed={CAP};laws={CAP:scale_interval(o[CAP],b[CAP],'45')}
    assert laws[CAP]['status']=='passed'
    for channel in ['xch','xcs']:
        for instance in ['xm3','xm4']:
            for kind in ['w','l','delvto','factuo']:
                key='@n.xt.%s.%s.nsg13_lv_nmos[%s]'%(channel,instance,kind);changed.add(key)
                laws[key]=rounding_relation(o[key],b[key],kind,3e-6 if kind=='w' else .13e-6)
    assert len(changed)==17
    assert [r for r in before if r[0] not in changed]==[r for r in old if r[0] not in changed]
    assert len(legacy)==27 and legacy==oldlegacy
    return dict(parameters_before=before,parameters_after=after,legacy27=legacy),laws
