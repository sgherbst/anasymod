class TemplXSCTProgram:
    def __init__(self, sdk_path, cpu_filter='"ARM*#0"', hw_name='hw',
                 top_name='top', sw_name='sw'):

        self.text = f'''\
# References:
# 1. https://www.xilinx.com/html_docs/xilinx2018_1/SDK_Doc/xsct/use_cases/xsdb_standalone_app_debug.html
# 2. https://github.com/Digilent/Arty-Z7-20-linux_bd/blob/master/sdk/.sdk/launch_scripts/xilinx_c-c%2B%2B_application_(system_debugger)/system_debugger_using_debug_video.elf_on_local.tcl
    
# connect to the HW server
puts "Connecting to the HW server..."
connect

# select the CPU
puts "Selecting the CPU..."
targets -set -filter {{name =~ {cpu_filter}}}

# reset the system
puts "Resetting the system..."
rst

# program the FPGA
puts "Programming the FPGA..."
fpga "{sdk_path / hw_name / top_name}.bit"

# make the debugger aware of the memory map
# TODO: is this needed?
puts "Setting up the debugger..."
loadhw "{sdk_path / top_name}.hdf"

# initialize the processor
puts "Initializing the processor..."
source "{sdk_path / hw_name / 'ps7_init'}.tcl"
ps7_init
ps7_post_config

# download the program
puts "Downloading the program..."
dow "{sdk_path / sw_name / 'Debug' / sw_name}.elf"

# run program
puts "Starting the program..."
con

# print message for debugging purposes
puts "Program started."'''
