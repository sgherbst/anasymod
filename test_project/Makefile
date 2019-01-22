
BUILD_SYS_DIR = $(abspath build_system/)

include $(BUILD_SYS_DIR)/includes.mk

#########################################
# emulation commands
#########################################

all: create_sources create_project gen_bitstream

gen_models: $(EMUFLOW_GEN)
	@mkdir -p $(BUILD_MODEL_DIR)
	$(PYTHON) $(EMUFLOW_GEN) -o $(BUILD_MODEL_DIR)
	
gen_templates: $(IP_CORE_GEN)
	$(MAKE) -f $(BUILD_SYS_DIR)/make_gen_templates.mk

create_sources: gen_templates gen_models
	$(MAKE) -f $(BUILD_SYS_DIR)/make_create_sources.mk

create_project: create_project_pm

create_project_pm:
	$(VIVADO_BATCH) -mode batch -source $(BUILD_SYS_DIR)/create_project.tcl -tclargs $(TCL_ARGS_CREATE_PROJECT)

create_project_npm:

gen_bitstream:
	#$(VIVADO_BATCH) -mode tcl -source $(BUILD_SYS_DIR)/gen_bitstream.tcl -tclargs $(TCL_ARGS_GEN_BITSTREAM)
	$(VIVADO_BATCH) -mode batch -source $(BUILD_SYS_DIR)/gen_bitstream.tcl -tclargs $(TCL_ARGS_GEN_BITSTREAM)

simulate:
	$(VIVADO_BATCH) -mode batch -source $(BUILD_SYS_DIR)/run_xsim.tcl -tclargs $(TCL_ARGS_SIM)

#########################################
# cleaning commands
#########################################

clean:
	rm -rf $(BUILD_DIR)
	
clean_project:
	rm -rf $(BUILD_PRJ_DIR)
