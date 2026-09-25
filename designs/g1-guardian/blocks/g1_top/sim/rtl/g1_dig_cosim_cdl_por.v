// G1_TOP chip-level co-simulation wrapper around the real digital macro RTL, variant for run_top_cdl.py
// (CDL-driven full-chip deck): identical to g1_dig_cosim_t2f.v except that the remaining g1_digital
// outputs bgr_r4, fault_n, trip_set_sel and clk_div_out are also exported (appended last), so that every
// output port of the gate-level g1_digital subckt of g1_chip_top_1414.cdl is driven. No logic is added.
// Variant _por (run_top_cdl.py --por-pin): por_n is an input (appended after tripped), driven by the
// CDL's sg13g2_tiehi through the single-threshold receiver, instead of being tied to 1.
// (blocks/g1_ctrl/rtl, blocks/g1_seu/rtl). It only fixes the ports the analog
// deck does not drive (por_n = 1: no POR cell exists, register map section 2)
// and exposes the breaker-path signals in a fixed order for the XSPICE d_cosim
// instance in tb_g1_top (inputs and outputs are matched by position, vectors
// MSB first). No logic is added; the register defaults, cmp_clk divider,
// trip timer and serial interface are the RTL's own.
// The timescale directive is required by the Icarus/ngspice shim (ivlng): the
// RTL files carry none and inherit this one (compile this file first).
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps

module g1_dig_cosim_cdl_por (
    input  wire       osc_clk,     // from G1_OSC (through the adc bridge)
    input  wire       en,          // EN pad p2c
    input  wire       sclk,        // SCLK pad p2c
    input  wire       sdi,         // SDI pad p2c
    input  wire       cmp_soft,    // G1_TRIP soft comparator
    input  wire       cmp_hard,    // G1_TRIP hard comparator
    input  wire       tripped,     // G1_GATE latch state
    input  wire       por_n,       // from sg13g2_tiehi (CDL net 'net')
    output wire       cmp_clk,     // to G1_TRIP
    output wire [7:0] dac_soft,    // to G1_TRIP soft DAC
    output wire [7:0] dac_hard,    // to G1_TRIP hard DAC
    output wire       trip_d,      // to G1_GATE
    output wire       clr_d,       // to G1_GATE
    output wire       fast_en,     // to G1_GATE
    output wire       osc_en,      // to G1_OSC
    output wire [3:0] osc_trim,    // to G1_OSC
    output wire       trip,        // monitor: digital latch
    output wire       gate_en,     // monitor: en & ~trip
    output wire [1:0] trip_cause,  // monitor: 0 none, 1 soft, 2 hard, 3 forced
    output wire       sdo,         // SDO (not padded in the deck)
    output wire [15:0] soft_peak,  // monitor: SOFT_PEAK register (soft accumulator peak, units of 256 osc_clk)
    output wire       inrush_active, // monitor: STATUS.INRUSH_ACTIVE
    output wire       soft_armed,    // monitor: STATUS.SOFT_ARMED (soft accumulator above zero)
    output wire       t2f_en,        // to g1_ls_up -> G1_T2F en
    output wire       t2f_mode,      // to g1_ls_up -> G1_T2F mode
    output wire       bgr_r4,        // to g1_ls_up -> G1_BGR r4
    output wire       fault_n,       // open in the chip CDL
    output wire       trip_set_sel,  // open in the chip CDL
    output wire       clk_div_out    // open in the chip CDL
);

    // testbench-only hierarchical probes of trip-timer state (registers SOFT_PEAK, STATUS bits)
    assign soft_peak     = u_dig.u_core.u_trip.soft_peak;
    assign inrush_active = u_dig.u_core.u_trip.inrush_active;
    assign soft_armed    = u_dig.u_core.u_trip.soft_armed;

    g1_digital #(.SEU_PLAIN_LEN(256), .SEU_TMR_LEN(128)) u_dig (
        .osc_clk(osc_clk), .por_n(por_n), .en(en),
        .sclk(sclk), .sdi(sdi), .sdo(sdo),
        .cmp_clk(cmp_clk), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(dac_soft), .dac_hard(dac_hard), .trip_set_sel(trip_set_sel),
        .trip_d(trip_d), .clr_d(clr_d), .fast_en(fast_en), .tripped(tripped),
        .trip(trip), .gate_en(gate_en), .fault_n(fault_n), .trip_cause(trip_cause),
        .osc_en(osc_en), .osc_trim(osc_trim),
        .t2f_en(t2f_en), .t2f_mode(t2f_mode), .bgr_r4(bgr_r4),
        .clk_div_out(clk_div_out));
endmodule
