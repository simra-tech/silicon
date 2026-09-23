# SENSE terminal-boundary diagnostic contract

This is a source-held diagnostic branch, not an adopted layout, complete PEX,
or electrical qualification. The canonical gm4/comp3 source is unchanged
(`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`).
The r8 native GDS is unchanged
(`8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7`).

## Observed boundary

The independent native inventory has 58 logical MOS devices, 835 channels,
893 diffusion strips and 48 shared strips. The 541 source-terminal slots are
232 MOS, 294 resistor (including 98 BN), six MIM and nine external ports.
There are 835 gate contacts and 18,549 diffusion contacts. All original gates
are contacted on one end only, 330 nm beyond the Active edge. Counts of cuts
must not be confused with numbers of gate-contacted ends.

The pinned PSP wrapper sets NGCON=2. Its four external terminals do not expose
independent per-finger injection ports. Internal gate, source/drain and body
resistance networks must remain present. The installed equations and the
[PSP103.8 manual, section 3.4](https://www.cea.fr/cea-tech/leti/pspsupport/Documents/psp103p8_summary.pdf)
make gate resistance depend on NGCON, including a squared-denominator term.
Interpreting this as a one-ended versus two-ended distributed gate boundary
is an engineering inference from that equation, not an independently obtained
foundry applicability statement. The wrapper XGW default is 100 nm; the
native contact-center distance is 330 nm. Their physical correspondence and
RGO/contact ownership are unresolved. A second end alone does not close them.

## Geometry-only prototype

The prospective proposal adds, at each of the 835 opposite gate ends, a poly
head, 0.16 um contact, 0.30 um M1 landing and 0.16 um M1 gate-center bridge to
the original gate contact. No Via1 or M2 is added: on complementary input
arrays the opposite M2 bus can belong to the other input. No Active,
channel, diffusion, primitive instance, source parameter or logical port may
change. Source NGCON2 and physical mismatch identity remain unchanged.

The completed in-memory screen passed all 134 source nets and retained 229
physical components, with zero channel/diffusion XOR and zero conservative
180 nm foreign-net poly/M1/contact violations. It saved no candidate GDS.
Saved prototype acceptance requires exact original-plus-declared-additions
polygon equality, unchanged recursive texts and instance hierarchy, 835
two-ended covered contacts, an independent source-native W/L/ng/default-A/P
and matching-centroid audit, unchanged source-derived CDL, then stock main,
maximal and strict LVS. Stock extracted A/P must be audited separately:
the existing 51 failed per-node annotations are not waived by LVS Match.
Main/maximal children are bounded at 360 s; LVS at 120 s. Failure stops the
chain. Complete field coupling/current, zero-R parity, electrical response,
intrinsic applicability and fullchip adoption are **not run** by this gate.

## Distributed terminal representation

An implementable diagnostic keeps one original model instance and its exact
source path and mismatch draw. An ideal multiport adapter imposes terminal
voltage `u = sum(w_i*v_i)` and physical-port current `i_i = w_i*I`, with
nonnegative weights summing to one. Signed KCL and instantaneous power are
then conserved, including displacement current. Exact-rational algebra
controls pass, but simulator syntax/runtime controls are **not run**.

Fixed weights are a declared homogenization assumption, not an exact local
nonlinear finger solution. No weight or single injection point is selected
for the real device. A separate positive-resistance, fixed-current mesh can
bound every linear voltage observation over all simplex allocations using
each terminal's minimum and maximum transfer coefficient. This bounds only
that fixed linear problem, not nonlinear gain or calibration. Shared strips
must aggregate their owners' signed currents at the same physical conductor.

Before use, require both literal reverse restoration of all 159 original
primitive lines and an explicit adapter zero-R simulation control with the
full 11,512 parameter fingerprints, 27 OP rows and original waveform parity.
Do not silently substitute a collapsed renderer for the explicit adapter
control or waive its solver-order/rshunt failures. Keep the original PSP
internal resistance and all MIM compact models. Body/BN spreading and MIM
electrode ownership remain unresolved. No source/model/finger split, fitted
junction parameters, tolerance change or rule-deck change is authorized.
