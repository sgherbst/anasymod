import os.path
import multiprocessing
import shutil

from anasymod.files import which, get_full_path, get_from_module
from anasymod.util import path4vivado, back2fwd
from os import environ as env

class EmuConfig:
    def __init__(self, vivado=None, iverilog=None, vvp=None, gtkwave=None):
        # source files
        self.sim_only_verilog_sources = []
        self.synth_only_verilog_sources = []
        self.verilog_sources = []

        # header files
        self.sim_only_verilog_headers = []
        self.synth_only_verilog_headers = []
        self.verilog_headers = []

        # build root
        self.build_root = get_full_path('build')

        # definitions
        self.sim_only_verilog_defines = []
        self.synth_only_verilog_defines = []
        self.verilog_defines = []

        # other options
        self.top_module = 'top'
        self.emu_clk_freq = 25e6
        self.dbg_hub_clk_freq = 100e6
        self.dt = None
        self.tstop = None
        self.ila_depth = None
        self.preprocess_only = False
        self.csv_name = f"{self.top_module}.csv"
        self.vcd_name = f"{self.top_module}.vcd"

        # FPGA board configuration
        self.fpga_board_config = FPGABoardConfig()

        # Vivado configuration
        self.vivado_config = VivadoConfig(parent=self, vivado=vivado)

        # GtkWave configuration
        self.gtkwave_config = GtkWaveConfig(parent=self, gtkwave=gtkwave)

        # Icarus configuration
        self.icarus_config = IcarusConfig(parent=self, iverilog=iverilog, vvp=vvp)

    @property
    def sim_verilog_sources(self):
        return self.verilog_sources + self.sim_only_verilog_sources

    @property
    def sim_verilog_headers(self):
        return self.verilog_headers + self.sim_only_verilog_headers

    @property
    def synth_verilog_sources(self):
        return self.verilog_sources + self.synth_only_verilog_sources

    @property
    def synth_verilog_headers(self):
        return self.verilog_headers + self.synth_only_verilog_headers

    @property
    def sim_verilog_defines(self):
        return self.verilog_defines + self.sim_only_verilog_defines

    @property
    def synth_verilog_defines(self):
        return self.verilog_defines + self.synth_only_verilog_defines

    @property
    def vcd_path(self):
        return os.path.join(self.build_root, self.vcd_name)

    @property
    def csv_path(self):
        return os.path.join(self.build_root, self.csv_name)

    def set_dt(self, value):
        self.dt = value
        self.verilog_defines.append(f'DT_MSDSL={value}')

    def set_tstop(self, value):
        self.tstop = value
        self.verilog_defines.append(f'TSTOP_MSDSL={value}')

    def setup_vcd(self):
        self.sim_only_verilog_defines.append(f'VCD_FILE_MSDSL={back2fwd(self.vcd_path)}')

    def setup_ila(self):
        self.ila_depth = int(self.tstop/self.dt)

class MsEmuConfig(EmuConfig):
    def __init__(self):
        super().__init__()

        # load msdsl library
        self.verilog_headers.append(get_from_module('msdsl', 'include', '*.sv'))
        self.verilog_sources.append(get_from_module('msdsl', 'src', '*.sv'))

        # load svreal library
        self.verilog_sources.append(get_from_module('svreal', 'src', '*.sv'))
        self.verilog_headers.append(get_from_module('svreal', 'include', '*.sv'))

        # top-level structure
        self.sim_only_verilog_sources.append(get_from_module('anasymod', 'verilog', 'top_sim.sv'))
        self.synth_only_verilog_sources.append(get_from_module('anasymod', 'verilog', 'top_synth.sv'))
        self.verilog_defines.append('CLK_MSDSL=top.emu_clk')
        self.verilog_defines.append('RST_MSDSL=top.emu_rst')

        # simulation options
        self.sim_only_verilog_defines.append('SIMULATION_MODE_MSDSL')

class FPGABoardConfig():
    def __init__(self):
        self.clk_pin = 'H16'
        self.clk_io = 'LVCMOS33'
        self.clk_freq = 125e6
        self.full_part_name = 'xc7z020clg400-1'
        self.short_part_name = 'xc7z020'

class VivadoConfig():
    def __init__(self, parent: EmuConfig, vivado):
        # save reference to parent config
        self.parent = parent

        # set project name
        self.project_name = 'project'

        # set path to Vivado
        hints = [lambda: os.path.join(env['VIVADO_INSTALL_PATH'], 'bin')]
        self.vivado = vivado if vivado is not None else find_tool(name='vivado', hints=hints)

        # set various project options
        self.num_cores = multiprocessing.cpu_count()
        self.probe_cfg_path = os.path.join(self.project_root, 'probe_config.txt')
        self.bitfile_path = os.path.join(self.project_root, f'{self.project_name}.runs', 'impl_1',
                                         f'{self.parent.top_module}.bit')
        self.ltxfile_path = os.path.join(self.project_root, f'{self.project_name}.runs', 'impl_1',
                                         f'{self.parent.top_module}.ltx')
        self.vio_name = 'vio_0'
        self.vio_inst_name = self.vio_name + '_i'
        self.ila_inst_name = 'u_ila_0'
        self.ila_reset = 'reset_probe'
        self.vio_reset = 'vio_i/rst'

    @property
    def project_root(self):
        return os.path.join(self.parent.build_root, self.project_name)

    @property
    def ip_dir(self):
        return os.path.join(self.project_root, f'{self.project_name}.srcs', 'sources_1', 'ip')

class IcarusConfig():
    def __init__(self, parent: EmuConfig, iverilog, vvp):
        # save reference to parent config
        self.parent = parent

        # set path to iverilog and vvp binaries
        hints = [lambda: os.path.join(env['ICARUS_INSTALL_PATH'], 'bin')]
        self.iverilog = iverilog if iverilog is not None else find_tool(name='iverilog', hints=hints)
        self.vvp = vvp if vvp is not None else find_tool(name='vvp', hints=hints)

        # name of output file
        self.output_file_name = 'a.out'

    @property
    def output_file_path(self):
        return os.path.join(self.parent.build_root, self.output_file_name)

class GtkWaveConfig():
    def __init__(self, parent: EmuConfig, gtkwave):
        # save reference to parent config

        # find binary
        hints = [lambda: os.path.join(env['GTKWAVE_INSTALL_PATH'], 'bin')]
        self.gtkwave = gtkwave if gtkwave is not None else find_tool(name='gtkwave', hints=hints)

def find_tool(name, hints: list):
    # first check the system path for the tool
    tool_path = shutil.which(name)

    # if the tool isn't found in the system path, then try out the hints in order
    if tool_path is None:
        for hint in hints:
            try:
                tool_path = shutil.which(name, path=hint())
            except:
                continue

            if tool_path is not None:
                break

    # finally get the fully path to the tool if it was found and if not raise an exception
    if tool_path is not None:
        return get_full_path(tool_path)
    else:
        raise KeyError(f'Tool:{name} could not be found')