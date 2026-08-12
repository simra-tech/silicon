# Load-servo corner matrix — C148 (800 ps/bit) and C149 (400 ps/bit)

Public-experiment record, 2026-08-06 evening — 2026-08-07 morning. In simulation only
(IHP SG13G2 corner libs, ngspice). Nothing here is a signoff or a tape-out claim.

> **This file contains two investigations.** Lines 1-4077 are the 2026-08-06/07 load-servo corner
> matrix (C148/C149), the study this directory is named for. From line ~4078 onward it records a
> separate 2026-08-11/12 investigation into the **p-bit comparator's offset distribution and trim
> array**, appended here rather than in a new directory. If you are looking for the second study,
> start at **"FINAL SIZING RECOMMENDATION"** near the end -- that is the closing position. The
> **"STATE OF THIS INVESTIGATION"** sections before it are dated snapshots, superseded in order;
> read the last one only for the list of what was withdrawn and what remains unmeasured. The entries before it are chronological and
> include claims later retracted; the retractions sit beneath the claims rather than replacing them,
> so the reasoning stays auditable.
>
> Both studies are simulation only (IHP SG13G2, ngspice). Neither is a signoff or a tape-out claim.


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

## Trim architecture: C164–C166 (2026-08-09)

The randomness campaign specified a 0.05 mV input-referred trim step. Building it took four attempts,
each failing for a different and instructive reason. All measured in the working deck, arrival-gated.

| attempt | mechanism | worst step | range | verdict |
|---|---|---|---|---|
| C164 | extra DAC bits, independently referenced | 0.728 mV @125 °C | 121.6 → 3.9 mV | **96× step variation** across corners |
| C165 | ratiometric: trim pairs on the CML tail | 0.742 mV @−40 °C | 325.9 → 12.7 mV | 26× variation, range still collapses, **sign reverses** |
| — | fine trim by load imbalance | — | — | **not manufacturable**: 0.19% of 838 Ω = 1.6 Ω, needs a 434 kΩ tap or is swamped by switch R_on |
| C166 | **dithered LSB** | effective 0.00625 mV | unchanged | **works** |

**Why C164 failed:** the trim was referenced to an absolute quantity while the thing it corrects
scales with the stage's own bias, so the two drift apart. *Any correction referenced to something
absolute, when the thing corrected is not, will separate from it* — the third time this principle
decided an outcome (see also the CMFB loop and the one-time-calibration analysis).

**Why C165 fell short of its prediction:** the ratiometric arithmetic — input-referred step =
ΔI/g_m, and g_m = I_tail/V_T for a bipolar pair, so ΔI = k·I_tail gives step = k·V_T with only a
1.71× spread over −40…125 °C — is correct, but assumes the trim devices *share the tail as a
controlled fraction*. Measured, they sat at V_be ≈ 1.16 V, hard on and outside that regime. **The
arithmetic was right about a circuit that was not built.**

**Why the load-ratio idea died:** (ΔR/R)·V_T is exactly the right relation and depends on no bias
point at all, but at an 838 Ω load a 0.19% imbalance is 1.6 Ω — two orders below what an rppd tap or
a switch can resolve. Sound requirement, unmanufacturable at this impedance.

**C166, the solution — buy the resolution in digital:** keep the 0.2 mV physical LSB that *is*
buildable and toggle it with probability p from a 5-bit dither register. Effective offset = p·LSB,
resolution set by the register rather than by any physical dimension: **0.00625 mV effective step,
32× finer than the LSB**, from logic the servo already requires.

- Mean bias at p = 0.25: Φ(0.05/3.25) = 50.61% → **0.61%**, inside the 1% target.
- Steady-state residual (half p-step, 0.0031 mV): **0.038%** bias — 26× inside target.
  *(Reported as 0.055% by the DE; independently recomputed as 0.038%. Same order, does not change
  the conclusion, recorded for accuracy.)*
- It works because the servo already averages 32,768 bits — anything toggling faster than that
  window is seen only as its average, so the fine resolution is real from the loop's point of view.

**Requirement, not a detail — the dither must be RANDOM, not periodic.** A regular toggle puts a tone
at the dither rate into the output, precisely the structure certification tests hunt for. Quantified:
the dither's threshold jitter is LSB·√(p(1−p)) = 0.087 mV at p = 0.25, i.e. 2.7% of σ_n, raising the
effective noise to 3.2512 mV (+0.035%). Being a *random* component added to the threshold, it cannot
reduce per-bit entropy.

## Specification of the three additions (C166–C168, 2026-08-09)

Derived entirely by arithmetic from the measured properties above; **no simulation**. Every number
was computed independently by both chairs; the corrections that resulted are noted inline.

### 1. Offset trim — coarse/fine cascade

| element | value |
|---|---|
| structure | **(C, p)**: effective offset = (C + p) × 0.2 mV |
| coarse code C | ~10 bits, 0.2 mV per code, ±60 mV (±300 codes) — current-steering DAC |
| fine p | 5-bit **dither probability** over one LSB, 1/32 steps = 0.00625 mV effective |
| why dithered | a 0.05 mV physical step is unmanufacturable here (0.19% of 838 Ω = 1.6 Ω); the servo's 32,768-bit averaging converts digital duty-cycle into effective analogue resolution |
| dither requirement | **must be random, not periodic** — a periodic toggle puts a tone at the dither rate into the output. Jitter contributed: 0.087 mV = 2.7% of σ_n, raising effective σ_n to 3.2512 mV (+0.035%), entropy-neutral |

### 2. Bias servo

| element | value |
|---|---|
| window N | 32,768 bits = 26.2 µs at 1.25 GS/s (15-bit counter) |
| measurement σ | √(0.25/N) = 0.276% per window |
| error | e = count − 16,384; b = f − 0.5 |
| update | p ← clamp(p − g·b, 0, 31/32); **p railing steps C by ±1 and re-centres p** — normal tracking behaviour |
| loop gain | **g = 10.2**, giving dimensionless loop gain 0.25 (db/dp = 0.0245). *Originally specified as g = 0.25, which confuses bias-fraction with probability units and would have been 40× too slow — τ = 163 windows instead of 4.* |
| response | τ = 4 windows = 105 µs; 5τ = 0.52 ms, against drift of ~20 ms per 1% at 1 °C/s |
| settled residual | **0.105%** bias — loop-noise-dominated (per-update p noise 0.028 ≈ 0.9 p-step; steady-state wander 1.4 steps). *Not the 0.038% quantization figure: the loop noise dominates it.* |
| start-up | p = 0.5, output gated until one full window has been observed (26 µs) |

### 3. Health monitors — three independent channels

| channel | watches | alarm | why it survives audit |
|---|---|---|---|
| envelope detector | 1.8–2.2 GHz band at the comparator input | 0.34 mV rms (healthy 0.687) | spectral, so it separates thermal noise from clock-harmonic pickup; a 20 dB source loss lands 5× below the alarm |
| repetition count | P(repeat) over raw windows | 3σ = 50.83% (natural 49.9%) | the dither is white per bit, contributing ρ ≈ 0 — invisible to this statistic, as required |
| **coarse-code rail** | C pinned at 0 or 599, 4-window debounce | — | the total correction has run out of authority. *Replaces two rejected designs: a raw pre-trim balance channel (saturates at ~100% ones for every real part — cannot distinguish healthy from dead) and a p-rail alarm (p railing is normal coarse-step behaviour and would fire during ordinary tracking).* |

### Interaction audit (the composition check)

Each subsystem was specified against its own requirement; the audit asked what they do to each
other. Three pairs compatible with margin (dither vs repetition counts: ρ ≈ 0 against a 0.83%
alarm; dither vs envelope band: ~4 µV in-band against a 340 µV alarm, 85×; start-up: output gated
before monitors are asked to judge). **One pair failed** — see the coarse-code-rail row above.

**Three monitoring channels were designed and then found to alarm on the design's own intended
behaviour** (an amplitude detector that could not separate source from pickup; a balance channel
saturated by the imbalance it was meant to survive; an alarm on a control value that rails
routinely). Each was a reasonable design *considered alone*. The recurring lesson — after H-724's
empty intersection — is that **correctness of parts does not compose into correctness of wholes**,
and the check costs arithmetic against a design that does not yet exist.

**Still unbuilt:** none of this is drawn, simulated or laid out. The metastability rate remains
unmeasured (H-731). No layout parasitics anywhere.

### Behavioural verification of the servo — `servo_model.py`

The specification above was derived by arithmetic, with every parameter computed independently by
both chairs. It still contained a **sign error** that made the loop diverge: the correction
(C+p)·LSB *opposes* the offset, so a positive measured bias means more correction is needed, and the
originally specified `p ← p − g·b` applies less. Simulated, it rails within a few windows and sits
at 50% bias permanently. The corrected rule is **`p ← p + g·b`**, and the convention is now stated
explicitly in the spec so the polarity cannot be re-inferred: *correction opposes the offset;
positive b raises the correction.*

Running the model confirms the response time (first window under 1% at **window 23 = 0.6 ms**,
against the predicted 5τ of 0.52 ms) and revises the settled residual to **0.23%** — the analytic
0.105% omits the coarse/fine interaction with loop noise, so the simulated figure is the one of
record. Both remain inside the 1% target.

**Method note:** a sign error in feedback is the most consequential and least visible defect in
control design — every gain, time constant and threshold can be correct while the loop drives into
the rail. It survives inspection because a minus sign reads as a considered choice. Nothing catches
it except letting the design run. Forty lines, minutes to write, against a fabricated part whose
output would be stuck at one value in a block whose entire purpose is unpredictability.

**Final servo parameters after the coverage fix.** The fine control spans **8 coarse codes**
(1.6 mV) with **6-bit** dither, giving an unchanged 0.025 mV effective step and a **2.95×** coverage
margin over the worst measured coarse step. Loop gain rescales with the wider span:
db/dp = 0.194, so **g = 1.29** holds the dimensionless loop gain at 0.25. Acquisition **18 windows
(0.47 ms)**, settled bias **0.25%** (max 0.90%).

*Why 8 codes and not the 4 that satisfied the arithmetic:* the coverage condition is compared
against a worst coarse step of 0.543 mV taken from **C165, a build that was rejected** — the coarse
DAC is not designed yet, so that number is provisional, while coverage failure is permanent and
inescapable for an affected part. **Margin should scale with how well the number is known, not only
with how bad the failure is.** At 4 codes the check passed 0.800 against 0.798, ~1.5% of headroom on
a placeholder. The extra span costs one register bit.

`servo_model.py` now carries `coverage_check(coarse_step_mV)` as a **fail-loud assertion** taking the
coarse step as an input, so the condition is re-tested automatically when the coarse design lands
rather than being remembered by whoever happens to still be here. It also retains a **regression
case for the sign error** — a defect already found must not be able to return silently.

### Single-step correction, acquisition scaling, and the timeout — the last correction round

Both chairs' copies of `servo_model.py` were found to **slew the coarse code** — up to 6 steps in a
single window (mean 5.1 during acquisition) — while both specification and commentary described a
single-step loop. Neither noticed until the models were *instrumented* rather than read: the p update
can reach g·0.5 = 0.645 and each coarse step consumes 1/FINE_CODES = 0.125 of p, so ~5 steps per
window. **A property of the specification had been asserted as a property of the code, by both sides.**

A related error ran alongside it: acquisition was measured against the wrong σ. Two distinct
quantities in this design are both spread parameters — the noise at the comparator (3.25 mV) and the
part-to-part offset distribution (11.8 mV). Scaling a sweep by the first while meaning the second
gives internally consistent numbers about a part that does not exist.

**With single-stepping enforced (verified by instrumentation: max 1 C-step per window), acquisition
is simply the walk:**

| offset | codes | windows | time |
|---|---|---|---|
| 0.5σ (5.9 mV) | 29 | 29 | 0.77 ms |
| 1σ typical (11.8 mV) | 59 | 59 | 1.55 ms |
| 2σ (23.6 mV) | 118 | 118 | 3.09 ms |
| 3σ (35.4 mV) | 177 | 177 | 4.64 ms |
| 4σ (47.2 mV) | 236 | 229 measured | 6.18 ms |

**Consequence, which neither chair had drawn:** the previously agreed 100-window timeout covers
offsets only to 20 mV = 1.69σ, so **~9% of perfectly healthy parts would raise a fault at every
power-up** — the alarm-on-healthy-behaviour failure for the fourth time, this time inside a number
that had been *verified as safe* using acquisition times nobody knew were slewed.

**Timeout raised to 400 windows (10.5 ms)** — and justified by the *architectural* limit rather than
a statistical tail: the coarse code spans ±300 codes, so the longest possible walk is 300 windows
however the offset distribution turns out; anything beyond is uncorrectable and is caught by the
coarse-rail alarm. **400 = full coarse range + ⅓ margin.** A threshold justified by a statistical
tail must be revisited whenever the tail estimate moves — and 11.8 mV rests on one MC campaign with
one gate-failed sample. A threshold justified by the range moves only when the range does.

The two alarms are then complementary rather than overlapping: **the timeout catches a loop that is
walking but slow (something wrong with the loop); the coarse rail catches one out of authority
(something wrong with the part).**

**Slewing is recorded as a deferred optimisation**, not a bug: it acquires in ~55 windows instead of
229, but a coarse control that can accelerate is a second feedback loop and needs its own overshoot
and stability analysis before it is adopted.

## C169 — the coarse DAC, first build: a void measurement, and the check that will catch the next one

The coarse DAC was built to replace the **provisional** 0.543 mV worst-step figure (itself taken from
C165, a rejected build) that the coverage assertion depends on. The first build measured:

| corner | mean step | worst step | sign reversals |
|---|---|---|---|
| tt/typ/27 | −0.817 mV | 258.3 mV | 373 / 599 |
| ss/wcs/−40 | −0.668 mV | 223.5 mV | 428 / 599 |
| tt/typ/125 | −0.256 mV | 79.8 mV | 5 (only **10 of 599** steps nonzero) |

`coverage_check(258.3)` duly failed — the assertion working as designed, hours after being written.

**But all of it is VOID, and the numbers above must not be quoted as data.** Three symptoms had one
cause: the bench decoder read the sweep *voltage* as the code count (missing a ×100 scale), so
`floor(0.64 V / 64) = 0` — the code never advanced. That single fault explains the inverted direction
(mean step negative at every corner), the ~4× oversize implied full scale (−489 mV against a target
of +120), and the two-thirds-of-boundaries reversals. **A binary-weighted DAC can lose monotonicity
only at major carries — nine of them among 599 boundaries — so 373–428 reversals was never a
matching result.**

**Diagnostic that found it:** a coarse sweep every 64 codes, before any further corner work. The
transfer showed two populations — five points moving by hundreds of millivolts, five by microvolts —
which is not a transfer curve.

**Standing check adopted (see harness finding H-733):** *before characterising any converter, sweep
N codes and count the DISTINCT output levels; if it is not ≈N the decode is broken and nothing
downstream means anything.* The tell was already in the data — 10 nonzero steps across 599 codes,
which no 10-bit converter produces — and would have halted the run before two further corner sweeps,
a monotonicity analysis, and the coverage assertion being fed a number that was never real.

**Rebuild direction:** fix the decoder scale, then **thermometer-code the top bits** — unary segments
are monotonic by construction, which removes the failure mode rather than measuring it. The
distinct-levels check runs first, before any corner run or assertion.

**The worst-case coarse step therefore remains unmeasured**, and the coverage margin still rests on
the provisional 0.543 mV. That is the most load-bearing placeholder in the specification.

## C169 characterised — 2026-08-09, after three apparatus faults

The rebuild was measured. Getting a number out of it required removing three faults, none of which
were in the converter:

1. **The bench had no ground.** `VSS` was never tied to node `0` — no source, no `.global` — and was
   passed positionally into `XCOMP`/`XISO` as the ground port. Ground floated 795 mV above the
   reference the forced bias sources used; every segment sat at V_BE = −21.8 mV, cut off. The deck
   had been made to converge by relaxing `reltol` to 2e-2; a circuit with no ground is not stiff, it
   is singular. Caught by an impossible coincidence: seven segment emitters reading **794.769 mV
   identical to the microvolt** across seven degeneration resistors spanning m=1…64. See H-734.
2. **The comparator was permanently latched.** With balanced inputs (both 1.245 V) `c_p − c_n` read
   −1705 mV. The bench pinned `e_track` and `e_latch` — the tail nodes of the input pair and of the
   cross-coupled latch — with ideal sources, defeating `XQCLK_TRACK`/`XQCLK_LATCH` so the clock could
   not steer between track and latch. With those deleted, `e_latch` has **no DC path to ground** in
   the track phase, so the DC solution is latched regardless: `.op` is the wrong instrument for a
   regenerative block. Resolved by characterising the DAC standalone, with resistive loads and no
   comparator.
3. **Every switch had two terminals transposed.** The PDK declares `.subckt sg13_lv_nmos d g s b`;
   the instances read `XSWBN0 c_n vsegb0 b0 VSS` — gate on the segment node, source on the decoder
   bit. All fourteen HBT collectors were therefore open-circuit (a gate carries no DC current),
   which is why the current sat at the leakage floor from VREF 0.75 V to 1.10 V and never lifted.
   The 2 nA reported "equal weights" was the identical off-state leakage of fourteen identically
   sized switches.

**The measurement, once the apparatus was sound.** Transfer curve `v(c_n)` over codes 0–127, one
column (a seven-column print had been silently dropping columns). Excluding seven codes corrupted by
decoder floating-point, a **static seven-weight model fits the remaining 121 points to a max residual
of 0.0013 mV against a 0.1497 mV LSB — 0.9%.** There is no code-dependent interaction; the converter
is exactly a weighted sum, and the weights are simply wrong.

| bit | fitted weight (mV) | ratio to ideal 2^k |
| --- | --- | --- |
| b0 | 0.1497 | 1.000 |
| b1 | 0.3529 | 1.179 |
| b2 | 0.4825 | **0.806** |
| b3 | 1.2661 | 1.058 |
| b4 | 2.6096 | 1.090 |
| b5 | 4.9546 | 1.035 |
| b6 | 11.1719 | **1.166** |

Two entries account for every symptom: **b2 19% light** makes W2 − W1 − W0 = −0.0201 mV, which is all
14 clean reversals (every code ≡ 3 mod 8); **b6 17% heavy** makes W6 − Σbelow = 1.3565 mV, the
observed −1.356 mV worst step at 63→64.

**Cause is mismatch, and the design weights are correct.** With `mm_ok=0`: turn-on steps uniform at
0.154–0.155 mV, **0/127 reversals**, and range/(N−1) = 19.70/127 = **0.15512 mV**, matching the step
size from an independent direction to four digits.

**The obvious repair would have measured nothing.** `sg13g2_hbt_mod_mismatch.lib:49` sets
`qarea='agauss(1, 0.1, …)'` with **no `Nx` term** — a flat 10% area sigma regardless of device size.
Scaling `Nx` changes the mismatch by nothing. Area helps only through **replication**: 2^k parallel
`Nx=1` unit devices give 2^k independent draws with σ ∝ 1/√m, which is both what the model will show
and what the layout would do. See H-736.

**Architectural consequence — move the segmentation boundary.** The limiting step is the
**binary-to-unary handover**, where a unary element of 2^(k+1) LSB replaces a binary array summing to
2^(k+1) − 1: nominal margin exactly one LSB, variance u²·0.10²·(2^(k+2) − 1).

*(Corrected 2026-08-09. The first version of this table quoted the margin at the **internal binary**
boundary, 1/(0.1·√(2^(k+1) − 1)) — one row optimistic — and reported σ alone. σ is the wrong figure
of merit here: there are many handovers per part and the worst one decides, so the number that
matters is 1 − (1 − Φ(−margin))^n over n boundaries. A build had already been generated at b2 on the
strength of the wrong row.)*

| binary top bit | unary unit | margin at the handover | P(reversal) per boundary | boundaries | **P(any reversal per part)** |
| --- | --- | --- | --- | --- | --- |
| b0 | 2 LSB | 5.77σ | 3.9e-9 | 303 | ~0 |
| b1 | 4 LSB | 3.78σ | 7.9e-5 | 151 | **1.2%** |
| b2 | 8 LSB | 2.58σ | 4.9e-3 | 75 | 30.9% |
| b3 | 16 LSB | 1.80σ | 3.6e-2 | 37 | 74.5% |

C169 is binary to b6. The repair is not better matching but a boundary move to **b1 (4 LSB units,
151 elements, 1.2% escape) or b0 if 303 elements is affordable** — because the unary segments are **monotonic by construction**: each element need only be
positive, so mismatch there costs linearity and can never cost monotonicity, which is the one
property the bias servo cannot function without.

**Acceptance gate for the rebuild, stated before the run** (all three required): zero reversals on
**every** seed, not the best one; range/(codes−1) equal to the turn-on step to three digits; and a
static-weight fit with residual under 10% of an LSB.

**Still open.** The worst-case coarse step remains unmeasured for the *rebuilt* architecture, so the
`servo_model.py` coverage assertion still carries the provisional 0.543 mV from rejected build C165.
Under the b2 boundary the expected bound is ~1 LSB + 3σ ≈ 2.2 LSB ≈ 0.34 mV against a 1.6 mV fine
range, but that is a prediction, not a measurement, and the placeholder stays until it is one.

## C169 v5 — the steering element changed, and why (2026-08-09, later)

The b1-boundary rebuild produced no current at all. The chain that found it, in order, took four
minutes after eight hours of everything else:

1. **Diff before probe.** A version existed in which the b0 segment conducted 0.435 µA at VREF
   0.650. Placing its four lines beside the dead version's showed them equivalent in every
   meaningful parameter — so the fault was environmental, not in the description.
2. **Three voltages.** `v(ref)` = 0.6500, `v(vsegb0)` = 0.6215, `v(e_dacb0)` = 0.0008 →
   **V_BE = 649.2 mV** (fully asking to conduct) with **V_CE = 620.7 mV** (not saturated) and no
   current. The collector path was blocked: the switch.
3. **One subtraction.** The steering nmos gate is the 1 V logic rail; its *source* is the segment
   node at 0.62 V, so V_gs = 0.38 V — subthreshold. With V_th above 0.38 V (call it 0.45), the gate
   needs ~1.07 V merely to reach threshold and ~1.4 V for usable overdrive. **VDD is 1.2 V.**

**This is not a marginal design but one that does not fit its supply.** The distinction matters: a
marginal design improves when adjusted; a design whose requirement exceeds its rail does not improve
however it is adjusted, because the constraint violated is arithmetic rather than a performance
target. It would have failed across corners even had this draw scraped through.

**Resolution: HBT differential-pair steering** (`XQP<k>`/`XQN<k>`, bases on the decoder's
complementary outputs, emitters on the shared segment node) in place of the nmos pass switches. It
steers fully on a few hundred mV of differential swing, needs no level shifter, has no threshold to
be marginal about over temperature and supply, is faster with no gate capacitance in the signal
path, and matches the CML style the rest of the comparator already uses. The alternative — level
shifting the gate drive into the 2.5 V HBT domain, which this design already does for the output —
was rejected as more circuitry for a worse result.

**Three symptoms closed on that one change**: the 1045 µA steered to the wrong side, the segment that
would not conduct at a reference where it previously did, and the subthreshold switch. When several
symptoms resolve on one change, that is the strongest available evidence the diagnosis was right.

### First clean operating point, and the level

| figure | value |
| --- | --- |
| b0 pair current | 0.467 µA |
| array total | 305.8 µA |
| steering at code 0 | c_p 2.4127 V (87.3 mV drop), c_n 2.5000 V clean |
| **balance check** | 87.3 mV / 305.8 µA = **285.5 Ω** vs the independently known ~290 Ω |

The balance is the point: drop and current were not derived from each other and they agree to 2%.
The same check failed on every earlier state of this bench.

**Set the level from the total, not from a canary segment.** b0 is one device with 10% σ; the array
total averages 603 draws and has 0.41%. b0's 0.467 µA against the array mean of 0.5071 µA is a 0.8σ
low draw — ordinary, and not a calibration reference.

### Effective thermal voltage, measured

A −9.6 mV VREF move predicted a current ratio of 0.690 (assuming kT/q = 25.85 mV) and delivered
0.718. That miss is a measurement, not an annoyance. Correcting each point for its own degeneration
drop (0.728 mV and 0.522 mV):

    ΔV_BE = 9.395 mV for a current ratio of 0.718
    →  effective kT/q = 28.36 mV,  ideality n ≈ 1.10

Ordinary for SiGe at this current, and the reason the prediction undershot. **Use 28.4 mV for every
subsequent level move.** The residual to 0.3503 µA is then −1.116 mV → **VREF 0.6393**, one shot.

Not applied yet, deliberately: the LSB is 0.2078 mV against 0.200 (3.9% high), which is immaterial
to a servo that measures the real output and corrects — the fine dither spans eight coarse codes, so
a 4% LSB moves loop gain and nothing else. Measuring the escape rate ranked higher than a perfect
LSB.

### Monotonicity: count boundaries, not draws

Nine draws: eight clean, one with a single reversal; worst steps 1.00–1.76 LSB against the 1.66 LSB
predicted before the run. Reported first as "1/9 = 11%, ten times the 1.2% spec". **That reading is
wrong.** Each part contains 151 handover boundaries, so nine parts give **1359 independent
opportunities**, not nine:

| | |
| --- | --- |
| model rate | 7.85e-5 per boundary → expects **0.107** events |
| P(≥1 under the model) | **10.1%** — the observation is an ordinary draw *from* the arithmetic |
| 95% CI on a count of 1 | 0.025–5.57 events → 0.24×–52× the model, i.e. 0.3%–46% per part |

*The natural unit is the thing you ran; the informative unit is the thing that can independently
fail.* Recounting the same nine runs by opportunity multiplied the statistical power by 151, for
free. A 250-draw run (37,750 boundaries, model expects 3.0) is executing to settle it — three
confirms, thirty refutes.

### Gate corrections (both mine)

- **Gate scope**: three draws cannot distinguish a 1.2% escape rate from the 31% of the architecture
  it replaced (three clean draws happen 33% of the time at 31%). The gate checks the arithmetic's
  assumptions; it does not measure the rate.
- **Gate 2 retired for mismatch runs**: requiring range/(n−1) to equal the b0 turn-on step pits a
  603-sample average against a single 10% draw. Valid only with `mm_ok=0`; kept for the control run,
  with the static-fit residual carrying the load otherwise.

Two of the three conditions set in advance were corrected afterwards. That is not a failure of the
practice — stating them early is what made it possible to notice they were unsound.

## C169 v6 — the handover deficit, and the three repairs it took (2026-08-10)

The 250-draw run measured 11 reversals against a predicted 3.0. The excess was never a σ error and
never a heavy tail: **the model had the right spread and the wrong centre.** The handover step
averaged **0.868 LSB, not the 1.000 assumed**, which moves the margin from 3.94σ to 3.42σ and the
expected count from 1.5 to 11.8 — against 11 observed. A ratio assumed exact by construction (4 unary
units against 3 binary) was 4.4% off, and 4% in the centre moves the tail by a factor of eight.

**Three repairs were made chasing it. Only the third mattered.**

1. **Missing `m=4` on the unary degeneration** (generator line 35 wrote `m=1` for both arrays). A
   genuine defect, predicted from the emitter voltages before the grep confirmed it, fixed at the
   generator. The emitter ratio collapsed 3.69× → 0.92×. **It changed the current ratio by nothing:**
   rearranging as `emitter ratio = 4·(Ru/Rb)·x` gives x = 0.922 before and 0.920 after. *A genuine
   defect can be correctly diagnosed and properly repaired while the metric everyone cares about does
   not move.* State what should change, measure it, and credit a fix with nothing you have not seen.
2. **Trimming the binary 4.2% lighter** — proposed, then withdrawn. It compensates for an
   unidentified effect, which holds at 27 °C and drifts everywhere else.
3. **The steering pairs were all `Nx=1` while carrying 1, 2 or 4 units.** The unary pair therefore
   ran at 4× b0's current density, raising its V_BE by kT/q·ln4 = 39 mV, dropping the current
   source's collector by the same amount and costing ~8% of its current to the Early effect.

**The confirmation was already in a printout taken an hour earlier for another purpose:**
`vsegb0 = 0.3571 V` against `vsegu1 = 0.3217 V` — a **35.4 mV** gap against 39 mV predicted from
first principles. Scaling the pairs to Nx = 1/2/4 closed it to 2.1 mV and moved x from 0.920 to
1.033.

