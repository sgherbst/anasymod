
BUILD_SYS_DIR = $(abspath build_system/)

include $(BUILD_SYS_DIR)/includes.mk


# Build targets for IP cores
EMU_BUILD_IP_DIRS = $(foreach d,$(GEN_IPS),$(BUILD_IP_DIR)/$(d))
EMU_IPS = $(foreach d,$(GEN_IPS),$(BUILD_IP_DIR)/$(d)/$(d).xci)

define GENERATE_IP =
$(1)/%.xci : $$(BUILD_IP_TEMPL_DIR)/gen_%.tcl
	@mkdir -p $$(BUILD_IP_DIR)
	rm -rf $(1)
	$$(VIVADO_BATCH) -mode batch -source $$(BUILD_IP_TEMPL_DIR)/gen_$$*.tcl -tclargs $$(BUILD_IP_DIR) $$(EMU_PART) $$*
endef

$(foreach ip,$(EMU_BUILD_IP_DIRS), $(eval $(call GENERATE_IP,$(ip))))


create_sources: $(EMU_IPS)
	#echo $($(abspath $(SOURCE_IP_TEMPL_DIR)))
	echo $(GEN_IPS)
	echo $(EMU_IPS)
	echo $(EMU_BUILD_IP_DIRS)
	echo $(BUILD_IP_TEMPL_DIR)