import os.path
import multiprocessing
import shutil

from anasymod.files import get_full_path, get_from_module, mkdir_p
from anasymod.util import back2fwd, read_config, update_config
from anasymod.filesets import Filesets
from os import environ as env
from anasymod.enums import ConfigSections, BoardNames
from anasymod.plugins import *
from anasymod.fpga_boards.boards import *

class EmuConfig:
    def __init__(self, root, cfg_file, build_root=None):

        # define and create build root
        self.build_root = build_root if build_root is not None else os.path.join(root, 'build')
        if not os.path.exists(self.build_root):
            mkdir_p(self.build_root)

        # Initialize internal variables
        self._cfg_file = cfg_file

        # Initialize config options
        self.preprocess_only = False

        # Initialize config  dict
        self.cfg = {}
        self.cfg['dec_bits'] = 24
        self.cfg['board_name'] = BoardNames.PYNQ_Z1
        self.cfg['emu_clk_freq'] = 25e6
        self.cfg['emu_gated_clocks'] = 0
        self.cfg['dbg_hub_clk_freq'] = 100e6
        self.cfg['conn_dbg_clk'] = 'clk_gen_i/clk_wiz_0_i/clk_out2'
        self.cfg['jtag_freq'] = 15e6
        self.cfg['plugins'] = []
        self.cfg['plugins'].append('msdsl')
        #self.cfg['plugins'].append('netexplorer')
        #self.cfg['plugins'].append('stargazer')

        # Update config options by reading from config file
        self.cfg = update_config(cfg=self.cfg, config_section=read_config(cfg_file=self._cfg_file, section=ConfigSections.PROJECT))

        # FPGA board configuration
        self.fpga_board_config = FPGABoardConfig(board_name=self.cfg['board_name'])

        # Vivado configuration
        self.vivado_config = VivadoConfig(parent=self)

        # GtkWave configuration
        self.gtkwave_config = GtkWaveConfig(parent=self)

        # SimVision configuration
        self.simvision_config = SimVisionConfig(parent=self)

        # Icarus configuration
        self.icarus_config = IcarusConfig(parent=self)

        # Xcelium configuration
        self.xcelium_config = XceliumConfig(parent=self)

    @property
    def ila_depth(self):
        return 4096

class FPGABoardConfig():
    def __init__(self, board_name):
        self.board_name = board_name
        self.board = None

        # Fetch board info
        self.board = self.fetch_board(board_name=board_name)

        self.full_part_name = 'xc7z020clg400-1'
        self.short_part_name = 'xc7z020'

    def fetch_board(self, board_name):
        """
        Fetch boards info
        :param board_name: name of board to be fetched
        :return:
        """

        if board_name == BoardNames.PYNQ_Z1:
            return PYNQ_Z1()
        elif board_name == BoardNames.VC707:
            return VC707()
        else:
            raise Exception(f'The requested board {board_name} could not be found.')

class VivadoConfig():
    def __init__(self, parent: EmuConfig, vivado=None):
        # save reference to parent config
        self.parent = parent

        # set project name
        self.project_name = 'project'

        # set path to vivado binary
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
    def __init__(self, parent: EmuConfig, xrun=None):
        # save reference to parent config
        self.parent = parent

        # set path to xrun binary
        self.hints = [lambda: os.path.join(env['XCELIUM_INSTALL_PATH'], 'bin')]
        self._xrun = xrun

        # name of TCL file
        self.tcl_input = 'input.tcl'

    @property
    def xrun(self):
        if self._xrun is None:
            self._xrun = find_tool(name='xrun', hints=self.hints)
        return self._xrun

    @property
    def tcl_input_path(self):
        return os.path.join(self.parent.build_root, self.tcl_input)

class IcarusConfig():
    def __init__(self, parent: EmuConfig, iverilog=None, vvp=None):
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
    def __init__(self, parent: EmuConfig, gtkwave=None):
        # save reference to parent config
        self.parent = parent

        # find gtkwave binary
        self.hints = [lambda: os.path.join(env['GTKWAVE_INSTALL_PATH'], 'bin')]
        self._gtkwave = gtkwave
        self.gtkw_config = None

    @property
    def gtkwave(self):
        if self._gtkwave is None:
            self._gtkwave = find_tool(name='gtkwave', hints=self.hints)
        return self._gtkwave

class SimVisionConfig():
    def __init__(self, parent: EmuConfig, simvision=None):
        # save reference to parent config
        self.parent = parent

        # find simvision binary
        self.hints = [lambda: os.path.join(env['SIMVISION_INSTALL_PATH'], 'bin')]
        self._simvision = simvision
        self.svcf_config = None

    @property
    def simvision(self):
        if self._simvision is None:
            self._simvision = find_tool(name='simvision', hints=self.hints)
        return self._simvision

def find_tool(name, hints=None, sys_path_hint=True):
    # set defaults
    if hints is None:
        hints = []

    # add system path as the last "hint" if desired (default behavior)
    if sys_path_hint:
        hints.append(lambda: None)

    # check the hints in order
    for hint in hints:
        try:
            tool_path = shutil.which(name, path=hint())
        except:
            continue

        if tool_path is not None:
            return get_full_path(tool_path)
    else:
        raise KeyError(f'Tool:{name} could not be found')


