import os

from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.util import back2fwd
from anasymod.targets import FPGATarget

class TemplPROBE_EXTRACT(JinjaTempl):
    def __init__(self, target: FPGATarget):
        super().__init__()
        self.project_dir = back2fwd(target.project_root)
        self.dcp_path = back2fwd(os.path.join(self.project_dir, target.prj_cfg.vivado_config.project_name + r".runs", r"synth_1", target.cfg.top_module + r".dcp"))

    TEMPLATE_TEXT = '''
# Load synthesized design
open_checkpoint "{{subst.dcp_path}}"

# Extract analog_signals
set ana_s [get_nets -hier -filter {analog_signal == "true"}]

regsub -all "\[{1}[0123456789]+\]{1}" $ana_s "" ana_s
set ana_s [lsort -unique $ana_s]

set ana_s_exponents [list]
set ana_s_widths [list]

foreach {signal} $ana_s {
	append signal [0]
	lappend ana_s_exponents [get_property fixed_point_exponent [get_nets $signal]]
	lappend ana_s_widths [get_property BUS_WIDTH [get_nets $signal]]
}

# Extract time_signal
set time_s [get_nets -hier -filter {time_signal == "true"}]
regsub -all "\[{1}[0123456789]+\]{1}" $time_s "" time_s
set time_s [lsort -unique $time_s]
set time_s_tmp $time_s
append time_s_tmp [0]

set time_s_exponent [get_property fixed_point_exponent [get_nets $time_s_tmp]]
set time_s_width [get_property BUS_WIDTH [get_nets $time_s_tmp]]

# Extract reset_signal
set reset_s [get_nets -hier -filter {reset_signal == "true"}]

# Extract other_signals marked for debug
set other_s [get_nets -hier -filter {digital_signal == "true" && MARK_DEBUG}]

set sb_s [list]
set sb_s [lsearch -regexp -not -inline -all $other_s "\[{1}[0123456789]+\]{1}"]

set mb_s [list]
set mb_s [lsearch -regexp -inline -all $other_s "\[{1}[0123456789]+\]{1}"]
regsub -all "\[{1}[0123456789]+\]{1}" $mb_s "" mb_s
set mb_s [lsort -unique $mb_s]

set mb_s_widths [list]

foreach {signal} $mb_s {
	append signal [0]
	lappend mb_s_widths [get_property BUS_WIDTH [get_nets $signal]]
}

set outputFile [open "{{subst.project_dir}}/probe_config.txt" w]
puts $outputFile [concat "ANALOG:" $ana_s]
puts $outputFile [concat "ANALOG_EXPONENT:" $ana_s_exponents]
puts $outputFile [concat "ANALOG_WIDTH:" $ana_s_widths]
puts $outputFile [concat "TIME:" $time_s]
puts $outputFile [concat "TIME_EXPONENT:" $time_s_exponent]
puts $outputFile [concat "TIME_WIDTH:" $time_s_width]
puts $outputFile [concat "RESET:" $reset_s]
puts $outputFile [concat "SB:" $sb_s]
puts $outputFile [concat "MB:" $mb_s]
puts $outputFile [concat "MB_WIDTH:" $mb_s_widths]
close $outputFile

close_design
'''

def main():
    print(TemplPROBE_EXTRACT(cfg=EmuConfig()).render())

if __name__ == "__main__":
    main()