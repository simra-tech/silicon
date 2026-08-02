# V8 hybrid CML-to-CMOS interface — nominal DC checkpoint

This directory publishes the V8 differential CML-to-1.2 V CMOS interface,
its nominal-DC and unrun 2.5 GHz transient decks, and the evidence from the
single nominal-DC run. It is a portable derivative of three sealed private
packages:

- source/deck V8 manifest: `9685e6e3ad8c7e5e5f4e5832f7aa9343ca9a90c5485d2ec9e295db9527394dc9`
- DC runtime V2 manifest: `1fb63c4fe0a41724245841430aef296ce735ba48513291033873270dd016c098`
- DC facts V1 manifest: `a6e5929297a3773fde9623badf2c8ea23f6e821efaf38fc4ba3192472e8002ce`

The interface source is byte-identical to sealed source
`68b1bc654f4449e63958f7dd0e82154aa54f8d3fd39725ec1dc74834876053b2`.
The copied raw, FACTS and REPORT are also byte-identical to their sealed
members: `3242af860cc73eab78ead1972135ec8fe8eb42b866a9651e742a126214190d64`,
`5dd62d7a4b56bda7218ba6acf418c8c321b7b6b69cb9c3653a0c1931945e68ea`,
and `5201ebe4a1f701538ac8dbe52fa5dc85f3b8dde7fa10d30c0a9c059f0f1544a6`.

For portability, the two public decks replace only the private PDK prefix
with `$PDK_ROOT`. The public run log retains native messages and exact run
metadata but omits absolute private execution paths. `SHA256SUMS` is the
authority for these public-copy bytes; private orchestration scripts and
manifests are intentionally not published.

## Nominal-DC result

One ngspice-46 batch invocation at 27 C returned zero and produced a binary
raw with 78 variables and 141 points. Independent parsing found all 10,998
payload values finite. `CMOS_OUT_N` falls rail-to-rail and crosses 0.6 V at
a sweep of 1.3880909334 V; `CMOS_OUT_P` rises rail-to-rail and crosses at
1.3875022859 V. Their midpoint separation is 0.588648 mV.

This verifies complementary nominal static logic for this deck only. The
transient deck is included but remains unrun at this checkpoint. Timing,
corners, loading compatibility, specification status, layout, signoff and
tape-out readiness are not established.

## Reproduce

Set `PDK_ROOT` to an IHP SG13G2 PDK root and run:

```sh
ngspice -b -o ngspice_dc_v8.log NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-DC-TRANSFER.cir
```

The deck writes `raw_tb_p1_cml2lv_hybrid_dc_v8.raw`. Compare that output
and the public files against `SHA256SUMS`; simulator-build differences can
change a raw hash even when the numeric series agrees, so also recount the
payload rather than treating hash inequality alone as an engineering failure.
