# Load-servo corner matrix — C148 (800 ps/bit) and C149 (400 ps/bit)

Public-experiment record, 2026-08-06 evening — 2026-08-07 morning. In simulation only
(IHP SG13G2 corner libs, ngspice). Nothing here is a signoff or a tape-out claim.

## The circuit change (C148)

Common-mode feedback moved to the **loads**: the diode PMOS gates (XM3/XM4, 16.0u) are servoed so
the cml_out_p/cml_out_n average tracks VCMREF = 0.75 V (absolute source — a testbench idealization;
see Open items). XMTAIL fixed at 2.5u, so common mode and tail current are independent. Under the
previous tail-servo (C146), cm wandered ~100 mV across corners; under C148 it holds 0.765–0.776 V
(11 mV spread).

## The measurement standard (eye_decode.py)

Decode by **sweeping the sampling offset** (0.05-bit steps, bounded above by the simulated window)
and report the contiguous zero-error spans — never an error count at a single phase. A
phase-quantized decoder (integer pattern shift + fixed 0.5-bit phase) can only sample at offsets
k+0.5 and turned corner-dependent chain latency into phantom errors: the "5/64 and 12–13/64
failures" first reported for the C148 27 C corners were the sampling instant sitting on the eye
edge. Controls that keep the standard honest:

- **Reference**: comparator differential (xcomp.c_p − c_n, 0 V slice) must decode 0/64 in the same
  raw, else the run is void.
- **Floor**: the 64-bit TX has 31 ones / 33 zeros, so a stuck pin scores 33 (high) or 31 (low).
- **Closed-eye control**: C146's failing corners have **no** zero-error offset at any position —
  the standard does not rescue genuinely broken circuits.
- **Point count**: verify raw npoints against the deck's expected count before reading anything
  (ngspice exits 0 after aborted transients).
- **Sweep bound**: latency in bits doubles when the bit halves; a minimum at the sweep edge means
  the sweep is too short (C149's first report clipped the −40 minimum this way: 20/64 at a 0–3
  sweep, truly 8/64 at offset 3.35).

## C148 verified results, 800 ps/bit, 64-bit PRBS-7 window

| corner | cm (V) | zero-error span (bits past 10 ns settle) | width |
|---|---|---|---|
| TT-TYP-125 | 0.7760 | 1.30–2.15 | ~720 ps |
| SS-TYP-27  | 0.7673 | 1.55–2.45 | ~720 ps |
| SS-TYP-125 | 0.7716 | 1.50–2.35 | ~680 ps |
| SS-WCS-27  | 0.7673 | 1.60–2.45 | ~680 ps |
| SS-WCS-125 | 0.7715 | 1.50–2.35 | ~680 ps |
| SS-WCS-N40 | 0.7651 | 1.70–2.55 | ~680 ps |

**Cross-corner intersection 1.70–2.15 bits (360 ps): one fixed sampling instant decodes all six
corners at 0/64.** The −40 corner had been dead (stuck-pin floor) in every prior configuration.
Threshold sensitivity: at a fixed in-window instant, all six corners decode 0/64 for any slice
threshold 0.10–1.10 V.

## C149 verified results, 400 ps/bit, same netlist

No corner has any zero-error offset (sweep 0–11 bits). Minima: TT-TYP-125 2/64 @2.60,
SS-TYP-125 5/64 @2.90, SS-WCS-125 6/64 @2.95, SS-TYP-27 7/64 @3.05, SS-WCS-27 7/64 @3.10,
SS-WCS-N40 8/64 @3.35. The rig holds a 0.95-bit clean span at every corner, so the comparator
front end is clean at 2.5 GS/s; the ceiling is the sense-amp/latch stage (state-change time,
~100 ps evaluate needed).

**Rate of record: 1.25 GS/s across the full six-corner matrix. 2.5 GS/s fails at every corner
with this architecture.**

## Prior-claim audit (C145, tail-servo era, same standard)

27 C corners at 1600 ps/bit: no zero-error offset (minima 11 and 9). SS-WCS-N40: stuck-pin floor
at 1600 and 3200 ps. SS-TYP-27 at 3200 ps: 1/64 at best offset. SS-WCS-27 at 3200 ps: 1440 ps
clean span. All pre-C148 rate-ladder conclusions stand.

## Open items

- VCMREF is an ideal 0.75 V source; a real part needs a VDD-ratioed or bandgap reference. C150
  (full 127-bit PRBS period, VDD 1.08/1.32/1.20 V, six corners) is running as this is written and
  will be appended once independently verified.
