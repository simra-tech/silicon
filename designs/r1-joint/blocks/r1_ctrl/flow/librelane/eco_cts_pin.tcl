# Revision 0.9 (track T5i): post-CTS repair of one clock pin lost by OpenROAD CTS latency balancing.
# OpenROAD CTS (delay-buffer latency balancing of the clock-gate ANDs) leaves input A of one clock-gate AND
# unconnected for the 0.9 netlist (runs t24, t25, t26; CTS_DELAY_BUFFER_DERATE_PCT 0 and CTS_BALANCE_LEVELS
# do not stop the balancer). This script reconnects that pin to a named clock net of the CTS result, writes the
# odb and the derived views, and refuses to act if the pin is already connected or the net is not a clock net.
# Inside the container (openroad -exit -no_splash eco_cts_pin.tcl) with the environment:
#   ECO_IN  <odb of step 35-openroad-cts>   ECO_OUT_DIR <directory>   ECO_INST <instance>   ECO_PIN A
#   ECO_NET <clock net>                     ECO_TOP <top cell name>
set block_name $::env(ECO_TOP)
read_db $::env(ECO_IN)
set block [ord::get_db_block]
set inst [$block findInst $::env(ECO_INST)]
if {$inst == "NULL"} { puts "ECO: instance $::env(ECO_INST) not found"; exit 1 }
set it [$inst findITerm $::env(ECO_PIN)]
if {[$it getNet] != "NULL"} { puts "ECO: pin already connected to [[$it getNet] getName]"; exit 1 }
set net [$block findNet $::env(ECO_NET)]
if {$net == "NULL"} { puts "ECO: net $::env(ECO_NET) not found"; exit 1 }
if {[$net getSigType] != "CLOCK"} { puts "ECO: net $::env(ECO_NET) is [$net getSigType], not CLOCK"; exit 1 }
$it connect $net
puts "ECO: connected $::env(ECO_INST)/$::env(ECO_PIN) to $::env(ECO_NET) ([llength [$net getITerms]] pins on the net)"
set o $::env(ECO_OUT_DIR)
write_db $o/$block_name.odb
write_def $o/$block_name.def
write_verilog $o/$block_name.nl.v
write_verilog -include_pwr_gnd $o/$block_name.pnl.v
