# Candidate V5 Full-MNA Snapshot Probe V3 Evidence

## Scope

This package preserves the source, matched build boundary, paired native ngspice runs, full sparse MNA snapshot, solver-residual reconstruction, runtime equation-name map, and equation-100 contribution join for Candidate V5's VBIC thermal-node investigation.

The diagnostic captures one event at thermal-node equation 100, iteration 3, simulation time zero, mode 1056. It records the assembled sparse matrix and right-hand side immediately before the solver and the complete solution vector immediately after it. The base and patched executables then run the same frozen 4 ns deck.

Engineering status: **UNKNOWN**. The package establishes a numerically consistent captured solve, names all 13 columns in equation 100, quantifies strong cancellation, and establishes exclusive static write-chain ownership for 11 entries. It does not resolve all entry ownership or physical-device causality, evaluate a circuit measurement, satisfy a specification, or support signoff or tape-out-readiness.

## Strongest supported result

The accepted runtime recount is `evidence/runtime/NGSPICE46-VBIC-MNA-SNAPSHOT-PROBE-V3-RUNTIME-V4.log`, SHA-256 `474ff3593c7369cfd378a8ca6e9b60c423c1fb0eb3795fd848a0169f073a4434`.

The patched run emits one structurally complete pair:

- prefactor: one BEGIN, 3,254 unique in-range matrix entries, 371 right-hand-side values, and one END;
- postsolve: one BEGIN, 371 solution values, and one END;
- all four boundaries share snapshot id 1, thermal node 100, iteration 3, time 0, mode 1056, and backend 0;
- all 3,996 numeric payload records are finite;
- no guard, unsupported, or abort record appears.

Reconstruction of every captured equation gives a maximum normalized residual of `1.997255e-15` at equation 214. Equation 100 has 13 terms and a normalized residual of `1.108590e-16`. This rejects a malformed linear solve at the captured event: the solver accurately solved the coupled system it was given.

The result does **not** show which device contribution assembled that system. The negative equation-100 solution is therefore localized to the assembled coupled system, not assigned to a device or model mechanism.

The follow-on equation-map runtime report is `evidence/eqmap/NGSPICE46-VBIC-MNA-SNAPSHOT-PROBE-V3-EQMAP-PATCH-V4-RUNTIME-V2.log`, original SHA-256 `27ef7c0d0a37e46f6d61ba3c01d588815081fecbbad0b2c50407422725b2bf2b`. It joins all 13 equation-100 columns to runtime node names at the same snapshot event while preserving the binary circuit payload.

## Source and build boundary

`NGSPICE46-VBIC-MNA-SNAPSHOT-PROBE-V3.patch`, SHA-256 `d833221f0d133ea75ea5e70861eb42c32a409f6c1aa01465cf78dc93aa2e4afa`, is a unified diff over three ngspice 46 files. Corrected Audit V3, SHA-256 `840a5097675506fc4940eadf1031eabcc3847e66386ba77446612b7cbee31b90`, records every hunk and reconstructs the three published applied sources byte-for-byte:

- `source/smpdefs_probe_v3.h`: `61acdc96443b583cf8915bf3e3528284fbeb9c4b48fb694787f1a7959b45b369`;
- `source/klusmp_probe_v3.c`: `d9a40052c6c29c6ecf7c2ee34a946512d3221908787b2e15095fad69ea9f297d`;
- `source/niiter_probe_v3.c`: `fa26677f5436801e0e725cf9500b80a03b3c2faf7a8fa0cbe32c518f1d7a811e`.

The helper is stderr-only and uses hexadecimal floating-point output. It does not write matrix, RHS, state, model, or device data; create sparse elements; or change the existing load, solve, factor, reorder, or damping calls.

Matched syntax evidence covers four translation units. All four compiler invocations return zero; base and patched KLU units each retain the same three pre-existing warnings, while both NIiter units emit none. The patch warning delta is zero. Object evidence identifies all four resulting objects. LINK-V4 forces the two archives and top executable on both sides: all six link commands return zero, with no link warning or error.

The startup boundary invokes each matched executable only through `--version`. Both return zero with identical 449-byte output and leave the executables unchanged. Startup completion is not circuit evidence.

## Frozen deck and native-runtime boundary

The executed deck has original SHA-256 `46e7f223c140769ddbb1f503200caf463bccb395c6f117c39873a600170076fa`. The exact netlist has SHA-256 `689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`. The 35-entry include manifest has original SHA-256 `32cc8891585e8e14666f1acdc0a32c55c7b59b4620b6a766cdea8d532d1cb6cf`.

The public deck replaces its private PDK prefix with literal `$PDK_ROOT`; the public include manifest uses `$PDK_ROOT` and package-relative deck/netlist names. `PUBLIC-COPY-IDENTITIES.tsv` binds each sanitized copy to its frozen original.

This deck loads PDK libraries and OSDI models and contains a native control block. It is outside the shared OpenADA backend-comparable profile. The evidence is native ngspice evidence only.

The accepted V2 capture directories contain one base and one patched invocation. Both return zero. Direct parsing of each binary raw file finds:

- 429 variables × 2,284 points = 979,836 IEEE-754 doubles per side;
- all values finite;
- a strictly increasing time vector from 0 to 4 ns;
- an exact 7,838,688-byte binary data region;
- data-region SHA-256 `26c62c1942b552ae609f6eb57e9746ee30ad77b7a5c6e433c118ddd965de3de7` on both sides.