- Schematic-level only: no layout parasitics, no mismatch, no noise analysis yet.
- Path to 2.5 GS/s: interleaved sense amps (alternate bits) — proposed, not designed.

## C150 (2026-08-07) — full-period pass, supply axis void

**Axis 1 (pattern) — valid, passed.** TX extended to the full 127-bit PRBS-7 period (64 ones,
63 zeros; first 64 bits identical to the previous window), 800 ps/bit, 10 ns settle + 131 bits.
All six corners decode 0/64 with a 720 ps eye and spans identical to the 64-bit result
(TT-TYP-125 1.30–2.15, SS-TYP-27 1.55–2.40, SS-TYP-125 1.50–2.35, SS-WCS-27 1.60–2.45,
SS-WCS-125 1.50–2.35, SS-WCS-N40 1.70–2.55; cm unchanged to 4 digits). The previously untested
half of the pattern, including the runs of seven, changes nothing.

**Axis 2 (supply) — VOID, unrun.** The V108/V120/V132 decks all carry `VDD VDD 0 DC 1.200` and
`VBUF_VDD VDD_BUF 0 DC 1.200`; the supply distinction exists only in the header comment. Confirmed
by identical non-comment deck bodies and by `v(vdd)` = 1.2000 sampled from all three raws. Each
corner ran three times at nominal. Detected because the three "conditions" agreed to every digit —
a 10% supply step cannot leave cm identical to 0.1 mV (harness finding H-723). **Behaviour across
supply is unknown**; the standing prediction that 1.08 V fails (VCMREF being an absolute source) is
untested, neither confirmed nor refuted. C151 reruns it with the sources actually edited.

**Standing rule added:** every swept quantity (supply, temperature, bit period) must be read back
out of the raw and reported beside the result. A condition named only in a filename is not a
condition.

## C151 (2026-08-07) — supply axis rerun, and the empty intersection

Supply genuinely applied this time: `v(vdd)` read back from every raw as 1.0800 / 1.2000 / 1.3200.
64-bit pattern, 800 ps/bit. **All 18 conditions (6 corners × 3 supplies) decode 0/64**, rig 0/64
throughout, per-condition eyes 640–760 ps.

| condition | window (bits past 10 ns settle) | | condition | window |
|---|---|---|---|---|
| TT-TYP-125 @1.32 | 1.25–2.05 | | SS-TYP-125 @1.20 | 1.50–2.35 |
| TT-TYP-125 @1.20 | 1.30–2.15 | | SS-WCS-125 @1.20 | 1.50–2.35 |
| TT-TYP-125 @1.08 | 1.40–2.25 | | SS-TYP-27 @1.20 | 1.55–2.45 |
| SS-TYP-125 @1.32 | 1.35–2.20 | | SS-WCS-27 @1.20 | 1.60–2.45 |
| SS-WCS-125 @1.32 | 1.35–2.20 | | SS-WCS-N40 @1.20 | 1.70–2.55 |
| SS-TYP-27 @1.32 | 1.35–2.20 | | SS-TYP-125 @1.08 | 1.80–2.60 |
| SS-WCS-27 @1.32 | 1.35–2.20 | | SS-WCS-125 @1.08 | 1.80–2.60 |
| SS-WCS-N40 @1.32 | 1.50–2.30 | | SS-TYP-27 @1.08 | 1.85–2.70 |
| | | | SS-WCS-27 @1.08 | 1.85–2.70 |
| | | | SS-WCS-N40 @1.08 | 2.15–2.90 |

**INTERSECTION ACROSS ALL 18: EMPTY.** Latest opening 2.15 (SS-WCS-N40 @1.08 V) vs earliest
closing 2.05 (TT-TYP-125 @1.32 V) — a fixed sampling instant misses by 0.10 bits (80 ps). Chain
latency spread across corner and supply is ~700 ps, one full bit period, as wide as the eye itself.

**Claim of record (revised):** in simulation, 0/64 at 1.25 GS/s at every corner and supply
**given a clock that tracks temperature and supply**. A fixed-instant clock does not work across
the full matrix. Not a signoff; schematic-level only.

**Note on axis coverage:** C151 used the 64-bit pattern, so the supply axis and the full-127-bit
axis have each passed separately but not together.

Per-condition margins do not compose (harness finding H-724): report the cross-condition
intersection as the headline number, the per-condition table as diagnostic.

**Open, pending C152:** where the 700 ps of latency spread accumulates, stage by stage. If one
stage dominates, replica-path clocking is the fix; if it is spread evenly, clock-and-data recovery
or a per-condition clock. Also open: the bit rate at which the intersection first becomes non-empty.

