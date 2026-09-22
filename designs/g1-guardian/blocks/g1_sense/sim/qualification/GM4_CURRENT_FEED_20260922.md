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
