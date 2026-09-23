# Digital clock-tree fanout remedy — candidate only

The placed CTS candidate meets the integrated fanout limit of eight without
changing RTL, source timing limits, package pins, or library/model files.
It is **not an adopted macro**: routing, scoped macro timing and stock macro
DRC/antenna checks and an independent geometry-exact flat native LVS pass.
Full-chip integration and acceptance remain incomplete.

The downstream wrapper `run_digital_postcts.py` resumes the candidate at the
first post-CTS STA step using the original Classic configuration and step
substitutions. Old SDF and placement/timing metrics are deliberately removed
from the initial state; only source headers and lint/synthesis checks survive.
The new flow runs in a fresh bulk directory with one CPU and one flow worker.
Its first preparation attempt failed because `Config.get_meta` requires a
string, not a Path; no flow step ran. The corrected attempt uses the required
argument type. Downstream execution results and independent affected-view
checks must be recorded separately before adoption. The state-isolation unit
control passed, bringing the current helper controls to 12.

## Follow-through and naming correction

The corrected downstream launch completed detailed routing, with actual
`DRT_THREADS=1`, zero routing violations and zero antenna violations.
Post-global-route repair retains maximum clock-buffer fanout eight.
The first post-route STA attempt failed because the default newer executable
has a scene-API incompatibility with the installed flow; its result is retained.

Independent Yosys loading found that the original two-buffer insertion gave
each new instance the same identifier as its output wire. OpenDB accepted
that naming, but Yosys rejected it. The original failed input and log remain
preserved. The CTS generator now appends `_cell` to those two instance names;
the wire names do not change. `rename_digital_clock_instances.py` proves the
existing netlist correction changes exactly those instance keys, holds all
masters and terminal connections, and restores the original bytes under the
inverse mapping. Four naming controls pass. The corresponding final routed,
filled OpenDB rename now passes whole-DEF inverse-byte equality and saved
OpenDB roundtrip equality, without any placement/routing command. Earlier
SWIG-wrapper equality and nonexistent `getId` API attempts failed and remain
preserved. The final canonical database is
`05568ddf0fd08151bc05f8f6003fe9c1ceb97b3d6c052366281133357f6668da`;
its DEF is `fc52dc7174a10fe590296a5e1a072cb1a84590baded2069ae76e918b9809706b`.

The post-global-route corrected netlist (`e24a65a8a1dd62810087a90308306910ab4e51d734592515bf54706cc46444b9`)
passes the independent mapped-netlist Boolean comparison against the original
run7 pre-CTS netlist: all **4,042 equivalence points proven**, zero unresolved,
33.027 s tool time. This uses unchanged typical-corner functional Liberty,
not black-box cell stubs, and Yosys `clk2fflogic` global-step semantics with
its documented negative asynchronous hold assumption. It is not a timing,
analog reset, metastability or post-route signoff proof.

Five backend controls pass: direct buffer equivalence, inverted-output
rejection, buffered-clock equivalence, changed-reset rejection and rejection
of an instantiated cell lacking a complete Liberty function. Two earlier
method controls failed and are retained: unused library clock-gating cells
without functions, then unsupported direct asynchronous-FF SAT modelling.
The qualified import may omit a whole unsupported **unused** cell; hierarchy
checking and zero-blackbox checks fail if such a cell is instantiated. No PDK
library bytes are changed. The method does not ignore unknown cells in SAT.

Evidence run IDs: `digital-equivalence-controls-20260923-r1` through `r3`,
`digital-postgrt-clock-names-20260923-r1`, and
`digital-equivalence-postgrt-20260923-r1` (original naming failure) / `r2`
(corrected Boolean proof). Final routed equivalence separately passes all
4,042 points in `digital-equivalence-final-20260923-r2`; the r1 incorrect
reference-path attempt failed before proof and is retained. Final DEF pins
remain exactly equal (46), and all 199 TMR stages / 597 flops satisfy the
existing 20 µm minimum-separation criterion. This geometry result is not a
radiation cross-section or multiple-upset immunity claim.

`run_digital_postroute.py` verifies the saved DB/NL/PNL rename proofs and starts
at RC extraction with matching pinned OpenROAD and OpenSTA 2.7.0 binaries.
It preserves proved geometry metrics, removes stale timing/power metrics,
and uses unchanged flow configuration, constraints and library files.
All three original macro timing corners pass setup/hold and slew/capacitance/
fanout limits. Worst setup slack is 28.487318 ns; worst hold slack is
0.104289 ns. `audit_digital_routed_sta.py` independently accounts for every
one of the 60 unannotated drivers as an actual disconnected dummy clock-load
output, with zero partially unannotated drivers. All 222 clock buffers have
at most eight attached loads. Six annotation controls pass, rejecting foreign,
duplicate, connected, wrong-pin and partially unannotated cases. Full-chip
timing integration and adoption remain **not run** for this new macro.

