set root [file normalize [file join [file dirname [info script]] ..]]
set_param general.maxThreads 2
set impl [file join $root experiments interface_contract]
set programs [file join $root experiments programs]
set names {orsirr_1_L_free_work orsirr_1_L_budget_0 fpga_dcop_01_L_free_work fpga_dcop_01_L_budget_0 fpga_dcop_01_L_affinity_1}
if {[info exists ::env(POWER_ONE)]} {set names [list $::env(POWER_ONE)]}
if {[info exists ::env(POWER_CASES)]} {set names [split $::env(POWER_CASES)]}
foreach name $names {
  set case [file join $programs $name]
  set suffix {}
  if {[info exists ::env(POWER_IP)]} {set suffix {_ip}}
  puts "POWER_CASE_START $name"
  open_checkpoint [file join $impl routed.dcp]
  set_operating_conditions -process typical -junction_temp 25
  read_saif -strip_path tb_post/dut -out_file [file join $case saif_annotation${suffix}.rpt] [file join $case activity32${suffix}.saif]
  report_power -file [file join $case power${suffix}.rpt]
  report_power -format xml -file [file join $case power${suffix}.xml]
  report_switching_activity -file [file join $case register_activity${suffix}.rpt] -all -type register
  report_switching_activity -file [file join $case default_activity${suffix}.rpt] -default_toggle_rate -default_static_probability
  puts "POWER_CASE_END $name"
  close_project
}
