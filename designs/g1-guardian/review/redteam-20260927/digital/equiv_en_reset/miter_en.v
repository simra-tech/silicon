// Red-team 2026-09-27: sequential-equivalence miter under the CHIP's reset conditions.
// gold = frozen ECO RTL, gate = r3 netlist 4b83f181. Differences from the committed miter_top.v:
//   * por_n is tied 1 in both designs (as on the chip: sg13g2_tiehi), never low;
//   * every flop of both designs starts from an independent free value (write_aiger -zinit);
//   * the only reset is EN: EN is forced low for the first 12 osc_clk rising edges, then free;
//   * outputs are compared only after those 12 edges.
module miter_en (
    input wire osc_clk, en, sclk, sdi, cmp_soft, cmp_hard, tripped,
    output wire trigger
);
    reg [3:0] n = 4'd0;
    always @(posedge osc_clk) if (n != 4'd12) n <= n + 4'd1;
    wire started = (n == 4'd12);
    wire en_eff = en & started;
    wire [35:0] og, on;
    gold u_gold (.osc_clk(osc_clk), .por_n(1'b1), .en(en_eff), .sclk(sclk), .sdi(sdi),
        .sdo(og[0]), .cmp_clk(og[1]), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(og[9:2]), .dac_hard(og[17:10]), .trip_set_sel(og[18]), .trip_d(og[19]),
        .clr_d(og[20]), .fast_en(og[21]), .tripped(tripped), .trip(og[22]), .gate_en(og[23]),
        .fault_n(og[24]), .trip_cause(og[26:25]), .osc_en(og[27]), .osc_trim(og[31:28]),
        .t2f_en(og[32]), .t2f_mode(og[33]), .bgr_r4(og[34]), .clk_div_out(og[35]));
    gate u_gate (.osc_clk(osc_clk), .por_n(1'b1), .en(en_eff), .sclk(sclk), .sdi(sdi),
        .sdo(on[0]), .cmp_clk(on[1]), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(on[9:2]), .dac_hard(on[17:10]), .trip_set_sel(on[18]), .trip_d(on[19]),
        .clr_d(on[20]), .fast_en(on[21]), .tripped(tripped), .trip(on[22]), .gate_en(on[23]),
        .fault_n(on[24]), .trip_cause(on[26:25]), .osc_en(on[27]), .osc_trim(on[31:28]),
        .t2f_en(on[32]), .t2f_mode(on[33]), .bgr_r4(on[34]), .clk_div_out(on[35]));
    assign trigger = started & |(og ^ on);
endmodule
