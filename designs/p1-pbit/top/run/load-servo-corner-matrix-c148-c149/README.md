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
