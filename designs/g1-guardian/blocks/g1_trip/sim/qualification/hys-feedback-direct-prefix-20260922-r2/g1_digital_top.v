// G1 digital core: serial interface + register file + trip timer + SEU monitor.
// One synchronous domain on osc_clk (from G1_OSC); the serial shift logic runs
// on sclk and is handed over inside g1_serial. Reset is asynchronous on
// (por_n & en) and released synchronously to osc_clk.
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

    // ---------------- reset: async assert, sync release ----------------
    wire arst_n = por_n & en;
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
        .fast_en(fast_en), .sense_ofs(sense_ofs),
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
