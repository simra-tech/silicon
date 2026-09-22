# Nominal integrated hard-trip anchor

The compact `c_mid` fixture completed its full 28 µs endpoint and passed all
14 saved-vector acceptance checks. This run contains actual BGR, SENSE, TRIP
and GATE block capacitance extraction and actual control RTL. Its oscillator
is ideal, output pads are fitted behavioral models, and the external switch
and load are behavioral. It does not qualify a real cutoff FET or assembled
wire resistance, fill coupling, mismatch, or alternate power sequences.

Evidence directory: [`stream_20260921T220244Z_879e85e2`](stream_20260921T220244Z_879e85e2).
The run manifest identifies tool/image, pinned models, RTL and source-deck
hashes. `assessment.json` records numerical completion; the separate
`electrical_acceptance.json` records electrical checks and observation hash.
The earlier owner-interrupted compact runs remain incomplete evidence.

| Simulated quantity / check | Result |
|---|---|
| Endpoint / wall runtime | 28 µs / 2315.13 s |
| Requested fault | 1.8 A modeled profile, 45 mV shunt, starts16 µs |
| Programmed soft / hard codes | 153 / 200, checked before fault |
| Before fault | GATE enabled, inrush inactive, no digital trip |
| GATE below1 V, remains low | 1.4034586 µs after fault; passed<10 µs target |
| Final state | Analog and digital latches set, hard cause, FAULT_N low |
| Final modeled load current | 3.71 nA; below1% of1 A nominal |

Re-evaluate a copied run directory using:

```sh
python3 designs/g1-guardian/blocks/g1_top/sim/check_stream.py \
 designs/g1-guardian/blocks/g1_top/sim/campaigns/stream_20260921T220244Z_879e85e2
```

The checker refuses to overwrite an existing acceptance artifact. Its
source-hash contract identifies the exact fixture, and it requires complete
finite saved observations and verified input/output hashes. A partial trace
does not pass this check and cannot restore analog or RTL simulator state.

The baseline fixture with serial writes at18 µs and fault at30 µs is still
running under `stream_20260921T222734Z_4153bbdc`. Compact-preamble equivalence
is **not run** until that endpoint completes and the predeclared settled-state
comparison is evaluated. Full functional coverage, serial counter readback,
numerical refinement and PVT qualification remain incomplete.

The completed waveform's scoped [block-supply audit](../../../../review/audits/INTEGRATED_SUPPLY_20260922.md) reports nominal idle, gate-on, and tripped currents. Named-block rail power is about 3.463 mW before the fault; omitted real oscillator, RTL, input-driver and output-pad power prevent a whole-chip power claim.