## Completed downstream physical checks and remaining strict LVS

`digital-postroute-20260923-r1` completed the original downstream flow in
547.164 s: RC extraction, three-corner timing, IR analysis, both streamouts,
zero XOR differences, zero Magic/KLayout DRC errors and zero Netgen LVS
differences. Final GDS SHA256 is
`1a66208253ceacd1033ae97a4f4e67051755dbd8e38254ac53c0a9f34fefe5bf`.
These are macro-scoped flow results, not full-chip adoption.

Independent unchanged stock main/maximal decks both produced zero markers
(81.22/179.33 s engine time), and stock antenna produced zero (29.639 s).
The first wrapper incorrectly expected two report databases instead of the
stock driver's merged database; that wrapper failure is retained. The first
saved-result audit checked a zero-count line in the wrong log and failed.
Corrected saved audit r2 passes with both completed engine logs and the actual
merged XML; neither DRC engine was rerun to repair reporting. The original
KLayout processes used default internal threading constrained to one CPU;
future wrapper invocations explicitly set one internal thread.

The independent source mapper accounts for all 7,771 powered-netlist instances
and all 60 source-disconnected clock-load outputs against the unchanged PDK
CDL. Top-level bus spelling restoration has an exact inverse-byte check.
The hierarchical stock KLayout engine reports Match, but the stronger inventory
audit **fails**: 29 source singleton clock-load output nets have no corresponding
parent-level extracted net, and the native inverter child omits its unused Y
port. No exception was introduced for those absent objects.

Original flat-mode stock comparison also **fails**: all 59,328 device and
29,765 net pairs report Match, but flattening promotes standard-cell internal
labels into 4,968 layout ports versus 46 source ports. Source SPICE case folding
is separately accounted for without changing GDS labels or connections.
A derived flat-input control retains every non-TEXT physical layer and all
48 original top-level TEXT records (46 distinct ports; both supplies labelled
on TM1 and TM2), removing only descendant TEXT records. Seven preparation
controls pass, including rejection of changed/removed metal and top labels.
The actual saved GDS validates zero physical XOR on all 29 source layers,
unchanged top TEXT and exact saved roundtrip. Three earlier preparation failures
are retained: 46-port versus 48-TEXT counting, text extents in a generic Region
iterator, and GDS omitting empty annotation layers on serialization. Explicit
physical-shape selection and comparison against empty for absent layers retain
the requirement to preserve every nonempty physical layer.

Stock strict LVS on this derived view **passes** in 80.187 s tool / 89.145 s
wrapper time: all 59,328 devices, 29,765 nets and 46 ports are paired Match,
each with a real object on both sides and full inventory coverage. All strict
stock extraction switches remain enabled. Derived GDS SHA256 is
`8f2f2ceb035f7bca33793ce613b4bdde515c6c4809aa5c4c277b465e7473dbbf`.
Run IDs are `digital-flat-view-20260923-r4` and
`digital-cleanflat-lvs-20260923-r1`. No source connection, rule deck or
acceptance criterion changed to waive either earlier failure. The original
hierarchical GDS remains the physical candidate; this exact derived view is an
independent LVS representation, not a replacement tape-out layout.

## Built against

- Pinned image: `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
- IHP PDK: `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, live COMMIT checked.
- Successful executable: OpenROAD `26Q1-1024-gdcf36133a`, the image's
  `openroad-librelane` binary. Each run records its executable SHA256.
- Stock LibreLane CTS Tcl and helper sources are hash-held. The saved run7
  pre-CTS OpenDB is `fb92d5d466f4d841324082476ef3bf6f88bbd1838ca6a8d23dab9c198a426876`.
- Original macro SDC is `c36bf03041045f951179e22970de05bcdcae2dd66374f175a9da8e91a2b84673`.

## Change and controls

