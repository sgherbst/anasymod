#########################################
# Example-specific settings
#########################################

EXAMPLE_NAME = filter
DT = 1e-7

#########################################
# User-specific settings
#########################################

ifndef VIVADO_INSTALL_PATH
VIVADO_INSTALL_PATH = C:/Inicio/tools/64/Xilinx-18.2.0.0/Vivado/2018.2
endif

ifndef PYTHON
PYTHON = C:/Inicio/tools/64/Anaconda3-5.2.0.1/python.exe
endif

ifndef GTKWAVE
GTKWAVE = C:/Inicio/tools/common/gtkwave-3.3.65.0/bin/gtkwave.exe
endif

#########################################
# project structure
#########################################

ANASYMOD_DIR = $(abspath ..)

PROJECT_NAME = test_project
TOP_DIR = $(abspath ../$(PROJECT_NAME))

SOURCE_DIR = $(abspath $(TOP_DIR)/source/)
SOURCE_MODEL_DIR = $(abspath $(SOURCE_DIR)/models)
SOURCE_IP_DIR = $(abspath $(SOURCE_DIR)/ips)
SOURCE_CONST_DIR = $(abspath $(SOURCE_DIR)/constraints/)
SOURCE_SIM_TB_DIR = $(abspath $(SOURCE_DIR)/sim_tb/)

BUILD_DIR = $(abspath $(TOP_DIR)/build/)
BUILD_MODEL_DIR = $(abspath $(BUILD_DIR)/models/)
BUILD_IP_DIR = $(abspath $(BUILD_DIR)/ips)
BUILD_CONST_DIR = $(abspath $(BUILD_DIR)/constraints/)
BUILD_IP_TEMPL_DIR = $(abspath $(BUILD_DIR)/ip_gen_scripts)
BUILD_INC_DIR = $(abspath $(BUILD_DIR)/includes/)
BUILD_LIB_DIR = $(abspath $(BUILD_DIR)/libs/)
BUILD_PRJ_DIR = $(abspath $(BUILD_DIR)/$(PROJECT_NAME)/)

BUILD_SYS_DIR = $(abspath $(TOP_DIR)/build_system/)

#########################################
# external tool,lib paths
#########################################

VIVADO_SCRIPTS = $(ANASYMOD_DIR)/vivado_scripts

MSDSL_INSTALL_DIR = $(abspath $(ANASYMOD_DIR)/msdsl/)
MSDSL_LIB_DIR = $(MSDSL_INSTALL_DIR)/src
MSDSL_INC_DIR = $(MSDSL_INSTALL_DIR)/include

EMU_INSTALL_DIR = $(abspath $(ANASYMOD_DIR)/emuflow/)
EMUFLOW_TEST_FOLDER = $(EMU_INSTALL_DIR)/tests/$(EXAMPLE_NAME)
EMUFLOW_GEN = $(EMUFLOW_TEST_FOLDER)/gen.py
EMUFLOW_EXAMPLE_TOP = $(EMUFLOW_TEST_FOLDER)/tb.sv

SVREAL_INSTALL_DIR = $(abspath $(ANASYMOD_DIR)/svreal/)
SVREAL_LIB_DIR = $(SVREAL_INSTALL_DIR)/src
SVREAL_INC_DIR = $(SVREAL_INSTALL_DIR)/include

IP_CORE_GEN = $(SOURCE_DIR)/ip_templ_gen/templ_gen.py
ILA_GEN = $(SOURCE_DIR)/ip_templ_gen/ila_gen.py

VIVADO_BATCH = $(VIVADO_INSTALL_PATH)/bin/vivado.bat -nolog -nojournal
VIVADO_BOARD_FILES = $(VIVADO_INSTALL_PATH)/data/boards/board_files

#########################################
# Vivado options
#########################################
NUM_CORES = 4

# design settings
PART = xc7z020clg400-1
TOP = top
TOP_INST = top_i
GEN_IPS = $(subst gen_,,$(basename $(notdir $(wildcard $(abspath $(BUILD_IP_TEMPL_DIR))/*.tcl))))

#########################################
# Simulation options
#########################################

SIM_TB = test
SIM_TIME = 100ns
DEBUG_LEVEL = all

#########################################
# Emulation options
#########################################

BIT_FILE = $(BUILD_PRJ_DIR)/$(PROJECT_NAME).runs/impl_1/top.bit
LTX_FILE = $(BUILD_PRJ_DIR)/$(PROJECT_NAME).runs/impl_1/top.ltx
PART_HW_DEV = xc7z020_1
VIO_INST_NAME = vio_i/vio_0_i
ILA_INST_NAME = u_ila_0
ILA_OUTPUT_CSV = $(BUILD_DIR)/ila_output.csv
ILA_PROBE_FILE = $(BUILD_PRJ_DIR)/probe_config.txt
ILA_RST_PROBE = rst
VIO_RST_PROBE = vio_i/rst

#########################################
# Viewing options
#########################################

ILA_OUTPUT_VCD = $(BUILD_DIR)/ila_output.vcd

#########################################
# Build target specific tcl args
#########################################

TCL_ARGS_CREATE_PROJECT = $(PROJECT_NAME) $(BUILD_PRJ_DIR) $(PART) $(BUILD_INC_DIR) $(BUILD_LIB_DIR) $(BUILD_MODEL_DIR) $(BUILD_IP_DIR) $(BUILD_CONST_DIR) $(SOURCE_DIR) $(TOP) $(SOURCE_SIM_TB_DIR) $(SVREAL_LIB_DIR) $(SVREAL_INC_DIR) $(MSDSL_LIB_DIR) $(MSDSL_INC_DIR) $(EMUFLOW_EXAMPLE_TOP)
TCL_ARGS_SYNTH_DESIGN = $(PROJECT_NAME) $(BUILD_PRJ_DIR) $(NUM_CORES)
TCL_ARGS_GEN_BITSTREAM = $(PROJECT_NAME) $(BUILD_PRJ_DIR) $(NUM_CORES)
TCL_ARGS_SIM = $(PROJECT_NAME) $(BUILD_PRJ_DIR) $(SIM_TB) $(TOP_INST) $(SIM_TIME) $(DEBUG_LEVEL) $(DT)
TCL_ARGS_EMU = $(BIT_FILE) $(LTX_FILE) $(PART_HW_DEV) $(VIO_INST_NAME) $(ILA_INST_NAME) $(ILA_OUTPUT_CSV) $(ILA_PROBE_FILE) $(ILA_RST_PROBE) $(VIO_RST_PROBE)