"""Exact pure interval routine from the bound physical candidate helper; no new tolerance."""
from decimal import Decimal,localcontext
import math
import numpy as np

def scale_interval(old,new,cap_width_um='50'):
    """Outward binary64 interval for the pinned native expression.

    Old decimal-only failure is retained. Inverting the old rounded `1+t`
    requires a rounding enclosure; decimal print uncertainty alone is not an
    enclosure of the underlying t. Each native operation is bounded outward
    by its neighboring binary64 value. No simulator tolerance changes.
    """
    assert cap_width_um in ['50','45']
    down=lambda x:float(np.nextafter(float(x),-np.inf))
    up=lambda x:float(np.nextafter(float(x),np.inf))
    def outward(values):return [down(min(values)),up(max(values))]
    def multiply(a,b):return outward([x*y for x in a for y in b])
    def divide(a,b):
        assert b[0]>0
        return outward([x/y for x in a for y in b])
    def root_area(width):
        # Mantissa-times-suffix parsing followed by the explicit source order.
        l=outward([23.*1e-6]);w=outward([float(width)*1e-6])
        area=multiply(multiply(l,w),[1e12,1e12])
        return outward([math.sqrt(x) for x in area])
    with localcontext() as context:
        context.prec=60
        a,b=Decimal(old),Decimal(new)
        da=Decimal(10)**a.as_tuple().exponent/2
        db=Decimal(10)**b.as_tuple().exponent/2
        factor=(Decimal(69)/Decimal(cap_width_um)).sqrt()
        decimal_only=[1+(a-da-1)*factor,1+(a+da-1)*factor]
        original_print=[str(a-da),str(a+da)]
        observed_print=[str(b-db),str(b+db)]
        old_export=outward([float(a-da),float(a+da)])
        observed=outward([float(b-db),float(b+db)])
        # Enclose pre-rounding input of the old final addition, then undo the
        # division. The same area-independent native random deviation is used.
        old_t=outward([down(old_export[0])-1,up(old_export[1])-1])
        deviation=multiply(outward(old_t),root_area(69))
        assert .5 < 1+deviation[0] <= 1+deviation[1] < 2
        new_t=divide(deviation,root_area(float(cap_width_um)))
        predicted=outward([1+new_t[0],1+new_t[1]])
        passed=max(predicted[0],observed[0])<=min(predicted[1],observed[1])
        return dict(status='passed' if passed else 'failed',
            old_printed=old,new_printed=new,area_ratio='69/'+cap_width_um,
            exact_formula='new_scale=1+(old_scale-1)*sqrt(69/'+cap_width_um+')',
            native_expression='1+(cap_carea_mm-1)/sqrt(l*w*1e12)',
            old_decimal_print_interval=original_print,new_decimal_print_interval=observed_print,
            prior_decimal_only_prediction=[str(x) for x in decimal_only],
            old_root_area_interval=root_area(69),new_root_area_interval=root_area(float(cap_width_um)),
            held_random_deviation_enclosure=deviation,
            predicted_binary64_interval=predicted,observed_binary64_interval=observed,
            rounding_basis='Outward nextafter at each binary64 operation and inverse old addition/division; half-last-decimal print interval. No fitted absolute/relative tolerance.',
            numerical_options_changed=False)
