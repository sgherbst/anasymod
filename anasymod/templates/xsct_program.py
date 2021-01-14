from anasymod.util import back2fwd

# References:
# 1. https://www.xilinx.com/html_docs/xilinx2018_1/SDK_Doc/xsct/use_cases/xsdb_standalone_app_debug.html
# 2. https://github.com/Digilent/Arty-Z7-20-linux_bd/blob/master/sdk/.sdk/launch_scripts/xilinx_c-c%2B%2B_application_(system_debugger)/system_debugger_using_debug_video.elf_on_local.tcl
# 3. https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/18842240/Programming+QSPI+from+U-boot+ZC702
# 4. https://github.com/analogdevicesinc/no-OS/blob/master/scripts/xsdb.tcl
# 5. https://www.xilinx.com/html_docs/xilinx2018_1/SDK_Doc/xsct/use_cases/xsdb_debug_app_zynqmp.html

from pathlib import Path

class TemplXSCTProgram:
    def __init__(self, sdk_path, bit_path, hw_path, tcl_path, pcfg,
                 sw_name='sw', program_fpga=True, reset_system=True,
                 loadhw=True, init_cpu=True, download=True,
                 run=True, connect=True, is_ultrascale=False,
                 xsct_install_dir=None, no_rev_check=False,
                 server_addr=None):

        # save settings
        self.sdk_path = sdk_path
        self.bit_path = bit_path
        self.hw_path = hw_path
        self.tcl_path = tcl_path
        self.sw_name = sw_name
        self.is_ultrascale = is_ultrascale
        self.xsct_install_dir = xsct_install_dir
        self.no_rev_check = no_rev_check
        self.pcfg  = pcfg

        # initialize text
        self.text = ''

        ##################
        # apply commands #
        ##################

        # connect
        if connect:
            self.connect(server_addr=server_addr)

        # load utility functions for Zynq MP
        if is_ultrascale:
            self.puts('Load utility functions for Zynq MP.')
            zynqmp_utils_tcl = (Path(self.xsct_install_dir) / 'scripts' /
                                'vitis' / 'util' / 'zynqmp_utils.tcl')
            self.line(f'source "{zynqmp_utils_tcl.as_posix()}"')
            self.line()

        # reset_system
        if reset_system:
            self.reset_system()

        # program_fpga
        if program_fpga:
            self.program_fpga()

        # loadhw
        if loadhw:
            self.loadhw(hw_path)

        # disable access protection for dow, mrd, and mwr commands
        if is_ultrascale:
            self.puts('Disable access protection for dow, mrd, and mwr commands.')
            self.line('configparams force-mem-access 1')
            self.line()

        # init_cpu
        if init_cpu:
            self.init_cpu()

        # download
        if download:
            self.download()

        # enable access protection for dow, mrd, and mwr commands
        if is_ultrascale:
            self.puts('Enable access protection for dow, mrd, and mwr commands.')
            self.line('configparams force-mem-access 0')
            self.line()

        # run
        if run:
            self.run()

        # print message indicating that program has been loaded
        self.puts("Program started.")

    def line(self, s='', nl='\n'):
        self.text += f'{s}{nl}'

    def puts(self, s):
        self.line(f'puts "{s}"')

    def set_target(self, pattern):
        self.line(f'targets -set -filter {{name =~ "{pattern}"}}')

    def connect(self, server_addr):
        self.puts('Connecting to the HW server...')
        if server_addr is not None:
            self.line(f'connect -url {server_addr}')
        else:
            self.line('connect')
        self.line()

    def reset_system(self):
        self.puts('Resetting the system...')
        self.set_target('APU*')
        if self.is_ultrascale:
            self.line('rst -system')
            self.line('after 3000')
        else:
            self.line('stop')
            self.line('rst')
        self.line()

    def program_fpga(self):
        self.puts('Programming the FPGA...')
        if self.is_ultrascale:
            self.set_target('PSU')
        else:
            self.set_target('xc7z*')
        cmd = []
        cmd += ['fpga']
        cmd += ['-f', f'"{self.bit_path.as_posix()}"']
        if self.no_rev_check:
            cmd += ['-no-revision-check']
        self.line(' '.join(cmd))
        self.line()

    def loadhw(self, hw_path):
        if self.pcfg.vivado_config.version_year < 2020:
            # For Vivado 2018.2, it is necessary to use the .hdf rather than the .sysdef file.
            hw_path = hw_path.with_suffix('.hdf')

        self.puts('Setting up the debugger...')
        self.set_target('APU*')
        cmd = []
        cmd += ['loadhw']
        cmd += ['-hw', f'"{hw_path.as_posix()}"']
        if self.is_ultrascale:
            cmd += ['-mem-ranges [list {0x80000000 0xbfffffff} '
                                      '{0x400000000 0x5ffffffff} '
                                      '{0x1000000000 0x7fffffffff}]']
            cmd += ['-regs']
        self.line(' '.join(cmd))
        self.line()

    def init_cpu(self):
        self.puts('Initializing the processor...')
        if self.is_ultrascale:
            # set the boot mode
            self.set_target('APU*')
            self.line('set mode [expr [mrd -value 0xFF5E0200] & 0xf]')
            # reset the processor
            self.set_target('*A53*#0')
            self.line('rst -processor')
            # download the FSBL ELF is located
            fsbl_path = (Path(self.sdk_path) / 'top' / 'export' / 'top' /
                         'sw' / 'top' / 'boot' / 'fsbl.elf')
            self.line(f'dow "{fsbl_path.as_posix()}"')
            # wait for FSBL to finish running
            self.line('set bp_0_6_fsbl_bp [bpadd -addr &XFsbl_Exit]')
            self.line('con -block -timeout 60')
            self.line('bpremove $bp_0_6_fsbl_bp')
        else:
            self.set_target('APU*')
            self.line(f'source "{self.tcl_path.as_posix()}"')
            self.line('ps7_init')
            self.line('ps7_post_config')
        self.line()

    def download(self):
        elf_path = str(self.sdk_path / self.sw_name / 'Debug' / self.sw_name) + '.elf'
        self.puts('Downloading the program...')
        if self.is_ultrascale:
            self.set_target('*A53*#0')
            self.line('rst -processor')
        else:
            self.set_target('*Cortex-A9 MPCore #0*')
        self.line(f'dow "{back2fwd(elf_path)}"')
        self.line()

    def run(self):
        self.puts('Starting the program...')
        self.line('con')
        self.line()
