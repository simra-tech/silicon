# Historical preparation checkpoint: pure-fill representation control

Handoff review, 24 September 2026: the preparation sequence below is retained
as a historical record, not a current execution queue. `current_bindings.py`
subsequently received concrete geometry, proof, and context hashes; references
below to pending preparation or `NOT_PREPARED` describe the earlier checkpoint.
Inspect the corresponding source-bound result records for acceptance. Populated
bindings alone do not establish full-chip LVS or electrical qualification.

No helper in this directory establishes full-chip LVS acceptance yet. Original
300-second preparation timeouts and the first small saved-record failure remain
retained. The completed earlier checkpoint is separate: 207 files, 1,874,746 bytes.

Execution order, one CPU with a fresh coordinated resource/RAM/storage gate:

1. Small corrected control **passed** 11.025 seconds; summary `0fe02fbd…`.
   The earlier synthetic unsaved top-cell property loss is separately failed.
2. Full dcca/R62 representation proof **passed** 52.738 seconds, 16,738 arrays;
   GDS `8cd255c0…`, proof `4bb4ce88…`. Original two 300-second failures retained.
   Do not rerun these completed controls.
3. Their hashes are now frozen in `current_projection_bindings.py` and
   `current_bindings.py`. The first is an immutable generation dependency;
   only the second receives future GDS/proof/context output hashes. This avoids
   mutating a hash-bound generation input after the candidate is created.
4. `flatten_current_fill.py --output <results-root>/current-purefill-flat-20260923-r1`
   (300 seconds). It binds current `1c953318`/reader `94e50a2a`, requires exact
   qualified fill templates/zero-device witnesses, all native definitions,
   full affected-layer XOR and saved inverse. On pass freeze GDS/proof hashes
   in `current_bindings.py`.
5. `derive_current_context.py --output <results-root>/current-purefill-context-20260923-r1`
   (60 seconds). On pass freeze context hash.
6. `run_current_lvs.py --output <results-root>/current-purefill-native-lvs-20260923-r1
   --resource-gate <container-visible-gate> --minimum-budget <current-coordinated-budget>`.
   Exactly one 600-second native engine run; allow declared kill grace and
   the existing 60-second strict parser stage (outer bound 690 seconds).
   Reserve 16 GiB RAM and 2 GiB bulk growth; memory is not cgroup-enforced.

The prior R62 causal stock test is **not run/deferred** to prioritize current
acceptance. No causal speed benefit may be claimed merely from a later pass.
All `NOT_PREPARED` hashes intentionally fail closed. The final wrappers have only
AST/static preparation checks; runtime tests are **not run**. They use unchanged
installed stock rules, retain all three original source dummies, and do not
promote warning matches. Actual native interface/dummy comparisons remain
separate required gates if the stock database completes with those known issues.
