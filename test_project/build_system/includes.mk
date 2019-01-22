#########################################
# project structure
#########################################

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
BUILD_IP_TEMPL_DIR = $(abspath $(BUILD_DIR)/ip_gen_scripts)
BUILD_INC_DIR = $(abspath $(BUILD_DIR)/includes/)
BUILD_LIB_DIR = $(abspath $(BUILD_DIR)/libs/)
BUILD_PRJ_DIR = $(abspath $(BUILD_DIR)/$(PROJECT_NAME)/)

BUILD_SYS_DIR = $(abspath $(TOP_DIR)/build_system/)


#########################################
# external tool,lib paths
#########################################
EXAMPLE_NAME = filter
ANASYMOD_DIR = C:/Inicio_dev/anasymod

MSDSL_INSTALL_DIR = $(abspath $(ANASYMOD_DIR)/msdsl/)
MSDSL_LIB_DIR = $(MSDSL_INSTALL_DIR)/src
MSDSL_INC_DIR = $(MSDSL_INSTALL_DIR)/include

EMU_INSTALL_DIR = $(abspath $(ANASYMOD_DIR)/emuflow/)
EMUFLOW_GEN = $(EMU_INSTALL_DIR)/tests/$(EXAMPLE_NAME)/gen.py
EMUFLOW_EXAMPLE_TOP = $(EMU_INSTALL_DIR)/tests/$(EXAMPLE_NAME)/tb.sv

SVREAL_INSTALL_DIR = $(abspath $(ANASYMOD_DIR)/svreal/)
SVREAL_LIB_DIR = $(SVREAL_INSTALL_DIR)/src
SVREAL_INC_DIR = $(SVREAL_INSTALL_DIR)/include

IP_CORE_GEN = $(SOURCE_DIR)/ip_templ_gen/templ_gen.py

VIVADO_INSTALL_PATH = C:/Xilinx/Vivado/2017.3
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
# Gerneral options
#########################################

DT = 1e-7

#########################################
# Simulation options
#########################################

SIM_TB = test
SIM_TIME = 100ns
DEBUG_LEVEL = all

#########################################
# Build target specific tcl args
#########################################
TCL_ARGS_CREATE_PROJECT = $(PROJECT_NAME) $(BUILD_PRJ_DIR) $(PART) $(BUILD_INC_DIR) $(BUILD_LIB_DIR) $(BUILD_MODEL_DIR) $(BUILD_IP_DIR) $(SOURCE_CONST_DIR) $(SOURCE_DIR) $(TOP) $(SOURCE_SIM_TB_DIR) $(SVREAL_LIB_DIR) $(SVREAL_INC_DIR) $(MSDSL_LIB_DIR) $(MSDSL_INC_DIR) $(EMUFLOW_EXAMPLE_TOP)
TCL_ARGS_GEN_BITSTREAM = $(PROJECT_NAME) $(BUILD_PRJ_DIR) $(NUM_CORES)
TCL_ARGS_SIM = $(PROJECT_NAME) $(BUILD_PRJ_DIR) $(SIM_TB) $(TOP_INST) $(SIM_TIME) $(DEBUG_LEVEL) $(DT)