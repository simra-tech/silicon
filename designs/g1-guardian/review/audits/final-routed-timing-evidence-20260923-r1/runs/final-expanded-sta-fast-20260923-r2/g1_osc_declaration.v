// Declaration-only interface; no timing or analog model.
module g1_osc (en, trim, osc_clk, VDD, VSS);
input en;
input [3:0] trim;
output osc_clk;
inout VDD;
inout VSS;
endmodule
