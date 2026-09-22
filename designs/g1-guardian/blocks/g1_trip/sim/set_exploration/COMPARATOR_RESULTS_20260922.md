# Exploratory comparator charge injection

Simulated with ngspice46 / IHP SG13G2
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`. Existing revision1 comparator
CPEX source SHA256
`2b655dfb3780eb43f55bf2641c93ea58e150c08e4691343e5e5a796ebc32fe2d`
retains30MOS and109capacitors. This inherits that source's per-finger/native
model convention, not a new junction-equivalence qualification. All120
W/L/DELVTO/FACTUO observations match before/after and across24 transients at
seed62001. Canonical source/model cards are unchanged.

The fixture uses1.2V,25°C,0.75V common mode,±10mV differential, equal1kΩ/1pF
input networks,10fF per output,10MHz clock and720ns duration with20ps maximum
step. A current trapezoid has10ps edges and990ps plateau; its integrated area
is amplitude×1ns. Positive polarity injects current from ground into a node.
These electrical inputs are **not particle LET, physical collected-charge
predictions, upset rates, or radiation qualification**.

Two12-transient pilots include zero-charge controls for both differential
signs and polarities. First:±1pC into output nodes q/qb at250ns. Second:±100fC
into regeneration nodes n4/n10 at220.3ns, shortly after the220ns clock edge.
Zero-charge waveforms match byte-for-byte across polarities within each pilot.
Integrated saved source-current charge matches the declared trapezoid area.

| Check | Status | Result |
| --- | --- | --- |
| 24 numerical transients / full120parameter freeze | passed | Complete finite saved waves; source/hash audit |
| Zero-charge controls / injected-charge area | passed | Exact control waves; measured simulated source integral |
| Any wrong comparator logic after pulse | failed no-glitch screen | Three cases described below |
| Held decision at280ns | failed retention screen | Two regeneration cases hold the wrong decision |
| Next decision340ns and later440/540/640ns | passed recovery characterization | All24 recover required logic |
| Reliability/model validity during excursions | not run | Observed internal nodes−0.808V to1.963V |
| Actual digital feedback / loaded full-chain response | not run | Standalone comparator only |
| Physical radiation measurement | not applicable | Simulation campaign, no physical samples |

The negative1pC pulse at q with+10mV differential briefly forces the output
below0.6V from sampled250.037 to251.131ns, then recovers before280ns. With
−10mV differential, negative100fC at n10 and positive100fC at n4 each produce
a false high: first observed about220.725/220.746ns and still high immediately
before the320ns clock. Both are high at240/280ns and low again at340ns.
The first/last sample span is not an interpolated exact glitch width.
Recovery does not erase these hazards, and out-of-rail voltages preclude a
fault-survival inference. No critical charge or physical susceptibility is
extracted from these two coarse stimuli.

See [independent saved-wave audit](comparator-pilot-audit-20260922.json) for
per-case hashes, all sampled decisions, extrema and wrong-logic observations.
Bulk decks/waves/logs remain outside Git. Reproduce inside the pinned runtime
with one allocated CPU and a fresh mounted output for each sign:

```sh
python3 designs/g1-guardian/blocks/g1_trip/sim/set_exploration/run_comparator_pilot.py --polarity "$SIGN" --output "$FRESH_OUTPUT"
python3 designs/g1-guardian/blocks/g1_trip/sim/set_exploration/run_comparator_pilot.py --polarity "$SIGN" --phase 220.3 --nodes n4,n10 --charge-fc 100 --output "$FRESH_REGEN_OUTPUT"
```

SIGN is−1 or1. Original outputs are`cmp-set-sink/inject-20260922-r1` and
`cmp-set-regen-sink/inject-20260922-r1`. Wrapper times were79.903/80.179s and
80.124/79.879s respectively; each individual simulator has a120s watchdog.
Pulse shape/PVT refinement, reference-bias injection and fullchain fault
propagation are separate required work; this does not close all V20 gates.
