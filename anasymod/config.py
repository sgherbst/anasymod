import os.path
import multiprocessing
import shutil

from anasymod.files import get_full_path, get_from_module
from anasymod.util import back2fwd
from anasymod.filesets import Filesets
from os import environ as env

class EmuConfig:
    def __init__(self, root, vivado=None, iverilog=None, vvp=None, gtkwave=None, xrun=None, simvision=None, build_root=None):

        # define and create build root
        self.build_root = build_root if build_root is not None else get_full_path('build')
        if not os.path.exists(self.build_root):
            os.mkdir(self.build_root)

        # other options
        # self.top_module = top_module if top_module is not None else 'top'
        self.emu_clk_freq = 25e6
        self.dbg_hub_clk_freq = 100e6
        self.preprocess_only = False

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

    def setup_ila(self):
        self.ila_depth = 1024

    @property
    def dec_bits(self):
        return 8

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
