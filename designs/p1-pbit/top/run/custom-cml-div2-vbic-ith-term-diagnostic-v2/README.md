# Candidate V5 VBIC Ith Current-Term Diagnostic Evidence V2

## Scope

This package preserves one frozen 4 ns Candidate V5 transient performed with the accepted Ith current-term V2 diagnostic layered on the retained ngspice 46 Vrth-origin, temperature-node stamp, and Ith RHS decomposition diagnostics. It publishes the exact patch lineage and applied sources, corrected audits, Candidate V5 deck and netlist, native simulation log, full binary raw dataset, path-sanitized syntax/build logs, and provenance tables. The executable is identified but deliberately not included.

Engineering status: **UNKNOWN**. This is one diagnostic run, not a circuit specification result. It makes no root-cause, unit, circuit-improvement, signoff, or tape-out-readiness claim.

## Strongest supported result

Native log line 3 begins the one current-term marker for the exact target device:

```text
[VBIC_ITH_TERM_DIAGNOSTIC] Site: MODEL_CALL@721 | iret: 0 | Ith: nan (isfinite=0) | SCALE: 0x1p+0 (isfinite=1)
```

The following 14 source-order term groups show:

- the 14 groups contain 15 returned current operands because transport group 03 prints `Itzf` and `Itzr` separately;
- 14 of those 15 current operands are non-finite; only `Ibex` is finite;
- all 14 voltage operands are finite;
- 13 of 14 products are non-finite;
- group 04, `Ibex*Vbex`, is the only finite current/voltage/product group;
- group 01, `Ibe*Vbei`, is the first source-order term group with a non-finite current and product; and
- all 14 post-scale algebraic cumulative values are non-finite, starting at `cum 00`.

The marker observes `SCALE=0x1p+0`, exactly 1.0. Applied source line 4312 guards output scaling with `if((*SCALE)!=1.0)`, so the scaling block was skipped for this target in this observation. `Ith` and the returned non-finite currents were therefore already non-finite before that conditional block. This run does not identify which upstream model computation first made `Ibe` or the other returned currents non-finite.

The strongest result is exactly: **at this post-model-call boundary, `Ith` is non-finite; 14 of 15 returned current operands across the 14 source-order Ith groups are non-finite while all 14 voltage operands are finite; the conditional output-scaling block was skipped because SCALE was exactly 1.0; group 01 is the first source-order non-finite term group and group 04 is the only finite product group.**

This does not establish a physical unit, upstream root cause, solver implication, or circuit status.

## Source and diagnostic boundary

In exact applied source `vbicload_ith_term_diag_v2.c` (SHA-256 `01cc4f1fe6c078df51147cf1ab6b60714b3fe68e704053769777528a1f1f3b06`):

- the model call is at physical lines 721–739;
- the current-term diagnostic is at physical lines 740–803;
- the model's 14-term `Ith` assignment is at physical line 4229;
- the output-scaling guard is at physical line 4312 and its block ends at line 4414.

The cumulative values are explicitly labeled post-scale algebraic reconstructions from returned operands, not exact floating-point replays of source line 4229. No equality between `cum 13` and `Ith` is claimed.

The audit's `BRIDGE_TRIGGER` text names line 4165 for that formula; this is the physical formula line in the exact P4 base source `e8939ea1` before the 64-line insertion. In the final applied source, the same unchanged formula is at physical line 4229.

The retained marker tokens `MODEL_CALL@721` and `STAMP_ITH_RHS_DECOMP@1472` are source-site labels. The first matches the current call line; the second is a historical label inherited from the earlier diagnostic and is not a current physical source line number.

## Static V2 audit

The V2 patch is a pure 64-line insertion after the unchanged model call and before the unchanged `here->VBICpower = Ith` write. Corrected audit `NGSPICE46-VBIC-ITH-TERM-DIAGNOSTIC-AUDIT-V2.tsv` inventories all 64 additions and explicitly distinguishes:

