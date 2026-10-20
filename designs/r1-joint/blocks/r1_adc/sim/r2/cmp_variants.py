# comparator size variants for the revision-2 comparator study (instance parameters of r1_cmp2), second round:
# pair 48u/0.3u (input capacitance ~79 fF; the 96u/0.25u pair, ~125 fF, gave path-dependent codes in the ADC,
# run r2-quick-tt-e vs r2-dbg-quick-cmpB). Tail bias ib from r1_cmp2_bias (tail current ~10 x ib).
BASE = dict(wi="48u", li="0.3u", ngi=12, wt="16u", wtc="8u", ltc="0.5u", wcap="8u", lcap="4u", wr="2u", wh="8u")
VARIANTS = {
    "B": dict(BASE),
    "B12": dict(BASE, wcap="12u", wtc="12u"),
    "B16": dict(BASE, wcap="16u", wtc="16u"),
}


def inst(v):
    return " ".join("%s=%s" % (k, val) for k, val in VARIANTS[v].items())