## C152 (2026-08-07) — where the latency spread accumulates

Delay from the bit-clock edge to the crossing at each node, spread across the 18 conditions:

| node | spread across 18 (ps) | mean delay (ps) |
|---|---|---|
| c_p − c_n (comparator) | **11** | 140 |
| cml_out | 53 | 351 |
| sa_n (sense amp) | 111 | 294 |
| Q (NAND latch) | 252 | 543 |
| pbit_out_core | 524 | 626 |
| PBIT_OUT (pad) | 533 | 778 |

The analogue front end is essentially invariant (11 ps); the digital tail — latch, buffers, output
driver — carries ~400 ps of the 533 ps total. Spread is distributed across a latch and three
buffers rather than concentrated in one stage, so a **simple replica-path clock will not track it**;
a replica would have to duplicate the whole NAND→buffer→output chain.

**Tested and refuted: sampling before the pad does not rescue the intersection.** The output driver
and pad exist only for observability, so the obvious hypothesis was that the empty window is an
artifact of the observation path. Decoding internal nodes across all 18 conditions (harness finding
H-725):

| sampling point | intersection across 18 |
|---|---|
| Q (latch, on-chip) | empty by 360 ps |
| pbit_out_core (pre-pad) | empty by 40 ps |
| PBIT_OUT (pad) | empty by 120 ps |

Sampling at Q is *worse*. Per-condition windows are ~600 ps at Q against 640–760 ps after the
buffers: buffers sharpen edges, so window width grows along the chain slightly faster than delay
spread does. Intermediate nodes are not automatically better test points.

## Axis decomposition and the supply-tolerance specification

Window-position shift by axis, from the 18 measured windows (no additional simulation):

| axis | at VDD 1.32 | at VDD 1.08 |
|---|---|---|
| supply 1.32 → 1.08 V (per corner) | 120 ps (TT-TYP-125) … 520 ps (SS-WCS-N40) | — |
| temperature 125 °C → −40 °C | 120 ps | 280 ps |
| process TT → SS (at 125 °C) | 80 ps | 320 ps |

**Every axis is 3–4× worse at low supply**: the axes are not independent contributions, low supply
amplifies sensitivity to all of them (gates short of headroom). One fix aimed at supply sensitivity
would improve temperature and process behaviour too.

**Specification derived:** at nominal supply alone the six-corner intersection is **open 360 ps**;
at ±10% it is empty by 120 ps; linear interpolation of the measured window edges puts the closing
point at **≈ ±7.5% supply**. As drawn, this block needs its supply held to roughly 7% for a
fixed-instant clock to work across the corner matrix — an on-chip regulator requirement, not a
defect.

**In flight (C153):** the 18-condition matrix at 1000 ps/bit, testing the published prediction that
the intersection opens to ~116 ps and that the crossing is near 861 ps/bit (model: eye ≈ 0.836 × BP,
latency spread ≈ 720 ps fixed). Partial at 4/18 conditions: eyes 850–950 ps, intersection open
300 ps — but the late-edge condition (SS-WCS-N40 @1.08 V) has not finished, so the number will
shrink. Not scored until complete.

## C153 (2026-08-07) — 1000 ps/bit: the first composable result

All 18 conditions (6 corners × 1.08/1.20/1.32 V), 127-bit PRBS-7, 1000 ps/bit. Rig 0/127 and
output 0/127 at every condition; per-condition eyes 850–950 ps.

**INTERSECTION OPEN 150 ps** — late open SS-WCS-N40 @1.08 V at 1.65 bits, early close
TT-TYP-125 @1.32 V at 1.80 bits. A single fixed sampling instant decodes the full pattern at every
corner, over 165 °C, with the supply ±10%.

**Prediction scored.** Published before the runs existed, from the 800 ps/bit windows alone
(eye ≈ 0.836 × BP, latency spread ≈ 720 ps fixed): +116 ps. Measured: **+150 ps**, an error of
34 ps on a quantity that moved 270 ps between the two rates. The model's assumptions were both
slightly wrong in opposite directions — the spread shrank to 650 ps rather than staying fixed (part
of it is tied to the decision schedule, not propagation), while the eye grew to ~0.90 × BP — and the
errors largely cancelled. Predicted crossing 861 ps/bit; interpolating the two measured
intersections (−120 ps at 800, +150 ps at 1000) puts it at **≈889 ps/bit**.

### Claim of record (2026-08-07, supersedes all earlier rate claims)

