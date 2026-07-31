# Candidate V5 VBIC Vrth-Origin Diagnostic Evidence V1

## Scope

This package preserves one frozen 4 ns Candidate V5 transient performed with a read-only ngspice 46 VBIC origin diagnostic. It publishes the exact V2 patch and patched source, the Candidate V5 netlist, a path-sanitized deck, native log, full binary raw dataset, and provenance tables. The diagnostic executable is identified but deliberately not included.

Engineering status: **UNKNOWN**. This is diagnostic evidence, not a specification result. It makes no root-cause, circuit-improvement, signoff, or tape-out-readiness claim.

## Strongest supported result

The native log contains exactly one origin marker:

```text
[VBIC_VRTH_ORIGIN_DIAGNOSTIC] Instance: q.xdiv2.xqs_comp_s.qnpn13g2 | Origin: 8 (tempnode_load_line_484) | OriginScalar: -nan (isnan=1) | Vrth(current): -nan (isnan=1) | Vrth(stored): -0x1.802fd62bf6888p+8 (isnan=0)
```

The hierarchical device maps to Candidate V5 instance `XQS_COMP_S` at netlist line 91. The V2 patch defines Origin 8 at the load-path assignment whose source expression is `*(ckt->CKTrhsOld + here->VBICtempNode)`, before the unchanged `DEVlimitlog` call.

Therefore, the strongest result is only: **XQS_COMP_S Origin 8 read NaN from `CKTrhsOld` `VBICtempNode` before the limiter, while stored `Vrth` was finite.** This does not identify where the circuit-vector value became NaN, why it became NaN, or a physical unit. Root cause remains unresolved.

## Execution record

`EXECUTION-HISTORY.tsv` separates a rejected foreground request from process execution. The harness rejected that request before spawning a process, so it was not an ngspice invocation. One tracked background process then made exactly one actual ngspice invocation. It exited successfully, wrote the retained raw dataset, and produced a log containing `ngspice-46 done` and `NGSPICE_EXIT=0`. There was no retry.

The executable identity is SHA-256 `a70433fb7936a2217e98b87cf37b41fe2a46543c5245da9a94c0929c157d93e9`; the binary is not published.

## Raw evidence

Direct parsing of `raw_tb_p1_cml_div2_front_tran_v5.raw` gives:

- 429 variables and 2,284 points;
- 979,836 total IEEE-754 doubles;
- 979,836 finite and 0 non-finite scalars;
- time from 0 to 4 ns, strictly increasing;
- SHA-256 `f8cf21033cd8110c2aa931927e98afc0c13820aa23c07556e9d18c4deead608b`.

The raw dataset is marked binary in `.gitattributes`.

## Comparison boundary

The deck SHA-256 (`46e7f223...`) and Candidate V5 netlist SHA-256 (`689d4bee...`) match the retained first-NaN diagnostic run. The output raw SHA differs: prior `c2f70547...`, this run `f8cf2103...`. The stored finite operand also differs in low-order hexadecimal bits: prior `-0x1.802fd620a7987p+8`, this run `-0x1.802fd62bf6888p+8`.

Those are observations only. They are not treated as an input failure, circuit improvement, regression, or explanation. The run is inconclusive for byte-level output reproduction, and engineering status remains UNKNOWN.

## Deck and source reconstruction

`tb_p1_cml_div2_front_tran_v5.public.cir` differs from the executed private deck only by replacing the installation-specific PDK root with the literal `$PDK_ROOT`. Substituting the execution root for that literal rehydrates the 1,648-byte private deck byte-for-byte at SHA-256 `46e7f223c140769ddbb1f503200caf463bccb395c6f117c39873a600170076fa`.

The diagnostic source can be reconstructed from the official ngspice 46 `vbicload.c` identity in `SOURCE-IDENTITIES.tsv` by applying `NGSPICE46-VBIC-VRTH-ORIGIN-DIAGNOSTIC-V2.patch`. The result must match `vbicload_origin_diagnostic_v2.c` at SHA-256 `b3abd28a43ee30204673eb1ea6f6fd5de0b049e2e03de168b25b94a2f86e2dcf`.

## Manifest boundary

`PUBLISH-MANIFEST.tsv` covers every published payload except itself, whose self-hash would be recursive. No executable, credential, cookie, private reasoning, or unrestricted transcript is included.
