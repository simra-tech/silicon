// G1 digital core: serial interface + register file + trip timer + SEU monitor.
// One synchronous domain on osc_clk (from G1_OSC); the serial shift logic runs
// on sclk and is handed over inside g1_serial.
// ECO 2026-09-25 (blocks/g1_ctrl/ECO_20260925.md, change 4): the core reset is
// asserted when EN has been sampled low on 8 consecutive osc_clk edges (after a
// 2-flop synchroniser), or immediately (combinationally from EN) while EN has
// never been seen high since power-up; release stays synchronous to osc_clk.
// The analog EN path (G1_GATE en_core) is outside this macro and unchanged.
// ECO 2026-09-25 (change 5a): the fast_en port is MODE.FAST_EN gated by fast_dly[2],
// which is 0 in reset and rises 3 osc_clk edges after reset release, i.e. one
// edge after the first real hard-comparator decision. While the core is in
// reset cmp_clk is static and the unstrobed hard comparator output is not a
// decision (it sits at 1 on the chip netlist, g1_top eco_c_mid run); a fast
// path enabled at that moment would set the G1_GATE latch as soon as EN rises.
// Interface names: G1_REGISTER_MAP.md section 2, blocks/g1_trip/INTERFACE.md,
// blocks/g1_t2f/INTERFACE.md.
// SPDX-License-Identifier: Apache-2.0

