# Loaded reference/bias observation — simulated

Both output-only replays passed: all original13 waveform columns match the
complete decoded archived bytes and numeric rows exactly, and all27 observed
parameters remain exact. Room/hot runs completed in182.018/190.767 seconds;
there are6626/6499 rows including headers. The original 5 MHz hot HIGH/HIGH
and 10 MHz hot LOW/HIGH decisions are unchanged, not waived.

Only saved/output vectors and a tagged quiet operating-point print were added
to the previously qualified room/hot5 MHz fixtures. Sources, body connections,
cards, seed71002, codes136/154, 24.5 mV shunt, clocks, solver and tolerances
did not change. Added outputs are VREF, IPTAT pin voltage, VREF_BUF, VPED and
SHP, following the retained original13 columns. IPTAT voltage is not current.

## Observed temperature motion

At quiet OP, hot125°C minus room25°C is VREF−11.631 mV,
VREF_BUF−11.335 mV, VPED−11.661 mV, ISENSE−8.524 mV, ICMP−4.263 mV,
softDAC−8.363 mV and hardDAC−8.749 mV. Thus soft/hard differential inputs
move by+4.100/+4.486 mV. At the last actual evaluation edge+20 ns, their
respective soft/hard differential motions are+6.501/+7.070 mV.

The following algebraic terms reconstruct the hard differential motion;
units are mV, hot minus room. They are descriptive bins, not isolated causes.

| Term | Quiet OP | Last hard actual edge+20 ns |
|---|---:|---:|
| Reference under nominal ratios | +3.379645 | +3.380321 |
| Buffer tracking residual | −0.086183 | −0.085100 |
| Pedestal residual | −0.377277 | −0.377766 |
| Shunt nominal contribution | 0 | 0 |
| SENSE gain/pedestal residual | +1.568633 | +1.572933 |
| Conditioning residual | −0.001143 | +0.060549 |
| DAC ratio/loading residual | +0.002559 | +2.518969 |
| Sum: differential motion | +4.486235 | +7.069906 |

For code `c`, let `r=VREF`, `b=VREF_BUF`, `p=VPED`, `s=SHP`,
`y=ISENSE`, `i=ICMP`, and `t=VTH`. The exact identity used is:

```text
i−t = −c*r/530 − c*(b−r)/530 + (p−51*b/53)/2
      + 10*s + (y−p−20*s)/2 + (i−y/2) − (t−(255+c)*b/530)
```

Nominal ratios come from the retained source:51/53 pedestal divider,
gain20, half-scale conditioning, and530-unit DAC with code0 at unit255.
The residual terms retain all deviations from those nominal ratios. They do
not fit new calibration, infer independent block sensitivity, or establish
comparator correctness from static input sign. Dynamic feedback/loading can
appear in several bins.

Quiet OP and cycles2/3/4 at actual clock-edge offsets−1,0,0.2,0.5,1,20 ns
are reported. Waveform samples are linearly interpolated between retained rows;
each bracket, fraction and width is explicit. Largest bracket is approximately
0.2 ns; largest individual identity reconstruction error is1.11e−16 V.
Room/hot comparisons use matching actual clock phases, not assumed inverter
delay or identical absolute timestamps.

## Reproduction and scope

From `blocks/g1_trip/sim`, prepare with `prepare_bias_observation_probe.py`
using the corresponding `joint-gm4comp3-s71002-5mhz-room/hot-20260922-a`
reference; execute `run_bias_observation_probe.py --run-id <fresh-id>
--image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
--timeout-s 600` through the pinned flow. Fresh IDs are
`joint-gm4comp3-s71002-bias-observation-room-20260922-a` and the corresponding
`...-hot-...` run. Tool/PDK/source identities remain in portable provenance.
Run `analyze_bias_observation.py --runs <room-id> <hot-id> --output <fresh-json>`.

The [full decomposition](resume-server-20260922/joint-gm4comp3-71002-bias-observation-decomposition.json)
and both `resume-server-20260922/portable-runs/` exports retain summaries,
preparation, literal output differences, runner snapshots and artifact hashes.
Total retained new output is2,506,905 bytes.48 related regression tests passed.

Reference substitution, new BGR mismatch qualification, new calibration,
statistical joint expansion and causal block-isolation experiments are **not run**.
