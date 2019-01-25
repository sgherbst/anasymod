# STEP#1: define the output directory area.
#
set MODE [lindex $argv 0]
set REAL_DIR [lindex $argv 1]
set COMPONENT_DIR [lindex $argv 2]
set FPGA_DIR [lindex $argv 3]
set MODEL_DIR [lindex $argv 4]
set BUILD_ROOT [lindex $argv 5]
set BUILD_IP_ROOT [lindex $argv 6]
set PART [lindex $argv 7]
set TOP [lindex $argv 8]
set BUILD_PRJ_DIR $BUILD_ROOT/prj

set_part $PART

#set MODE [if {$MODE} {}]
#foreach a [list 1 2 3 4] {
#	
#}

file mkdir $BUILD_PRJ_DIR
#
# STEP#2: setup design sources and constraints
#
read_verilog  [ glob $MODEL_DIR/*.*v ]
read_verilog  [ glob $REAL_DIR/*.*v ]
read_verilog  [ glob $COMPONENT_DIR/*.*v ]
read_verilog  [ glob $FPGA_DIR/*.*v ]

# read_ip [ glob $BUILD_IP_ROOT/*/*.xci ]
# puts [ glob $BUILD_IP_ROOT/*/*.xci ]

read_ip $BUILD_IP_ROOT/clk_wiz_0/clk_wiz_0.xci
read_ip $BUILD_IP_ROOT/vio_0/vio_0.xci

#read_verilog -library work [ glob C:/Inicio_dev/flyback/models/design_1_wrapper.v ]
#read_checkpoint
read_bd C:/Inicio_dev/flyback/emu_build/bd/myproj/project_1.srcs/sources_1/bd/design_1/design_1.bd

# read_ip $BUILD_IP_ROOT/ila_0/ila_0.xci

#file mkdir $BUILD_PRJ_DIR/IP/clk_wiz_0
#file copy -force $BUILD_IP_ROOT/clk_wiz_0/clk_wiz_0.xci $BUILD_PRJ_DIR/IP/clk_wiz_0/clk_wiz_0.xci
#read_ip $BUILD_PRJ_DIR/IP/clk_wiz_0/clk_wiz_0.xci
#generate_target all [get_ips clk_wiz_0]
#synth_ip [get_ips clk_wiz_0]
#set clk_wiz_xdc [get_files -of_objects [get_files clk_wiz_0.xci] -filter {FILE_TYPE == XDC}]
#set_property is_enabled false [get_files $clk_wiz_xdc]

#file mkdir $BUILD_PRJ_DIR/IP/vio_0
#file copy -force $BUILD_IP_ROOT/vio_0/vio_0.xci $BUILD_PRJ_DIR/IP/vio_0/vio_0.xci
#read_ip $BUILD_PRJ_DIR/IP/vio_0/vio_0.xci
#generate_target all [get_ips vio_0]
#synth_ip [get_ips vio_0]
#set vio_xdc [get_files -of_objects [get_files vio_0.xci] -filter {FILE_TYPE == XDC}]
#set_property is_enabled false [get_files $vio_xdc]

#file mkdir $BUILD_PRJ_DIR/IP/ila_0
#file copy -force $BUILD_IP_ROOT/ila_0/ila_0.xci $BUILD_PRJ_DIR/IP/ila_0/ila_0.xci
#read_ip $BUILD_PRJ_DIR/IP/ila_0/ila_0.xci
#generate_target all [get_ips ila_0]
#synth_ip [get_ips ila_0]
#set ila_xdc [get_files -of_objects [get_files ila_0.xci] -filter {FILE_TYPE == XDC}]
#set_property is_enabled false [get_files $ila_xdc]

read_xdc  [ glob $FPGA_DIR/*.xdc ]

set_property file_type {Verilog Header} [get_files  $REAL_DIR/math.sv]
set_property file_type {Verilog Header} [get_files  $REAL_DIR/real.sv]
set_property file_type {Verilog Header} [get_files  $COMPONENT_DIR/components.sv]
 
#
# STEP#3: run synthesis, write design checkpoint, report timing, 
# and utilization estimates
#

synth_design -top $TOP -part $PART -include_dirs {$REAL_DIR $COMPONENT_DIR}
write_checkpoint -force $BUILD_PRJ_DIR/post_synth.dcp
report_timing_summary -file $BUILD_PRJ_DIR/post_synth_timing_summary.rpt
report_utilization -file $BUILD_PRJ_DIR/post_synth_util.rpt

write_hwdef -force -file $BUILD_PRJ_DIR/flyback.hwdef
#
# Run custom script to report critical timing paths
# reportCriticalPaths $BUILD_PRJ_DIR/post_synth_critpath_report.csv
#
# STEP#4: run logic optimization, placement and physical logic optimization, 
# write design checkpoint, report utilization and timing estimates
#
opt_design
# reportCriticalPaths $BUILD_PRJ_DIR/post_opt_critpath_report.csv
place_design
report_clock_utilization -file $BUILD_PRJ_DIR/clock_util.rpt
#
# Optionally run optimization if there are timing violations after placement
if {[get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]] < 0} {
    puts "Found setup timing violations => running physical optimization"
    phys_opt_design
}
write_checkpoint -force $BUILD_PRJ_DIR/post_place.dcp
report_utilization -file $BUILD_PRJ_DIR/post_place_util.rpt
report_timing_summary -file $BUILD_PRJ_DIR/post_place_timing_summary.rpt
#
# STEP#5: run the router, write the post-route design checkpoint, report the routing
# status, report timing, power, and DRC, and finally save the Verilog netlist.
#
route_design
write_checkpoint -force $BUILD_PRJ_DIR/post_route.dcp
report_route_status -file $BUILD_PRJ_DIR/post_route_status.rpt
report_timing_summary -file $BUILD_PRJ_DIR/post_route_timing_summary.rpt
report_power -file $BUILD_PRJ_DIR/post_route_power.rpt
report_drc -file $BUILD_PRJ_DIR/post_imp_drc.rpt

write_verilog -force $BUILD_PRJ_DIR/cpu_impl_netlist.v -mode timesim -sdf_anno true
#
# STEP#6: generate a bitstream
# 
write_debug_probes -force $BUILD_PRJ_DIR/flyback.ltx
write_bitstream -force $BUILD_PRJ_DIR/flyback.bit

write_sysdef -force -hwdef $BUILD_PRJ_DIR/flyback.hwdef -bitfile $BUILD_PRJ_DIR/flyback.bit -file $BUILD_PRJ_DIR/flyback.hdf
