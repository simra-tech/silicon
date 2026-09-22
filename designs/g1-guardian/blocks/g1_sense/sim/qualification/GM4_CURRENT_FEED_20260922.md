# gm4 current observations for physical feed sizing

The completed gm4/compensation-3 schematic screen contains 100 independent
draws and 3,600 OP rows, including the temperature return. Its largest printed
testbench supply current is simulated **1.53392 mA**, at seed 41093, 125 C,
common mode −0.1 V and shunt 50 mV. The exact row is
`t2_c-0.1_s0.05` in
[the fourth 80-sample cohort summary](mc-gm4-comp3-screen80-b4-20260922-a/summary.json).

This is not directly the SENSE VDD-pin current: the testbench also draws its
ideal PTAT current from VDD (`Iib vdd iptat`). The
[same seed deck](mc-gm4-comp3-screen80-b4-20260922-a/seed41093.cir)
sets that current to 5.478459103781443 µA at 125 C. Subtracting that known
testbench load gives **1.528441540896219 mA inferred SENSE VDD-pin current**.
The extra digits reflect arithmetic, not increased precision of the printed
1.53392 mA datum. These are OP observations, not transient peaks or a proved
worst-case envelope.

The older approximately 1.065 mA integrated current observation used a different
SENSE source and cannot bound gm4. The current canonical gm4 source is
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.

Separate copied-source current controls split the VDD supply of XOTA, XBUF and
XREF using zero-volt probes and an independent total SENSE supply meter. They
do not change canonical devices. However, the inherited 1 TΩ `rshunt` adds
conductance at each new monitor node, so source-text restoration alone does
not prove electrical equivalence. The original room/hot OP controls completed
all 11,512 parameter checks but **failed** the prospective raw 1 pA KCL check
(approximately 3.3 pA residual). Their exact original-voltage comparisons also
**failed**; maximum OP differences were 14.8 pV and 75.3 pV. These failures
remain separate from any later explicitly accounted current observation.

## Representative transient VDD observations

Two separately declared instrumented runs completed at 25 C and 125 C,
respectively, in 403.421 and 390.270 seconds. Each preserves all 11,512 model
parameters and 27 legacy anchors. Their fixed conditions are seed 73001,
nominal process, 3.3 V, common mode 0 V, shunt 25 mV, codes 135/151,
5 MHz comparator timing and a 1.02 µs DC-initialized transient. They are not
power-on startup simulations or a statistical/corner current envelope.

The four saved monitor voltages equal 3.3 V throughout both waves. Thus their
added shunts draw 13.2 pA in total. The top monitor's shunt is inside the total
meter and outside all three branch meters; each other shunt is inside its own
branch meter. Subtracting these explicitly measured contributions gives:

| VDD boundary | 25 C sampled peak (mA) | 125 C sampled peak (mA) | 25 C last-200-ns mean (mA) | 125 C last-200-ns mean (mA) |
|---|---:|---:|---:|---:|
| Entire SENSE | 1.115180 | 1.509169 | 1.115054 | 1.509042 |
| XOTA | 0.419924 | 0.565465 | 0.419798 | 0.565335 |
| XBUF | 0.328354 | 0.452470 | 0.328348 | 0.452465 |
| XREF | 0.367026 | 0.491344 | 0.366908 | 0.491242 |

The accounted KCL residual stays below 9×10⁻¹⁹ A, passing the original 1 pA
residual bound. The **raw KCL check remains failed** at approximately 3.3 pA.
Original 18-column decoded-byte, numeric-row and time-grid equality checks
also **failed**. Interpolating the original reference onto instrumented times
gives maximum voltage differences of 0.8223 µV at 25 C and 5.905 nV at 125 C;
these are observations, not replacements for failed exact equality. Actual-edge
and legacy late-three decision policies both give LOW/LOW in both runs,
agreeing with their original fixed-code references; this is not calibration
accuracy acceptance.

[Portable evidence](../../../g1_trip/sim/qualification/portable_evidence/sense-current-20260922)
includes all six controls, including the two original failures, exact output-only
OP replays, declared source/deck differences, full parameter vectors, runtime
identity and raw-wave hashes. Two preliminary observation preparations failed
before simulation due a preparer path error; their `-a` directories remain
archived. A launcher working-directory error likewise occurred before Python
or ngspice started and did not overwrite any simulator run.

VSS envelopes, individual source-contact currents, a worst-case VDD bound,
and hot lifetime/electromigration qualification: **not run** by this record.
The physical remedy's exploratory 2 mA sizing and 50% engineering utilization
target are not a qualified current bound or hot lifetime rating.

## Eleven combined source/body stages

Four further copied-source controls (room/hot OP, then room/hot transient)
passed all 11,512 parameters, 27 anchors and the explicitly accounted 1 pA KCL
bound. The transient runs completed 1.02 µs in 400.358/391.248 seconds.
The source copy is
`3a0958fb699feda1686eb0bf7c4fc045e3a0100a828fa911e6f7da8ec2d4f6bc`;
its exact restoration to the prior macro-instrumented copy is checked before
simulation. The same representative conditions above apply.

These probes combine both rail-connected source and body terminals of each
listed MOS. They therefore observe a signed device supply-stage current,
**not** an individual physical source contact or body/well-tap current. Separate
physical islands and possible source/body cancellation prevent using this table
as an individual contact-capacity qualification.

