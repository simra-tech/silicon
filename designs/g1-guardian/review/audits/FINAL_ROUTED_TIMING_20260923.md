# Final signal-routing RCX and expanded digital timing

Stock signal-routing extraction and independent SPEF graph checks **passed**.
Complete integrated timing acceptance is **not established**. Two distinct
parasitic-import problems were found and retained. The corrected import passed
the three-corner source/report coverage audit; physical-scope omissions and
existing slew/fanout violations remain unresolved.

## Built against

| Item | Identity established by the recorded runtime |
|---|---|
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, runtime COMMIT file |
| OpenROAD | `26Q1-1024-gdcf36133a`, executable version |
| OpenSTA | `3.1.0`, executable version |
| Runtime image | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |
| Detailed routing OpenDB | `88143d849e5c599423c04e4824c14463b53a08d997aa50d9ea6e6441c811e8d7` |
| Routing DEF | `348dba8bc4db2f4aeefb9233f7aa5fb60512e7132963628dce7df5a0bfb2b612` |
| Stock RCX rules | `ffda02d57a6ecb39b02268be9511d89ef072911f17bd2dcd095f3f3cbeb5a905` |

The unchanged digital macro uses its run7 gate netlist and nominal SPEF.
Per-corner standard-cell and pad libraries, the existing two SDC files,
executables and all input views have individual hashes in each run manifest.
No library, rule deck, model card, clock uncertainty or acceptance criterion
was edited.

## Extraction

`run_final_routed_rcx.py` completed in 10.416 wrapper seconds, 1.033 extractor
seconds. The full functional OpenDB instance/net observations were unchanged.
The resulting SPEF is
`ceb5651e41c4dfc3ede324dd10febcbe53ddf3809c3db20aebbea0234cfd638d`;
the nonpowered netlist is
`337db3b1e5bc4686b421c185e25cc6bcd44327bc6b8eb0411a16a2f764e533c4`.

The independent audit checks all 57 routed nets against exact DEF endpoints,
connected positive-resistance graphs, 290 reciprocal coupling pairs and
printed capacitance totals with decimal-rounding intervals. Thirteen parser
and failure-injection controls pass. An initial coupling-order assumption and
an aliased synthetic fixture failed; both original failures are retained.

The pinned extractor grounds coupling below 0.1 fF. Its default via merging
and LEF resistance setting were retained. This is the **signal-routing DB**,
not extraction of final fill, all native terminal metal, power routing or
subsequently moved bond pads. Sum of resistor edges is not effective resistance.

## Timing-import failures and recovery

1. Inferred analog black boxes did not supply the TRIP/OSC vector declarations;
   40 SPEF connection warnings resulted. Declaration-only stubs derived from
   the held LEFs removed those warnings. Seven parser controls pass. These
   declarations add no analog functionality, timing arcs or input capacitance.
2. Repeating `read_spef -corner CURRENT` produced 110 unannotated and 11
   partially annotated drivers. Reversing the read order produced 4,856
   unannotated drivers and different timing. Positive slack in either run is
   not proof that both parasitic views were loaded.
3. Reading the top view into `CURRENT`, then using `-name CURRENT` for the
   hierarchical macro read, gave 101 unannotated and **zero partially
   annotated drivers** in all three corners. The remaining 101 comprise 56
   unused CTS load-cell outputs, 17 external ports and 28 pad pins; their
   physical/functional disposition is not a blanket annotation waiver.
4. A further boundary-capacitance check found that default coupling grounding
   loaded about 0.05806828 pF on SDO, versus the two input SPEF totals summing
   to 0.05817966 pF. The difference closely tracks the macro's 0.000111372 pF
   coupling on its hierarchical SDO port. The source-held fast-corner test
   with `-keep_capacitive_coupling`, unchanged reduction factor 1, reported
   0.058179643–0.058179650 pF and retained zero partial drivers. This is a
   numerical observation, not a newly allocated capacitance tolerance.

The named-set and coupling investigations were guided by the upstream
[OpenSTA read implementation](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/search/Sta.cc)
and [SPEF reader](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/parasitics/SpefReader.cc).
Those moving upstream sources are hypotheses, not a claim that their bytes
equal the pinned executable's source. The recorded pinned-runtime controls
provide the actual evidence above.

| Check | Status | Result |
|---|---|---|
| Original repeated-corner import completeness | Failed | Missing top/macro annotation retained |
| LEF declaration recovery | Passed | No bus-pin import warnings |
| Shared-set clock coverage | Passed | 52 SCLK and 1,148 oscillator registers in every corner |
| Shared-set default-grounding boundary conservation | Failed | SDO discrepancy retained |
| Shared-set retained-coupling fast execution | Passed | 9.488 s; hold +0.106013673 ns, setup +28.006294965 ns |
| Retained-coupling three-corner source/report coverage audit | Passed | All 57 positive wire-C reports per corner; original 1,200 registers; zero partial drivers |
| Full physical parasitic annotation | Failed | 101 unannotated drivers retained, not waived |
| Existing reported max slew/fanout constraints | Failed | Analog pad transitions and CTS fanout violations retained |
| Analog/physical clock and load bounds | Not run | Existing SDC assumptions only |
| Final filled/moved-pad full-chip timing qualification | Not run | Native/pad/power parasitics and analog response incomplete |
| Stochastic seed | Not applicable | Deterministic extraction and STA |

All numerical timing results are simulated. The SDC continues to use 100 ns
clocks, 0.5 ns setup and 0.05 ns hold uncertainty, the existing asynchronous
exceptions and existing external delays/loads. Three unconstrained digital D
pins are the first synchronizer stages fed by `cmp_soft`, `cmp_hard` and
`tripped`; the other reported unconstrained endpoints are external ports.
Their source mapping does not establish metastability MTBF, asynchronous
analog timing, board loading or physical clock bounds. No full V19 or tapeout
sign-off claim follows from these scoped checks.

The final all-net runs took 10.129/9.843/10.424 wrapper seconds for fast,
typical and slow libraries. Simulated hold/setup slacks were respectively
+0.106013673/+28.006294965 ns, +0.185126419/+27.277491260 ns and
+0.326143732/+25.751415951 ns. Seven import-selector controls and five
independent report-parser controls passed. The independent three-corner
coverage audit took 8.476 wrapper seconds. Across all 57 nets, the largest
absolute difference between reported wire capacitance and the sum of printed
top/macro SPEF totals was 0.000000467 pF in each corner. This is a descriptive
cross-check, not a new numerical acceptance tolerance or physical RC accuracy
claim. The full per-net differences and source hashes are retained in
`final-routed-timing-evidence-20260923-r1`.
