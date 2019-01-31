import os.path

from anasymod.files import which, get_full_path, get_from_module
from anasymod.util import back2fwd

class EmuConfig:
    def __init__(self):
        # source files
        self.sim_only_verilog_sources = []
        self.synth_only_verilog_sources = []
        self.verilog_sources = []

        # header files
        self.sim_only_verilog_headers = []
        self.synth_only_verilog_headers = []
        self.verilog_headers = []

        # definitions
        self.sim_only_verilog_defines = []
        self.synth_only_verilog_defines = []
        self.verilog_defines = []

        # FPGA board configuration
        self.fpga_board_config = FpgaBoardConfig()

        # Vivado configuration
        self.vivado_config = VivadoConfig()

        # Icarus configuration
        self.icarus_config = IcarusConfig()

        # paths
        self.build_dir = get_full_path('build')

        # other options
        self.top_module = 'top'
        self.vcd_rel_path = 'dump.vcd'
        self.emu_clk_freq = 25e6
        self.dbg_hub_clk_freq = 100e6
        self.dt = None
        self.tstop = None
        self.ila_depth = None
        self.probe_signals = []

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
    def vcd_abs_path(self):
        return os.path.join(self.build_dir, self.vcd_rel_path)

    def set_dt(self, value):
        self.dt = value
        self.verilog_defines.append(f'DT_MSDSL={value}')

    def set_tstop(self, value):
        self.tstop = value
        self.sim_only_verilog_defines.append(f'TSTOP_MSDSL={value}')

    def setup_vcd(self):
        self.sim_only_verilog_defines.append(f'VCD_FILE_MSDSL={back2fwd(self.vcd_abs_path)}')

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

class FpgaBoardConfig:
    def __init__(self, clk_pin='H16', clk_io='LVCMOS33', clk_freq=125e6, full_part_name='xc7z020clg400-1',
                 short_part_name='xc7z020'):
        self.clk_pin = clk_pin
        self.clk_io = clk_io
        self.clk_freq = clk_freq
        self.full_part_name = full_part_name
        self.short_part_name = short_part_name

class VivadoConfig:
    def __init__(self, project_name='project', project_directory='project', vivado=None):
        self.project_name = project_name
        self.project_directory = project_directory
        self.vivado = vivado if vivado is not None else which('vivado')

class IcarusConfig:
    def __init__(self, iverilog=None, vvp=None, output='a.out'):
        self.iverilog = iverilog if iverilog is not None else which('iverilog')
        self.vvp = vvp if vvp is not None else which('vvp')
        self.output = output