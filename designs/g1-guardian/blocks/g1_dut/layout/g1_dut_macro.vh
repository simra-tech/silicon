// G1_DUT black box for the chip flow (LibreLane MACROS entry, see ../../g1_padring/INTEGRATION.md).
// Analog macro, no timing arcs: one npn13G2 (Nx=1) with all three terminals on Metal3 stubs on the
// west edge (layout/g1_dut_macro.lef); vss (p+ substrate ring) is the Metal3 bar on the south edge.
(* blackbox *)
module g1_dut_macro (
`ifdef USE_POWER_PINS
    inout  vss,   // substrate ring
`endif
    inout  HBT_C, // collector, to pad 24
    inout  HBT_B, // base, to pad 23
    inout  HBT_E // emitter, to pad 22
);
endmodule
