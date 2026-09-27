#!/usr/bin/env python3
"""Red-team bring-up 2026-09-27: run the unmodified g1_host calibration (DummyTransport) against a
hard-comparator model whose kick offset depends on the driven DAC code, as the TRIP NF4 block bench
shows (offset = k200 + slope*(code-200) LSB). Reports: crossing codes, frames/time of the sweep,
the effective hard threshold that results for each target after a 25 mV calibration, and the
reach of code 255. Usage: calsim.py <k200> <slope> [sense_offset_mV] [targets...]"""
import sys, os
sys.path.insert(0, os.environ.get('HOSTDIR', '.'))
import g1_host as h

class CodeKick(h.DummyTransport):
    def __init__(self, k200, slope, **kw):
        super().__init__(**kw); self.k200 = k200; self.slope = slope
    def _cmp(self, noise=True):
        # hard kick as a function of the driven hard code
        c = self._eff_codes()[1]
        self.hard_kick_lsb = self.k200 + self.slope * (c - 200)
        return super()._cmp(noise)

def eff_threshold_mV(k200, slope, driven, lsb):
    return (driven - (k200 + slope * (driven - 200))) * lsb

k200, slope = float(sys.argv[1]), float(sys.argv[2])
ofs = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
targets = [float(x) for x in sys.argv[4:]] or [30.0, 33.0, 35.0, 37.0, 39.0]
t = CodeKick(k200, slope, sense_offset_mV=ofs)
g = h.G1(t, vref_V=t.vref_V); g.declare_inhibit(True)
t.set_en(False); t.sleep(1e-3); g.enable(10); g.identify()
t.vin_mV = 25.0
n0 = len(t.frames); t0 = t.t
s = g.calibrate_soft(25.0); n1 = len(t.frames)
HV=float(os.environ.get('HARDV','25'))
t.vin_mV = HV
hd = g.calibrate_hard(HV)
t.vin_mV = 25.0; n2 = len(t.frames); t2 = t.t
cal = g.compute_calibration(s, hd)
print('hard calibrated at %.1f mV' % HV)
lsb = cal['lsb_mV']
print('k200=%.1f slope=%.3f sense_ofs=%.2f mV | soft c_high %d, hard c_high %d, SENSE_OFS %d, hard_extra %d'
      % (k200, slope, ofs, s['c_high'], hd['c_high'], cal['sense_ofs'], cal['hard_extra']))
print('frames: soft %d, hard %d; chip-side time %.1f ms; at 1 ms/USB transaction about %.2f s'
      % (n1 - n0, n2 - n1, (t2 - t0) * 1e3, (n2 - n0) * 1e-3))
for T in targets:
    try:
        c = g.codes_for(T, min(T - 5, 30.0))
    except h.G1Error as e:
        print('target %.1f mV: REFUSED (%s)' % (T, e)); continue
    d = c['driven_hard']
    eff = eff_threshold_mV(k200, slope, d, lsb) - ofs
    print('target %.1f mV: DAC_HARD %d driven %d -> effective %.2f mV (error %+.2f mV, %+.1f %%)'
          % (T, c['DAC_HARD'], d, eff, eff - T, 100 * (eff - T) / T))
reach = eff_threshold_mV(k200, slope, 255, lsb) - ofs
print('reach at driven code 255: %.2f mV' % reach)
