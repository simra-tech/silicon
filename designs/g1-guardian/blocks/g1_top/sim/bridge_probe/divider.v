`timescale 1ns/1ps
module divider(input clk, output reg q=0);
always @(posedge clk) q <= ~q;
endmodule
