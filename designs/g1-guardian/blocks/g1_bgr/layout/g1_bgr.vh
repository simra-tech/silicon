// G1_BGR black box for the chip flow (LibreLane MACROS entry, see ../../g1_padring/INTEGRATION.md).
// Analog macro: no timing arcs; pin names and order as xschem/g1_bgr.sym and layout/g1_bgr.lef.
// vdd/vss are the 3.3 V IOVDD/IOVSS rails of the padring (LEF USE POWER/GROUND, Metal3 bars on the
// north/south edges); all signal pins are Metal3 stubs on the west (vref iptat vbe dvbe) and east
// (pbias pcasc r4) edges.
(* blackbox *)
module g1_bgr (
`ifdef USE_POWER_PINS
    inout  vdd,      // 3.3 V, IOVDD
    inout  vss,      // IOVSS / substrate
`endif
    input  r4,       // 3.3 V logic: 1 = 1:4 emitter-ratio test mode (default 0)
    output vref,     // 1.04 V reference, unbuffered (~88 kOhm)
    output iptat,    // PTAT current output (PMOS cascode source, 4.1 uA at 27 C into a node between 0 V and about 2 V)
    output pbias,    // mirror gate rail (copies of I_PTAT: PMOS w/l = 10/4 on vdd)
    output pcasc,    // cascode gate rail
    output vbe,      // Q1 base/collector node (monitor)
    output dvbe      // top of R1 = delta-V_BE (monitor)
);
endmodule
