# The chain will not simulate a noise transient away from 27 °C

The feedback fix in
[`../bit-autocorrelation/`](../bit-autocorrelation/) takes the bit correlation from
0.777 to 0.079. Confirming it over process, voltage and temperature was the next step,
and **it cannot be done yet** — not because the fix fails, but because the chain's noise
transient does not converge at any temperature other than 27 °C.

**The fix is therefore confirmed at typical only.** That is a limit on the evidence, not
a finding against the circuit, and it is recorded here so nobody reads the typical result
as a PVT result.

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
