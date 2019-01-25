# Open previously created project

set PROJECT_NAME [lindex $argv 0]
set BUILD_PRJ_DIR [lindex $argv 1]
set NUM_CORES [lindex $argv 2]

puts PROJECT_NAME:$PROJECT_NAME
puts BUILD_PRJ_DIR:$BUILD_PRJ_DIR
puts NUM_CORES:$NUM_CORES

open_project $BUILD_PRJ_DIR/$PROJECT_NAME.xpr

# Run implementation and generate bitstream
reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs $NUM_CORES
wait_on_run impl_1

close_project



#write_hwdef -force -file $BUILD_PRJ_DIR/flyback.hwdef

#write_sysdef -force -hwdef $BUILD_PRJ_DIR/flyback.hwdef -bitfile $BUILD_PRJ_DIR/flyback.bit -file $BUILD_PRJ_DIR/flyback.hdf
