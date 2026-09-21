// Exploratory state fault injection at actual256/128 monitor sizes.
// Passing assertions confirm the stated behavior, including vulnerabilities;
// they are not a claim of radiation hardness or fault-tolerant control.
`timescale 1ns/1ps
module tb_fault_contract;
reg clk=0,run_clk=1,por_n=0,en=0,hard=0;
wire [7:0] soft_code,hard_code;
wire trip,gate_en,osc_en;
g1_digital_top dut(.osc_clk(clk),.por_n(por_n),.en(en),.sclk(1'b0),.sdi(1'b0),
 .cmp_soft(1'b0),.cmp_hard(hard),.tripped(1'b0),.dac_soft(soft_code),
 .dac_hard(hard_code),.trip(trip),.gate_en(gate_en),.osc_en(osc_en));
always #50 if(run_clk) clk=~clk;
integer checks=0,errors=0,k,c;
reg [7:0] corrupt;
reg [127:0] original;
task check(input [255:0] name,input cond);
begin checks=checks+1;if(cond!==1'b1)begin errors=errors+1;$display("FAIL %s",name);end end
endtask
task cycles(input integer n);begin repeat(n)@(posedge clk);#2;end endtask
task reset_core;
begin run_clk=1;en=0;por_n=0;hard=0;#120;por_n=1;en=1;cycles(5);end
endtask
initial begin
 reset_core;
 check("actual plain length",$bits(dut.u_seu.u_plain.q)==256);
 check("actual TMR length",$bits(dut.u_seu.u_tmr_a.q)==128);
 // Persistent threshold corruption: these control registers are not TMR.
 for(k=0;k<8;k=k+1)begin
  reset_core;@(negedge clk);corrupt=8'hfe^(8'b1<<k);
  dut.u_regfile.dac_hard_code=corrupt;#1;
  check("hard DAC upset visible",hard_code===corrupt);
  cycles(8);check("hard DAC upset persists",hard_code===corrupt);
 end
 $display("CLASS persistent threshold corruption:8/8 hard-DAC bit upsets persist until rewrite/reset");
 reset_core;@(negedge clk);dut.u_regfile.osc_ctrl[4]=0;#1;
 check("OSC_EN upset disables",osc_en===0);
 cycles(4);check("OSC_EN upset persists",osc_en===0);
 $display("CLASS OSC_EN upset persists; physical stopped-clock recovery requires EN/POR or external action");
 // An externally stopped clock prevents sampled hard trip with FAST disabled.
 reset_core;@(negedge clk);dut.u_regfile.inrush=0;cycles(10);
 @(negedge clk);run_clk=0;hard=1;#2000;
 check("clock loss prevents hard trip",trip===0 && gate_en===1);
 $display("CLASS dangerous:clock absent,FAST disabled,hard comparator high => digital path remains armed without trip for2us");
 en=0;#2;check("EN reset works with no clock",gate_en===0);
 reset_core;cycles(270);
 // Each single physical monitor-copy bit upset is masked immediately and
 // corrected on the next shift. All384 physical stage locations exercised.
 for(c=0;c<3;c=c+1)for(k=0;k<128;k=k+1)begin
  @(negedge clk);original=dut.u_seu.vote;
  case(c)
   0:dut.u_seu.u_tmr_a.q[k]=~dut.u_seu.u_tmr_a.q[k];
   1:dut.u_seu.u_tmr_b.q[k]=~dut.u_seu.u_tmr_b.q[k];
   2:dut.u_seu.u_tmr_c.q[k]=~dut.u_seu.u_tmr_c.q[k];
  endcase
  #1;check("single copy vote masked",dut.u_seu.vote===original);
  cycles(1);check("single copy rewritten",dut.u_seu.disagree===0);
 end
 check("384 corrections counted",dut.u_seu.cnt_corr===16'd384);
 check("single upsets no unc",dut.u_seu.cnt_unc===0);
 $display("CLASS384/384 single-copy monitor upsets masked and corrected");
 // Corrupt two copies at the same physical stage: majority is wrong and
 // rewrite spreads the wrong bit. This is an intentional fault-model limit.
 reset_core;cycles(270);@(negedge clk);original=dut.u_seu.vote;
 dut.u_seu.u_tmr_a.q[64]=~dut.u_seu.u_tmr_a.q[64];
 dut.u_seu.u_tmr_b.q[64]=~dut.u_seu.u_tmr_b.q[64];#1;
 check("double upset changes vote",dut.u_seu.vote!==original);
 cycles(140);check("double upset is uncorrectable",dut.u_seu.cnt_unc===1);
 $display("CLASS two-copy same-stage upset escapes majority correction and is counted as uncorrectable");
 // Counter copy upset masked and repaired without changing the telemetry.
 reset_core;cycles(270);@(negedge clk);
 dut.u_seu.u_cnt_plain.u_a.q[7]=1;#1;
 check("counter copy vote masked",dut.u_seu.cnt_plain===0);
 cycles(1);check("counter copy rewritten",dut.u_seu.u_cnt_plain.u_a.q===0);
 $display("SUMMARY checks=%0d errors=%0d; vulnerabilities above are expected characterizations",checks,errors);
 if(errors==0)$display("ALL TESTS PASSED");else $display("SOME TESTS FAILED");
 $finish;
end
initial begin #10000000;$display("FAIL watchdog");$finish;end
endmodule
