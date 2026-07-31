# Candidate V5 VBIC Ibe Source Diagnostic Evidence V1

## Scope

This package preserves one frozen 4 ns Candidate V5 transient performed with the accepted Ibe-source V2 diagnostic layered on the retained ngspice 46 Vrth-origin, temperature-node stamp, Ith RHS decomposition, and Ith current-term diagnostics. It publishes the exact five-patch source lineage, Ibe static source trace and correction history, syntax evidence, clean-build provenance, Candidate V5 deck and netlist, native simulation log, full binary raw dataset, and identity tables. The executable is identified but deliberately not included.

Engineering status: **UNKNOWN**. This is one diagnostic run, not a circuit specification result. It makes no root-cause, unit, circuit-improvement, signoff, or tape-out-readiness claim.

## Strongest supported result

Native log lines 3–6 contain the one Ibe-source marker for the exact target device. Its first line is:

```text
[VBIC_IBE_SOURCE_DIAGNOSTIC] Branch: p[32]==1.0 (WBE=1), p[98]<=0.0 (VBBE=0), BaseAssignment: 01cc4f1f@3639 | *Ibe: -nan (isfinite=0) | IBEIatT: -nan (isfinite=0) | expi: 0x1.138fec8ceee34p-147 (isfinite=1) | IBENatT: -nan (isfinite=0) | expn: 0x1.a17f4acb5c4bbp-79 (isfinite=1)
```

The exact observation shows:

- runtime branch selectors `p[32]=0x1p+0` and `p[98]=0x0p+0`, both finite;
- output `*Ibe` is non-finite;
- `IBEIatT` is the first printed immediate operand that is non-finite, and `IBENatT` is also non-finite;
- junction exponentials `expi` and `expn`, and their arguments `argi` and `argn`, are finite;
- `*Vbei`, `Vtv`, `Tdev`, `*Vrth`, `rT`, `dT`, and printed parameters `p[31]`, `p[33]`, `p[34]`, and `p[35]` are finite; and
- `Vtv`, `Tdev`, `*Vrth`, `rT`, and `dT` are finite but negative in this observation.

The strongest result is exactly: **at the runtime-taken `p[32]==1.0`, `p[98]<=0.0` assignment boundary, `*Ibe`, `IBEIatT`, and `IBENatT` are non-finite while the printed junction exponential values and arguments are finite; the other printed supporting operands and parameters are finite, with the printed thermal quantities listed above negative.**

This identifies a measured separation between the temperature-scaled current operands and the junction exponential operands. It does not identify which earlier computation first made either temperature-scaled current non-finite. The static source trace includes `xvar2=pow(rT,p[79])`, but this run did not print `p[79]` or `xvar2`; any negative-`rT` power-domain explanation remains **PROVISIONAL and unmeasured**, not a root-cause result.

## Source and marker boundary

The marker label `BaseAssignment: 01cc4f1f@3639` deliberately names the assignment in exact P5 base source `vbicload_ith_term_diag_v2.c`, SHA-256 `01cc4f1fe6c078df51147cf1ab6b60714b3fe68e704053769777528a1f1f3b06`. In final applied source `vbicload_ibe_source_diag_v2.c`, SHA-256 `2999b2afa9a34fdd501f02a2312be2b98f5f5f57c9d7bd0637321a61aa581075`, the same unchanged assignment is at physical line 3640 and the marker block is at lines 3641–3653.

The V2 patch changes the prototype, call-site tail, and function definition only to pass one exact-instance integer predicate. The runtime marker reads function locals, call inputs, and the `p[]` parameter array, writes diagnostic text to stderr, and mutates one once flag. It makes no circuit, model, matrix, RHS, or state write.

## Ibe audit correction history

`NGSPICE46-VBIC-IBE-SOURCE-TRACE-AUDIT-V1.tsv` is the retained static source map that identified all five `*Ibe` assignments, the frozen candidate branch, immediate operands, and the smallest read-only observation boundary.

The Ibe V1 patch and Audit V2 are published as static-draft history. They apply cleanly and bind exact sources, but V1 was not accepted for build: its marker used an ambiguous applied/base line label, its nonlinear inventory was incomplete, and several interface/output classifications needed correction.

The Ibe V2 patch, SHA-256 `3699f89330327627b1b9c50ecae4c7fc7c8fb6d60ef831d57967cdd65634c4b2`, retains the 17-addition/3-deletion footprint while correcting the provenance label and indentation. Audit V3 is preserved as superseded history because it still mislabeled the caller predicate, function-definition interface, and comment scope. Audit V4, SHA-256 `8f39abcde7166071a18d36321ffd3250efaff3d657afef1bdf46dca5e81061e4`, is the current authority: 37 rows × 9 columns, 37 unique IDs, 30 byte-exact numeric source rows, and 7 bridge rows.

## Syntax evidence and correction boundary

