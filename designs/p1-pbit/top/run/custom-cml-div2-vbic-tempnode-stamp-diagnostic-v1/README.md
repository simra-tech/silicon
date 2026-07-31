# Candidate V5 VBIC Temperature-Node Stamp Diagnostic Evidence V1

## Scope

This package preserves one 4 ns Candidate V5 transient performed with a read-only ngspice 46 VBIC temperature-node stamp diagnostic layered on the retained Vrth-origin diagnostic. It publishes the exact diagnostic patches and applied source, the corrected V4 static stamp audit, Candidate V5 netlist, path-sanitized deck, native simulation log, full binary raw dataset, path-sanitized public build logs, and identity tables. The diagnostic executable is identified but deliberately not included.

Engineering status: **UNKNOWN**. This package is diagnostic evidence, not a circuit specification result. It makes no root-cause, circuit-improvement, signoff, or tape-out-readiness claim.

## Strongest supported result

Native simulation log line 3 is:

```text
[VBIC_TEMPNODE_STAMP_DIAGNOSTIC] Site: STAMP_ITH_RHS@1472 | Category: rhs_accumulator | Pre: 0x0p+0 (isfinite=1) | Contribution: -nan (isfinite=0) | Post: -nan (isfinite=0)
```

Native log line 6 is:

```text
[VBIC_VRTH_ORIGIN_DIAGNOSTIC] Instance: q.xdiv2.xqs_comp_s.qnpn13g2 | Origin: 8 (tempnode_load_line_484) | OriginScalar: -nan (isnan=1) | Vrth(current): -nan (isnan=1) | Vrth(stored): -0x1.802fd62bf6888p+8 (isnan=0)
```

The V4 static audit binds `STAMP_ITH_RHS@1472` to the unchanged statement `*(ckt->CKTrhs + here->VBICtempNode) += rhs_current;` in the self-heating block. The target accumulator was finite zero before that stamp, while the observed contribution and post-stamp accumulator were NaN.

Therefore, the strongest result is exactly: **the first observed target-device non-finite stamp is localized to the Ith RHS contribution.** This does not identify which operand or arithmetic operation made `rhs_current` non-finite, the upstream root cause, a physical unit, or circuit status. Those remain unresolved.

## Correction and retraction history

The publication retains the review history instead of silently replacing failed claims:

- Stamp diagnostic V1 was rejected before compilation. Its 35-site source map was retained, but its added observations ran for every self-heating instance, it used `isnan` while claiming all non-finite values, and its audit bridge carried a stale patch hash.
- Stamp diagnostic V2 was held before build. Its 105 observation statements were exact-target guarded, but broad declaration initializers were omitted from the guard proof and two audit bridge rows shifted semantic columns.
- Stamp diagnostic V3 removed the broad initializers and made predicate construction the explicit necessary guard-establishment exception. The accompanying report's 15,168-byte patch-size claim was retracted: the byte-exact V3 patch is 15,137 bytes. A contradictory guard label in its audit also kept build and simulation on hold.
- Audit V4 kept the V3 patch byte-identical, corrected the size and guard-exception wording, and restored the bridge-row meanings. Only after that static correction was the retained build and this single run performed.

The exact V3 patch and corrected V4 audit are published here. Earlier rejected patch/audit bytes remain in the upstream review record and are not represented as accepted artifacts in this package.

## Build evidence

The source was reconstructed from the official ngspice 46 `vbicload.c`, the retained Vrth-origin V2 patch, and the stamp-diagnostic V3 patch. The two patch steps, configure, and make each recorded exit 0. The make log retains compiler warnings; a completed build does not establish circuit correctness or an engineering gate.

The executable is identified as SHA-256 `74f7186acec23dbc1b4686ca38ad3d7b00fd97fef9252da355b8e2a059d43719`, 8,029,776 bytes, and reports ngspice 46 with KLU. It is not published.

Files under `evidence/build/` are public, path-sanitized copies. `BUILD-IDENTITIES.tsv` records both the original/private hashes and the public-copy hashes. Private build-tree, system-bin, system-include, and proc paths were replaced with literal symbolic tokens. Independently reversing the private substitutions reproduced each original log hash. The original private build logs are not included.

## Execution record

`INVOCATION-METADATA.txt` is the exact retained three-line process record: one invocation started at `2026-07-31T13:55:34Z`, returned `NGSPICE_EXIT=0`, and ended at `2026-07-31T13:55:36Z`. The native log ends with 2,284 data rows and `ngspice-46 done`. There was no retry represented by this record.

Exit 0 and completion text establish process completion only. They do not establish circuit validity. The diagnostic marker itself preserves the non-finite stamp observation.

## Raw evidence

Direct parsing of `raw_tb_p1_cml_div2_front_tran_v5.raw` gives:

- 429 variables and 2,284 points;
- 979,836 total IEEE-754 doubles;
- 979,836 finite and 0 non-finite scalars;
- time from 0 to 4 ns, strictly increasing;
- SHA-256 `4287d89b964f577fe228200bc6626464eb8c6e3eda71f8839c06b950b70bf9c7`.

The fully finite retained raw structure does not retract or explain the native diagnostic line. It records the values written to the selected raw vectors; the stamp diagnostic observes an internal contribution and accumulator during model loading.

## Deck and source reconstruction

`tb_p1_cml_div2_front_tran_v5.public.cir` differs from the executed private deck only by replacing the private PDK installation root with the literal `$PDK_ROOT`. Substituting the private execution root for that literal rehydrates the 1,648-byte executed deck byte-for-byte at SHA-256 `46e7f223c140769ddbb1f503200caf463bccb395c6f117c39873a600170076fa`.

Applying `NGSPICE46-VBIC-VRTH-ORIGIN-DIAGNOSTIC-V2.patch` to official ngspice 46 `vbicload.c` yields `vbicload_origin_diagnostic_v2.c` at SHA-256 `b3abd28a43ee30204673eb1ea6f6fd5de0b049e2e03de168b25b94a2f86e2dcf`. Applying `NGSPICE46-VBIC-TEMPNODE-STAMP-DIAGNOSTIC-V3.patch` to that retained base yields `vbicload_stamp_diagnostic_v3.c` at SHA-256 `ee6b2aa917c57a79d1694f885fa9b2ac593c5750da92b910ed2bae1eacdb27c9`. Full identities are in `SOURCE-IDENTITIES.tsv`.

## Manifest boundary

`PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive. No executable, credential, cookie, private reasoning, raw prompt, transcript, private deck, private build log, or unrestricted log is included.
