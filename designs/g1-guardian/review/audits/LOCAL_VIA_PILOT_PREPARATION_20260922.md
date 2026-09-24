# Two local via pilots: bounded paired extraction

The two authorized pilots passed geometry identity, bounded KPEX, matrix reduction and all 16 capacitor-network AC comparisons, plus the 6/3.5 fF synthetic controls. [Results](priority-via-local-pilots-20260922-r1/summary.json) and [frozen contract](priority-via-local-pilots-20260922-r1/contract.json) preserve exact inputs and boundaries. Transistor-level dynamic acceptance, full-route RC and current-margin qualification are **not run** for these two sites. Tools: pinned KLayout 0.30.9, KPEX 0.3.12 and ngspice 46; unchanged PDK revision 84374023ee8b4b126bebbba67fcbada0a9c0ff0b.

| Site | Parent actual-fill load, floating / grounded (fF) | Candidate-minus-parent, floating / grounded (fF) |
|---|---:|---:|
| Stage 4, remote clock | 1.671013324 / 1.773161354 | +0.045962249 / +0.052429460 |
| Stage 19, T2F VDD | 2.376755435 / 2.389965753 | +0.168373813 / +0.171273630 |

Finite Schur charge residual and absolute AC agreement were each required to be ≤1e-25 F. The completed batch wrote 1,664,636 bytes and its bounded children totalled 48.82 seconds. These measured runtimes/output sizes are not guarantees for other neighborhoods. Together with the separate three-stage clock interval, local coverage is 5/21 changed stages, not 21/21.

The exact geometry sources are the SENSE parent `build/scratch/sense-route-remedy-20260922-pinned-r1/g1_chip_top.gds` (SHA-256 `af9ac30034c8c11e09d1f24f732f3476c5653fb95eaa0b67f214c2e14c56f76d`) and priority21 candidate `build/scratch/priority-via-remedy-20260922-r1/g1_chip_top.gds` (`04fb6443010bed31595974cca636a9dbd292fda47f0cd45507688f05b1c9a7d8`). Original files must remain unchanged.

| Pilot | Priority21 stage | Net / transition | 12×12 µm clip bounds |
|---|---:|---|---|
| Remote clock | 4 | cmp_clk, Via3 at (965.76,630.42) µm | x959.76–971.76, y624.42–636.42 |
| T2F feed | 19 | VDD, TopVia2 at (630,909.46) µm | x624–636, y903.46–915.46 |

The candidate manifest specifies exact retained/added cut and landing rectangles. The preparation helper requires every changed rectangle inside its clip. These are two of the 18 stages missing from the completed clock-interval paired extraction, not a claim covering all remaining stages.

`prepare_local_via_clip.py` first builds an actual seven-metal/six-via network without label joining. Its target must match every recorded route-via anchor for the named net. Every clipped drawing polygon is independently associated with that full-layout physical network; fill is separate. Each clipped conductor receives a unique label, including multiple disconnected-in-clip pieces of the same target net. The source/clip identities, target anchor matches, each polygon label/group and physical-net ID are saved. Every exported layer must match the exact clipped source region by XOR. Only isolated output clips may be written, never canonical or source GDS.

`analyze_local_target_cap.py` rejects malformed/duplicate/nonpositive capacitor records, unknown extracted labels, missing target labels and inconsistent target/context aliases. It builds the full nodal capacitance matrix. Other drawing nets/substrate are grounded as a declared diagnostic boundary. Floating-fill charge is eliminated by a Schur complement. For proven target-net pieces, the declared ideal outside-clip connection holds all those pieces at the same voltage, giving `C_target = 1ᵀ C_reduced 1`. This is an electrical boundary assumption backed by actual full-net membership, not a claim that disconnected clipped pieces physically join inside the window.

Prospective validation before accepting any pilot result:

- A synthetic multiple-target-piece case must give 6 fF with fill grounded and 3.5 fF with fill floating: target-to-fill capacitors 2/3 fF, fill-to-ground 5 fF, target-to-ground 1 fF, and an internal target-piece capacitor 7 fF that must cancel under equal target voltage.
- Each parent/candidate, no-fill/actual-fill, grounded/floating-fill matrix reduction must independently agree with a one-frequency ngspice capacitor-network calculation within 1e-25 F; finite vectors and explicit completion are required. No transistor model or design card changes are involved.
- All extraction/KPEX children retain 120-second limits. Output growth for the two-pilot batch is at most 128 MiB, with a fresh gate before launch. Parser, target-identity, charge-balance, completion, numerical-comparison or output-limit failure stops expansion; no automatic wider window or longer watchdog.

Isolated outputs are `review/audits/priority-via-local-pilots-20260922-r1/{remote_clock,t2f_vdd}/{parent,candidate}/`. Paired changes describe target ground-equivalent load under both fill boundaries, not actual operating current, signal coupling to a specific aggressor, full-route RC, convergence or dynamic acceptance. Grounded context, ideal outside connections, omitted device/diffusion/depletion capacitance and unknown source/current partition remain explicit limitations. Original wide-IPTAT timeout, context-convergence failures and full-IO failure remain unchanged.
