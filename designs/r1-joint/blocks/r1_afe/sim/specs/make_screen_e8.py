#!/usr/bin/env python3
"""Layout E8 (track T3l): operating-point screen spec (x32 offset and its drift) for R-only views of screen builds.
  python3 specs/make_screen_e8.py <out.json> <build> [<build> ...]   (netlist $G1_RESULTS_ROOT/r1_afe/pexr-e8-<build>/pexr/r1_afe_post_rc.spice)"""
import json, sys
out, builds = sys.argv[1], sys.argv[2:]
J = []
for cm in (0.5, 1.5, 2.5, 2.8):
    for v in (3.0, 3.6):
        J.append(dict(tag='op_tt_ib10.14_cm%.1f_v%.1f' % (cm, v), tmpl='tb_afe_op.cir', corner='tt', subs=dict(VCMI=cm, IB='10.14u', VDDA=v)))
J.append(dict(tag='op_tt_ib10.14_cm2.5_v3.3', tmpl='tb_afe_op.cir', corner='tt', subs=dict(VCMI=2.5, IB='10.14u', VDDA=3.3)))
for cm in (0.5, 2.5):
    J.append(dict(tag='op_ss_ib11.81_cm%.1f' % cm, tmpl='tb_afe_op.cir', corner='ss', subs=dict(VCMI=cm, IB='11.81u')))
    J.append(dict(tag='op_ff_ib9.00_cm%.1f' % cm, tmpl='tb_afe_op.cir', corner='ff', subs=dict(VCMI=cm, IB='9.00u')))
V = {b: dict(netlist='$G1_RESULTS_ROOT/r1_afe/pexr-e8-%s/pexr/r1_afe_post_rc.spice' % b) for b in builds}
json.dump(dict(question='Layout E8 screen (track T3l): x32 / x1 output offset of the wiring-R-only views of builds %s over input CM 0.5-2.8 V '
                        '(tt 3.0/3.6 V), CM 2.5 V at 3.3 V, ss and ff at CM 0.5 and 2.5 V' % ', '.join(builds), variants=V, jobs=J), open(out, 'w'), indent=1)
print(len(J) * len(V), 'jobs')
