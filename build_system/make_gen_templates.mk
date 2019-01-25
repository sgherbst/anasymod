ifndef ANASYMOD_DIR
ANASYMOD_DIR = C:/Inicio_dev/anasymod
endif

include $(ANASYMOD_DIR)/build_system/includes.mk

gen_templates:
	$(PYTHON) $(IP_CORE_GEN) -r $(TOP_DIR) -o $(BUILD_IP_DIR)