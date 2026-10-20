// R1_CTRL / r1_adcw: digital CDAC weight correction of one SAR ADC slice
// (PLAN.md D12, D18; INTERFACES.md "ADC -> ctrl").
// Revision 0.3 (D18): 14 decisions per conversion, one instance per slice.
//   sum  = SUM_{i=0..13} raw[i] * w[i]      w[i]: 14-bit unsigned, units of 1/4 LSB
//   code = clamp((sum + 2) >> 2, 0, 4095)   12-bit offset binary
// raw[13] is the first (most significant) decision, raw[0] the last. The
// weights are loaded by the host from a bench or self measurement; the reset
// weights are the nominal r1_adc revision-3 weights (r1_regs).
// Serial accumulation, four decisions per tick: valid at tick t, code_valid
// (combinational from the accumulator) in the cycle after the edge t + 3, so
// that the corrected pair reaches r1_pos inside the 22-tick frame for a
// conversion of <= 17 ticks (r1_gate). A new valid while busy restarts the
// accumulation (the ADC needs >= 14 ticks per conversion).
// SPDX-License-Identifier: Apache-2.0

module r1_adcw (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         valid,          // one-tick pulse with raw
    input  wire [13:0]  raw,
    input  wire [195:0] w,              // w[i] at [14*i +: 14]
    output wire         code_valid,
    output wire [11:0]  code
);
    reg [13:0] rr;                      // decisions, shifted right by 4 per tick
    reg [17:0] acc;
    reg [1:0]  k;                       // group index 0..3
    reg        busy;

    // weight group for the current index: w[4k .. 4k+3] (w[14], w[15] = 0)
    reg [13:0] w0, w1, w2, w3;
    always @(*) begin
        case (k)
            2'd0: begin w0 = w[14*0 +: 14];  w1 = w[14*1 +: 14];  w2 = w[14*2 +: 14];  w3 = w[14*3 +: 14];  end
            2'd1: begin w0 = w[14*4 +: 14];  w1 = w[14*5 +: 14];  w2 = w[14*6 +: 14];  w3 = w[14*7 +: 14];  end
            2'd2: begin w0 = w[14*8 +: 14];  w1 = w[14*9 +: 14];  w2 = w[14*10 +: 14]; w3 = w[14*11 +: 14]; end
            default: begin w0 = w[14*12 +: 14]; w1 = w[14*13 +: 14]; w2 = 14'd0;    w3 = 14'd0;            end
        endcase
    end
    wire [17:0] acc_n = acc + (rr[0] ? {4'd0, w0} : 18'd0) + (rr[1] ? {4'd0, w1} : 18'd0)
                            + (rr[2] ? {4'd0, w2} : 18'd0) + (rr[3] ? {4'd0, w3} : 18'd0);
    wire [16:0] rnd   = acc_n[17:2] + {15'd0, acc_n[1]};        // (sum + 2) >> 2
    assign code_valid = busy && (k == 2'd3) && !valid;
    assign code       = (rnd > 17'd4095) ? 12'hFFF : rnd[11:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rr <= 14'd0; acc <= 18'd0; k <= 2'd0; busy <= 1'b0;
        end else begin
            if (valid) begin
                rr <= raw; acc <= 18'd0; k <= 2'd0; busy <= 1'b1;
            end else if (busy) begin
                acc <= acc_n;
                rr  <= {4'b0000, rr[13:4]};
                k   <= k + 2'd1;
                if (k == 2'd3) busy <= 1'b0;
            end
        end
    end
endmodule
