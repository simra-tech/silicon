# Candidate V5 VBIC Temperature-Scale Diagnostic Evidence V1

## Scope

This package preserves one frozen 4 ns Candidate V5 transient performed with the temperature-scale V1 diagnostic layered on the retained ngspice 46 Vrth-origin, temperature-node stamp, Ith RHS-decomposition, Ith current-term, and Ibe-source diagnostics. It publishes the exact six-patch source lineage and current static audits, syntax evidence, failed pre-configure correction history, successful clean-build evidence, Candidate V5 deck and netlist, native log, full binary raw dataset, and identity tables. The executable is identified but deliberately not included.

Engineering status: **UNKNOWN**. This is diagnostic evidence, not a circuit specification result. It makes no physical-root-cause, design-improvement, signoff, or tape-out-readiness claim.

## Strongest supported result

Native log lines 3–5 contain the one temperature-scale marker for the exact target device. Its first line is:

```text
[VBIC_TEMP_SCALE_DIAGNOSTIC] BaseAssignment: 01cc4f1f@2038 (2999b2af@2039) | Tdev: -0x1.5025bf1640888p+6 (isfinite=1) | Vtv: -0x1.da9861fa26caap-8 (isfinite=1) | rT: -0x1.1eb3d5166ee8p-2 (isfinite=1) | p[79]: 0x1.a666666666667p+1 (isfinite=1) | xvar2: -nan (isfinite=0)
```

Exact final source `vbicload_temp_scale_diag_v1.c`, SHA-256 `92123daa3d880ac25960b8758b1e4cb4440fc55cb30f100c5750b5aa20c3e292`, computes `xvar2=pow(rT,p[79]);` at physical line 2019. At the later read-only marker:

