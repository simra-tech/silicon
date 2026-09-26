// Sequential-equivalence miter: gold = frozen ECO RTL (module renamed gold), gate = r3 candidate
// v2 netlist (module renamed gate). Shared free inputs; por_n is forced low in the first cycle
// (register "started", initial 0) so that both designs start from their reset state; after that
// por_n is a free input. trigger = 1 if any output differs.
module miter_top (
    input wire osc_clk, por_n, en, sclk, sdi, cmp_soft, cmp_hard, tripped,
    output wire trigger
);
    reg started = 1'b0;
    always @(posedge osc_clk) started <= 1'b1;
    wire por_eff = por_n & started;
    wire [47:0] og, on;
    gold u_gold (.osc_clk(osc_clk), .por_n(por_eff), .en(en), .sclk(sclk), .sdi(sdi),
        .sdo(og[0]), .cmp_clk(og[1]), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(og[9:2]), .dac_hard(og[17:10]), .trip_set_sel(og[18]), .trip_d(og[19]),
        .clr_d(og[20]), .fast_en(og[21]), .tripped(tripped), .trip(og[22]), .gate_en(og[23]),
        .fault_n(og[24]), .trip_cause(og[26:25]), .osc_en(og[27]), .osc_trim(og[31:28]),
        .t2f_en(og[32]), .t2f_mode(og[33]), .bgr_r4(og[34]), .clk_div_out(og[35]));
    gate u_gate (.osc_clk(osc_clk), .por_n(por_eff), .en(en), .sclk(sclk), .sdi(sdi),
        .sdo(on[0]), .cmp_clk(on[1]), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(on[9:2]), .dac_hard(on[17:10]), .trip_set_sel(on[18]), .trip_d(on[19]),
        .clr_d(on[20]), .fast_en(on[21]), .tripped(tripped), .trip(on[22]), .gate_en(on[23]),
        .fault_n(on[24]), .trip_cause(on[26:25]), .osc_en(on[27]), .osc_trim(on[31:28]),
        .t2f_en(on[32]), .t2f_mode(on[33]), .bgr_r4(on[34]), .clk_div_out(on[35]));
    assign og[47:36] = 12'd0;
    assign on[47:36] = 12'd0;
    assign trigger = |(og ^ on);
endmodule
