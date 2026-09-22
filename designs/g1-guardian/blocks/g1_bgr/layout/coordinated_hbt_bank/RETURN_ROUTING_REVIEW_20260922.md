# Full HBT-bank return routing — source/pack review

This is a read-only source/placement calculation, not routed geometry or an
electrical result. Inputs are the exact source586 and pack hashes in the
[preparation contract](PREPARATION_CONTRACT_20260922.md).

The bank has 301 fixed HBTs: 192 E=DVBE, 24 E=VD2, 76 functional E=VSS,
and nine all-ground dummies. The 76 functional grounded emitters comprise
24 XQ56, four XQ60, 24 XQ62 and 24 XQ67. Their return trees must be represented
separately from general guard VSS in a physical-ownership ledger before a
declared common join. These roles do not alter source nets.

## A new worst-row channel

The passed worst-row pilot sent all base taps below their rows and emitter /
distinct collector taps above. Extending those directions literally creates
this demand in the row16–row17 gap (zero-based pack rows):

| Owner | Required horizontal roles |
| --- | --- |
| Row16 upper collector / emitter taps | C2, DVBE, XQ67 emitter return, VBE |
| Row17 lower base taps | B1B, VD2 |
| General substrate guard | VSS |

All six signal/functional-return roles are distinct in this physical ledger.
Even provisionally using only 0.30 µm for every functional return, 0.30 µm
spacing and 0.80 µm for general VSS requires
`6×0.30 + 5×0.30 + 0.30 + 0.80 = 4.40 µm` in a 4.00 µm native-device gap.
This is already over capacity before extra margin, turns or via landing
constraints. Functional current-return widths are not qualified by that
provisional 0.30 µm calculation.

This is a **failed capacity screen for the literal fixed-direction full-width
collector extrapolation**, not proof that the fixed placement is unroutable.
Possible bounded next designs include reversing selected row16/17 escape
directions, moving one ownership role to another routing layer, or proving
nonoverlapping localized collector intervals. Every option needs explicit
terminal / via / neighbor checks. No option is implemented or preferred on
electrical grounds by this report.

Row2 has the same four upper roles, but row3 below-base demand is only VBE,
which is already one of those roles. Reusing one conductor there requires
actual same-source-net connectivity checks; simply counting labels is not a
routing proof. Rows7/11 remain the previously exercised pilot rows, but do not
exercise the new functional grounded-emitter contact variants.

## Trunk demand and precision ownership

Eight electrical HBT source nets plus four separate functional VSS-emitter
roles require twelve physical collector/trunk roles before the star if every
role is taken to a bank-wide trunk. The pilot's six-trunk placement at
`x=190.8 + 1.1×i µm` cannot simply be extended to twelve: the final center
would be x=202.9 µm, beyond the planned bank/MOS corridor boundary at x=202.
This is not a claim that all twelve trunks must use that corridor. Separate
left-side return escapes or another layer are design options needing review.

The existing R1 resistor-return branch is only one part of the complete star:
XQ56 must meet its intended R1 reference point, while XQ60 reference-leg,
XQ67 mode-dependent and XQ62 startup currents must not acquire unrecorded
shared path impedance in that branch. Existing native silicon is not isolated
merely by separating drawn metal; substrate coupling remains. All current,
IR-drop, noise, startup, mismatch and PEX budgets are not run.

| Check | Status |
| --- | --- |
| Read-only 301-device / 76-functional-return source count | passed |
| Literal row16/17 full-width fixed-direction track screen | failed; 4.40 µm required in 4.00 µm |
| Literal twelve-trunk extrapolation of pilot coordinates | failed; final center x=202.9 µm exceeds x=202 boundary |
| Alternative direction/layer/local-interval implementation | not run |
| New contact controls, stock DRC/LVS, complete bank/star geometry | not run in this review |
| PEX and analog / matching / return-current qualification | not run |
| Simulation seed | not applicable |
