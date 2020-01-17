import os

from anasymod.defines import Define
from anasymod.util import back2fwd
from anasymod.config import EmuConfig
from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections, FPGASimCtrl
from anasymod.structures.structure_config import StructureConfig
from anasymod.structures.module_top import ModuleTop
from anasymod.structures.module_clk_manager import ModuleClkManager
from typing import Union
from anasymod.sources import VerilogSource
from anasymod.sim_ctrl.uart_ctrlinfra import UARTControlInfrastructure
from anasymod.sim_ctrl.vio_ctrlinfra import VIOControlInfrastructure
from anasymod.structures.module_traceport import ModuleTracePort

class Target():
    """
    This class inherits all source and define objects necessary in order to run actions for a specific target.

    Attributes:
        _name               Target name
        content    Dict of Lists of source and define objects associated with target
    """
    def __init__(self, prj_cfg: EmuConfig, plugins: list, name):
        self.prj_cfg = prj_cfg
        self.plugins = plugins

        # Initialize structure configuration
        self.str_cfg = StructureConfig(prj_cfg=self.prj_cfg)

        # Instantiate Simulation ControlInfrastructure Interface
        self.ctrl = None
        """ :type : ControlInfrastructure"""

        self._name = name

        # Initialize Probe Objs; there can be a probe obj for each supported simulator and synthesizer
        self.probes = {}
        """ :type : dict(Probe)"""

        # Initialize content dict  to store design sources and defines
        self.content = Content()

        # Initialize target_config
        self.cfg = Config(cfg_file=self.prj_cfg.cfg_file, prj_cfg=self.prj_cfg, name=self._name)

    def set_tstop(self):
        """
        Add define statement to specify tstop
        """
        self.content.defines.append(Define(name='TSTOP_MSDSL', value=self.cfg.tstop))

    def assign_fileset(self, fileset: dict):
        """
        Add a fileset to the target by adding defines and sources to the according attributes

        :param fileset: fileset that shall be added to target
        :type fileset: dict
        """

        for k in fileset.keys():
            setattr(self.content, k, getattr(self.content, k) + fileset[k])

    def update_structure_config(self):
        self.str_cfg.cfg.update_config(subsection=self._name)

    def gen_structure(self):
        """
        Generate toplevel, IPCore wrappers, debug infrastructure and clk manager.
        """

        # Generate toplevel and add to target sources
        toplevel_path = os.path.join(self.prj_cfg.build_root, 'gen_top.sv')
        with (open(toplevel_path, 'w')) as top_file:
            top_file.write(ModuleTop(target=self).render())

        self.content.verilog_sources += [VerilogSource(files=toplevel_path)]

        # Build control structure and add all sources to project
        if self.ctrl is not None:
            self.ctrl.gen_ctrlwrapper(str_cfg=self.str_cfg, content=self.content)

        # Generate clk management wrapper and add to target sources
        clkmanagerwrapper_path = os.path.join(self.prj_cfg.build_root, 'gen_clkmanager_wrap.sv')
        with (open(clkmanagerwrapper_path, 'w')) as clkm_file:
            clkm_file.write(ModuleClkManager(scfg=self.str_cfg).render())

        self.content.verilog_sources += [VerilogSource(files=clkmanagerwrapper_path)]

        # Generate traceport wrapper and add to target sources
        trapwrapper_path = os.path.join(self.prj_cfg.build_root, 'gen_traceport_wrap.sv')
        with (open(trapwrapper_path, 'w')) as trap_file:
            trap_file.write(ModuleTracePort(scfg=self.str_cfg).render())

        self.content.verilog_sources += [VerilogSource(files=trapwrapper_path)]

    def setup_ctrl_ifc(self):
        """
        Setup the control interface according to what was provided in the project configuration. default is VIVADO_VIO
        mode, which does not possess a direct control interface via anasymod.

        :rtype: ControlInfrastructure
        """
        #ToDo: This should only be executed for FPGA simulation!

        if self.cfg.fpga_sim_ctrl == FPGASimCtrl.VIVADO_VIO:
            print("No direct control interface from anasymod selected, Vivado VIO interface enabled.")
            self.ctrl = VIOControlInfrastructure(prj_cfg=self.prj_cfg)
        elif self.cfg.fpga_sim_ctrl == FPGASimCtrl.UART_ZYNQ:
            print("Direct anasymod FPGA simulation control via UART enabled.")
            self.ctrl = UARTControlInfrastructure(prj_cfg=self.prj_cfg)
        else:
            raise Exception("ERROR: No FPGA simulation control was selected, shutting down.")

    @property
    def project_root(self):
        return os.path.join(self.prj_cfg.build_root, self.prj_cfg.vivado_config.project_name)

