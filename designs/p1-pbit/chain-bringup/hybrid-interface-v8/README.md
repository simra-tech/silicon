# V8 hybrid CML-to-CMOS interface — DC and failed-transient checkpoint

This directory publishes the V8 differential CML-to-1.2 V CMOS interface,
its nominal-DC and 2.5 GHz transient decks, and evidence from one invocation
of each. It is a portable derivative of four sealed private
packages:

- source/deck V8 manifest: `9685e6e3ad8c7e5e5f4e5832f7aa9343ca9a90c5485d2ec9e295db9527394dc9`
- DC runtime V2 manifest: `1fb63c4fe0a41724245841430aef296ce735ba48513291033873270dd016c098`
- DC facts V1 manifest: `a6e5929297a3773fde9623badf2c8ea23f6e821efaf38fc4ba3192472e8002ce`
- transient failed-facts V1 manifest: `ef8d8cc3a4ce9a35a79d0a4518f1bf34c9d437c207ad2572af95b7e71d771094`

The interface source is byte-identical to sealed source
`68b1bc654f4449e63958f7dd0e82154aa54f8d3fd39725ec1dc74834876053b2`.
The copied DC raw, FACTS and REPORT are byte-identical to their sealed
members: `3242af860cc73eab78ead1972135ec8fe8eb42b866a9651e742a126214190d64`,
`5dd62d7a4b56bda7218ba6acf418c8c321b7b6b69cb9c3653a0c1931945e68ea`,
and `5201ebe4a1f701538ac8dbe52fa5dc85f3b8dde7fa10d30c0a9c059f0f1544a6`.
The transient raw, FACTS and REPORT are likewise byte-identical:
`dbab1bd80ddaed8c3bee8f0c5ca816ac192fb687a7c31e841c1de46a7f68906c`,
`77066d4353d9802507f07280268bf7a29285003818d8bdc5ee7918d52e400544`,
and `afa2d9b288cba5a757540df9eca048b72ba2fe719c322b96060ee6a43b688530`.

For portability, the two public decks replace only the private PDK prefix
with `$PDK_ROOT`. The public run log retains native messages and exact run
metadata but omits absolute private execution paths. `SHA256SUMS` is the
authority for these public-copy bytes; private orchestration scripts and
manifests are intentionally not published.

The `UNRUN` wording frozen inside the source and deck comments records their
pre-invocation preparation state; it is not the current status of the
transient deck. The run log and failed-facts package below are later evidence.

## Nominal-DC result

One ngspice-46 batch invocation at 27 C returned zero and produced a binary
raw with 78 variables and 141 points. Independent parsing found all 10,998
payload values finite. `CMOS_OUT_N` falls rail-to-rail and crosses 0.6 V at
a sweep of 1.3880909334 V; `CMOS_OUT_P` rises rail-to-rail and crosses at
1.3875022859 V. Their midpoint separation is 0.588648 mV.

This verifies complementary nominal static logic for this deck only.

## Nominal-transient result

One ngspice-46 batch invocation at 27 C returned zero and produced a binary
raw with 78 variables and 1,065 points from 0 to 2 ns. Independent parsing
found all 83,070 payload values finite. The differential input crosses zero
ten times, but neither CMOS output crosses the 0.6 V rail midpoint. The N
output remains between -0.355 mV and 0.343 mV; the P output remains between
1.199967 V and 1.200021 V. V8 therefore does not switch under this nominal
transient deck.

The original runtime checker returned 1 because its pre-manifest set expected
11 files after its own ordering had already created a twelfth validation log.
That bookkeeping failure, the successful simulator return, and the no-switch
engineering result are separate facts and are all retained here. This is not
a P1 gate conclusion. Timing compatibility, corners, specification status,
layout, signoff and tape-out readiness remain unestablished.

## Reproduce

Set `PDK_ROOT` to an IHP SG13G2 PDK root and run:

```sh
ngspice -b -o ngspice_dc_v8.log NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-DC-TRANSFER.cir
ngspice -b -o ngspice_tran_2p5g_v8.log NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-TRAN-2P5G.cir
```

The decks write the two `raw_tb_*.raw` files in this directory. Compare those
outputs and the public files against `SHA256SUMS`; simulator-build differences
can change a raw hash even when the numeric series agrees, so also recount the
payload rather than treating hash inequality alone as an engineering failure.
