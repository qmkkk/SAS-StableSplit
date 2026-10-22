set root [file normalize [file join [file dirname [info script]] ..]]
set_param general.maxThreads 2
set src [file join $root experiments implementation]
set out [file join $root experiments implementation_holdfix]
file mkdir $out
open_checkpoint [file join $src routed.dcp]
phys_opt_design -hold_fix
route_design
report_utilization -file [file join $out utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_route_status -file [file join $out route_status.rpt]
report_drc -file [file join $out drc.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
write_checkpoint [file join $out routed.dcp]
set s [get_timing_paths -delay_type max -max_paths 1]
set h [get_timing_paths -delay_type min -max_paths 1]
puts "HOLD_REPAIR_SETUP_SLACK [get_property SLACK $s]"
puts "HOLD_REPAIR_HOLD_SLACK [get_property SLACK $h]"
if {[get_property SLACK $s] < 0 || [get_property SLACK $h] < 0} {
  error "Hold repair did not close timing"
}
puts "HOLD_REPAIR_TIMING_PASS"
