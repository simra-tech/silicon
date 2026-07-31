# Candidate V5 VBIC Thermal-Vector Probe V4 Evidence

## Scope

This package preserves one frozen 4 ns Candidate V5 transient performed with the ngspice 46 NIiter thermal-vector Probe V4 layered on the retained VBIC diagnostic build. It publishes the complete V4 patch, corrected V5 audit, exact applied `niiter.c`, matched syntax/object/library/top-link evidence, sanitized Candidate V5 deck and 35-entry include identity manifest, exact netlist, native simulation log, full binary raw dataset, and invocation metadata. Compiled objects, libraries, and the executable are identified but deliberately not included.

Engineering status: **UNKNOWN**. This is one diagnostic observation, not a circuit specification result. It makes no per-device cause, design-improvement, signoff, or tape-out-readiness claim.

## Strongest supported result

Native log lines 3–4 contain the one thermal-vector marker for the exact target instance:

```text
[VBIC_THERMAL_VECTOR_PROBE] Instance: q.xdiv2.xqs_comp_s.qnpn13g2 | tnode: 100 | iterno: 3 | CKTtime_at_load: 0 | CKTmode_at_load: 1056
  old_before_load: 0x1.c72b23f8bee14p+4 (isfinite=1) | assembled_before_solve: 0x1.4322d5214a7cfp-5 (isfinite=1) | solved_after_solve: -0x1.6cdd6aab2657p+9 (isfinite=1) | after_damping: -0x1.6cdd6aab2657p+9 (isfinite=1) | old_after_swap: -0x1.6cdd6aab2657p+9 (isfinite=1)
```

Exact applied source `niiter_thermal_vector_probe_v4.c`, SHA-256 `687e2f85776c7c1a064a980e333502aefd8162c4dd3a360412845a7a923e9625`, captures the aggregate target thermal row immediately before the unchanged `SMPsolve`, immediately after it, after the unchanged damping region, and after the unchanged RHS-vector swap.

The strongest result is exactly: **for iteration 3 at simulation time zero, the aggregate target thermal row was finite positive immediately before the coupled MNA solve and finite negative immediately after it; the printed post-damping and post-swap values remained equal to the post-solve value.** This localizes the observed sign emergence to the interval containing the coupled MNA solve.

It does not identify a device, terminal, model contribution, diagonal, conductance, integration term, or initialization mechanism as the cause. The probe does not access matrix fields or per-device stamp contributions, and the MNA solve is coupled. Device-level cause remains **UNKNOWN**.

## Source and audit boundary

Probe V4 applies to exact retained base `src/maths/ni/niiter.c`, SHA-256 `270de96a44bc550a5edb21801b9e728e8bf9d6bdb44d78a9125e655e730192af`. Independent `patch --dry-run -p0` and `git apply --check -p0` both succeeded. An independent application reproduced the published 18,197-byte source byte-for-byte.

The patch adds 80 lines and removes none. It resolves the exact VBIC instance's thermal node after NI initialization, captures five vector-boundary values with load-site time and mode, and emits once when any captured finite value is negative. Its write boundary is stderr plus the once-emitted flag. It does not modify the matrix, RHS, state, model, limiter, integration arithmetic, existing solver calls, or existing control flow.

Corrected Audit V5 is the current authority. Direct review found 57 rectangular nine-column data rows, and every physical-line `source_literal` exactly matched the SHA-bound base or applied source. It corrects earlier audit history by recording that the base source is newline-terminated and that `CKTmode`, but not `CKTtime`, changes between the relevant capture and emit sites.

## Matched build evidence

The matched syntax experiment checks retained control and V4 sources with the same configured header and compiler flags. Both syntax-only invocations exit 0, and neither emits a compiler diagnostic.

The object experiment begins with matched control/V4 trees, applies V4 with exit 0, and builds `niiter.lo` in each tree with `make -j1 V=1`; both exits are 0. The V4 object is SHA-256 `0f81b74d267a495fc6363bc1b3dbc42cca66fa16aff909ff1d3b9266b333875e`.

The library experiment rebuilds `libni.la` under matched conditions; both control and V4 exits are 0. The V4 `libni.a` is SHA-256 `257c2024c352674cb7e02d2b35dcda6f041756397130870f5b381ea4bb3f35f9`.

The top experiment runs `make -j1 V=1` in both trees; both exits are 0. The V4 top-linked executable is SHA-256 `9ec2e4a14ba0f497c6f8f253546081d7dc3b59131c19e4be50cd60284bf3c054`. The retained control source and executable identities remain unchanged after the experiments. These records establish syntax/build/link execution only, not circuit correctness.

All path-bearing build logs are public, reversibly sanitized copies. `BUILD-IDENTITIES.tsv` binds each frozen original to its public copy and documents the symbolic substitutions.

## Invocation and diagnostic evidence

`INVOCATION-METADATA.txt` is the exact three-line record: start `2026-07-31T17:39:45Z`, ngspice exit 0, end `2026-07-31T17:39:46Z`. The exact native log is 16,313 bytes with SHA-256 `14b0060ce504ac757e3e233493882c72a1b1798679cd039643e67dc920588df0`.

The native log records, each once and in order: NIiter thermal vector at line 3, Vrth transition at line 6, temperature scale at line 9, Ibe source at line 13, Ith current term at line 18, Ith RHS decomposition at line 48, temperature-node stamp at line 83, and Vrth origin at line 86. The retained thermal warning occupies lines 90–92. The log ends with 2,284 data rows and `ngspice-46 done`. Exit 0 and the done marker are process observations, not a circuit pass.

The include identity manifest contains one header and 35 executed-input rows. Its sizes and SHA-256 values remain those of the original executed inputs; only its header and paths are normalized. `INVOCATION-IDENTITIES.tsv` binds the 5,296-byte frozen original and the 4,816-byte public copy.

## Raw evidence

Direct parsing of `raw_tb_p1_cml_div2_front_tran_v5.raw` gives 429 variables × 2,284 points = 979,836 IEEE-754 doubles. All saved values are finite, and time is strictly increasing from 0 to 4 ns. The raw SHA-256 is `fe2a0f495bf85b9adda7382372affcfd3bd4fc92b8af812c02723f1783ac37fa`.

The 7,838,688-byte binary payload has SHA-256 `26c62c1942b552ae609f6eb57e9746ee30ad77b7a5c6e433c118ddd965de3de7` and is byte-identical to the preceding published Vrth-transition V2 run. Their headers differ.

**Raw finiteness and payload identity are not an engineering pass.** The raw file contains selected saved vectors; the diagnostics observe internal model and solver values not represented by those vectors.

## Public-copy and manifest boundary

The executed deck's private PDK root is replaced by literal `$PDK_ROOT`. The include manifest uses `$PDK_ROOT` and package-relative artifact names. Build evidence uses `$RETAINED_BUILD_ROOT`, `$MATCHED_BUILD_ROOT`, `$SYSTEM_CC`, and `$SYSTEM_SHELL`. Reversing every documented substitution reproduced the frozen originals byte-for-byte.

`PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive. No executable, object, library, credential, cookie, prompt, transcript, private reasoning, private host path, unrestricted log, symlink, or executable-mode file is included.
