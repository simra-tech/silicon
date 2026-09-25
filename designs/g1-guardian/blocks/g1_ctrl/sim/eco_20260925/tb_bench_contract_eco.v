// ECO 2026-09-25 copy of tb_bench_contract.v for map 1.2 (blocks/g1_ctrl/ECO_20260925.md):
// EN-low reset step 200 ns -> 1.5 us (reset needs 8 consecutive low samples), INRUSH reset 0x14 -> 0x02.
// Executable bench sequencing contract; no production RTL modifications.
// External bus isolation and comparator decisions are ideal behavioral fixtures.
// This is NOT analog calibration, external switch validation, or a safety proof.
`timescale 1ns/1ps
module tb_bench_contract_eco;
reg clk=0, por_n=0, en=0, sclk=0, sdi=0;
reg external_bus_inhibit=1, persistent_fault=1, cmp_hard=0;
wire sdo, cmp_clk, trip, gate_en, fast_en;
wire [7:0] dac_soft, dac_hard;
wire [1:0] trip_cause;
wire bus_applied = !external_bus_inhibit;
wire load_energized = bus_applied && gate_en;
integer checks=0, errors=0, waited, masked_cycles, scenario;
g1_digital_top dut(.osc_clk(clk),.por_n(por_n),.en(en),
 .sclk(sclk),.sdi(sdi),.sdo(sdo),.cmp_clk(cmp_clk),
 .cmp_soft(1'b0),.cmp_hard(cmp_hard),.tripped(1'b0),
 .dac_soft(dac_soft),.dac_hard(dac_hard),.trip(trip),
 .gate_en(gate_en),.fast_en(fast_en),.trip_cause(trip_cause));
always #50 clk=~clk;
// A persistent over-threshold fault is presented only when the external bus
// is connected. It stays high after digital trip, exercising latched behavior.
always @(negedge cmp_clk) cmp_hard <= #1 (bus_applied && persistent_fault);
task check(input [8*96-1:0] name, input condition);
begin
 checks=checks+1;
 if(condition!==1'b1)begin errors=errors+1;$display("FAIL %0s t=%0t",name,$time);end
end endtask
task cycles(input integer n);begin repeat(n)@(posedge clk);#2;end endtask
task send_byte(input [7:0] value);
integer k;
begin for(k=7;k>=0;k=k-1)begin sdi=value[k];#100;sclk=1;#100;sclk=0;end sdi=0;end
endtask
task write_reg(input [6:0] addr,input [7:0] value);
begin send_byte({1'b0,addr});send_byte(value);#2000;end endtask
task read_reg(input [6:0] addr,output [7:0] value);
integer k;
begin
 send_byte({1'b1,addr});send_byte(0);
 for(k=7;k>=0;k=k-1)begin #100;sclk=1;value[k]=sdo;#100;sclk=0;end
 #2000;
end endtask
task read_check(input [6:0] addr,input [7:0] expected);
reg [7:0] value;
begin read_reg(addr,value);check("serial register readback",value===expected);
 $display("READ addr=%02h value=%02h expected=%02h EN=%b inhibit=%b",addr,value,expected,en,external_bus_inhibit);
end endtask
task reset_and_verify;
begin
 external_bus_inhibit=1;en=0;#1500;
 check("EN low shuts digital gate off",gate_en===0);
 check("EN low resets configuration",dut.u_regfile.dac_hard_code===8'hfe && dut.u_regfile.sense_ofs===0 && dut.u_regfile.inrush===8'h02);
 write_reg(7'h03,8'hc8);read_check(7'h00,0);
 check("EN low serial write ignored",dut.u_regfile.dac_hard_code===8'hfe);
 en=1;cycles(130);
 check("EN high may arm while physical bus remains isolated",gate_en===1 && load_energized===0 && bus_applied===0);
 read_check(7'h00,8'h47);read_check(7'h03,8'hfe);
 read_check(7'h27,0);read_check(7'h08,8'h02);
end endtask
task program_fixture(input [7:0] mask);
begin
 // HARD-only, no FAST, no retrigger. Synthetic offset +3 is register state,
 // not a measured calibration; threshold codes deliberately stay interior.
 write_reg(7'h0b,8'h02);write_reg(7'h07,8'h04);
 write_reg(7'h02,8'h96);write_reg(7'h03,8'hc8);
 write_reg(7'h27,8'h03);write_reg(7'h08,mask);
 read_check(7'h0b,8'h02);read_check(7'h07,8'h04);
 read_check(7'h02,8'h96);read_check(7'h03,8'hc8);
 read_check(7'h27,8'h03);read_check(7'h08,mask);
 read_check(7'h2a,8'h99);read_check(7'h2b,8'hcb);
 check("configuration requires EN high with independent inhibit",en && external_bus_inhibit && !load_energized && !trip && !fast_en);
end endtask
initial begin
 #200;por_n=1;
 for(scenario=0;scenario<2;scenario=scenario+1)begin
  reset_and_verify;
  program_fixture(scenario==0 ? 8'd0 : 8'd8);
  // Programming does not restart the mask counter. Apply the bus while the
  // second scenario still has residual mask time; measure that actual state.
  check("declared mask state before bus application",dut.inrush_active===(scenario==1));
  @(negedge clk);external_bus_inhibit=0;#2;
  check("external command deliberately applies bus",bus_applied && load_energized);
  masked_cycles=0;
  while(dut.inrush_active && masked_cycles<4097)begin
   check("persistent fault is digitally masked during inrush",trip===0 && gate_en===1);
   cycles(1);masked_cycles=masked_cycles+1;
  end
  check("mask expires within declared bound",masked_cycles<4097);
  if(scenario==1)check("nonzero mask was actually exercised",masked_cycles>100);
  waited=0;
  while(!trip && waited<16)begin cycles(1);waited=waited+1;end
  check("persistent fault trips within 16 clocks after unmask/apply",trip===1 && gate_en===0 && trip_cause===2 && !load_energized);
  cycles(30);check("hard-only no-retry trip stays latched",trip===1 && gate_en===0);
  $display("SCENARIO mask=%0d residual_mask_cycles=%0d post_mask_trip_clocks=%0d",scenario==0?0:8,masked_cycles,waited);
  external_bus_inhibit=1;#200;
 end
 // Cycling EN erased the first programmed state (checked on the second
 // reset); both scenarios explicitly reprogrammed and read back before load.
 en=0;#200;check("final independently isolated and disabled state",!bus_applied && !gate_en && !load_energized);
 $display("BENCH_CONTRACT scenarios=2 checks=%0d errors=%0d analog_validation=not_run physical_inhibit_validation=not_run",checks,errors);
 if(errors)$fatal(1,"bench sequence contract failed");
 $display("ALL TESTS PASSED");$finish;
end
initial begin #2000000;$fatal(1,"FAIL watchdog");end
endmodule
