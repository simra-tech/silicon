# Candidate V5 VBIC Vrth-Transition Diagnostic V2 Evidence

## Scope

This package preserves one frozen 4 ns Candidate V5 transient performed with the repaired Vrth-transition V2 diagnostic layered on seven retained ngspice 46 diagnostics. It publishes the exact eight-patch source lineage, current and correction-history audits, syntax/configuration history, fresh-build provenance, Candidate V5 deck and netlist, native simulation log, full binary raw dataset, invocation metadata, and identity tables. The executable is identified but deliberately not included.

Engineering status: **UNKNOWN**. This is one diagnostic observation, not a circuit specification result. It makes no solver-root-cause, design-improvement, signoff, or tape-out-readiness claim.

## Strongest supported result

Native log lines 3–4 contain the one Vrth-transition marker for the exact target device:

```text
[VBIC_VRTH_TRANSITION_DIAGNOSTIC] Site: state0_writeback@1075 | stored_before: 0x1.c72b23f8bee14p+4 (isfinite=1) | Vrth(local): -0x1.21ba19b869b9ep+6 (isfinite=1) | state0_after_write(direct read): -0x1.21ba19b869b9ep+6 (isfinite=1) | state1: 0x0p+0 (isfinite=1) | state2: 0x0p+0 (isfinite=1) | CKTtime: 0 | CKTmode: 1056
  tempnode RHS accumulator (current read, not a causal sum): 0x0p+0 (isfinite=1)
```

Exact final source `vbicload_vrth_transition_diag_v2.c`, SHA-256 `59d875679da675ef8daedbd151e91b39b27a13ae197530af40650c62e3e75172`, reads `Vrth` from `CKTrhsOld + here->VBICtempNode` at physical line 504, captures the existing stored state immediately before the unchanged writeback at line 1075, performs the unchanged writeback at line 1076, and then reads state0 directly in the marker.

The strongest result is exactly: **at simulation time zero for the target instance, a finite positive stored Vrth value was replaced by a finite negative local Vrth value sourced from the old-RHS thermal node; the direct post-write state0 read equals that negative local value.** State1 and state2 were finite zero. The separately printed current RHS accumulator was finite zero and is explicitly only a contemporaneous read, not a causal sum.

This proves the finite positive-to-negative stored-state transition at this exact writeback boundary. It does not explain why the solver's old-RHS thermal-node value was negative. That upstream solver/circuit cause remains **UNKNOWN**. The later retained diagnostics show non-finite model quantities, but they do not retroactively establish the cause of this earlier finite transition.

## Diagnostic and repair boundary

The Vrth-transition V1 patch adds a read-only pre-write capture and a target-gated, once-only marker around the unchanged state0 writeback. The trigger requires finite non-negative `stored_before` and finite negative local `Vrth`. It writes only stderr and one once flag; it does not change model, matrix, RHS, state, limiter, or evaluator arithmetic.

V1's configured syntax check exposed one genuine format warning: `CKTmode` is `long`, but the marker used `%d`. The V2 patch is one hunk with one deletion and one addition; it changes only `%d` to `%ld`. All other 4,453 lines remain byte-identical. V2's configured syntax-only check exits 0 with no compiler output. Audit V3 binds V1, Audit V4 binds the one-conversion repair, and corrected Audit V5 is the current authority.

`NGSPICE46-VBIC-VRTH-UPSTREAM-TRACE-AUDIT-V1.tsv` is retained as superseded planning history because its post-write observation boundary could not prove a transition. V2 of that audit moves the observation boundary immediately before the unchanged writeback and defines the finite sign-transition gate used by P7.

## Syntax/configuration history

The first V1 syntax attempt reconstructed the seven-patch lineage in a pristine, unconfigured tree. It then exited 1 because ngspice's headers require the generated `ngspice/config.h`. This is a configuration-environment boundary, not a source diagnostic result.

A separate fresh tree reconstructed the same seven-patch source and ran configure once. Its pre-configure record has zero object files, generated Unix `config.h`, configure state, active make process, active ngspice process, or built executable. Configure exited 0, generated header SHA-256 `486fa8f0e2459cd8d2bb92e6c020f30da1d95197783a2ff631de9f0d650fe82b`, and still produced no object or executable.

