# IO tap reference-binding diagnosis

The four Corner/Filler circuits reported as missing on the reference side of the previous full IO comparison are **present in the exact source CDL**. A new read-only audit of that source and its preserved LVSDB establishes a more precise distinction: their tap definitions disappear before the final comparison. This corrects the earlier description that their intended reference views were absent from the stock CDL.

The exact source contains four Corner, 28 Filler2000, 36 Filler400 and 28 Filler4000 instances, plus definitions for all four cells. Each definition contains two `XR... ptap1` statements with A/P parameters. The final reference netlist in the saved LVSDB has no `ptap1` or `ntap1` device class and none of those four circuits. `LevelUpInv` retains eight MOS devices and loses its single reference tap; `RCClampInverter` retains three combined MOS devices and loses its tap. Their cross-reference records each show one additional extracted device. Source and database hashes and exact source tap statements are retained in [the audit](io-tap-binding-source-audit-20260922-r1.json).

The unchanged stock-reader probe now confirms the binding cause. Its custom element handler supports `M/C/R/Q/L/D`; it does not convert `X` subcircuit instances into tap devices. The `ptap1 → R` prefix map is used by the writer, not by this reader. The source has no `.SUBCKT ptap1` definition. Original `XR` statements become empty parameterized subcircuits such as `PTAP1(A=0.680625P,P=3.3U)` and simplification removes them. The entire Filler400 reference disappears. This was observed directly under the pinned runtime, independently of layout extraction.

An isolated source-derived syntax candidate changes only the 63 tap instance identifiers in 41 cells from `X...` to an explicitly unique `R_G1_BIND_X...` prefix. Every node, model and A/P parameter suffix is verified byte-identical. The original source is preserved. Candidate SHA-256: `365166c1871a7fa44549bdae0fc740e29282bf86104b5736a8b076830529ad46`, at `build/scratch/io-tap-binding-20260922-r1/g1_chip_top_tap_syntax.cdl`. No extracted device values are used as a reference and no PDK deck or model is edited.

This syntax change does **not** resolve or hide the earlier physical tap-area/perimeter discrepancies, multiple disconnected same-name rails, or missing PolyRes recognition. Those remain separate comparison failures. In particular, the stock A/P values retain their original electrical-model meaning; they have not been replaced with extracted values. A full-chip rerun is not justified until the smallest stock-reader test and focused cell comparison establish what this change actually fixes.

The normalized references retain two real tap devices in Filler400 and one each in LevelUpInv and RCClampInverter, before and after simplification. [The independent checker](io-tap-binding-reader-check-20260922-r1.json) passed all four taps against the original source A/P values and TIE/WELL nodes, and confirmed non-tap device identities are preserved. The reader report and unchanged stock-file hashes are in `build/scratch/io-tap-binding-20260922-r1/stock_reader.json`.

The focused LevelUpInv layout comparisons completed and both **failed**: original 4.83584 s, normalized 3.73820 s. The original comparison has one unpaired layout tap. The normalized comparison pairs the tap with `MatchWithWarning` and retains two mismatched nets. Its extracted tap A/P is 1.053 µm² / 7.62 µm versus the unchanged source 1.051 µm² / 4.1 µm. The syntax repair fixes device binding; it does not establish a parameter or circuit pass. The existing concise cross-reference summary groups `MatchWithWarning` with matches, so its “unmatched devices 0” count must not be interpreted as parameter acceptance. Full evidence is under `io-tap-binding-lvs-levelup-20260922-r1/`; both wrapper return codes are zero despite explicit comparison failure.

The [detailed warning audit](io-tap-binding-lvs-levelup-20260922-r1/tap_warning_analysis.json) confirms that the normalized tap's TIE/WELL mapping respects the compared net pairs. Both mismatched nets are incident on the warned tap. Its A difference is +0.002 µm² and P difference +3.52 µm. This local topology evidence isolates the remaining parameter discrepancy; it does not establish full assembled connectivity or justify changing the reference values.

The [independent stock-GDS geometry audit](io-tap-levelup-geometry-20260922-r1.json) identifies the source/layout definition conflict without using extracted netlists as a reference. The unmodified stock LevelUpInv tap is one 3.51 × 0.30 µm active rectangle: area 1.053 µm² and actual perimeter 7.62 µm. Its source perimeter 4.1 µm is instead nearly the equivalent-square perimeter `4*sqrt(1.051) = 4.100732` µm. RCClampInverter similarly uses source A/P 68.973 µm² / 33.22 µm (`4*sqrt(A) = 33.219994` µm) for a physical guard shape with area 69.122 µm² and perimeter 406.6 µm. Thus this discrepancy exists in the stock cell views, not only after G1 placement or routing.

The [stock semantic audit](io-tap-levelup-semantics-20260922-r1/summary.json) independently checks that the source A/P reproduces the stock SPICE tap resistance through the public `CbTapCalc` equation: LevelUpInv 190.254 Ω versus stock 190.268 Ω; RCClampInverter 9.58970 Ω versus stock 9.59 Ω. Substituting physical shape A/P would yield different conditional estimates (112.994 Ω and 2.06003 Ω). The applicability of that equation to arbitrary guard shapes is not validated here. These are conflicting view semantics, not permission to fit the reference to extraction; all original parameters remain unchanged. A stock-deck-clean IO-LVS closure remains **failed**, and physically justified view reconciliation is unresolved.

## Separable physical rail-connectivity check

The earlier flat AnalogIO comparison had two separate physical IOVDD rail groups (`cathode,iovdd` and `iovdd,plus`), even with a global substrate declaration and diagnostic PolyRes marker. A new metal/via-only audit probes existing IOVDD text coordinates without importing labels into connectivity or adding virtual joins. Ten metal-backed coordinates on M3/M4/M5/TM1/TM2 identify two distinct standalone clusters. In each of the 11 placed analog pads, all ten coordinates map to the same assembled physical cluster; all 110 valid probes share `g1_chip_top` cluster 3. Thus the sampled standalone rail split is physically joined in the actual ring. This does not resolve tap parameters, missing resistor recognition, or all device-terminal connectivity.

One additional M1 text coordinate, local (62.645,1.98) µm, is off metal in both standalone and placed views. All 11 null results are retained in the [raw audit](io-rail-assembly-20260922-r1.json); its broad “all probes present” check is false. The [separate analysis](io-rail-assembly-analysis-20260922-r1.json) reports only the ten metal-backed probes per pad as the narrower rail-joining pass. Resolution of that off-metal text location is **not run**, and full IO-inclusive LVS remains **failed**.

| Check | Status |
|---|---|
| Source/CDL versus saved comparison-netlist audit | passed; binding discrepancy found |
| Syntax-only normalization and exact suffix preservation | passed |
| Unchanged stock-reader original/normalized probe and source A/P/node checks | passed; binding repair established |
| Focused LevelUpInv original and normalized reference LVS | failed; binding repaired, parameter warning and two net mismatches retained |
| Full IO-inclusive LVS after normalization | not run; historical full comparison remains failed |

Reproduce source audit and normalization with fresh outputs:

```sh
python3 designs/g1-guardian/review/audits/audit_io_tap_binding.py --output designs/g1-guardian/review/audits/io-tap-binding-source-audit-NEW.json
python3 designs/g1-guardian/review/audits/prepare_io_tap_reference.py --output build/scratch/io-tap-binding-NEW
```
