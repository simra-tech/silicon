// Declaration-only interface; no timing or analog model.
module g1_trip (VREF, ISENSE, cmp_soft, cmp_hard, clk, VDD, IOVDD, VSS, dac_soft, dac_hard);
input VREF;
input ISENSE;
output cmp_soft;
output cmp_hard;
input clk;
inout VDD;
inout IOVDD;
inout VSS;
input [7:0] dac_soft;
input [7:0] dac_hard;
endmodule