class SimulationTarget(Target):
    def __init__(self, prj_cfg: EmuConfig, plugins: list, name=r"sim"):
        super().__init__(prj_cfg=prj_cfg, plugins=plugins, name=name)

    def setup_vcd(self):
        self.content.defines.append(Define(name='VCD_FILE_MSDSL', value=back2fwd(self.cfg.vcd_path)))

class FPGATarget(Target):
    """

    Attributes:
        _ip_cores        List of ip_core objects associated with target, those will generated during the build process
    """
    def __init__(self, prj_cfg: EmuConfig, plugins: list, name=r"fpga"):
        # call the super constructor
        super().__init__(prj_cfg=prj_cfg, plugins=plugins, name=name)

        # use a different default TSTOP value, which should provide about 0.1 ps timing resolution and plenty of
        # emulation time for most purposes.
        self._ip_cores = []

    def gen_structure(self):
        """
        Generate toplevel, IPCore wrappers, debug/ctrl infrastructure for FPGA and clk manager.
        """
        super().gen_structure()
        self.ctrl.gen_ctrl_infrastructure(str_cfg=self.str_cfg, content=self.content)

    @property
    def probe_cfg_path(self):
        return os.path.join(self.project_root, 'probe_config.txt')

    @property
    def bitfile_path(self):
        return os.path.join(self.project_root, f'{self.prj_cfg.vivado_config.project_name}.runs', 'impl_1',
                            f"{self.cfg.top_module}.bit")

    @property
    def ltxfile_path(self):
        return os.path.join(self.project_root, f'{self.prj_cfg.vivado_config.project_name}.runs', 'impl_1',
                            f"{self.cfg.top_module}.ltx")

    @property
    def ip_dir(self):
        return os.path.join(self.project_root, f'{self.prj_cfg.vivado_config.project_name}.srcs', 'sources_1', 'ip')

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """
    def __init__(self, cfg_file, prj_cfg, name):
        super().__init__(cfg_file=cfg_file, section=ConfigSections.TARGET)
        self.tstop = 10.0
        self.emu_clk_freq =25e6
        self.top_module = 'top'
        self.custom_top = False
        self.vcd_name = f"{self.top_module}_{name}.vcd"
        self.vcd_path = os.path.join(prj_cfg.build_root, r"vcd", self.vcd_name)
        # TODO: move these paths to toolchain specific config, which shall be instantiated in the target class
        self.csv_name = f"{self.top_module}_{name}.csv"
        self.csv_path = os.path.join(prj_cfg.build_root, r"csv", self.csv_name)
        self.fpga_sim_ctrl = FPGASimCtrl.VIVADO_VIO

class Content():
    """
    Container storing all Project specific source files, such as RTL, eSW code, blockdiagrams, IP core configs,
    constraint files, ... .
    """

    def __init__(self):
        self.verilog_sources = []
        """:type : List[VerilogSource]"""
        self.verilog_headers = []
        """:type : List[VerilogHeader]"""
        self.vhdl_sources = []
        """:type : List[VHDLSource]"""
        self.defines = []
        """:type : List[Define]"""
        self.xci_files = []
        """:type : List[XCIFile]"""
        self.xdc_files = []
        """:type : List[XDCFile]"""
        self.mem_files = []
        """:type : List[MEMFile]"""
        self.bd_files = []
        """:type : List[BDFile]"""