The retained 816-byte syntax log records base `01cc4f1f`, one Ibe V2 patch application at exit 0, applied source `2999b2af`, one stated `gcc ... -fsyntax-only vbicload.c` invocation, exit 0, and no compiler stdout/stderr.

Its source tree was copied with plain `cp -a` from a previously configured tree. That copied tree already contained an executable, object files, `config.log`, and `config.status`, with modification times preceding the syntax step, and it already contained reconstructed base `01cc4f1f`. Therefore this package claims only that no executable was **created, linked, or invoked during the syntax step**, and that the copied base and final translation-unit identities were verified. It does not call that syntax tree build-product-free or freshly lineage-reconstructed.

## Clean build evidence

The later isolated build began from the official ngspice 46 archive, SHA-256 `a0d1699af1940b06649276dcd6ff5a566c8c0cad01b2f7b5e99dedbb4d64c19b`, whose official `vbicload.c` is `752518c6b2c943e901ed4f20199aa80e66b04820de9db7ecae774e20a0d746f5`. Five patches were then applied exactly once:

1. Vrth-origin V2 → `b3abd28a…`;
2. temperature-node stamp V3 → `ee6b2aa9…`;
3. Ith RHS decomposition V1 → `e8939ea1…`;
4. Ith current-term V2 → `01cc4f1f…`; and
5. Ibe-source V2 → `2999b2af…`.

All five patch exits are 0. Each 51-byte apply log contains `patching file src/spicelib/devices/vbic/vbicload.c`; none is empty. Independent source reconstruction from the published patches reproduced every intermediate and the clean-build final source byte-for-byte.

The raw pre-build scan reports 55 executable-permission files and `CONFIGURE_STATE=7`. These are pristine archive contents, not prior build products: the executable-permission files are shipped scripts/test runners, while the seven configure-state matches are six shipped test `Makefile`s plus the shipped Visual C `config.h`. The fresh tree had no object files, `.deps` directories, prior build logs, `config.log`, `config.status`, or built `src/ngspice`.

Configure ran once and exited 0. Exactly one tracked `make -j4` background process ran; one orchestration wait timed out while that same process continued, and its later collection returned exit 0. This was not a retry. The make log has 233 compiler-warning lines byte-identical to the preceding accepted isolated build, no VBIC-specific warning, and no `error:` line. These facts establish no build execution failure; they do not establish circuit correctness.

The executed binary is identified as SHA-256 `8d0e5e52fa6f6da7d6f1c9f383a4044d64843b182d482d9b5dc9eebfa15d6277`, 8,046,160 bytes. It is not published.

Files under `evidence/build/` are public copies. Private build-tree, system-bin, system-include, and proc paths were replaced by literal symbolic tokens where present. `BUILD-IDENTITIES.tsv` records original and public-copy hashes. Reversing each substitution reproduced the immutable scratch snapshot byte-for-byte.

## Invocation and native evidence

`INVOCATION-METADATA.txt` is the exact frozen three-line record for one invocation: start `2026-07-31T15:22:05Z`, `NGSPICE_EXIT=0`, end `2026-07-31T15:22:07Z`. No preflight executable invocation or retry occurred. The native log records these markers and warnings in exact order, each once:

1. Ibe-source marker, line 3;
2. Ith current-term marker, line 8;
3. Ith RHS decomposition marker, line 38;
4. temperature-node stamp marker, line 73;
5. Vrth Origin-8 marker, line 76; and
6. the retained thermal warnings, lines 80–81.

The native log ends with 2,284 data rows and `ngspice-46 done`. These establish process completion only.

## Raw evidence

Direct parsing of `raw_tb_p1_cml_div2_front_tran_v5.raw` gives 429 variables × 2,284 points = 979,836 IEEE-754 doubles, all finite, with strictly increasing time from 0 to 4 ns. Its SHA-256 is `6e0404129c8401451099c3d758763164f63b6358c170df7f8af984d446210ca7`.

The 7,838,688-byte binary payload has SHA-256 `26c62c1942b552ae609f6eb57e9746ee30ad77b7a5c6e433c118ddd965de3de7` and is byte-identical to the preceding published Ith current-term run. Their 18,789-byte ASCII headers differ only in `Date:` and `Command: ... Build ...` metadata.

**Raw finiteness and payload identity are not an engineering pass.** The raw file records selected saved vectors; the Ibe marker observes internal model operands not represented by those saved vectors.

## Deck reconstruction

`tb_p1_cml_div2_front_tran_v5.public.cir` differs from the executed private deck only by replacing the private PDK installation root with literal `$PDK_ROOT`. Reversing that substitution reproduced the 1,648-byte executed deck byte-for-byte at SHA-256 `46e7f223c140769ddbb1f503200caf463bccb395c6f117c39873a600170076fa`.

## Manifest boundary

`PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive. No executable, credential, cookie, private reasoning, prompt, transcript, private deck, private build log, unrestricted log, symlink, or executable-mode file is included.
