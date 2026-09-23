# R100 affected-source rejection and DC coverage

This record is separate from the frozen R100 partial-field milestone. It does
not adopt a circuit or transfer an earlier mismatch population.

## Conditional loaded rejection

Three nominal actual-BGR/full-TRIP leaves completed with exact 11,512 model
observations and 27 legacy controls, the original 1 µV/1 nA own-source DC
equivalence limits, 901 finite complex samples, and explicitly checked input
and supply excitations. The source is the same R100 diagnostic used by the
completed differential baseline: `ffb14762659eaf02b6a62e9edea3caa0e143cbc7881378b329d6ab9945a6554b`.

| Simulated rejection | 1 Hz, dB | 1.995262 MHz, dB |
|---|---:|---:|
| CMRR | 80.618787 | 63.296977 |
| PSRR, analog VDDA | 102.409521 | 24.459149 |
| PSRR, core VDD | 226.450649 | 106.092120 |

Rejection means `20 log10(abs(differential output transfer) / abs(disturbance
output transfer))`, not standalone output attenuation. No rejection limit was
allocated. In particular, the very large low-frequency core-VDD number is not
a physical isolation guarantee. The clock is frozen at DC zero. Only the
same 844 extracted source-pair capacitors are included; 134 unbound VSUBS terms,
complete MIM/tap fields, finite metal resistance, compact-model reference
planes and full-chip fill coupling remain unqualified. No zero physical
coupling, physical bound or full-PEX acceptance follows.

Common-mode OP observations were exact. Supply-leaf exact equality was false:
the maximum quiet-voltage difference was 48.447 pV and supply-current
difference 49.150 fA. These separately recorded differences passed the original
bounded own-source controls; they are not relabeled exact.

## Original standalone DC fixture

The required grid preserves the original V06 ideal VREF/PTAT, passive TRIP
load, model libraries, solver options and nodesets. It covers nine MOS/resistor
combinations, three analog rails, four temperatures and nine true-common-mode/
shunt pairs per tuple. It is **not** an actual-BGR/full-TRIP 108-tuple grid.
The ideal-reference limitation is retained explicitly.

The historical fixture source is
`8880157bd2a88c92a248c4865fc79b9242954d1920ce6e3834b776cae6eee57f`.
The new source is canonical R100
`bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782`.
Both have 159 identical primitive paths and terminal/model assignments. Ten
main-OTA parameter records differ; all remaining records are exact:

| Devices | Historical → R100 source geometry, µm |
|---|---|
| XM1, XM2 | W96/L2/ng16 → W384/L2/ng64 |
| XM3, XM4 | W80/L1/ng10 → W320/L4/ng40 |
| XM11, XM12, XM14, XM15 | W96/L1/ng12 → W384/L4/ng48 |
| XCC | W23/L23 → W45/L23 |
| XRZ | W1/L6.2 → W1/L100 |

Thus the historical result is a fixture replay control, not changed-source
acceptance. Its nine printed rows replayed exactly. The new nominal tuple,
repeat and reversed-order controls passed all 529 SENSE model observations
and all nine operating-point vectors at all nine points exactly. Each run
also returns to its first bias point. Gain remains 19.9–20.1 V/V; offsets are
reported separately, without claiming joint-chain calibration.

Preparation, controls and the independent saved-log audit passed. All 108
source-held tuples completed: 972 true-common-mode/shunt points and 108 return
controls. The audit independently checked 159 primitive paths, all 529 model
observations before and after each tuple, exact source/runtime bindings,
finite results and the original 19.9–20.1 V/V gain limit. All 108 source,
finite and gain checks passed; the simulated gain range was
19.970331784624307–19.981915194544655 V/V, with zero gain failures. The
audit record is `sense-rz100-dc-grid-audit-20260923-r1/summary.json` under
the configured simulation bulk root. Completed tuples, including nominal, were reused
without rerun. Capacity and host-supervisor failures are preserved separately
from simulator results.

The completed batch supervisor reserved up to four disjoint tuples per fresh
resource/storage gate, with a five-minute batch envelope. It retained the
original 120-second simulator and 150-second tool limits and reserved the full
tool limit plus frontend allowance before each launch. The earlier supervisors
were retired only after every actual child finished. Two later supervisor
starts failed during preflight because their inherited single-CPU affinity
prevented global resource-ledger validation; neither launched a leaf. The
final successors used host affinity for resource observation and explicit CPU
affinity for their leaves. No numerical helper, source, solver option or
acceptance limit changed.

## Built against

| Item | Identity / verification |
|---|---|
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; exact installed model-tree hashes |
| ngspice | 46, SPARSE; exact historical/runtime version comparison |
| OCI config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |
| OCI manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` |

Source-bound commands and per-leaf inputs are retained in each run contract.
Complete physical PEX and changed-source statistical qualification remain
separate open requirements. Hardware verification is **not run**.
