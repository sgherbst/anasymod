# STEP#1: define the output directory area.
#
set PROJECT_NAME [lindex $argv 0]
set BUILD_PRJ_DIR [lindex $argv 1]
set PART [lindex $argv 2]
set BUILD_INC_DIR [lindex $argv 3]
set BUILD_LIB_DIR [lindex $argv 4]
set BUILD_MODEL_DIR [lindex $argv 5]
set BUILD_IP_DIR [lindex $argv 6]
set BUILD_CONST_DIR [lindex $argv 7]
set SOURCE_CONST_DIR [lindex $argv 8]
set PROJECT_SOURCE_DIR [lindex $argv 9]
set TOP [lindex $argv 10]
set PROJECT_SOURCE_SIM_TB_DIR [lindex $argv 11]
set SVREAL_LIB_DIR [lindex $argv 12]
set SVREAL_INC_DIR [lindex $argv 13]
set MSDSL_LIB_DIR [lindex $argv 14]
set MSDSL_INC_DIR [lindex $argv 15]
set EMUFLOW_EXAMPLE_TOP [lindex $argv 16]


#puts PROJECT_NAME:$PROJECT_NAME
#puts BUILD_PRJ_DIR:$BUILD_PRJ_DIR
#puts PART:$PART
#puts BUILD_INC_DIR:$BUILD_INC_DIR
#puts BUILD_LIB_DIR:$BUILD_LIB_DIR
#puts BUILD_MODEL_DIR:$BUILD_MODEL_DIR
#puts BUILD_IP_DIR:$BUILD_IP_DIR
#puts BUILD_CONST_DIR:$BUILD_CONST_DIR
#puts SOURCE_CONST_DIR:$SOURCE_CONST_DIR
#puts PROJECT_SOURCE_DIR:$SOURCE_DIR
#puts TOP:$TOP
#puts PROJECT_SOURCE_SIM_TB_DIR:$PROJECT_SOURCE_SIM_TB_DIR
#puts SVREAL_LIB_DIR:$SVREAL_LIB_DIR
#puts SVREAL_INC_DIR:$SVREAL_INC_DIR
#puts MSDSL_LIB_DIR:$MSDSL_LIB_DIR
#puts MSDSL_INC_DIR:$MSDSL_INC_DIR
#puts EMUFLOW_EXAMPLE_TOP:$EMUFLOW_EXAMPLE_TOP

create_project $PROJECT_NAME -dir $BUILD_PRJ_DIR -force -part $PART

#
# STEP#2: setup design sources and constraints
#


read_verilog  [ glob $SVREAL_LIB_DIR/*.*v ]
read_verilog  [ glob $SVREAL_INC_DIR/*.*v ]
read_verilog  [ glob $MSDSL_LIB_DIR/*.*v ]
read_verilog  [ glob $MSDSL_INC_DIR/*.*v ]

read_verilog  [ glob $EMUFLOW_EXAMPLE_TOP ]

read_verilog  [ glob $BUILD_MODEL_DIR/*.*v ]
read_verilog  [ glob $PROJECT_SOURCE_DIR/*.*v ]
read_verilog  [ glob $PROJECT_SOURCE_SIM_TB_DIR/*.*v ]

set_property used_in_synthesis false [get_files  $PROJECT_SOURCE_SIM_TB_DIR/*.*v]
set_property used_in_implementation false [get_files  $PROJECT_SOURCE_SIM_TB_DIR/*.*v]

# read_ip [ glob $BUILD_IP_ROOT/*/*.xci ]
# puts [ glob $BUILD_IP_ROOT/*/*.xci ]

read_ip  [ glob $BUILD_IP_DIR/*/*.xci ]
#read_ip $BUILD_IP_ROOT/clk_wiz_0/clk_wiz_0.xci
#read_ip $BUILD_IP_ROOT/vio_0/vio_0.xci

#read_verilog -library work [ glob C:/Inicio_dev/flyback/models/design_1_wrapper.v ]
#read_checkpoint
#read_bd C:/Inicio_dev/flyback/emu_build/bd/myproj/project_1.srcs/sources_1/bd/design_1/design_1.bd

read_xdc  [ glob $BUILD_CONST_DIR/*.xdc $SOURCE_CONST_DIR/*.xdc]

set_property file_type {Verilog Header} [get_files  $SVREAL_INC_DIR/*.sv]
set_property file_type {Verilog Header} [get_files  $MSDSL_INC_DIR/*.sv]


set_property top $TOP [current_fileset]

close_project