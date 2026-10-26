# sep_ref.py <run id>: separation of the reference error in an R2-4 buffer run: follower source (vrefa) vs slice port (vref__p8/p9); falls back to the source when the port vectors are not saved. Diagnostic (2026-10-26).
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "r4"))
from p4common import read, ts, T, ND
rid = sys.argv[1]
d, _ = read(os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_adc", rid, "codes.raw"))
F = 22 * T
nslot = int((d["time"][-1] - ts(0, "a", 0) - ND * T - 30e-9) // F) + 1
def s(v, t): return np.interp(t, d["time"], d[v])
pairs = {"a": ("v(vrefa)", "v(xadc.xl.vref__p8)", "v(vrefla)", "v(xadc.xl.vrefl__p2)"),
         "b": ("v(vrefb)", "v(xadc.xl.vref__p9)", "v(vreflb)", "v(xadc.xl.vrefl__p4)")}
LSB = 1.045 / 2048.0  # V of reference error that moves a full-scale MSB step by 1 LSB (worst case, full MSB sum)
for sl, (src, port, srcl, portl) in pairs.items():
    if port not in d: port = src; portl = srcl
    st, dsrc, dport, dportl = [], [], [], []
    for k in range(nslot):
        t0 = ts(k); tm = t0 + np.arange(ND) * T + 25e-9
        st.append(s(src, t0 - 0.2e-9) - s(port, t0 - 0.2e-9))
        dsrc.append(np.max(np.abs(s(src, tm) - s(src, t0 - 0.2e-9))))
        dport.append(np.max(np.abs(s(port, tm) - s(port, t0 - 0.2e-9))))
        dportl.append(np.max(np.abs(s(portl, tm) - s(portl, t0 - 0.2e-9))))
    st = np.array(st)
    print("slice %s: nslot %d; static src-port %.2f..%.2f mV (%.1f LSB-equiv at full MSB sum); "
          "src at slot start %.5f..%.5f V; max droop in eval: src %.3f mV, port %.3f mV, vrefl port %.3f mV "
          "(%.2f / %.2f / %.2f LSB-equiv)" % (sl, nslot, st.min()*1e3, st.max()*1e3, st.mean()/LSB,
          min(s(src, ts(k)-0.2e-9) for k in range(nslot)), max(s(src, ts(k)-0.2e-9) for k in range(nslot)),
          max(dsrc)*1e3, max(dport)*1e3, max(dportl)*1e3, max(dsrc)/LSB, max(dport)/LSB, max(dportl)/LSB))