`run_digital_cts_fanout.py` redirects output views to fresh directories and
reconstructs the installed flow's three timing-corner and layer/via-RC
environment from the saved configuration. The original inputs remain held.
The candidate sets `CTS_SINK_CLUSTERING_SIZE=8`; the option is documented in
the [OpenROAD CTS reference](https://openroad.readthedocs.io/en/latest/main/src/cts/README.html).
The actual pinned-runtime result, not that moving documentation, establishes
the observations below.

Smaller clusters removed the leaf violations but left one root driving 16
branches. The second candidate inserts exactly two `sg13g2_buf_16` cells:
each drives eight original root branches, and the original root drives these
two cells. All inserted cells are noninverting. Stock placement legalization,
power connections and placement parasitic estimation follow the insertion.
No clock frequency, uncertainty, load, or acceptance limit is relaxed.

| Check | Status | Result |
|---|---|---|
| First standalone launch | failed | Missing derived corner environment; synthesis not reached |
| PATH OpenROAD 26Q3 replay, two attempts | failed | Stock flow's scene-name/scene-object mismatch in `set_layer_rc`; exact stack retained |
| Explicit 26Q1 baseline | passed, scoped | 12.374 s tool; CTS netlist byte-identical to original run7 CTS, SHA `cf87ffb214b290f9d61f945f612c66b4e253695196cf02141a3bec810c429214` |
| Baseline integrated fanout | failed | Original violations retained |
| Cluster-eight candidate | failed fanout | 12.326 s tool; only root remains at 16 versus limit 8 |
| Cluster-eight plus two-buffer split | passed fanout | 13.379 s tool; 222 clock buffers, maximum attached-pin fanout 8, zero violations |
| Named device/terminal graph | passed | All 4,413 non-clock instances and terminal connections exact after contraction of proved noninverting CTS buffers |
| Dummy-load handling | passed, scoped | All 60 dummy outputs are unconnected; their input pins remain counted in physical fanout |
| Clock register counts | passed | 52 serial-clock and 1,148 oscillator-clock registers |
| Original DEF pin section | passed | All 46 pin declarations and geometries equal after whitespace normalization |
| Placed TMR separation | passed | All 199 stages / 597 flops; minimum 27.4 um, none below existing 20 um criterion |
| Harness and graph controls | passed | 11 tests, including wrong data connection, buffer cycle, inverter substitution and connected dummy output |
| Routed RCX and original three-corner macro STA | passed | Positive setup/hold slack, no slew/cap/fanout violations; all 60 unannotated drivers independently proved disconnected dummy outputs |
| Detailed route and route antenna | passed | Zero violations; exact geometry retained through canonical naming |
| Final routed Boolean and TMR/pins | passed, scoped | All 4,042 equivalence points; 46 pins exact; 199 stages meet 20 µm geometry criterion |
| Original downstream physical flow | passed, scoped | Magic/KLayout DRC, streamout XOR and Netgen macro LVS report zero errors |
| Independent stock main/maximal/antenna | passed | Zero markers; reporting failures retained and corrected from saved evidence |
| Independent strict native KLayout LVS | failed | Hierarchical open-output inventory and flat internal-label port mismatch retained |
| Geometry-exact flat-view strict native KLayout LVS | passed | 59,328 devices, 29,765 nets, 46 ports; complete two-sided inventory and unchanged stock rules |
| Full-chip density and affected integrated physical checks | not run | New macro not adopted; old full-chip results do not transfer automatically |
| Full-chip integration and adoption | not run | Current adopted views are unchanged |
| Statistical seed | not applicable | Deterministic implementation control |

The contraction proof is structural, not timing equivalence. Dummy loading
and new clock latency require actual routed checks. The unchanged logical
graph does not qualify jitter, metastability, power, or final chip timing.

Candidate hashes:

- Netlist: `f991e5af3fa1a5ad1b0178de8287c1dc4519269f1c645a9a914a2bad430f8ad7`.
- OpenDB: `24d4207bcdc507b114f9237d004872155d32756f888b1e23d0c63668cc961c6b`.
- DEF: `c49dd1b75bed7fba3eefc229fc7642887acf4ebffc92061e40371ce4c20bd140`.

Bulk run identities are `digital-cts-baseline-20260923-r1` through `r4`,
`digital-cts-cluster8-20260923-r1`, and `digital-cts-split-20260923-r1`.
They retain source snapshots, environment, commands, input hashes, tool logs,
views and scoped summaries. The graph auditor independently reads the saved
netlists. Original failures are not overwritten by later successful controls.

Reproduction uses the saved run7 pre-CTS inputs and a fresh result directory:

```sh
python3 designs/g1-guardian/review/audits/run_digital_cts_fanout.py \
  --openroad /foss/tools/openroad-librelane/bin/openroad \
  --cluster 8 --split-root --output "${RESULTS}/digital-cts-split-NEW"
```

Run inside the pinned image, with one allocated CPU and the repository at
`/work`. Use `--cluster 0` without `--split-root` for the source-held baseline.
