# OpenROAD PSM (analyze_power_grid) on the ECO digital macro g1_digital (r3/r4, byte-identical), final views of
# run digital-eco-r3cand2-20260926. Environment: MACRO (final-views directory), DEF (DEF to read; default the
# macro's own), LIB (stdcell liberty file name), VDDV (supply V), PERIOD (osc_clk period, ns),
# ACT (global switching activity, "" = OpenSTA default vectorless propagation), OUT (output directory).
set pdk $::env(PDK_ROOT)/$::env(PDK)
read_lef $pdk/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef
read_lef $pdk/libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef
read_liberty $pdk/libs.ref/sg13g2_stdcell/lib/$::env(LIB)
read_def $::env(DEF)
read_sdc $::env(MACRO)/sdc/g1_digital.sdc
create_clock -name osc_clk -period $::env(PERIOD) [get_ports osc_clk]
set_propagated_clock [get_clocks osc_clk]
read_spef $::env(MACRO)/spef/nom/g1_digital.nom.spef
if { $::env(ACT) ne "" } {
    set_power_activity -global -activity $::env(ACT)
    set_power_activity -input -activity $::env(ACT)
}
report_power
set_pdnsim_net_voltage -net VDD -voltage $::env(VDDV)
set_pdnsim_net_voltage -net VSS -voltage 0
foreach net {VDD VSS} {
    analyze_power_grid -net $net -voltage_file $::env(OUT)/psm_$net.csv -error_file $::env(OUT)/psm_$net.err \
        -enable_em -em_outfile $::env(OUT)/psm_em_$net.csv
}
exit
