# C79 portable AC evidence package

This directory is a self-contained, portable copy of the C79 portable staging run:
the C45 and C75 sources, the portable deck (C76 content with ONLY the two include
operands made local), the run's own OP/AC raws, its log/stdout, and the facts,
bindings, verifier and checksums. **No absolute paths, no session IDs, no secrets,
no prompt text** — the package is path-scrubbed and self-contained (relative paths
only).

## Contents (12 files)

1. `C45-V1-SOURCE-p1_top_hier_v3-no-bleed-wrapped-damp35-ls-hbtv-nx4el5.spice` —
   a **path-scrubbed derivative** of the executed C45 source (`102f2a9d…`): exactly
   the nine xschem `** sch_path`/`** sym_path` provenance comment lines replaced by
   neutral comments; every electrical line byte-identical. The deterministic
   noncomment electrical-line hash (`d050778a…`) is verified equal to the original;
   the original/public hash is bound as provenance in `BINDINGS.json`/`FACTS.json`.
2. `C75-V1-SOURCE-p1_hybrid.spice` — byte-identical copy of the 12-pin hybrid source
   (`cd475e71…`).
3. `C76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.cir` — the portable deck
   (`646ca890…`): the native C76 deck (`3beb35b7…`, bound as provenance ONLY) with
   exactly the two `.include` operands made local; every other byte preserved.
4. `c76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.op.raw` — the run's OP raw (20×1 real).
5. `c76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.raw` — the run's AC raw (21×201
   complex, finite, monotone).
6. `c76-V1-run.log` — the run's full log (all native warnings preserved verbatim).
7. `c76-V1-run.stdout.log` — the run's console copy (identical content).
8. `README.md` — this file.
9. `FACTS.json` — the 40 measured scalars, the literal warning counts, the raw
   dimensions, the claims scope, the derivative scope, and the correction note.
10. `BINDINGS.json` — the bound SHA-256 of every file plus the provenance hashes
    (the original C45 `102f2a9d…`, the noncomment electrical-line hash, the native
    C76 deck/raws/log, the C46-V3 basis).
11. `verify.py` — the fail-closed verifier (no forbidden strings, exact set/hashes,
    raw/log/facts, derivative scope, the two local includes, the portable deck
    hash).
12. `SHA256SUMS` — SHA-256 of the other 11 files.

## Correction note (C79 review, preserved)

The portable raws differ from the native C76 run's raws **only in the header lines**
(Date/Command). The logs differ in the warning interleave **order** and in the
clobbered-line **location/content**, while the **literal counts and the prefix
multiset match**. This evidence is therefore **not "header-only"** (raws) and
**not "content-identical"** (logs) — the raws are payload-identical, the logs are
count-identical with run-dependent interleave order.

## Claims scope (PROVISIONAL)

- The AC experiment evidence is **PROVISIONAL** and **AC-experiment-only**.
- The derivative/hybrid netlists are **PE-reviewed/non-native representations**,
  never native PEX.
- **No bandwidth decision, no loading gate, no PEX/P1/pass/signoff claim.** P1 open.

## Reproduce

From this directory (relative paths only): `ngspice -b C76-V1-AC-TRACKPHASE-HYBRID-CANDIDATE-ONLY.cir`
after the embedded fail-closed wrapper's absence checks; then `python3 verify.py`.
