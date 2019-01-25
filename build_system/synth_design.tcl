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


# Extract debug nets + net props for waveform viewing from design and store in file
open_checkpoint $BUILD_PRJ_DIR/$PROJECT_NAME.runs/synth_1/top.dcp
set dbgs [get_nets -hier -filter {MARK_DEBUG}]

set sb_sigs [list]
set sb_sigs [lsearch -regexp -not -inline -all $dbgs "\[{1}[0123456789]+\]{1}"]

set mb_sigs [list]
set mb_sigs [lsearch -regexp -inline -all $dbgs "\[{1}[0123456789]+\]{1}"]
regsub -all "\[{1}[0123456789]+\]{1}" $mb_sigs "" mb_sigs
set mb_sigs [lsort -unique $mb_sigs]

set mb_sigs_exponents [list]
set mb_sigs_widths [list]

foreach {signal} $mb_sigs {
	append signal [0]
	lappend mb_sigs_exponents [get_property fp_exponent [get_nets $signal]]
	lappend mb_sigs_widths [get_property fp_width [get_nets $signal]]
}

#puts single:$sb_sigs
#puts multi:$mb_sigs
#puts mb_sigs_exponents:$mb_sigs_exponents
#puts mb_sigs_widths:$mb_sigs_widths

# Extraction of time_signal and reset_signal
set reset_s [get_nets -hier -filter {reset_signal}]

set time_s [get_nets -hier -filter {time_signal}]
regsub -all "\[{1}[0123456789]+\]{1}" $time_s "" time_s
set time_s [lsort -unique $time_s]

set time_s_exponent [get_property fp_exponent [get_nets $signal]]
set time_s_width [get_property fp_width [get_nets $signal]]



#TBD: Add check for empty string elements and replace with None!
#TBD: Change format into python dict
set outputFile [open "$BUILD_PRJ_DIR/probe_config.txt" w]
puts $outputFile [concat "SB:" $sb_sigs]
puts $outputFile [concat "MB:" $mb_sigs]
puts $outputFile [concat "MB_EXPONENT:" $mb_sigs_exponents]
puts $outputFile [concat "MB_WIDTH:" $mb_sigs_widths]
puts $outputFile [concat "RESET:" $reset_s]
puts $outputFile [concat "TIME:" $time_s]
puts $outputFile [concat "TIME_EXPONENT:" $time_s_exponent]
puts $outputFile [concat "TIME_WIDTH:" $time_s_width]
close $outputFile

close_design
close_project