- the per-instance predicate read from `here->VBICname`;
- the static first-occurrence flag;
- the post-call local numeric `Ith` used by the trigger;
- the header's `iret`, `Ith`, and `SCALE` reads;
- the returned current operands and retained local voltage operands; and
- the 14 diagnostic-local cumulative assignments.

The separately retained syntax-only compile returned exit 0. Syntax completion is not a configured-build, simulation, or circuit-status result.

## Build evidence

The build source was reconstructed in four patch steps: official ngspice 46 plus the Vrth-origin V2 patch, then temperature-node stamp V3, then Ith RHS decomposition V1, then Ith current-term V2. `lineage.public.log` records exactly four patch exits, P1 through P4, all 0. Configure and make exits are separate and both 0. Each 51-byte apply log contains the line `patching file src/spicelib/devices/vbic/vbicload.c`; none is empty.

Exactly one tracked `make -j4` background process was launched. A 180-second orchestration wait timed out while that same process remained active, and a later collection returned its exit 0. The wait was not a build retry. The make log contains 233 compiler-warning lines byte-identical to the preceding accepted isolated build, no VBIC-specific warning, and no `error:` line. These facts establish no build execution failure; successful build completion does not establish circuit correctness.

The executed binary is identified as SHA-256 `1b6c79d345f6787bb6eb63bf807f8219f55789bc81e4869f5714dbda8f5f93df`, 8,046,160 bytes. It is not published.

Files under `evidence/build/` are public copies. Private build-tree, syntax-tree, system-bin, system-include, and proc paths were replaced with literal symbolic tokens where present. `BUILD-IDENTITIES.tsv` records each original/private hash and public-copy hash. Independently reversing every substitution reproduced each original snapshot byte-for-byte.

## Invocation and native evidence

`INVOCATION-METADATA.txt` is the exact frozen three-line process record: exactly one batch invocation started at `2026-07-31T14:43:24Z`, returned `NGSPICE_EXIT=0`, and ended at `2026-07-31T14:43:26Z`. No preflight invocation or retry occurred. The native log records the diagnostic markers in this exact line order, each once:

1. Ith current-term marker, line 3;
2. Ith RHS decomposition marker, line 33;
3. temperature-node stamp marker, line 68;
4. Vrth Origin-8 marker, line 71; and
5. the two retained warnings, lines 75–76.

The native log ends with 2,284 data rows and `ngspice-46 done`. These establish process completion only.

## Raw evidence and preceding-run comparison

Direct parsing of `raw_tb_p1_cml_div2_front_tran_v5.raw` gives 429 variables × 2,284 points = 979,836 IEEE-754 doubles, all finite, with strictly increasing time from 0 to 4 ns. Its SHA-256 is `555918cbfd03783df575ee76c0d203cc0275c7f6d717bf2f511c82278d702b30`.

The 7,838,688-byte binary payload has SHA-256 `26c62c1942b552ae609f6eb57e9746ee30ad77b7a5c6e433c118ddd965de3de7` and is byte-identical to the preceding published Ith RHS decomposition run. The 18,789-byte ASCII headers differ only in their `Date:` and `Command: ... Build ...` metadata lines.

**Raw finiteness and payload identity are not an engineering pass.** The raw file records selected saved vectors; the marker observes local model outputs at an internal boundary. A fully finite saved raw structure neither retracts nor explains the native non-finite diagnostic evidence.

## Deck reconstruction

`tb_p1_cml_div2_front_tran_v5.public.cir` differs from the executed private deck only by replacing the private PDK installation root with literal `$PDK_ROOT`. Substituting the private root rehydrates the 1,648-byte executed deck byte-for-byte at SHA-256 `46e7f223c140769ddbb1f503200caf463bccb395c6f117c39873a600170076fa`.

The source identities and every reconstruction boundary are recorded in `SOURCE-IDENTITIES.tsv`. Build-log and deck substitutions are recorded in `BUILD-IDENTITIES.tsv` and `INVOCATION-IDENTITIES.tsv`.

## Manifest boundary

`PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive. No executable, credential, cookie, private reasoning, prompt, transcript, private deck, private build log, or unrestricted log is included.