module g1_digital_top #(
    parameter SEU_PLAIN_LEN = 256,    // plain shift register stages (area budget, see g1_seu/README.md)
    parameter SEU_TMR_LEN   = 128     // TMR shift register stages (x3 copies)
) (
    input  wire       osc_clk,
    input  wire       por_n,         // power-on reset from the analog wrapper, active low (tie 1 if absent)
    input  wire       en,            // EN pad (level-shifted); low resets the core
    // serial pads
    input  wire       sclk,
    input  wire       sdi,
    output wire       sdo,
    // analog trip path (G1_TRIP, blocks/g1_trip/INTERFACE.md)
    output wire       cmp_clk,       // osc_clk/2 comparator strobe
    input  wire       cmp_soft,
    input  wire       cmp_hard,
    output wire [7:0] dac_soft,      // effective codes: register + hysteresis + sense_ofs, saturated
    output wire [7:0] dac_hard,
    output wire       trip_set_sel,
    // G1_GATE latch
    output wire       trip_d,        // set (level = digital latch state)
    output wire       clr_d,         // clear pulse (2 cycles)
    output wire       fast_en,       // enable the analog fast path
    input  wire       tripped,       // analog latch state (asynchronous)
    // breaker outputs (monitor copies; the pads are driven by G1_GATE)
    output wire       trip,
    output wire       gate_en,       // en & ~trip
    output wire       fault_n,
    output wire [1:0] trip_cause,
    // G1_OSC
    output wire       osc_en,
    output wire [3:0] osc_trim,
    // G1_T2F / G1_BGR control bits (1.2 V here; shifted to 3.3 V by g1_ls_up in the wrapper)
    output wire       t2f_en,
    output wire       t2f_mode,
    output wire       bgr_r4,
    // test
    output wire       clk_div_out
);

    // ---------------- EN deglitch (ECO 2026-09-25) ----------------
    // These flops are reset by por_n only (tied high on the chip), never by EN.
    // en_hist is a shift register rather than a counter so that an unknown
    // power-up state is flushed by EN itself (8 known samples), in silicon and
    // in X-propagating simulation alike.
    reg  [1:0] en_sync;       // metastability filter for the EN pad
    reg  [6:0] en_hist;       // previous 7 synchronised samples
    reg        en_off;        // 1 = EN sampled low on 8 consecutive edges
    reg        en_seen;       // 1 = EN has been sampled high since power-up
    always @(posedge osc_clk or negedge por_n) begin
        if (!por_n) begin
            en_sync <= 2'b00;
            en_hist <= 7'h00;
            en_off  <= 1'b1;
            en_seen <= 1'b0;
        end else begin
            en_sync <= {en_sync[0], en};
            en_hist <= {en_hist[5:0], en_sync[1]};
            en_off  <= ~en_sync[1] & (en_hist == 7'h00);
            if (en_sync[1]) en_seen <= 1'b1;
        end
    end
    // en_seen = 0: reset follows EN directly (first reset after power-up needs no clock
    // edge). en_seen = 1: reset only from the filtered en_off (a flop, glitch-free).
    wire arst_n = por_n & ~en_off & (en | en_seen);

    // ---------------- reset: async assert, sync release ----------------
    reg  rs0, rs1;
    always @(posedge osc_clk or negedge arst_n) begin
        if (!arst_n) begin
            rs0 <= 1'b0;
            rs1 <= 1'b0;
        end else begin
            rs0 <= 1'b1;
            rs1 <= rs0;
        end
    end
    wire rst_n = rs1;

    // ---------------- comparator strobe: osc_clk / 2 ----------------
    reg cmp_clk_q;
    always @(posedge osc_clk or negedge rst_n) begin
        if (!rst_n) cmp_clk_q <= 1'b0;
        else        cmp_clk_q <= ~cmp_clk_q;
    end
    assign cmp_clk = cmp_clk_q;

    // ---------------- fast path enable qualification (ECO 2026-09-25) ----------------
    wire       fast_en_reg;       // MODE.FAST_EN from the register file
    reg  [2:0] fast_dly;          // edges since reset release, saturating at 3
    always @(posedge osc_clk or negedge rst_n) begin
        if (!rst_n) fast_dly <= 3'b000;
        else        fast_dly <= {fast_dly[1:0], 1'b1};
    end
    assign fast_en = fast_en_reg & fast_dly[2];

    // ---------------- serial ----------------
    wire       wr_en, rd_en;
    wire [6:0] wr_addr, rd_addr;
    wire [7:0] wr_data, rd_data;

    g1_serial u_serial (
        .osc_clk(osc_clk), .rst_n(rst_n),
        .wr_en(wr_en), .wr_addr(wr_addr), .wr_data(wr_data),
        .rd_en(rd_en), .rd_addr(rd_addr), .rd_data(rd_data),
        .sclk(sclk), .sdi(sdi), .sdo(sdo));

    // ---------------- register file ----------------
    wire [7:0]  dac_soft_code, dac_hard_code, hard_n, inrush, hold_time, retry_max;
    wire [15:0] soft_time;
    wire [1:0]  decay;
    wire        hyst_en, hyst_2, soft_en, hard_en, retrig, force_trip;
    wire        clear, clr_trip_cnt, clr_peak;
    wire        inrush_active, holding, gave_up, soft_armed, cmp_soft_s, cmp_hard_s, gate_en_i;
    wire        tripped_a_s;
    wire [7:0]  sense_ofs;
    wire [7:0]  retry_cnt;
    wire [15:0] trip_cnt, soft_peak;
    wire        scrub_en, seu_clr_cnt, seu_inj_plain, seu_inj_tmr;
    wire [1:0]  pattern;
    wire [15:0] seu_cnt_plain, seu_cnt_corr;
    wire [7:0]  seu_cnt_unc, seu_run_max;
    wire        seu_active, seu_filling;

    g1_regfile u_regfile (
        .clk(osc_clk), .rst_n(rst_n),
        .wr_en(wr_en), .wr_addr(wr_addr), .wr_data(wr_data),
        .rd_en(rd_en), .rd_addr(rd_addr), .rd_data(rd_data),
        .dac_soft_code(dac_soft_code), .dac_hard_code(dac_hard_code),
        .soft_time(soft_time), .decay(decay), .hyst_en(hyst_en), .hyst_2(hyst_2),
        .hard_n(hard_n), .inrush(inrush), .hold_time(hold_time), .retry_max(retry_max),
        .soft_en(soft_en), .hard_en(hard_en), .retrig(retrig),
        .trip_set_sel(trip_set_sel), .force_trip(force_trip),
        .fast_en(fast_en_reg), .sense_ofs(sense_ofs),
        .clear(clear), .clr_trip_cnt(clr_trip_cnt), .clr_peak(clr_peak),
        .trip(trip), .trip_cause(trip_cause), .inrush_active(inrush_active),
        .holding(holding), .gave_up(gave_up), .soft_armed(soft_armed),
        .cmp_soft_s(cmp_soft_s), .cmp_hard_s(cmp_hard_s), .gate_en(gate_en),
        .tripped_a_s(tripped_a_s), .dac_soft_eff(dac_soft), .dac_hard_eff(dac_hard),
        .retry_cnt(retry_cnt), .trip_cnt(trip_cnt), .soft_peak(soft_peak),
        .scrub_en(scrub_en), .pattern(pattern),
        .seu_clr_cnt(seu_clr_cnt), .seu_inj_plain(seu_inj_plain), .seu_inj_tmr(seu_inj_tmr),
        .seu_cnt_plain(seu_cnt_plain), .seu_cnt_corr(seu_cnt_corr),
        .seu_cnt_unc(seu_cnt_unc), .seu_run_max(seu_run_max),
        .seu_active(seu_active), .seu_filling(seu_filling),
        .osc_en(osc_en), .osc_trim(osc_trim), .clk_div_out(clk_div_out),
        .t2f_en(t2f_en), .t2f_mode(t2f_mode), .bgr_r4(bgr_r4));

    // ---------------- trip timer ----------------
    g1_trip_timer u_trip (
        .clk(osc_clk), .rst_n(rst_n), .cmp_clk(cmp_clk_q),
        .cmp_soft(cmp_soft), .cmp_hard(cmp_hard), .tripped_a(tripped),
        .soft_en(soft_en), .hard_en(hard_en), .retrig(retrig), .force_trip(force_trip),
        .soft_time(soft_time), .decay(decay), .hyst_en(hyst_en), .hyst_2(hyst_2),
        .hard_n(hard_n), .inrush(inrush), .hold_time(hold_time), .retry_max(retry_max),
        .dac_soft_code(dac_soft_code), .dac_hard_code(dac_hard_code), .sense_ofs(sense_ofs),
        .clear(clear), .clr_trip_cnt(clr_trip_cnt), .clr_peak(clr_peak),
        .trip(trip), .trip_cause(trip_cause), .gate_en(gate_en_i), .fault_n(fault_n),
        .trip_d(trip_d), .clr_d(clr_d),
        .inrush_active(inrush_active), .holding(holding), .gave_up(gave_up),
        .soft_armed(soft_armed), .cmp_soft_s(cmp_soft_s), .cmp_hard_s(cmp_hard_s),
        .tripped_a_s(tripped_a_s),
        .retry_cnt(retry_cnt), .trip_cnt(trip_cnt), .soft_peak(soft_peak),
        .dac_soft_out(dac_soft), .dac_hard_out(dac_hard));

    // EN low holds the core in reset (trip = 0); the gate must still be off then.
    assign gate_en  = en & gate_en_i;

    // ---------------- SEU monitor ----------------
    g1_seu #(.PLAIN_LEN(SEU_PLAIN_LEN), .TMR_LEN(SEU_TMR_LEN)) u_seu (
        .clk(osc_clk), .rst_n(rst_n),
        .scrub_en(scrub_en), .pattern(pattern),
        .clr_cnt(seu_clr_cnt), .inj_plain(seu_inj_plain), .inj_tmr(seu_inj_tmr),
        .cnt_plain(seu_cnt_plain), .cnt_corr(seu_cnt_corr), .cnt_unc(seu_cnt_unc),
        .run_max(seu_run_max), .active(seu_active), .filling(seu_filling));

endmodule
