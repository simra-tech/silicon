// G1_TRIP black box for the chip flow (LibreLane MACROS entry, see ../../g1_padring/INTEGRATION.md).
// Analog macro: no timing arcs; pin names as layout/g1_trip.lef (schematic ports in schematic/g1_trip.sym:
// isense vref cmp_clk soft[7:0] hard[7:0] cmp_soft cmp_hard vdd vdda vss).  VSS/VDD are Metal3 bars on
// the south/north edges, IOVDD (3.3 V, the DAC switch drive) a Metal3 bar just inside the north edge;
// signal pins are Metal3 stubs on the west (ISENSE VREF dac_soft) and east (dac_hard clk cmp_soft cmp_hard) edges.
(* blackbox *)
module g1_trip (
`ifdef USE_POWER_PINS
    inout  VDD,            // 1.2 V core
    inout  IOVDD,          // 3.3 V (level shifters that drive the thick-oxide DAC switches)
    inout  VSS,            // ground of both domains, substrate
`endif
    input  ISENSE,         // 1.0..2.0 V from G1_SENSE (halved on chip)
    input  VREF,           // 1.04 V, the buffered VREF copy from G1_SENSE (2 x 20.5 uA load)
    input  [7:0] dac_soft, // soft threshold code, 1.2 V logic, static
    input  [7:0] dac_hard, // hard threshold code
    input  clk,            // comparator strobe (5 MHz): soft on the rising, hard on the falling edge
    output cmp_soft,       // 1 while ISENSE/2 > V_DAC(dac_soft), held between strobes
    output cmp_hard        // same for dac_hard
);
endmodule
