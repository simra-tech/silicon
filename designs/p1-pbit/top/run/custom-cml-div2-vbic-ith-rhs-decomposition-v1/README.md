# Candidate V5 VBIC Ith RHS Decomposition Evidence V1

## Scope

This package preserves one frozen 4 ns Candidate V5 transient performed with a read-only Ith RHS decomposition diagnostic layered on the retained ngspice 46 Vrth-origin and temperature-node stamp diagnostics. It publishes the exact patch lineage and applied sources, both the superseded Ith audit V1 and corrected audit V2, Candidate V5 deck and netlist, native simulation log, full binary raw dataset, path-sanitized build logs, and provenance tables. The executable is identified but deliberately not included.

Engineering status: **UNKNOWN**. This is one diagnostic run, not a circuit specification result. It makes no root-cause, unit, circuit-improvement, signoff, or tape-out-readiness claim.

## Strongest supported result

Native log line 3 begins the one decomposition marker for the exact target device:

```text
[VBIC_ITH_RHS_DECOMP_DIAGNOSTIC] Site: STAMP_ITH_RHS_DECOMP@1472 | rhs_current: -nan (isfinite=0) | Ith: nan (isfinite=0)
```

The following 16 pair rows show:

- `Ith` is non-finite;
- 15 of 16 derivative outputs are non-finite;
- all 16 printed voltage operands are finite;
- the `Vbex` pair alone has a finite derivative (`-0x0p+0`), finite voltage, and finite product (`-0x0p+0`);
- the other 15 products are non-finite;
- diagnostic cumulative reconstruction is already non-finite at `cum 00 = -Ith` and remains non-finite.

The patch and corrected audit place this observation after the unchanged model-output computation and exact `rhs_current` expression, but before the unchanged Ith RHS stamp. Therefore, the strongest result is exactly: **at the post-model/pre-stamp boundary, `Ith` and 15 of its 16 printed derivative outputs are non-finite while all 16 printed voltage operands are finite; the Vbex derivative/voltage/product pair is finite.**

This does not identify which upstream model state or arithmetic operation made `Ith` or the derivative outputs non-finite. It does not establish a causal ordering among those non-finite outputs, their physical units, the upstream root cause, or circuit status.

## Historical site-label boundary

The marker token `@1472` is a retained **historical source-site label**, not a current applied-source line number. It names the original Ith RHS stamp site used by the earlier diagnostic lineage. In `vbicload_ith_rhs_decomp_v1.c`, the exact `rhs_current` expression is at physical lines 1488–1493, the decomposition block is at lines 1494–1566, and the unchanged Ith RHS stamp is at physical line 1569.

## Audit correction history

The Ith V1 patch itself was retained. Its first audit, `NGSPICE46-VBIC-ITH-RHS-DECOMP-DIAGNOSTIC-AUDIT-V1.tsv` (SHA-256 `2acd6c82011e74fc6833e68806c5d29b5eac98658cc3499d44061f28ce1a3401`), correctly showed no circuit, model, state, matrix, or RHS writes, but made stronger unsupported or incomplete claims:

- it omitted 17 intentionally target-triggered diagnostic reconstruction-local assignments while saying the once flag was the only write;
- it applied one target-trigger containment label to all added rows, including the pre-trigger comment, static declaration, and guard statement.
- its added-line inventory stopped at 72 and omitted the 73rd added line, the trigger block's closing brace.

That V1 audit is published as superseded correction-history evidence, not as current authority. Corrected `NGSPICE46-VBIC-ITH-RHS-DECOMP-DIAGNOSTIC-AUDIT-V2.tsv` (SHA-256 `495bc5e867e37249ffb1ac868aedb129de1774e171ed56578762faceb36eb013`) keeps the patch byte-identical, inventories all 73 additions and 17 diagnostic-local assignments, distinguishes the static once-flag declaration from its target-triggered runtime mutation, and assigns actual containment to the comment, declaration, guard, and guarded body.

The earlier stamp-diagnostic V3 patch and corrected audit V4 are retained as necessary lineage. Their own V1–V3 review history remains in the preceding published package and is not silently recharacterized here.

## Build evidence

The build source was reconstructed in three patch steps: official ngspice 46 plus the Vrth-origin V2 patch, then the temperature-node stamp V3 patch, then the Ith decomposition V1 patch. Each patch log records exit 0 and the expected intermediate source hash. Configure and make each record exit 0. Compiler warnings remain in the public make-log copy; build completion does not establish circuit correctness.

The executed binary is identified as SHA-256 `99ae102acae6825e5cab5f249180fb5a7c39fb3b6d1d9ec81d8d2f1143f92c2e`, 8,037,968 bytes. It is not published.

Files under `evidence/build/` are public copies. Private build-tree, system-bin, system-include, and proc paths were replaced with literal symbolic tokens where present. `BUILD-IDENTITIES.tsv` records each original/private hash and public-copy hash. Independently reversing the private substitutions reproduced the original configure and make hashes.

## Invocation and raw evidence

`INVOCATION-METADATA.txt` is the exact frozen three-line process record: one invocation started at `2026-07-31T14:18:42Z`, returned `NGSPICE_EXIT=0`, and ended at `2026-07-31T14:18:44Z`. The native log ends with 2,284 data rows and `ngspice-46 done`. These establish process completion only.

Direct parsing of `raw_tb_p1_cml_div2_front_tran_v5.raw` gives 429 variables × 2,284 points = 979,836 IEEE-754 doubles, all finite, with strictly increasing time from 0 to 4 ns. Its SHA-256 is `e4ff41fffc480c87b96fe132e9bb8f5b045a23d7a9c26ad9fee6ccba1a72178e`.

**Raw finiteness is not an engineering pass.** The raw file records selected saved vectors; the decomposition marker observes local model outputs and arithmetic at an internal pre-stamp boundary. A fully finite saved raw structure neither retracts nor explains the native non-finite diagnostic evidence.

## Deck and source reconstruction

`tb_p1_cml_div2_front_tran_v5.public.cir` differs from the executed private deck only by replacing the private PDK installation root with literal `$PDK_ROOT`. Substituting the private root rehydrates the 1,648-byte executed deck byte-for-byte at SHA-256 `46e7f223c140769ddbb1f503200caf463bccb395c6f117c39873a600170076fa`.

The source identities and each reconstruction boundary are recorded in `SOURCE-IDENTITIES.tsv`. The final applied source is `vbicload_ith_rhs_decomp_v1.c`, SHA-256 `e8939ea16fc58d8998b495e7f5f524b1a272b164b43ae2e9771de224ce4f97ff`.

## Manifest boundary

`PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive. No executable, credential, cookie, private reasoning, prompt, transcript, private deck, private build log, or unrestricted log is included.
