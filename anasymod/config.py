import os.path
import pathlib
import re
import multiprocessing
import shutil

from sys import platform
from glob import glob
from anasymod.files import get_full_path, mkdir_p
from anasymod.util import vivado_search_key
from os import environ as env
from anasymod.enums import BoardNames
from anasymod.plugins import *
from anasymod.fpga_boards.boards import *
from anasymod.base_config import BaseConfig

class EmuConfig:
    def __init__(self, root, cfg_file, active_target, build_root=None):

        self._valid_ila_values = [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

        self.root = root

        # define and create build root
        self.build_root_base = build_root if build_root is not None else os.path.join(root, 'build')

        # define build root for functional models
        self.build_root_functional_models = os.path.join(self.build_root_base, 'models')

        self.build_root = os.path.join(self.build_root_base, active_target)
        if not os.path.exists(self.build_root):
            mkdir_p(self.build_root)

        self.cfg_file = cfg_file

        # Initialize config  dict
        self.cfg = Config(cfg_file=self.cfg_file)

        # Update config options by reading from config file
        self.cfg.update_config()

        # Try to initialize Inicio config_dict
        # TODO: add more reasonable defaults
        try:
            from inicio import config_dict
            self.cfg_dict = config_dict()
        except:
            self.cfg_dict = {
                'TOOLS_xilinx': '',
                'INICIO_TOOLS': '',
                'TOOLS_iverilog': '',
                'TOOLS_gtkwave': ''
            }

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
        if self.cfg.ila_depth in self._valid_ila_values:
            return self.cfg.ila_depth
        else:
            raise Exception(f'Provided value for ILA depth is not valid, allows values are:{self.cfg.ila_depth}, '
                            f'given: {self.cfg.ila_depth}')

    def _update_build_root(self, active_target):
        self.build_root = os.path.join(self.build_root_base, active_target)
        if not os.path.exists(self.build_root):
            mkdir_p(self.build_root)

    def _fetch_board(self):
        """
        Fetch FPGA board info.
        """

        if self.cfg.board_name == BoardNames.PYNQ_Z1:
            return PYNQ_Z1()
        elif self.cfg.board_name == BoardNames.ARTY_A7:
            return ARTY_A7()
        elif self.cfg.board_name == BoardNames.VC707:
            return VC707()
        elif self.cfg.board_name == BoardNames.ULTRA96:
            return ULTRA96()
        elif self.cfg.board_name == BoardNames.TE0720:
            return TE0720()
        elif self.cfg.board_name == BoardNames.ZC702:
            return ZC702()
        elif self.cfg.board_name == BoardNames.ARTY_200T_CUSTOM_LIDAR:
            return ARTY_200T_CUSTOM_LIDAR()
        else:
            raise Exception(f'The requested board {self.cfg.board_name} could not be found.')

class VivadoConfig():
    def __init__(self, parent: EmuConfig, vivado=None, version=None,
                 version_year=None, version_number=None):
        # save reference to parent config
        self.parent = parent

        # set project name
        self.project_name = 'prj'
        # intermediate variables for generic Xilinx path
        if platform in {'win32', 'cygwin'}:
            xilinx_version_path = parent.cfg_dict['TOOLS_xilinx']
            xilinx_version = "20" + ".".join(xilinx_version_path.split(".")[0:2]).split("-")[1]
        # set path to vivado binary
        self.hints = [lambda: os.path.join(env['VIVADO_INSTALL_PATH'], 'bin'),
                      lambda: os.path.join(parent.cfg_dict['INICIO_TOOLS'], xilinx_version_path, "Vivado", xilinx_version, "bin" ),]
        # lsf options for tcl mode of Vivado
        self.lsf_opts_ls = ''
        self.lsf_opts = parent.cfg.lsf_opts
        if platform in {'linux', 'linux2'}:
            sorted_dirs = sorted(glob('/tools/Xilinx/Vivado/*.*'), key=vivado_search_key)
            self.hints.extend(lambda: os.path.join(dir_, 'bin') for dir_ in sorted_dirs)
            if 'CAMINO' in os.environ:
                self.lsf_opts = "-eh_ram 70000 -eh_ncpu 8 -eh_ui inicio_batch"
                self.lsf_opts_ls = "-eh_ram 70000 -eh_ncpu 8 -eh_dispatch LS_SHELL"

        self._vivado = vivado

        # version, year, number
        self._version = version
        self._version_year = version_year
        self._version_number = version_number

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
    def version(self):
        if self._version is None:
            self._version = pathlib.Path(self.vivado).parent.parent.name
        return self._version

    @property
    def version_year(self):
        if self._version_year is None:
            self._version_year = re.match(r'(\d+)\.(\d+)', self.version).groups()[0]
            self._version_year = int(self._version_year)
        return self._version_year

    @property
    def version_number(self):
        if self._version_number is None:
            self._version_number = re.match(r'(\d+)\.(\d+)', self.version).groups()[1]
            self._version_number = int(self._version_number)
        return self._version_number

class XceliumConfig():
    def __init__(self, parent: EmuConfig, xrun=None):
        # save reference to parent config
        self.parent = parent
        self.lsf_opts = parent.cfg.lsf_opts
        # set path to xrun binary
        self.hints = [lambda: os.path.join(env['XCELIUM_INSTALL_PATH'], 'bin')]
        self._xrun = xrun

        # name of TCL file
        self.tcl_input = 'input.tcl'



    @property
    def xrun(self):
        if self._xrun is None:
            try:
                self._xrun = find_tool(name='ifxxcelium', hints=self.hints)
                self.lsf_opts = "-eh_ncpu 4"
                #self._xrun += " execute"
            except:
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
                      lambda: os.path.join(parent.cfg_dict['INICIO_TOOLS'], parent.cfg_dict['TOOLS_iverilog'], 'bin')]
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
                      lambda: os.path.join(parent.cfg_dict['INICIO_TOOLS'], parent.cfg_dict['TOOLS_gtkwave'], 'bin')]
        self._gtkwave = gtkwave
        self.gtkw_config = None
        self.lsf_opts = parent.cfg.lsf_opts
        if 'CAMINO' in os.environ:
            self.lsf_opts = "-eh_ram 7000"

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
        self.lsf_opts = parent.cfg.lsf_opts
        if 'CAMINO' in os.environ:
            self.lsf_opts = "-eh_ram 7000"

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
        """ type(int) : number of bits used for decimation threshold value, which controls the ila capture feature """

        self.board_name = BoardNames.PYNQ_Z1
        """ type(str) : name of FPGA board, that shall be used for this project. """

        self.emu_clk_freq = 25e6
        """ type(float) : emulation frequency in Hz, that is used as main independent clk in the design. """

        self.preprocess_only = False
        """ type(bool) : indicate, whether or not only conduct elaboration and compile during simulation run. This will
            show all Macros expanded and currently only works for icarus verilog. """

        self.jtag_freq = 15e6
        """ type(float) : jtag communication frequency in Hz. This impacts the frequency used for programming the 
            bitstream onto the FPGA, a value that is set too high might cause stability issues. """

        self.plugins = ['msdsl']
        """ type(list(str)) : list of plugins that shall be used in the scope of this project. """

        self.dt = 0.1e-6
        """ type(float) : globally used dt value for projects, that strictly use fixed-timestep-based models. """

        self.dt_scale = 1e-15
        """ type(float) : resolution for dt request and response signals (e.g., "1e-15" means 1fs resolution). """

        self.dt_width = 32
        """ type(int) : number of bits used for dt request and response signals """

        self.time_width = 64
        """ type(int) : number of bits used for emulation time signal.  TODO: explore issue with using
            values larger than 39 (related to ILA). """
        
        self.lsf_opts = ''
        """ type(string) : LSF options which can be passed to our tool wrapper commands in the Inicio Flowpackage
            Execution handler options, e.g. '-eh_ncpu 8' can be used"""

        self.ila_depth = 4096
        """ type(int) : number of samples that can be stored in the ILA for each signal that is probed. Valid values are:
            1,024, 2,048, 4,096, 8,192, 16,384, 32,768, 65,536, 131,072. Also when choosing this value keep in mind,
            that this will consume Block Memory. Possible values are further limited by the number of signals to be 
            stored, number of block memory cells available on the FPGA board and also block memory that was consumed 
            already be the design itself. """

        self.cpu_debug_mode = False
        """ type(bool) : Enables probing all signals for either everything below the testbench, or for modules 
            provided in the cpu_debug_hierarchies attribute."""

        self.cpu_debug_hierarchies = None
        """ type(str, list) : Either tuple of depth and absolute path or list of tuples of depth and absolute path to 
            design modules, for which all signals shall be stored in result file. e.g.:
            [(0, top.tb_i.filter_i)]"""

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


