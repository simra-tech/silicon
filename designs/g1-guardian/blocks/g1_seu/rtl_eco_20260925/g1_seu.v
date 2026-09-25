// G1_SEU: single-event-upset monitor. Behaviour: G1_REGISTER_MAP.md section 6.
//   - PLAIN_LEN-stage plain shift register (one flop per stage)
//   - TMR_LEN-stage TMR shift register: three separately placeable copies,
//     per-stage majority vote written into all copies at every shift
//   - pattern generator, fill counter and counters triple-redundant (g1_tmr_reg)
//   - both registers shift on every osc_clk (no clock enable, no per-bit mux);
//     with a constant pattern (all 0 / all 1) the flops hold static data while
//     clocked, with the checkerboard they toggle every cycle
// Expected output bit = current input bit, valid because the patterns have
// period 1 or 2 and both lengths are even (checked at elaboration).
// SPDX-License-Identifier: Apache-2.0

module g1_seu #(
    parameter PLAIN_LEN = 1024,
    parameter TMR_LEN   = 256
) (
    input  wire        clk,          // osc_clk
    input  wire        rst_n,
    // configuration (quasi-static)
    input  wire        scrub_en,     // 1: compare and count (registers shift regardless)
    input  wire [1:0]  pattern,      // 0 checkerboard, 1 zeros, 2 ones, 3 checkerboard
    // commands (one-cycle pulses)
    input  wire        clr_cnt,
    input  wire        inj_plain,
    input  wire        inj_tmr,
    // telemetry
    output wire [15:0] cnt_plain,
    output wire [15:0] cnt_corr,
    output wire [7:0]  cnt_unc,
    output wire [7:0]  run_max,
    output wire        active,
    output wire        filling
);
    localparam FILL_LEN = (PLAIN_LEN > TMR_LEN) ? PLAIN_LEN : TMR_LEN;

    // ---------------- sequencer state (TMR) ----------------
    wire        phase;        // checkerboard generator
    wire [10:0] fill_cnt;     // shifts since the last restart, saturates at FILL_LEN
    wire [1:0]  pattern_d;
    wire        scrub_en_d;
    reg  [10:0] fill_cnt_n;

    wire filled  = (fill_cnt == FILL_LEN[10:0]);
    wire restart = (scrub_en & ~scrub_en_d) | (pattern != pattern_d);

    g1_tmr_reg #(.W(1))  u_phase (.clk(clk), .rst_n(rst_n), .d(~phase),     .q(phase));
    g1_tmr_reg #(.W(11)) u_fill  (.clk(clk), .rst_n(rst_n), .d(fill_cnt_n), .q(fill_cnt));
    g1_tmr_reg #(.W(2))  u_pat_d (.clk(clk), .rst_n(rst_n), .d(pattern),    .q(pattern_d));
    g1_tmr_reg #(.W(1))  u_en_d  (.clk(clk), .rst_n(rst_n), .d(scrub_en),   .q(scrub_en_d));

    always @* begin
        if (restart)      fill_cnt_n = 11'd0;
        else if (!filled) fill_cnt_n = fill_cnt + 11'd1;
        else              fill_cnt_n = fill_cnt;
    end

    // no comparison in the restart cycle: the registers still hold the old
    // pattern while pat_bit already follows the new one
    wire cmp_en = scrub_en & filled & ~restart;
    assign filling = scrub_en & ~filled;
    assign active  = scrub_en & filled;

    wire pat_bit = (pattern == 2'd1) ? 1'b0 :
                   (pattern == 2'd2) ? 1'b1 : phase;

    // ---------------- plain register ----------------
    wire [PLAIN_LEN-1:0] plain_q;
    g1_seu_chain #(.LEN(PLAIN_LEN)) u_plain (
        .clk(clk), .rst_n(rst_n),
        .d({plain_q[PLAIN_LEN-2:0], pat_bit ^ inj_plain}), .q(plain_q));
    wire plain_out = plain_q[PLAIN_LEN-1];

    // ---------------- TMR register: three copies, vote and rewrite ----------------
    wire [TMR_LEN-1:0] qa, qb, qc;
    wire [TMR_LEN-1:0] vote = (qa & qb) | (qa & qc) | (qb & qc);
    g1_seu_chain #(.LEN(TMR_LEN)) u_tmr_a (
        .clk(clk), .rst_n(rst_n), .d({vote[TMR_LEN-2:0], pat_bit ^ inj_tmr}), .q(qa));
    g1_seu_chain #(.LEN(TMR_LEN)) u_tmr_b (
        .clk(clk), .rst_n(rst_n), .d({vote[TMR_LEN-2:0], pat_bit}), .q(qb));
    g1_seu_chain #(.LEN(TMR_LEN)) u_tmr_c (
        .clk(clk), .rst_n(rst_n), .d({vote[TMR_LEN-2:0], pat_bit}), .q(qc));
    wire tmr_out  = vote[TMR_LEN-1];
    wire disagree = |((qa ^ qb) | (qa ^ qc));

    // ---------------- comparison and counters (TMR) ----------------
    wire plain_err = cmp_en & (plain_out ^ pat_bit);
    wire tmr_err   = cmp_en & (tmr_out   ^ pat_bit);
    wire corr_ev   = cmp_en & disagree;

    wire [7:0]  run_cur;
    reg  [15:0] cnt_plain_n, cnt_corr_n;
    reg  [7:0]  cnt_unc_n, run_max_n, run_cur_n;

    g1_tmr_reg #(.W(16)) u_cnt_plain (.clk(clk), .rst_n(rst_n), .d(cnt_plain_n), .q(cnt_plain));
    g1_tmr_reg #(.W(16)) u_cnt_corr  (.clk(clk), .rst_n(rst_n), .d(cnt_corr_n),  .q(cnt_corr));
    g1_tmr_reg #(.W(8))  u_cnt_unc   (.clk(clk), .rst_n(rst_n), .d(cnt_unc_n),   .q(cnt_unc));
    g1_tmr_reg #(.W(8))  u_run_max   (.clk(clk), .rst_n(rst_n), .d(run_max_n),   .q(run_max));
    g1_tmr_reg #(.W(8))  u_run_cur   (.clk(clk), .rst_n(rst_n), .d(run_cur_n),   .q(run_cur));

    always @* begin
        cnt_plain_n = cnt_plain;
        cnt_corr_n  = cnt_corr;
        cnt_unc_n   = cnt_unc;
        run_max_n   = run_max;
        run_cur_n   = run_cur;
        if (clr_cnt) begin
            cnt_plain_n = 16'd0;
            cnt_corr_n  = 16'd0;
            cnt_unc_n   = 8'd0;
            run_max_n   = 8'd0;
            run_cur_n   = 8'd0;
        end else begin
            if (plain_err && cnt_plain != 16'hFFFF) cnt_plain_n = cnt_plain + 16'd1;
            if (corr_ev   && cnt_corr  != 16'hFFFF) cnt_corr_n  = cnt_corr  + 16'd1;
            if (tmr_err   && cnt_unc   != 8'hFF)    cnt_unc_n   = cnt_unc   + 8'd1;
            if (cmp_en) begin
                if (plain_err) begin
                    if (run_cur != 8'hFF) run_cur_n = run_cur + 8'd1;
                    if (run_cur_n > run_max) run_max_n = run_cur_n;
                end else begin
                    run_cur_n = 8'd0;
                end
            end
        end
    end

`ifndef SYNTHESIS
    // elaboration-time checks for the expected-bit shortcut (simulation only)
    initial begin
        if (PLAIN_LEN % 2 != 0 || TMR_LEN % 2 != 0)
            $display("g1_seu: register lengths must be even");
        if (FILL_LEN > 1024)
            $display("g1_seu: lengths above 1024 overflow the 11-bit fill counter");
    end
`endif

endmodule
