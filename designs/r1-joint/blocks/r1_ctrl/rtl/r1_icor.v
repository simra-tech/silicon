// R1_CTRL / r1_icor (revision 0.9, PLAN.md D27): host offset and gain correction of the two
// phase-current samples. The corrected samples are the bus registers I_A / I_B and the inputs
// of the I2t over-current model (r1_safe); the raw samples (r1_gate) feed the raw-code capture.
//
//   d  = (RAW - 2048) - OFS                          13-bit signed, ADC LSB (OFS 12-bit two's complement)
//   q  = floor((d * GAIN + 2^13) / 2^14)             GAIN unsigned Q2.14 (0x4000 = 1.0), round half up
//   I  = min(4095, max(0, q + 2048))                 12-bit offset binary, as the raw code
//
// With the reset words (OFS 0, GAIN 0x4000) I = RAW for every code (bit-identical to revision 0.8).
// Area form: one shift-add multiplier (one 14-bit adder, 16 ticks per channel), channels in turn.
// The first form (one parallel 13 x 17 multiplier, 2 ticks) synthesized to 15 040 um2 (run
// r1ctrl_20261028_v09); the current pair arrives once per PWM period, so the latency costs nothing.
// Timing from the tick in which cur_valid is high: I_A is written 18 ticks later, I_B 35 ticks later.
// A pair that arrives while the previous one is being corrected restarts the sequence (the newer
// pair wins); this happens only for PWM periods below 36 ticks.
// SPDX-License-Identifier: Apache-2.0

module r1_icor (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        cur_valid,      // pulse: raw_a / raw_b hold a new current pair from this tick on
    input  wire [11:0] raw_a, raw_b,   // weight-corrected ADC codes (r1_gate)
    input  wire [11:0] ofs_a, ofs_b,   // IA_OFS, IB_OFS (signed, subtracted)
    input  wire [15:0] gain_a, gain_b, // IA_GAIN, IB_GAIN (Q2.14)
    output reg  [11:0] i_a, i_b        // corrected samples (reset 0, as I_A / I_B of revision 0.8)
);
    // st: 0 idle, 1 load A, 2 multiply A (16 ticks), 3 write I_A + load B, 4 multiply B, 5 write I_B
    reg  [2:0]  st;
    reg  [3:0]  k;
    reg  [12:0] dr;                    // d of the channel being multiplied
    reg  [13:0] ph;                    // product register, high part (signed)
    reg  [15:0] pl;                    // product register, low part (gain bits shifted out, product bits shifted in)
    wire        sel_a = (st == 3'd0) || (st == 3'd1);
    wire [11:0] raw_s = sel_a ? raw_a : raw_b;
    wire [11:0] ofs_s = sel_a ? ofs_a : ofs_b;
    wire signed [12:0] d_n = $signed({~raw_s[11], raw_s[10:0]}) - $signed(ofs_s);   // (RAW - 2048) - OFS
    // one shift-add step: if the gain bit is 1 add d to the high part, then shift the 30-bit register right
    // (arithmetic). |high part| < |d| <= 4095 before the add, so the 14-bit sum cannot overflow.
    wire signed [13:0] sum = $signed(ph) + (pl[0] ? $signed({dr[12], dr}) : 14'sd0);
    // result: P = {ph, pl} = d * GAIN; q = P[29:14] + P[13] (round half up); I = sat(q + 2048)
    wire signed [15:0] q = $signed({ph, pl[15:14]}) + $signed({15'd0, pl[13]});
    wire signed [16:0] s = q + 17'sd2048;
    wire [11:0] sat = s[16] ? 12'd0 : (s > 17'sd4095) ? 12'd4095 : s[11:0];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st <= 3'd0; k <= 4'd0; dr <= 13'd0; ph <= 14'd0; pl <= 16'd0; i_a <= 12'd0; i_b <= 12'd0;
        end else if (cur_valid) begin
            st <= 3'd1;                                    // new pair (also restarts a running sequence)
        end else begin
            case (st)
                3'd1, 3'd3: begin
                    if (st == 3'd3) i_a <= sat;
                    dr <= d_n; ph <= 14'd0; pl <= (st == 3'd1) ? gain_a : gain_b; k <= 4'd0;
                    st <= st + 3'd1;
                end
                3'd2, 3'd4: begin
                    ph <= {sum[13], sum[13:1]};
                    pl <= {sum[0], pl[15:1]};
                    k  <= k + 4'd1;
                    if (k == 4'd15) st <= st + 3'd1;
                end
                3'd5: begin i_b <= sat; st <= 3'd0; end
                default: st <= 3'd0;
            endcase
        end
    end
endmodule