The raw files have different full-file hashes because their headers contain different date lines. Their binary payloads are byte-identical. Patched stderr, after removal of exactly 4,000 snapshot lines, equals base stderr byte-for-byte. The two stdout files differ only in one wall-clock progress-print line; this is not circuit data.

## Residual and equation-name authority

`evidence/analysis/NGSPICE46-VBIC-MNA-SNAPSHOT-PROBE-V3-RESIDUAL-V3.log`, SHA-256 `1123147613f776974e332a1ff7c21beb3585565424ab3c7c5bb88cf52c5aba03`, recomputes the accepted residual result from the immutable patched stderr. The equations and equation-100 term TSVs are the unchanged V1 data tables; V3 corrects only the explanatory log.

The static authority audit explicitly rejects raw-file variable ordering as an equation map. Raw `Variables:` rows describe saved outputs and list device currents before node voltages.

One exact retained static chain exists for equation 100: the accepted NIiter source resolves `q.xdiv2.xqs_comp_s.qnpn13g2`, reads its `VBICtempNode`, and the runtime marker reports `tnode: 100` at the accepted event. Ngspice allocates node numbers as external equation indices, and the snapshot reports external indices through the sparse maps. Equation 100 is therefore mapped to the target instance's VBIC thermal node.

The accepted equation-map patch adds a read-only external-equation-to-node-name walk to the existing diagnostic event. Its matched syntax, object, link, loader, and runtime evidence is retained under `evidence/eqmap/`. In the experiment, exactly one BEGIN record, 13 unique equation/name rows, and one END record share snapshot id 1. Removing those 15 diagnostic lines makes experiment stderr byte-identical to control stderr. The two binary waveform data regions are also byte-identical. The named set is exactly equations 2, 70, 79, 98, 99, 100, and 102 through 108; no value-match or output-order heuristic is used.

`evidence/eqmap/NGSPICE46-VBIC-MNA-SNAPSHOT-PROBE-V3-EQMAP-ROW100-ANNOTATED-V1.tsv`, original SHA-256 `e396325218f2a64aac5a16015130d0aeaf4567f07b153f5e1190dacda9373f25`, performs a one-to-one immutable join between those names and the 13 retained equation-100 products. Recalculation gives:

- positive-product sum `0x1.1066945a83c2bp+1`;
- negative-product sum `-0x1.0b5a0905fe98ap+1`;
- signed row total `0x1.4322d5214a813p-5`;
- sum of absolute products `0x1.0de04eb0412dap+2`;
- cancellation ratio `9.354291e-03`.

The largest absolute terms are equation 70 `xdiv2.e_tail_s`, equation 106 target-VBIC `#collCI`, equation 100 `xdiv2.xqs_comp_s.t`, equation 102 target-VBIC `#collector`, and equation 108 target-VBIC `#baseBI`. Magnitude and naming establish coupled participation, not source ownership or causality.

## Static stamp-authority boundary

`evidence/eqmap/NGSPICE46-VBIC-MNA-SNAPSHOT-PROBE-V3-VBIC-TEMP-STAMP-AUTHORITY-V1.tsv`, SHA-256 `bcac0618541f0d1b987941df700436af8b39fec353c212d3316f6226b7e3c5a3`, traces the frozen hierarchy, VBIC node fields, sparse-pointer orientation, and all 33 transient `vbicload.c` writes that can address the 13 captured row entries.

The fail-closed source-only dispositions are:

- **SOURCE_EXCLUSIVE (11):** equations 70, 79, 98, 99, and 102 through 108 have one retained device/write chain from the target VBIC temperature row to the named column;
- **SOURCE_CAPABLE_NOT_EXCLUSIVE (1):** equation 100 is the temperature diagonal, stamped both through `VBICtempTempPtr` and by the wrapper's `Rt t 0 R=1e9`;
- **NOT_BOUND (1):** equation 2 is global `sub!`; no exact frozen source/hierarchy chain establishes a writer for the assembled `(100,2)` entry.

These labels classify static write-chain authority. They do not measure the numerical contribution made at the captured event and do not establish a causal device mechanism.

The retained next-experiment contract is a target-instance-only before/after delta probe for equation 100, equation 2 if an existing entry can be read without sparse-element creation, and RHS(100). No such patch, build, invocation, or simulation is included in this package.

## Preserved failed attempts

`FAILED-ATTEMPTS.tsv` retains the actual correction history. It includes the superseded syntax package, interrupted or overwritten-provenance link attempts, runtime parsing and reporting defects, two residual-report corrections, and the equation-map patch/build/runtime retries. The accepted result does not erase those attempts.

The V1 paired runtime directories are not duplicated here: both completed captures, but the wrapper failed afterward and wrote no final V1 log. Runtime V4 identifies that retained attempt and the accepted V2 captures. LINK-V3's partial raw directory likewise remains in the design workspace and is identified by LINK-V4; it has no final log to publish.

## Package boundary

`RESULT-SUMMARY.tsv` separates execution, evidence validity, comparison, mapping, measurement, and specification dispositions. `PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive.

Compiled objects, archives, executables, private PDK files, credentials, cookies, prompts, transcripts, private reasoning, absolute host paths, symlinks, and executable-mode files are excluded. The equation-map runtime subdirectories contain only the deck-backed captures (`rc`, `times`, stdout, stderr, and binary raw output); the existing sanitized deck and dependency manifest remain their authority.
