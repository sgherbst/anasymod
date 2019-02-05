# Open previously created project

set PROJECT_NAME [lindex $argv 0]
set BUILD_PRJ_DIR [lindex $argv 1]
set NUM_CORES [lindex $argv 2]

puts PROJECT_NAME:$PROJECT_NAME
puts BUILD_PRJ_DIR:$BUILD_PRJ_DIR
puts NUM_CORES:$NUM_CORES

open_project $BUILD_PRJ_DIR/$PROJECT_NAME.xpr

# Run synthesis

reset_run synth_1
launch_runs synth_1 -jobs $NUM_CORES
wait_on_run synth_1


# Load synthesized design
open_checkpoint $BUILD_PRJ_DIR/$PROJECT_NAME.runs/synth_1/top.dcp

# Extract analog_signals
set ana_s [get_nets -hier -filter {analog_signal == "true"}]

regsub -all "\[{1}[0123456789]+\]{1}" $ana_s "" ana_s
set ana_s [lsort -unique $ana_s]

set ana_s_exponents [list]
set ana_s_widths [list]

foreach {signal} $ana_s {
	append signal [0]
	lappend ana_s_exponents [get_property fixed_point_exponent [get_nets $signal]]
	lappend ana_s_widths [get_property BUS_WIDTH [get_nets $signal]]
}

# Extract time_signal
set time_s [get_nets -hier -filter {time_signal == "true"}]
regsub -all "\[{1}[0123456789]+\]{1}" $time_s "" time_s
set time_s [lsort -unique $time_s]
append time_s [0]

set time_s_exponent [get_property fixed_point_exponent [get_nets $time_s]]
set time_s_width [get_property BUS_WIDTH [get_nets $ime_s]]

# Extract reset_signal
set reset_s [get_nets -hier -filter {reset_signal == "true"}]

# Extract other_signals marked for debug
set other_s [get_nets -hier -filter {time_signal != "true" && MARK_DEBUG && reset_signal != "true" && analog_signal != "true"}]

set sb_s [list]
set sb_s [lsearch -regexp -not -inline -all $other_s "\[{1}[0123456789]+\]{1}"]

set mb_s [list]
set mb_s [lsearch -regexp -inline -all $other_s "\[{1}[0123456789]+\]{1}"]
regsub -all "\[{1}[0123456789]+\]{1}" $mb_s "" mb_s
set mb_s [lsort -unique $mb_s]

set mb_s_widths [list]

foreach {signal} $mb_s {
	append signal [0]
	lappend mb_s_widths [get_property fp_width [get_nets $signal]]
}

set outputFile [open "$BUILD_PRJ_DIR/probe_config.txt" w]
puts $outputFile [concat "ANALOG:" $ana_s]
puts $outputFile [concat "ANALOG_EXPONENT:" $ana_s_exponent]
puts $outputFile [concat "ANALOG_WIDTH:" $ana_s_width]
puts $outputFile [concat "TIME:" $time_s]
puts $outputFile [concat "TIME_EXPONENT:" $time_s_exponent]
puts $outputFile [concat "TIME_WIDTH:" $time_s_width]
puts $outputFile [concat "RESET:" $reset_s]
puts $outputFile [concat "SB:" $sb_s]
puts $outputFile [concat "MB:" $mb_s]
puts $outputFile [concat "MB_WIDTH:" $mb_s_widths]
close $outputFile

close_design
close_project