# Differential-expression diagnostic proof

For arbitrary finite real contact voltages p0,p1 and nonnegative weights
w0,w1 with w0+w1=1:

`p0 + w1*(p1-p0) = (1-w1)*p0 + w1*p1 = w0*p0 + w1*p1`.

The output of the E source remains av-to-ground. Only its second differential
control input and first coefficient change; no output reference terminal,
F source, current weight, source/load, solver option, numerical tolerance,
rshunt accounting, observation vector, time endpoint or acceptance gate changes.
This distinction prevents accidentally drawing model current from p0 through
a new physical E-source output terminal.

The five preparedr4 decks are byte-exact to preparedr3 after replacing
`Eaverage av 0 POLY(2) p0 0 p1 p0 0 1 {2/3}` with
`Eaverage av 0 POLY(2) p0 0 p1 0 0 {1/3} {2/3}`. The direct control is unchanged.
Exact-rational coefficient and729 signedvoltage/weight controls pass, including
simplex endpoints and the actual1/3,2/3weights; wrong-current-sign rejection
and all prior analyzer controls remain. Recorded18-test receipt:
sense_distributed_coupon_synthetic_20260923_r4.

The purpose is numerical representation only: equal p0,p1 make the difference
input exactly zero in real algebra. It does not guarantee simulator binary
time/wave equality, actual SENSE applicability or a physical weight choice.
Original1266vs1275 zeroR time/wave FAIL remains. One bounded alternative only;
no further variants without a new diagnosed cause and coordinator direction.
Runtime not run at preparation; waiting explicit CPU48 return and fresh43gate.
