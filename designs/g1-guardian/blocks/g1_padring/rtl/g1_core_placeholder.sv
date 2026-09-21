// SPDX-License-Identifier: Apache-2.0
// Placeholder core for the G1 pad-ring build. Gives every digital output pad
// a driver and every input pad a load so the ring can be placed, routed and
// checked; carries no G1 function. The analog terminals are accepted and left
// unconnected. To be replaced by the G1 block macros.

`default_nettype none

module g1_core_placeholder (
`ifdef USE_POWER_PINS
    inout  wire  VDD,         // 1.2 V core
    inout  wire  VSS,         // core and analog ground
    inout  wire  VDDA,        // 3.3 V analog supply (pin 7, D14), unused here
`endif
    input  logic en_i,        // pin 12 EN
    input  logic sclk_i,      // pin 14 SCLK
    input  logic sdi_i,       // pin 15 SDI
    output logic gate_o,      // pin 10 GATE
    output logic fault_n_o,   // pin 11 FAULT_N
    output logic sdo_o,       // pin 16 SDO
    output logic temp_out_o,  // pin 17 TEMP_OUT
    /* verilator lint_off UNUSEDSIGNAL */
    inout  wire  sense_p, sense_n, trip_set, vref,       // analog, unused here
    inout  wire  g_shared, d_std, d_elt,
    inout  wire  hbt_e, hbt_b, hbt_c
    /* verilator lint_on UNUSEDSIGNAL */
);

    logic sdo_q;

    always_ff @(posedge sclk_i) begin
        sdo_q <= sdi_i;
    end

    assign gate_o     = en_i;
    assign fault_n_o  = ~en_i;
    assign sdo_o      = sdo_q;
    assign temp_out_o = en_i & sdi_i;

endmodule

`default_nettype wire
