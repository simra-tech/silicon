# Saved native comparison: actual parent connectivity and physical ports

All four completed comparisons **failed strict matching**. They reuse the
unchanged native database from sealed GDS `3a24f4d7…`, rather than rerunning
physical extraction. Original deep extraction failed; the separate unchanged
native flat run reached its 900-second watchdog without a comparison database.
Neither a zero wrapper exit nor an engine pin-pair `Match` alone is acceptance.

| Saved comparison view | Wall seconds | Matched devices | Mismatched devices | Mismatched nets | Strict result |
|---|---:|---:|---:|---:|---|
| Original source, original promoted ports | 39.785 | 61,023 | 261 | 219 | Failed |
| Source-faithful tap syntax, original ports | 39.661 | 61,023 | 647 | 396 | Failed |
| Original source, physically derived 22 ports | 60.328 | 61,023 | 261 | 219 | Failed |
| Tap syntax, physically derived 22 ports | 58.618 | 61,023 | 647 | 396 | Failed |

The tap syntax correction makes exactly 386 existing reachable source taps
visible to the pinned reader. It changes no source nodes, model or A/P values;
the reverse transform reproduces the original source bytes. It exposes more
unmatched devices and is not a tap-parameter or substrate-topology repair.

Independent hierarchy traversal and real parent-pin unions prove that native
flattening preserves 61,516 primitive records, 245,160 terminal incidences and
30,929 distinct nodes. The comparison-class adapter copies 428,749 parameters
bit-for-bit into the unchanged installed reader's class constructors; it does
not use rounded SPICE output or replace extracted parameters with source values.
Stock simplification and parameter semantics remain in force. Positive and
wrong-wire/parameter/missing-port controls distinguish actual strict rejection.

The physical-port view maps all 24 audited pad rectangles to 22 distinct real
saved nets using exact TopMetal2 geometry XOR and geometry probes. Only the
tool-promoted port metadata changes. Every device, parameter, node and terminal
binding is identical before and after, including reverse restoration. All 22
logical pin names are present, but the original-source comparison still has
13 logical pins with null-sided pairings. Those are failures, even though the
engine labels the individual pin records `Match`. Device and net outcomes are
exactly invariant under the physical-port projection in both source arms.

The initial metadata implementation crashed because removing a circuit pin
without disconnecting it leaves stale reciprocal net-pin entries in this API.
The original SIG11, six earlier comparison-harness failures, reader failures,
flatten-audit failures and preflight failures remain retained. A seven-case
lifecycle experiment contains six expected-disposition passes and one actual
reproducer SIG11; disconnect-before-remove eliminates that reproducible stale
entry. This is a harness repair, not a circuit or rule change.

| Check | Status |
|---|---|
| Native hierarchy/terminal and binary64 preservation | Passed |
| Source-faithful tap reader/reverse transform | Passed |
| Physical 24-rectangle/22-node binding and metadata reversibility | Passed |
| Both source arms: strict device/net/pin comparison | Failed |
| Original native deep extraction comparison | Failed |
| Original native flat diagnostic | Failed, watchdog; comparison not run |
| New native extraction of the source-adapter/physical-port views | Not run |
| Substrate-global or resistor-marker repair adoption | Not run |
| Analog simulation, Monte Carlo seed | Not applicable |

Remaining mismatches must be resolved as physical/source defects or explicit
model-interface conflicts. They are not all attributable to IO by assumption:
the complete discrepancy ledger also includes core DUT and dose records.
No `.same_nets` hints, name-based electrical joins, model-card edits, rule edits,
parameter tolerances or extracted-netlist-as-golden reference are used.