> In simulation: 0/127 errors from a **single fixed sampling instant** across six process/temperature
> corners × three supplies (±10%), full PRBS-7 period, at **1.0 GS/s**, with 150 ps of shared
> margin. Fixed-clock operation fails above ≈1.12 GS/s; per-condition operation reaches 1.25 GS/s
> but does not compose.

Still schematic-level: no layout parasitics, no device mismatch, no noise analysis, VCMREF an ideal
source. Not a signoff, not a tape-out claim.

**Next (C154):** strengthen the digital tail (NAND latch + three buffer stages, which carry ~400 ps
of the 533 ps spread), rerun the 18-condition matrix at 800 ps/bit, target making 1.25 GS/s
composable.

## Derived design trade-off — supply regulation vs achievable fixed-clock rate

From the measured window edges at 800 and 1000 ps/bit (linear interpolation of edges in VDD; no
additional simulation):

| supply tolerance | shared margin @800 ps | @1000 ps | max fixed-clock rate |
|---|---|---|---|
| ±0% (perfect) | +360 ps | +550 ps | >1.25 GS/s |
| ±2.5% | +240 ps | +450 ps | >1.25 GS/s |
| ±5% | +120 ps | +350 ps | >1.25 GS/s |
| ±7.5% | 0 ps | +250 ps | ≈1.25 GS/s (boundary) |
| ±10% | −120 ps | +150 ps | 1.13 GS/s (889 ps/bit) |

**Sampling-instant specification.** At ±10% supply and 1000 ps/bit: sample at **1.725 bits past the
settle reference, ±75 ps**. At nominal supply and 800 ps/bit: 1.925 bits, ±180 ps. That tolerance is
the whole budget for clock jitter, distribution skew, and edge-placement error — and none of
mismatch, extracted parasitics or noise has been charged against it yet.

**Reading:** the rate is not a property of the circuit alone. Behind a dedicated on-chip regulator
(±5% or better) the 1.25 GS/s rate is composable; on a raw ±10% supply the fixed-clock ceiling is
1.13 GS/s. Quote the trade, not a single number.

## Output-chain taper: C154 / C155 / C156 (2026-08-07)

The chain is Q → XB1 → XB2 → XM7/8 (PBIT_RAW tap) → XM9/10 (block output) → XISO1 → XISO2 → 210 fF
pad load. The last two stages live in a **separate include** (`*-ISOBUF-PBIT_OUT.spice`), so the
chain crosses a file boundary. Chain delay is set by the ratio between neighbouring stages; as
drawn those ratios are 4.94, 1.15, 1.00, 1.00, 8.94, 2.86 — three stages amplifying nothing and one
overloaded ~9×. Delay proxy (Σ of 1+fanout): 25.9 τ.

| run | change | intersection @800 ps/bit | start spread |
|---|---|---|---|
| C148 | baseline | −120 ps | 720 ps |
| C154 | every device ×2 | **0 ps** (exactly) | 680 ps |
| C155 | retaper, comparator block only | **−160 ps** | 760 ps |
| C156 | retaper both files, equal 2.29× | running | — |

**C154** should have been a no-op — uniform scaling doubles drive and load together — and recovered
120 ps *because the scaling stopped at the block boundary*: exactly one ratio changed (XM9/10 driving
an unscaled XISO1, 1.0 → 0.5).

**C155** set the three in-block ratios to 3.53/4.0/4.0 — textbook — and was **worse by 160 ps**,
because the two unreachable ratios became 0.10 and 8.94. Predicted in advance from the delay proxy
(29.4 τ vs 25.9, "≈14% slower, −80 to −100 ps"); measured every condition 40–160 ps later. Direction
and scale correct, magnitude understated. See harness finding H-727: partial optimisation across an
interface is worse than none, because the quantity optimised belongs to the *pair*.

**C156** (in flight) applies one equal ratio of 2.29 across all six stages, both files:

| stage | as drawn (µm, P+N) | C156 |
|---|---|---|
| XB1 | 0.85 | 0.85 (unchanged) |
| XB2 | 4.20 | 1.95 |
| XM7/8 | 4.83 | 4.47 |
| XM9/10 | 4.83 | 10.25 |
| XISO1 | 4.83 | 23.50 |
| XISO2 | 43.20 | 53.86 (w=15.71/11.22 with **m=2**) |

Build verified against the netlists: all six ratios = 2.29, delay proxy 19.8 τ (−24%).
**Prediction on record:** spread ~760 → ~520 ps, intersection ≈ +160 ps, which would make 1.25 GS/s
composable. Not scored until all 18 conditions land.

