# Source-held T2F VDDA escape

The original T2F M3 VDDA header at x953–1045/y1053–1055.6 µm is a separate
source-bound domain from its VDD12 header. The north core-VDD TM2 ring at
y1051.3–1066.3 prevents a direct upper-metal supply landing there.

The bounded proposal uses a 1.1 µm M3 escape from (1044,1054.3) to
(1048,1054.3), then down to (1048,1043.5). It crosses the existing T2F VDD12
M4 bridge without a cut. Twelve Via3, twelve Via4, four TopVia1 and two
horizontal TopVia2 cuts connect to a 2.2 µm TM2 route to x1060, then down
to the existing shared VDDA handoff at y922. No stack lands on the east
core-VDD TM1 ring. Actual flat-net foreign-contact and stock clearance
checks are required before root integration.

The branch target is an exploratory 1 mA, not a qualified operating or
return-current limit. The shared pad's exploratory 10 mA is a total, not
an additional per-branch budget. Native primitive geometry, source, pins,
models and rules remain unchanged. Internal contact capacity, PVT/current
sharing/IR/EM, final signal context and complete extraction remain not run.
