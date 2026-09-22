# DOSE mismatch harness — paused after qualification

The five-leaf harness qualification **passed**. The requested 100-sample
nominal characterization and selected hot sample anchors are **not run**:
the owner explicitly paused immediately after qualification completed.
No simulation jobs remain.

`run_mismatch.py` consumes unchanged flat C-PEX
`reports/flat-pex-20260921T150428Z_7652097b/ngspice_pex.spice` and the existing
detailed AnalogPad/route-R fixture
`macro_20260921T153804Z_b4ddcb86/tt_27_1.2_3.3.cir`. Local copied netlists add
`mm_ok=1` only to the two coupon devices; controls use0. The installed MOS
mismatch model defaults remain0, and stock IO sources contain no enabling
`mm_ok` declaration. No model card, PDK deck, source layout or pad library is
modified. PDK commit84374023ee8b4b126bebbba67fcbada0a9c0ff0b, ngspice46,
pinned image/model/source hashes are in
[mismatch_qual_20260921_r1/provenance.json](mismatch_qual_20260921_r1/provenance.json).

[Qualification](mismatch_qual_20260921_r1/qualification.json) checks:

- Seed55001 repeated in separate processes: identical fingerprints and waves.
- Seed55002 changes each coupon's realized mismatch and observable currents.
- Mismatch-disabled55001/55002: identical fingerprints and currents.
- All four realized parameters (w,l,delvto,factuo) for each coupon plus all nine
  pad MOS devices:44 values retained before/after each DC sweep, frozen through
  27→125→27 C; returning to27 C reproduces currents exactly.
- All36 pad parameters unchanged across seeds/enabled/disabled cases; pad
  delvto=0 and factuo=1. Coupon disabledW/L are3.98um/0.13um and3.98um/0.45um,
  with delvto=0 and factuo=1. Pad PMOSW/L133.2um/0.6um and NMOS88um/0.6um
  match the unchanged library instance values.
- Each leaf completes three151-point gate sweeps from−0.3 to1.2V, drain sources
  held1.2V, rails1.2/3.3V, unchanged detailed pads and routeR/C assumptions.

At gate0 and27 C, enabled seed55001 has intrinsic HV terminal current
0.125194pA and LV165.655pA, versus external drain-source currents262.999pA
and428.529pA. Seed55002 gives HV0.143131pA and LV181.275pA. These two samples
only demonstrate active mismatch; they do not characterize a distribution.
“Intrinsic” here means measured at the coupon drain probe after pad/route,
including transistor terminal leakage, not isolated channel-only current.

The HV off-current is much smaller than pad contribution, so its external
observability is limited. At125 C the modeled pad contribution can reverse
sign (about−3.50nA), and external current must retain that sign instead of
being silently interpreted as coupon leakage. No physical leakage floor,
radiation calibration, dose response, packaged measurement model or allocated
acceptance tolerance is established by this harness.

After explicit owner resume, the nominal100 seeds55101–55200 can run with:

```sh
G1_CPUS=2 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/blocks/g1_dose/sim/qualification/run_mismatch.py --run-id mismatch_nominal100_20260921_r1 --mode nominal --qualification designs/g1-guardian/blocks/g1_dose/sim/qualification/mismatch_qual_20260921_r1/qualification.json
```

Select low/high and central observable-LV samples from that retained manifest,
plus HV extremes if distinct, before running `--mode hot --seeds <list>` with
the same qualification path and a fresh run-id. Compare first27C fingerprints
and waves to the corresponding nominal leaves; identical seed alone is not
proof of the same physical draw if source/order/library changes. A summary
analyzer and final100-sample report remain **not run/not written** at pause.

## Resumed result — 2026-09-22

The owner resumed execution. [The completed characterization](MISMATCH_20260922.md)
now records100/100 nominal samples and5/5 selected hot anchors. The paused state
above remains historical evidence, not the current campaign status.
