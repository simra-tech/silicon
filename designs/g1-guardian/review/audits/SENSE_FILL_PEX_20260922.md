# SENSE selective fill coupling pilot

The bounded KPEX 2.5D pilot **passed extraction and capacitor-network consistency checks** for one exact delivered-layout clip. Floating fill is represented electrically; its effect is not zero. Full-route extraction, clip-size convergence, actual global context connectivity, and circuit-level impact are **not run**. Production geometry is unchanged; this does not qualify LVS, DRC, or tapeout.

The source is `blocks/g1_padring/layout/g1_chip_top.gds`, SHA-256 `38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`. Coordinates `[1016,468,1028,488] µm` select a 12×20 µm box containing 20 µm of each parallel M4 SENSE_P/SENSE_N route. Native coordinates and 1 nm database units are retained. All seven metal drawing/fill layers and six via layers are clipped; active, poly, device layers, and conductors outside the box are omitted. The no-fill anchor removes only metal datatype22. Text labels identify each local conductor without adding conductive polygons. Every included nontext layer has zero polygon XOR against its corresponding source clip, recorded with counts, labels, areas, deck hashes and GDS hashes in [provenance](fill-clip-pilot-20260922-r1/provenance.json).

KLayout 0.30.9, KPEX 0.3.12 and ngspice46 ran in the pinned EDA image. The installed KPEX IHP deck explicitly joins metal drawing and filler layers (`layers_definitions.lvs`, e.g. metal4). No installed deck or model card was changed. This is an approximate 2.5D field model, not a 3D field-solver reference.

## Results

Values below are fF, derived only from the retained extracted capacitor graphs. P and N are external nodes. Substrate and the two clipped context conductors on TopMetal1/2 are assigned AC ground as an explicit boundary condition. “Grounded fill” grounds all extracted fill nodes; “floating fill” eliminates their voltages by zero incremental net charge (Schur complement), with no assumed leakage or DC tie. Neither condition establishes actual whole-chip connectivity.

| Exact clip / fill boundary | P equivalent to ground | N equivalent to ground | Effective P–N mutual | Balanced differential energy C | Common-mode energy C |
|---|---:|---:|---:|---:|---:|
| No fill | 1.103860 | 1.239216 | 3.487750 | 4.073519 | 2.343076 |
| Actual fill, grounded | 1.868217 | 2.052958 | 3.487750 | 4.468044 | 3.921175 |
| Actual fill, floating | 1.576940 | 1.718077 | 3.636670 | 4.460424 | 3.295017 |

“Equivalent to ground” is the reduced Maxwell-matrix row sum, so the mutual capacitor is separate. Differential energy C uses P=+0.5 V,N=−0.5 V; common-mode uses P=N=1 V. Floating fill increases this clip's effective mutual capacitance by 4.27% and differential energy C by 9.50% relative to no fill. These changes must not be applied as percentages to the entire route: other segments, context connectivity and omitted neighboring conductors differ.

The no-fill graph has 9 capacitors and 5 nets. The actual-fill graph has 375 capacitors, 61 nets including 56 distinct fill nets after extraction. Raw SPICE graphs are retained under [r4 no-fill](fill-clip-pex-20260922-r4/no_fill/kpex/clip__sense_fill_clip/sense_fill_clip_k25d_pex_netlist.spice) and [r4 actual-fill](fill-clip-pex-20260922-r4/actual_fill/kpex/clip__sense_fill_clip/sense_fill_clip_k25d_pex_netlist.spice). [Analysis](fill-clip-analysis-20260922-r1/summary.json) records graph hashes, full matrices, charge-conservation residuals and positive-eigenvalue assertions. The floating block condition number is 24.95 and its solved charge residual is 1.98e−31 F. Eight independent ngspice 1 MHz AC runs, exciting P and N separately for both layouts/boundaries, **passed** the declared absolute 1e−25 F matrix-agreement criterion; see [checks](fill-clip-analysis-20260922-r1/ac_checks.json). This validates network reduction, not the extractor's physical accuracy.

## Export failure and local fix

The installed RF MOS mapping file unconditionally calls `purge_devices` and `purge` before the optional simplification settings. It removes this intentionally device-free clip, even with `purge=false`. Initial r1 exports therefore contained no circuit and KPEX failed “No extracted layers found.” The first export also retained a cleanup-path permission error despite return code zero. These are invocation/export failures, not zero capacitance.

Failed r2/r3 wrapper trials attempted re-extraction through repeated DSL `lvs_data` calls and raised “The netlist has already been extracted.” The successful [local export wrapper](export_clip_lvsdb.lvs), snapshotted in r4, holds the returned LayoutToNetlist object once, resets its extracted state, and re-extracts its existing rule-defined connectivity. It writes that raw graph and explicitly creates top pins after the unchanged stock deck. This bypasses the post-extraction empty-circuit purge for a pure-metal diagnostic only. It is not used to qualify device matching or replace production LVS. Explicit `target_netlist` also avoids writing the cleanup file at filesystem root. All failed r1–r3 logs remain available.

## Reproduction

Run from repository root in the pinned image; choose fresh output directories. `prepare_fill_clip.py` and its retained r1 snapshot create the exact clips; the successful export and analysis commands are:

```sh
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/run_fill_clip_pex.py --clip designs/g1-guardian/review/audits/fill-clip-pilot-20260922-r1 --output designs/g1-guardian/review/audits/fill-clip-pex-NEW
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/analyze_fill_clip.py --input designs/g1-guardian/review/audits/fill-clip-pex-NEW --output designs/g1-guardian/review/audits/fill-clip-analysis-NEW
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/check_fill_clip_ac.py designs/g1-guardian/review/audits/fill-clip-analysis-NEW
```

The runner records exact tool commands, timeouts and statuses per independent check. The extraction command uses the unchanged installed KPEX deck through the local export wrapper, then `kpex --pdk ihp-sg13g2 --threads 1 --lvsdb ... --cell sense_fill_clip --2.5D --mode CC`. Full assembled conductor mapping, larger halo/clip convergence and an integrated SENSE coupling anchor remain required before substituting these values for whole-route parasitics. The earlier [route geometry audit](SENSE_ROUTE_FILL_20260922.md) remains an estimate of resistance and ground capacitance; this pilot adds local extracted coupling without silently replacing it.
