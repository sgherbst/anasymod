# Open previously created project

set PROJECT_NAME [lindex $argv 0]
set BUILD_PRJ_DIR [lindex $argv 1]
set SIM_TB [lindex $argv 2]
set TOP_INST [lindex $argv 3]
set SIM_TIME [lindex $argv 4]
set DEBUG_LEVEL [lindex $argv 5]
set DT [lindex $argv 6]

#puts PROJECT_NAME:$PROJECT_NAME
#puts BUILD_PRJ_DIR:$BUILD_PRJ_DIR
#puts SIM_TB:$SIM_TB
#puts TOP_INST:$TOP_INST
#puts SIM_TIME:$SIM_TIME
#puts DEBUG_LEVEL:$DEBUG_LEVEL
#puts DT:$DT

open_project $BUILD_PRJ_DIR/$PROJECT_NAME.xpr

set_property top $SIM_TB [get_filesets sim_1]

set_property verilog_define [list SIMULATION DT=$DT] [get_filesets sim_1]

set_property -name {xsim.simulate.runtime} -value $SIM_TIME -objects [get_filesets sim_1]
set_property -name {xsim.elaborate.debug_level} -value $DEBUG_LEVEL -objects [get_filesets sim_1]

launch_simulation

close_project