**Note on the rejected explanation.** A current-density asymmetry had been proposed and refuted:
the current-source devices each carry exactly one unit (unary element 1.4531 µA = 4.00 units across
four parallel devices = 0.3633 each, the same as b0's single device). That refutation was sound and
the conclusion drawn from it — that density was irrelevant here — was too broad. **Refuting a
mechanism in one place is not refuting the mechanism.**

### The overshoot is a design decision, not a residual

After the pair fix the handover step is `(1.5899 − 1.1541)/0.3847 = 1.133 LSB`, i.e. 13% heavy.
(The figure first reported as "the step" was the *pair sum*, 3.000 units — a different quantity.)

| handover step | margin | expected events / 37,750 |
| --- | --- | --- |
| 0.868 (before) | 3.42σ | 11.8 |
| 1.000 (nominal) | 3.94σ | 1.5 |
| **1.133 (v6, kept)** | **4.46σ** | **0.152** |
| 1.300 (deliberate option) | 5.12σ | 0.006 |

**Do not trim the overshoot out.** A deliberately heavy unary element is the standard segmented-DAC
move: it converts a symmetric risk — a step that may land either side of zero — into an asymmetric
one where every step is positive but slightly uneven. Cost: 0.133 LSB DNL per handover, ~0.10 LSB
peak INL, full scale 124.6 mV instead of 120.6. **A servo that measures its own output sees none of
it.** Textbook figures of merit for a converter include step evenness; this converter drives nothing
that looks at its steps. When two quantities trade and only one matters, the design point is not the
balanced one.

### Deferred numbers rot

The queued level trim of **VREF 0.6393** was computed when b0 drew 0.3641 µA. After the `m=4` and
pair-Nx repairs b0 draws 0.3847 µA (+5.7%), and the correct trim is **−2.709 mV → VREF 0.6377**.
Applying the queued value would have left the level 4% off in the wrong direction.

**Rule adopted: any deferred number is recomputed at the moment it is applied, never carried
forward.** A number carries an invisible attachment to the state of the world when it was produced,
and that attachment does not travel with it into a queue. Of three items pending, the two that were
*procedures* remained valid and the one that was a *value* had rotted — **instructions age well,
numbers age badly.** Prefer recording the procedure over the answer wherever both are possible.

The trim is in any case optional: LSB 0.2197 mV against 0.200 (9.8% high), full scale 132.5 mV
against a 120 mV spec — more range than required, and invisible to the loop.

## C169 v7 — the fix that loaded the node it was fixing (2026-08-10)

**The range problem, found on paper.** The DAC exists to cancel the comparator's offset, and it had
never been connected to it. The comparator's tail current is derivable from the source without any
bench: `XRDEG_P1_COMP` 41.2 Ω, `XRPTAT_COMP` 161.4 Ω, `XRDEG_SCOMP` 6.9 Ω, so the PTAT reference is
Vt·ln4/(R2−R1) = 35.8 mV/120.2 Ω = **298 µA**, and R1/RS = 6.00 against Nx = 6 makes a cleanly
scaled 1:6 mirror — **tail 1.79 mA**. Hence gm = I_T/2Vt = 34.6 mA/V and the input-referred trim
range is I_FS/gm = **±6.7 mV against an offset σ of 11.79 mV — 0.57σ, only 43% of parts reachable.
A 5.3× shortfall.** (An earlier threshold of 678 µA was 2× optimistic: it used 2·I_FS as the
one-sided range. The correct figure is 339 µA.) Independent support: 1.79 mA through the 285 Ω loads
puts c_p/c_n ~255 mV below VCC_HBT, a sensible CML point.

**The levers, and one blind alley.**

- **Blind alley — do not degenerate the input pair.** The dominant offset originates *downstream* of
  the comparator gain, and so does the trim. Reducing gm scales the input-referred offset and the
  input-referred trim range by the same factor: **the ratio is invariant.** *Before adjusting a gain
  to fix a ratio, check whether both numbers in the ratio move with it.*
- **Lever 1 — the load resistance.** At c_p/c_n the trim range is I_FS·R while the sense-amp's own
  offset is independent of R, so R trades against I_T at constant gain and constant DC drop
  (338 µA / 1510 Ω closes the 5.3×). Cost: bandwidth.
- **Lever 2, probably cheapest — the offset's source.** 11.5 of the 11.79 mV is the sense-amp chain,
  not the comparator. Halving it halves the requirement, and attacks the cause.

**Lever 1 is dead, killed by a cost of our own earlier fix.** Every steering pair puts one collector
on c_p and one on c_n. From the HBT model, collector-node capacitance (cjc + cbco + cjcp) is 2.48 fF
at Nx=1 and 8.45 fF at Nx=4, so 150 unary pairs give **379 fF per node before the pair-Nx scaling
and 1275 fF after — 3.4×, spent to fix an 8% current error.** The comparator's own devices there are
tens of fF: **the trim DAC came to dominate the electrical behaviour of the node it exists to
correct.** Poles: 438 MHz at 285 Ω (τ = 363 ps against a 1000 ps bit period), **83 MHz at lever 1's
1510 Ω — unusable.**

> **Why it hid.** The DAC was measured all evening in a deck of its own, deliberately, because
> isolation made it fast to test and easy to reason about. Isolation is exactly the condition under
> which loading effects vanish — there is nothing left to load. Every property established in
> isolation was real; the one property that only exists in company was invisible by construction.

**v7 — the synthesis.** Revert the pairs to Nx=1 (recovering 379 fF and a ~1.5 GHz pole) and correct
the 8% by widening the **unary current sources** instead. Their collectors sit on `vsegu`, an
internal node, so the correction costs nothing on c_p/c_n.

This is compensation, rejected earlier in almost identical words. **The rule that separates the two
cases: compensate a mechanism you have characterised, never one you have not.** Because the
mechanism is now known — the pair's V_BE difference is kT/q·ln4, proportional to absolute
temperature — its drift is computable rather than feared:

| | kT/q | ΔV_BE | Early loss |
| --- | --- | --- | --- |
| −40 °C | 20.09 mV | 27.9 mV | 6.2% |
| +27 °C | 25.86 mV | 35.9 mV | 8.0% |
| +125 °C | 34.31 mV | 47.6 mV | 10.6% |

A fixed 8% compensation leaves **−2.6% to +1.8%** across the range — 3× better than the 8% removed,
everywhere, and well inside the trim's budget.

**Result, and a correction of the report.** v7 measured x = I_u/(4·I_b) = 1.0246, reported as a
"2.5% residual". Worked through, the handover step is 4x − 3 = **1.098 LSB → 4.33σ → 0.28 expected
events**, against **4.06σ / 0.94** for the pair-enlarged build. **v7 improves monotonicity *and*
recovers the capacitance.** The 2.5% is the deliberate overshoot working, not an error to remove.

**But the tuning was fitted to one draw** — the third appearance of the canary-vs-total error, and
the first inside a tuning loop. On a single draw x carries σ = √(0.10² + 0.05²) = **11.2%** (I_b is
one device, I_u is four in parallel), so 1.0246 from one `.op` is 1.02 ± 0.11 — indistinguishable
from 1.00 and from 1.13. The 1.08 → 1.032 width move was real in *direction*; the landing point was
one sample's mismatch. Re-tune against the 250-draw ensemble mean (uncertainty 0.71%), targeting
**1.03, not 1.00**.

**Still owed before any of this is settled:** measure the c_p/c_n capacitance and settling on the
rebuilt comparator bench — the pole arithmetic is model-derived, and the comparator bench itself is
still the broken one (latched, five forced bias nodes).

---

## Correction (2026-08-10) — every mismatch figure in this package was measured with resistor mismatch disabled

**What was found.** Every deck in this lineage selects two corner blocks:

```
.lib .../cornerHBT.lib hbt_typ_mismatch     <- transistor mismatch ON
.lib .../cornerRES.lib res_typ              <- resistor mismatch OFF
```

`res_typ` (cornerRES.lib lines 19–37) sets `drsh_rppd = dl_rppd = dw_rppd = 0.0` and includes the
plain `resistors_mod.lib`. The block that enables it is **`res_typ_mismatch`**, which supplies
`rsh_rppd_mm = 2.0 %·µm`, `dl_rppd_mm = dw_rppd_mm = 6 nm` and includes
`resistors_mod_mismatch.lib`. No run behind any number in this document contained a resistor that
differed from its neighbour.

**Why it went unnoticed for the whole exercise.** The two device families are switched at *different
levels*. For HBTs, mismatch is gated per instance by `mm_ok`, and `mm_ok=1` is written on
essentially every device in the netlists. **For `rppd`, `mm_ok` is a no-op** — it appears only in the
subcircuit's `.param` default line and nowhere in the `NR1` model card. The switch is the corner
block one file higher. So every resistor carries a marking that reads *mismatch enabled* while being
perfectly matched, which is the most persuasive possible form of the fault.

**Measured effect on the comparator** (5 draws each, same protocol, gate at 7.450 ns):

| configuration | sample σ (collector) | input-referred (gain 8.17) |
|---|---|---|
| HBT mismatch only (`res_typ`) | 18.46 mV | **2.26 mV** |
| HBT + resistor mismatch (`res_typ_mismatch`) | 29.65 mV | **3.63 mV** |

The implied resistor term is √(3.63² − 2.26²) = **2.84 mV** input-referred — larger than the
loads-only hand estimate of 0.87 mV (27 °C) / 1.15 mV (125 °C), because the corner switch mismatches
the *entire* `rppd` set at once: the pair loads, `XRDEG_SCOMP`, `XRPTAT_COMP`, the `g_p`/`g_n`
divider, the CMFB sense pair, and the DAC degeneration resistors. **At 5 + 5 draws the increase is
11.19 ± 12.35 gate-mV and the 95% interval includes zero — the direction is established by the
mechanism, the magnitude is not yet significant.**

**Consequence for the figures in this document.** Every mismatch-derived number above — the handover
σ, the per-boundary reversal probabilities, the 4.33σ / 4.06σ margins, the "0.20% of parts affected
against a 1.2% spec", and the 250-draw validation (σ 0.2569 measured vs 0.2538 modelled) — was
computed on a bench where the unit-cell degeneration resistors could not vary. Those resistors are
`rppd w=1.0 µm l=5.4 µm`, giving

```
rsh term  2.0 / sqrt(1.0 x 5.4) = 0.861 %
dl  term  0.006 / 5.4           = 0.111 %
dw  term  0.006 / 1.0           = 0.600 %
                        total     1.055 % per device (1 sigma)
```

and they sit **directly in the current-setting path** of every unit cell, so the mapping into weight
error is close to one-for-one rather than attenuated. The model's agreement with the 250-draw
ensemble is not evidence against this: the model was built from the same HBT-only physics the bench
simulated, so both are short the same term and agree with each other.

**Status.** The C169 v7 build (`6ac3acf0`) remains the selected variant — nothing here changes the
ranking of the alternatives, all of which were compared under the same omission. **But its margin
figures are provisional, not frozen, until the 250-draw ensemble is re-run under
`res_typ_mismatch`.** The direction of the correction is known and unfavourable: σ can only grow, so
the margins can only shrink and the escape rate can only rise. It is stated here rather than left
implicit because a margin on record is read as a margin measured.

**Rule this earns.** *A per-instance mismatch flag is not evidence that mismatch is enabled.* Verify
enablement by measuring it: run two draws and confirm the quantity actually moves. Every device
family in a PDK may switch at a different level, and the one that silently does nothing is the one
written most consistently.

## Correction, second part (2026-08-10) — MOS mismatch has never been enabled in any deck in this repository

The resistor finding above has a third instance, and it reaches the dominant term in the offset
budget.

**File evidence (certain).**

- `cornerMOSlv.lib` / `cornerMOShv.lib` block **`mos_tt`** includes `sg13g2_moslv_mod.lib`, which
  contains **zero `agauss` calls**. The enabling block is **`mos_tt_mismatch`**, which includes
  `sg13g2_moslv_mismatch.lib` + `sg13g2_moslv_mod_mismatch.lib` — 48 `agauss` calls, gated by
  `mm_ok`, including the one that matters: `delvto = agauss(0, delvto_mm/sqrt(m·l·w·1e12), …)`.
- **`mm_ok` on a MOS instance is a no-op under `mos_tt`**, exactly as on an `rppd` under `res_typ`.
  This is now the *third* device family found switching at the corner-block level while carrying a
  per-instance flag that reads as enabled.
- Across the whole design repository: **423 decks select `mos_tt`, 30 select `mos_ss`, 19 select
  `mos_ff`, and none selects any `_mismatch` MOS block.**

**Scale of the omitted term.** `sg13g2_lv_nmos_delvto_mm = 0.0039 V·µm`. For the sense-amp input pair
`XSA1/XSA2` at `w = 2.0 µm, l = 0.13 µm, m = 1`:

```
sigma(Vth) = 0.0039 / sqrt(0.13 x 2.0) = 7.65 mV per device
differential                            = 10.8 mV
```

That is threshold mismatch on the pair that makes the decision, and it has never been drawn.

**The open question, stated as open.** The table above records **σ = 11.79 mV** input-referred from
an *MC mismatch, N = 200* campaign (2026-08-08), and attributes **11.5 mV of it to the
sense-amp/latch/buffer chain** — which is CMOS. Those two statements are hard to hold together with
the file evidence: if that campaign selected `mos_tt` like the other 423 decks, the chain's devices
could not vary, and the attribution cannot be what it says. Either

- the campaign used a deck that enabled MOS mismatch by some route not present in the current
  netlists — in which case 11.79 stands and only everything *since* is incomplete; or
- it did not — in which case **the dominant term of the offset budget has never been measured**, the
  11.5 mV attribution is misassigned, and the trim-range shortfall (currently 5.3×) is sized against
  a number of unknown accuracy.

**This is not yet resolved and is not being asserted either way.** The check is one `grep` of that
campaign deck's `.lib` lines and it has been requested. Recording the question here because the
trim-range analysis later in this document consumes the 11.79 mV as an input, and a reader sizing
the trim needs to know that its provenance is under review.

**Immediate consequence for live work.** Both MOS corners must be switched to `_mismatch` before any
offset number from this bench is used for a design decision. Note that this cannot be verified by
inspecting the netlist — every instance already says `mm_ok=1`.

### Resolved, same day — the N=200 campaign ran with MOS and resistor mismatch off

The open question above is closed, from the archive rather than by re-running.
`designs/p1-pbit/comparator/run/offset-mismatch-n200/` holds the campaign, and its decks select:

```
204 x cornerHBT.lib   hbt_typ_mismatch     <- HBT mismatch ON
203 x cornerMOSlv.lib mos_tt               <- MOS mismatch OFF
203 x cornerMOShv.lib mos_tt               <- MOS mismatch OFF
203 x cornerRES.lib   res_typ              <- resistor mismatch OFF
```

**The second branch is the case: σ = 11.79 mV was produced by HBT mismatch alone.** Two consequences,
and the first is the more surprising:

1. **The attribution is mislabelled.** "11.5 mV sense-amp/latch/buffer chain" cannot be CMOS device
   mismatch, because across all 200 draws **every CMOS device was identical**. The partition was
   real — holding the input pair matched did move 11.5 mV of variance elsewhere — but the devices
   that were varying in that "elsewhere" bucket are **HBTs**: the bias block (`XQS_COMP`, the PTAT
   pair `XQP1/XQP2_COMP`), the clock devices, and the emitter followers `XQEF1/XQEF2`. A tail-current
   shift from bias mismatch moves the whole chain's decision point, which is a plausible route to a
   term that large and is *not* what the label directs a reader to.

2. **The CMOS term is additional and still unmeasured.** The 10.8 mV differential threshold mismatch
   on `XSA1/XSA2` computed above sits **on top of** whatever the 11.5 mV actually is, not inside it.

**Consequence for the trim-range work.** Lever 2 of the shortfall analysis — *"reduce the offset at
source: 11.5 of the 11.79 mV is the sense-amp chain"* — is aimed at devices that were held identical
in the measurement that motivated it. The lever may still be sound, but **its target must be
re-derived** from a partition run with all three families enabled before any effort is spent
re-sizing the sense amp. The 5.3× trim shortfall itself is unchanged in character; what changes is
*which* devices to attack to close it.

**Rule.** *An attribution is only as good as the set of things that were allowed to vary.* A
variance partition names the bucket that moved, not the mechanism inside it, and the label attached
afterwards is a hypothesis. Record which families were enabled alongside every attribution, or the
label outlives the conditions that produced it — which is H-740 (instructions age well, numbers age
badly) applied to a *name* rather than a number.

### Guard — the two margins in this document are in different units and are not interchangeable

This document reports two families of "σ margin" and they were conflated once (2026-08-10), so the
distinction is recorded explicitly:

| | **handover margin** | **trim-reach margin** |
|---|---|---|
| question | is the converter monotonic? | can the trim correct this part? |
| units | **LSB** | **mV** |
| formula | handover step (LSB) / σ_handover (LSB) | trim range (mV) / σ_offset (mV) |
| current value | 1.098 / 0.2538 = **4.33σ** | 6.7 / σ_offset |
| failure it counts | a reversed step at a binary→unary boundary | a part the trim cannot reach |

**They share no term.** Multiplying a handover margin by an offset σ to recover a "correctable
range", or dividing such a range by a new offset σ to obtain a new handover margin, is not a defined
operation — both quantities change meaning halfway through. The 4.33σ says nothing about millivolts
and the trim reach says nothing about monotonicity.

**The free check that catches this class of error.** *Enabling additional mismatch sources cannot
improve a margin.* Any recompute that adds resistor and MOS variation and returns a **larger** σ
margin than before has gone wrong somewhere upstream of its arithmetic, and no amount of checking the
arithmetic will find it. Apply the monotonicity test to the result before reading the number:
more variation ⇒ σ up ⇒ margin down, always.

**The correct recompute for the handover margin** is the DAC ensemble re-run under
`res_typ_mismatch` so the unit-cell degeneration resistors vary, giving σ_handover in LSB against the
unchanged 1.098 LSB step. σ_handover can only grow from 0.2538, so the margin can only fall from
4.33σ. That number is still owed.

## The trim-range shortfall is architectural, not a sizing problem (2026-08-10)

Derived on paper while the handover recompute was in flight. **It does not depend on the pending
σ, and every plausible value of that σ makes it worse** — so the design question is open now.

**Assumptions, stated.** Correction range for a bipolar pair at balance, with the DAC steering a
one-sided full-scale current `I_FS` into a collector:

```
V_range = 2 . V_T . I_FS / I_T          V_T = 25.86 mV (27 C), I_T = 1.79 mA (derived)
```

**Where the present design sits.** The measured range of ±6.7 mV implies

```
I_FS = 6.7 x 1.79 / (2 x 25.86) = 0.232 mA  =  13.0 % of the tail
```

**What coverage costs.**

| target | range needed | I_FS | % of tail | scale-up |
|---|---|---|---|---|
| 99 % of parts at σ = 11.79 mV | ±30.4 mV | 1.05 mA | 59 % | **4.5×** |
| 99.9 % at σ = 11.79 mV | ±38.8 mV | 1.34 mA | 75 % | **5.8×** |
| 99 % at σ = 15 mV | ±38.6 mV | 1.34 mA | 75 % | **5.8×** |

**Why scaling the array cannot deliver it.** The DAC's contribution to `c_p`/`c_n` scales with its
full-scale current, and **`c_p`/`c_n` capacitance is already the binding constraint on the design** —
it is what killed the pair-enlargement lever at a mere **3.4×** increase (379 → 1275 fF, pole at
438 MHz). A 4.5–5.8× scale-up fails for the identical reason with a larger factor. The two
constraints are independent and neither alone forbids anything; **together they close the route
completely.**

**Consequence.** The correction cannot stay on `c_p`/`c_n`. Closing the shortfall requires injecting
the correction at a node that is **not** bandwidth-critical, which is a change of arrangement rather
than a change of dimensions. Candidate directions, none yet assessed: trim on the tail/emitter side
rather than the collectors; trim further down the chain where the node is slower; or move the
correction out of the analogue path entirely and let the servo carry more of it.

**Status of the two earlier levers.** Lever 1 (load R traded against I_T at constant gain) was
already closed by the same capacitance wall. **Lever 2 (reduce the offset at source) is now known to
have been aimed at devices that were held identical in the measurement that motivated it** — see the
attribution correction above — so it must be re-derived before it can be costed. Lever 3 (more
segments) is a resolution lever, not a range lever, and does not address this at all.

### Handover recompute — resolved: the margin is not broken, the measurement was

The recompute first came back as a **collapse**: σ_handover 0.2688 → 1.2111 mV (4.5×), margin
4.33σ → **0.96σ**, with 94% of the variance attributed to the unit-cell degeneration resistors that
had never drawn. Both figures are **retracted**. What happened:

**The physics check that stopped it.** For a degenerated current source the mismatch splits by where
the voltage sits:

```
HBT term   = V_T . ln(1.1) / (V_T + V_R)   = 2.47 mV / (25.9 + V_R)
resistor   = (dR/R) . V_R / (V_T + V_R)    = 0.01055 . V_R / (25.9 + V_R)
ratio res/HBT = V_R / 234 mV
```

For the resistors to carry 94% of the variance, `V_R ≈ 925 mV` is required across each unit-cell
degeneration. **Measured: `v(e_dacb1) = 0.967 mV`, `v(e_dacb0) = 0.68 mV`** — the cell carries
≈0.7 µA, not the ~2.9 µA assumed in the first estimate. Resistor share of the step variance is
`(0.967/234)²` ≈ **0.0017%**. The unit-cell degenerations are very nearly irrelevant to the handover;
they provide almost no degeneration at all at these currents.

*(The estimate that raised the objection said ~4 mV and was itself 4× high — it assumed a 4-LSB unary
unit. The conclusion held with more room than claimed, not less.)*

**What the 4.5× actually was.** The run measured `c_n − c_p` at code 0 — a **level**, not the
boundary **step**. A level carries every common-mode term in the circuit, including the comparator
load resistors `XRC1/XRC2` (2.38%/device, 3.36% differential), which began drawing for the first time
in that same run: 3.36% of the 66 mV level ≈ 2.2 mV, the right magnitude for the observed growth.
**The step at the boundary cancels all of it.**

**Status.** The 4.33σ handover margin **stands**, pending the correct measurement — `code 1 − code 0`
at the b1 boundary over the same 250 draws. The load resistors' 3.36% differential is real and does
belong in the `c_p`/`c_n` **level** budget, which is the trim-range question, not the monotonicity
question.

**Rule.** *If the quantity of interest is a difference, measure it as a difference.* Never let a
level stand in for a step: a level is contaminated by every device the step cancels, and the
contaminating devices are typically the largest in the circuit.

### WITHDRAWN — every σ measured from `gate@7.450 ns` is compressed

**All offset σ figures reported in the corrections above are withdrawn**, including the
`2.26 → 3.63 → 4.742 mV` progression and the gate-level `47.7 / 35.4 / 42.7 / 38.7 mV`. The metric
they came from saturates.

A nine-point input sweep on the comparator gives:

```
dV_in (mV)  -20    -15    -10    -5     0      +5     +10    +15    +20
gate (mV)  -168.3 -158.1 -47.2  -7.6  -16.5  +22.0  +43.3 +161.9 +171.2
```

Floor ≈ −160 mV, ceiling ≈ +170 mV, **linear only within roughly ±10 mV of input**. The draws being
measured span well beyond that, so the observable compresses the tail of the offset distribution by a
draw-dependent factor. This is why σ *fell* when mismatch sources were added: more draws pushed into
the flat region.

**The same sweep also questions the referral gain.** From −10 to +10 mV the gate moves −47.2 to
+43.3 — a slope near **4.5**, against the **8.17** used to refer every gate σ to the input. Both the
compression and the referral factor are therefore in doubt, in the same direction of unreliability.

**What replaces it.** The **flip point** — the input differential at which the decision changes —
which is linear in the offset by construction and indifferent to how hard the output saturates
afterwards. Measured with the whole input staircase inside a *single* ngspice run per draw, so that
every point on a curve belongs to the same drawn chip (the RNG draws once at netlist expansion).

**What still stands.** The *structural* findings are unaffected, because none of them depends on the
magnitude of a compressed σ: that resistor and MOS mismatch were disabled in every deck; that
`mm_ok` is a no-op for `rppd` and MOS; that the 11.79 mV attribution names devices that could not
vary; that the trim range is short by 4.5–5.8× against the capacitance wall. The handover margin is
unaffected — it is measured from the DAC step, not from this metric.

### The coarse DAC's resolution is redundant with the dither — a lever, and the measurement that decides it

Found while landing the servo-model correction (2026-08-10).

**The observation.** With the input-referred LSB, the two resolutions are numerically identical:

```
coarse LSB                 = 0.2078 / 8.17            = 0.0254 mV
dither effective resolution = DITHER_SPAN_MV / 64      = 1.63 / 64 = 0.0255 mV
```

The coarse step has been made *exactly* as fine as the dither's own 6-bit granularity. That is
redundant work: **the dither sets the trim resolution at `span/64` regardless of the LSB.** The only
constraint the LSB must satisfy is this package's own coverage rule, `fine span ≥ 2 × worst coarse
step`, with the worst step at `1 + 5σ_handover = 2.33 LSB`. That permits

```
LSB_max = 1.63 / (2 x 2.33) = 0.3505 mV input-referred  =  13.8x today's LSB
```

**What that buys in code count.** At `LSB_max`, the range needed for 99% coverage at σ = 11.79 mV
(±30.4 mV) requires **87 codes**. Today's design spends **300 codes to buy ±7.63 mV** — a quarter of
the range for 3.4× the codes.

**The caveat, which is load-bearing.** Range in millivolts comes from `I_FS`, **not** from the code
count: `V_range = 2·V_T·I_FS/I_T`. So this is *not* a free 4× in range. It is **4× the full-scale
current carried by 3.4× fewer unit cells.**

**Therefore the whole lever reduces to one measurable question:**

> Does the DAC's contribution to `c_p`/`c_n` scale with **total current** (device area), or with
> **cell count** (per-cell fixed overhead — routing, cascode, junction perimeter)?

- *Current-dominated* → the lever is dead, 4× the current is 4× the capacitance, and the wall that
  killed the 3.4× pair enlargement kills this too.
- *Count-dominated* → 87 large cells at 4× the current may cost **less** capacitance than 300 small
  ones, and this is the first candidate all night with a chance of breaking that wall.

The measurement is a netlist question, not a campaign: extract the DAC's share of `c_p`/`c_n` and
split it into a per-cell constant and an area-proportional term. **Recorded before the answer is
known, so that a dead lever is buried with its reason rather than re-proposed.**

#### Costed and dead — with the number worth keeping

The lever above resolves **against**, and it can be buried without the layout extraction.

The two archived collector-side capacitance points (`cjc+cbc+cjcp`, per cell) give the
fixed-versus-area split directly:

```
Nx = 1 : 2.48 fF        fit  C(Nx) = 0.49 + 1.99 * Nx  fF
Nx = 4 : 8.45 fF        device-level FIXED term = 0.49 fF = 20% of a unit cell
```

Junction capacitance therefore tracks **area**, i.e. current, with only a fifth of a unit cell's C
sitting in a per-cell constant. Costing 4× range over 87 cells (each `Nx = 4·300/87 = 13.8`):

| build | node C |
|---|---|
| today, 300 unit cells | **744 fF** |
| 4× current spread over 1200 unit cells | 2976 fF |
| 4× current consolidated into 87 large cells | **2431 fF** |

Consolidation saves **18%** against the naive spread — real, and irrelevant: the net cost against
today is **3.27×**, not the 4× a pure area scaling would give, and 3.27× is still well past the wall
that killed the 3.4× pair enlargement at 438 MHz.

For per-cell **routing** overhead to rescue this, it would have to exceed **27 fF per cell** — the
area term at `Nx = 13.8`. That is not plausible for local interconnect inside an array, so the
layout-extraction path is not worth opening for this question.

**Keep the 0.49 fF fixed term.** It is the number anyone will want the next time consolidating cells
is proposed, and it says the answer in advance: consolidation buys ~20% at best, because 80% of a
unit cell's collector capacitance is area that has to exist to carry the current.

*(Caution recorded with it: an intermediate costing of "87 cells at Nx=4 ≈ 735 fF vs today's 744 fF"
appeared to show the lever working. It compares 348 unit-currents against 300 — a 1.16× build, not
the 4× one. When a capacitance comparison looks free, check that both sides carry the same current.)*

### Handover margin measured — but on the pre-v7 array. The 4.33σ is still unverified.

The corrected step campaign (code 127→128, correct scale, `n = 250`, all runs clean) gives

```
sigma_step = 0.0693 mV      mean_step = -1.1004 mV
margin     = 1.098 x 0.2078 / 0.0693 = 3.29 sigma        (package quotes 4.33)
```

**But the deck it ran on is not the frozen build.** `C169-SOURCE-coarse-dac.spice` still carries
`XQU1..7 @ Nx=128` and `XQB0..6 @ Nx=1..64`, and contains **no v7 compensation of any kind** — no
1.037 µm width, no compensation devices. The v7 rebuild (`6ac3acf0`) has never been merged back into
the source deck, an item outstanding since the morning of 2026-08-10. It is now the thing blocking
the verdict.

**The step's mean confirms the diagnosis rather than raising a new question.** At the b7 handover the
step is `128x − 127` LSB, with `x` the unary-to-binary current ratio:

```
measured  |−1.1004 mV| / 0.2078 = 5.295 LSB   ->  x = 1.0336   (3.4% ratio error)
v7 ideal   1.098 LSB                          ->  x = 1.0008   (0.08%)
```

So the deck sits ~3.3% off on **exactly the ratio the v7 compensation exists to set**, while
containing no compensation. *(The sign is convention: every code step is negative on this node, so a
negative handover step is a step in the same direction, 5.3× a normal one.)*

**Status of the three numbers.**

| figure | what it describes | standing |
|---|---|---|
| 0.96σ | contaminated *level* measurement | **dead** — artefact (loads, see above) |
| **3.29σ** | the **pre-v7, uncompensated** array | **valid, correctly labelled** |
| 4.33σ | the frozen v7 build | **unverified** — needs the merge first |

Keep the 3.29σ: it is the first correctly-measured handover margin in this lineage, and it is the
baseline the compensation has to beat.

#### Correction, same session — the 3.29σ label above is wrong, and the deck is a different architecture

The section immediately above labels 3.29σ as *"the pre-v7, uncompensated array — valid, correctly
labelled."* **That is wrong on both counts**, and the deck is further from v7 than "missing the
compensation" suggests.

**The deck is not a stale v7. It is a different segmentation.**

| | campaign deck | frozen v5/v7 |
|---|---|---|
| segments at | **b7** | **b1** |
| unary elements | 7 × `Nx=128` | 150 × 4 LSB |
| binary units | 7 (`Nx=1..64`) | 2 |
| codes | 1023 | 603 |
| **handovers per part** | **7** | **151** |

The frozen architecture is the one `servo_model.py` documents and the one
`HANDOVER_SIGMA_LSB = 0.265` was measured on. Two generations apart, not one merge.

**So 3.29σ belongs to neither build.** It divides v7's ideal step (1.098 LSB — a *b1*-boundary
quantity) by this deck's σ (a *b7*-boundary quantity). The deck's own margin is its own step over its
own σ:

```
5.295 LSB / 0.3335 LSB = 15.9 sigma
```

— large precisely because it overshoots by 5.3 LSB, and overshoot is what buys monotonicity.

**Exposure differs too, and it is not a detail.** Per-part reversal risk goes as the number of
boundaries: **151 against 7 is a factor of 21** before any margin is compared. Two builds with equal
per-boundary margins have very different per-part rates.

**What the campaign did establish, and it is worth keeping:** a clean handover σ of **0.3335 LSB** at
the b7 boundary, `n = 250`, correct scale, all three mismatch families enabled — the first such
measurement in this lineage. It is not a v7 number and **no arithmetic converts it into one.**

**Rule (this is its third appearance today).** *A margin is a ratio between two quantities that must
come from the same build.* Mixing an ideal from one architecture with a σ from another produces a
number that looks like a margin, sits in the right units, and describes nothing — the same failure as
the LSB-σ × mV-σ conflation (H-750) and the level-for-step substitution (H-752).

### The trim verdict, pre-committed before the measurement (2026-08-10)

The architectural verdict recorded above rests on **σ = 11.79 mV**, which is now known to be
HBT-mismatch-only, DC-protocol, and measured on a different comparator deck. A whole-chain,
uncompressed σ is in flight. **The decision rule is written here first, so the result is a test
rather than a rationalisation.**

`range needed for 99% = 2.576σ`; `shortfall = that / 6.7 mV`. Range scales with DAC full-scale
current, so **the shortfall factor is the multiplier on the DAC's contribution to `c_p`/`c_n`** — and
the pair enlargement died at **3.4×** on that node.

| whole-chain σ | within ±6.7 mV | 99% needs | shortfall | verdict |
|---|---|---|---|---|
| 4.0 mV | 90.6% | 10.30 mV | 1.54× | **scalable** |
| 5.2 mV | 80.2% | 13.40 mV | 2.00× | **scalable** (boundary) |
| 7.0 mV | 66.2% | 18.03 mV | 2.69× | marginal |
| 8.8 mV | 55.1% | 22.80 mV | 3.40× | **architectural** (boundary) |
| 12.0 mV | 42.3% | 30.91 mV | 4.61× | architectural |

**Thresholds: σ < 5.2 mV → the range problem is a sizing exercise after all. 5.2–8.8 mV → a real
trade against the pole, not a yes/no. > 8.8 mV → the architectural verdict stands as written.**

**Correction, same session — read these thresholds as hard, not pessimistic.** They were first
recorded as *"conservative in the design's favour, since the DAC is only part of the 379 fF."* **The
premise is wrong: 379 fF is the DAC array alone** — 150 unary elements at `Nx=1` × 2.48 fF = 379, and
the rejected pair enlargement's 1275 fF is 150 × 8.45 = 1274. This document says so a few hundred
lines above: *"the comparator's own devices there are tens of fF: the trim DAC came to dominate the
electrical behaviour of the node it exists to correct."*

With the node at ≈ 379 + 40 fF, scaling the DAC by *k* gives a node multiplier of `(379k + 40)/419`:

| DAC ×k | node × | relief |
|---|---|---|
| 1.53 | 1.48 | 3.3% |
| 2.0 | 1.90 | 4.8% |
| 3.4 | 3.17 | 6.7% |

The relief is real and **immaterial — 3–7%, not a cushion.** The shortfall factor therefore maps to
the node capacitance factor almost exactly. **If the whole-chain σ lands within a few percent of
5.20 or 8.84 mV, treat it as inside the worse band.**

**Also recorded: an input-stage-only σ of 3.975 mV** (n=250, flip-point at `v(c_p) − v(c_n)`,
linear by construction, all three mismatch families). It is **not** comparable to the 11.79 —
it excludes the CML, sense amp, output latch and buffers, where most of the old budget sat. The
tell was the monotonicity check: 11.79 → 3.975 while *adding* two mismatch families is impossible,
so the two describe different objects. It is a valid number for the input stage and nothing else.

### Relocating the trim cannot help — `c_p`/`c_n` is the minimum-current injection node

The fallback recorded earlier — *"the correction cannot stay on `c_p`/`c_n`; it has to inject
somewhere that is not bandwidth-critical"* — is **refuted by its own arithmetic and is withdrawn.**

To null an input-referred offset `V_os` you must produce `A_X · V_os` at whatever node X you inject
into, where `A_X` is the gain from the input to X. So the injected current is

```
inject at c_p/c_n :  dI = gm . V_os                       (gm = I_T/2V_T = 34.6 mA/V)
inject at cml_out :  dI = gm . R_C . gm_cml . V_os        -> R_C.gm_cml times MORE
```

`R_C·gm_cml > 1` whenever the CML tail exceeds **0.18 mA** — true of any CML stage; at a 1 mA tail it
is **5.5×**. Every node downstream is worse by the gain preceding it, and there is nothing upstream of
the input pair except the input. **`c_p`/`c_n` is already the cheapest place in the chain to inject a
correction**, so no relocation can beat it, and the four-candidate injection survey is closed.

### What replaces it: the offset is downstream, and downstream mismatch is an area problem

Pre-committed against the pending whole-chain σ. If it lands near **9.95 mV** against the input
stage's measured **3.975 mV**, then the downstream contributes

```
sqrt(9.95^2 - 3.975^2) = 9.12 mV  ->  84% of the offset VARIANCE
```

The downstream is CMOS. Its mismatch scales as `1/sqrt(W·L)`, and area there loads `cml_out` and the
sense nodes — **not `c_p`/`c_n`**, which is the constrained node. To bring the whole chain to the
5.2 mV *scalable* threshold, the downstream must fall 9.12 → 3.35 mV, a factor 2.72, i.e.

```
area factor = 2.72^2 = 7.4x   ->  sense-amp pair w = 2.0 um  ->  ~15 um at the same length
```

Large but ordinary, and paid in gate capacitance on a node that is not the bottleneck.

**So the headline may not be "the trim needs to be bigger". It may be "the sense amp needs to be
better matched"** — a different and considerably cheaper class of fix, and one that only became
visible once the offset was decomposed by stage rather than quoted as a single number.

*(Conditional on the campaign: if the whole-chain σ lands well below ~9 mV the split changes and this
costing must be redone with the measured numbers.)*

## VERDICT — the whole-chain offset, and the architectural conclusion confirmed (2026-08-10)

Measured against the thresholds pre-committed above, before the number existed.

```
whole-chain offset sigma  = 9.395 mV   (quantisation-corrected 9.28; n=235 uncensored + 15 no-crossing)
tail-only cross-check     = 10.63 mV   (15/250 beyond +/-20; agrees within 12%, and higher as censoring predicts)
systematic mean           = -3.4 mV    (design asymmetry, not per-part spread)
shortfall = 2.576 x 9.395 / 6.7 = 3.61x   >  3.4  ->  ARCHITECTURAL BAND
downstream term = sqrt(9.395^2 - 3.975^2) = 8.51 mV = 82% of the variance
99% range = +/-24.2 mV -- EXTRAPOLATED (the +/-20 bracket cannot support it)
```

**The trim range at ±6.7 mV cannot be rescued by scaling under the 3.4× capacitance wall.** The
architectural verdict recorded earlier is no longer suspended: it is confirmed, on a number measured
after the ruler was fixed (H-753), the mismatch enabled (H-746/748), and the rule written down first.

### The coverage count needs correcting before it is quoted

The campaign's direct count — **163/250 (65.2%) beyond ±6.7 mV** — is **biased high and should not be
quoted.** A Gaussian at (−3.4, 9.395) predicts 126; the 4.7σ gap is the 5 mV sweep grid straddling
the 6.7 mV threshold (grid points at 2.083 and 7.083). Correcting the 2.117 mV misclassified band
per side gives ≈129 draws, **51.7%**, consistent with the fitted σ. See H-760.

**The exact figure costs two runs per draw**: apply exactly −6.7 mV and exactly +6.7 mV and compare
the output bit — different means the flip point is inside the trim range. No grid, no σ, no
censoring, no distributional assumption, and cheaper than the nine-point sweep it replaces.

### What the verdict does and does not settle

- **Settled:** widening the trim by scaling the DAC is dead. So is relocating the injection point —
  `c_p`/`c_n` is the minimum-current node.
- **Open, and now the live question:** 82% of the variance is downstream, and the partition campaign
  will name which device carries it. If it is a device whose area can grow on `cml_out` rather than
  `c_p`/`c_n`, the fix is matching, not range — and the architectural verdict, while correct about
  the *trim*, would not be the last word on the *design*.

---

# STATE OF PLAY — 2026-08-10, end of the 9-hour session

This document grew by ~600 lines in one night, almost all of it corrections appended in sequence so
the reasoning stays auditable. **That makes the archaeology readable and the current position hard to
find. This section is the current position.** Where it conflicts with anything above, this wins.

## Numbers that stand

| quantity | value | how measured |
|---|---|---|
| whole-chain offset σ | **~10.5 mV** | 250 draws, flip-point at `pbit_out`; bulk 9.395 is censored-low, tail 10.63, censored count pins ~10.5 |
| input-stage-only offset σ | **3.975 mV** | same protocol at `v(c_p)−v(c_n)`; **not** comparable to the whole-chain figure |
| downstream share | **~82% of the variance** | difference of the two above |
| trim range (hardware) | **±6.7 mV** | `I_FS/gm`, cross-checked by `300 codes × 0.0254 mV = ±7.63` |
| **shortfall** | **3.6–4.6×** | `2.576σ / 6.7`, architectural at every σ estimate |
| handover σ (b7 deck) | **0.3335 LSB** | 250 draws, correct boundary and scale |
| DAC node capacitance | **379 fF** (the array alone) | `150 × 2.48 fF`; per-cell fixed term 0.49 fF |
| nominal whole-chain offset | **+2.083 mV** | `mm_ok=0`, deterministic — a real downstream asymmetry |

## Retracted tonight — do not quote

- **σ = 11.79 mV** (HBT-only, DC protocol, different deck) and its *"11.5 mV sense-amp chain"*
  attribution: the named devices could not vary.
- **All σ from `gate@7.450 ns`** (2.26 / 3.63 / 4.742 mV): the metric saturates (H-753).
- **65.2% beyond ±6.7 mV**: grid straddled the threshold; ~52% is honest (H-760).
- **Handover margins 0.96σ and 3.29σ**: a level for a step, then an ideal from one architecture over a
  σ from another (H-752, H-757).
- **Servo convergence figures** from before the unit fix: 8× the trim range the part has (H-754).
- **The relocation fallback**: `c_p`/`c_n` is the minimum-current injection node.
- **The cell-consolidation lever**: 3.27×, not free.

## Settled conclusions

1. **The trim range cannot be widened by scaling** — the shortfall multiplies the DAC's current and
   the DAC *is* the node capacitance (379 of ~419 fF); the 3.4× wall killed a smaller increase.
2. **Nor by relocating** — every downstream node needs more current by the intervening gain.
3. **The frozen DAC's v7 margin is unverified** — the deck two generations behind (b7/7 handovers vs
   b1/151). The merge is the blocker.
4. **The offset is downstream**, and *which device* is the live question.

## The one question that decides whether a fix exists

**Is the dominant downstream term HBT or resistor?**

- **Resistor** → mismatch scales `1/√(W·L)`; ordinary sizing works, on nodes that are not `c_p`/`c_n`.
- **HBT** → **there is no area lever at all.** `qarea = agauss(1, 0.1, …)` has **no `Nx` term**
  (H-736): a flat 10% regardless of device size. The fix would have to be topological — fewer HBTs in
  the offset path, or more gain ahead of them.

Everything else now waiting is subordinate to that split. The MOS partition that failed is *not* the
route to it (H-762); the deterministic sensitivity sweep — one run per device, no ensemble — is.

## VERDICT SUSPENDED at the boundary (2026-08-10, band-centre result)

**The band-centre estimator (H-764) resolved the mean and moved σ, and the verdict is now
undetermined.** Recorded here immediately because the movement favours the *more favourable* band and
therefore needs the most scrutiny.

```
band-centre campaign, n=238 of 250:   mean = +0.420 mV    sigma = 8.484 mV
```

**Mean: settled.** +0.420 against the first-crossing estimator's −3.00 — the 7.3σ anomaly (H-761) was
the estimator, exactly as predicted. That thread is closed.

**Shortfall: at the boundary.**

| σ source | σ | shortfall | band |
|---|---|---|---|
| band-centre, raw | 8.484 | **3.26×** | **marginal** |
| exact-count core (H-768) | 9.15 | 3.52× | architectural |
| first-crossing MLE | 11.0 | 4.23× | architectural |

Boundary is 3.4× at **σ = 8.84 mV**. The raw band-centre σ sits **0.9 standard errors below it**
(4.6% uncertainty at n=238) — statistically indistinguishable from the boundary.

**Why the raw figure should not stand, and all three reasons point the same way:**

1. It is the **fallback summary** — the specified analysis (clipped-band flagging, recovery,
   h-distribution) errored twice and never ran. **Clipping biases σ downward** by pulling the largest
   offsets inward (H-765/766).
2. **12 of 250 draws are unaccounted** (n=238, 4.8%). If those are the no-crossings, they are the
   largest offsets, missing in the same direction.
3. The **distribution-free count** independently implies a core σ of **9.15 mV** → 3.52×,
   architectural — and the tail is **heavier than Gaussian** (H-768), so `2.576σ` *understates* the
   99% range.

**What closes it.** (a) The clipped-band recovery, reporting corrected σ with the censored count.
(b) **Stop using `2.576σ`** — with 250 band centres the **empirical 95th percentile of |offset| is
directly countable**, so the shortfall at 95% coverage becomes a *measurement*; the 99% figure stays
labelled extrapolated and optimistic.

**Unchanged and not in question:** the exact coverage count — **46.4% of parts lie beyond ±6.7 mV**
(H-768), measured with no distributional assumption at all. Whatever band the shortfall lands in,
nearly half the population is uncorrectable as drawn.

## The v7 compensation is inert, and the number that shows it opens a better fix (2026-08-10)

**The carrier, located in the frozen generator** (`C169-gen-standalone.py:35`):

```
XRCU{j}  e_dacu{j} VSS  rppd w=1.037u l=5.4u m=4     unary
XRCB{k}  e_dacb{k} VSS  rppd w=1.0u   l=5.4u m=1     binary
```

Conductance ratio `4 × 1.037 = 4.148` against an exact 4 — a **+3.7%** trim, not the 8% the v7
section above quotes. *(The surrounding architecture is right: the unary element is `NUNBITS`
parallel `Nx=1` devices, which is H-736 applied correctly, since `qarea` has no `Nx` term.)*

**It cannot deliver that.** Measured `V_R` on a unary cell is **0.6 mV** (predicted ~0.5 before the
run; `b1` reads 1.0 mV in the same `.op`, consistent with the earlier 0.967). The unary cell carries
4 LSB through *four parallel* resistors, so its `V_R` equals a unit cell's rather than 4×. Then

```
sensitivity of I to R  =  (V_R/V_T)/(1 + V_R/V_T)  =  0.022
3.7% conductance trim  ->  0.08% of current change      inert by ~44x
```

**Consequence.** v7's headline — *"improves monotonicity **and** recovers the capacitance"* — is
**half supported**. Reverting the pairs genuinely recovers 379 fF and the ~1.5 GHz pole. The
compensation that was to replace them does essentially nothing, so the 1.098 LSB handover step and
the **4.33σ margin were computed from a single-draw `x` on a correction that is not working** (and
that `x` was already H-742). The margin is unsupported from two independent directions.

### The same number is the lever

Degeneration suppresses V_BE mismatch by `1/(1+V_R/V_T)` and raises the resistor's authority by
`(V_R/V_T)/(1+V_R/V_T)`. **Both are governed by the one quantity now measured at 0.6 mV:**

| `V_R` | HBT term | R term | cell mismatch | trim sensitivity |
|---|---|---|---|---|
| **0.6 mV (today)** | 9.31% | 0.02% | **9.31%** | **0.023** |
| 25 mV | 4.85% | 0.49% | 4.87% | 0.492 |
| 50 mV | 3.25% | 0.66% | 3.32% | 0.659 |
| **100 mV** | 1.96% | 0.79% | **2.11%** | **0.795** |

**Raising `V_R` to 100 mV cuts unit-cell current mismatch 4.4× and makes a width trim deliver what it
claims.** Two problems, one lever — the first proposal tonight that improves the mismatch and the
trim together instead of trading them.

**It also pre-answers the open HBT-vs-resistor split.** At 0.6 mV the answer is *necessarily* HBT,
because the resistors are electrically almost absent from the current-setting path. Degenerating
deliberately moves weight onto the resistors — which **have** an area lever — and off the
transistors, which per H-736 **do not**.

**Cost, and the open question:** ~100 mV of headroom per cell on the emitter node. The supply budget
there is not established in this package and is the number to obtain before this is costed.

### Correction — v7's margin is 3.94σ, and the 1.037 µm was the *overshoot*, not a correction

Following the inertness finding above, the record's characterisation of what the compensation is
**for** is also wrong, and the corrected reading is cleaner.

**There is no systematic ratio error in v7 to correct.** The unary element is **4 identical unit
devices**; the binary section is `b0 + b1` = **3 identical units**. The handover step is therefore
`4 − 3 = 1.000 LSB` **exactly, by construction** — the replication architecture (H-736) removed the
error that the pair-scaled builds had. So the 1.037 µm was never a correction. **It was the deliberate
overshoot** — the segmented-DAC move this document rightly defends — and *the overshoot* is what is
inert.

**Consequences for the numbers on record:**

```
v7 nominal step   1.000 LSB  (not 1.098)   ->  margin 3.94 sigma  (not 4.33)
```

which is the *nominal* row of this document's own table. **And it flips the comparison:** v7 at
**3.94σ** against the pair-enlarged build's **4.06σ** is slightly **worse** on monotonicity, not
better.

**v7 remains the right choice by a distance** — 379 fF against 1275, a ~1.5 GHz pole against 438 MHz.
But the stated basis, *"improves monotonicity **and** recovers the capacitance"*, is wrong in its
first half. **The correct claim is that v7 trades a little monotonicity for a great deal of
bandwidth** — which is a good trade, honestly stated, and did not need the overstatement.

**It also raises the value of the degeneration lever.** The point is not merely that a width trim
would work; it is that **the overshoot the design deliberately wants is undeliverable without it.**
At `V_R = 25 mV` the exact 1.000 step alone gives **7.5σ** and the overshoot would take it to 8.3σ —
at which point the overshoot becomes a nicety rather than a necessity, and keeping the exact step
(with its zero DNL) becomes a defensible choice on its own merits.

## Requirement — bias start-up budget: one servo window (2026-08-10)

Recorded because it was previously **unstated**, and a starter was about to be sized without it.

**No external power-on specification exists in this package.** The budget below is derived from
internal consistency; **a system-level spec, if one appears, supersedes it.**

**Derivation.** The servo window is `32768 bits × 800 ps = 26.2 µs`, and the corrected servo model
converges by window 23 — **~603 µs** from cold. The bias must be up before the first window's
statistics mean anything, or that window is wasted. So:

```
BUDGET: the bias loop reaches its live state within ONE SERVO WINDOW = 26.2 us
```

**Sizing that follows.** The start-up barrier is a *charge* problem (H-778): `C ≈ 8.5 pF` on
`c_p1_comp`, `ΔV = 0.207 V` from the dead state to the unstable crossing at 0.439 V.

| budget | minimum starter current |
|---|---|
| one servo window (26.2 µs) | **67 nA** |
| ×1.5 margin | 101 nA |
| ×3 margin | 201 nA |

**Recommendation: size for 0.1–0.2 µA at the cold slow corner**, where the barrier is deepest and the
capacitance largest.

**And take the margin.** A *self-disabling* starter (H-775) costs **nothing in steady state**, so the
only penalty for oversizing is a starter that fails to switch off cleanly — which the
third-equilibrium sweep (H-776) already tests for. The 10 nA candidate is ~6× under this budget: it
would take **176 µs** and burn the first six servo windows, a self-inflicted delay of a third of the
convergence time to economise on a device that is free once it turns off.

**Measured inputs behind this:** barrier current **0.07 nA max at 0.400 V**; equilibria at
**0.232 / 0.439 / 0.812 V**; both cold-start ramps confirmed **dead**, so unaided start is impossible
at any realistic ramp rate — the starter is a requirement, not insurance.

---

# THE TRIM RANGE VERDICT, MEASURED — supersedes every shortfall figure above (2026-08-10)

**The architectural verdict is withdrawn.** Every shortfall figure in this document — 3.6×, 3.7×,
4.2×, 4.6× — rested on a trim range of **±6.7 mV that was derived and never measured.** It has now
been measured, and it was wrong by a factor of three.

## What was actually built

Measured on the merged v7 deck at `mm_ok=0` (nominal, no mismatch), endpoints of the code range:

```
code 0    (I_cp - I_cn) = -671 uA
code 602                = +669 uA
midpoint                =   -1 uA      -> the array is SYMMETRIC
span                    = 1340 uA      -> ONE-SIDED reach 670 uA
```

**One-sided voltage reach** (`V = 2·V_T·atanh(I/I_T)`, `I_T = 1.79 mA`): **±20.3 mV**.

## The verdict

| quantity | value |
|---|---|
| requirement (95th percentile of \|offset\|, ranked) | **25 mV** = 804 µA one-sided |
| available | **20.3 mV** = 670 µA one-sided |
| **shortfall** | **1.23×** |
| **band** | **SCALABLE** (architectural begins at 3.4×) |

**Fix: ~20% more full-scale current** (1340 → ~1610 µA). The DAC's contribution to `c_p`/`c_n` rises
379 → ~455 fF and the node 419 → ~495 fF — an **18% capacitance penalty on the node whose wall killed
a 3.4× increase.** Entirely affordable.

## Why the record was wrong

The derivation `range = I_FS/gm` was **correct**; its `I_FS` input was not. **232 µA was the design
intent; the built array delivers 1340 µA nominal** — 5.8× more. Both cross-checks agreed with each
other because **both consumed the same wrong `I_FS`**: `300 codes × 0.0254 mV` inherits it through the
LSB. Two independent-looking derivations sharing one unverified input agree exactly as strongly as one.

**The ninth instance of *which circuit is this number for*** — and the only one that sat in the
**denominator** of the question the whole exercise existed to answer. Everything above the line was
scrutinised for eleven hours: the saturating metric, the censoring, the estimator, the heavy tail, the
metastable band. The term underneath was never questioned, because it arrived as a derivation.

## Two claims retracted on the way, both within twenty minutes of being accepted

1. **"The range is unbounded"** — `I_FS/I_T = 1.078 > 1` used the **span** as though one-sided. Neither
   end alone exceeds the tail; the range is finite (H-783).
2. **"1340 µA is 1.67× the 804 µA requirement"** — the same span/reach confusion, in the opposite
   direction, twenty minutes later (H-785).

**Both errors are invisible to dimensional analysis** — span and reach share units and differ by two.
**Put the convention in the identifier:** `I_FS_span` vs `I_reach_one_sided`.

## Also settled

- **The array is symmetric.** A −249 µA "centring error" measured with mismatch on was the
  comparator's own offset (7.24 mV, 0.73σ — an ordinary draw). No centring fix is needed (H-784).
- **The offset numbers stand:** whole-chain σ ≈ 8.5–11 mV, **46.4% of parts beyond ±6.7 mV** by direct
  count. That figure was always about ±6.7 mV, a range the part does not have; against the real
  ±20.3 mV the reachable fraction is far higher and should be recounted from the same data.

---

# STATE OF PLAY — REVISED, 2026-08-10 (14 h). Supersedes the 9-hour section above.

The 9-hour state-of-play is now itself out of date in its most important row. **Where the two
conflict, this one wins.**

## Corrected since that section was written

| quantity | 9 h section said | now |
|---|---|---|
| **trim range** | ±6.7 mV (derived) | **±20.3 mV per side (MEASURED)** — symmetric, `mm_ok=0`, endpoints −671/+669 µA |
| **shortfall** | 3.6–4.6×, architectural | **1.23×, SCALABLE** — fix is ~20% more `I_FS` for an 18% node-capacitance rise |
| whole-chain offset σ | ~10.5 mV | **~8.5–10 mV** — both censoring campaigns reconcile once their windows are read correctly (±20 and ±10, not ±15) |
| the headline count | 46.4% beyond ±6.7 mV | **being recounted** as a *predicate*: input at zero, sweep the code, does the bit flip — distribution-free, in flight |

## The root cause of the withdrawn verdict

`range = I_FS/gm` was **correct**; its `I_FS` was the **design intent (232 µA)**, not the built array
(**1340 µA nominal**). The two cross-checks agreed because **both consumed the same wrong `I_FS`** —
the second inherits it through the LSB. *Two derivations sharing one unverified input agree exactly as
strongly as one.*

## Also retracted since the 9-hour section

- **"The range is unbounded"** — the span used as though one-sided (H-783).
- **"1340 µA is 1.67× the requirement"** — the same span/reach error, opposite direction, twenty
  minutes later (H-785).
- **"The array is mis-centred by −249 µA"** — that was the comparator's own offset measured through
  itself; at `mm_ok=0` the midpoint is **−1 µA** (H-784).
- **"The censored population fits no distribution"** — mine, computed on a ±15 mV window that was
  actually ±10 mV. Everything reconciles at σ ≈ 8.5 (H-786, corrected).

## Standing, and unaffected by any of the above

- **The v7 compensation is inert** — `V_R = 0.6 mV` gives it 0.08% authority; v7's true nominal margin
  is **3.94σ**, not 4.33 (H-780/H-781).
- **The bias loop has no starter** and comes up dead from a cold ramp — a real silicon defect, fix
  specified (three-stack pull-down on `c_p2_comp`), not gating any measurement (H-774/H-775/H-779).
- **Resistor and MOS mismatch were disabled in every deck** until tonight (H-746/H-748).
- **The offset metric saturated**, compressing every σ taken from it (H-753).

## What is still open

1. **The correctable count** — in flight, with per-draw tail/core breakdown. Reading pre-committed:
   >95% fine as built; 89–95% the 1.23× sizing closes it; <89% the tail needs its own investigation.
2. **The step at code 3→4** — verifies the 3.94σ handover margin on the real v7 boundary.
3. **The HBT-vs-resistor budget** — decides whether the downstream offset has an area lever at all.
4. **The starter build and its sign-off pair** — forced sweep (one zero) plus ramped transients across
   the corner matrix.

# THE CORRECTABLE COUNT IS RETIRED AND REBUILT (2026-08-10)

**No correctable-fraction figure from tonight's count campaign may be quoted.** Versions 1 through 6
all shared a defect in the sample unit, found by reading the PDK rather than the results.

**The defect.** The harness ran one `ngspice` process per code point (`c0`, `c602`, `c476`). Mismatch
in this deck comes from the `*_mismatch` corner libs, every one of which draws through `agauss`
(`resistors_mod_mismatch`, `cornerRES.lib:219+`; `sg13g2_moshv_mod_mismatch:78–91`;
`sg13g2_hbt_mod_mismatch`), and **`agauss` is evaluated at netlist expansion — once per process.**
So the points of one "draw" were **independent parts**, and the predicate `pbit(c0) != pbit(c602)`
differenced one chip against a different chip.

**Confirmed empirically, not just by reading:** the identical deck run twice gave `c_p` differing by
**9.1 mV**. Per-process draws; no deterministic seeding.

**What the reported numbers were.** At either code endpoint the DAC steers hard, so a *correctable*
part answers deterministically whichever part it is, and an *uncorrectable* one reports the sign of
its own offset — a coin flip. The reported fraction is therefore

    P(scored correctable) = ((1 + p) / 2)^2 ,  not p

compressed toward one exactly where the decision sits (p = 0.9 → 0.90; p = 1 → 1.00). The 40/40 run
bounds **p ≈ 0.93**, not ≥ 0.95, and **the pre-committed 89 / 95 % thresholds never applied to the
statistic being produced.** They are void; new thresholds must be set against the rebuilt measure
before its first result is read.

**The rebuild.** One process per draw, code stepped **inside** the run — a PWL staircase on `VCODE`
with `IKICK2` re-fired at each plateau, `pbit_out_core` read at the end of each. One expansion, one
chip, the whole code axis. Not `alter` (killed v1/v2) and not `.dc` (no time axis, cannot exercise
the latch).

**Three things it delivers that the old campaign could not:**

1. **A genuine per-chip predicate** — does *this* part's output change anywhere across *its own* code
   sweep — with no independence assumption in it.
2. **The flip code per draw**, i.e. the **margin distribution** this README previously recorded as
   needing a bisection. It is free here.
3. **The cold answer off the same sweep** — a flip below 79 % of full scale survives −40 °C (the V_T
   equivalence already recorded), so no separate cold deck.

At one deck per draw instead of three, the draw rate rises ~3× despite the longer transient.

**Settling is verified internally, because it can no longer be verified externally.** With one chip
per process, a plateau cannot be checked against a fixed-code deck — that deck is a different part.
Instead the staircase runs **up through the codes and back down**, and each code is compared against
itself on the two passes. Agreement ⇒ the plateau is long enough; disagreement is hysteresis, i.e.
unallowed settling.

**Declined:** drawing the mismatch in Python and injecting literals. It requires reimplementing the
foundry's statistics (global vs per-instance terms, `sqrt(m·l·w)` scaling on `delvto`/`factuo`,
`mm_ok` gating, the joint `w`/`l` draw); a subtle error there produces a distribution that is silently
not the PDK's, with nothing to compare against. **The PDK draws its own devices.**

*Nothing in the measured trim-range verdict above depends on the count campaign; that section stands.*

# THE OFFSET VARIANCE BUDGET, FROM THE MODELS (2026-08-10)

Read directly out of the IHP SG13G2 model files — no simulation, no fitting. **Conditional on
`mm_ok = 1` being set on the comparator's input-pair HBT instances; verify before quoting.**

| term | device-plane sigma | input-referred sigma | share of 8.5 mV | area lever |
|---|---|---|---|---|
| HBT **input pair** (`qarea`) | 10 % area, **flat** | **3.66 mV** | **18 %** | **none, at any size** |
| HBT **DAC cells** (`qarea`, ~undegenerated) | 10 % area | ~1.29 mV | ~2 % | none |
| HBT **CML pair**, referred through gain 8.17 | 10 % area | ~0.45 mV | < 1 % | none |
| **HBT total** | — | **~3.9 mV** | **~21 %** | **none** |
| rppd load / DAC (`rsh_rppd_mm`) | 0.44 % | **0.11 mV** | < 1 % | 1/sqrt(W·L·m), irrelevant |
| MOS (`delvto_mm`) — **by subtraction** | 3.9–7.0 mV·µm | balance | **~79 %** | **1/sqrt(W·L·m)** |

**Two qualifications on this table, both mine.** (1) The 18 % line covers **only the input pair**;
`qarea` sits on *every* HBT — DAC cells, CML, tail — and each refers to the input plane. The extra
rows above cost those out: HBT total lands near **21 %**, still a clear minority, so the conclusion
holds — but it holds by arithmetic done *after* the claim, not before. (2) **The MOS share is
obtained by subtraction**, the weakest form of attribution: every unmodelled term and every error in
the modelled ones lands in it. It is not yet a measurement of MOS.

**The experiment that replaces the subtraction** — run the offset measurement three times with one
family's mismatch enabled at a time (HBT-only, rppd-only, MOS-only) and check the three variances sum
to the measured total. If they do, the ~79 % becomes a reading. **If they do not, that is the more
useful outcome**: either a term outside all three families, or interaction between them.
**The switching is not symmetric** (H-7xx): HBT needs `hbt_typ_mismatch` **and** `mm_ok=1` on the
instances — the corner alone does nothing; rppd and MOS are corner-only and `mm_ok` is a no-op on
them. Getting that backwards is how two families were found silently disabled earlier tonight.

**HBT.** `qarea = agauss(1, 0.1, (mm_ok != 1 ? 0 : 1))`, `sg13g2_hbt_mod_mismatch.lib` lines 49, 159,
289, 397, 528, 636 — every block, and **no geometry term in any of them**. This is the source-level
confirmation of the flat `qarea` inferred in H-736. `sigma_Vbe = V_T·(sigma_A/A) = 2.59 mV` per
device, `sqrt(2)·2.59 = 3.66 mV` for the pair. **Emitter area is not a lever and never will be.**

**Resistors.** For a *bipolar* pair the referral collapses:
`input-referred = I·dR/(g_m·R) = V_T·dR/R` — the current and the resistance divide out. At 0.44 %
that is **0.11 mV**; even a 10×-smaller resistor reaches only ~0.35 mV. **The resistor path is
bounded well below half a millivolt.** General property: bipolar load mismatch is suppressed by
`V_T / V_load`, which is why it seldom dominates here and routinely does in CMOS.

**Consequence, and it reverses the standing worry.** The item was framed as *"decides whether the
downstream ~80 % of the variance has any area lever"*, on the expectation that it might be HBT and
therefore immovable. It is not. **The immovable term is the 18 % minority; the ~80 % majority is MOS
and scales as 1/sqrt(W·L·m).** Halving the MOS-contributed sigma costs 4× area on those devices only
— and cuts total sigma from 8.5 mV to about **5.3 mV**, which is a 1.6× relaxation of the trim range
requirement, on top of the 1.23× shortfall already measured.

**This supersedes any statement in this file that the offset spread has no design lever.**

# PRE-COMMITTED READING FOR THE REBUILT COUNT (written at draw 26 of 60, before any result)

The old thresholds are **void** — they were set against `((1+p)/2)^2`, not `p`. These replace them,
and they are recorded here *before* the number exists, which is the only time it can be done honestly.

**Two statistics, read in this order.**

1. **`p_room`** — the fraction of chips whose output flips *anywhere* across codes 0…602 at 27 °C.
   Rule of three now applies honestly, because the predicate is finally per-chip: **60 perfect draws
   bound the failure rate below 5 %.**
2. **`p_cold`** — the fraction whose **consumed margin ≤ 79 %**, where

       consumed margin = |flip_code - 301| / 301

   **CORRECTED 2026-08-10, before the first result.** This originally read "flip code ≤ 79 % of full
   scale", which is **wrong**: the code axis is **bipolar** — code 0 = **−671 µA** (full negative
   steer), code 602 = **+669 µA**, and **zero correction is the MIDPOINT, code 301**. A chip flipping
   near *either end* consumed nearly all the trim; a chip with no offset flips in the *middle*. The
   original definition would have scored the worst parts as the best and returned ~100 %.
   79 % at 27 °C reproduces the trim reach available at −40 °C (the V_T equivalence recorded above).

**Pre-committed thresholds on `p_cold`:**

| `p_cold` | reading |
|---|---|
| **> 95 %** | fine as built |
| **89 – 95 %** | the already-costed **+20 % `I_FS`** (DAC 379→455 fF, node 419→495 fF) closes it |
| **< 89 %** | range alone is insufficient; the variance work must come with it |

**A forecast the old campaign could never produce.** With a **flip code** per chip rather than a
yes/no, the sizing change can be evaluated *without simulating it*: a +20 % `I_FS` moves every chip's
required code down by the same factor, so **divide every measured flip code by 1.23 and recount how
many land under the 79 % line.** That is the predicted `p_cold` after the fix, free, from data
already in hand. **If the forecast clears 95 %, the sizing decision is settled without its own
campaign.**

# A ~16 mV SYSTEMATIC OFFSET — MEASURED WITH ALL MISMATCH DISABLED (2026-08-10)

**PROVISIONAL, pending one discriminating test.** Read this section together with its confound.

**Measurement.** All six corners at plain typ (`hbt_typ`, `res_typ`, `cap_typ`, `mos_tt` ×2,
`dio_tt`), **no `_mismatch` block anywhere** — so there is exactly one possible part and no statistics
are involved. Code sweep, 16 points:

    levels                 0011111111111111      flip at index 2  ->  code ~60
    from midpoint (301)    -241 codes  =  80 % of the one-sided trim range
    input-referred         ~ -16.2 mV     (+/- 1.35 mV, set by the 16-point resolution)

**A fixed asymmetry carried by every part.** It also explains the first two mismatch draws (67 % and
80 % consumed) — a ~16 mV fixed term plus a modest random one, not a coincidence.

**THE CONFOUND.** The start-up kick `IKICK2 0 xcomp.c_p1_comp` injects **1 mA into a single node**,
and the measurement cannot separate the circuit's own asymmetry from the state that kick leaves the
part in. The kick cannot be removed — the bias loop has no starter (see the start-up section above),
which is precisely why this confound exists.

*Corrected 2026-08-10: an earlier draft of this paragraph called `c_p1_comp` "one side of a
differential pair" and proposed symmetrising the injection. **That was wrong.** `c_p1_comp` and
`c_p2_comp` are the **bias loop's compensation nodes** — the same ones in the three-equilibria
start-up finding above — so the kick moves the loop off its dead equilibrium onto the live one rather
than unbalancing the comparator inputs. It has **no complement**, and "symmetrise it" is undefined.*

**Discriminating test (assumes nothing about topology): sweep the kick amplitude.** Same no-mismatch
deck at **0.5 mA / 1 mA / 2 mA**.

    flip stays at code 60 across 4:1 in stimulus  ->  the kick is not the cause; the 16 mV is real
    flip moves with amplitude                     ->  the kick sets where the loop lands; it is ours

**A rerun is not this test.** `systest3` was byte-identical to `systest2` but for output filenames;
its matching answer shows only that a no-mismatch deck is deterministic.

**IF REAL, this supersedes the +20 % `I_FS` recommendation.**

    required correction   = -16.2 +/- 8.5 mV        against a reach of +/- 20.3 mV
    headroom              =   4.1 mV  ~= 0.5 sigma
    uncorrectable         ~  1 in 3        (not the 5-10 % assumed all evening)

    fix by growing the DAC   +20 % I_FS, 379->455 fF and 419->495 fF   ->  1.2x usable range
    fix by removing the skew zero area                                 ->  5x usable range
                                                                           (4.1 mV -> 20.3 mV)

**Paying silicon area to compensate a fixed design asymmetry is the worst class of fix, because it
works.** If the test confirms, the sizing change comes off the table and is replaced by locating the
asymmetry.

*No action is to be taken on this section until the kick test resolves it.*

# THE SYSTEMATIC OFFSET IS CONFIRMED, AND THE START-UP DEFECT IS NOW A BLOCKER (2026-08-10)

**The confound above is cleared.** Kick-amplitude sweep, mismatch off throughout:

| kick | levels | flip | code | offset |
|---|---|---|---|---|
| 0.5 mA | `1111111111111110` | idx 15 | 582 | **INVERTED TRANSFER** |
| 1.0 mA | `0011111111111111` | idx 2 | 60 | −16.2 mV |
| 2.0 mA | `0111111111111111` | idx 1 | 20 | −18.9 mV |

**1 mA and 2 mA differ by exactly one resolution step** (602/15 = 40 codes = 2.7 mV): a **doubling of
the stimulus moved the answer by less than the measurement resolves.** The kick does not manufacture
the offset. **The ~16–19 mV systematic term is real.**

**It is worse than the provisional section stated.** The asymmetry consumes **80–94 % of the one-sided
range** before any mismatch. At 2 mA the flip lands **20 codes from the end** — nearly railed; a
slightly larger asymmetry would give **no flip at all**. **The array is close to unable to centre even
the nominal part.**

**Decision (supersedes the +20 % `I_FS` sizing entirely).** Do not grow the array: 1.2× on a range
already ~90 % consumed by a defect. **Locate and remove the asymmetry** — zero area, ~5× usable range
(4.1 mV → 20.3 mV). The 379→455 fF and 419→495 fF changes are withdrawn.

## The 0.5 mA control case: the part can come up inverted

Same deck, same devices, **no mismatch** — and the transfer is **reversed**: 1 at low codes, 0 at
high. **Halving the start-up current reverses the input-to-output polarity of the part.**

This is the three-equilibria / no-starter defect recorded earlier in this file, now seen in a
transient rather than a DC sweep: a smaller kick leaves the bias loop in the *other* stable state, and
in that state **the signal path runs backwards.**

**In silicon this means the p-bit generator can power up producing the logical inverse of its intended
output, with nothing in the circuit to prevent it** — which state it lands in depends on supply ramp
and on what the loop sees on the way up.

**The starter is promoted from non-blocking to a HARD BLOCKER, with a stronger acceptance test than
previously written.** It is not sufficient to reach the live equilibrium; it must reach **the same**
equilibrium every time. **Sign-off must include: sweep the start-up energy across a wide range and
confirm the transfer polarity never inverts** — in addition to the forced-sweep (exactly one zero)
and ramped-transient checks already specified.

# THE COUNT IS BIMODAL: IT MEASURES WHICH POWER-UP STATE, NOT HOW MUCH OFFSET (2026-08-10)

First ten draws of the rebuilt campaign, read directly from the CSVs:

    draw 0  0011111111111111  code  60      draw 4  0000000000000111  code 502
    draw 1  0001111111111111  code 100      draw 6  0000000000000111  code 502
    draw 2  0001111111111111  code 100      draw 7  0000000000000111  code 502
    draw 3  0010010000000111  NON-MONOTONIC
    draw 5  0010000000000011  NON-MONOTONIC

**Bimodal, with nothing in the middle** — no draw lands near code 301. Chips at ~60–100 sit in one
bias equilibrium; chips at ~502 sit in the **inverted** one, exactly where the 0.5 mA control put the
nominal part (code 582). **Consumed margin reads 67–80 % for every chip**, because the flip is always
near an *end* and only *which* end varies.

**The non-monotonic draws are the mechanism, visible.** Those parts sit near the boundary between the
two states, and **sweeping the code switches the loop from one equilibrium to the other mid-sweep** —
their output is not a comparator decision at all.

**Consequence: `p_room`, `p_cold` and the ÷1.23 forecast cannot be produced from this run.** The
campaign is not measuring how much offset the trim can cancel; it is measuring **which of two
power-up states each chip fell into**. Every statistical apparatus specified above sits downstream of
a quantity that is not the one it names. **The pre-committed thresholds are not void — they are
simply not yet applicable, and will not be until the part has a single power-up state.**

**The run continues, re-purposed.** It now measures **the fraction of parts that come up inverted** —
roughly **half** on the first ten. That figure, not the equilibrium diagram, is the case for the
starter: *approximately one part in two powers up producing the logical inverse of its intended
output.*

**Order of work is now fixed by this.** The starter is the blocker; the systematic offset (~16–19 mV)
is the next item; the correctable count can only be re-run once the part has one deterministic
power-up state. **Re-running the count before then measures the coin toss, however many draws it
takes.**

# QUALIFICATION ON EVERY PBIT NUMBER ABOVE: THE SAMPLE IS TAKEN MID-TRANSIENT (2026-08-10)

**Read this before quoting the systematic offset or the state split.**

    bias loop settling (servo window)   ~26 us
    transient in every deck tonight      12 ns
    ratio                                ~2000x

**Every `pbit` reading this session was sampled roughly 2000× sooner than the bias loop settles.**
Confirmation from the localisation run: at 12 ns `c_p1_comp = 0.7348`, while the measured stable
equilibria are **0.232** and **0.812** — the node is *in transit*, not at either one. **The comparator
is being asked to decide while its own operating point is still sliding.**

**This is a candidate common cause for three findings recorded above:**

- the answer moving with kick amplitude — amplitude sets the trajectory;
- the bimodal flip codes — different trajectories are elsewhere at 10 ns;
- the non-monotonic draws — trajectory and code interact.

**It does not refute them.** The ~16–19 mV may well survive. What is true is that **no measurement
taken tonight distinguishes a settled offset from a snapshot of a transient**, and that ambiguity sits
under every number since the campaign began.

**Waiting it out is not available**: 26 µs at the measured 0.056 s/ns is ~1450 s per point.

**The fix, and it costs nothing.** Initialise the loop into its live state at t = 0:

    .ic v(xcomp.c_p1_comp)=0.812  v(xcomp.c_p2_comp)=0.975     # measured live values

This steers the DC solve onto the **live** equilibrium instead of the dead one, so the transient
**begins settled** and 12 ns is ample for the comparator alone. **It is a software starter standing in
for the missing circuit** — and it makes every subsequent measurement comparable to every other.

**All quantitative claims in the two sections above are provisional until re-taken with the loop
initialised.** The qualitative conclusions — starter is a blocker, count cannot be produced without a
single power-up state — are unaffected, since they rest on the multiplicity of states rather than on
any particular value.

# VOID: EVERY RESULT FROM THE `.ic` / `uic` DECKS (2026-08-10)

**`icdeck3` line 35 reads `tran 0.05n 12n uic`.** `uic` **skips the operating point entirely** — the
transient begins with **every node at 0 V** except the two named in `.ic`. Not the dead equilibrium,
not any equilibrium. Every collector, bias node and internal supply node at ground, given 12 ns to
recover in a circuit whose bias loop settles in 26 µs.

**Voided by this, with no residual claim:**

- the "no flip at any code with the loop settled" result — the loop was not settled, it was at zero;
- the "output stuck; no response to ±50 mV" result — same decks, same defect;
- any inference that the nominal part cannot be centred by the trim. **That question is OPEN.**

**The `.ic` software starter is withdrawn entirely** (it was already withdrawn on the weaker grounds
of clamping a partial state; this is the stronger reason).

**A methodological failure of my own belongs on the record beside it.** The validity column added to
guard exactly this read **0.813 at every code**, and I read that as proof the circuit was live. It was
the initial condition *persisting* — nothing had moved it. **A forced node reports on the forcing, not
on the circuit.** Every validity column from here must include at least one **unforced** node whose
value can only be right if the rest of the circuit is right — the collectors near 2.5 V would have
caught this instantly.

**Still open, and now with no valid answer at all:** the ±50 mV must-succeed test — does the signal
path respond to a differential far larger than any offset? It must be re-run under the first
configuration that solves a genuine operating point.

**Unaffected:** the kicked-deck results (H-814/H-816 systematic offset, the bimodal state split), which
solved real operating points. They remain subject to the separate mid-transient qualification above.

# THE OPERATING-POINT FAILURES ARE NUMERICAL, NOT PHYSICAL (2026-08-10)

Pull-down bisection on `c_p2_comp`, by whether an initial transient solution was found:

| value | current at ~1 V | result |
|---|---|---|
| 200 MΩ | ~5 nA | **converges** |
| 500 MΩ | ~2 nA | **converges** |
| 1 GΩ | ~1 nA | fails |
| 10 GΩ | ~100 pA | fails |
| 100 GΩ | ~10 pA | **converges** |

**Not a threshold — it converges, fails, then converges again across four orders of magnitude**, with
the *weakest* value of all (100 GΩ, electrically indistinguishable from nothing) working while 1 GΩ
does not. **No physical mechanism is non-monotonic like that.**

**Conclusion: the DC solution of this circuit is hard for the solver to locate**, and success depends
on where the homotopy path lands rather than on the load. Consistent with the three-equilibria
structure recorded above: two stable points and one unstable one give a complicated basin structure
for Newton to wander in. **This numerical fragility is a property of the design worth carrying — a
block whose operating point cannot be reliably solved is expensive to verify at every future stage.**

**Retracted on this basis:** every reading in which an operating-point failure was taken as evidence
about the circuit — "the pull-down removes a solution", "the loop has no stable DC state". **Those
were the solver.**

**The genuine conflict that remains, one run from resolution.** Every converging value is **far too
weak to act as a starter**: 200 MΩ passes ~5 nA against the derived **67 nA** floor. The
starter-relevant values (~10 MΩ) failed — **but in earlier deck variants, not in the bisection deck.**

**Owed: 10 MΩ and 50 MΩ in the identical deck that converged at 200 MΩ.**

    converges     -> a working configuration exists; the measurement proceeds
    fails         -> across the whole range where this fix could function, the OP cannot be solved,
                     and the fix must change: a different node, a switched element that disengages
                     after start-up, or a change to the loop itself

**The two sweeps bracket from opposite directions** — minimum strength that guarantees starting versus
maximum strength the analysis tolerates. **The design exists only if the brackets overlap.**

# THE OBSERVABLE IS DUTY CYCLE, NOT A LOGIC LEVEL (2026-08-10)

**Supersedes the metric used by every count campaign in this file.** `pbit_out_core` is a
**probabilistic** output — that is the circuit's function — so the quantity is its **duty cycle**, the
fraction of the run spent high. **Sampling one instant at 10 ns measures which phase of the clock the
sample landed on.**

**Measured from CSVs already on disk** (all samples after 2 ns, mid-band excluded), duty vs code index:

    draw 0   0.64 0.66 1.00 1.00 ... 1.00
    draw 1   0.63 0.65 0.66 1.00 ... 1.00
    draw 3   0.00 ...... 0.00 | 0.31 0.34 0.35
    draw 4   0.64 | 0.00 ... 0.00 | 0.32 0.34 0.34

**Draws 0 and 1 are nearly balanced at the bottom of the code range** (duty 0.64 against the 0.50
wanted) and saturate high as the code rises — they need **more negative correction than code 0
provides**. Just outside the range, **and the shortfall is now a number.** Draw 3 is the mirror,
reaching only 0.35 at maximum code.

**Across all four, nothing reaches 0.50 at any code.** The same conclusion the binary analysis was
approaching — now quantified per part.

**The binary classifier also manufactured artefacts.** Draw 3's isolated 1s at codes 2 and 5, recorded
earlier as "non-monotonic", are codes where the part **sat stuck high rather than toggling**.

**Re-analysis, not re-simulation.** Every CSV exists. Definitions:

| term | definition |
|---|---|
| correctable | some code brings duty within 0.45–0.55; that code is the part's trim setting |
| out of range | closest approach outside the band; **report the best achievable duty**, not a verdict |
| headline | the **distribution of best-achievable duty** over 60 parts |

**Consequences.** The trim-range question is finally answerable in its own units — distance from 0.50
maps onto required range. **The intended/inverted/no-transfer split recorded above is suspect and must
be recomputed on this basis.** Keep the level-crossing analysis alongside: the two disagreeing on a
part is itself informative.

*Four hours of analysis in this file treated a random-number generator as a comparator, because the
harness had always sampled it that way.*

# THE BIMODAL RESULT WAS OUR SAMPLING GRID (2026-08-10) — RETRACTS THE STATE-SPLIT SECTION

Duty-cycle re-analysis over all **24** complete draws. Per chip, the code whose duty is closest to
0.50; sorted best-achievable duties:

    0.32 0.34 0.34 0.34 0.35 0.35 0.35 0.35 0.35 | 0.63 0.63 0.64 0.64 0.65 (x8) 0.66 0.67

**Zero of 24 within 0.45–0.55** — but the shape is the finding. **Nine chips at ~0.34, fifteen at
~0.65, and nothing at all between 0.35 and 0.63:** an empty gap **centred exactly on the target,
symmetric about it.** *No physical spread of manufacturing offsets avoids a value.*

**It is the grid.** 16 points across 602 codes is a **40-code step**, while duty moves **≥0.30 between
adjacent samples** (draw 0: 0.66 → 1.00; draw 3: 0.00 → 0.31). **The transition is far narrower than
the step.** Every chip was stepped over its own balance point, landing either side and never on it.
**The two clusters are the duty values at the bracketing codes.**

**Retracted on this basis:** the "intended / inverted / no-monotonic-transfer" split recorded above,
including the "about half the parts come up inverted" figure. **What was read as two power-up states
is, at least in large part, one steep transition sampled too coarsely.** The start-up defect itself
stands on its own evidence (three DC equilibria; the 0.5 mA control inverting) — but **the population
fractions attributed to it are withdrawn.**

**The trim-range question is open again, for a reason not previously considered: sweep resolution, not
array range.** The part may be centreable at a code never sampled.

**Method: bisect on duty.** Duty is continuous and monotonic in code on nearly every draw — ideal for
bisection, which the binary flip never was. Bracket from the coarse sweep (free), then ~9 halvings to
single-code resolution: **~11 evaluations per chip against 16, cheaper and far sharper**, returning
the **balance code** per part.

**Headline becomes the distribution of balance codes**, and how many lie inside 0–602:

    all inside   -> the range is adequate; the shortfall discussion in this file evaporates
    any outside  -> the excess IS the extra range required, in codes, directly

**Caution:** draw 4 is non-monotonic (0.64 at code 0, flat 0 mid-range, 0.34 at top). **Bisection
returns a confident wrong answer on such a part.** Screen for monotonicity on the coarse sweep and
bisect only the chips that pass; the remainder are a separate population.

# CORRECTION: THE GAP IS NOT THE GRID — THE CROSSING IS OUTSIDE THE ARRAY (2026-08-10)

**Supersedes the section immediately above, which was wrong.** Interpolating for the balance point on
every monotonic draw: **of 19 monotonic chips, ZERO have a duty crossing of 0.50 anywhere inside the
code range.**

    upper cluster   0.63-0.65 at code 0, rising monotonically to 1.00
                    -> balance point lies BELOW code 0
    lower cluster   0.00 through most of the range, only 0.35 at code 602
                    -> balance point lies ABOVE code 602

**The empty span between 0.35 and 0.63 is the range of duty the array cannot reach**, not a
transition stepped over. A coarse grid would still have bracketed a crossing that existed; **no draw
brackets one.** The state-split retraction in the previous section stands for the *fractions*; the
"sampling artefact" explanation for the gap does not.

## The trim-range answer, in the right units at last

From the endpoint slopes (duty changes ~0.02 per 40 codes at both ends):

    low end    0.64 -> 0.50   needs ~280 more codes
    high end   0.35 -> 0.50   needs ~200 more codes

**The array is short by roughly 200–280 codes of 602 — it must be ~1.3–1.5× larger, or the offset
consuming it must be removed.** Extrapolated from endpoint slope, so treat as an estimate pending the
bisection; but the direction and order of magnitude are firm.

**Independent convergence.** The first measured verdict of this session — *"shortfall 1.23×,
scalable"*, from the DAC-current route with no reference to duty cycle — agrees with **1.3–1.5×**
from the duty route, ten hours and one complete change of metric later.

**Still owed:** bisection on duty for the monotonic chips, to replace the extrapolation with a measured
balance code per part; and a separate treatment of the **7 non-monotonic** draws of 26, which are a
different population and are not described by any of this.

# RETRACTED IN FULL — THIS SECTION MEASURED A NEAR-SHORT, NOT A STARTER (retracted 2026-08-11)

> **DO NOT QUOTE ANY NUMBER BELOW.** Diffing the include files found one character:
>
>     converging deck   RSTART c_p2_comp 0 10M     <- 10 MILLIOHMS
>     failing deck      RSTART c_p2_comp 0 10MEG   <- 10 megohms
>
> **In SPICE `M` means milli.** Every converging run in this section — `10M`, `50M`, `100M`, `200M`,
> `500M` — was **10–500 mΩ, a near-short to ground**, not a pull-down. So:
>
> - the **"flat over a 20× band"** was five slightly different ways of *grounding a node*;
> - the **67 nA floor "comfortably satisfied"** — it was never 10 MΩ;
> - the **bias node "at 0.8725, therefore live"** is column two, `c_p1_comp`; `c_p2_comp`, the node
>   actually shorted, would sit near zero. Consistent with a short, and read as a working starter.
>
> **The real starter has never converged** — not at nominal, not with mismatch, not at the midpoint,
> not at any value tried with correct units. **The proposed fix has not been simulated even once.**
>
> **Unaffected and still standing:** the three equilibria and absent starter (DC sweeps); the polarity
> inversion at 0.5 mA kick; the duty-cycle analysis and the control campaign, which never involved a
> pull-down at all.

Pull-down `RSTART c_p2_comp` inside the `p1_comparator` subcircuit, bisection deck:

| value | current at ~0.87 V | bias node | duty | run |
|---|---|---|---|---|
| 10 MΩ | ~87 nA | **0.8725** | 0.16 | full 12 ns |
| 50 MΩ | ~17 nA | **0.8724** | 0.16 | full 12 ns |
| 200 MΩ | ~4 nA | **0.8724** | 0.16 | full 12 ns |

**10 MΩ converges** — the value that failed in earlier deck variants, whose failures are now
attributed to the numerical fragility recorded above. **The brackets overlap; the starter as specified
can exist.**

**Three results.**

1. **The bias node sits at 0.8725 — the live equilibrium, not the dead 0.233.** The pull-down
   establishes the working state and holds it, **with no kick, no initial condition, and nothing to
   verify after the fact.** It replaces every start-up workaround used in this file.
2. **Across a 20× range of strength the operating point is unchanged** — duty identical to two
   decimals, bias to four. *The element establishes the state without perturbing it*, so sizing has
   wide margin and needs no tolerance argument.
3. The **67 nA** floor derived by charge arithmetic is met comfortably at 10 MΩ, with room either way.

**Still owed — the dynamic half, and the harder one.** This shows the starter works *once the supplies
are up*, not *during a supply ramp*. **The acceptance test stands as written in the start-up section:
ramp the supply across a wide range of rates and confirm the transfer polarity never inverts**, plus
the forced sweep (exactly one zero) and the ramped transients across the corner matrix.

**Implementation note for layout:** the model is a conductance to ground on `c_p2_comp`; the intended
device is the 3-stack nmos pull-down. Size it anywhere in the 10–200 MΩ equivalent band — **the flat
region is the specification, not a target value.**

# THE "THIRD POPULATION" IS A SOLVER ARTEFACT (2026-08-10) — RETRACTS THE NO-MONOTONIC-TRANSFER CLASS

The 9-of-31 draws classified as having "no monotonic transfer" are **not a population of parts.**
Their duty curves:

    draw 3    0.00 0.00 1.00 0.00 0.00 1.00 0.00 ... 0.31 0.34 0.35
    draw 15   0.00 x5 1.00 0.00 x5 1.00 0.00 0.00 0.00 0.34
    draw 24   0.67 0.79 1.00 1.00 | 0.00 x9 | 1.00 1.00 1.00

**The values are almost all exactly 0.00 or 1.00 — fully railed — flipping between codes with no
pattern.** Not a curve doubling back: a part sitting hard at one rail, with *which* rail changing per
code.

**Mechanism.** Each code performs `alter` then `tran`, and **every `tran` re-solves the operating
point.** This circuit has **two stable equilibria** and a **numerically fragile OP solve** (see the
non-monotonic convergence section above). **At each code the solver may land in either equilibrium —
and does.** The railing flips because the equilibrium flips.

**So this is one measurement artefact affecting 29 % of draws, not a third class of silicon.**

**Falsifiable prediction: with the 10 MΩ starter in the campaign deck, this population should vanish**
— the dead equilibrium is removed, leaving one state for the OP solve to find.

    vanishes  -> artefact explained; every remaining chip is measurable
    survives  -> a real second mechanism, and much narrower than before

**Action: re-run the campaign with the starter in place.** This is the "starter unblocks the
measurement" argument recorded earlier, now with a number: **29 % of draws recovered**, on top of the
silicon defect it fixes.

*Note the sequence: the starter was a silicon fix, then a blocker, then an unblocker for measurement,
and is now also the repair for 29 % of the data. One defect, four consequences.*

# STANDING QUALIFICATION ON EVERY NUMBER ABOVE (2026-08-10, end of session)

**If the operating-point solver selects an equilibrium per code (previous section), then codes within
the *monotonic* 71 % could also have been solved in the wrong equilibrium** — those draws merely came
out consistent. Their credibility rests on their curves *looking* sensible, which is weaker than
knowing the equilibrium was held.

**So the starter re-run is not a repair of the 29 %. It is the first campaign in which every data
point has a determined operating state.** Provisional on it:

- the duty distribution and its empty span between 0.35 and 0.63;
- the **200–280 code** shortfall and the 1.3–1.5× figure derived from endpoint slopes;
- the ~16–19 mV systematic offset (kicked decks; also subject to the mid-transient qualification);
- every population fraction quoted anywhere in this file.

**Not provisional on it** — these rest on their own evidence and stand:

- the bias loop has **three equilibria and no starter** (DC sweep);
- the transfer **polarity inverts** at reduced start-up energy (0.5 mA control);
- the pull-down **establishes the live state and is flat over 20×** in strength;
- `qarea` is **geometry-independent**, so HBT mismatch has no area lever, at any size.

**Order of work for the next session.** (1) Re-run the count with the 10 MΩ starter in the deck and
confirm the 29 % artefact vanishes. (2) Measure the shortfall directly by bisecting the **input
differential** at the code extremes — the quantity the whole session was about, never yet measured.
(3) Complete the starter's dynamic acceptance test: ramp the supply across a wide range of rates and
confirm the polarity never inverts. (4) The three-run family decomposition, to replace the ~79 % MOS
residual with a reading.

# THE STARTER NODE IS A CURRENT-MIRROR REFERENCE — THE SPECIFICATION MUST CHANGE (2026-08-11)

Netlist around `c_p2_comp`:

    XMP2_COMP  c_p2_comp c_p2_comp VCC_HBT VCC_HBT  sg13_hv_pmos   gate tied to own drain: DIODE
    XMP1_COMP  c_p1_comp c_p2_comp VCC_HBT VCC_HBT  sg13_hv_pmos   gate = c_p2_comp: MIRROR OUTPUT
    XQP2_COMP  c_p2_comp c_p1_comp e_p2_comp sub!   npn13G2 Nx=4   collector pulls the reference

**It is a pmos current mirror.** MP2 is the diode-connected reference, MP1 the mirrored output, and an
npn pulls current out of the reference branch.

**1. The node is not DC-isolated.** It has conducting paths through a pmos drain and an npn collector,
which rules out the isolation hypothesis that would have explained both the current-source failure and
the resistor failure. **The 10 MΩ convergence failures are therefore numerical** (consistent with the
non-monotonic-convergence section above), and seeding the solver should resolve them.

**2. A permanent pull-down on a mirror's diode node permanently increases the mirror current.** At the
live value (~0.975 V), 10 MΩ draws **~97 nA out of the reference branch**, and MP1 copies that shift
downstream. **The starter as specified is not a neutral addition that only matters at power-up — it
moves the bias of the entire compensation network for the life of the part.**

**Specification change.** The starter must **disengage once the loop is up**: a switched device, or one
referenced to a start-up detector, rather than a resistor that sits there forever. *A starter that
alters the steady-state bias is not a starter; it is a bias change with a start-up side effect.* The
3-stack nmos pull-down should be re-specified on that basis — and its node re-examined, since the
mirror reference is the most bias-sensitive point available.

**Unblock for the seeding plan:** the **no-starter deck converges** (45 chips run on it). **Dump node
voltages from that** to seed the starter runs — the starter perturbs one branch by ~10 %, so it is an
excellent initial guess. Do not wait for a nominal-with-starter solve; none has ever succeeded.

# CORRECTION TO THE NUMERICAL-FRAGILITY TABLE — SAME UNITS ERROR (2026-08-11)

The pull-down bisection table recorded earlier in this file used the includes **200M, 500M, 1G, 10G,
100G**. `G` is giga and correct; **`M` is milli and was not.** So that table compared **two shorts
against three gigaohm resistors**, and its headline — *"non-monotonic over four orders of
magnitude"* — is **withdrawn**.

**Corrected reading:**

| value | actual | result | note |
|---|---|---|---|
| 200M | **0.2 Ω** | converges | pinning the node makes the solve trivial |
| 500M | **0.5 Ω** | converges | same |
| 1G | 1 GΩ | fails | |
| 10G | 10 GΩ | fails | |
| 100G | 100 GΩ | converges | electrically negligible |

**Among genuine resistors the behaviour is still non-monotonic** — 1 G and 10 G fail while 100 G
succeeds, all three negligible loads, with no physical ordering. **The numerical-fragility conclusion
survives on thinner evidence; the "four orders" phrasing does not.**

**The consequence is worse than the previous section states.** Combining every correctly-read run:
**10 MΩ fails, 1 GΩ fails, 10 GΩ fails — the entire starter-relevant range, three decades wide.** The
only converging values are **shorts** (which destroy the bias rather than start it) and **100 GΩ**
(far too weak to act).

**So: no usable starter value has ever converged — only values that cannot work do.** Seeding the
solver from the converged **no-starter** solution is therefore required, not optional, before any
statement about the starter can be made at all.

# CONTROL CAMPAIGN — FINAL RESULT, n = 46 (2026-08-11)

Called complete at 46 draws. The distribution's **shape was identical at four checkpoints** (n = 19,
31, 44, 46) — two clusters, an empty span between them, same width, same edges — so further draws
tighten an already-wide interval without changing any decision on the board.

    complete draws                46
    usable (monotonic transfer)   32
    spoiled by per-code equilibrium selection   14  = 30%   (95% CI 17-44%)

    of the 32 usable:
      closest approach BELOW 0.5   12   (max 0.36)
      closest approach ABOVE 0.5   20   (min 0.63)
      within 0.45-0.55              0
      empty span   0.36 -> 0.63    width 0.27, and nothing has appeared inside it at any sample size

**Headline, as it may honestly be stated:**

> **Of 32 chips with a usable transfer, none can be brought within striking distance of balance by any
> code in the array.**

**Standing qualification, unchanged:** the operating state at each code is undetermined (the solver
selects among two stable equilibria per `alter`+`tran`), which is what the seeding run exists to
settle. The *shape* of this result is firm; its *values* are provisional on that.

**Next experiment, and the only one that unblocks the rest:** dump node voltages from a converged
no-starter draw, feed them as a **`.nodeset`** to a **10 MΩ** (`10MEG`, not `10M`) starter deck, and
see whether it solves. Nothing competes for the machine now.

# THE MEASUREMENT ARTEFACT IS FIXED — BY SEEDING, NOT BY THE STARTER (2026-08-11)

A mismatch-enabled, **no-starter** campaign draw with `.nodeset` seeded from a live (kicked-transient)
dump:

    code  0..14   duty 0.00    c_p1_comp 0.7344 .. 0.7364
    code 15..16   duty 0.34    c_p1_comp 0.7348, 0.7342

**The validity column is the result: `c_p1_comp` spans 2.2 mV across the entire sweep.** Against the
unseeded campaign, where the equilibrium flipped code-to-code and produced railed 0.00/1.00 in no
order. **The operating state is now determined and identical at every code**, and **the transfer is
monotonic.** 17 initial transient solutions, **0 operating-point failures.**

**So the 30 % artefact recorded above is repaired by one `.nodeset` directive** — no starter, no
circuit change. **This supersedes the prediction that the starter would fix it.** The starter returns
to being what it actually is: **a silicon defect, judged on the three-equilibria sweep and the
polarity inversion, not on measurement convenience.**

**The headline survives the clean measurement.** This chip still tops out at **0.34** and never
reaches 0.50 — exactly the lower-cluster shape of the n=46 control. The trim-range conclusion does not
depend on the artefact.

**Standing procedure from here, for every campaign deck:**

1. `.nodeset` seeded from a **live** dump — taken at the end of a **kicked transient** (the campaign's
   own 1 mA `IKICK2 0 xcomp.c_p1_comp` PWL, *not* another testbench's kick);
2. **`v(xcomp.c_p1_comp)` written as a second column**, so every draw proves its own validity;
3. reject any draw whose bias column is not near the live value.

**Next: re-run the count with the nodeset in place** — the first fully determined dataset, with no
artefact class and every draw usable.

**Seeded campaign verified in production (2026-08-11).** Draw 0, all 17 codes: bias column
**0.7307–0.7327, spread 2.1 mV**; duty monotonic (`0.00 ×14, 0.21, 0.33, 0.34`); best approach 0.34 —
the control's lower cluster. **The nodeset holds at every code.** This is the first campaign in which
every data point has a determined operating state, verified rather than assumed. The intermediate
0.21 is new: a stable operating state reveals structure the rail-hopping version destroyed.

*Expect the artefact class near zero rather than 30 %. Any draw that still returns non-monotonic is
now a real finding — flag those individually rather than bucketing them. If the duty distribution
reproduces the n=46 control's shape (two clusters, empty span, nothing reaching 0.50), the trim-range
conclusion is established on determined data and ceases to be provisional.*

# QUALIFICATION: MECHANISM CONFIRMED, OUTCOME NOT YET (2026-08-11)

**Applies to the "measurement artefact is fixed by seeding" section above, which over-claimed.**

Point-level metric — descents, i.e. codes where duty drops by more than 0.02:

| dataset | draws | mean descents/draw | median | clean | max |
|---|---|---|---|---|---|
| unseeded control | 46 | **0.57** | 0 | 70 % | 5 |
| seeded campaign | 6 | **0.50** | 0 | 67 % | 2 |

**Indistinguishable at this sample size.** So the claim that the disorder "collapsed by an order of
magnitude" is **withdrawn** — it came from comparing two plots against a recollection of the others,
and the recollection was itself an exaggeration (the draw quoted as chaotic has 2–3 descents, not 10).

**Separate the two claims, which were conflated:**

    MECHANISM   the bias column holds within ~2 mV at every code in every seeded draw.
                Verified. The unseeded runs demonstrably did not have this.
    OUTCOME     fewer anomalies in the transfer. NOT established. No detectable difference at n=6.

**The nodeset provably holds the operating state. Whether that buys cleaner transfers is a separate
empirical question, and it is open.** Recompute the descent comparison at **20 and 30 seeded draws**
before any statement about the outcome.

**Unchanged by this:** the seeding is still correct practice — a determined operating state is worth
having on its own terms, independently of whether it improves the transfer statistics — and the
standing procedure (live seed, bias column, reject on bad bias) stands.

# WITHDRAWN: EVERY EXTRAPOLATED SHORTFALL IN THIS FILE (2026-08-11)

**Applies to the 200–280 codes and the 1.3–1.5× recorded above, and to anything derived from the slope
at the end of a duty curve.** They are not merely uncertain — they are **arbitrary within an order of
magnitude.**

Demonstrated from data already in hand. For three seeded draws, extrapolate to the 0.50 crossing using
the **last** pair of samples, then the **pair before it**:

| draw | last three duty | last pair | previous pair | ratio |
|---|---|---|---|---|
| 0 | 0.21 0.33 0.34 | **24.93 mV** | **1.29 mV** | **19×** |
| 1 | 0.33 0.35 0.36 | 20.52 mV | 6.07 mV | 3.4× |
| 4 | 0.00 0.31 0.33 | 8.20 mV | 0.51 mV | 16× |

**Same chip, same data, two adjacent choices of slope, answer moves by up to 19×.** The duty curve has
a knee; the 16-point grid straddles it; the extrapolation reports **which side of the knee the last
samples happened to fall on**, not the distance to the crossing.

**Consequence: the direct measurement is the only route to the trim shortfall.** The input-differential
sweep moves from a nice-to-have to the critical path. Bracket already established on the first chip:
duty **0.35 at 0 mV**, **1.00 at −110 mV**, so the crossing lies between — and on the transition-width
argument (13 mV for the full swing, 15 % of it needed) it should land within **a few millivolts of
zero**, not tens. *That prediction is on the record before the measurement.*

**Standing check to adopt: extrapolate twice from different adjacent pairs and compare.** If they
differ by more than the tolerance you care about, the extrapolation is meaningless. **One line, and it
would have caught this at first use rather than after four separate quotations of the number.**

# THE TRIM CONCLUSION IS CONFIRMED ON DETERMINED DATA (2026-08-11)

**Seeded campaign, n = 21, every point with a verified operating state (bias column within ~2 mV
across each sweep):**

    best-achievable duty:  15 below 0.5 (max 0.37)   6 above (min 0.64)   within 0.45-0.55: ZERO

**Same shape as the n=46 control** — two clusters, empty span across the middle, nothing reaching
balance. **The trim-range conclusion is no longer provisional on the operating-state question.**

> **Of chips with a usable transfer, none can be brought within striking distance of balance by any
> code in the array** — now established on data where the operating state is determined and checked,
> not merely on data where it was undetermined.

*The magnitude of the shortfall remains unmeasured; every extrapolated figure is withdrawn (see the
preceding section). The direct input-differential sweep is the only route to it and is outstanding.*

# AND THE ARTEFACT EXPLANATION IS REFUTED — THE ANOMALOUS POPULATION MAY BE REAL

    descents/draw   unseeded 0.565 (n=46)    seeded 0.667 (n=21)
    difference      -0.101 +/- 0.252  =  -0.4 sigma
    clean draws     70%                      57%   (1.0 sigma, not significant)

**Seeding does not reduce the anomalies.** The explanation recorded earlier in this file — that the
non-monotonic draws are the solver selecting a different equilibrium per code — **is refuted.** The
state is demonstrably held (bias column within 2 mV) and **the anomalies persist at the same rate.
Whatever is switching, it is not that node.**

**Consequence for the design: the 30–40 % anomalous population can no longer be dismissed as a
measurement artefact. It may be real circuit behaviour, and it is now the largest unexplained item on
this design.** Next investigation should probe *which* node bistability produces a duty curve that
doubles back while `c_p1_comp` stays fixed — the candidates are downstream of the bias loop.

*Retained without change: seeding is still correct practice. A determined operating state is worth
having on its own terms, and it is what makes the confirmation above trustworthy.*

# THE DUTY METRIC WAS ONE BIT IN DISGUISE — READ THIS BEFORE ANY SECTION ABOVE (2026-08-11)

**Every CSV contains exactly one transition, at 8.5–8.8 ns in nearly all of them. Only the DIRECTION
differs.**

    duty 0.337   starts 0, ends 1, edge 8.61 ns      duty 0.646   starts 1, ends 0, edge 8.54 ns
    duty 0.353   starts 0, ends 1, edge 8.54 ns      duty 0.645   starts 1, ends 0, edge 8.66 ns

Averaging window 2–12 ns: an edge at 8.6 ns **rising** leaves 3.4 ns high of 10 → **0.34**; the same
edge **falling** leaves 6.6 ns → **0.66**. **Duty is the direction of a single comparator decision,
encoded by a fixed edge time. It is not a probability.**

**Withdrawn as artefacts of the metric:** the two clusters at 0.34 / 0.65 (they are the two logic
outcomes); the empty span between them (the absence of a third possibility); *"nothing reaches 0.50"*
(0.50 is not an available value); and **the trim-range headline confirmed earlier today.**

## Re-derived from the settled decision — and it reverses the conclusion

Output state is constant from 9.5 to 12 ns in four of five files checked: **the decision at 12 ns is
settled.** Taking final state vs code over 24 seeded draws:

    13 draws   single clean change, ALL at index 14 or 15  ->  code 508 or 546
    11 draws   multiple changes (the anomalous population)
     0 draws   no change

**The balance point is at code ~508–546 — INSIDE the array's 0–602 range.** This **contradicts and
replaces** the earlier "crossing lies outside the array in both directions".

## The sharpest open question now on this design

Thirteen chips all flip at one of **two adjacent** code steps. The step is 602/16 ≈ 38 codes ≈
**0.96 mV** input-referred, so the whole spread of balance points across thirteen mismatched chips is
**under 2 mV** — against a believed offset sigma of **8.5 mV**. **Those cannot both be true.** Either
mismatch is not producing the offset spread assumed, or the code axis is not moving the balance point
as assumed. **Resolve this before any sizing decision.**

## Replacement metric: edge time

Draw 0's file at its flip boundary resolves at **~10 ns** against **8.6 ns** everywhere else —
regeneration slowing as the input approaches balance, exactly as a comparator should. **Edge time is
the continuous quantity: it peaks at the balance point, it is measured rather than inferred, and it
assumes nothing about the output being probabilistic. Record final state and edge time per code.
Duty is deleted.**

# CORRECTED HEADLINE: THE ARRAY COVERS EVERY CHIP MEASURED (2026-08-11)

**Supersedes every trim-shortfall statement in this file.** Derived from the **control** campaign
(no nodeset) by the settled-decision method — the only combination of dataset and metric that has
survived scrutiny.

    37 clean draws of 46 (9 multi-change, see below)
    flip index   2: 8    3: 13   4: 2   |   13: 8   14: 5   15: 1
    BIMODAL, sd 5.33 index = 5.10 mV

    index 3   -> code  94  -> 207 codes from centre  ->  5.3 mV
    index 14  -> code 508  -> 207 codes from centre  ->  5.3 mV (opposite side)
    extreme (index 2)                                ->  6.2 mV
    half range = 301 codes                           ->  7.65 mV

**Every one of the 37 clean chips has its balance point inside the array, with ~20 % margin.
The correction range covers every chip measured.**

## Why the seeded campaign must not be used for this

    SEEDED  14 clean draws   flip index 14:6  15:8 ONLY   sd 0.49 mV, lower cluster absent

**The nodeset collapsed the distribution** — seeding every draw with identical node voltages pinned
each operating point to the same solution and erased mismatch's effect on the balance point. **The
seeded run is less trustworthy for offsets than the control, not more.** Seeding remains valid for
what it was verified to do (hold a determined operating state); it is **not neutral with respect to
the quantity being measured.**

## What this conclusion still owes

1. **9 of 46 control draws change decision multiple times** and are excluded here. ~20 % of the
   population unexplained; if they represent parts whose balance point is undefined, the coverage
   claim is incomplete.
2. **The distribution is bimodal at ±5.3 mV**, not unimodal about zero. That structure is unexplained
   and is not what random mismatch alone produces.
3. **Measured sd is 5.10 mV against a believed offset sigma of 8.5 mV.** Closer than the seeded run's
   0.49 mV, still a discrepancy worth resolving.
4. The **starter defect stands independently** (three equilibria, polarity inversion at reduced
   kick) and is unaffected by any of this.

*Confidence: the coverage claim rests on 37 draws, one metric, one dataset, and is the fourth headline
this design has had in twelve hours. It should be reproduced before anyone acts on it.*

# THE OFFSET SPREAD IS THE POWER-UP STATE, NOT MISMATCH (2026-08-11)

**This is the unifying result of the session and it supersedes every offset-sigma figure in this
file.** Control campaign, clean draws, split by cluster and measured within each:

| population | n | sd |
|---|---|---|
| lower cluster | 23 | **0.59 mV** |
| upper cluster | 14 | **0.62 mV** |
| seeded run (state pinned) | 14 | **0.49 mV** |
| **separation between clusters** | — | **10.30 mV** (±5.15 mV) |

**Three independent estimates of the mismatch-only spread, all ~0.5–0.6 mV.**

    device mismatch          ~0.6 mV of balance-point spread
    two power-up states      10.3 mV apart
    ratio                    ~17x

**The apparent offset spread is dominated by which state the part came up in, not by device
mismatch.**

**What this retro-explains.** The **8.5 mV offset sigma** used throughout this file was measuring **the
state split**, not device variation — which is why the HBT/resistor/MOS variance budget never
reconciled with anything. The bimodality is not unexplained structure: it is **two states, each with
its own balance point**. And the nodeset did not suppress mismatch generally — **it selected one
state**, and the state was most of the distribution.

## Design consequence — the quantified case for the starter

    with two power-up states     offset spread +/-5.15 mV   against 7.65 mV reach  ->  ~1.5x margin
    with one power-up state      offset spread +/-0.6  mV   against 7.65 mV reach  ->  ~12x margin

**The starter is not merely a correctness fix for parts that come up inverted. It is worth an order of
magnitude in trim margin**, and that figure comes from measured data rather than from an argument.

**Sequencing follows directly:** fix the starter first, then re-measure the offset distribution on a
single-state population, then size the array against ~0.6 mV rather than ~8.5. **The +20 % `I_FS`
proposal, already withdrawn, is not merely unnecessary — the array is oversized by roughly an order of
magnitude for a single-state part.**

# SETTLED PICTURE FROM EDGE LOCATION — SUPERSEDES ALL EARLIER CLASSIFICATIONS (2026-08-11)

Switching region located by **edge presence**, not by any derived metric. All 35 seeded draws:

    17 draws   edges at codes 1-3      (low cluster)
    18 draws   edges at codes 14-16    (high cluster)
     3 draws   one stray edge outside their block
     0 draws   scattered switching

**Every draw has a tight contiguous switching block. The "anomalous / multi-change" population does
not exist** — it was an artefact of reading the **final state** at codes where no transition occurred,
where the output merely sat where the operating point left it. All anomaly classes recorded earlier in
this file are withdrawn.

## The measured picture

| quantity | value | how obtained |
|---|---|---|
| split between clusters | **17 / 18** | edge location, 35 draws |
| cluster separation | **~12 mV** | balance codes ~56 and ~546 |
| displacement of each cluster from centre | **~6.2 mV** | 245 codes from code 301 |
| within-cluster spread (mismatch only) | **~0.6 mV** | 3 independent estimates |
| comparator transition width | **2–3 mV** | switching block is 2–3 codes wide |
| margin from balance point to array end | **1.4 mV ≈ 2.3 sigma** | 56 codes remaining |
| implied fallout | **1–2 % of a cluster** | 2.3 sigma one-sided |

## What this says about the design, in two parts

**1. The starter removes the bimodality.** A 17/18 split is exactly what two power-up states predict,
and pinning the state (nodeset) produced a single cluster. Fixing it removes ~12 mV of apparent spread
that is not device variation at all.

**2. A ~6.2 mV systematic displacement remains in each state, and that is what consumes the range.**
With the balance point 245 codes from centre, only 56 codes remain before the array runs out —
**1.4 mV, or 2.3 sigma against the 0.6 mV mismatch spread.** *The starter alone does not fix this.*
Removing the systematic displacement would leave ~7.6 mV of reach against 0.6 mV of spread — margin of
order 12 sigma.

**Order of work, unchanged in sequence but now quantified:** starter first (removes the bimodality and
makes every subsequent measurement single-valued), then locate and remove the 6.2 mV systematic
displacement, then size the array — which on this evidence is oversized for a single-state,
symmetric part.

# UNRESOLVED: A FACTOR OF 2.65 IN THE CODE-TO-MILLIVOLT CONVERSION (2026-08-11)

**Every millivolt figure in this file is provisional on this.** Two established numbers in this record
imply different scale factors:

    from the LSB     0.2078 mV at the collectors / stage gain 8.17  =  0.02543 mV/code
                     -> 602 codes = 15.3 mV full scale = +/- 7.65 mV
    from the reach   measured endpoints -671 / +669 uA -> +/- 20.3 mV input-referred
                     -> 40.6 mV / 602 codes = 0.0674 mV/code

**Ratio 2.65.** All conversions above used the first.

| quantity | if 0.02543 | if 0.0674 |
|---|---|---|
| systematic displacement per state | 6.2 mV | **16.4 mV** |
| within-cluster spread (mismatch) | 0.6 mV | **1.6 mV** |
| margin from balance point to array end | 1.4 mV | **3.8 mV** |
| comparator transition width | 2–3 mV | **5–8 mV** |

*Note the second column reconciles better with two independent measurements recorded earlier: the
~16 mV nominal offset from the no-mismatch sweep, and the 9–15 mV chaotic band read as a transition
width. That is suggestive, not decisive.*

**Do not resolve this by re-reading the derivations.** Both look sound and one is wrong — the exact
situation in which re-reading yields a confident wrong answer.

**Measure it.** Apply a known input differential (**5 mV, `VIN_P` = 1.2475**) and observe **how far the
switching block moves in codes**:

    moves ~74 codes  ->  0.0674 mV/code   (reach-derived)
    moves ~28 codes  ->  0.02543 mV/code  (LSB-derived)

A handful of simulations on an existing deck. **It calibrates the code axis in the only way that
cannot be argued with, and every quantitative conclusion in this file depends on it.**

# THE CODE AXIS, MEASURED: 0.0095 mV/CODE — BOTH RECORD VALUES WERE WRONG (2026-08-11)

**Resolves the 2.65× conflict above, by rejecting both candidates.**

    cal-base    0 mV differential   switching block at index 1-2
    cal-p5     +5 mV differential   switching block at index 15-16
    -> 5 mV moved the balance point 14 index steps = 526 codes
    -> 0.0095 mV/code   ->  full scale 5.7 mV,  reach +/-2.85 mV

| route | mV/code | verdict |
|---|---|---|
| LSB (0.2078 / 8.17) | 0.02543 | **2.7× too large** |
| reach (±20.3 mV) | 0.0674 | **7× too large** |
| **measured** | **0.0095** | **use this** |

**Corrected figures — every millivolt in this file is 2.7× smaller than written:**

    systematic displacement per state    ~2.3 mV    (was 6.2)
    within-cluster spread (mismatch)     ~0.22 mV   (was 0.6)
    comparator transition width          ~1 mV      (was 2-3)
    array reach                          +/-2.85 mV (was +/-7.65 or +/-20.3)

**The relative picture is unchanged.** The clusters sit at index 2 and 15 — **75 % of the way to the
ends whatever the conversion** — because cluster position and reach scale together. **The two-state
structure, the 17/18 split, the tight within-cluster spread and the small margin all stand.** Only the
absolute labels move.

**Caveat: one chip, one pair of runs.** Repeat on a second chip and at a second differential (10 mV
should move the block twice as far). *A calibration appearing in every result deserves at least one
confirmation of its own.*

*Note for whoever re-derives this: the LSB and reach values were each internally consistent and each
wrong. Do not attempt to repair them by inspection — the measured value is the only one with an
instrument behind it.*

# WITHDRAWN: THE 0.0095 mV/CODE CALIBRATION MEASURED THE STATE SPLIT (2026-08-11)

**The second chip contradicts the first by ~28×.**

    chip 2, base     10011111111111111   balance between index 2 and 3
    chip 2, +10 mV   10001111111111111   balance between index 3 and 4   -> ONE index step
    chip 1, +5 mV                                                        -> FOURTEEN index steps

**`cal-base` and `cal-p5` were separate ngspice invocations — separate mismatch draws — two different
chips.** Different chips land in one of two power-up states whose balance points differ by ~13 index
steps. **The 14-step shift was `cal-base` in the low cluster and `cal-p5` in the high one: the state
split, not the input response.**

**This is the one-process-per-condition trap** already diagnosed and fixed for the campaign, then
reintroduced in a two-run side experiment because two runs did not look like a campaign.

**Chip 2's pair landed in the same state**, so its one-step shift is the believable one — but a single
index step is the quantisation limit, bounding the constant only to **0.18–0.53 mV/code**.

**Status of the code-to-millivolt conversion: THREE mutually inconsistent values, none measured.**

    LSB-derived     0.02543 mV/code
    reach-derived   0.0674  mV/code
    chip-2 bound    0.18 - 0.53 mV/code
    withdrawn       0.0095 (confounded)

**No absolute millivolt figure in this file should be quoted until this is settled.** The **relative**
conclusions — cluster positions as a fraction of range, the 17/18 split, within-cluster spread as a
fraction of separation — are unaffected, being ratios on a single axis.

**Correct experiment:** **one ngspice process**, `alter` the input differential *and* the code inside
it, so both differentials are measured **on the same chip**, with finer differential steps than one
index of resolution.

# ROOT CAUSE CANDIDATE: THE INPUT PAIR IS SATURATED (2026-08-11)

**Read this before any quantitative section in this file.** Collector probe, one chip, one process,
at 10 ns:

| differential | c_p | c_n | c_p − c_n |
|---|---|---|---|
| 0 mV | 1.13828 | 2.49892 | −1.360637 |
| +50 mV | 1.13992 | 2.49821 | −1.358294 |
| +100 mV | 1.13914 | 2.49798 | −1.358840 |
| −100 mV | 1.13773 | 2.49980 | −1.362069 |

**A 200 mV input swing moves the collector differential by 3.8 mV — a stage gain of 0.019 against the
design record's 8.17, short by ~430×.**

**And the absolute values say why: `c_p − c_n = −1.36 V`, with `c_n` at the supply rail (2.4989).**
The pair is **driven hard into saturation with one side pinned to the rail.** A saturated stage has no
gain — which explains the complete absence of input authority (H-872, H-883).

**Consequence: the switching measured throughout this file is not the comparator deciding about its
input.** Every "balance point" recorded here is the switching point of whatever else responds to the
code. **Every quantitative claim in this document — offsets, spreads, margins, cluster separations,
transition widths, correctable fractions — was measured through a stage that was not amplifying.**

**Unaffected** (separate sweeps, structural): three equilibria and no starter; polarity inversion at
reduced start-up energy; `qarea` geometry-independence.

## Next test, and it decides which kind of fault this is

**Sweep the input common mode** — `IN_P` and `IN_N` together, ~0.8 V to ~2.0 V — and find where the
collectors leave the rail and a differential gain appears.

    a working window exists and 1.245 V is outside it  ->  TESTBENCH fault; fix the bias, re-measure
    the window includes 1.245 V                        ->  front-end DESIGN fault, and it is the headline

**Note for the record:** both inputs have sat at **1.245 V** in every deck this session, and nobody
ever verified the input pair can operate there. **One printed collector voltage at the start would
have shown 1.36 V of separation.**

# PHASE-CORRECT FRONT-END DIAGNOSIS: UNDER-BIASED, GAIN 0.0985 (2026-08-11)

**Supersedes the earlier saturated/dead-input entries, which were sampled at the wrong clock phase.**

**This is a track-and-latch comparator.** `XQCLK_TRACK e_track CLK_P e_tail` switches the input pair's
tail with the clock; `XQ3`/`XQ4` are a cross-coupled latch on `c_n`/`c_p`. Clock high 400 ps per 1 ns.
**87 % of output transitions occur in the latch window, peaking 100–350 ps after the clock falls** —
textbook behaviour, and it validates reading the settled state at 12 ns as the last latched decision.

**Track-phase probe (`CLK_P` verified at 1.2000 V):**

| phase | e_track | c_p − c_n | differential |
|---|---|---|---|
| TRACK | 0.57567 | −1.333459 | 0 mV |
| TRACK | 0.59899 | −1.323613 | +100 mV |
| latch | 0.60602 | −1.356677 | 0 mV |

    V_BE during track = 1.245 - 0.576 = 669 mV      (HBT wants 850-900 mV)
    gain across 100 mV = 9.85 mV / 100 mV = 0.0985  (design value 8.17 -> ~83x short)
    c_p - c_n = 1.33 V apart DURING TRACK           (should be near balance)
    e_track moves only 30 mV latch -> track         (a tail turning fully on should pull it hard)

**Diagnosis: the tail current is far too small.** The input pair is badly under-biased even when its
switch is on, the stage has a gain of ~0.1 instead of ~8, and the collectors never leave the rail.
**This explains the 100 mV input insensitivity that survived every retraction.**

**The tail is biased from the compensation network — the loop with three equilibria and no starter.**
So the missing starter remains the leading root-cause candidate, now with phase-correct evidence
beneath it.

**Next:** print the tail current directly and trace its bias path from `e_tail` back into the
compensation network.

# THE CHAIN CLOSES: `c_p1_comp` BIASES THE COMPARATOR'S TAIL SOURCE (2026-08-11)

**From the netlist, everything on `e_tail`:**

    XQCLK_TRACK  e_track CLK_P e_tail       track switch emitter
    XQCLK_LATCH  e_latch CLK_N e_tail       latch switch emitter
    XQS_COMP     e_tail c_p1_comp e_scomp   npn: collector e_tail, BASE = c_p1_comp
    XRDEG_SCOMP  e_scomp VSS  rppd w=24.0u l=0.50u

**`XQS_COMP` is the tail current source for the whole comparator — track pair and latch pair both —
and its base is the compensation node of the loop with three equilibria and no starter.**

**Computable from one measured number.** `c_p1_comp` = **0.7324 V** (measured). With little current
flowing, `e_scomp` sits near VSS, so **V_BE(XQS_COMP) ≈ 732 mV** against the 850–900 mV these devices
need.

    tail source weakly on
      -> tiny tail current            (confirmed: e_track moves only 30 mV latch -> track)
      -> input pair starved           (confirmed: V_BE 669 mV during track)
      -> gain 0.0985 instead of 8.17  (measured, phase-correct)
      -> collectors railed 1.33 V apart during track
      -> 100 mV at the input does nothing

**Every link is now measured or read off the netlist.**

## This changes the starter requirement

Avoiding the dead equilibrium (0.232 V) is necessary but **not sufficient**. The "live" equilibrium at
**0.812 V gives V_BE ≈ 812 mV — marginal, not comfortable.**

> **The requirement is not merely that the loop starts. It is that it settles high enough to bias the
> tail properly — and 0.812 V may not be high enough.**

**Owed, and it is now the top item:** determine what `c_p1_comp` must be for `XQS_COMP` to deliver its
intended tail current, and whether the loop's live equilibrium reaches it. If it does not, the fix is
a bias-level change in the compensation loop, not only a start-up circuit — and every measurement in
this file was taken through a comparator running at ~1 % of its designed gain.

---

## 2026-08-11 — two faults found in the merged comparator, and what every earlier number means

**Read this before using any number measured on `C169-SOURCE-coarse-dac-v7-merged.spice`.**

### The two faults

Both were introduced when the trim DAC was merged into the comparator. Neither is visible from inside
either block; both live in the seam.

**1. The correction array draws ~20x the comparator's tail current.**

    XQS_COMP (tail)      1.24 mA measured
    150 unary segments   170 uA each  = 25.5 mA
    2 binary segments                 =  0.1 mA
    collector loads      XRC1/XRC2 rppd w=1.0u l=0.838u ~= 218 ohm

~21 mA into 218 Ω wants to drop 4.6 V on a 2.5 V supply. It cannot, so the collectors are dragged to
**0.26 V** against a design intent of 1.9–2.5 V. Everything downstream starves: emitter followers at
**0 V**, level shift passing zero, CMOS pair below threshold, sense amp receiving **0.04 mV**, hold latch
frozen, output stuck. Nine links, all measured.

The original schematic (`cace_ihp_sg13g2_demo/netlist/schematic/p1_comparator.spice`) states the intent:

    ISET e_tail VSS DC 2.0m
    RC1 VCC_HBT c_n 300      RC2 VCC_HBT c_p 300

**Those loads carry the tail current and nothing else. There was never a current budget for a trim
array.** The merge reduced them 300 → 218 Ω, which buys ~0.75 mA of headroom. The array draws 25.5.

**Budget: ~3.5 mA for the array** (218 Ω loads, collectors ≥1.9 V, 2.0 mA tail). Reducing segments to
**23 µA** restores collectors to **1.86 V**, followers to **1.06 V**, and gives a **74 mV** sense-amp
differential.

**2. `SACLK`, the sense amplifier's strobe, is a dangling node.**

It appears exactly three times in the netlist — `XSA_T` (tail), `XPC1`, `XPC2` (precharge) — **all three as
gate terminals, zero times as any device's output.** Nothing drives it; it floats at ~0.72 V. The stage
never evaluates, and the hold latch repeats a stale decision indefinitely. A netlist comment states the
intent: *evaluates on CLK_N high*. **The connection was never made.**

### Trim sizing — a resolution problem, not a range problem

Input-pair differential transconductance `gm = I_tail/(2 VT)` = 23.98 mA/V at 1.24 mA. A segment steered
across changes the output current by `2 I_seg`; input-referred weight is `2 I_seg / gm`.

    as-built  : unary step 14.2 mV | binary LSB 3.17 mV | range +/-1063 mV
    at 23 uA  : unary step  1.92 mV | binary LSB 0.43 mV | range +/- 144 mV
    measured offsets: +8.6, +2.5, +1.16 mV

**As built the array has ~100x more range than needed and cannot step finer than 3.2 mV — larger than
most of the offsets it exists to null.** That is how "the trim cannot correct this part" becomes "we need
more range" when the actual defect is granularity. **Derived, not yet measured; a direct reach
measurement is in progress.**

### What every earlier measurement means

**Every campaign on this block ran 12 ns transients. The bias loop needs ~100 ns to settle and the
comparator produces no decisions at all until it does.** Twelve nanoseconds lies entirely inside the
start-up window. The 92 output transitions once used to conclude the comparator works were **collected
during start-up**; in the settled state, across six independent runs including one of 1 µs, **the output
never changes.**

**So no number measured on this netlist before 2026-08-11 describes normal operation.** They are not
approximate — they describe a circuit whose decision nodes sit at 0.26 V and whose sense amp is never
strobed.

Also: **175 of 429 decks in the `correct250` campaign carry a repeating 30 µA/10 ns injection into the
bias node (`IKICK`) and 254 do not.** Any statistic pooled across that fleet mixes two different circuits.

### Method constraints specific to this PDK

**Mismatch is drawn once per ngspice process at netlist expansion and cannot be seeded.** Therefore:

- **a process is a chip.** Two files are two parts, however identical the decks.
- **no measurement can be resumed.** An interrupted sweep must be redone, not continued — a continuation
  is a different chip filed under the same name.
- **nothing transfers between parts.** No shared coarse scan, no bracket reuse, no caching. Per-part cost
  is irreducible; throughput comes only from running parts concurrently.
- **sample in the correct clock phase and print the clock beside every sample.** Track and latch phases
  give different answers; a precharge-phase sample reads both sense nodes at the rail and carries no
  decision.
- **gate every output on run completion.** A truncated transient still writes a file whose columns parse
  and whose forced nodes read their forced values.

---

## 2026-08-12 — the offset distribution, and what the correction array should be

**This answers the question the work was commissioned around, and it answers it in the opposite
direction to how it was posed.**

### The measurement

Input differential swept per part in a **single ngspice process** (mismatch is drawn once per process,
so one process = one part; a sweep cannot be resumed or split), 5 mV grid over ±300 mV, decision read at
the **latch phase** with the clock recorded beside every sample, every file gated on run completion, and
any part showing more than one sign change excluded rather than reported.

    n = 16 parts
    mean  +0.16 mV      sd 8.59 mV      range -17.5 .. +12.5 mV

**The mean is zero within resolution.** There is no systematic offset to remove in the design — this is
a zero-centred random spread, which is what device mismatch should look like. **Sigma ~8.6 mV is the
number the array must be sized against.**

### What the array should be

    requirement:  range >= +/-5 sigma = +/-43 mV      step <= 0.1 sigma = 0.86 mV

Range must cover the tails of the population, not the average part. Step must be a small fraction of
sigma, or a part can be brought close to centre but not to it.

### What the array is

    as-built (170 uA/segment):  range +/-1063 mV = 124 sigma | step 3.17 mV = 0.37 sigma
    at 23 uA/segment         :  range +/- 144 mV =  17 sigma | step 0.43 mV = 0.05 sigma

**As built the array is wrong in both directions at once: ~25x more range than required, and a step
about four times too coarse.** It can bring any part close to centre and few parts to it. *That is how
"the trim cannot correct this part" becomes "we need more range" — the array reaches a volt; it simply
cannot step finer than 3 mV.*

**At 23 µA per segment it meets both requirements with margin.** That reduction was specified for an
unrelated reason — the array was drawing **25.5 mA against a 1.24 mA comparator tail** and pinning the
decision nodes at 0.26 V — and it happens to size the trim correctly as well.

### Caveats, in order of how much they should worry you

1. **n = 16.** The uncertainty on a sd from 16 samples is ~18 %, and the **tails — precisely what the
   range depends on — are the least determined part of a small sample.**
2. **Simulated mismatch at one corner and one temperature.** These are `mm_ok=1` agauss draws from the
   PDK, not silicon, and not swept over process corners or temperature.
3. **Convergence failures are not evenly distributed across parts** (0 to ~40 % per part). Parts that
   failed heavily were re-run with looser solver settings rather than dropped. **The correlation between
   a part's failure count and the magnitude of its offset is −0.38** — negative, i.e. difficult parts
   have *smaller* offsets, which is the opposite of the feared bias. Weak at this n, but it points the
   reassuring way.
4. **Everything here post-dates two repairs** — the array current and the dangling sense-amp strobe. It
   describes the repaired circuit, not the one in the merged netlist.

---

## Update, 2026-08-11 23:2x — n = 18

Two parts previously listed as unresolved were recovered. Neither had failed to reach its decision
point; both had *found* it, with the intermediate points missing because the solver rejected them,
leaving a 25 mV bracket that the analysis correctly refused to report as a measurement. Re-running
only the rejected points inside each bracket — **four simulation points per part** — closed both.

    part 20   50 valid  17 rejected   crossing  +7.5 mV +/-2.5
    part 26   56 valid  11 rejected   crossing  -2.5 mV +/-2.5

Revised distribution:

    n = 18 parts
    mean  +0.42 mV      sd 8.28 mV      range -17.5 .. +12.5 mV

The conclusion is unchanged and slightly firmer. sd moved 8.59 -> 8.28 mV (3.6 %), well inside the
~18 % uncertainty a sample this size carries, which is what convergence rather than discovery looks
like. Against sd = 8.28 mV the requirement is **range >= +/-41 mV, step <= 0.83 mV**; the as-built
array gives **+/-1063 mV = 128 sigma and a 3.17 mV = 0.38 sigma step**, and at 23 µA/segment
**+/-144 mV = 17 sigma and 0.43 mV = 0.05 sigma**. Still wrong in both directions as built; still
correct at the reduced current.

Caveat 1 above now reads n = 18 (sd uncertainty ~17 %); caveat 3's bias correlation is **−0.34 over
18 parts**, unchanged in sign and still the reassuring direction.

Two parts remain outside the sample and are recorded rather than dropped, because the count of parts
that could not be measured is part of the result:

    part 16   9 valid, 9 rejected -- 50 % failure even at the looser solver settings; unmeasurable
    part 25   36 valid, 7 rejected -- no crossing found in -300..+5 mV; still sweeping

**Twenty attempted, eighteen measured, one unmeasurable, one still running.** The rule-of-three bound
on the unobserved fraction is 3/18 = 17 %: a trim range set from this sample covers the parts seen,
not the parts that exist.

**The step figure of 3.17 mV/segment is still derived, not measured.** A direct measurement — one
part, three trim codes, one process — is running. Until it lands, every statement above comparing a
measured spread against a calculated step is comparing one measurement to one calculation.

---

## Correction, 2026-08-11 23:4x — the step conclusion was wrong by 4x (units)

**The resolution conclusion above is withdrawn.** The array netlist states its own encoding at
`C169-array23-strobe.spice:268`:

    * V7 MERGE: 2-binary (codes 0-3) + 150 unary elements of 4 LSB (codes 4-603).
    * 603 codes, 151 handovers, segmenting at b1. Handover = code 3->4 = VCODE 0.03->0.04.

Two things follow.

**A unary segment is 4 LSB, not 1.** The 3.17 mV I derived is a *segment weight*. The resolution — the
smallest change the trim can make — is a quarter of it: **0.79 mV as built, 0.107 mV at 23 µA/segment.**
I compared a segment weight against a resolution requirement, which is comparing a quantity to a
requirement four times finer than the quantity's own unit.

    requirement (sd 8.28 mV):  step <= 0.1 sigma = 0.83 mV
    as built,   per LSB     :  0.79 mV = 0.096 sigma   -- MEETS, marginally
    at 23 uA,   per LSB     :  0.107 mV = 0.013 sigma  -- meets comfortably

So **the array as built does not have a resolution problem.** The claim that it is "about four times too
coarse" was an artifact of the unit error and is retracted. What survives is the range half of the
finding: the array is grossly oversized in range, and the current reduction specified for the 25.5 mA
overdraw remains correct. **The range figure of +/-1063 mV was derived in segment units and has not been
re-derived per code; treat its magnitude as unverified while its direction stands.**

**The code input is scaled 0.01 V per code.** Centre is code 301 = `VCODE 3.01` (what the campaign
uses). The direct step measurement was launched at `VCODE 0.0 / 3.0 / 6.0`, which is codes **0, 300 and
600** — the bottom, middle and top of the array, not codes 0, 3 and 6.

That explains its code-0 sweep finding no crossing in +/-80 mV, and the null result carries information.
If the code-0 crossing lies beyond 80 mV while the part's own offset is within ~25 mV, then 300 codes are
worth more than 55 mV, so **LSB >= 0.18 mV** — about twice the derived 0.107 mV. A lower bound from a
sweep that measured nothing.

A replacement measurement at codes 300 / 400 / 500 (hundred-code levers about centre) is running. Until
it lands, every step figure here remains derived, and the derivation has now been wrong once.

### First measured constraint on the step, 2026-08-11 23:5x

Same part, same process, three codes (mismatch drawn once, so these three numbers are comparable):

    code 300 (VCODE 3.0)   crossing  -2.50 mV  +/-2.50   [33 points, 0 rejected]
    code   0 (VCODE 0.0)   NO crossing in -80..+80 mV    [33 points, 0 rejected]
    code 600 (VCODE 6.0)   in progress

The code-300 crossing is this part's offset near centre code. The code-0 sweep found nothing in the
window, so the crossing moved by **more than 77.5 mV over 300 codes**:

    LSB > 0.258 mV  (this deck is the 23 uA/segment array)

**That is at least 2.4x the derived 0.107 mV/LSB.** The derivation is low, and it is now low by a
measured amount rather than a suspected one. Note this bound needs no assumption about the part's
intrinsic offset -- both crossings are the same part in the same process, so the offset cancels.

Carried through, as bounds rather than results:

    at 23 uA :  LSB > 0.26 mV = 0.031 sigma   range > 603*0.26 = +/-78 mV = 9.4 sigma
    at 170 uA:  LSB > 1.9 mV  = 0.23 sigma    (scaling by the ~7.4x current ratio)

If that scaling holds, **the as-built array fails the 0.1 sigma resolution requirement after all** --
by about 2.3x, not the 4x claimed and retracted above, and from a bound rather than a measurement. The
retraction stands as written: the 4x figure was wrong. Whether the true figure is 1x or 2.3x is what
the codes 300/400/500 measurement is for. **Do not quote a resolution verdict from this section.**

The range picture also tightens: at 23 uA the array covers >9.4 sigma rather than the 17 sigma derived,
still comfortably above the +/-5 sigma requirement.

### Step bounded from below by a same-chip subtraction, 2026-08-12 00:0x

Second step deck (`stepmid`, codes 300/400/500, identical to `stepfast` apart from the codes):

    code 300   crossing +42.50 mV +/-2.50   33 points, 0 rejected
    code 400   NO crossing, LOW at both -80 and +80  => crossing below -80 mV

Both from one ngspice process, so the part's offset cancels and no assumption enters:

    > 122.5 mV of movement over 100 codes   =>   LSB > 1.225 mV   (23 uA/segment array)

**That is >11x the derived 0.107 mV/LSB.** The first deck's bound (LSB > 0.275 mV from 300 codes) is
consistent with it: both are floors, and the larger floor wins. Direction is downward with increasing
code, confirmed on both chips by the output state at the window edges.

Consequence, and it is a real verdict rather than a bound-shaped hint, because the requirement is an
upper limit and a lower bound is enough to violate one:

    requirement       step <= 0.1 sigma = 0.83 mV
    measured floor    step  > 1.225 mV = 0.148 sigma      -- FAILS, at 23 uA/segment
    as-built (x7.4)   step  > ~9 mV = ~1.1 sigma          -- fails by ~an order of magnitude

So the array is **oversized in range and too coarse in step**, which is the shape of the original
claim -- but the original claim was reached by a broken comparison (H-1017) and its 4x figure was
wrong. The correct statement is a floor of 0.148 sigma at reduced current, from a subtraction on one
chip, pending the short-lever measurement that will give a value instead of a floor.

### Open inconsistency: two step-deck chips sit 45 mV apart

    stepfast chip, code 300:   -2.50 mV
    stepmid  chip, code 300:  +42.50 mV

The decks are identical apart from the code list, including solver tolerance (`reltol=1e-3`, matching
20 of the 24 campaign decks; only the four rescue decks used 3e-3). Against the campaign's **sd
8.28 mV over 18 parts**, two draws 45 mV apart is a ~5 sigma separation.

**Either we have drawn a rare part, or the campaign's sd is wrong -- and the campaign's sd is the
headline number of this study.** The check is nearly free, because the code-300 sweep *is* an offset
measurement: run it alone on 6-8 fresh processes and compare the spread against 8.28 mV. Commissioned.
Until it returns, treat sd = 8.28 mV as unconfirmed by any second method.

### Resolved, 2026-08-12 00:2x — the 45 mV disagreement was self-inflicted; sd 8.28 mV stands

The "open inconsistency" recorded above is closed, and the cause was the 20 ns stop time I introduced
to speed the step decks up. It was validated in the wrong place.

Reading the campaign's own 50 ns files at 20 ns instead of 50 ns -- same files, same parts, nothing
changed but the moment the decision is read:

    decision read at 50 ns:   n=15  mean +0.83 mV  sd  9.00 mV   -17.5 .. +12.5
    decision read at 20 ns:   n=17  mean -1.91 mV  sd 15.40 mV   -27.5 .. +32.5

Settling time measured against distance from the decision point (campaign files, last output
transition through 0.6 V):

    >30 mV from crossing   n=695   median  8.9 ns   90th 14.9   max 21.9
    10-30 mV               n=104   median  9.9 ns   90th 20.9   max 28.0
    <=10 mV                n= 52   median 11.0 ns   90th 25.9   max 45.0

**Near the decision point the comparator can still be resolving at 45 ns.** The 20 ns figure came from
reading one file at -400 mV -- as far from the decision point as the sweep goes -- and applying its
settling time to the points near the crossing, which are the only points the measurement depends on.
Timing was measured in the region where timing does not matter.

Consequences:

  - **sd = 8.28 mV is not contradicted.** The step decks' apparent spread (23.5 mV over 7 parts) is
    inflated by the short run; the campaign's is not compressed. The 5 sigma alarm was manufactured.
  - **`tstop` returns to 50 ns** and must not be shortened again without repeating the settling check.
    50 ns is only just adequate against a 45 ns worst case.
  - The window narrowing (33 points instead of 161) is unaffected and remains the larger speedup.
  - **The measured step of 6.0 mV/LSB from the 10-code lever is withdrawn pending a 50 ns re-run.**
    It was implausible on its face -- 603 codes x 6 mV would need 3.6 V of range on a 2.5 V supply.

Everything derived from 20 ns runs tonight -- both step decks, all eight offset runs, the LSB floors of
0.275 and 1.225 mV -- is suspect in magnitude. The *direction* results survive (the crossing moves down
with increasing code, and every long lever overshoots the window), because those depend on the sign of
a large movement rather than on when the decision is read.

---

## MEASURED: the trim step is 2.50 mV/LSB, 2026-08-12 00:5x

One part, one ngspice process, 50 ns runs, 10-code lever (offset cancels between the two crossings):

    VCODE 3.00 (code 300)   crossing +27.50 mV +/-2.50   33 valid, 0 rejected
    VCODE 3.10 (code 310)   crossing  +2.50 mV +/-2.50   20 valid, 1 rejected
    -----------------------------------------------------------------------
    10 codes move the decision point -25.00 mV   =>   LSB = 2.50 mV +/-0.50

**This is a measurement, not a bound and not a derivation.** It supersedes every step figure earlier in
this file, including the withdrawn 6.0 mV/LSB (which was the same measurement at the bad 20 ns stop --
inflated 2.4x, exactly the direction H-1023 predicts).

### It agrees with an independent physical calculation

Full-scale from the measured step, against full-scale from device sizes -- two routes that share no
arithmetic:

    from the measurement:  603 codes x 2.50 mV        = 1507 mV = +/-753 mV
    from the devices    :  150 seg x 23 uA x 218 ohm x 2 = 1504 mV = +/-752 mV

Agreement to 0.2 %. That is the plausibility check I skipped before reporting 6.0 mV/LSB, which would
have needed 3.6 V of range from a 2.5 V supply and should never have left my hands.

It also locates my original error exactly: one segment is 23 uA x 218 ohm x 2 = **10.0 mV differential**,
i.e. 2.50 mV/LSB. My derived 0.43 mV/segment was low by 23x, and dividing it by 4 for the LSB made it
worse. The device sizes were always sufficient to get this right.

### Sizing verdict, now measured on both sides

    sd = 8.28 mV (n=18)      requirement:  range >= +/-5 sigma = +/-41 mV     step <= 0.1 sigma = 0.83 mV

    at 23 uA/segment (as simulated):  range +/-753 mV = 91 sigma  |  step 2.50 mV = 0.30 sigma
    at 170 uA/segment (as built)   :  range would exceed the supply |  step ~18.5 mV = 2.2 sigma

**Range is oversized ~18x. Step is ~3x too coarse.** Both at the *reduced* current; as built it is worse
in both directions. This is the same shape as the claim retracted in H-1017 -- and close to it
numerically -- but reached by measurement rather than by comparing a segment weight against a per-LSB
requirement. The retraction stands: that figure was unsupported when published.

### What the current should be

Segment current scales the step and the range together, so one number sets both:

    23.0 uA :  step 0.30 sigma (fails)   range 91 sigma
     7.6 uA :  step 0.10 sigma (exactly at limit)   range 30 sigma
     4.0 uA :  step 0.05 sigma            range 16 sigma      <-- comfortable on both
     1.3 uA :  step 0.016 sigma           range  5 sigma (at the range limit)

Anything from ~1.3 to ~7.6 uA/segment satisfies both requirements; **~4 uA/segment sits centrally with
margin on each side**, a further 5.75x reduction from the 23 uA already specified for the overdraw fault.
The array is currently sized as though range were scarce, when range is the requirement it exceeds by
nearly two orders of magnitude.

Caveats unchanged: n=18 (going to ~35), one corner, one temperature, simulated mismatch, and everything
post-dates two repairs. The 20-code lever (code 320) is still running and will halve the +/-0.50 mV
uncertainty and give a linearity check.

## n = 27 — the fresh batch confirms the spread, 2026-08-12 01:0x

Eight parts run at `VCODE 3.01` (code 301), 50 ns, same deck and analysis as the campaign, so they
join the sample rather than sitting beside it:

    campaign (cam6)     n=19  mean -0.13 mV  sd 8.39 mV   -17.5 .. +12.5
    fresh batch (off6)  n= 8  mean +4.69 mV  sd 7.49 mV    -7.5 .. +17.5
    ---------------------------------------------------------------------
    COMBINED            n=27  mean +1.30 mV  sd 8.30 mV   -17.5 .. +17.5

**sd 7.49 against 8.39 from eight independent draws.** The apparent 5 sigma disagreement recorded
earlier is now closed from both directions: it was entirely the 20 ns stop time, and a proper 50 ns
batch agrees. The mean difference (4.8 mV) is 1.3 standard errors -- not significant at this n.

    sd uncertainty at n=27          ~14 %   (was ~17 % at n=18)
    rule of three, unobserved tail  11.1 %  (was 16.7 %)
    distribution is now symmetric   -17.5 .. +17.5 mV

### Sizing verdict on 27 parts — unchanged

    requirement:  range >= +/-5 sd = +/-41.5 mV     step <= 0.1 sd = 0.83 mV

    at 23.0 uA/segment:  range +/-753 mV = 91 sd   step 2.500 mV = 0.300 sd   FAILS step
    at  7.6 uA/segment:  range +/-249 mV = 30 sd   step 0.826 mV = 0.100 sd   at the limit
    at  4.0 uA/segment:  range +/-131 mV = 16 sd   step 0.435 mV = 0.052 sd   RECOMMENDED
    at  1.3 uA/segment:  range +/- 43 mV =  5 sd   step 0.141 mV = 0.017 sd   at the range limit

sd moved 8.28 -> 8.30 mV on adding eight parts and the recommendation does not move at all. **~4 uA per
segment sits centrally between the two limits**, with the usable band running from about 1.3 to 7.6 uA.

## A flat decade: possible differential non-linearity, 2026-08-12 01:2x

The 50 ns lever deck completed all three codes on one part, one process:

    code 300   crossing +27.50 mV +/-2.50
    code 310   crossing  +2.50 mV +/-2.50      -25.00 mV over 10 codes  =>  2.50 mV/code
    code 320   crossing  +2.50 mV +/-2.50        0.00 mV over 10 codes  =>  <=0.5 mV/code

With the 5 mV grid the second decade's shift lies between -5 and +5 mV, so **its incremental step is at
most one fifth of the first decade's, and may be zero.**

**This is a worse class of defect than either problem recorded above.** Excess range is waste. A coarse
step is a resolution limit that can be quoted. A dead zone means **there are offsets no code can
correct**, however much range exists and however fine the average step is. The 20-code average of
1.25 mV/code is a fiction: it describes a jump followed by a flat, not a ramp.

**The measured step of 2.50 mV/LSB is therefore a local figure, valid across codes 300-310 on one part.**
It should not be treated as the array's step until the transfer curve is known. The sizing verdict above
(range 91 sigma, step 0.30 sigma, recommend ~4 uA/segment) rests on that local value and is provisional
pending the fine sweep.

What to look for: the array segments every 4th code with 151 handovers across its range, and a handover
is exactly where a segmented converter goes non-monotonic if the binary sub-elements do not match the
unary element they hand over to. A flat sitting **on** a handover boundary is a known fault with a known
fix; a flat sitting somewhere arbitrary is something else. A fine sweep of every code from 305 to 325 in
one process, at a 2.5 mV grid, is running -- three points cannot distinguish these and should not be
asked to.

## n = 33 at code 301, 2026-08-12 01:4x

All four sources pooled, on a deliberately strict gate (the campaign's own report resolves a few more,
so read this as a floor):

    campaign (cam6)   15      fresh batch (off6)    5
    recovery (cam5r)   8      fresh batch (off7)    5      ->   n = 33

    mean +1.89 mV     sd 7.37 mV     -17.5 .. +12.5 mV
    sd uncertainty ~12 %            rule of three: 9.1 % unobserved-fraction bound

    requirement at this sd:   range >= +/-36.8 mV     step <= 0.74 mV

The recovery of already-simulated parts (see 2026-08-12 00:4x entry) contributed **more parts than
either batch of fresh simulation**, at roughly a third of the cost per part.

sd has moved 8.59 -> 8.28 -> 8.30 -> 7.37 mV as n went 16 -> 18 -> 27 -> 33. The last step is the
largest recent move and sits at the edge of the ~12 % uncertainty band; it is not yet a reason to
revise the recommendation, which depends on sd only through a ratio, but it is worth watching rather
than averaging away.

### The step reproduces on a second chip, 2026-08-12 02:0x

First two codes of the fine transfer sweep, a different ngspice process (so a different mismatch draw)
from the lever deck, at a 2.5 mV grid:

    code 300   crossing +13.50 mV +/-1.50      (lever deck, other chip: +27.50)
    code 309   crossing  -9.00 mV +/-1.00
    9 codes move the crossing -22.50 mV   =>   2.500 mV/LSB

**Identical to the lever deck's 2.500 mV/LSB on a different chip.** The two parts' absolute crossings
differ by 14 mV, as independent mismatch draws should; their step does not differ at all within the
resolution available.

This verifies an assumption made hours earlier rather than leaving it asserted. When the fast step deck
was started alongside the slow one, the justification for accepting a fresh mismatch draw was that "the
step is set by segment current and load resistance and should be very nearly the same part to part,
unlike the offset". That licensed a cross-process comparison. It is now measured on two chips and holds.

    quantity   chip A      chip B      chip-to-chip
    offset     +27.50 mV   +13.50 mV   differs by 14 mV  (expected: sd 7.4 mV)
    step        2.500       2.500      no measurable difference

So the step may legitimately be characterised on one part, and the offset may not -- which is what the
whole campaign structure assumes.

---

## Correction, 2026-08-12 02:2x — two parts were spliced from two chips; n = 39 clean

**Parts 20 and 26 are withdrawn from the sample.** They were "recovered" earlier by re-running only the
missing points inside their brackets, in a *new ngspice process*. Mismatch is drawn per process, so
those points came from a different chip and were spliced into another chip's sweep.

Direct evidence:

    part 20 retry points (+10,+15,+20,+25 mV): LOW, LOW, LOW, LOW -- no sign change of their own
    part 26 retry points (  0, +5,+10,+15 mV): LOW, LOW, LOW, LOW -- no sign change of their own

Each original sweep was HIGH below its bracket; the retry chip reads LOW throughout. Splicing the two
manufactures an apparent crossing at the join. The reported +7.5 mV and -2.5 mV were artifacts of the
seam, not measurements of anything.

That the draw varies per process is directly demonstrated, not assumed: twelve clones of one deck,
differing only in output filename, returned crossings of +12.5, -7.5, +7.5, +7.5, -2.5 and +12.5 mV.

**The `cam5r` recovery is unaffected and remains valid** -- those decks re-ran the *full* 33-point sweep
in one process each, so every one is a self-consistent chip. The distinction is exactly whether a
process contains a complete measurement or a fragment of one.

Clean sample, with the 6 resolved parts of the `off9` batch added:

    cam6 13    cam5r 8    off6 5    off7 7    off9 6      n = 39
    mean +2.50 mV     sd 7.43 mV     -17.5 .. +12.5 mV
    sd uncertainty ~11 %       rule of three: 7.7 %

    requirement:  range >= +/-37.2 mV      step <= 0.74 mV
    measured step 2.50 mV = 0.34 sigma     -- still fails by ~3.4x

Conclusion and recommendation unchanged (~4 uA/segment). The correction removes two values near the
centre of the distribution, so sd rises slightly (7.21 -> 7.43 mV) rather than falling.

## n = 48, 2026-08-12 03:3x — a new tail point, and a possible centre offset

    cam6 13   cam5r 8   off6 5   off7 7   off9 6   off10 9      n = 48
    mean +3.02 mV     sd 8.14 mV     -17.5 .. +27.5 mV
    sd uncertainty ~10 %      rule of three: 6.2 %

**The maximum moved from +12.5 to +27.5 mV.** That is the first genuinely new tail point in several hours
and it is exactly what more parts buys: not precision on the centre, which was already adequate, but
observations where the distribution is thinnest and where the range requirement is actually set.
sd rose 7.43 -> 8.14 mV as a result, which is the honest direction for a tail discovery.

    requirement:  range >= +/-40.7 mV     step <= 0.81 mV
    measured step 2.50 mV = 0.31 sigma    -- unchanged, still ~3x too coarse

### The mean may not be zero, and that would be a centring error

    mean +3.02 mV     standard error 1.17 mV     -> 2.6 SE from zero

Marginal on its own, and the batches disagree: `cam6` sits near -0.1 mV while the `off*` batches sit
near +4.7 to +5.0 mV. Those are 1.5-2 standard errors apart, so the split may be nothing. But if a
genuine +3 mV mean survives more parts, it means **code 301 is not the centre of the correction range** --
at 2.50 mV/code the array is centred about 1.2 codes low, and the fix is to centre at code 302.

This costs nothing to watch and would cost a silicon revision to discover late, so it is recorded now
rather than after it is certain. **Not a conclusion.** The batch disagreement needs explaining before the
mean is worth acting on, and the two candidate explanations -- sampling noise, or something differing
between the campaign deck and the offset decks -- have not been separated.

## Exclusion policy tested: it does not bias the distribution, 2026-08-12 03:5x

34 % of fully-swept parts (18 of 53) are excluded by the bracket guard -- their crossings are bracketed
too widely because solver failures removed intermediate points. Whether that exclusion biases the
result is testable directly by varying the guard:

    guard    n   mean     sd     min    max   corr(rejections,|offset|)
      7.5   48   +3.02   8.14   -17.5  +27.5      -0.07
     12.5   62   +2.66   8.41   -17.5  +27.5      +0.06
     25.0   71   +3.24   8.35   -17.5  +27.5      -0.03
     50.0   73   +3.63   8.81   -17.5  +30.0      -0.13

**Admitting 25 more parts (+52 %) moves sd by 8 %** -- inside the ~10 % uncertainty the sample carries
anyway. The strict guard is mildly *conservative*: sd creeps up as wide-bracket parts are admitted, so
those parts are if anything slightly more extreme, not less. **No tail truncation.**

Separately confirmed, and it removes the other candidate bias: **no part anywhere has "no crossing" in
the +/-80 mV window** (0 of 53). The window is not clipping the distribution.

### Correction: the bias correlation was small-sample noise

Earlier entries recorded corr(rejections, |offset|) = -0.41 (n=16) then -0.34 (n=18), described as
"the reassuring direction" -- difficult parts having *smaller* offsets. At n = 48-73 the correlation is
**-0.07 to -0.13, i.e. nothing**. The honest statement is that there is *no detectable relationship*
between how hard a part is to simulate and how far out it sits. That still means no bias, which was the
question; but the earlier negative value was over-read, and it is withdrawn as a finding.

**The conclusion is invariant across every one of these choices**: with sd between 8.1 and 8.8 mV the
requirement is a step below 0.81-0.88 mV, and the measured step is 2.50 mV -- 0.28 to 0.31 sigma,
~3x too coarse, at every n and every guard.

The mean also survives all of them (+2.7 to +3.6 mV), which strengthens rather than settles the possible
centring error noted above: it is at least not an artifact of the exclusion policy.

## Code 311 is unmeasurable: no decision point can be determined, 2026-08-12 04:2x

Complete sweep, 31 points, one chip, 50 ns, 2.5 mV grid. Shown in sweep order, `.` = transient failed
to converge:

    code 309  HHHHHHHHHHHHHHHHHHHHHHHHLLLLL.L    1/31 failed   crossing -11.25 mV +/-1.25
    code 310  H.H.HHHHHHHH.......H..L..LL....   17/31 failed   crossing -18.75 mV +/-3.75
    code 311  HHHHHHHH.HHHHH.HH..............   16/31 failed   NO CROSSING among converged points

**Code 311 converges cleanly from -70 mV up to -30 mV, all HIGH, and then every point above -30 mV
fails.** Its decision point must lie in that region, and the region cannot be simulated. This is not a
wide bracket or a noisy measurement -- there is no measurement.

That is a result about the array, not about the data collection: **there exists a trim setting at which
this comparator's decision point cannot be determined.** Whether it is a property of the circuit or of
the solver is the open question, and it is exactly the question the two commissioned tests separate:

  - codes 309-312 re-run on an independent mismatch draw (`recur.cir`, running) -- same codes failing
    the same way means structural
  - one failing point re-run at a 0.01 ns timestep -- numerical trouble usually yields to a finer step;
    a circuit with no findable operating point does not

Until those return, the honest statement is that **codes 310 and 311 are not characterised**, and any
transfer curve drawn through this region is drawn through a hole. The measured 2.50 mV/LSB (2026-08-12
00:5x) came from codes 300-310 and remains the only step figure with a clean measurement behind it.

## n = 63 — the mean is systematic, not noise: the array is centred ~1.3 codes low

    cam6 13  cam5r 8  off6 5  off7 7  off9 6  off10 9  off11 7  off12 8      n = 63

    mean +3.29 mV     sd 7.94 mV     -17.5 .. +27.5 mV
    SE(mean) 1.00 mV  -> the mean is 3.3 standard errors from zero
    sd uncertainty ~9 %      rule of three: 4.8 %

At n = 18 this was +0.4 mV and dismissible; at n = 48, +3.0 mV and marginal; at n = 63 it is **+3.29
+/- 1.00 mV**, and the batch-to-batch disagreement that made it doubtful has washed out as the batches
grew. **It is a systematic offset, not sampling noise.**

Checked for the obvious artifacts before believing it: the sweep grid is symmetric about zero at a
uniform 5 mV, so the bracket-midpoint estimator carries no rounding bias; `EIN_N` is the exact
complement `2.49 - v(IN_P)`; `VTRIM_P` and `VTRIM_N` are equal. The deck is symmetric, so the asymmetry
is in the circuit.

### This is a different kind of defect from the other two, and a much cheaper one

    random part-to-part spread   sd 7.94 mV   cannot be trimmed away; sets the range requirement
    systematic offset            +3.29 mV     the same on every part; trimmed away by one choice

A systematic offset costs nothing to remove: pick a different centre code. At the measured 2.50 mV/LSB,
+3.29 mV is **1.3 LSB**, so the array's nominal centre should sit at **code 302 rather than 301**.
Left uncorrected it consumes 3.3 mV of one-sided correction range on every part and biases the whole
population toward one rail.

Three findings now stand against this block, in increasing order of how easily they are fixed:

    1. step 2.50 mV = 0.31 sigma, ~3x too coarse       -> reduce segment current to ~4 uA
    2. range +/-753 mV = 95 sigma, ~19x oversized      -> same change fixes it
    3. centre offset +3.29 mV = 1.3 LSB                -> shift the nominal code by one

The first two are the same knob. The third is free.

## Correction: code 311 is measurable — the failure was numerical, 2026-08-12 04:5x

**The "no determinable decision point" entry above is withdrawn.** The same point, same code, same input,
at two timesteps:

    code 311, -10 mV, tran 0.05n 50n   ABORTED at 39.49 ns
    code 311, -10 mV, tran 0.01n 50n   completed 50.00 ns, 5725 rows, decision LOW

The failure yields to a finer timestep, so it is a solver artifact, not a circuit without an operating
point. The correct and much weaker claim: **at the 0.05 ns timestep, codes 310 and 311 cannot be
characterised.** That is a statement about the method, not the design.

It also locates the crossing. Code 311's converged points were HIGH up to -30 mV and this new point at
-10 mV is LOW, so its decision point lies **between -30 and -10 mV** -- close to where the trend from
the codes below predicts. Nothing exotic is happening; it simply could not be seen.

### Gate before re-measuring: does the timestep move the answer?

Established tonight (2026-08-12 00:2x): the *sample time* changes the result, not merely the
convergence -- reading at 20 ns instead of 50 ns moved sd from 9.00 to 15.40 mV. A finer *timestep*
could do the same. So before mixing 0.01 ns and 0.05 ns data in one transfer curve:

    re-run 3-4 points either side of code 309's crossing (-11.25 mV, cleanly measured at 0.05 ns)
    at 0.01 ns and compare the decisions

If they agree, the timesteps agree on points both can resolve and the data may be combined. If they
disagree, **every crossing measured tonight is timestep-dependent** and the problem is far larger than
one awkward code. Four points, ~20 minutes, and it gates everything after it.

If it passes: re-run codes 310 and 311 at 0.01 ns over -40..0 mV. Five times the cost per point, so
narrow the window rather than coarsen the resolution.

### Gate passed: the two timesteps agree, 2026-08-12 05:0x

Four points spanning code 309's crossing (-11.25 mV), each run at both timesteps on the same chip:

    -20.0 mV   0.01 ns: HIGH   0.05 ns: HIGH   match
    -15.0 mV   0.01 ns: HIGH   0.05 ns: HIGH   match
    -10.0 mV   0.01 ns: LOW    0.05 ns: LOW    match
     -5.0 mV   0.01 ns: LOW    0.05 ns: LOW    match

The two points that straddle the crossing (-15 and -10) are the demanding ones and they agree, so the
crossing is between -15 and -10 mV by either method -- consistent with the -11.25 +/-1.25 measured at
the standard step.

**The timesteps agree on points both can resolve, so 0.01 ns and 0.05 ns data may be combined**, and
re-measuring codes 310 and 311 at the finer step is legitimate. That run is under way.

Limits of the test, stated because it gates hours of work: four points, one code, one chip. It
establishes agreement where both timesteps converge; it does not establish that a finer step never
changes an answer, and it says nothing about points only the fine step can resolve -- which are, by
construction, the ones we are about to rely on. **The comparison it licenses is between measured
crossings, not between a measured crossing and an unresolvable one.**

---

## A flat region in the trim transfer: codes 309-312 deliver no correction, 2026-08-12 05:1x

Transfer sweep, one chip, one process, 50 ns, 2.5 mV grid. Failure counts in brackets:

    code 300   +13.50 mV +/-1.50   (clean)
    code 309   -11.25 mV +/-1.25   ( 1/31 failed)
    code 310   -18.75 mV +/-3.75   (17/31 failed)
    code 311   no crossing         (16/31 failed -- solver, not circuit; see 04:5x)
    code 312    -8.75 mV +/-1.25   ( 4/31 failed)

**The two cleanest codes in the sweep are 309 and 312**, at 1 and 4 failures of 31, and they bracket the
messy region. So the comparison that matters does not depend on the codes that were hard to simulate.

    measured step, codes 300 -> 309:   -24.75 mV over 9 codes  =  -2.75 mV/code
    predicted for codes 309 -> 312:    -8.25 mV over 3 codes
    observed for codes 309 -> 312:     +2.50 +/- 2.50 mV

**The crossing failed to move as predicted by ~10.75 mV, against a combined uncertainty of +/-2.50 mV
-- more than four standard errors.** Stated carefully: the *reversal* is marginal on its own
(+2.50 +/- 2.50, about 1 sigma, so consistent with zero). What is firmly established is that the trim
**did not advance**: three codes that should have moved the decision point 8 mV moved it by nothing
measurable.

So the array has a flat of at least three codes, and roughly 7.5 mV of intended correction range is
absent there. That is the differential non-linearity this sweep was built to look for, and it is the
first version of that claim resting on well-converged codes rather than on the failures.

**Confirmation required before this is treated as a design fault**: `recur2` is running codes 309-312 on
an independent mismatch draw. If the flat appears at the same codes on a second chip it is structural.
If it moves, it belongs to this draw. Until then the finding is one chip, and one chip is one sample.

## The non-linearity is a period-4 sawtooth — matching the segment structure, 2026-08-12 05:3x

Fitting a local slope through the two end codes of the measured run (309 and 313, both the cleanest
class of measurement) gives **-1.25 mV/code**, half the -2.75 mV/code measured over codes 300-309.
Residuals against that local slope:

    code   mod 4   measured    local fit   residual
     309     1      -11.25      -11.25      +0.00
     310     2      -18.75      -12.50      -6.25
     311     3      (unresolved at 0.05 ns; bounded -30..-10 by the 0.01 ns point)
     312     0       -8.75      -15.00      +6.25
     313     1      -16.25      -16.25      +0.00

**A sawtooth of amplitude ~6.25 mV with period 4**, returning to zero at both codes that are 1 mod 4.

The array is 150 unary elements of 4 LSB each plus 2 binary elements which subdivide them
(`C169-array23-strobe.spice:268`). **A period-4 error is exactly what mismatch between the binary
sub-elements and the unary element they subdivide produces.** The period matches the structure without
being fitted to it -- the model has two parameters (slope, amplitude) against four measurements.

    amplitude 6.25 mV = 2.5 LSB of differential non-linearity

### Falsifiable prediction, recorded before the data lands

Code 314 is 2 mod 4, so the model puts its residual at -6.25 mV against a local fit of -17.50 mV:

    predicted crossing, code 314:   -23.75 mV, uncertainty ~+/-2.5 mV

Code 314 is sweeping now (6 of 31 points at time of writing). If it lands near -23.75 the sawtooth model
survives and the mechanism is identified. If it lands near -17.50 the oscillation is not periodic and
the model is wrong.

### If it holds, the sizing verdict gets worse

With a 2.5 LSB DNL the *effective* resolution is not the 2.50 mV step but the sawtooth amplitude --
about 6.25 mV, or **0.79 sigma against sd 7.94 mV**, versus a requirement of 0.1 sigma. That is ~8x
too coarse rather than ~3x. **Provisional**: one chip, four codes, one unresolved code in the middle,
and the recurrence test on a second chip still running.

## Corroboration: the convergence failures have period 4 too, 2026-08-12 05:3x

Failure counts per code, complete sweeps only, grouped by code modulo 4:

    mod 4 = 0    code 312 ->  4/31 failed  (13 %)
    mod 4 = 1    code 309 ->  1/31 ( 3 %),  code 313 -> 4/31 (13 %)
    mod 4 = 2    code 310 -> 17/31 failed  (55 %)      [code 314, partial: 8/22 = 36 %]
    mod 4 = 3    code 311 -> 16/31 failed  (52 %)

**Two of the four residue classes are hard and two are easy, splitting 52-55 % against 3-13 %.**

This is corroboration of the period-4 sawtooth (05:3x entry) from a **completely different observable**.
The sawtooth came from crossing residuals -- four measurements against a two-parameter model, which is
weak on its own. The failure rates are an independent quantity, computed from which runs converged
rather than from where the decision points landed, and they show the same period on the same codes.

### It revives the handover mechanism at a different phase

H-1045 set the handover hypothesis aside on the grounds that element boundaries fall at multiples of 4
and code 310 is not one. That reasoning assumed a phase that was never verified. The data says the
**difficult codes are those 2 and 3 mod 4** -- so the region where elements overlap sits at that phase,
not at 4k. The mechanism was right and my phase assumption was wrong, which is a different error from
the mechanism being wrong.

Physically coherent: codes where the binary sub-elements and the unary element are simultaneously
partly on are both the hardest to converge (two devices contending) and the largest contributors to
transfer error. Codes 310 and 311 are those; 309, 312 and 313 are not.

### Prediction, filed before the data

Code 315 is 3 mod 4, so it should be in the **hard** class: failure rate near 50 %, not near 10 %.
It is the last code in this sweep. A low failure rate at 315 falsifies the period-4 reading of the
convergence data.

Caveats: one chip, five complete codes, one partial. The recurrence test on an independent draw
(`recur3`, 53-point window) is running and remains the test that matters.

## Code 314 result: the failure prediction confirmed, the crossing prediction not discriminating

    predicted (period-4 sawtooth):   -23.75 mV
    predicted (null, no oscillation): -17.50 mV
    measured:                         -21.25 mV +/-3.75   (26/31 points, 12 failures)

    distance to sawtooth prediction:  2.50 mV = 0.67 sigma
    distance to null prediction:      3.75 mV = 1.00 sigma

**Consistent with the sawtooth; not inconsistent with the null.** The two hypotheses are separated by
6.25 mV and this measurement carries +/-3.75, so it cannot discriminate between them. Recorded as weak
support, not as confirmation.

The other half of the prediction did discriminate. Code 314 is 2 mod 4, predicted to be in the *hard*
class:

    predicted failure rate: ~50 %      measured: 12/26 = 46 %      CONFIRMED

### Why the crossing prediction could not be sharp

The model's largest predicted deviations are at codes 2 and 3 mod 4 -- and those are exactly the codes
whose convergence failures are worst, which widens their brackets. **The codes where the model makes
its sharpest predictions are the codes hardest to measure**, and the same physical mechanism causes
both. Any test of this model on the crossing alone will be blunted in precisely the places it matters.

That is an argument for testing it on the failure rates, where the signal is a 4x difference in a
quantity with no bracket to widen, and for the 0.01 ns re-measurement of the hard codes, which is what
would sharpen the crossings.

Code 314 is still sweeping (26 of 31); the bracket may tighten. Code 315 (3 mod 4) is the last of this
run and is predicted hard.

## Code 314 complete: the residue classes reproduce exactly

    mod 4 = 0    code 312 ->  4/31 (13 %)
    mod 4 = 1    code 309 ->  1/31 ( 3 %)   code 313 ->  4/31 (13 %)
    mod 4 = 2    code 310 -> 17/31 (55 %)   code 314 -> 17/31 (55 %)
    mod 4 = 3    code 311 -> 16/31 (52 %)

**Both codes in class 2 failed 17 of 31 -- the same count, not merely the same rate.** With the two
hard classes at 16-17 and the two easy classes at 1-4, the split is now four-to-one on counts that
reproduce across the period.

The transfer picture, one chip, six complete codes:

    309  -11.25 +/-1.25      312   -8.75 +/-1.25
    310  -18.75 +/-3.75      313  -16.25 +/-1.25
    311  unresolved          314  -21.25 +/-3.75

Every code in the hard classes carries a +/-3.75 bracket or no crossing at all; every code in the easy
classes carries +/-1.25. **The measurement precision is itself a function of code modulo 4**, which is
the same anti-correlation between prediction and precision noted above -- now visible directly in the
brackets rather than inferred.

Code 315 (3 mod 4, predicted hard) is sweeping and completes this run.

---

## Recurrence test, first result: the transfer anomaly reproduces, the convergence anomaly does not

Chip 3 (`recur3`, independent mismatch draw) against chip 1 (`fb`), compared inside the **matched**
input window -70..+5 mV and at **matched progress** (the same first N points), since chip 3's sweep is
wider and still running:

    step across the 309 -> 310 transition       nominal 2.50 mV/code
        chip 1:  -11.25 -> -18.75   =  -7.50 mV      3.0x nominal
        chip 3:  -18.75 -> -31.25   = -12.50 mV      5.0x nominal

    convergence failures, code 310, first 27 in-window points
        chip 1:  13/27  (48 %)
        chip 3:   5/27  (19 %)     -- and chip 3's *easy* code 309 sits at 4/31 (13 %)

**The oversized step at 309 -> 310 reproduces on an independent draw; the convergence difficulty does
not.** On chip 3, code 310 is barely harder than code 309; on chip 1 it was dramatically harder
(13/27 against 1/31). Fisher exact on 13/27 vs 5/27 gives p ~ 0.03.

### What this does to the findings above

  - **The transfer non-linearity gains its first independent support.** Two chips, two draws, both
    showing a step 3-5x nominal at the same code transition. This is the finding that matters for the
    design and it is now more than one chip.
  - **The period-4 structure in the *failure rates* (05:3x entries) is weakened.** It was recorded as
    corroboration "from a completely different observable"; that observable now appears to be
    chip-specific. Convergence difficulty is a property of a particular mismatch draw meeting a
    particular solver, not of the array.
  - The two were treated as mutually supporting. They are not: one reproduces and one does not.

Chip 3 has only codes 309 and 310 so far; 311 and 312 follow. The sawtooth model predicts chip 3's
crossings recover upward at 312, as chip 1's did. That is the next test and it is already running.

## n = 91 — the distribution has converged, and the drift did not continue

    n = 91     mean +4.37 mV   SE 0.87   (5.0 standard errors from zero)
               sd 8.32 mV      -17.5 .. +27.5 mV
               sd uncertainty ~7 %       rule of three: 3.3 %

    requirement:  range >= +/-41.6 mV     step <= 0.83 mV
    measured step 2.50 mV = 0.30 sigma    -- unchanged across n = 18 .. 91

The mean across the night: +0.42 (n=18), +3.02 (48), +3.29 (63), +4.53 (74), **+4.37 (91)**. It rose
and then stopped. The apparent monotone drift that prompted a check at n = 74 has not continued, which
is what the per-part correlation predicted when it came back insignificant -- an implicit prediction,
now supported by the sample refusing to keep climbing.

sd across the same range: 8.59, 8.28, 8.30, 7.37, 7.94, 8.72, 8.32. **Wandering inside its own ~7-12 %
uncertainty and going nowhere**, which is what a converged estimate looks like.

### Consolidated verdict on this block

    1. step        2.50 mV = 0.30 sigma against a 0.1 sigma requirement    ~3x too coarse
    2. range       +/-753 mV = 90 sigma against a 5 sigma requirement      ~18x oversized
    3. centring    mean +4.37 mV = 1.75 LSB                                nominal centre should be ~code 303
    4. linearity   step 3-5x nominal at the 309->310 transition, on two independent chips

(1) and (2) are the same knob: reduce segment current to ~4 uA. (3) is one number. (4) is the one that
may require a design change rather than a parameter change, and it is the least characterised -- two
chips, one transition each, and the second chip's sweep still running.

## Chip 1 transfer sweep complete, and the decisive prediction for chip 3

Chip 1 (`fb`), all 217 points, seven codes, 50 ns, 2.5 mV grid:

    code   mod4   crossing            failures
     300    0     +13.50 +/-1.50       (anchor)
     309    1     -11.25 +/-1.25        1/31
     310    2     -18.75 +/-3.75       17/31
     311    3     unresolved           16/31
     312    0      -8.75 +/-1.25        4/31
     313    1     -16.25 +/-1.25        4/31
     314    2     -21.25 +/-3.75       17/31
     315    3     unresolved           17/29

Chip 3 (`recur3`, independent draw, 53-point window) so far:

     309          -18.75 +/-1.25        6/53
     310          -31.25 +/-1.25       11/53      step -12.50 mV/code = 5x nominal
     311          in progress

### The test that decides whether the sawtooth is structural

The defining feature of the sawtooth is not the large step at 309 -> 310 -- a merely steeper local slope
would produce that too. It is the **recovery**: on chip 1 the crossing went -18.75 (310) then back up to
-8.75 (312), a **+10 mV reversal**.

    if the sawtooth is structural:  chip 3's code 312 is LESS negative than its code 310
                                    i.e. above -31.25 mV, recovering by roughly +10 to +17 mV
    if it is only a steeper slope:  chip 3's code 312 continues DOWN, near -40 mV or below

Those predictions are ~20 mV apart against a +/-1.25 mV measurement, so unlike the code-314 test this
one discriminates sharply. Chip 3's code 311 is sweeping now; 312 follows.

**This is the last outstanding question of the session on this block.** Everything else -- step, range,
centring -- is measured and consistent across 91 parts. Whether the trim array is non-monotonic, or
merely non-uniform, turns on the sign of one number.

## Non-uniformity is forced by conservation of full-scale, independent of the recovery test

Chip 3 so far:

    309  -18.75      310  -31.25      311  -46.25 +/-1.25
    steps:  -12.50 mV/code,  -15.00 mV/code       (nominal 2.49)

**A local slope of ~13.75 mV/code cannot be the array's average slope**, and the average is not a matter
of opinion. Full-scale is set by device values that were checked independently earlier tonight:

    150 segments x 23 uA x 218 ohm x 2 = 1504 mV across 603 codes = 2.49 mV/code

That calculation agreed with the measured step to 0.2 % (2026-08-12 00:5x) and does not depend on any
crossing measurement. So if three consecutive codes step at 12-15 mV, **other codes must step at well
under 2.49 mV -- and the deficit has to appear somewhere.** Over 603 codes the excess in this region
must be repaid by flat, or reversed, codes elsewhere.

**Non-uniformity is therefore established without needing to observe the recovery directly.** What the
recovery test still decides is *where* the deficit sits: adjacent to the steep codes (a local sawtooth,
as chip 1 showed) or distributed across the range (a smooth but non-linear transfer). Those have
different consequences -- a local sawtooth means specific offsets are uncorrectable; a distributed
non-linearity means the effective step varies with code but every offset remains reachable.

Prediction unchanged and now sharper, since chip 3's excursions are larger than chip 1's:

    sawtooth      -> code 312 recovers above -31.25 mV
    steeper slope -> code 312 continues down, near -60 mV

~40 mV apart against a +/-1.25 measurement.

Note also that chip 3 resolves code 311 cleanly (-46.25 +/-1.25) where chip 1 could not resolve it at
all -- further confirmation that the convergence difficulty belongs to chip 1's draw, not to the code.

---

## The finding, stated in converter terms: good INL, bad DNL, non-monotonic

Chip 1's completed sweep, resolved codes only:

    300 -> 309 :  -24.75 mV over  9 codes  =  -2.75 mV/code
    309 -> 310 :   -7.50 mV over  1 code   =  -7.50 mV/code
    310 -> 312 :  +10.00 mV over  2 codes  =  +5.00 mV/code    <- reversed
    312 -> 313 :   -7.50 mV over  1 code   =  -7.50 mV/code
    313 -> 314 :   -5.00 mV over  1 code   =  -5.00 mV/code

    NET 300 -> 314 :  -34.75 mV over 14 codes  =  -2.482 mV/code
    nominal from device values                 =  -2.490 mV/code      agreement 0.3 %

**Integral linearity is essentially perfect and differential linearity is badly broken.** Over 14 codes
the array delivers exactly the correction the device sizing predicts -- 0.3 % -- while individual codes
step at anything from 3x the nominal to a full reversal.

Expressed as DNL against the ideal -2.49 mV step:

    -7.50 mV/code   ->  DNL +2.0 LSB
    +5.00 mV/code   ->  DNL +3.0 LSB   (the transfer runs backwards here)
    -5.00 mV/code   ->  DNL -1.0 LSB

**DNL exceeding 1 LSB permits non-monotonicity; +3 LSB delivers it.** This is a non-monotonic trim DAC
whose endpoints are correct.

### Why the errors cancel, and what that means

The excess in the steep codes is repaid within ~14 codes, not spread across the range -- which is why
the net matches nominal so exactly. That answers the local-versus-distributed question without the
recovery test: **the non-linearity is local and self-cancelling.**

Consequences for the block:

    total range          correct, as conservation requires -- and irrelevant, being 18x oversized
    effective resolution set by the local excursion (~6 mV), not the 2.49 mV step
    monotonicity         violated: a higher code can correct less than a lower one
    trim algorithm       any successive-approximation or binary search over this code space can
                         converge to the wrong code, because it assumes monotonicity

That last consequence is the one that reaches beyond this block. A non-monotonic trim array is not
merely imprecise; it breaks the search procedure normally used to find the right code.

---

# STATE OF THIS INVESTIGATION — 2026-08-12 06:2x

A navigation aid. This file is appended chronologically, including the entries that were later
withdrawn, so that the reasoning remains auditable. This section says what currently stands.

## Established

    quantity              value                          basis
    part-to-part spread   sd 8.32 mV, mean +4.37 mV      91 parts, 7 batches, one deck
                          -17.5 .. +27.5 mV             sd uncertainty ~7 %, rule of three 3.3 %
    trim step (nominal)   2.49 mV/LSB                    device values; agrees 0.2-0.3 % with two
                                                         independent measured routes
    correction range      +/-753 mV = 90 sigma           603 codes x measured step
    integral linearity    -2.482 vs -2.490 mV/code       chip 1, 14 codes, 0.3 %
    differential lin.     DNL +2, +3, -1 LSB             chip 1, resolved codes; NON-MONOTONIC
    oversized step        0.30 sigma vs 0.1 required     ~3x too coarse
    oversized range       90 sigma vs 5 required         ~18x
    centring error        +4.37 mV = 1.75 LSB            centre belongs near code 303, not 301

## Recommended

    1. segment current 23 uA -> ~4 uA      fixes step AND range (one knob, both scale with current)
    2. nominal centre code 301 -> ~303     one number; removes 1.75 LSB of wasted one-sided range
    3. monotonicity: structural fix        matched unit devices for the binary elements, or
                                           deliberate binary/unary overlap. NOT fixed by (1):
                                           DNL in LSB is a ratio and does not scale with current.
    4. trim search algorithm               any binary/SAR search over this code space is unsafe
                                           while DNL > 1 LSB; it converges silently to a wrong code

## Pending

    chip 3 code 312       decides whether the deficit is repaid locally (chip 1's shape) or
                          over a wider span. 4 of 53 points down.
    DNL at 4 uA           expected unchanged in LSB; being wrong would be good news
    chips 4 and 5         monotonicity currently rests on one draw; the steep region on two

## Withdrawn during the session (retained above with their retractions)

    "step 4x too coarse"              unit error, segment weight vs per-LSB requirement
    "6.0 mV/LSB"                      measured at a 20 ns stop that changes the answer
    "no determinable decision point"  numerical, yields to a 0.01 ns timestep
    "corr(rejections,|offset|) -0.41" small-sample noise; ~0 at n = 48-73
    "parts 20 and 26"                 spliced from two different mismatch draws
    "period-4 in failure rates"       chip-specific; does not reproduce on an independent draw

## Standing constraints on method

    a process is a chip                 quantities that depend on the draw need one process
    tstop 50 ns                         20 ns changes the answer, not merely the convergence
    window sized from the population    +/-60 mV floor for multi-code sweeps on an unseen draw
    filenames carry the value set       not a label typed alongside
    no rate from a partial sweep        unless compared at matched progress

---

## RESOLVED: non-monotonicity reproduces on an independent draw, 2026-08-12 06:3x

The discriminating prediction (filed 2026-08-12 05:5x, before the data):

    sawtooth structural  ->  chip 3's code 312 recovers, above -31.25 mV
    steeper slope only   ->  chip 3's code 312 continues down, near -60 mV

Chip 3, code 312, 19 of 53 points: **swept -70 to -25 mV with no crossing.** The crossing lies above
-25 mV. The steeper-slope prediction is dead -- the sweep passed -60, -50, -40 and -30 without a
transition.

    chip 3:  code 311  -46.25 mV      code 312  above -25 mV      step > +21.25 mV in one code
    chip 1:  code 310  -18.75 mV      code 312   -8.75 mV         step   +10.00 mV over two codes

**The transfer reverses on both chips, and recovers into the same code.** Code 312 is 0 mod 4 and is a
high point on both draws.

### Why the matching phase is the important part

Random mismatch differs per draw; a systematic design property does not. Two independent chips showing
a reversal *at the same code, in the same direction, with the same period* is what distinguishes a
built-in structural error from a coincidence of one draw. Chip 3's excursion is larger than chip 1's
(>21 mV against 10 mV), which is what random mismatch superimposed on a systematic error looks like:
same sign and position, different magnitude.

**The non-monotonicity is therefore a property of the array as designed**, not of a particular
simulated part. That was the last open question of the session on this block.

    established now:   DNL > 1 LSB and non-monotonic, on two independent draws
    consequence:       any binary or successive-approximation trim search is unsafe over this
                       code space -- it converges silently to a wrong code
    fix:               structural (matched unit devices for the binary elements, or deliberate
                       binary/unary overlap). NOT fixed by the current reduction, which addresses
                       step and range only.

Caveats unchanged and still material: two draws, one corner, one temperature, simulated mismatch, and
the whole study post-dates two repairs to the netlist made at the start of the session.

## DNL measured on both chips: up to +14 LSB, 2026-08-12 06:4x

    chip 1                                    chip 3
      309 -> 310   -7.50 mV/code  DNL -2.01     309 -> 310  -12.50 mV/code  DNL  -4.02
      310 -> 312   +5.00 mV/code  DNL +3.01     310 -> 311  -15.00 mV/code  DNL  -5.02
      312 -> 313   -7.50 mV/code  DNL -2.01     311 -> 312  +32.50 mV/code  DNL +14.05
      313 -> 314   -5.00 mV/code  DNL -1.01
      net 309-314  -2.00 (ideal -2.49)          net 309-312  +1.67 (ideal -2.49)

**Same shape and same phase on both draws; amplitude differs by ~4x.** Several codes stepping far too
far in the descending direction, then one code reversing hard. Chip 3 reverses **+32.50 mV in a single
code** -- a DNL of **+14 LSB**.

That is worse than chip 1 suggested, and it changes how the defect should be described. At +3 LSB the
array is a poor-resolution trim. At +14 LSB **the array skips ~35 mV of correction between adjacent
codes**: there are offsets that no code in that neighbourhood produces at all.

Whether those offsets are reachable *elsewhere* in the range depends on whether the pattern repeats
with the same phase across all 150 segments -- **not measured**. If it does, specific offset values are
unreachable by any code, which is a categorically different defect from imprecision. If the phase
varies between segments, the gaps move and every offset is reachable somewhere. That is now the most
valuable remaining measurement on this block: the same four codes in a different segment, e.g. around
code 409 or 509.

Note also that the net over the measured span is wrong on both chips (-2.00 and +1.67 against -2.49),
so the repayment extends beyond these four codes. Chip 1's wider span (300 -> 314, fourteen codes)
returns -2.482, i.e. correct to 0.3 %. **The error cancels over ~14 codes, not over 4.**

---

## MECHANISM IDENTIFIED: the binary sub-elements are oversized; the unary element is correct

Mapping every measured step onto the array's element structure (150 unary elements, element k covering
codes 4k..4k+3):

    chip 1   309->310  element 77 -> 77  within     -7.50 mV/code   DNL  -2.01
             310->312  element 77 -> 78  BOUNDARY   +5.00 mV/code   DNL  +3.01
             312->313  element 78 -> 78  within     -7.50 mV/code   DNL  -2.01
             313->314  element 78 -> 78  within     -5.00 mV/code   DNL  -1.01

    chip 3   309->310  element 77 -> 77  within    -12.50 mV/code   DNL  -4.02
             310->311  element 77 -> 77  within    -15.00 mV/code   DNL  -5.02
             311->312  element 77 -> 78  BOUNDARY  +32.50 mV/code   DNL +14.05

**The sign of the DNL is determined entirely by whether the step crosses an element boundary.** Every
within-element step is negative and oversized; every boundary step is positive and hugely oversized.
Chip 1 spans two adjacent elements (77 and 78) and behaves identically in both.

### The arithmetic closes

Within an element the two binary sub-elements step the array; at the boundary they reset and the next
unary element switches in. So the boundary step should be **one unary element minus three binary
steps**. With the unary element at its nominal 4 LSB = -9.96 mV:

    chip 1   mean binary step  -6.67 mV (2.7x nominal)   predicted boundary +10.05   measured +10.00
    chip 3   mean binary step -13.75 mV (5.5x nominal)   predicted boundary +31.29   measured +32.50

**Agreement to 0.05 mV and 1.2 mV, on two independent draws.** The model has no fitted parameters --
the binary step is measured within the element, the unary weight is the nominal 4 LSB, and the boundary
step is predicted from them.

    the unary element delivers its nominal weight
    the binary sub-elements deliver 2.7-5.5x their nominal weight

**This is a binary-to-unary weighting error, not a mismatch problem.** The unary array is correct; the
sub-elements that subdivide it are too strong, so they overshoot within each segment and the handover
snaps back.

### What this changes

    fix               resize the binary sub-elements to 1 and 2 LSB against the unary element's 4,
                      preferably by building them from the same unit device rather than by scaling
    not the fix       reducing segment current (scales everything together; the ratio is untouched)
    not the fix       better matching or larger devices (this is a nominal weighting error, present
                      in both draws with the same sign, not a random mismatch)

The `seg.cir` sweep at codes 409-412 straddles a boundary at the same relative position (element 102 ->
103) and tests whether the same weighting error appears in a distant segment, as the model requires.

---

## The comparator is PINNED at code 409 — the oversized range is not merely wasteful

A locate sweep at code 409 (a different unary segment, 108 codes above centre) returned identical node
voltages at every input from -900 mV to -400 mV:

    code 409, any input in -900..-400 mV:   raw_inv 0.0040   sa_n 1.1803   pbit 0.0000
    code 309, -70 mV                    :   raw_inv 1.1275   sa_n 0.0156   pbit 1.2000
    code 309, +5 mV                     :   raw_inv 0.0067   sa_n 1.1698   pbit 0.0000

**Identical to four decimal places across 500 mV of input.** This is not a decision -- the comparator is
insensitive to its input. It is the same signature as the original array-overdraw fault repaired at the
start of this session: the trim array overwhelms the comparator and pins it.

### This reframes the range finding

The array's full-scale is +/-753 mV, which was recorded as "90 sigma, ~18x oversized" -- wasteful but
harmless. It is not harmless. **Beyond some code the array saturates the comparator and the part stops
deciding at all.** Codes above that limit are not merely unnecessary; they are destructive.

    code 315 (14 codes from centre,  ~35 mV of trim)   works, decisions clean
    code 409 (108 codes from centre, ~269 mV of trim)  PINNED, no decisions at any input

The usable code range therefore lies somewhere between, and the *usable* correction range is a fraction
of the nominal +/-753 mV. That is a different and more serious statement than "oversized".

A two-point test is running (`pe-pin.cir`): codes 301, 310, 320, 330, 340, 350, 360, 380, 400, 420,
450, 500, 550, 600, each evaluated at -800 mV and +800 mV. If the two inputs give different outputs the
comparator still responds; if identical, it is pinned. 28 runs, ~30 minutes, and it bounds the usable
range directly.

**Note this was found by accident.** The sweep was aimed at the segment-phase question and its window
was wrong; chasing the wrong window turned up a failure mode that matters more than the question it was
built to answer.

## The saturation limit measured: only ~1/4 of the nominal range is usable

Two-point test (inputs -800 and +800 mV, 50 ns), one chip:

    code   from centre   nominal trim   verdict
     301      +0 codes        +0 mV     responds
     310      +9             +22        responds
     320     +19             +47        responds
     330     +29             +72        responds
     340     +39             +97        responds
     350     +49            +122        responds
     360     +59            +147        responds
     380     +79            +197        PINNED
     400     +99            +247        PINNED
     420    +119            +296        PINNED

**The comparator stops responding between +59 and +79 codes from centre -- between +147 and +197 mV of
applied trim.** Beyond that the array overwhelms it and no input produces a decision.

    nominal full-scale        +/-753 mV  =  90 sigma
    usable one-sided range    +147 .. +197 mV  =  18 .. 24 sigma
    requirement               +/-5 sigma

So the picture is sharper and worse than "18x oversized":

  - the **usable** range is ~20 sigma, still 4x the requirement -- the design meets its range spec
  - roughly **three quarters of the code space does nothing useful**, and is not inert: entering it
    produces a part that never decides
  - the earlier figure of 90 sigma describes a range the circuit cannot actually deliver

A refinement across codes 362-377 is running to narrow the boundary to +/-3 codes.

Caveat: one chip. The boundary depends on how much array current a given part's comparator can absorb,
so it will move with mismatch. The mechanism is deterministic; the exact code is not.

## Saturation boundary narrowed, and the current reduction verified against it

Refinement across codes 362-377 (two-point test, one chip):

    code 368  (+67 codes, +167 mV trim)  responds
    code 371  (+70 codes, +174 mV trim)  PINNED

**The boundary sits between +67 and +70 codes -- about +170 mV of applied trim, or 20.4 sigma.**

### The recommended fix, tested

A variant array at ~4 uA/segment (`C169-array4.spice`, a 5.75x current cut) re-run at the two codes
that were pinned at 23 uA:

    code 400  (+99 codes from centre)    at 23 uA: PINNED     at 4 uA: RESPONDS
    code 500  (+199 codes from centre)   at 23 uA: PINNED     at 4 uA: RESPONDS

**Prediction confirmed.** The current reduction recommended for the step and range problems also buys
back the usable code range: at 4 uA the array no longer overwhelms the comparator at codes where it
did at 23 uA. Code 500 corresponds to ~87 mV of trim at the reduced step, comfortably inside the
comparator's capability.

This is the first element of the recommendation to be verified by measurement rather than inferred. Two
remain -- whether the step scales as 2.50 -> 0.435 mV/code, and whether DNL in LSB is unchanged -- and
those decide whether the structural rework of the binary sub-elements is still required.

Note the `redstep` deck needs its window extended: at code 300 it swept -80..-10 mV and found no
crossing, because at the reduced step the crossing sits above -10 mV. The window was sized for the
23 uA array.

---

## ROOT CAUSE: the binary degeneration resistors are 15.6x too short

Comparing the elements in `C169-array23-strobe.spice` directly:

    element              device    degeneration           R_eff ~ l/m   current per LSB
    unary   (150 of)     Nx=4      rppd w=1.0u l=84u  m=4     21.0          0.0119
    binary b1            Nx=2      rppd w=1.0u l=5.4u m=2      2.7          0.1852   15.6x
    binary b0            Nx=1      rppd w=1.0u l=5.4u m=1      5.4          0.1852   15.6x

**Every element should carry the same current per LSB.** The unary element is degenerated with 84 um of
rppd; the binary sub-elements that are supposed to be 1 and 2 LSB against its 4 use **5.4 um**. Current
in a degenerated element is set by that resistor, so the binaries carry ~15.6x their share.

That is the nominal weighting error measured all session, now located in two lines of netlist. It
explains why the within-element steps run 2.7-5.5x oversized, why the boundary snaps back by exactly
"one unary minus three binary steps" (H-1071), and why the error is identical in sign on every draw --
it is not mismatch, it is sizing.

**The fix is now specific:** give the binary sub-elements the same degeneration *per unit device* as the
unary -- l=84u with m=2 for b1 and m=1 for b0 -- rather than the present 5.4u. Same device, same
current density, weights in the intended 1:2:4 ratio.

### The reduced-current variant does not test the recommendation

`C169-array4.spice` scales **only the unary** resistors, 84u -> 483u (5.75x), and leaves the binary
elements at 5.4u:

    diff of the two arrays:  150 x l=84u  ->  150 x l=483u     (unary only)
                             binary l=5.4u unchanged in both

So it makes the binary-to-unary ratio **5.75x worse**, which is exactly what the measurement shows:

    DNL at 23 uA, code 309->310:  -2.01 LSB (chip 1),  -4.02 LSB (chip 3)
    DNL at  4 uA, code 309->310:  -5.93 LSB

**That result is not evidence about the current reduction.** It is evidence that scaling half an array
makes its ratios worse, which was never in doubt. The prediction "DNL in LSB is unchanged by a current
reduction" remains untested, and testing it requires scaling *both* element types together.

---

# STATE OF THIS INVESTIGATION — 2026-08-12 10:0x (supersedes the 06:2x summary)

## Established

    part-to-part spread    sd 8.32 mV, mean +4.37 mV, -17.5..+27.5      91 parts, 8 batches
                           SE(mean) 0.87 -> the mean is systematic, not noise
    trim step              2.49 mV/LSB, agreeing 0.2-0.3 % across three independent routes
    nominal full-scale     +/-753 mV = 90 sigma
    USABLE range           +/-~170 mV = 20 sigma; beyond +67..+70 codes from centre the
                           array saturates the comparator and it stops deciding entirely
    integral linearity     -2.482 vs -2.490 mV/code over 14 codes (0.3 %)
    differential linearity DNL -5 to +14 LSB; NON-MONOTONIC, on two independent draws
    mechanism              binary sub-elements degenerated 5.4u where the unary uses 84u,
                           so they carry 15.6x their share. Boundary step = one unary minus
                           three binary steps, closing to 0.04 and 1.21 mV on two chips
                           with no fitted parameters.

## The three faults and the three changes — non-overlapping

    fault                        fix                                    what it does NOT fix
    step 3x too coarse           segment current 23 -> ~4 uA            monotonicity
    range 18x oversized (and     same change                            monotonicity
      only 1/4 of it usable)
    non-monotonic, DNL>1 LSB     binary degeneration 5.4u -> 84u        step, range, saturation
    centre offset 1.75 LSB       nominal code 301 -> ~303               everything else

**A review applying only the obvious change (reduce the current) ships a non-monotonic trim array with
every other number looking correct.**

## Verified by measurement

    current reduction restores the saturated codes      codes 400 and 500 pinned at 23 uA, respond at 4 uA

## Under test now

    corrected weighting (`C169-correct`, all elements 84u/unit device) on codes 309-312
      prediction: steps uniform, boundary reversal gone, DNL < 1 LSB
      falsifier:  if the reversal survives, the mechanism account is incomplete
    step scaling at 4 uA (`pe-red50`, 50-code lever)
      prediction: 2.49 -> ~0.43 mV/code

## Not established

    DNL in LSB under a pure current reduction   `C169-array4` scaled only the unary and is invalid
                                                for this; `C169-array4b` scales both and is untested
    whether the weighting error keeps its phase across all 150 segments (one segment measured)
    anything about corners, temperature, or silicon -- one corner, one temperature, simulated mismatch

## Withdrawn during the session

    "step 4x too coarse" (unit error) | "6.0 mV/LSB" (20 ns stop changes the answer) |
    "no determinable decision point" (numerical) | "corr(rejections,|offset|) = -0.41" (noise) |
    "parts 20 and 26" (spliced chips) | "period-4 in failure rates" (chip-specific) |
    "range oversized but harmless" (it saturates the comparator)

## Corrected weighting, first result: the within-element step is fixed

`C169-correct` (all element types 84u per unit device), codes 309-310, original current:

    transition        original chip 1   original chip 3   CORRECTED
    309 -> 310        -7.50 mV/code     -12.50 mV/code    -1.50 mV/code
    DNL               -2.01 LSB         -4.02 LSB         +0.40 LSB
    (ideal step -2.49 mV/code; |DNL| < 1 LSB guarantees monotonicity)

**The within-element step falls from 3-5x oversized to 0.6x nominal**, and DNL from -2 and -4 LSB to
+0.40. Prediction confirmed on this half of the test.

Uncertainty stated honestly: each crossing carries +/-1.25 mV on the 2.5 mV grid, so the step is
-1.50 +/- 2.50 and the DNL is +0.40 +/- 1.0. **The improvement is unambiguous** (from -2/-4 to
approximately zero); **the claim "below 1 LSB" is supported but not tightly** -- the error bar reaches
the threshold it is being compared against.

The decisive half is still running: the **boundary** transition 311 -> 312, where the original array
gave DNL +3.01 (chip 1) and +14.05 (chip 3). That is where a segmented converter with mismatched
sub-elements snaps back, and it is the signature the whole mechanism account rests on.

    if the boundary reversal is gone     the account is complete and the fix is the fix
    if it survives                       something else contributes and the account has a gap

## The recommended configuration: the whole code space is usable

`C169-array4b` (both element types scaled to ~4 uA/segment), two-point test at +/-800 mV:

    code   1   (-300 from centre)   responds
    code 100   (-201)               responds
    code 200   (-101)               responds
    code 400   ( +99)               responds
    code 500   (+199)               responds
    code 600   (+299)               responds

**Every code in the array produces a decision.** Tested on both sides of centre, which no earlier
saturation measurement did -- all of them swept upward only, and the array is differential.

    at 23 uA/segment    nominal +/-753 mV = 90 sigma    usable +/-~170 mV = 20 sigma   (~1/4 of codes)
    at  4 uA/segment    nominal +/-131 mV = 16 sigma    usable +/-131 mV = 16 sigma    (all codes)
    requirement                                          +/-5 sigma

So the current reduction does something better than shrink an oversized range. **It converts a range
that is 18x oversized and three-quarters unusable into one that is ~3x oversized and entirely usable.**
The usable correction range in sigma barely changes -- 20 to 16 -- while the wasted silicon, the wasted
current, and the trap for the calibration algorithm all disappear.

That last point is the practically important one. At 23 uA a trim search that overshoots lands in a
region where the part stops deciding; there is no such region at 4 uA. Combined with the weighting fix
removing the non-monotonicity, **both of the ways the calibration search could fail are closed by the
two recommended changes.**

## Corrected weighting on a second chip: the within-element step is nominal

    chip A (`correct`)       309 -> 310  -1.50 mV/code   DNL +0.40 LSB   (3 and 8 failures)
                             310 -> 311  -1.00 mV/code   DNL +0.60 LSB   (8 and 6 failures)
    chip B (`pe-correct2`)   309 -> 310  -2.50 mV/code   DNL -0.00 LSB   (0 and 0 failures)

    ideal step -2.49 mV/code; each DNL carries +/-1.0 from the 2.5 mV grid

**Chip B lands on the ideal step exactly**, and with zero convergence failures across both codes. The
three within-element measurements on the corrected array are +0.40, +0.60 and -0.00 LSB, mean ~+0.33,
every one inside the +/-1 LSB band that guarantees monotonicity.

For comparison, the same transition on the original array: **-2.01 LSB (chip 1), -4.02 and -5.02 LSB
(chip 3)** -- all outside the band, on every draw.

Chip B's clean convergence is also the third independent sign that the solver difficulty seen on the
original chip 1 was a property of that draw (H-1062), not of the codes or the weighting.

Still outstanding: the **boundary** transition 311 -> 312, sweeping on chip A now. That is where the
original array reversed by +3.01 and +14.05 LSB, and it is the measurement the mechanism account
stands or falls on.

---

# RESOLVED: the corrected weighting removes the non-monotonicity

Corrected array (`C169-correct`, all element types 84u per unit device), chip A, all four codes:

    code   crossing      transition                    DNL
     309   -8.50 mV
     310  -10.00 mV      309 -> 310  within   -1.50   +0.40 LSB
     311  -11.00 mV      310 -> 311  within   -1.00   +0.60 LSB
     312  -12.50 mV      311 -> 312  BOUNDARY -1.50   +0.40 LSB

**Every crossing decreases. Every step runs in the same direction. Every DNL is inside +/-1 LSB.**
The array is monotonic across the element boundary that previously reversed.

The comparison that matters, same transition, same codes:

    original array, boundary 311 -> 312
      chip 1   +5.00 mV/code   DNL  +3.01 LSB     (reversal)
      chip 3  +32.50 mV/code   DNL +14.05 LSB     (reversal)
    corrected array
      chip A   -1.50 mV/code   DNL  +0.40 LSB     (no reversal)

The measured -1.50 sits 6.5 mV from chip 1's boundary step and 34 mV from chip 3's, against a
measurement uncertainty of +/-2.5 mV. **The reversal is excluded, not merely reduced.** The exact
residual DNL remains grid-limited (+/-1 LSB per measurement) and is consistent with zero.

## What this closes

The mechanism account is complete. The chain, each link measured rather than assumed:

    binary sub-elements degenerated 5.4u where the unary uses 84u        (netlist, H-1079)
      -> they carry 15.6x their share                                    (arithmetic)
      -> within-element steps run 2.7-5.5x oversized                     (measured, two chips)
      -> the boundary snaps back by one unary minus three binary steps   (predicted +10.04/+31.29,
                                                                          measured +10.00/+32.50)
      -> DNL exceeds 1 LSB, so the transfer is non-monotonic             (measured, two chips)
    correct the degeneration to 84u per unit device
      -> within-element DNL +0.40, +0.60, -0.00 LSB                      (measured, two chips)
      -> boundary DNL +0.40 LSB, no reversal                             (measured)
      -> monotonic                                                        (measured)

**The falsifier did not fire.** It was stated before the run: if the reversal survived a corrected
weighting, something else contributed and the account had a gap. It did not survive.

---

# STATE — 2026-08-12 12:1x (supersedes the 10:0x summary)

## The block, as characterised

    part-to-part spread     sd 8.32 mV, mean +4.37 mV (systematic), 91 parts
    trim step               2.49 mV/LSB, three independent routes agreeing to 0.2-0.3 %
    nominal range           +/-753 mV = 90 sigma
    usable range at 23 uA   +/-~170 mV = 20 sigma -- beyond +67..+70 codes the array
                            saturates the comparator and it stops deciding
    integral linearity      0.3 % over 14 codes
    differential linearity  DNL -5 to +14 LSB, NON-MONOTONIC, two independent draws

## Cause, measured end to end

    binary sub-elements degenerated 5.4u where the unary uses 84u -> 15.6x over-weight
      -> within-element steps 2.7-5.5x oversized (two chips)
      -> boundary step = one unary minus three binary steps
         (predicted +10.04 / +31.29, measured +10.00 / +32.50, no fitted parameters)
      -> DNL > 1 LSB -> non-monotonic

## The two changes, both now measured rather than inferred

    segment current 23 -> ~4 uA
      whole code space usable, both sides (codes 1..600 all respond)
      converts a range 18x oversized and 3/4 unusable into ~3x oversized and fully usable
      does NOT fix monotonicity (DNL in LSB is a ratio; scaling preserves it)

    binary degeneration 5.4u -> 84u per unit device
      within-element DNL +0.40, +0.60, -0.00, +1.00 LSB (two chips) -- mean +0.50, SE ~0.5
      boundary DNL +0.40 LSB, NO REVERSAL (chip A; chip B sweeping)
      array monotonic across the boundary that previously reversed
      does NOT fix step size, range, or saturation

    nominal centre code 301 -> ~303        removes the +4.37 mV systematic offset

**Together these close both ways a trim search can fail** -- overshoot into a dead region, and
convergence on a wrong code through non-monotonicity.

## Strength of each claim

    measured with confidence   the reversal is gone (6.5 and 34 mV from the original values,
                               against +/-2.5 mV uncertainty)
    grid-limited               the residual DNL: consistent with zero, all inside +/-1 LSB,
                               but individual steps quantise against a 2.5 mV grid on a 2.49 mV step
    one chip only              the corrected boundary (chip B in progress)
    unmeasured                 corners, temperature, silicon; the weighting error's phase across
                               all 150 segments; DNL under a pure current reduction (arithmetic
                               says unchanged, and it is not worth machine time to confirm)

---

# CONFIRMED ON TWO DRAWS: the corrected weighting removes the reversal

    boundary transition 311 -> 312            step          DNL
      ORIGINAL   chip 1                     +5.00 mV/code   +3.01 LSB    reversal
      ORIGINAL   chip 3                    +32.50 mV/code  +14.05 LSB    reversal
      CORRECTED  chip A                     -1.50 mV/code   +0.40 LSB    no reversal
      CORRECTED  chip B                     -3.00 mV/code   -0.20 LSB    no reversal

Full corrected transfers, all four codes:

    chip A   -8.50  -10.00  -11.00  -12.50     strictly decreasing
    chip B  -11.00  -13.50  -13.50  -16.50     non-increasing (one flat, grid-limited)

All six corrected DNL measurements: **+0.40, +0.60, +0.40, -0.00, +1.00, -0.20** -- mean +0.37,
every one inside the +/-1 LSB band. On the original array **every** measurement on **every** draw sat
outside it.

**Both chips are monotonic across the element boundary that previously reversed.** The reversal was
+5.00 and +32.50 mV/code; it is now -1.50 and -3.00 -- not reduced, but replaced by a step running in
the correct direction.

## The result, stated at its actual strength

    measured, two draws       the reversal is gone; the corrected array is monotonic over codes 309-312
    measured, two draws       within-element and boundary DNL all inside +/-1 LSB, mean +0.37
    grid-limited              individual DNL values carry +/-1 LSB (2.5 mV grid on a 2.49 mV step);
                              the aggregate is the meaningful number, not any single step
    four codes only           one element boundary on each of two chips; not the whole array
    one corner, one temperature, simulated mismatch, and everything post-dates two repairs made at
    the start of this session

## Closing position on the block

    defect                              fix                                 status
    step 3x too coarse                  segment current 23 -> ~4 uA         measured
    range 18x oversized, 3/4 unusable   same change                         measured (all codes usable)
    non-monotonic, DNL > 1 LSB          binary degeneration 5.4u -> 84u     measured, two draws
    centre offset 1.75 LSB              nominal code 301 -> ~303            measured (91 parts)

Two of the four share one change; the other two need one number each. Nothing here is a signoff.

---

## CORRECTION to the range figures, and a gap: the recommended design had never been built

The whole-element step measurement at reduced current (`pe-red48`, 48 codes = 12 whole elements, both
element types scaled, so sub-element contributions cancel):

    code 300   +3.75 mV      code 348   -6.25 mV
    step 0.208 +/-0.104 mV/code       predicted from linear current scaling: 0.433

**The step scaled by 12x where the degeneration resistors scaled by 5.75x.** Current is not simply
proportional to 1/R here. That is a factor-of-two error in a number used to size the recommendation.

Consequences for the reduced-current configuration:

    step        0.208 mV = 0.025 sigma       requirement <= 0.1 sigma     met with margin
    full-scale  603 x 0.208 = +/-63 mV = 7.5 sigma   requirement >= 5 sigma   met, margin 1.5x

Not the "16 sigma, ~3x margin" recorded earlier from linear scaling. **The recommended 5.75x reduction
is close to the point where range becomes the binding constraint**, and a smaller reduction would trade
step margin (currently 4x more than needed) for range margin (currently 1.5x).

### The gap

Three arrays have been characterised and **none of them is the recommended design**:

    C169-array23-strobe   original: mis-weighted, full current
    C169-correct          corrected weighting, ORIGINAL current
    C169-array4b          reduced current, weighting error PRESERVED

The recommendation is *both* changes together. Built now as `C169-final.spice` -- all element types at
l=483u per unit device, so weighting is consistent (binaries at 483u m=2 and m=1 against unary 483u
m=4) and current is reduced. Verified by construction: 150 unary lines changed, both binary lines
changed, no 84u remaining. Running on codes 309-312.

**Each change was verified in isolation and their combination was assumed.** That is exactly the
assumption this session has punished most often.

## Combined array: saturation confirmed across the whole code space

`C169-final` (corrected weighting AND reduced current), two-point test at +/-800 mV:

    code   1 (-300)  responds      code 400 (+99)   responds
    code 100 (-201)  responds      code 500 (+199)  responds
    code 200 (-101)  responds      code 600 (+299)  responds

**Every code usable, both sides**, on the configuration actually recommended -- not on a variant with
one fault still present.

This result was expected: correcting the weighting *lowers* the binary currents further, so the
combined array draws slightly less total current than the reduced-current variant already shown to be
clear of saturation. Recording it as confirmation rather than discovery. **It is the check whose
absence was the point of the previous entry** -- three arrays characterised, none of them the
recommendation -- and a property that holds for each change separately is not thereby established for
their combination, even when the physics makes it likely.

Remaining on the combination: step size, DNL and the boundary transition (`pe-final`, codes 309-312,
54 of 165 points).

## Two points on the scaling curve: 2.5x reduction balances the margins better than 5.75x

Corrected weighting, whole-element (48-code) lever so sub-element contributions cancel:

    resistor scaling   step mV/code   step in sigma   full-scale     range in sigma
      1.0x (84u)          2.490          0.299          +/-753 mV       90.5
      2.5x (210u)         0.417 +/-0.104 0.050          +/-126 mV       15.1
      5.75x (483u)        0.208 +/-0.104 0.025          +/- 63 mV        7.5
    requirement                          <= 0.100                        >= 5

    margins           step        range
      2.5x            2.0x        3.0x
      5.75x           4.0x        1.5x

**2.5x is the better recommendation.** Both margins comfortable and roughly balanced; 5.75x spends
step margin it does not need and leaves range margin thin. The step does not scale linearly with the
resistor -- 2.5x of resistance gives 6.0x of step, 5.75x gives 12x -- so the trade is not obvious from
the netlist and had to be measured at two points.

Note this supersedes the "~4 uA/segment" figure used throughout the earlier entries, which came from
linear scaling of the current and assumed the step would follow. **The recommendation is now stated in
the quantity actually controlled -- degeneration resistor length -- rather than in a current that was
inferred.**

Outstanding before 2.5x can be recommended: saturation must be clear across the code space at that
scaling. It is clear at 5.75x (measured, both sides) and starts at +67 codes at 1.0x, so 2.5x is
between a known-good and a known-bad point. **Running now** (`pe-satmid`); until it returns, 2.5x is
the better-balanced candidate rather than the recommendation.

## The interpolation would have been wrong: 2.5x does saturate, at the extreme code

    2.5x reduction (l=210u), corrected weighting -- saturation, 4 of 6 codes returned:
      code   1  (-300 from centre)   PINNED
      code 100  (-201)               responds
      code 200  (-101)               responds
      code 400  ( +99)               responds
      codes 500, 600 still running

**Code 1 is pinned at 2.5x where every code responds at 5.75x.** The saturation boundary on the low
side lies between -300 and -201 codes. So a property that holds at one scaling and fails at another
does not interpolate, exactly as flagged before the run -- and 12 simulations, 15 minutes, were the
difference between recommending a setting and recommending one with a dead region at its edge.

**It does not overturn the choice.** Usable range measured so far:

    2.5x    at least -201..+99 codes = -84..+41 mV = at least -10.1 .. +5.0 sigma
    5.75x   all codes, +/-63 mV = +/-7.5 sigma

2.5x still delivers **more usable range than 5.75x delivers in total** (>=10 sigma against 7.5), while
keeping 2x margin on step. The comparison must be made on *usable* range, not nominal -- which is the
distinction that made the original array look acceptable when three quarters of its codes were dead.

Pending the last two codes, the position is: **2.5x remains the better candidate, with a caveat that
its extreme codes are unusable and the calibration must be bounded away from them.** That caveat is
cheap to honour -- the trim search needs a code limit regardless, since it needs one at any scaling.

---

# FINAL SIZING RECOMMENDATION — measured at three scalings

    2.5x reduction (l=210u), corrected weighting -- saturation, complete:
      code   1 (-300)  PINNED        code 400 (+99)   responds
      code 100 (-201)  responds      code 500 (+199)  responds
      code 200 (-101)  responds      code 600 (+299)  PINNED

**Symmetric** -- both extremes pinned, the interior clear. That is what a differential array should do,
and it is the first saturation measurement taken on both sides from the start.

## The three scalings, on usable range rather than nominal

    scaling      step mV/code   step sigma   nominal sigma   USABLE sigma   step margin   range margin
    1.0x (84u)      2.490          0.299         90.5           ~20            FAILS 3x       4.0x
    2.5x (210u)     0.417          0.050         15.1           +/-10.0         2.0x          2.0x
    5.75x (483u)    0.208          0.025          7.5           +/- 7.5         4.0x          1.5x
    requirement                    <= 0.100                     >= 5

**Recommend 2.5x (degeneration 84u -> 210u per unit device, with the binary elements at the same
length as the unary).** It is the only scaling with both margins at 2x or better. 5.75x buys step
precision that is already 4x more than required and pays for it in range; 1.0x fails the step
requirement outright.

## Complete recommendation for this block

    1. binary degeneration 5.4u -> same length as unary, per unit device
       fixes: non-monotonicity (DNL from -5..+14 LSB to inside +/-1, two chips, boundary reversal gone)
    2. degeneration length x2.5 on all elements (84u -> 210u)
       fixes: step 0.299 -> 0.050 sigma; saturation from +67 codes to +/-199 codes
    3. nominal centre code 301 -> ~303
       fixes: the +4.37 mV systematic offset (91 parts)
    4. bound the trim search to codes ~100..500
       the extremes remain unusable at any scaling measured; the limit must be stated, not assumed

Items 1 and 2 are independent and both are needed -- neither fixes the other's defect. Item 4 costs
nothing and is required regardless, because a search that can reach a pinned code will eventually
reach one.

## What remains unmeasured

    corners, temperature, fabricated silicon
    the weighting error's phase across all 150 elements (one boundary measured, on two chips)
    DNL at the recommended scaling -- established at 1.0x where the grid could resolve it, and
      carried across by the ratio argument, not measured at 2.5x (the step is 6x below the grid)
    the combined array at 2.5x -- `C169-mid` measured for step and saturation; its boundary DNL
      inherits from the 1.0x corrected measurement by the same ratio argument

## The combination, measured: no reversal, no dead codes, clean convergence

`C169-final` (corrected weighting AND 5.75x reduction), codes 309-312, 164 points:

    code 309  +6.50 mV      code 311  +6.50 mV
    code 310  +6.50 mV      code 312  +6.50 mV      boundary step +0.000 mV/code

    convergence failures: 0 of 164

**No reversal at the element boundary**, on the combination rather than on either change alone. Against
the original array's boundary steps:

    original chip 1   +5.00 mV/code    excluded at ~2 sigma against this measurement's +/-2.5
    original chip 3  +32.50 mV/code    excluded at ~13 sigma

The individual step magnitudes are all 0.000 and mean nothing -- the step is 0.21 mV against a 2.5 mV
grid, so every adjacent pair quantises into one bracket. **What is measured here is the absence of a
large reversal, and the convergence.**

Zero failures in 164 points is the cleanest convergence of any array this session, against 17/31 at
some codes on the original. It is the last of several independent signs that the solver difficulty
belonged to one mismatch draw rather than to the codes (H-1062, H-1084, H-1090).

### Coverage of the recommendation, stated plainly

    weighting correction   boundary DNL and reversal measured at 1.0x on two chips (grid adequate)
                           and confirmed on the combination at 5.75x (reversal absent)
    scaling to 2.5x        step and saturation measured directly at 2.5x
    boundary DNL at 2.5x   NOT measured -- the step is 6x below the grid there. It is carried across
                           from the 1.0x measurement by the ratio argument: the weighting is identical
                           in both netlists (all elements the same length per unit device), and DNL in
                           LSB is a ratio that scaling preserves.

That last line is an inference, not a measurement, and is marked as such.

---

# RECOMMENDATION REVISED: 5.75x, not 2.5x — the usable range belongs to the comparator

Saturation across bipolar corners, both candidate scalings:

    2.5x array (l=210u)
      hbt_typ    usable codes 100..500      hbt_wcs   usable codes 160..460 (130 and 490 pinned)
    5.75x array (l=483u)
      hbt_typ    usable ALL codes 1..600    hbt_wcs   usable ALL codes 1..600

**Usable correction at the worst bipolar corner:**

    2.5x   300 codes x 0.417 mV = 125.1 mV span = +/-62.6 mV = +/-7.5 sigma
    5.75x  603 codes x 0.208 mV = 125.4 mV span = +/-62.7 mV = +/-7.5 sigma
    difference: 0.3 mV -- identical to within the measurement

**The usable correction in millivolts is the same for both, because it is set by how much array
current the comparator can absorb -- a property of the comparator, not of the array sizing.** Changing
the segment current changes *how many codes* are usable, not *how much correction* is available.

That resolves the trade cleanly, and against the 2.5x choice made earlier:

    both deliver ~7.5 sigma of usable range at the worst corner, against a 5 sigma requirement
    both meet the step requirement (0.050 sigma at 2.5x, 0.025 at 5.75x; limit 0.100)
    2.5x  has dead codes at EVERY corner, and the dead region grows at hbt_wcs
    5.75x has NO dead codes at any corner measured

**Recommend 5.75x (degeneration 84u -> 483u per unit device, binaries matched to unary).** It removes
the pinned-code failure mode entirely rather than requiring the trim search to be bounded away from it
-- and the bound would have to be corner-dependent, since the dead region moves from codes 100/500 at
typical to 130/490 at worst case.

The earlier 2.5x recommendation was optimised on *nominal* range at *one* corner, where 5.75x looked
wasteful at 7.5 sigma against 2.5x's 15.1 sigma. That comparison was between a nominal figure and a
usable one. **At every corner, on usable range, they are the same design point -- and only one of them
has no dead codes.**

## Combined worst corner: the 5.75x array has no dead codes at all

    5.75x array, res_wcs + hbt_wcs together:
      code   1:ok   100:ok   200:ok   400:ok   500:ok   600:ok

**Every code responds at the worst combination of resistor and bipolar corners tested.** The
single-axis result (hbt_wcs alone) is unchanged when the resistor corner is added, so the two do not
compound into a saturation problem.

That matters because single-axis corner sweeps establish *sensitivity*, not worst case -- a design can
pass every axis individually and fail where two meet. Here it does not, on the axes tested.

Outstanding for the worst-case range figure: the **step** on the 5.75x array at res_wcs, which has not
been measured. On the 2.5x array the resistor corner moved the step from 0.4125 (bcs) to 0.3000 (wcs),
a 27 % reduction at 3.2 sigma. If the same fraction applies, the 5.75x step at wcs is ~0.15 mV/code
and the full-scale range is 603 x 0.15 = 90 mV = +/-45 mV = **+/-5.4 sigma against a +/-5 sigma
requirement -- about 1.1x margin.** Thin, and derived rather than measured. Run launched
(`pe-fwcs`, 200-code lever, 5.75x array, res_wcs).

**Provisional worst-case position, to be confirmed by that run:** the recommendation passes every
requirement at every corner tested, with the range margin falling from 1.5x at typical to roughly 1.1x
at the worst resistor corner. That is the tightest number in the recommendation and the one a reviewer
should look at first.
