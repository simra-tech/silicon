// G1_OSC black box for the chip flow (LibreLane MACROS entry, see ../../g1_padring/INTEGRATION.md).
// Analog macro: no timing arcs; pin names as layout/g1_osc.lef (schematic ports in schematic/g1_osc.sym:
// en trim0..3 osc_clk vdd vss).  VSS/VDD are Metal3 bars on the south/north edges; signal pins are
// Metal3 stubs on the west (en trim) and east (osc_clk) edges.
(* blackbox *)
module g1_osc (
`ifdef USE_POWER_PINS
    inout  VDD,            // 1.2 V core
    inout  VSS,            // ground, substrate
`endif
    input  en,             // 1 = run; 0 holds osc_clk low and both timing capacitors discharged
    input  [3:0] trim,     // capacitor trim, code 8 nominal (about 2.7 % per LSB)
    output osc_clk         // ~10 MHz, 50 % duty
);
endmodule
