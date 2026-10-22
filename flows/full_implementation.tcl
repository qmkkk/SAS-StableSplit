set root [file normalize [file join [file dirname [info script]] ..]]
set hw [file join $root src]
set out [file join $root experiments implementation]
set_param general.maxThreads 2
create_project -in_memory -part xc7a200tfbg484-2
set_property target_language Verilog [current_project]
set_property include_dirs [list [file join $hw rtl]] [current_fileset]
set_property verilog_define {PHYSICAL_FP_IP} [current_fileset]
foreach name {fp_add_zero fp_mul_zero} {
 read_ip [file join $root .. experiments build repaired.srcs sources_1 ip $name ${name}.xci]
}
read_verilog -sv [list [file join $hw common_pkg.sv] [file join $hw config_pkg.sv]]
foreach f [glob [file join $hw rtl *.sv]] {
 if {[string match tb_* [file tail $f]]} {continue}
 read_verilog -sv $f
}
synth_design -top stpu_top -mode out_of_context -part xc7a200tfbg484-2 -flatten_hierarchy rebuilt
create_clock -name core_clk -period 100 [get_ports clk]
set_input_delay 0 -clock core_clk [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay 0 -clock core_clk [get_ports -filter {DIRECTION == OUT}]
report_utilization -file [file join $out synth_utilization.rpt]
report_utilization -hierarchical -file [file join $out synth_hierarchy.rpt]
report_drc -file [file join $out synth_drc.rpt]
report_timing_summary -report_unconstrained -file [file join $out synth_timing.rpt]
write_checkpoint [file join $out synth.dcp]
set ff [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]
set br [llength [get_cells -hier -filter {REF_NAME =~ RAMB*}]]
set bb [llength [get_cells -hier -filter {IS_BLACKBOX == 1}]]
puts "SYNTH_QUALIFICATION FF=$ff BRAM=$br BLACKBOX=$bb"
if {$ff < 1000 || $br < 64 || $bb > 0} {error "State, RAM or IP qualification failed"}
set loops [get_drc_violations -quiet -filter {NAME =~ LUTLP*}]
if {[llength $loops] > 0} {error "Combinational loop: no waiver allowed"}
opt_design
place_design
phys_opt_design
route_design
report_utilization -file [file join $out routed_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out routed_timing.rpt]
report_timing -delay_type max -max_paths 10 -file [file join $out routed_max_paths.rpt]
report_timing -delay_type min -max_paths 10 -file [file join $out routed_min_paths.rpt]
report_route_status -file [file join $out routed_status.rpt]
report_drc -file [file join $out routed_drc.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
write_checkpoint [file join $out routed.dcp]
write_verilog -mode funcsim [file join $out functional_netlist.v]
write_verilog -mode timesim -sdf_anno false [file join $out timing_netlist.v]
write_sdf [file join $out routed.sdf]
set worstsetup [get_timing_paths -delay_type max -max_paths 1]
set worsthold [get_timing_paths -delay_type min -max_paths 1]
puts "ROUTED_SETUP_SLACK [get_property SLACK $worstsetup]"
puts "ROUTED_HOLD_SLACK [get_property SLACK $worsthold]"
if {[get_property SLACK $worstsetup] < 0 || [get_property SLACK $worsthold] < 0} {
 error "Timing remains open; retain checkpoint for diagnosis, no timing-qualified performance claim"
}
puts "IMPLEMENTATION_TIMING_GATE_PASS"

