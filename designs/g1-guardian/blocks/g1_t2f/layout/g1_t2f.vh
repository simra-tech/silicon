// G1_T2F black box for the chip flow (LibreLane MACROS entry, see ../../g1_padring/INTEGRATION.md).
// Analog macro: no timing arcs; pin names as xschem/g1_t2f.sym and layout/g1_t2f.lef.
// Revision 2 (2026-09-19, collector cascodes): macro 92 x 102.6 um; same pin names, layers and edges as
// revision 1 (vdd bar and the vdd12/fout/en stubs 2.2 um higher).
// vdd/vss are the 3.3 V IOVDD/IOVSS rails of the padring (LEF USE POWER/GROUND, Metal3 bars on the
// north/south edges); vdd12 is the 1.2 V core supply of the output stage only (Metal3 stub, east edge);
// all signal pins are Metal3 stubs on the east edge.
(* blackbox *)
module g1_t2f (
`ifdef USE_POWER_PINS
    inout  vdd,      // 3.3 V, IOVDD
    inout  vdd12,    // 1.2 V, VDD (output level shifter and buffer only, < 1 uA)
    inout  vss,      // IOVSS / VSS / substrate
`endif
    input  pbias,    // bandgap mirror gate rail (g1_bgr.pbias)
    input  pcasc,    // bandgap cascode gate rail (g1_bgr.pcasc)
    input  vref,     // bandgap output (g1_bgr.vref, ~1.04 V, unbuffered)
    input  en,       // 3.3 V logic: 1 = oscillator runs (register bit T2F_EN, reset value 1)
    input  mode,     // 3.3 V logic: 0 = PTAT threshold (V_REF), 1 = REF threshold (2 I_PTAT R_REF)
    output fout      // 1.2 V CMOS square wave, 1.2 .. 2.4 MHz, to the TEMP_OUT pad
);
endmodule