| Combined stage | 25 C sampled absolute peak (mA) | 125 C sampled absolute peak (mA) |
|---|---:|---:|
| XOTA XM11, VDD | 0.072623 | 0.105366 |
| XOTA XM14, VDD | 0.072495 | 0.105233 |
| XOTA XMT, VDD | 0.094614 | 0.122045 |
| XOTA XM20, VDD | 0.145388 | 0.187847 |
| XOTA XM3, VSS | 0.119726 | 0.166221 |
| XOTA XM4, VSS | 0.119951 | 0.166382 |
| XOTA XM21, VSS | 0.122969 | 0.165931 |
| XBUF XM11, VDD | 0.040388 | 0.062372 |
| XBUF XM14, VDD | 0.040158 | 0.061970 |
| XREF XM11, VDD | 0.041189 | 0.063192 |
| XREF XM14, VDD | 0.041022 | 0.063012 |

The remaining VDD current after subtracting the two selected combined stages
from each accounted macro branch has sampled peaks 0.247828/0.328144 mA
for XBUF and 0.284870/0.365186 mA for XREF (room/hot). This remainder includes
all remaining rail-connected contributions; it is not a per-contact allocation.

All twelve added VDD monitor voltages are measured at 3.3 V, giving 39.6 pA
total added shunt current. The three added VSS nodes are measured at zero.
Accounted KCL residuals are below 9×10⁻¹⁹ A; raw KCL still **fails** at
approximately 3.3 pA. Both original-voltage byte/numeric/time-grid comparisons
**fail**. Maximum reference-interpolated voltage differences are 0.9052 µV
and 7.014 nV; interpolation does not replace exact equality. Actual-edge and
legacy late-three policies agree on LOW/LOW in both runs, without an accuracy
or physical-adoption claim.

[Four-control portable evidence](../../../g1_trip/sim/qualification/portable_evidence/sense-supply-stage-20260922)
preserves declared source/deck differences, all parameter vectors, the failed
exact comparisons, runtime/tool/model identities, and bulk-wave hashes.
Separate source/body currents, buffer VSS groups and the resistor-bank VSS
current are **not run** in this eleven-stage fixture; their new independent
fixture must qualify separately.

## Separately metered external source and body terminals

A separate four-control fixture has now completed room/hot OP and 1.02 µs
transients. Its 102 zero-volt meters observe each rail-connected MOS external
terminal individually, each OTA compensation-resistor substrate, and one
explicitly signed resistor-bank VSS aggregate. The latter contains 96 original
source-call pins, not 96 individually measured currents. The MOS source and
body meters are distinct, so their individual extrema remain visible even if
their signed sum cancels. This fixture does not infer physical terminal identity
from possibly collapsed OSDI internal-node labels.

The copied SENSE source
`4f7999919b8c14506c5f409d810f0931bdbf63febbb851134fd57a6702385300`
restores exactly to the prior macro-current copy. Canonical devices and model
cards remain unchanged. All four controls pass the original full 11,512-vector
and 27-anchor contracts. The new 54 VDD monitors plus the four prior monitors
are each measured at 3.3 V: 191.4 pA of explicitly added shunt current in total.
All 48 new VSS monitor nodes are measured at zero. Corrected total KCL remains
below 9×10⁻¹⁹ A, and each macro's independent VDD branch-versus-all-terminal
current sum closes within 2.5×10⁻¹⁹ A. Raw top KCL still fails its 1 pA check.

The transients completed in 399.283/395.415 seconds. Representative hot
external **source-terminal** sampled absolute peaks are 0.105365, 0.105232,
0.122045 and 0.187836 mA for XOTA XM11, XM14, XMT and XM20, respectively.
Main VSS-source peaks for XM3, XM4 and XM21 are 0.166221, 0.166381 and
0.165927 mA. The largest separately observed body-terminal peak across all
58 MOS bodies is approximately 30.54 nA at XOTA XM16. All signed extrema and
last-200-ns means, including smaller body currents, are retained in the ledger.

| Signed external-terminal group | 25 C absolute peak (mA) | 125 C absolute peak (mA) |
|---|---:|---:|
| XBUF VSS: XM3/XMB2/XMB4/XMB6 source and body | 0.121521 | 0.167462 |
| XBUF VSS: XM21/XM4 source and body | 0.202115 | 0.280392 |
| XREF VSS: XM3/XMB2/XMB4/XMB6 source and body | 0.120384 | 0.166252 |
| XREF VSS: XM21/XM4 source and body | 0.203040 | 0.281555 |
| Top resistor-bank VSS aggregate | 0.001994 | 0.001952 |

These sums contain only the listed external terminals. Separate physical source
and tap islands must use the individual records, not a signed group sum as a
cancellation-proof capacity bound. VSS was measured directly, never inferred
from VDD. Remaining-buffer VDD groups also enumerate their exact members.

Original 18-column byte/numeric/time-grid comparisons **fail** in both runs.
Reference-interpolated maxima are 0.9739 µV and 7.817 nV; those observations do
not waive exact failure. Both actual-edge and legacy late-three decisions remain
LOW/LOW. The fixtures remain representative nominal-process, fixed-input,
DC-initialized model-level observations, not startup, statistical/corner current
envelopes, physical RC adoption, or lifetime qualification.

[Separate-terminal portable evidence](../../../g1_trip/sim/qualification/portable_evidence/sense-rail-terminals-20260922)
contains all four controls, 102-port mappings, measured monitor voltages,
accounted and raw checks, original exact failures and complete bulk hashes.