**Note — stage count kept at six.** An earlier recommendation to remove two stages was withdrawn:
XM7/8 feeds the separate PBIT_RAW output pin, so deleting it changes the block's I/O, and each stage
inverts so only an even number may be removed. Six equal stages give −24% delay against −31% for
four; 7% is a cheap price for leaving the interface alone.

**Open — unmodelled load:** PBIT_RAW is connected to nothing in these testbenches while PBIT_OUT
carries 210 fF. On a real part it would drive a comparable pad, so the stage feeding it is
under-loaded here and today's timing is optimistic by an unquantified amount.

## Randomness campaign, 2026-08-08 (C157–C162): offset, noise, bias, correlation

The timing work above says whether the part moves bits correctly. This section is the first evidence
about whether the bits are **unpredictable**, which is what the part is for.

### Measured

| quantity | value | method |
|---|---|---|
| input-referred offset, σ | **11.79 mV** (mean −0.19, 90th pct \|offset\| 19.12) | MC mismatch, N=200, track-phase DC sweep; 1/200 failed the validity gate, excluded |
| offset attribution | **11.5 mV** sense-amp/latch/buffer chain, **2.7 mV** CML stage | second MC population with the CML held matched |
| trim efficacy | 1.002 mV input-referred per mV trim differential; range ±60 mV (5σ) | trim sweep at the operating point |
| trim resolution | 0.20 mV per step as drawn; 0.05 mV with 2 extra DAC bits | fine-trim bench |
| noise at comparator, σ_n | **3.246 mV rms** | `.noise`, band later characterised by `.ac` |
| noise band | −3 dB 15.8 MHz … 5.62 GHz, peak \|H\| 14.8 V/V @0.32 GHz, NEBW 8.0 GHz | `.ac` sweep |
| serial correlation ρ (800 ps) | **−0.0033** (independently reproduced: −0.004) | analytic from the `.ac` transfer, dense linear grid |

**Consistency check (independent, both chairs):** implied input density S = 6.12e-18 V²/Hz = 4kTR
with R = 278 Ω at 125 °C — a physical source resistance. √(S·NEBW·|H|²) = 3.253 mV against the
measured 3.246.

### Conclusions

- **Bias, not error rate, is the binding constraint.** Against the 121 mV test differential the
  offset is 10σ of headroom and harmless. Against σ_n = 3.25 mV — the correct yardstick, since in
  service the input is noise centred on zero — an *untrimmed* part gives P(one) ≈ 100%: dead-biased,
  not merely skewed. **Trim is mandatory.**
- **Trim resolution, not range, is the specification.** Required residual is σ_n/40 = **0.081 mV**
  for <1% imbalance. As drawn (0.20 mV) gives 2.45% — 2.5× outside. With 0.05 mV steps: 0.6% —
  inside, min-entropy 0.983 bits/bit.
- **Serial correlation is not a defect.** ρ ≈ −0.003 → P(repeat) ≈ 49.9%, indistinguishable from a
  fair coin. An earlier ρ = 0.102 was a log-grid aliasing artefact (see H-730) and is retracted,
  along with the "correlation dominates" conclusion built on it.
- **One-time calibration cannot work, by arithmetic rather than measurement.** The 0.081 mV budget is
  0.69% of the 11.8 mV offset; a part drifting 1% of its own offset yields 1.45% bias, 5% yields
  7.2%. Any plausible tempco over 165 °C is tens of percent — 30–70× over budget. Three attempts to
  measure the drift factor all failed (probe fighting the CMFB loop; forced-bias deck giving a
  non-physical 375× gain span; unseedable RNG preventing per-part tracking), and none of them matter.
- **The answer is a background servo**, not a tighter component: count the output ones/zeros and
  servo the trim to hold the ratio at ½. Sizing: N = 10,000 bits resolves 1% at 2σ (32,768 at 3σ),
  giving an 8–26 µs window against a 20–50 ms drift time at 1 °C/s — three orders of margin. It also
  absorbs ageing and supply drift, which no factory calibration can.

### Open

- **Servo hazards (raised, not yet analysed):** a loop that forces the ratio to ½ will do so even if
  the noise source dies, so **health monitoring must be independent of the servo** — repetition
  counts and raw pre-trim balance, not the corrected ratio. And the loop imprints a slow negative
  correlation at its own window scale; that must be shown to sit below the measurement floor.
- Metastability rate never calculated — and this circuit deliberately operates in the small-input
  regime other designs treat as the dangerous tail, so it is a first-order quantity here.
- No layout parasitics, no post-layout re-verification. Nothing fabricated.
