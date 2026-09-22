# Native decap grid and supply integration

This is an intermediate physical verification record, not chip signoff or
electrical adoption. The revised core retains source-held BGR and SENSE cells,
4,662 native decaps and their actual VDD/VSS domains. SENSE uses **VDDA**, not
the core VDD ring. Full macro and pad supply connectivity remains unfinished.

## Built against

| Item | Exact identity / establishment |
|---|---|
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime COMMIT and stock-rule hashes |
| KLayout | 0.30.9; runtime API assertion |
| Final BGR native geometry | `6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04` |
| SENSE native geometry | `8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7` |
| Refreshed source core | `a001df1aec9d38d18bbf9649b0944f977eb40cb04a5a23f2f49be4f79d2476c5` |
| Execution | One assigned CPU per process; fresh resource gates, bounded commands, bulk results retained |
| Seed / ngspice result | Not applicable to these deterministic geometric checks |

## Completed stages and retained failures

The read-only planner progressed from 255 to 386, 415, 456 and finally all
464 supply components reachable. Its first 300-second timeout is retained.
Reachability alone is not a physical-connectivity or DRC result.

The first constructed grid used 16 TopMetal1 spine segments, M2 feeders and
eight M5 flyovers, with redundant via arrays. All 9,324 native M1/M2 pin pairs
connected to their intended rings, with no foreign native-net contact and
exact additive geometry/text/saved-roundtrip checks. Its stock main DRC
**failed 269 markers**: 264 TopVia2 spacing markers from overlapping new and
native corner lattices, two TopMetal1 notches, two M2 spacing markers and one
M2-filler spacing marker. Connectivity did not excuse those failures.

The next revision preserves the full native side-ring widths, avoids adding
another via lattice where the spine already contacts a proved native ring,
and includes retained datatype-22 filler in route-clearance screening.
Two additional M5 flyovers avoid the filler. Its core GDS is
`b50a26670086a05cd751b4c56abffde7c0416345a30da90bcc96e31223ed947e`.

| Revision-r2 check | Status | Result |
|---|---|---|
| Exact source/native geometry, texts and saved roundtrip | Passed | Only declared additive routes/cuts |
| Foreign native-net contacts | Passed | Seven drawing metals and six cut layers; no text-based joins |
| Native decap pin pairs to correct core ring | Passed | 9,324 pairs, all 464 original components |
| Stock main DRC | Passed | Zero markers, 118.513 s |
| Stock maximal DRC | Passed | Zero markers, 304.121 s |
| Full native IO/glue assembly | Passed | 4,904 instances held, 178.500 s |
| SENSE supply overlay combined with this grid | Failed | VDDA bridge intersects a new core-VDD feeder landing |
| Full macro/pad PDN, current sharing, IR and EM | Not run | Not established by decap continuity |

The failed combined SENSE gate is an actual new-context conflict, not a
failure of its separately recorded isolated-overlay checks. The VDDA M3
bridge near y=395 µm contacted the VDD side-spine landing near
(1061.52,395.42) µm and adjacent cut/metal paths. The merge stopped before
adoption. The source-held SENSE overlay itself is unchanged.

The planner now reserves the exact frozen SENSE M2–M5 conductor corridors.
Only two feeder plans change: one VSS landing moves to another VSS spine,
and one VDD feeder uses an M5 flyover to another VDD spine. The resulting
core GDS is `88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb`;
its additive overlay is
`c5a58179c263cfd3528196310832f0480f3226092731a6e30a56031552fb7a01`.
Native contact, 9,324 pin-pair connectivity and exact saved geometry passed
in 66.267 s. Stock main and maximal checks both passed with zero markers
(446.864 s combined launcher). Exact full-native PDN refresh also passed
in 191.431 s while retaining all 4,904 instances. The combined SENSE merge
then passed in 253.297 s: VDDA reaches actual external pad07, VSS joins the
actual core-VSS ring, core VDD stays distinct, and all 9,324 decap pin pairs
remain connected correctly. Foreign-contact, exact additive geometry/text,
4,904 native instances and saved-roundtrip gates passed. Result GDS SHA256:
`4e9f6248652e15b43ff250337e33f9813fdc9761dd3bf3f3b6e3789fc20ea5cc`.
Combined stock checks and other macro feeds are not yet complete.
A preceding invocation
failed before runtime launch because of an invalid results-directory argument;
the failure and corrected invocation are retained separately.

## Other integration evidence

The routed pre-PDN native assembly retains 60 failed Pad.fR main-deck markers
and four failed Pad.d1R maximal-deck markers. Recommended rules remain release
gates. No bond-pad coordinate change or rule waiver is adopted here.

Actual metal-backed signal probing covers 10,222 instance terminals and
90 logical nets with zero off-metal probes and zero signal-net splits.
Eight raw physical net merges initially failed the generic no-merge check.
An independent audit of the unchanged `sg13g2_IOPadAnalog` Verilog proves those
eight pad/padbare aliases; no unexpected merge remains in that scoped audit.
External BTerms, full power connectivity and strict full-chip LVS are separate
unfinished checks. Alias proof is not an LVS substitution.

Routing obstacles are decomposed into exact orthogonal rectangles, rather than
bounding an entire connected grid by one large box. The first PDN/SENSE export
contains 1,644 rectangles with zero geometry XOR and no omitted conductor.
Signal routing must use the final power geometry; an older signal-route pass
does not establish clearance from new supplies.

The isolated 1,414 µm seal ring has actual die area 1.999396 mm². Its unchanged
driver's native 900-to-1000 µm PCell stretch control passes polygon XOR on all
20 layers. Literal text equality **fails** for the PCell's parameter-dependent
registration-size annotation; all other text matches. The native base-size
annotation is retained verbatim, not used as the final die-size measurement.
The first CLI invocation lacked the registered PCell library; explicit stock
library bootstrap resolved that setup failure. The isolated ring passed
unchanged stock main and maximal DRC with zero markers in 6.906 and 3.883 s
(20.551 s launcher). Earlier invalid-watchdog and wrong-topcell invocations
failed and are retained; the corrected wrapper explicitly validates the
requested topcell in the hash-bound GDS. Combined placement remains not run.

## Remaining qualification

Full macro/pad feeds, final routing, density/fill, antenna, strict IO-inclusive
LVS, full parasitic field/model composition, current/IR/EM and affected
electrical/statistical checks remain failed or not run in their own records.
Neither local stock-rule passes nor lower fixed-current metal drops establish
those results. No PDK rule deck, compact-model card, acceptance threshold or
canonical electrical source was changed by this work.
