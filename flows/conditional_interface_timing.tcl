set root [file normalize [file join [file dirname [info script]] ..]]
set_param general.maxThreads 2
set from [file join $root experiments implementation_holdfix routed.dcp]
set out [file join $root experiments interface_contract]
file mkdir $out
open_checkpoint $from
# The cold-transaction driver updates setup inputs on the falling edge. This
# report specifies the corresponding minimum input data hold contract, rather
# than claiming an unconstrained board-level interface has been implemented.
set inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -min 1.0 -clock core_clk $inputs
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
report_timing -delay_type min -max_paths 10 -file [file join $out hold_paths.rpt]
write_checkpoint [file join $out routed.dcp]
set s [get_timing_paths -delay_type max -max_paths 1]
set h [get_timing_paths -delay_type min -max_paths 1]
puts "INTERFACE_CONTRACT_SETUP_SLACK [get_property SLACK $s]"
puts "INTERFACE_CONTRACT_HOLD_SLACK [get_property SLACK $h]"
if {[get_property SLACK $s] < 0 || [get_property SLACK $h] < 0} {
  error "Conditional timing not closed"
}
puts "INTERFACE_CONTRACT_TIMING_PASS"
