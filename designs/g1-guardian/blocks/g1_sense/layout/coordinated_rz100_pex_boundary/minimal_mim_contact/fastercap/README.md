# Native CMIM FasterCap diagnostic

This is a diagnostic on the unchanged, LVS-passing 7 × 7 µm native CMIM
coupon. It does not establish macro PEX or authorize electrical adoption.

`probe_raw_coupon.py` checks pinned input, technology, and binary hashes,
generates the native three-dimensional dielectric/conductor geometry through
the installed KPEX interface, and calls the installed FasterCap 6.0.7 solver
directly. This deliberately bypasses the downstream KPEX netlist writer,
which failed in the earlier stock run. No PDK, deck, model, GDS, CDL, or
material coefficient is changed. `audit_raw_coupon.py` independently checks
saved geometry and the unmodified iteration matrices.

The default 5% auto-tolerance run completed in 67.51 s. Its three conductors
were virtual `VSUBS`, CMIM bottom, and CMIM top. The generated bottom/top
horizontal faces were 67.24/49 µm², separated by 0.04 µm. The final raw
Maxwell matrix, in farads, was:

```
 5.22219e-15  -1.35960e-15  -3.38300e-16
-1.37331e-15   8.18665e-14  -8.01945e-14
-3.89662e-16  -8.00953e-14   8.07838e-14
```

The solver met its configured 5% weighted auto criterion, but the last two
iteration matrices changed by 2.54%, 8.39%, and 2.45% for the three averaged
positive mutual capacitances, respectively. Final reciprocity differences
were 1.00%, 14.11%, and 0.12%. Thus the raw matrix is **not quantitatively
qualified** against a 1% mutual-change/reciprocity criterion. The physical
reference plane of virtual `VSUBS`, passivity under a converged matrix, and
intrinsic/extrinsic capacitance ownership remain unresolved.

A distinct run with 1% auto tolerance and identical generated geometry hit
the 300 s wall bound before a matrix was returned. The solver's redirected
stdout was empty due to buffering at termination; its stale in-progress
summary is not a success receipt. The bounded-tool receipt records timeout.

Output-only `stdbuf` and PTY adapters were checked on separate default-5%
control runs. Each regenerated bit-identical geometry, returned ten matrices,
and matched the unwrapped final matrix exactly. The PTY adapter was then used
for a 1% run with a 4 GiB address-space limit. FasterCap exited 71 after
reporting out-of-memory at 4,082,162 KiB allocated, retaining 12 raw matrices.
Its last reported weighted auto difference was 1.59182%; last-two-iteration
mutual changes were 4.27%, 9.80%, and 1.59%, and reciprocity differences
were 4.18%, 15.86%, and 0.004%, respectively. The symmetrized last matrix
was positive definite, but this does not qualify the unconverged data.
`audit_failed_refinement.py` preserves and checks these partial results.
No macro scaling or electrical adoption was attempted.

With a fresh resource gate and a 16 GiB address-space limit, one further
unchanged-geometry 1% run completed in 368.35 s, reporting 4,247,218 KiB
allocated. It returned 13 matrices and 135,661 refined panels. The final
weighted auto difference was 0.488677%, and the symmetrized matrix was
positive definite. Nevertheless, the last two iteration matrices changed
by 2.47%, 4.70%, and 0.487% for VSUBS–bottom, VSUBS–top, and bottom–top
mutual capacitances; raw reciprocity differences were 2.76%, 15.31%, and
0.023%. The default 5% and tighter 1% matrices differ by 3.33%, 14.24%,
and 4.38% for those same pairs. Thus the requested 1% mutual-change and
reciprocity criterion is **not met**, despite the solver's own auto stopping
criterion. No positive mutual term is silently omitted to make a subset pass.
The converged reference-plane interpretation and intrinsic/extrinsic
ownership remain open.

The installed FasterCap 6.0.7 help and pinned KPEX CLI both support the
Galerkin `-g` option. A single otherwise identical 1% Galerkin run completed
in 287.91 s, reporting 1,913,336 KiB allocated, with exact generated-geometry
parity. Its 12-matrix final auto norm was 0.596%, and its symmetrized matrix
was positive definite. Raw averaged mutual capacitances were 1.32254 fF
(VSUBS–bottom), 0.4432085 fF (VSUBS–top), and 76.3296 fF (bottom–top).
The corresponding last-step changes were 3.17%, 5.36%, and 0.591%; raw
reciprocity mismatches were 4.81%, 19.48%, and 0.0786%. Relative to the
1% collocation result, the Galerkin mutuals changed by 0.011%, 4.23%, and
0.589%. Thus changing the numerical scheme does **not** qualify all three
mutuals to 1%; notably the small substrate terms remain poorly conditioned.
No substrate term was discarded or silently bound to ground.

Saved raw output and audits are under the local results root as
`sense-rz100-fastercap-raw-coupon-20260923-r2` (default) and `...-r3`
(tight timeout); `...-r5` and `...-r6` are output-adapter controls, and
`...-r7` is the 4 GiB-limited refinement, and `...-r8` is the completed
16 GiB-limited refinement; `...-r9` is the Galerkin comparison. `audit_v2.json` in each completed run records the
same explicit 1% qualification test. Corresponding bounded-tool receipts
are under the private verification directory. These paths are local evidence
locations, not portable dependencies.
