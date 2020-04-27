from anasymod.templates.templ import JinjaTempl
from anasymod.util import back2fwd
from anasymod.generators.gen_api import SVAPI
from anasymod.config import EmuConfig
from anasymod.structures.structure_config import StructureConfig

class TemplLAUNCH_FPGA_SIM(JinjaTempl):
    def __init__(self, pcfg: EmuConfig, scfg: StructureConfig, bitfile_path, ltxfile_path, server_addr: str):
        super().__init__(trim_blocks=False, lstrip_blocks=False)
        pcfg = pcfg
        scfg = scfg

        # set server address
        self.server_addr = server_addr

        # set the paths to the BIT and LTX file
        self.bit_file = back2fwd(bitfile_path)
        self.ltx_file = back2fwd(ltxfile_path)

        # set the JTAG frequency.  sometimes it is useful to try a slower frequency than default if there
        # are problems with the debug hub clock
        self.jtag_freq = str(int(pcfg.cfg.jtag_freq))

        # set the "short" device name which is used to distinguish the FPGA part from other USB devices
        self.device_name = pcfg.board.short_part_name

        # Set aliases for VIOs
        self.ctrl_io_aliases = SVAPI()
        for io in scfg.digital_ctrl_inputs + scfg.digital_ctrl_outputs + \
                  scfg.analog_ctrl_inputs + scfg.analog_ctrl_outputs:
            self.ctrl_io_aliases.writeln(f'set {io.name} [get_hw_probes "sim_ctrl_gen_i/{io.name}" -of_objects $vio_0_i]')

        # Set radix for VIOs
        self.ctrl_io_radix = SVAPI()
        for digital_in in scfg.digital_ctrl_inputs:
            signed = 'SIGNED' if digital_in.signed else 'UNSIGNED'
            self.ctrl_io_radix.writeln(f'set_property OUTPUT_VALUE_RADIX {signed} ${digital_in.name}')

        for digital_out in scfg.digital_ctrl_outputs:
            signed = 'SIGNED' if digital_out.signed else 'UNSIGNED'
            self.ctrl_io_radix.writeln(f'set_property INPUT_VALUE_RADIX {signed} ${digital_out.name}')

        for analog_in in scfg.analog_ctrl_inputs:
            self.ctrl_io_radix.writeln(f'set_property OUTPUT_VALUE_RADIX SIGNED ${analog_in.name}')

        for analog_out in scfg.analog_ctrl_outputs:
            self.ctrl_io_radix.writeln(f'set_property INPUT_VALUE_RADIX SIGNED ${analog_out.name}')

        # Set aliases for probes
        self.probe_aliases = SVAPI()
        for probe in scfg.digital_probes + scfg.analog_probes + [scfg.time_probe]:
            self.probe_aliases.writeln(f'set {probe.name} [get_hw_probes "trace_port_gen_i/{probe.name}" -of_objects $ila_0_i]')

        # Set radix for probes
        self.probe_radix = SVAPI()
        for digital_probe in (scfg.digital_probes + [scfg.time_probe]):
            signed = 'SIGNED' if digital_probe.signed else 'UNSIGNED'
            self.probe_radix.writeln(f'set_property DISPLAY_RADIX {signed} ${digital_probe.name}')

        for analog_probe in scfg.analog_probes:
            self.probe_radix.writeln(f'set_property DISPLAY_RADIX SIGNED ${analog_probe.name}')

    TEMPLATE_TEXT = '''\
# Connect to hardware
open_hw
catch {disconnect_hw_server}
{% if subst.server_addr is none %}
connect_hw_server
{% else %}
connect_hw_server -url {{subst.server_addr}}
{% endif %}
set_property PARAM.FREQUENCY {{subst.jtag_freq}} [get_hw_targets]
open_hw_target

# Configure files to be programmed
set my_hw_device [get_hw_devices {{subst.device_name}}*]
current_hw_device $my_hw_device
refresh_hw_device $my_hw_device
set_property PROGRAM.FILE "{{subst.bit_file}}" $my_hw_device
set_property PROBES.FILE "{{subst.ltx_file}}" $my_hw_device
set_property FULL_PROBES.FILE "{{subst.ltx_file}}" $my_hw_device

# Program the device
program_hw_devices $my_hw_device
refresh_hw_device $my_hw_device

# VIO setup
set vio_0_i [get_hw_vios -of_objects $my_hw_device -filter {CELL_NAME=~"sim_ctrl_gen_i/vio_0_i"}]
set rst_hw_probe [get_hw_probes *rst* -of_objects $vio_0_i]

# ILA setup
# set ila_0_i [get_hw_ilas] // this is how it was written beforehand
set ila_0_i [get_hw_ilas -of_objects $my_hw_device -filter {CELL_NAME=~"trace_port_gen_i/ila_0_i"}]
#display_hw_ila_data [get_hw_ila_data hw_ila_data_1 -of_objects $ila_0_i]

##############################################
# Code related to interactive mode starts here
##############################################

# configure VIO for low latency
set_property CORE_REFRESH_RATE_MS 0 $vio_0_i

# set aliases to VIOs
{{subst.ctrl_io_aliases.text}}

# configure VIO radix
{{subst.ctrl_io_radix.text}}

# configure the ILA for low latency
set_property CORE_REFRESH_RATE_MS 0 $ila_0_i

# set aliases to ILA probes
{{subst.probe_aliases.text}}

# configure radix for ILA probes
{{subst.probe_radix.text}}
'''

def main():
    print(TemplLAUNCH_FPGA_SIM(target=FPGATarget(prj_cfg=EmuConfig(root='', cfg_file=''), plugins=[], name=r"test"), server_addr='').render())

if __name__ == "__main__":
    main()
