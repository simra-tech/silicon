// R1_CTRL / r1_adcw: digital CDAC weight correction of the SAR ADC (PLAN.md D12,
// INTERFACES.md "ADC -> ctrl").
//   sum  = SUM_{i=0..12} raw[i] * w[i]      w[i]: 14-bit unsigned, units of 1/4 LSB
//   code = clamp((sum + 2) >> 2, 0, 4095)   12-bit offset binary, as in revision 0.1
// raw[11:0] are the 12 binary-weighted decisions (raw[11] = MSB, nominal 2048 LSB)
// and raw[12] is the redundant decision (nominal 64 LSB, position in the SAR
// sequence set by r1_adc revision 2). Reset weights are binary: w[i] = 4 * 2^i,
// w[12] = 256, so an ADC without redundancy (raw[12] = 0) gives the 0.1 code.
// Serial accumulation, two decisions per tick: valid at tick t, code_valid
// (combinational from the accumulator, one tick) at t + 7. A new valid while
// busy restarts the accumulation (the ADC needs >= 12 ticks per conversion,
// so this does not happen in operation).
// SPDX-License-Identifier: Apache-2.0

module r1_adcw (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         valid,          // one-tick pulse with raw
    input  wire [12:0]  raw,
    input  wire [181:0] w,              // w[i] at [14*i +: 14]
    output wire         code_valid,
    output wire [11:0]  code
);
    reg [12:0] rr;                      // decisions, shifted right by 2 per tick
    reg [17:0] acc;
    reg [2:0]  k;                       // pair index 0..6
    reg        busy;

    // weight pair for the current index: w[2k], w[2k+1] (w[13] = 0)
    reg [13:0] wa, wb;
    always @(*) begin
        case (k)
            3'd0: begin wa = w[14*0 +: 14];  wb = w[14*1 +: 14];  end
            3'd1: begin wa = w[14*2 +: 14];  wb = w[14*3 +: 14];  end
            3'd2: begin wa = w[14*4 +: 14];  wb = w[14*5 +: 14];  end
            3'd3: begin wa = w[14*6 +: 14];  wb = w[14*7 +: 14];  end
            3'd4: begin wa = w[14*8 +: 14];  wb = w[14*9 +: 14];  end
            3'd5: begin wa = w[14*10 +: 14]; wb = w[14*11 +: 14]; end
            default: begin wa = w[14*12 +: 14]; wb = 14'd0;      end
        endcase
    end
    wire [17:0] acc_n = acc + (rr[0] ? {4'd0, wa} : 18'd0) + (rr[1] ? {4'd0, wb} : 18'd0);
    wire [16:0] rnd   = acc_n[17:2] + {15'd0, acc_n[1]};        // (sum + 2) >> 2
    assign code_valid = busy && (k == 3'd6) && !valid;
    assign code       = (rnd > 17'd4095) ? 12'hFFF : rnd[11:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rr <= 13'd0; acc <= 18'd0; k <= 3'd0; busy <= 1'b0;
        end else begin
            if (valid) begin
                rr <= raw; acc <= 18'd0; k <= 3'd0; busy <= 1'b1;
            end else if (busy) begin
                acc <= acc_n;
                rr  <= {2'b00, rr[12:2]};
                k   <= k + 3'd1;
                if (k == 3'd6) busy <= 1'b0;
            end
        end
    end
endmodule
