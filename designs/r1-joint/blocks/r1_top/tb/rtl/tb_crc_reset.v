// RTL-only helper (track T10): CAL_CRC of the r1_ctrl 0.5 reset values, read back over SPI exactly as the host
// procedure of R1_REGISTER_MAP.md section 4.4. The full-chip decks write this value instead of reading 43 words
// at chip level (saves about 150 us of simulated time per deck). Output line: "CRC_RESET 0xNN".
`timescale 1ns/1ps
module tb_crc_reset;
    reg clk = 0, por_n = 0, cs_n = 1, ma = 0, sdi = 0, en = 1;
    always #16.667 clk = ~clk;
    wire slo_sdo;
    r1_ctrl_top u (.clk(clk), .por_n(por_n), .cs_n(cs_n), .ma_sclk(ma), .sdi(sdi), .slo_sdo(slo_sdo), .en_pad(en),
        .fault_n(), .gate_a(), .gate_b(), .gate_c(), .adc_hold(), .is_smp(), .adc_start(), .adc_sel(),
        .adc_valid_a(1'b0), .adc_raw_a(14'd0), .adc_valid_b(1'b0), .adc_raw_b(14'd0), .cmp(4'd0), .tap_p(), .tap_n(),
        .az_win(), .t2f_clk(1'b0), .osc_trim(), .pga_c(), .t2f_en(), .t2f_mode(), .bias_en());
    reg [23:0] mi; reg [15:0] rv; reg [7:0] c; integer i, a, j;
    task spi_x; input [23:0] mo; begin
        #25 cs_n = 0; #25; mi = 0;
        for (i = 23; i >= 0; i = i - 1) begin sdi = mo[i]; #25 ma = 1; mi[i] = slo_sdo; #25 ma = 0; end
        #25 cs_n = 1; #400; end endtask
    task rd; input [6:0] ad; begin spi_x({1'b1, ad, 16'd0}); spi_x({1'b1, 7'd0, 16'd0}); rv = mi[15:0]; end endtask
    task cw; input [15:0] w; begin
        c = c ^ w[15:8]; for (j = 0; j < 8; j = j + 1) c = c[7] ? ({c[6:0], 1'b0} ^ 8'h07) : {c[6:0], 1'b0};
        c = c ^ w[7:0];  for (j = 0; j < 8; j = j + 1) c = c[7] ? ({c[6:0], 1'b0} ^ 8'h07) : {c[6:0], 1'b0}; end endtask
    initial begin
        #100 por_n = 1; #200;
        c = 8'hFF;
        for (a = 8'h10; a <= 8'h17; a = a + 1) begin rd(a); cw(rv); end
        for (a = 8'h36; a <= 8'h3C; a = a + 1) begin rd(a); cw(rv); end
        for (a = 8'h50; a <= 8'h5D; a = a + 1) begin rd(a); cw(rv); end
        for (a = 8'h60; a <= 8'h6D; a = a + 1) begin rd(a); cw(rv); end
        $display("CRC_RESET 0x%02h", c);
        spi_x({1'b0, 7'h18, 8'd0, c}); #(400 * 33.3);
        rd(7'h01); $display("STATUS 0x%04h CAL_VALID=%0d", rv, rv[4]);
        $finish;
    end
endmodule
