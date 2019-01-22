
BUILD_SYS_DIR = $(abspath build_system/)

include $(BUILD_SYS_DIR)/includes.mk

gen_templates:
	$(PYTHON) $(IP_CORE_GEN) -r $(TOP_DIR) -o $(BUILD_IP_DIR)