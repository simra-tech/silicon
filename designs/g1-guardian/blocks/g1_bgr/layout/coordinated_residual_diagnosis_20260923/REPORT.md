# Redundant DVBE common-routing cuts

The additive26-cut candidate improved the **simulated, conditional** nominal
VREF by12.397999083mV relative to its supply-routing parent. It did not close
physical/electrical qualification: residual versus the identical zero-metal
source is **−1.152412482mV**. No acceptance tolerance was changed.

| Conditional27°C result | Supply parent | Redundant-cut candidate |
|---|---:|---:|
| VREF | 1.031909807V | 1.044307806V |
| VREF minus original zero-R1.045460219V | −13.550412mV | −1.152412mV |
| Whole DVBE metal voltage span | 7.431992mV | 5.778969mV |
| Whole VDD metal span | 5.983173mV | 6.190229mV |
| Whole VSS metal span | 8.649721mV | 8.947366mV |
| Supply current | 299.980592µA | 310.360281µA |

All192 DVBE emitters relative to XR16.2 span3.326730–5.615066mV after
the change, versus5.058904–7.273616mV before. All24 reference emitters relative
to XR16.1 span2.031205–3.295023mV. These are actual split-terminal observations,
not an inferred nonlinear benefit from a fixed-current network.

The change adds parallel common-routing Via2/3/4 paths around local y143µm
and enlarges the lower x203/y18.46µm arrays. All old cuts remain;26 genuinely
new cuts are distinguished from four reused lower cuts. Nine ports,420×354µm
footprint, native device positions, source586 and all model cards remain held.
The candidate GDS identity is
`f4d14755511ec73220c3afdcd211ee6547e0eb025d4615a30a4919c7d0e819c7`.

## Evidence and limits

| Check | Status |
|---|---|
| Native/source/55-net ownership, seven star cuts, exact additive XOR | Passed |
| Standalone stock main and maximal DRC | Passed, zero;44.530s combined wrapper |
| Strict standalone stock LVS | Passed;32 combined devices,24 nets,9 pins;6.748s |
| All336 source MOS junction A/P | Passed |
| Current rerouted full-parent9a52 source-owned clearance | Passed;102.827s;no foreign capture or250nm proximity |
| Complete KPEX/LEF positive networks and independent saved solves | Passed;42678 positive edges,33433 nodes each |
| Exact zero-R OP | Passed;original OP bytes,2842 parameters and3885 raw fields exact;11.747s |
| One matched KPEX nominal OP | Passed numerical/source controls;488.190s;3355 points/33433 nodes finite |
| All1036 stationary model terminal accounting | Completed;max nonreference KCL1.049755e−13A;max device terminal sum8.429468e−15A |
| Exact numerical maximum principle | Failed;1.221245327e−15V excursion retained, no tolerance waiver |
| Full physical substrate/contact/model-plane qualification | Not run/unresolved |
| LEF nonlinear OP, new capacitance coverage, PVT/startup/stability/MC | Not run |
| New overlay fullchip integration and affected fullchip checks | Not run |
| Canonical source/model/rule mutation or measured-silicon claim | Not applicable |

The stationary R3CMC proof and four negative controls establish zero modeled
DC NC branch current for the15 rhigh and384 rppd instances. NC voltage still
affects body current; all399 physical substrate potentials remain unqualified
ideal-VSS assumptions. Native M1 resistor-head/reference-plane overlap is
unresolved. No generic contact resistance or VBIC intrinsic resistance was
added/subtracted. All1036 compact-model calls and329 historical capacitors are
retained; the model-only KCL completion does not qualify those boundaries.

Original failures remain: y141 bridge captured VBE/VD2; the first y143
eight-cut candidate passed local stock checks but failed full-parent220nm
fill spacing; several CPU preflights deferred without launching; the first
zero invocation omitted the required image-identity prefix and failed before
simulation. The corrected six-cut upper arrays passed current-parent clearance
without deleting fill. Dynamic gmin stepping completed; no simulator errors.

## Built against and reproduction

Pinned IHP PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout0.30.9,
ngspice46 and image `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`
were checked by source/runtime controls. Source SHA586ffb58, seed44001,
3.3V,27°C,r4=0,IPTAT source1V and1pF load match the original OP fixture.
Post-DC parameter parity is not run for these OP-only leaves.

Scripts in this directory preserve source-bound screen/build/stock/context,
positive-network preparation, exact-zero/nominal and saved-analysis commands.
Fresh gates include RAM, separate home/bulk storage and inodes. The original
launches use one allocated CPU and reservation-only rootless memory; corrected
successor gates use a fixed30-second observer under the owner60% policy.
Evidence records exact commands and hashes; host-specific quota details stay
outside public Git. No extracted geometry is used to rewrite a golden device
parameter or calibrate the canonical electrical source.
