# References:
# 1. https://www.xilinx.com/html_docs/xilinx2018_1/SDK_Doc/xsct/use_cases/xsdb_standalone_app_debug.html
# 2. https://github.com/Digilent/Arty-Z7-20-linux_bd/blob/master/sdk/.sdk/launch_scripts/xilinx_c-c%2B%2B_application_(system_debugger)/system_debugger_using_debug_video.elf_on_local.tcl
# 3. https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/18842240/Programming+QSPI+from+U-boot+ZC702
# 4. https://github.com/analogdevicesinc/no-OS/blob/master/scripts/xsdb.tcl
# 5. https://www.xilinx.com/html_docs/xilinx2018_1/SDK_Doc/xsct/use_cases/xsdb_debug_app_zynqmp.html

class TemplXSCTProgram:
    def __init__(self, sdk_path, bit_path, hw_path, tcl_path,
                 sw_name='sw', program_fpga=True, reset_system=True,
                 loadhw=True, init_cpu=True, download=True,
                 run=True, connect=True, is_ultrascale=False):

        # initialize text
        self.text = ''

        ##################
        # apply commands #
        ##################

        # connect
        if connect:
            self.connect()

        # reset_system
        if reset_system:
            self.reset_system()

        # program_fpga
        if program_fpga:
            self.program_fpga(bit_path=bit_path,
                              is_ultrascale=is_ultrascale)

        # loadhw
        if loadhw:
            self.loadhw(hw_path)

        # init_cpu
        if init_cpu:
            self.init_cpu(tcl_path=tcl_path,
                          is_ultrascale=is_ultrascale)

        # download
        if download:
            self.download(elf_path=str(sdk_path / sw_name / 'Debug' / sw_name) + '.elf',
                          is_ultrascale=is_ultrascale)

        # run
        if run:
            self.run()

        self.puts("Program started.")

    def line(self, s='', nl='\n'):
        self.text += f'{s}{nl}'

    def puts(self, s):
        self.line(f'puts "{s}"')

    def set_target(self, pattern):
        self.line(f'targets -set -filter {{name =~ "{pattern}"}}')

    def connect(self):
        self.puts('Connecting to the HW server...')
        self.line('connect')
        self.line()

    def reset_system(self):
        self.puts('Resetting the system...')
        self.set_target('APU*')
        self.line('stop')
        self.line('rst')
        self.line()

    def program_fpga(self, bit_path, is_ultrascale):
        self.puts('Programming the FPGA...')
        if is_ultrascale:
            self.set_target('PSU')
        else:
            self.set_target('xc7z*')
        self.line(f'fpga "{bit_path}"')
        self.line()

    def loadhw(self, hw_path):
        self.puts('Setting up the debugger...')
        self.line(f'loadhw "{hw_path}"')
        self.line()

    def init_cpu(self, tcl_path, is_ultrascale):
        self.puts('Initializing the processor...')
        self.set_target('APU*')
        self.line(f'source "{tcl_path}"')
        if is_ultrascale:
            self.puts('Calling psu_init...')
            self.line('psu_init')
            self.line('after 1000')  # TODO: is this needed?

            self.puts('Calling psu_post_config...')
            self.line('psu_post_config')
            self.line('after 1000')  # TODO: is this needed?

            self.puts('Calling psu_ps_pl_isolation_removal...')
            self.line('psu_ps_pl_isolation_removal')
            self.line('after 1000')  # TODO: is this needed?

            self.puts('Calling psu_ps_pl_reset_config...')
            self.line('psu_ps_pl_reset_config')
            self.line('after 1000')  # TODO: is this needed?
        else:
            self.line('ps7_init')
            self.line('ps7_post_config')
        self.line()

    def download(self, elf_path, is_ultrascale):
        self.puts('Downloading the program...')
        if is_ultrascale:
            self.set_target('*Cortex-A53 #0*')
        else:
            self.set_target('*Cortex-A9 MPCore #0*')
        self.line(f'dow "{elf_path}"')
        self.line()

    def run(self):
        self.puts('Starting the program...')
        self.line('con')
        self.line()
