"""Conditional interval arithmetic; never turns a failed exact comparison into PASS."""
import math

VOLTAGE_COMPARISON_V=1e-7
CURRENT_COMPARISON_A=1e-9


def actual_bits(values,soft,hard):
    assert len(values)==16 and all(math.isfinite(v) for v in values)
    assert all(type(code) is int and 0<=code<=255 for code in [soft,hard])
    expected=[1.2*((code>>bit)&1) for code in [soft,hard] for bit in range(8)]
    return values==expected


def interval_divide(numerator,denominator):
    assert denominator[0]>0 and denominator[1]>=denominator[0]
    candidates=[n/d for n in numerator for d in denominator]
    return [min(candidates),max(candidates)]


def transfer_bounds(values,epsilon=VOLTAGE_COMPARISON_V):
    assert len(values)==256 and all(math.isfinite(v) for v in values)
    assert math.isfinite(epsilon) and epsilon>=0
    span=values[-1]-values[0];lsb=[(span-2*epsilon)/255,(span+2*epsilon)/255]
    assert lsb[0]>0
    steps=[];inl=[]
    for index in range(255):
        delta=values[index+1]-values[index]
        interval=[delta-2*epsilon,delta+2*epsilon]
        normalized=interval_divide(interval,lsb)
        dnl=[value-1 for value in normalized]
        steps.append(dict(lower_code=index,delta_V=interval,DNL_LSB=dnl,
            status='passed conditional numerical interval' if interval[0]>0 and dnl[0]>-1 else 'requires original-static refinement'))
    for index,value in enumerate(values):
        residual=value-(values[0]+index*span/255)
        inl.append(interval_divide([residual-2*epsilon,residual+2*epsilon],lsb))
    return dict(epsilon_V=epsilon,endpoint_LSB_V=lsb,steps=steps,INL_LSB=inl,
        status='passed conditional numerical intervals' if all(row['status'].startswith('passed') for row in steps) else 'requires original-static refinement',
        scope='Conditional on a separately justified uniform per-point epsilon. Finite anchor agreement alone is not proof of global error; no INL allocation invented.')
