# RETRACTED — the amplifier does not rectify its own noise

**Everything this page previously claimed is withdrawn.** It asserted that the
amplifier's differential output carries a DC mean proportional to the noise amplitude
it amplifies, that the input-referred signal-to-offset ratio is therefore 1.25 against
the 39.89 the specification requires, and that this was a fatal defect no trim could
reach. The chip gate was set to *fail* on it. All of that is wrong.

The +31.9 mV was the **interstage coupling network settling**, measured over a window
one fifth as long as its own time constant.

## The measurement that settles it

Between the two amplifier stages the signal passes through `XCAC1` / `XCAC2` — 36.5 ×
36.5 µm MIM capacitors, about 2 pF each — into bases biased through `XRB2_1` / `XRB2_2`,
`rppd` resistors 192 µm long, about 50 kΩ. That is a high-pass corner near 1.6 MHz and a
time constant of roughly **100 ns**.

Every earlier measurement on this page used a window of **2 … 20 ns**.

Extending the run to 400 ns and taking the same average in successive windows —
`walk_long2.cir`, amplifier alone, σ = 3.0818 mV throughout:

| window | mean of `v(NOISE_AMP_P) − v(NOISE_AMP_N)` |
| --- | --- |
| 2 … 20 ns | **+31.90 mV** ← the published figure |
| 60 … 100 ns | +1.328 mV |
| 150 … 200 ns | **+3.3 µV** |
| 250 … 300 ns | +0.616 mV |
| 350 … 400 ns | +0.735 mV |

Four orders of magnitude of decay. The 0.6 … 0.7 mV in the later windows is not a
residual offset: the output noise is 43.7 mV_rms and a 50 ns window holds about 5,000
independent samples, so the standard error on the mean is 43.7/√5000 ≈ **0.6 mV**. The
late windows are consistent with zero to within the precision the measurement has.

## Every piece of the original argument, and why it failed

**"A linear time-invariant system cannot put DC on a zero-mean input, so this must be a
nonlinearity."** True of steady state, false of a transient. A linear high-pass network
that is still charging produces a nonzero mean; that is what charging *is*. The theorem
was applied outside its domain, and it read as rigour — the page said the conclusion was
"free" and needed no further measurement, which in hindsight is the sentence that should
have triggered a check.

**"Linear in σ to four digits."** This was recorded as confirmation and it is the
refutation. A settling transient is a linear response, so its mean scales exactly with
the signal driving it. A rectifier's mean also scales with σ, but nothing else in the
data scaled *identically* — the means and the RMS values both came out at exactly 10.00×
across a tenfold input change, which is the signature of a linear system, not of an
even-order nonlinearity.

**"Not clipping — the ratio holds while peaks go from ±35 mV to ±141 mV."** True and
irrelevant. Ruling out one nonlinear mechanism is not evidence for another.

**"Confirmed on the amplifier alone, no comparator, no clock."** True and irrelevant.
The settling has nothing to do with either.

**"Scale-invariant peak asymmetry, 1.89:1 at both amplitudes."** Also a property of the
transient, and also linear.

**The tail nodes were the tell, and they were in the data.** `walk_hi` / `walk_lo`
measure the two emitter nodes that would have to move if the tail current were being
modulated: **0.562530 V** at full amplitude and **0.562524 V** at one tenth — identical
to six digits, as is the second stage's node at 0.393129 / 0.393073 V. Nothing in the
biasing behaves nonlinearly at any amplitude. That measurement was in the same run as
the result it contradicted.

## The rule this repository now holds itself to

**A transient measurement of a mean or an offset must state its window and the longest
time constant in the circuit, and the window must be several times that constant.**
Where it is not, the number is a settling value and must be labelled one.

For this design the binding constant is the **100 ns** interstage coupling network. Any
average taken over a window shorter than about 500 ns is suspect, and that includes
short-run averages elsewhere in this repository, which are being revisited.

This is the second time the same error has been made here. The comparator's kickback
figure was first published as 0.63 mV from a `FIND` at 250 ps in a run that began at
100 ps — see [`../../comparator/run/kickback-clocked-vs-frozen/`](../../comparator/run/kickback-clocked-vs-frozen/),
which records that correction. The lesson was written down and then not applied to a
larger claim one step later.

## What remains true, and what is open again

Still true: the comparator resolves both polarities and is not implicated; the chain
converges once the noise source is band-limited; the amplifier meets its bandwidth and
power bounds.

Open again: **the counted bitstream came back all zeros and there is no longer an
explanation for it.** The gate returns from *fail* to *running*. Removing a wrong
explanation is not progress toward a right one, and the honest state is that the cause
of the pinned bit is unknown — with the added constraint that any re-measurement must
run several hundred nanoseconds before its averages mean anything.

## Reproducing

```
ngspice -b walk_hi.cir        # stage walk, sigma, 20 ns  (short window: shows +31.9 mV)
ngspice -b walk_lo.cir        # stage walk, sigma/10, 20 ns
ngspice -b walk_long2.cir     # 400 ns, windowed averages: the decay
```

The decks named in the withdrawn sections are retained — `chain_*.cir`, `aa_*.cir` and
their logs — because they are the evidence for the retraction as much as they were for
the claim. They are correct runs of the wrong window.
