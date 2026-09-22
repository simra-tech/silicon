# Prospective typical-process runtime diagnostic

All12 legacy replay leaves for seeds51148/51296/51111 complete. Strict retained
five-parameter equality fails; output classification agreement is not full parity.

| Seed | Parameter | Native ARM ngspice47 | Legacy amd64 ngspice46 | ULP difference |
|---|---|---|---|---|
|51148 |`@n.xbgr.xr16.nr1[nsmm_rsh]` |0.2193081396694375 |0.2193081396694376 |4 |
|51111 |same |0.5843465204753614 |0.5843465204753613 |1 |
|51296 |all five probes |exact match |exact match |0 |

The input netlists, pinned PDK libraries and source hashes agree. The pinned
`resistors_mod_mismatch.lib` rppd definition assigns this parameter directly
from `agauss(0,1,(mm_ok != 1 ? 0 : 1))`; no geometry scaling precedes this
fingerprint. The retained46/47 source files `src/maths/misc/randnumb.c` and
`src/frontend/numparam/xpressn.c` are byte-identical. `agauss` calls `gauss1`,
which uses `sqrt(-2*log(r)/r)` in its Box–Muller transform. Therefore a changed
PDK card or changed Gaussian-generator source does not explain this discrepancy.
Architecture/compiler/libm rounding is a plausible hypothesis, not an established
cause. The five probes do not prove that every other realized parameter agrees.

A full per-device frozen-parameter replay could separate realized-input differences
from solver-runtime differences, but it needs an explicit design review: capture
all parameters, prove assignments survive operating point and temperature changes,
and leave PDK cards unchanged. Such a replay is **not run**. The original strict
failure and separate post-inspection four-ULP diagnostic remain distinct.
