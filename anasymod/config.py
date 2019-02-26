import os.path
import multiprocessing
import shutil

from anasymod.files import get_full_path, get_from_module
from anasymod.util import back2fwd
from anasymod.filesets import Filesets
from os import environ as env

class EmuConfig:
    def __init__(self, root, vivado=None, iverilog=None, vvp=None, gtkwave=None, xrun=None, simvision=None,
                 top_module=None, build_root=None):
        # Initialize and create attributes for filesets
        default_filesets = [r"sim_only_verilog_sources", r"synth_only_verilog_sources", r"verilog_sources",
         r"sim_only_verilog_headers", r"synth_only_verilog_headers", r"verilog_headers"]

        self.filesets = Filesets(root=root, default_filesets=default_filesets)
        self.filesets.read_filesets()
        self.filesets.create_filesets()

        for fileset in self.filesets.fileset_dict.keys():
            setattr(self, fileset, self.filesets.fileset_dict[fileset])

        # build root
        self.build_root = build_root if build_root is not None else get_full_path('build')

        # definitions
        self.sim_only_verilog_defines = []
        self.synth_only_verilog_defines = []
        self.verilog_defines = []

        # other options
        self.top_module = top_module if top_module is not None else 'top'
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

        # SimVision configuration
        self.simvision_config = SimVisionConfig(parent=self, simvision=simvision)

        # Icarus configuration
        self.icarus_config = IcarusConfig(parent=self, iverilog=iverilog, vvp=vvp)

        # Xcelium configuration
        self.xcelium_config = XceliumConfig(parent=self, xrun=xrun)

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # load msdsl library
        #self.verilog_headers.append(get_from_module('msdsl', 'include', '*.sv'))
        #self.verilog_sources.append(get_from_module('msdsl', 'src', '*.sv'))

        # load svreal library
        #self.verilog_sources.append(get_from_module('svreal', 'src', '*.sv'))
        #self.verilog_headers.append(get_from_module('svreal', 'include', '*.sv'))

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
        self.hints = [lambda: os.path.join(env['VIVADO_INSTALL_PATH'], 'bin')]
        self._vivado = vivado

        # set various project options
        self.num_cores = multiprocessing.cpu_count()
        self.vio_name = 'vio_0'
        self.vio_inst_name = self.vio_name + '_i'
        self.ila_inst_name = 'u_ila_0'
        self.ila_reset = 'reset_probe'
        self.vio_reset = 'vio_i/rst'

    @property
    def vivado(self):
        if self._vivado is None:
            self._vivado = find_tool(name='vivado', hints=self.hints)
        return self._vivado

    @property
    def project_root(self):
        return os.path.join(self.parent.build_root, self.project_name)

    @property
    def probe_cfg_path(self):
        return os.path.join(self.project_root, 'probe_config.txt')

    @property
    def bitfile_path(self):
        return os.path.join(self.project_root, f'{self.project_name}.runs', 'impl_1', f'{self.parent.top_module}.bit')

    @property
    def ltxfile_path(self):
        return os.path.join(self.project_root, f'{self.project_name}.runs', 'impl_1', f'{self.parent.top_module}.ltx')

    @property
    def ip_dir(self):
        return os.path.join(self.project_root, f'{self.project_name}.srcs', 'sources_1', 'ip')

class XceliumConfig():
    def __init__(self, parent: EmuConfig, xrun):
        # save reference to parent config
        self.parent = parent

        # set path to iverilog and vvp binaries
        self._xrun = xrun

        # name of TCL file
        self.tcl_input = 'input.tcl'

    @property
    def xrun(self):
        if self._xrun is None:
            self._xrun = find_tool(name='xrun')
        return self._xrun

    @property
    def tcl_input_path(self):
        return os.path.join(self.parent.build_root, self.tcl_input)

class IcarusConfig():
    def __init__(self, parent: EmuConfig, iverilog, vvp):
        # save reference to parent config
        self.parent = parent

        # set path to iverilog and vvp binaries
        self.hints = [lambda: os.path.join(env['ICARUS_INSTALL_PATH'], 'bin')]
        self._iverilog = iverilog
        self._vvp = vvp

        # name of output file
        self.output_file_name = 'a.out'

    @property
    def iverilog(self):
        if self._iverilog is None:
            self._iverilog = find_tool(name='iverilog', hints=self.hints)
        return self._iverilog

    @property
    def vvp(self):
        if self._vvp is None:
            self._vvp = find_tool(name='vvp', hints=self.hints)
        return self._vvp

    @property
    def output_file_path(self):
        return os.path.join(self.parent.build_root, self.output_file_name)

class GtkWaveConfig():
    def __init__(self, parent: EmuConfig, gtkwave):
        # save reference to parent config
        self.parent = parent

        # find binary
        self.hints = [lambda: os.path.join(env['GTKWAVE_INSTALL_PATH'], 'bin')]
        self._gtkwave = gtkwave
        self.gtkw_config = None

    @property
    def gtkwave(self):
        if self._gtkwave is None:
            self._gtkwave = find_tool(name='gtkwave', hints=self.hints)
        return self._gtkwave

class SimVisionConfig():
    def __init__(self, parent: EmuConfig, simvision):
        # save reference to parent config
        self.parent = parent

        # find binary
        self._simvision = simvision
        self.svcf_config = None

    @property
    def simvision(self):
        if self._simvision is None:
            self._simvision = find_tool(name='simvision')
        return self._simvision

def find_tool(name, hints=None):
    # set defaults
    if hints is None:
        hints = []

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
