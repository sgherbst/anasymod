import os.path
import multiprocessing
import shutil

from sys import platform
from glob import glob
from anasymod.files import get_full_path, get_from_module, mkdir_p
from anasymod.util import back2fwd, vivado_search_key
from anasymod.filesets import Filesets
from os import environ as env
from anasymod.enums import BoardNames, FPGASimCtrl
from anasymod.plugins import *
from anasymod.fpga_boards.boards import *
from anasymod.base_config import BaseConfig
from anasymod.sim_ctrl.uart_control import UARTControl, Control

class EmuConfig:
    def __init__(self, root, cfg_file, build_root=None):

        self.root = root

        # define and create build root
        self.build_root = build_root if build_root is not None else os.path.join(root, 'build')
        if not os.path.exists(self.build_root):
            mkdir_p(self.build_root)

        self.cfg_file = cfg_file

        # Initialize config  dict
        self.cfg = Config(cfg_file=self.cfg_file)

        # Update config options by reading from config file
        self.cfg.update_config()

        # Instantiate Simulation Control Interface
        self.ctrl = self._setup_ctrl_ifc()

        # FPGA board configuration
        self.board = self._fetch_board()

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

    def _fetch_board(self):
        """
        Fetch FPGA board info.
        """

        if self.cfg.board_name == BoardNames.PYNQ_Z1:
            return PYNQ_Z1()
        elif self.cfg.board_name == BoardNames.VC707:
            return VC707()
        elif self.cfg.board_name == BoardNames.ULTRA96:
            return ULTRA96()
        elif self.cfg.board_name == BoardNames.TE0720:
            return TE0720()
        else:
            raise Exception(f'The requested board {self.cfg.board_name} could not be found.')

    def _setup_ctrl_ifc(self):
        """
        Setup the control interface according to what was provided in the project configuration. default is VIVADO_VIO
        mode, which does not possess a direct control interface via anasymod.

        :rtype: Control
        """

        if self.board.sim_ctrl is FPGASimCtrl.VIVADO_VIO:
            print("No direct control interface from anasymod selected, Vivado VIO interface enabled.")
        elif self.board.sim_ctrl is FPGASimCtrl.VIVADO_VIO:
            print("Direct anasymod FPGA simulation control via UART enabled.")
            self.ctrl = UARTControl(prj_cfg=self)
        else:
            raise Exception("ERROR: No FPGA simulation control was selected, shutting down.")

class VivadoConfig():
    def __init__(self, parent: EmuConfig, vivado=None):
        # save reference to parent config
        self.parent = parent

        # set project name
        self.project_name = 'project'

        # set path to vivado binary
        self.hints = [lambda: os.path.join(env['VIVADO_INSTALL_PATH'], 'bin'),
                      lambda: os.path.join(env['INICIO_INSTALL'], 'tools', '64', 'Xilinx-18.2.0.1', 'Vivado', '2018.2', 'bin')]
        if platform == 'linux' or platform == 'linux2':
            sorted_dirs = sorted(glob('/tools/Xilinx/Vivado/*.*'), key=vivado_search_key)
            self.hints.extend(lambda: os.path.join(dir_, 'bin') for dir_ in sorted_dirs)

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
        self.hints = [lambda: os.path.join(env['ICARUS_INSTALL_PATH'], 'bin'),
                      lambda: os.path.join(env['INICIO_INSTALL'], 'tools', '64', 'iverilog-10.1.1.0', 'bin')]
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
        self.hints = [lambda: os.path.join(env['GTKWAVE_INSTALL_PATH'], 'bin'),
                      lambda: os.path.join(env['INICIO_INSTALL'], 'tools', 'common', 'gtkwave-3.3.65.0', 'bin')]
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

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """
    def __init__(self, cfg_file):
        super().__init__(cfg_file=cfg_file, section=ConfigSections.PROJECT)
        self.dec_bits = 24
        self.board_name = BoardNames.PYNQ_Z1
        #self.board_name = BoardNames.VC707
        self.emu_clk_freq = 25e6
        self.preprocess_only = False
        self.jtag_freq = 15e6
        self.fpga_sim_crtl = FPGASimCtrl.VIVADO_VIO
        self.plugins = []
        self.plugins.append('msdsl')
        #self.plugins.append('netexplorer')
        #self.plugins.append('stargazer')

def find_tool(name, hints=None, sys_path_hint=True):
    # set defaults
    if hints is None:
        hints = []



    # add system path as the last "hint" if desired (default behavior)
    if sys_path_hint:
        hints.append(lambda: None)

    # first check the system path for the tool
    tool_path = shutil.which(name)

    # if the tool isn't found in the system path, then try out the hints in order
    if tool_path is None:
        for hint in hints:
            try:
                if callable(hint):
                    tool_path = shutil.which(name, path=hint())
                else:
                    tool_path = shutil.which(name, path=hint)
            except:
                continue

            if tool_path is not None:
                break

    if tool_path is not None:
        return get_full_path(tool_path)
    else:
        raise KeyError(f'Tool:{name} could not be found')


