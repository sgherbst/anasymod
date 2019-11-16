from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.util import back2fwd
from anasymod.probe_config import ProbeConfig
from anasymod.targets import FPGATarget

class TemplEXECUTE_FPGA_SIM(JinjaTempl):
    def __init__(self, target: FPGATarget, start_time: float, stop_time: float, server_addr: str):
        super().__init__(trim_blocks=False, lstrip_blocks=False)
        pcfg = target.prj_cfg

        # read in probe signals from the probe config file
        self.probe_signals = ProbeConfig(probe_cfg_path=target.probe_cfg_path)

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

        # set the path where the CSV file of results from the ILA should be written
        self.output = back2fwd(target.cfg.csv_path)
        self.ila_reset = target.prj_cfg.vivado_config.ila_reset
        #tbd remove vio_reset
        self.vio_reset = target.prj_cfg.vivado_config.vio_reset

        # set the window count to half the ILA depth.  this is required because the window depth will be "2"
        # unfortunately a window depth of "1" is not allowed in "BASIC" capture mode, which needed to allow
        # decimation of the sampling rate.
        self.window_count = str(pcfg.ila_depth/2)

        # calculate decimation ratio
        if stop_time is None:
            decimation_ratio_float = 2.0
        else:
            decimation_ratio_float = ((stop_time-start_time)/pcfg.cfg.dt)/(pcfg.ila_depth/2)

        # enforce a minimum decimation ratio of 2x since the window depth is 2
        decimation_ratio_float = max(decimation_ratio_float, 2.0)

        # we have to subtract 1 from decimation ratio due to the FPGA implementation of this feature
        # that is, a decimation ratio setting of "1" actually corresponds to a decimation factor of "2"; a setting
        # of "2" corresponds to a decimation ratio of "3", and so on.
        decimation_ratio_setting = int(round(decimation_ratio_float)) - 1

        # extract the time signal
        # note that time_signal is actually a list (should have exactly one value)
        if len(self.probe_signals.time_signal) == 0:
            raise Exception('Time signal not found -- check the probe config file.')
        elif len(self.probe_signals.time_signal) > 1:
            raise Exception('Multiple time signals not found  -- check the probe config file.')
        else:
            time_signal = self.probe_signals.time_signal[0]

        # extract properties from the time signal, which is a 3-tuple of strings
        time_name, time_width, time_exponent = time_signal
        time_width = int(time_width)
        time_exponent = int(time_exponent)

        # determine starting time as an integer value
        start_time_int = int(round(start_time*(2**(-time_exponent))))

        # export the decimation ratio, starting time, and time signal name to the template
        self.time_name = time_name
        self.decimation_ratio_setting = str(decimation_ratio_setting)
        self.start_time_int = f"{time_width}'u{start_time_int}"

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

# Code related to non-interactive mode starts here 

# ILA setup
set my_hw_ila [get_hw_ilas]
display_hw_ila_data [get_hw_ila_data hw_ila_data_1 -of_objects $my_hw_ila]

# Trigger setup
# TODO: use starting time as trigger condition
startgroup
set_property CONTROL.CAPTURE_MODE BASIC $my_hw_ila
set_property CONTROL.TRIGGER_POSITION 0 $my_hw_ila
endgroup
set_property TRIGGER_COMPARE_VALUE gt{{subst.start_time_int}} [get_hw_probes {{subst.time_name}} -of_objects $my_hw_ila]

# Capture setup
# TODO: use variable for emu_dec_cmp_probe
# probably always be "2" because unfortunately "1" is not a valid option.
set_property CONTROL.DATA_DEPTH 2 $my_hw_ila
set_property CONTROL.WINDOW_COUNT {{subst.window_count}} $my_hw_ila
set_property CAPTURE_COMPARE_VALUE eq1'b1 [get_hw_probes emu_dec_cmp_probe -of_objects $my_hw_ila]

# VIO: decimation ratio
# TODO: use variable for emu_dec_thr
set_property OUTPUT_VALUE_RADIX UNSIGNED [get_hw_probes vio_gen_i/emu_dec_thr -of_objects $vio_0_i]
set_property OUTPUT_VALUE {{subst.decimation_ratio_setting}} [get_hw_probes vio_gen_i/emu_dec_thr -of_objects $vio_0_i]
commit_hw_vio [get_hw_probes vio_gen_i/emu_dec_thr -of_objects $vio_0_i]

# Radix setup: real numbers
{% for probename, _, _ in subst.probe_signals.analog_signals + subst.probe_signals.time_signal %}
catch {{'{'}}set_property DISPLAY_RADIX SIGNED [get_hw_probes {{probename}}]{{'}'}}
{% endfor %}

# Radix setup: unsigned digital values
# TODO: handle both signed and unsigned digital values
{% for probename, _, _ in subst.probe_signals.digital_signals + subst.probe_signals.reset_signal %}
catch {{'{'}}set_property DISPLAY_RADIX UNSIGNED [get_hw_probes {{probename}}]{{'}'}}
{% endfor %}

# Put design in reset
startgroup
set_property OUTPUT_VALUE 1 $rst_hw_probe
commit_hw_vio $rst_hw_probe
endgroup

# Arm the ILA trigger
run_hw_ila $my_hw_ila

# Take design out of reset
startgroup
set_property OUTPUT_VALUE 0 $rst_hw_probe
commit_hw_vio $rst_hw_probe
endgroup

# Get data from the ILA
wait_on_hw_ila $my_hw_ila
display_hw_ila_data [upload_hw_ila_data $my_hw_ila]

# Write ILA data to a file
write_hw_ila_data -csv_file -force "{{subst.output}}" hw_ila_data_1
'''

def main():
    print(TemplEXECUTE_FPGA_SIM(cfg=EmuConfig()).render())

if __name__ == "__main__":
    main()
