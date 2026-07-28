# Self-heating and the p-bit output stream — a paired controlled experiment

P1's noise generator, preamplifier and comparator are SiGe HBTs, and the VBIC models
for them ship with self-heating enabled (`selft=1`). Each device carries a thermal
node whose voltage is its own temperature rise. This measures what that does to the
random bitstream.

The question arose from an anomaly in the raw stream which we then believed to be a
property of the chip. It is not — see the update under Results; it is an artefact of our
own noise source. This note is kept as run, with the correction inline, because the
controlled experiment below stands on its own. The raw stream carries a reproducible
correlation structure at lags of 50–200 bits — roughly 10–40 ns at 5 GS/s — that
survives averaging over independent noise seeds and is not explained by the chain's
frequency response. The model's own thermal time constant is

```
rth = 3.26E+03 * (4/Nx)^0.9        cth = 1.60E-12 * (Nx*0.25)^0.95
tau = rth * cth = 4.83 ns * Nx^0.05
```

which is ~24 bits at 5 GS/s — close to where the structure begins. The Nx exponents
very nearly cancel, so tau is effectively the same for every device in the chain.
That coincidence is what made self-heating worth testing.

## Design

Twelve **paired** segments. Both arms of a pair use the **same seed and the same
1,000-tone excitation**, and differ only in which HBT model library they load:

| arm | library | `selft` |
| --- | --- | --- |
| `selft1` | PDK `cornerHBT.lib` | 1 |
| `selft0` | local `cornerHBT_isothermal.lib` → `sg13g2_hbt_mod_isothermal.lib` | 0 |

Pairing matters more than sample size here. The two arms share their noise
realisation, so the difference between them cancels almost all of it: the paired
floor is **0.0059** against **0.0283** unpaired, a **4.8× gain**. A 2,500-bit
experiment can say nothing arm-against-arm; paired, it can.

## The acceptance test

Four attempts were required before the experiment varied its independent variable.
Each failure read as correct in review and failed silently in execution:

1. no `selft` anywhere — the word appeared only in output filenames;
2. `.param SELFT=0` in the deck — right name, wrong scope. `selft` is a **model-card**
   parameter, and a deck-level `.param` never reaches it;
3. the **corner wrapper** was copied and edited, but `cornerHBT.lib` only
   `.include`s `sg13g2_hbt_mod.lib`, which is where `selft` actually lives;
4. correct: the model file itself copied and edited, wrapper pointed at the copy.

The test that catches all four is deliberately content-free:

> **The two arms' output hashes must differ.** Then, and only then, node `t` must read
> `0.000` in the isothermal arm.

No threshold and no judgement about how large a difference counts. It caught two
failure modes that were not anticipated when it was written. A second clause was added
after three "replicates" turned out to be byte-identical to each other: **hashes must
differ across pairs as well as within them.**

All 12 pairs published here pass both clauses — 24 distinct hashes, `t = 0` in every
isothermal arm and `t = 3.12…3.38` in every baseline. This is checkable from the
included logs.

## Results

**Self-heating is real and does change the output.** Bits differing between arms:
1.24, 1.24, 1.08, 1.36, 1.08, 1.32, 0.96, 0.84, 1.16, 1.04, 1.16, 1.04 % — mean
**1.13 %**.

**It is not the cause of the long-lag structure.** Explaining that would require
~0.011 in the paired difference. Measured, pooled over 12 pairs:

| lags | paired-difference spread |
| ---: | ---: |
| 3–20 | 0.0015 |
| 21–50 | 0.0017 |
| 51–100 | 0.0018 |
| 101–200 | 0.0017 |

Largest anywhere **0.0018** — a factor of six below what is required, and flat across
every band. The hypothesis is excluded.

> **Update, same day.** The long-lag structure is no longer unexplained, and it is not a
> property of the chip. It is the autocorrelation of our own multi-tone noise source,
> carried through the arcsine law: predicted 0.01196 against measured 0.01223 over lags
> 51-200, correlation +0.90, slope 0.94, nothing fitted. Its cause is the guard that
> pushes tones away from clock submultiples - with the guard the predicted amplitude is
> 0.0120, without it 0.0005. The guard carves a systematic gap around each f_clk/n, and a
> comb of gaps in the spectrum makes a comb in the autocorrelation. The measure taken to
> avoid one artefact created another.

**It does contribute to the adjacent-bit correlation**, which is the constraint that
binds this design. The shift is a broad positive offset across short lags
(**+0.0036** over lags 2–20) with lag 1 roughly double.

### Read this before quoting the number

| pairs | r₁ shift | t |
| ---: | ---: | ---: |
| 4 | +0.0112 | 3.7 |
| 8 | +0.0086 | 4.4 |
| **12** | **+0.0065** | **4.16** |

The effect is clearly real — positive in 11 of 12 pairs, t = 4.16. **Its magnitude has
fallen by about a quarter at every increase in sample size, three times running.** A
stable effect should wobble around a fixed value as n grows, not walk steadily
downhill. Isolating the four newest pairs, they average **+0.0023** against +0.0086 for
the first eight.

**Existence: solid. Size: not settled, and has only ever moved in one direction.**
Quote 0.0065 as a current best estimate, with that trend attached.

A bias shift would inflate every lag equally and mimic this exactly. It was checked
first: bias accounts for **−2 %** of the offset. The effect is genuine correlation.

### What it means, stated conservatively

Baseline r₁ averages **0.0586** here. Self-heating accounts for **11 %** of it.
Removing thermal coupling entirely would leave r₁ ≈ **0.0521** against a requirement of
**0.0140** — still **3.7× over**.

Thermal design is a genuine lever on the number that decides the architecture, and
device sizing, bias current and heat extraction are worth treating as first-order
choices. **It is not a route to meeting the requirement on the raw stream, and
whitening remains mandatory.** An earlier draft of this note called it a lever without
that arithmetic attached, which read as a reprieve. It is not one.

## Contents, and one deliberate omission

```
generate_paired_runs.py          deterministic deck generator (seeds 1001…12012)
run/sg13g2_hbt_mod_isothermal.lib   the manipulation: 6x selft=0, 0x selft=1
run/cornerHBT_isothermal.lib        corner wrapper pointing at the local model
run/bits_{selft0,selft1}_seg{1..12}.txt    24 extracted bitstreams, 2,500 bits each
run/ngspice_{selft0,selft1}_seg{1..12}.log 24 logs, including the operating points
run/tb_p1_{selft0,selft1}_seg1.spice       2 representative decks, one per arm
```

**The other 22 decks are not included.** Each is 1.9 MB of which 98 % is the PWL noise
table, and they regenerate byte-identically from `generate_paired_runs.py` and the
seed. Shipping 46 MB of deterministically reproducible text would have grown this
repository twentyfold. The two decks that *are* included let you verify the generator
reproduces them exactly before trusting it for the rest.

This is a deliberate departure from our usual rule that a bitstream travels with its
own deck, and it is flagged rather than quietly taken.

Reproduce with `ngspice -b <deck>` after setting `$PDK_ROOT` to an IHP SG13G2
installation.
