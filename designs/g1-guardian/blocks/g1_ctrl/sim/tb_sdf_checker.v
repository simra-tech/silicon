// Tool qualification: SDF raises setup limit from1ns to4ns.
// The 2ns setup stimulus must violate only after annotation.
`timescale 1ns/1ps
module timing_cell(input d,input clk,output reg q);
 reg notifier=0;
 integer notices=0;
 always @(notifier) if($time>0)begin notices=notices+1;$display("TIMING_NOTIFIER %0t",$time);end
 always @(posedge clk) q<=d;
 specify
  specparam tsu=1,th=1;
  $setuphold(posedge clk,d,tsu,th,notifier);
 endspecify
endmodule
module tb_sdf_checker;
 reg clk=0,d=0;wire q;
 timing_cell dut(d,clk,q);
 initial begin
`ifdef ANNOTATE
  $sdf_annotate("checker.sdf",dut);
`endif
  #5 d=1;#5 clk=1;#5 clk=0;
  #13 d=0;#2 clk=1;#5 clk=0;
  #10;
`ifdef ANNOTATE
  if(dut.notices>0)$display("CHECKER_EXPECTED_VIOLATION_PASS");else $display("CHECKER_FAIL_MISSING_VIOLATION notifier=%b",dut.notifier);
`else
  if(dut.notices==0)$display("CHECKER_EXPECTED_CLEAN_PASS");else $display("CHECKER_FAIL_UNEXPECTED_VIOLATION");
`endif
  $finish;
 end
endmodule
