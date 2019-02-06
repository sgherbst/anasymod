import os.path
import multiprocessing
import shutil

import dotmap

from anasymod.files import which, get_full_path, get_from_module
from anasymod.util import path4vivado
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
        self.csv_name = f"{self.top_module}.csv"
        self.vcd_name = f"{self.top_module}.vcd"

        # FPGA board configuration
        self.fpga_board_config = FPGABoardConfig()

        # Vivado configuration
        self.vivado_config = VivadoConfig(cfg=self, vivado=vivado)

        # GtkWave configuration
        self.gtkwave_config = GtkWaveConfig(cfg=self, gtkwave=gtkwave)

        # Icarus configuration
        self.icarus_config = IcarusConfig(cfg=self, iverilog=iverilog, vvp=vvp)

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
        self.sim_only_verilog_defines.append(f'VCD_FILE_MSDSL={path4vivado(self.vcd_path)}')

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
    def __init__(self, cfg : EmuConfig, vivado):
        self._cfg = cfg
        self.project_name = 'project'

        paths = [os.path.join(env['VIVADO_INSTALL_PATH'], r"bin")]
        self.vivado = vivado if vivado is not None else find_tool(name='vivado', hints=paths)

        self.num_cores = multiprocessing.cpu_count()
        self.probe_cfg_path = os.path.join(self.project_root, r"probe_config.txt")
        self.bitfile_path = os.path.join(self.project_root, f'{self.project_name}.runs', r"impl_1",
                                         f"{self._cfg.top_module}.bit")
        self.ltxfile_path = os.path.join(self.project_root, f'{self.project_name}.runs', r"impl_1",
                                         f"{self._cfg.top_module}.ltx")
        self.vio_name = r"vio_0"
        self.vio_inst_name = self.vio_name + r"_i"
        self.ila_inst_name = r"u_ila_0"
        self.ila_reset = r"reset_probe"
        self.vio_reset = r"vio_i/rst"

    @property
    def project_root(self):
        return os.path.join(self._cfg.build_root, self.project_name)

    @property
    def ip_dir(self):
        return os.path.join(self.project_root, f'{self.project_name}.srcs', 'sources_1', 'ip')

class IcarusConfig():
    def __init__(self, cfg: EmuConfig,  iverilog, vvp):
        paths = [os.path.join(env['ICARUS_INSTALL_PATH'], r"bin")]
        self.iverilog = iverilog if iverilog is not None else find_tool(name='iverilog', hints=paths)
        self.vvp = vvp if vvp is not None else find_tool(name='vvp', hints=paths)
        self.output = r"a.out"

class GtkWaveConfig():
    def __init__(self, cfg: EmuConfig, gtkwave):
        paths = [os.path.join(env['GTKWAVE_INSTALL_PATH'], r"bin")]
        self.gtkwave = gtkwave if gtkwave is not None else find_tool(name='gtkwave', hints=paths)

def find_tool(name, hints: list):
    tool_path = shutil.which(name)
    if tool_path is None:
        for hint in hints:
            try:
                tool_path = shutil.which(name, path=hint)
            except:
                pass
            if tool_path is not None:
                break

    if tool_path is not None:
        return get_full_path(tool_path)
    else:
        raise KeyError("Tool:{0} could not be found".format(name))