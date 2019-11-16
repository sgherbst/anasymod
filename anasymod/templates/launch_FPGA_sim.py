from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.util import back2fwd
from anasymod.targets import FPGATarget
from anasymod.generators.gen_api import SVAPI

class TemplLAUNCH_FPGA_SIM(JinjaTempl):
    def __init__(self, target: FPGATarget, server_addr: str):
        super().__init__(trim_blocks=False, lstrip_blocks=False)
        pcfg = target.prj_cfg
        scfg = target.str_cfg

        # set server address
        self.server_addr = server_addr

        # set the paths to the BIT and LTX file
        self.bit_file = back2fwd(target.bitfile_path)
        self.ltx_file = back2fwd(target.ltxfile_path)

        # set the JTAG frequency.  sometimes it is useful to try a slower frequency than default if there
        # are problems with the debug hub clock
        self.jtag_freq = str(int(pcfg.cfg.jtag_freq))

        # set the "short" device name which is used to distinguish the FPGA part from other USB devices
        self.device_name = pcfg.board.short_part_name

        # add vio probe aliases according to entries in ctrl_io.config file
        ctrl_ios = [scfg.reset_ctrl] + scfg.digital_ctrl_inputs + scfg.analog_ctrl_outputs + scfg.digital_ctrl_inputs + scfg.digital_ctrl_outputs

        self.ctrl_io_aliases = SVAPI()
        for io in ctrl_ios:
            self.ctrl_io_aliases.writeln(f'set {io.name} [get_hw_probes "sim_ctrl_gen_i/{io.name}" -of_objects $vio_0_i]')

    TEMPLATE_TEXT = '''
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
set vio_0_i [get_hw_vios -of_objects $hw_device -filter {CELL_NAME=~"sim_ctrl_gen_i/vio_0_i"}]
set rst_hw_probe [get_hw_probes *rst* -of_objects $vio_0_i]

# Code related to interactive mode starts here

set_property CORE_REFRESH_RATE_MS 0 $vio_0_i

# set aliases to VIO probes
{{subst.ctrl_io_aliases.text}}

# configure VIO radix
# TODO: this shall be specified in the ctrl_io.config file
set_property INPUT_VALUE_RADIX UNSIGNED $number
'''

def main():
    print(TemplLAUNCH_FPGA_SIM(target=FPGATarget(prj_cfg=EmuConfig(root='', cfg_file=''), plugins=[], name=r"test"), server_addr='').render())

if __name__ == "__main__":
    main()
