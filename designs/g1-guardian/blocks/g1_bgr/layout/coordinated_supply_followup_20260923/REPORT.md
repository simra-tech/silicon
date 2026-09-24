# BGR supply-routing follow-up

This is an isolated source-held geometry candidate, not an adopted full-chip or
electrical qualification. The preceding conditional collector result retains a
simulated 13.253897 mV VREF difference from its exact zero-resistance control.
That difference is not accepted as closed. The changes and prospective numerical
scope are specified in [CONTRACT.md](CONTRACT.md).

The local candidate is
`e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb`.
The separate filled-chip context candidate is
`b417a132626fd1d0f4cc8162c49449868f33096a8069bc7b90408864a0b0e5de`.
It starts from the exact `ae62bf68` assembled parent, excludes ten identified
generated M5 fill squares (160 µm²), and adds the independently source-owned
cumulative BGR geometry (733.166 µm² summed across layers). Other fill, native
devices, source, ports, functional hierarchy, text and die dimensions are held.
Forward/inverse all-layer XOR and serialized-GDS parity passed.

## Completed evidence and outstanding checks

| Check | Status | Scope |
|---|---|---|
| Three finite VDD M4 widening proposals | Failed | Foreign metal/cut clearance; none implemented |
| Selected M5/pad/16-cut local geometry | Passed | Native parity, 55 nets, seven star cuts, complete added-area ownership |
| Local main/maximal DRC | Passed | Zero markers, unchanged stock rules |
| Local strict LVS | Passed | 32 combined devices, 24 nets, nine pins; all Match |
| All 336 source MOS junction fields | Passed | Exact source-node W/L/A/P audit of all 20 combined groups |
| Unpruned assembled-parent clearance | Failed | Ten real generated-fill conflicts; original result retained |
| Exact ten-fill inventory/removal | Passed | One 560-repetition array; 550 other repetitions retained |
| Pruned-parent clearance | Passed | 3,424 source probes, 55 distinct nets, no foreign captures or 250 nm proximity findings |
| Full-parent main DRC | Passed | Zero markers; unchanged deck, 446.09 s engine / 450.230 s stock wrapper |
| Full-parent maximal DRC | Passed | Zero markers; unchanged deck, 834.74 s engine / 838.723 s stock wrapper |
| Full-parent antenna | Passed | Zero markers; unchanged stock check, 112.558 s |
| Full-parent density | Passed | Zero markers; unchanged stock check, 35.321 s; exact native die boundary |
| Fresh 10,222-terminal/24-port connectivity | Passed | Exact old/new component bijection; five supplies distinct, 22 physical pin identities, no unexpected merges/splits |
| Recomputed positive networks | Passed | Raw 48,946 edges/39,726 nodes; 6,306 exact-zero edges contracted, preserving all 42,640 positive edges/33,420 nodes, 3355 points and 55 nets |
| Exact zero-R OP control | Passed | Original OP bytes, all 2842 parameters and 3885 raw fields exact; 10.514 s |
| Matched nominal conditional OP | Passed | Numerical/source controls; 430.455 s, all 3355 points/33,420 nodes finite; electrical acceptance not established |
| Exact computed maximum principle | Failed | Largest interior excursion beyond sampled-terminal extrema is 1.221245327e-15 V; no tolerance waiver |
| Device-aware full-chip LVS | Not run | Existing source/model-topology failures are not waived |
| PVT, startup, mismatch and complete extracted C | Not run | Outside this conditional nominal diagnostic |
| Name-based physical net joining | Not applicable | No forced joins or ignore hints are used |
| Final adoption | Not run | Candidate remains isolated |

## Conditional nominal result

The simulated VREF is 1.031909806999675 V, **0.296515 mV lower** than the
preceding collector candidate (1.032206321859809 V). It remains 13.550412 mV
below the exact zero-resistance control (1.045460218565099 V). Thus this
supply change does not improve the VREF error, despite reducing the actual
whole-network VDD spread from 7.118961 to 5.983173 mV and VSS spread from
8.947433 to 8.649721 mV. Electrical closure is not established.

The DVBE spread remains 7.431992 mV. All 192 source-bound DVBE emitters are
5.058904–7.273616 mV above XR16 terminal 2; the 24 reference emitters are
1.962510–3.186707 mV above XR16 terminal 1. Simulated supply current is
299.980592 µA. Maximum metal-interior KCL residual is 8.037005405e-14 A;
mapped MOS/HBT point KCL residual is 2.274385023e-14 A. The exact computed
maximum-principle check fails as recorded above, not silently relaxed.

The independently saved comparison passed its source, coverage and parameter
controls. Compared with the original native conditional diagnostic, VREF is
24.234060 mV higher; that historical improvement does not turn the remaining
13.550412 mV difference into an accepted result. LEF-scenario nonlinear OP was
not run. These are conditional simulated numbers, not measured silicon or
qualified terminal-plane/electrical signoff.

## Preserved harness and resource failures

The original full-parent hierarchy query returned child-local geometry; a
two-instance positive/wrong-seed control reproduced it. The exact-flat recovery
preserved every conductor union and exposed the ten genuine fill conflicts.

A later all-local-probe assertion incorrectly treated cluster integers as global
identities. The bounded control establishes 55 distinct `(circuit, cluster)`
identities but only 36 raw integer values in the hierarchical representation.
Its first, over-specific split-net hypothesis failed and is also retained.
The final pruned-parent check uses independently XOR-verified flat geometry for
both local and full-parent ownership; it passed in 188.317 seconds.

The independent final terminal graph passed in 286.118 seconds. Its positive,
split, merge and empty-partition controls passed. Eight unchanged analog-pad
aliases are bound to the original library assignments, not inferred from observed
shorts. Complete source instances and physical port windows are checked; no
device-aware LVS acceptance follows from this conductor-only proof.

A fresh launch gate measured 42 available project CPUs against a stale coordinated
43-CPU floor and correctly did not launch. The coordinator subsequently reconciled
the complete reservation inventory to 41 distinct CPUs. The original failure and
new explicit allocation receipts are separate; no running job was interrupted.

After a later reservation increase to 45, a measured-44 terminal-audit launch was
also correctly blocked; its fresh measured-47 recovery is separate. The first
network preparation passed source junction and 3355-point checks, but the network
runner refused the declared 0.3 GiB output reservation because its unchanged
contract requires at least 2 GiB. No network solver started in that attempt.
The continuation preserves that failure and reuses the passed controls with a
fresh 4 GiB aggregate allowance for the two sequential network scenarios.

The unchanged compact models remain attached at the previously declared planes.
Resistor-head fitted-model ownership, 399 ideal resistor substrate attachments,
historical capacitor attachment and complete resistor external-field coverage
remain unqualified. No resistance is subtracted from a model or fitted to force
agreement. The routing and fill changes also change capacitance; these DC-only
preparations do not imply transient or final-PEX equivalence.
