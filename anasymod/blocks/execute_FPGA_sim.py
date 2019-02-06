import os

from anasymod.templ import JinjaTempl
from anasymod.util import next_pow_2
from anasymod.config import EmuConfig
from anasymod.util import path4vivado
from anasymod.codegen import CodeGenerator
from anasymod.probe_config import ProbeConfig

class TemplEXECUTE_FPGA_SIM(JinjaTempl):
    def __init__(self, cfg: EmuConfig, line_ending='\n'):
        self.project_dir = path4vivado(cfg.vivado_config.project_root)

        self.toggle_reset_template = CodeGenerator()
        self._toggle_reset()
        self.toggle_reset = self.toggle_reset_template.dump()
        self.probe_signals = ProbeConfig(probe_cfg_path=cfg.vivado_config.probe_cfg_path)

        # Necessary variables
        self.bit_file = path4vivado(r"{0}".format(cfg.vivado_config.bitfile_path))
        self.ltx_file = path4vivado(r"{0}".format(cfg.vivado_config.ltxfile_path))
        self.device_name = cfg.fpga_board_config.short_part_name

        self.vio_name = cfg.vivado_config.vio_inst_name
        self.ila_name = cfg.vivado_config.ila_inst_name
        self.output = path4vivado(r"{0}".format(cfg.csv_path))
        self.ila_reset = cfg.vivado_config.ila_reset
        #tbd remove vio_reset
        self.vio_reset = cfg.vivado_config.vio_reset

    TEMPLATE_TEXT = '''
# Connect to hardware
open_hw
catch {disconnect_hw_server}
connect_hw_server
open_hw_target

# Configure files to be programmed
set my_hw_device [get_hw_devices {{subst.device_name}}*]
set_property PROGRAM.FILE {{subst.bit_file}} $my_hw_device
set_property PROBES.FILE {{subst.ltx_file}} $my_hw_device
set_property FULL_PROBES.FILE {{subst.ltx_file}} $my_hw_device

# Program the device
current_hw_device $my_hw_device
program_hw_devices $my_hw_device
refresh_hw_device $my_hw_device

# ILA setup
set my_hw_ila [get_hw_ilas -of_objects $my_hw_device -filter CELL_NAME=~"{{subst.ila_name}}"]
display_hw_ila_data [get_hw_ila_data hw_ila_data_1 -of_objects $my_hw_ila]

# VIO setup
set my_hw_vio [get_hw_vios -of_objects $my_hw_device -filter CELL_NAME=~"{{subst.vio_name}}"]
set rst_hw_probe [get_hw_probes * -of_objects $my_hw_vio]

# Trigger setup
set_property CONTROL.TRIGGER_POSITION 0 $my_hw_ila
set_property TRIGGER_COMPARE_VALUE eq1'bF [get_hw_probes {{subst.ila_reset}} -of_objects $my_hw_ila]

# Radix setup
{% for probename, _, _ in subst.probe_signals.analog_signals + subst.probe_signals.time_signal %}
catch {{'{'}}set_property DISPLAY_RADIX SIGNED [get_hw_probes {{probename}}]{{'}'}}
{% endfor %}

# Toggle the reset VIO once to put it in a known state
{{subst.toggle_reset}}

# Arm the ILA trigger
run_hw_ila $my_hw_ila

# Toggle reset to cause emulation to run
{{subst.toggle_reset}}

# Get data from the ILA
wait_on_hw_ila $my_hw_ila
display_hw_ila_data [upload_hw_ila_data $my_hw_ila]

# Write ILA data to a file
write_hw_ila_data -csv_file -force {{subst.output}} hw_ila_data_1
'''

    def assign_reset(self, rst_hw_probe, value):
        self.toggle_reset_template.println("""startgroup
set_property OUTPUT_VALUE {0} {1}
commit_hw_vio {1}
endgroup""".format(value, rst_hw_probe))

    def _toggle_reset(self, rst_hw_probe=r"$rst_hw_probe"):
        self.assign_reset(rst_hw_probe, 1)
        self.assign_reset(rst_hw_probe, 0)

def main():
    print(TemplEXECUTE_FPGA_SIM(cfg=EmuConfig()).render())

if __name__ == "__main__":
    main()