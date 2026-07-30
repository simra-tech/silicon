# PVT convergence: fragile and path-dependent, and the fix holds at two corners

**Read the correction at the bottom before the analysis in the middle.** This page was
written in two passes and the first pass over-generalised. Current state:

- the feedback fix in [`../bit-autocorrelation/`](../bit-autocorrelation/) is confirmed at
  **typical and at cold** — ρ₁ = 0.079 at 27 °C and **0.032** at FF / −40 °C / VDD +10%;
- **every corner runs**, including 125 °C, once the maximum timestep is 2 ps rather than 5 ps.
  Self-heating was never disabled;
- but at 2 ps a 300 ns run **exhausts memory at 40 ns**, so a fine step and a long window
  cannot be had together, and 40 ns is inside the ~100 ns coupling settling;
- so **no corner has yet been measured over a valid window except typical and cold**, and any
  PVT correlation figure taken over 40 ns is a settling measurement — at 27 °C alone, a 40 ns
  window reads ρ₁ = 0.41 where 200 … 300 ns reads 0.079;
- convergence is **not monotonic in distance from typical**: temperature alone at −40 °C
  aborts, and −40 °C *combined with* the fast MOS corner completes.

The sections below record how that was arrived at, including the conclusion that had to be
withdrawn, because the withdrawn reasoning is the useful part.

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