The configured-tree V1 syntax check exited 0 but emitted the single `%d`/`long` warning. The V2 syntax check compiled the external repaired source without modifying the configured tree, exited 0, and emitted no compiler diagnostic. The V1 tree source stayed `c571a9c6…`; the checked V2 source stayed `59d87567…` before and after.

All scripts and path-bearing logs are public, reversibly sanitized copies. `SYNTAX-IDENTITIES.tsv` records original and public hashes and the exact symbolic substitutions.

## Eight-patch build lineage

The successful isolated build began from the official ngspice 46 archive, SHA-256 `a0d1699af1940b06649276dcd6ff5a566c8c0cad01b2f7b5e99dedbb4d64c19b`. Its official `vbicload.c` is `752518c6b2c943e901ed4f20199aa80e66b04820de9db7ecae774e20a0d746f5`. Eight patches were applied exactly once:

1. Vrth-origin V2 → `b3abd28a…`;
2. temperature-node stamp V3 → `ee6b2aa9…`;
3. Ith RHS decomposition V1 → `e8939ea1…`;
4. Ith current-term V2 → `01cc4f1f…`;
5. Ibe-source V2 → `2999b2af…`;
6. temperature-scale V1 → `92123daa…`;
7. Vrth-transition V1 → `c571a9c6…`; and
8. Vrth-transition repair V2 → `59d87567…`.

All eight patch exits are 0, and every 51-byte apply log contains the expected patching-file line. Independent reconstruction from the official archive and the eight published patches reproduced every intermediate identity and the candidate and build final source byte-for-byte.

The pre-build record reports zero object files, generated configure state, Unix `config.h`, build logs, `.deps` directories, built executable, active make process, or active ngspice process. The six `Makefile`s and Visual C `config.h` are shipped archive contents. Configure ran once and exited 0; `make -j4` ran once and exited 0. The make log contains 233 compiler-warning lines, no `error:` line, and no VBIC-specific warning. These establish build execution only, not circuit correctness.

The built and executed binary is identified as SHA-256 `7cdeb7f97c5744b8c453f52c404870df946e67657ff07537d63979928faca5c5`, 8,046,160 bytes. It is not published.

## Invocation evidence and metadata correction

`INVOCATION-METADATA.txt` is the exact frozen three-line record: start `2026-07-31T16:27:06Z`, exit 0, end `2026-07-31T16:27:08Z`. It is **89 bytes**, SHA-256 `53defb8d890e774afa1c5cdacc0a99bc8c12059c1c44b695449935e92fc35c8c`.

A stale report described this artifact as 132 bytes with a digest beginning `ec2f`. That claim is false and is not propagated as an artifact identity. Direct snapshot hashing, byte count, manifest entry, and `INVOCATION-IDENTITIES.tsv` all bind the actual 89-byte file.

The native log records, each once and in order: Vrth transition at line 3, temperature scale at line 6, Ibe source at line 10, Ith current-term at line 15, Ith RHS decomposition at line 45, temperature-node stamp at line 80, Vrth origin at line 83, and retained warnings at lines 87–88. It ends with 2,284 data rows and `ngspice-46 done`. These are process and diagnostic observations, not a circuit pass.

## Raw evidence

Direct parsing of `raw_tb_p1_cml_div2_front_tran_v5.raw` gives 429 variables × 2,284 points = 979,836 IEEE-754 doubles. All saved values are finite, and time is strictly increasing from 0 to 4 ns. The raw SHA-256 is `5fac5da9e6c5dd4094a1649956a5baa7cc13afed183df37b2c9ae56099e8cb9f`.

The 7,838,688-byte binary payload has SHA-256 `26c62c1942b552ae609f6eb57e9746ee30ad77b7a5c6e433c118ddd965de3de7` and is byte-identical to the preceding published temperature-scale run. Their headers carry different invocation metadata.

**Raw finiteness and payload identity are not an engineering pass.** The raw file contains selected saved vectors; the diagnostics observe internal model operands and state transitions not represented by those vectors.

## Public-copy and manifest boundary

The executed deck's private PDK root is replaced by literal `$PDK_ROOT`. Build and syntax evidence use the symbolic tokens documented in their identity tables. Reversing every substitution reproduced the frozen originals byte-for-byte.

`PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive. No executable, credential, cookie, prompt, transcript, private reasoning, private host path, unrestricted log, symlink, or executable-mode file is included.
