# Native fullchip stock LVS: prospective bounded contract

This distinct verification attempt uses the source-audited current fullchip
reference, including original IO device/tap records, all 1,036 BGR source
primitives and the already documented SENSE primitive projection. Known
tap A/P failures are expected to remain visible. No comparison result is
predetermined or waived.

## Held inputs and authority

- Reference SHA256:
  `f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9`.
  This is the approved top-name-only view; circuit/library body bytes are held.
- Top: `placed_core_NOT_CONNECTED_FULLCHIP`; exact 22 source top pins.
- PDK: `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; KLayout 0.30.9.
- Native GDS: coordinator supplies the final assembled, routed and sealed
  candidate and its exact SHA256. Required candidate receipt has a passed
  preparation status and matching `GDS_sha256`. No input substitution is
  inferred from a similar filename or earlier run.
- Runtime: existing pinned image config
  `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
- One CPU1 process, initial 900-second stock bound plus 5-second process-group
  kill grace; saved-result analysis separately bounded at 120 seconds.
  Reservation: 16 GiB RAM, 2 GiB bulk output and 0.02 GiB home output.
  Rootless memory is not enforced. Fresh resource gate must satisfy the current
  coordinated allocation (43 CPUs at preparation); new allocations require
  reassessment, not blind reuse of this planning number.

The command uses the pinned unmodified stock `run_lvs.py` with native
`--layout`, unchanged `--netlist`, `--run_mode deep`, `--top_lvl_pins`, and
`--spice_comments`. It does not use layout-netlist input, net-only operation,
implicit nets, ignored ports, disabled taps, comparison hints, source-derived
parameter replacement, or rule/model edits. Stock default simplification
behavior is preserved and compared-device counts are reported, not equated
silently with unsimplified source instance counts.

## Required result interpretation

The run is passed only if all of the following pass:

1. Exact GDS/reference/candidate-receipt/runner/parser and stock rule hashes
   remain unchanged; actual process exits zero within its bound.
2. Exactly one actual engine log and one readable LVS database exist.
   The engine explicitly reports a match, not a mismatch or error. The stock
   wrapper summary is not accepted as a result by itself.
3. Engine log confirms native extraction, taps enabled, no implicit nets,
   no ignored ports, and strict missing-port checking.
4. Both saved sides contain the expected top and exact source top-pin set.
   Every circuit reachable from that top on either side has a comparison
   pair, and its device/net/pin/subcircuit side counts are fully covered.
5. Every reachable circuit and every contained device/net/pin/subcircuit
   pair is `Match`. `MatchWithWarning`, `Mismatch`, `NoMatch`, `Skipped`,
   missing objects, empty top, or missing coverage fails. Uninstantiated
   library definitions are recorded separately, not counted as chip devices;
   reachability on either side prevents dropping an unexpected unmatched
   reachable circuit.
6. Output growth remains within the declared bound. A timeout, missing
   report, parser exception, or ambiguous result is failed/incomplete,
   never promoted to passed.

The analyzer preserves all saved circuit inventories and full non-Match
device parameters/terminals plus net, pin and subcircuit identities. A stock
pass would not establish compact-model junction applicability, electrical
performance, physical PEX completeness, IR/EM, or adoption. Those are separate
gates. No source tailoring or automatic retry follows a failure.

## Parser controls already run

Eight saved-data controls passed; **no new stock engine run** was used:

| Saved or synthetic case | Disposition |
|---|---|
| Actual same-name and child-name-alias comparisons | Passed; four expanded MOS retained on each side |
| Actual deliberately wrong wire | Failed comparison correctly rejected |
| Actual top-name mismatch with wrapper `PASS` | Exit 1 / no LVSDB correctly rejected |
| Actual saved IO tap `MatchWithWarning` | Correctly rejected |
| Positive engine text with nonzero exit | Correctly rejected |
| Positive engine text with missing database | Correctly rejected |
| Conflicting match/mismatch signatures | Correctly rejected |

Exact parser SHA256 at those controls:
`51c6fc43b69a9e3aa03dfb2f77d1cb4ab09c1836e5464f5b421f1bc04e048b11`.
The original control engine failures and earlier wrapper false summary are
retained in the name-interface evidence. Native fullchip extraction and
comparison on the coordinator's final input are **not run** at contract
preparation. Stochastic seed is **not applicable**.

## Original/portable binding correction

The first physical run failed preflight before extraction: the harness used
the portable exported reference while asserting the original reference hash.
Original `f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9`
is retained under `G1_RESULTS_ROOT/fullchip-name-interface-20260923-r1`.
The committed portable reference hashes to
`8f5e7ad53a2caeb366855290f5f90eff9886e770d1b0ae04d7f6dda76e1a032a`.
Exactly one `** sch_path:` comment prefix was normalized. The corrected
harness verifies that exact byte differential and uses the original f4ce
reference. No circuit line, pin, device, library or deck is changed.
