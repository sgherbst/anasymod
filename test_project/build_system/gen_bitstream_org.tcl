# Open previously created project

set PROJECT_NAME [lindex $argv 0]
set BUILD_PRJ_DIR [lindex $argv 1]
set NUM_CORES [lindex $argv 2]

#puts PROJECT_NAME:$PROJECT_NAME
#puts BUILD_PRJ_DIR:$BUILD_PRJ_DIR
#puts NUM_CORES:$NUM_CORES

open_project $BUILD_PRJ_DIR/$PROJECT_NAME.xpr

# Run synthesis

#reset_run synth_1
#launch_runs synth_1 -jobs $NUM_CORES
#wait_on_run synth_1

# Extract debug nets + net props for waveform viewing from design and store in file

open_checkpoint $BUILD_PRJ_DIR/$PROJECT_NAME.runs/synth_1/top.dcp
set dbgs [get_nets -hier -filter {MARK_DEBUG}]
puts dbgs:$dbgs


#extract buses from debug signals
set dbgs_stripped [list]

foreach {signal} $dbgs {
	lappend dbgs_stripped [regsub -all "\[{1}[0123456789]+\]{1}" $signal ""]
}

set dbgs_unique [lsort -unique $dbgs_stripped]

#exit

set dbgs_exponents [list]

foreach {signal} $dbgs_unique {
	set temp ""
	append temp $signal "_exponent_val"
	set temp1 [split $temp "/"]
	set temp2 [lrange $temp1 end end]
	set temp3 [lrange $temp1 0 end-1]
	puts temp2:$temp2!
	puts temp3:$temp3!
	set temp4 "[get_property $temp2 [get_cells $temp3]]"
	set temp4 {[get_property $temp2 [get_cells $temp3]]}
	puts "[get_property $temp2 [get_cells $temp3]]"
	puts temp4:$temp4
	set temp5 eval $temp4
	puts temp5:$temp5
	lappend dbgs_exponents $temp5
}

puts dbgs_stripped:$dbgs_stripped
puts dbgs_unique:$dbgs_unique
puts dbgs_exponents:$dbgs_exponents

close_design
exit

# Run implementation and generate bitstream

reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs $NUM_CORES
wait_on_run impl_1

close_project



#write_hwdef -force -file $BUILD_PRJ_DIR/flyback.hwdef

#write_sysdef -force -hwdef $BUILD_PRJ_DIR/flyback.hwdef -bitfile $BUILD_PRJ_DIR/flyback.bit -file $BUILD_PRJ_DIR/flyback.hdf
