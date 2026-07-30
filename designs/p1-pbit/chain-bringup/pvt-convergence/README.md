# PVT convergence: fragile and path-dependent, and the fix holds at two corners

**Read the correction at the bottom before the analysis in the middle.** This page was
written in two passes and the first pass over-generalised. Current state:

- the feedback fix in [`../bit-autocorrelation/`](../bit-autocorrelation/) is confirmed at
  **typical and at cold** — ρ₁ = 0.079 at 27 °C and **0.032** at FF / −40 °C / VDD +10%;
- **every corner runs**, including 125 °C, once the maximum timestep is 2 ps rather than 5 ps.
  Self-heating was never disabled, and that remains the reference path;
- **self-heating is confirmed as the mechanism** behind the aborts: over 20 ns at 125 °C and
  5 ps the identical deck completes with `selft=0` (10,496 rows) and aborts at 313.5 ps with
  `selft=1`. Disabling it costs less than the measurement error at 27 °C — but that was
  established at the corner where self-heating matters *least*, and 20 ns is inside the
  settling either way, so it is a labelled diagnostic and **not a measurable hot corner**
  ([below](#self-heating-confirmed-as-the-blocker-and-the-cost-of-disabling-it));
- but at 2 ps a 300 ns run **exhausts memory at 40 ns**, so a fine step and a long window
  cannot be had together, and 40 ns is inside the ~100 ns coupling settling;
- so **no corner has yet been measured over a valid window except typical and cold**, and any
  PVT correlation figure taken over 40 ns is a settling measurement — at 27 °C alone, a 40 ns
  window reads ρ₁ = 0.41 where 200 … 300 ns reads 0.079;
- convergence is **not monotonic in distance from typical**: temperature alone at −40 °C
  aborts, and −40 °C *combined with* the fast MOS corner completes;
- the `.ic` preset suggested further down is **withdrawn** — the coupling node starts at the
  right value and is driven away by the noise switching on, so presetting it changes nothing;
- reducing the coupling bias from **50 kΩ to 5 kΩ** does make short windows usable —
  P(bit=1) = 0.560 from 2 ns against 0.989 before — and **costs correlation**, ρ₁ rising from
  0.079 to 0.118. A trade to decide, not a fix to adopt.

The sections below record how that was arrived at, including three conclusions that had to be
withdrawn, because the withdrawn reasoning is the useful part.

> **Note on this page's structure.** It has been amended in four passes and its later sections
> contradict its earlier ones by design. That is honest but it is not readable, and it should be
> restructured into "what is true" followed by "what was withdrawn and why". Recorded as debt
> rather than left implicit.

## First pass: both corner runs abort

The original attempt used these two corner definitions, and both failed at ~11 ns of 300.

## What happens

Both corner runs abort at the same place:

```
doAnalyses: TRAN:  Timestep too small; time = 1.09131e-08, timestep = 6.25e-24:
  trouble with xamp.xq1:npn13g2_nx_vbic-instance q.xamp.xq1.qnpn13g2
```

| run | reaches |
| --- | --- |
| hot: 125 °C, `hbt_wcs`, `res_wcs`, `mos_ss`, supplies −5% | **10.9 ns** of 300 |
| cold: −40 °C, `hbt_bcs`, `res_bcs`, `mos_ff`, supplies +5% | **11.0 ns** of 300 |
| typical: 27 °C | 300 ns, complete |

`xamp.xq1` is the **amplifier's** input pair, not the comparator or the interface under
test. Per the lesson in the noise-convergence page, a device named in a timestep collapse
is where the solver gave up, not necessarily the cause.

## Bisected to one axis: temperature alone

Changing exactly one thing from typical, 20 ns each — long enough to pass the 11 ns
failure point:

| axis changed | result |
| --- | --- |
| **temp = 125 °C** | **aborts** |
| **temp = −40 °C** | **aborts** |
| `mos_ss` | completes |
| `hbt_wcs` | completes |
| `res_wcs` | completes |
| supply −5% | completes |

**Temperature alone does it, at both extremes.** No device corner and no supply shift
reproduces it. Failing at *both* ends rather than one is what makes this look like a
simulation property rather than a one-sided physical effect.

## The mechanism is not identified, and one hypothesis is untested rather than refuted

> **RESOLVED — this section is superseded.** Self-heating *is* the mechanism; it was tested
> properly later and confirmed. The scoping guess below is right: `selft` is declared inside
> `.subckt npn13G2`, so it must be overridden per instance. See
> [Self-heating confirmed as the blocker](#self-heating-confirmed-as-the-blocker-and-the-cost-of-disabling-it).
> The text below is kept as the state of knowledge at the time.

The `npn13G2` model carries self-heating: `sg13g2_hbt_mod.lib` sets `selft=1` and
`rth = selft·3.26E+03·(4/Nx)^0.9`, and the runs emit ngspice's *"check your power
dissipation and improve your heat sink Rth"* warning. A stiff thermal network away from
nominal temperature is a plausible cause.

**It has not been tested.** Adding `.param selft=0` at the top level of the deck changed
nothing — but the heat-sink warning still fired in that run, which shows the override
never reached the model. The parameter is scoped inside the model library, so a top-level
`.param` does not shadow it. **So self-heating remains a candidate, neither confirmed nor
ruled out**, and the negative result of that attempt says nothing about the hypothesis.

Testing it properly needs the override applied where the model can see it — a modified
copy of the library section, or `selft` passed per instance if the subcircuit exposes it.
Neither is done here.

## Why this matters beyond one fix

Temperature corners are not optional for a tape-out. Every transient result in this
repository — the counted bit probability, the autocorrelation, the interface behaviour —
is at 27 °C, and none of them can currently be repeated hot or cold. AC and DC analyses
over temperature have worked before on this project, so the block is specific to long
noise transients rather than to temperature simulation generally.

**Nothing here licenses disabling self-heating to make the corners run.** If self-heating
turns out to be the mechanism, switching it off buys convergence by removing physics that
is real at 125 °C, which is precisely the corner where it matters most. The options worth
weighing are a shorter transient with more samples per unit time, tighter solver
tolerances, or a deliberately documented reduced-order thermal model — not a silent flag.

## Reproducing

```
ngspice -b c2_hot.cir        # aborts at 10.9 ns
ngspice -b c2_cold.cir       # aborts at 11.0 ns
ngspice -b bis_temp125.cir   # temperature alone, aborts
ngspice -b bis_mos_ss.cir    # device corner alone, completes
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. Corner section names differ by library and are
worth writing down: MOS uses `mos_tt` / `mos_ss` / `mos_ff` / `mos_sf`, while resistors,
HBTs and capacitors use `_typ` / `_bcs` / `_wcs`. `mos_typ` does not exist.

## CORRECTION: convergence is path-dependent, and the fix does hold cold

The bisection above is a correct set of measurements and the conclusion drawn from it —
"temperature alone aborts, so the fix is confirmed at typical only" — is too pessimistic.
**Adding a second deviation rescues a failure caused by the first.**

| deck | 20 ns result |
| --- | --- |
| temp = −40 °C alone, `mos_tt` | **aborts** |
| temp = −40 °C, VDD +10%, `mos_tt` | **aborts** |
| temp = −40 °C, VDD +10%, **`mos_ff`** | **completes** |

So convergence here is **not a monotonic function of distance from typical**. Going further
from nominal on a second axis made a failing run converge. That is ordinary solver
behaviour, and it has a methodological consequence worth stating: **single-axis bisection
identifies the axis that breaks convergence in isolation, and does not predict which
combinations converge.** It answered the question it was given and I generalised past it.

## The fix holds at the cold corner

Running the full 300 ns transient at that corner — `mos_ff`, −40 °C, VDD 1.32 V, HBT and
resistors typical — sampling from 200 ns as always:

| | typical, 27 °C | **cold, FF, −40 °C** |
| --- | --- | --- |
| ρ₁ | +0.079 | **+0.032** |
| ρ₂ … ρ₅ | +0.108, +0.031, +0.109, +0.051 | +0.038, +0.016, +0.062, +0.040 |
| P(bit=1) | 0.517 | **0.5030** |
| variance inflation | 1.75 | 1.37 |
| corrected standard error | 0.0295 | 0.0262 |
| z against 0.5 | +0.57 | **+0.11** |
| `cml_out_p` mean | 0.6336 V | 0.6623 V |

Every lag at both corners is inside the 0.045 standard error on ρ. **The feedback fix is
now confirmed at two corners, not one**, and the cold corner is if anything slightly
better than typical.

### An independent measurement of the same corner disagrees, and this one is the more likely

A separate PVT matrix reports **ρ₁ = 0.2575** at FF / −40 °C / 1.32 V, with P(b=1) = 45.0%
— eight times the correlation measured here. It also honestly reports the 125 °C corner as
failed rather than concluding around it, which is the right behaviour.

The discrepancy is not resolved, but there is a specific candidate: **the sampling window.**
Every measurement on this page discards the first 200 ns, because the interstage coupling
network needs ~100 ns to settle and a decaying offset inside that window inflates ρ — that
is the mechanism that produced three all-zero bitstreams before it was found (see
[`../counted-bitstream/`](../counted-bitstream/)). A run that samples from early in the
transient would show exactly this: correlation several times too high, at any corner.

**The number to compare is the start of the sampling window**, not the correlation. If it
is earlier than ~200 ns the two measurements are measuring different things.

## Still open: the hot corner

125 °C has not been made to run by either measurement. The mechanism remains unidentified
and self-heating remains untested rather than refuted, for the reasons in the section above.

## The hot corner does run — at a 2 ps maximum timestep — and memory, not convergence, is the wall

The "125 °C runs nowhere" above is also wrong. Tried three things on the hot deck over 40 ns:

| change | result |
| --- | --- |
| maximum timestep 5 ps → **2 ps** | **completes** |
| `reltol=1e-4`, `abstol=1e-13` | aborts |
| `method=gear` | aborts |

**A finer maximum step is what it needed**, not tighter tolerances and not a different
integrator. So the earlier failure was a step-size choice of mine, and the physics stays
intact — no self-heating flag was touched.

But 300 ns at 2 ps does not finish either. It reaches **40.0 ns** and dies with
`Setting the output memory is not possible` — 150,000 points across several vectors exhausts
the available memory. So on this deck a fine step and a long window cannot be had together,
and **40 ns is the practical ceiling at the hot corner.**

## Which makes every corner number a settling measurement, and that is the whole discrepancy

40 ns is well inside the ~100 ns interstage coupling settling. To measure what that does,
hold **temperature fixed at 27 °C** and change only the resistor corner, sampling a 40 ns
window:

| corner, 27 °C, 40 ns window | P(bit=1) | ρ₁ | ρ₂ | ρ₃ |
| --- | --- | --- | --- | --- |
| `res_typ` | 0.963 | **+0.4065** | +0.2580 | +0.1095 |
| `res_wcs` | 0.968 | **+0.4835** | +0.3113 | +0.1390 |
| `res_bcs` | 0.958 | **+0.4778** | +0.3471 | +0.2163 |

Compare the same circuit, same corner, over a 200 … 300 ns window: **ρ₁ = 0.079, P(1) = 0.517.**

Two things follow, and neither involves temperature.

**Window length dominates.** ρ₁ goes from 0.079 to 0.41 purely by shortening the window, and
P(bit=1) goes from 0.517 to 0.96 — degenerate. A short window does not measure a slightly
worse version of the circuit; it measures the settling transient.

**And the resistor corner alone moves apparent ρ₁ from 0.41 to 0.48 with temperature held
constant**, because the coupling network's time constant is set by those resistors. So a
corner-to-corner spread in apparent correlation is expected from the settling alone, and a
PVT matrix measured over a short window will show one whether or not the circuit degrades.

**A separately reported matrix gives ρ₁ of 0.046 / 0.165 / 0.580 for typical / cold / hot over
40 ns.** Its typical value is close to the long-window figure, so its window must sit later in
the settling than the one used here — the numbers are not directly comparable. What the
measurements above establish is that this ordering is **producible without any temperature
effect at all**, so it is not evidence of one.

## What would make short-window corner measurements valid

The settling, not the solver, is the obstacle. Options, in order of directness:

1. **Preset the coupling nodes with `.ic`** to their settled DC values, so no settling
   transient occurs and a 40 ns window is usable from the first nanosecond. This is the clean
   answer and it changes no devices.
2. **Reduce the coupling time constant** — the ~2 pF into ~50 kΩ bias network is what costs
   100 ns. Smaller bias resistors would shorten it, at the price of loading. That is a design
   change with an independent justification: a 100 ns settling makes every corner measurement
   expensive.
3. Write out fewer vectors so the memory ceiling arrives later, which buys window length
   rather than removing the need for it.

## RETRACTED: `.ic` cannot fix the settling, because the settling is driven not initial

The `.ic` option offered above was wrong, and not merely misapplied. Presetting the coupling
nodes cannot help, because **they already start at the right value.**

The coupling node's DC operating point is a zero differential, by symmetry. The measured
differential goes **0 → −7.9 mV over 2 … 20 ns → back toward zero by 150 … 200 ns**. It is not
starting from a bad state and converging; it starts correct and is **driven away by the noise
source turning on at t = 0**, then recovers with the high-pass time constant. An initial
condition on a node that already begins correct changes nothing.

(An attempt with `.ic` plus `uic` also fails for a second, separate reason: `uic` skips the
operating point altogether, so every node not given an explicit `.ic` starts at zero and the
run dies at the initial timepoint with *"The temperature limiting function received NaN"*.
`.ic` without `uic` is the correct usage — but per the above it would not have helped anyway.)

So the settling is unavoidable for a high-pass network responding to a signal that switches
on. The only real levers are **wait longer** or **make the time constant smaller.**

## Making the time constant smaller: it works, and it costs correlation

`XRB2_1` / `XRB2_2` are `rppd` 192 µm at w = 1 µm — **49.99 kΩ** — and with ~2 pF of coupling
they set the ~100 ns constant. Reducing them to 19 µm gives **5.01 kΩ**, a 10× cut.
`p1_noise_amp_fastbias.spice`, same noise seed, 300 ns:

| window starts at | N | P(bit=1) | ρ₁ |
| --- | --- | --- | --- |
| 2 ns | 1490 | **0.560** | +0.1997 |
| 20 ns | 1400 | 0.535 | +0.1637 |
| 50 ns | 1250 | 0.522 | +0.1447 |
| 100 ns | 1000 | 0.522 | +0.1554 |
| 200 ns | 500 | 0.496 | **+0.1180** |

Against the original network, where a window starting at 2 ns gives **P(1) = 0.989** —
degenerate.

**So it does what it was meant to.** P(bit=1) is usable from 2 ns onward rather than
requiring 200 ns of discard, which is exactly what makes short-window corner measurement
viable under the memory ceiling.

**And it costs correlation.** ρ₁ at the settled window rises from **0.079 to 0.118** — same
seed, same window, so the difference is the circuit. The likely mechanism is loading: 5 kΩ
across the coupling node attenuates the signal reaching the comparator, so the interface's
residual memory is a larger fraction of what is left. Still 6.6× better than the unfixed
0.777, but at N = 500 it is about 2.6 standard errors from zero rather than comfortably
inside the noise.

**This is a trade to decide, not a fix to adopt.** Faster settling buys corner coverage;
higher correlation spends part of what the feedback fix won. The sizing between 50 kΩ and
5 kΩ has not been explored, and the right value is probably not either endpoint.

## Self-heating confirmed as the blocker, and the cost of disabling it

Two sweeps ago this page recorded self-heating as *untested rather than refuted*: an attempt to
switch it off had produced no change, and the reason was unknown. The reason is now known, and
it was a mistake in how the switch was set, not a property of the circuit.

`selft` is declared as a `.param` **inside** `.subckt npn13G2`:

```
.subckt npn13G2 c b e bn
.param Nx=1 dtemp=0
+Ny=1 le=0.96e-6 we=0.12e-6
+El=le*1e6
+selft=1
```

A `.param selft=0` at the top level of a netlist does not reach it — the subcircuit's own
declaration shadows the outer name. The override has to be applied **per instance**:

```
XQ1 c b e sub! npn13G2 Nx=1 selft=0
```

The tell was on screen the whole time. Every run kept printing

```
Please check your power dissipation and improve your heat sink Rth!
```

which is the self-heating code speaking. A warning from a feature believed to be disabled is
direct evidence that it is not disabled, and it was read past for four sweeps.

### The controlled comparison

Identical deck, 125 °C, 5 ps maximum timestep — the step that aborts with the physics intact.
This is the **20 ns bisection deck** from the section above, chosen for the same reason it was
chosen there: long enough to pass the point where the hot corner gives up. `selft=0` applied to
all 21 `npn13G2` instances (13 in `p1_comparator`, 8 in `p1_noise_amp`):

| run | result | data rows | heat-sink warning |
| --- | --- | --- | --- |
| 125 °C, 5 ps, 20 ns, `selft=0` × 21 | **completes** | 10,496 | absent |
| 125 °C, 5 ps, 20 ns, `selft=1` (default) | **aborts at 313.5 ps** | 166 | present |

Two controls, not one. The warning's disappearance confirms the override took effect — which
is exactly what the earlier attempt could not show. The **data-row count** confirms the run
produced a transient rather than merely failing to print an error; 10,496 rows against 166.

> The `.meas` lines in [`noself125.log`](noself125.log) report `out of interval` and return
> zeros. That is an artefact of a 300 ns deck's measurement statements left on a 20 ns run,
> **not** a failed simulation. It is recorded here because "no error string" was very nearly
> taken for "it worked" — the row count is what actually settles it.

**So self-heating is the convergence blocker.** That was previously a hypothesis; it is now a
measurement.

### What this does *not* buy

Convergence is not a measurement. 20 ns is still well inside the ~100 ns coupling settling
documented above, so a hot corner that now *runs* still yields **no valid hot-corner result**.
What has been established is the mechanism, not a measurable corner. The settling constraint
and the 40 ns memory ceiling are untouched by this.

### What disabling it costs — and why that number does not license using it

Confirming the mechanism is not permission to remove it. The thermal feedback is real at
125 °C and will be present in fabricated silicon; a run that converges because the hard part
was deleted is not evidence about the chip. So rather than argue the point, the error was
measured. Candidate-2 comparator, same noise seed, same 300 ns run, 27 °C:

| window from | `selft=1` P(1) | `selft=0` P(1) | `selft=1` ρ₁ | `selft=0` ρ₁ |
| --- | --- | --- | --- | --- |
| 2 ns | 0.989 | 0.602 | — | +0.2275 |
| 50 ns | — | 0.549 | — | +0.1511 |
| 200 ns (settled) | **0.517** | **0.530** | **+0.079** | **+0.0664** |

At the settled window the differences are 0.013 in P(1) against a standard error of ≈0.030,
and 0.013 in ρ₁ against ≈0.045. **Both are inside the measurement error**: at 27 °C, switching
self-heating off changes the result by less than this measurement can resolve.

The limit of that result is the important part, and it is a limit of where it was taken:

> The simplification was validated at **27 °C**, which is the condition under which the
> devices heat themselves *least*. The condition where it would actually be used is
> **125 °C**, which is precisely where the removed physics matters *most*. The evidence and
> the intended application sit at opposite ends of the temperature range.

That gap is not closed by the table above and no amount of room-temperature data will close it.

### Standing rule adopted

- The **2 ps timestep with self-heating intact** remains the reference path for any corner
  result that is quoted as a property of the circuit.
- `selft=0` is permitted as a **first look** at a corner otherwise unreachable, on two
  conditions: every number derived from it is labelled *thermally simplified* wherever it
  appears, and nothing is concluded from it before a full-physics run agrees.
- The decks in this directory carry `DIAGNOSTIC ONLY` on their first line for that reason.

### Files

- [`noself125.cir`](noself125.cir) / [`noself125.log`](noself125.log) — the 125 °C, 5 ps,
  20 ns run that completes with self-heating off (its `.meas` errors are a leftover 300 ns
  window, not a failure)
- [`noself27.cir`](noself27.cir) / [`noself27.log`](noself27.log) — the 27 °C cost
  measurement, a full 300 ns run at 150,005 rows
- [`p1_comparator_cand2_noself.spice`](p1_comparator_cand2_noself.spice),
  [`p1_noise_amp_noself.spice`](p1_noise_amp_noself.spice) — the two blocks with `selft=0`
  on every `npn13G2` instance. **Diagnostic variants; not the design netlists.**