- `rT` is finite and negative;
- `p[79]` is finite and non-integer (`0x1.a666666666667p+1`, the exact runtime double representation of the model's 3.3 value);
- the resulting `xvar2` is non-finite;
- the following `xvar3` and `xvar4` are finite, while `xvar1`, `xvar6`, and `IBEIatT` are non-finite; and
- `Tdev` and `Vtv` are also finite and negative in this observation.

The strongest result is exactly: **the printed temperature-scaling chain reaches the numerical domain boundary at `pow(rT,p[79])`: a finite negative base and finite non-integer exponent are followed by a non-finite `xvar2`, with non-finiteness then present in later `xvar1`, `xvar6`, and `IBEIatT`.**

This does not establish why `Vrth`, `Tdev`, or `rT` became negative. The upstream physical or circuit cause remains **UNKNOWN**. It also does not establish that this is the first non-finite computation anywhere in the full model evaluation; the claim is confined to this exact printed chain and source assignment.

## Diagnostic boundary

The V1 patch adds 11 lines and deletes none. Its trigger uses the exact-instance predicate already passed by the Ibe-source V2 diagnostic, a once flag, and `!isfinite(IBEIatT)`. It reads local values and the model-parameter array, writes only diagnostic text to stderr and the once flag, and does not alter circuit, model, matrix, RHS, state, or evaluator arithmetic. `NGSPICE46-VBIC-TEMP-SCALE-DIAGNOSTIC-AUDIT-V1.tsv` binds the base, patch, final source, trigger, and unchanged computation lines.

## Six-patch source lineage

The successful isolated retry began from the official ngspice 46 archive, SHA-256 `a0d1699af1940b06649276dcd6ff5a566c8c0cad01b2f7b5e99dedbb4d64c19b`. Its official `vbicload.c` is `752518c6b2c943e901ed4f20199aa80e66b04820de9db7ecae774e20a0d746f5`. Six patches were applied exactly once:

1. Vrth-origin V2 → `b3abd28a…`;
2. temperature-node stamp V3 → `ee6b2aa9…`;
3. Ith RHS decomposition V1 → `e8939ea1…`;
4. Ith current-term V2 → `01cc4f1f…`;
5. Ibe-source V2 → `2999b2af…`; and
6. temperature-scale V1 → `92123daa…`.

All six patch exits are 0, and every 51-byte apply log contains the expected patching-file line. Independent reconstruction from the official archive and the six published patches reproduced every intermediate identity and the final published source byte-for-byte. The successful-build source and retained static final source are also byte-identical.

The pre-build scan reports zero object files, generated configure state, build logs, `.deps` directories, or built `src/ngspice`. The six `Makefile`s and one Visual C `config.h` are shipped archive contents. Configure ran once and exited 0. One `make -j4` process ran; an orchestration wait elapsed while that same process continued, and later collection returned exit 0. This was not a build retry. The make log contains 233 compiler-warning lines, no `error:` line, and no VBIC-specific warning. These are build-execution facts only, not evidence of circuit correctness.

The built executable is identified as SHA-256 `3a4419de06139beec715fede7338fd63926895fede047b1e498b37203ee384dc`, 8,046,160 bytes. It is not published.

## Failed pre-configure attempt and correction

The first fresh attempt is preserved under `evidence/build/failed-attempt/`. Its pre-build scan establishes the same clean archive state, and its P1 apply log plus retained P1 source identity establish that P1 applied. The script then stopped before it could write a lineage row or invoke configure: under `set -u`, the text `P$i_EXIT` is parsed as expansion of the unset variable `i_EXIT`, rather than `${i}` followed by `_EXIT`. There is no P2–P6 apply log, lineage log, configure log, make log, linked executable, or simulation from this attempt.

This is classified as an **execution-harness correction**, not an engineering or simulation failure. The retry used a new build directory. The preserved correction diff changes only loop bookkeeping: it captures the patch exit before hashing, uses unambiguous `printf` arguments, checks each intermediate hash, and stops at a mismatch. `build-script-bashn.public.log` records `BASH_N_EXIT=0`. The successful retry then followed the clean six-patch lineage above.

Both scripts are path-sanitized public copies. Their original and public hashes are recorded in `BUILD-IDENTITIES.tsv`; reversing the documented symbolic substitutions reproduced the immutable snapshot byte-for-byte.

## Syntax evidence

The retained syntax log binds base `2999b2af`, final source `92123daa`, the exact `gcc ... -fsyntax-only vbicload.c` command, and exit 0 with empty stdout and stderr. Its private temporary working root is replaced by literal `$SYNTAX_ROOT`; reverse substitution reproduced the 682-byte original at SHA-256 `8d5bec5c75a7246da243b858176652a42d1e7bd571884321944b20a673e7d4f9`.

This establishes a narrow translation-unit syntax result. It does not replace the later isolated configure and build evidence.

## Invocation and native evidence

`INVOCATION-METADATA.txt` is the exact frozen three-line record for one executable invocation: start `2026-07-31T15:39:55Z`, exit 0, end `2026-07-31T15:39:57Z`. No preflight invocation or simulation retry occurred.

The native log records, each once and in order: the temperature-scale marker at line 3, Ibe-source marker at line 7, Ith current-term marker at line 12, Ith RHS-decomposition marker at line 42, temperature-node stamp marker at line 77, Vrth-origin marker at line 80, and the retained warning lines at 84–85. Process completion and a finite saved raw dataset do not override the internal non-finite diagnostic observations.

## Raw evidence

Direct parsing of `raw_tb_p1_cml_div2_front_tran_v5.raw` gives 429 variables × 2,284 points = 979,836 IEEE-754 doubles. All saved values are finite, and time is strictly increasing from 0 to 4 ns. The raw SHA-256 is `ca3a31431c211d61024e245bb9d8f3a1f791fd7a7652e86db607db2ea2f453ac`.

The 7,838,688-byte binary payload has SHA-256 `26c62c1942b552ae609f6eb57e9746ee30ad77b7a5c6e433c118ddd965de3de7` and is byte-identical to the preceding published Ibe-source run. Their headers carry different invocation metadata.

**Raw finiteness and payload identity are not an engineering pass.** The raw file contains selected saved vectors; the diagnostic marker observes internal model operands not represented by those vectors.

## Public-copy and manifest boundary

The executed deck's private PDK root is replaced by literal `$PDK_ROOT`. Build logs and scripts use the symbolic tokens documented in `BUILD-IDENTITIES.tsv`. Reversing each substitution reproduced the frozen originals byte-for-byte.

`PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive. No executable, credential, cookie, prompt, transcript, private reasoning, private host path, unrestricted log, symlink, or executable-mode file is included.
