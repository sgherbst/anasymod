import os

from anasymod.defines import Define
from anasymod.util import back2fwd
from anasymod.config import EmuConfig
from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections
from anasymod.structures.structure_config import StructureConfig
from anasymod.structures.module_top import ModuleTop
from anasymod.structures.module_vio import ModuleVIOManager
from anasymod.structures.module_clk_manager import ModuleClkManager
from typing import Union
from anasymod.sources import VerilogSource

class Target():
    """
    This class inherits all source and define objects necessary in order to run actions for a specific target.

    Attributes:
        _name               Target name
        content    Dict of Lists of source and define objects associated with target
    """
    def __init__(self, prj_cfg: EmuConfig, name):
        self.prj_cfg = prj_cfg

        # Initialize structure configuration
        self.str_cfg = StructureConfig(prj_cfg=self.prj_cfg)

        self._name = name

        # Initialize Probe Objs; there can be a probe obj for each supported simulator and synthesizer
        self.probes = {}
        """ :type : dict(Probe)"""

        # Initialize content dict  to store design sources and defines
        self.content = {}
        self.content['verilog_sources'] = []
        """:type : List[VerilogSource]"""
        self.content['verilog_headers'] = []
        """:type : List[VerilogHeader]"""
        self.content['vhdl_sources'] = []
        """:type : List[VHDLSource]"""
        self.content['defines'] = []
        """:type : List[Define]"""
        self.content['xci_files'] = []
        """:type : List[XCIFile]"""
        self.content['xdc_files'] = []
        """:type : List[XDCFile]"""

        # Initialize target_config
        self.cfg = Config(cfg_file=self.prj_cfg.cfg_file, prj_cfg=self.prj_cfg, name=self._name)
        self.cfg['custom_top'] = False

    def set_tstop(self):
        """
        Add define statement to specify tstop
        """
        self.content['defines'].append(Define(name='TSTOP_MSDSL', value=self.cfg.tstop))

    def assign_fileset(self, fileset: dict):
        """
        Add a fileset to the target by adding defines and sources to the according attributes

        :param fileset: fileset that shall be added to target
        :type fileset: dict
        """

        for k in fileset.keys():
            self.content[k] += fileset[k]

    def update_structure_config(self):
        self.str_cfg.cfg.update_config(subsection=self._name)

    def gen_structure(self):
        """
        Generate toplevel, IPCore wrappers, debug infrastructure for FPGA and clk manager
        """

        # Generate toplevel
        toplevel_path = os.path.join(self.prj_cfg.build_root, 'gen_top.sv')
        with (open(toplevel_path, 'w')) as top_file:
            top_file.write(ModuleTop(target=self).render())

        # Add toplevel to target sources
        self.content['verilog_sources'] += [VerilogSource(files=toplevel_path)]

        # Generate vio wrapper
        viowrapper_path = os.path.join(self.prj_cfg.build_root, 'gen_vio_wrap.sv')
        with (open(viowrapper_path, 'w')) as top_file:
            top_file.write(ModuleVIOManager(str_cfg=self.str_cfg).render())

        # Add vio wrapper to target sources
        self.content['verilog_sources'] += [VerilogSource(files=viowrapper_path)]

        # Generate clk management wrapper
        clkmanagerwrapper_path = os.path.join(self.prj_cfg.build_root, 'gen_clkmanager_wrap.sv')
        with (open(clkmanagerwrapper_path, 'w')) as top_file:
            top_file.write(ModuleClkManager(target=self).render())

        # Add clk management wrapper to target sources
        self.content['verilog_sources'] += [VerilogSource(files=clkmanagerwrapper_path)]

    @property
    def project_root(self):
        return os.path.join(self.prj_cfg.build_root, self.prj_cfg.vivado_config.project_name)

class SimulationTarget(Target):
    def __init__(self, prj_cfg: EmuConfig, name=r"sim"):
        super().__init__(prj_cfg=prj_cfg, name=name)

    def setup_vcd(self):
        self.content['defines'].append(Define(name='VCD_FILE_MSDSL', value=back2fwd(self.cfg.vcd_path)))

class FPGATarget(Target):
    """

    Attributes:
        _ip_cores        List of ip_core objects associated with target, those will generated during the build process
    """
    def __init__(self, prj_cfg: EmuConfig, name=r"fpga"):
        # call the super constructor
        super().__init__(prj_cfg=prj_cfg, name=name)

        # use a different default TSTOP value, which should provide about 0.1 ps timing resolution and plenty of
        # emulation time for most purposes.
        self.cfg['tstop'] = 10.0

        self._ip_cores = []

        # TODO: move these paths to toolchain specific config, which shall be instantiated in the target class
        self.cfg['csv_name'] = f"{self.cfg['top_module']}_{self._name}.csv"
        self.cfg['csv_path'] = os.path.join(self.prj_cfg.build_root, r"csv", self.cfg['csv_name'])

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
        self.tstop = 1e-05
        self.emu_clk_freq =25e6
        self.top_module = 'top'
        self.vcd_name = f"{self.top_module}_{name}.vcd"
        self.vcd_path = os.path.join(prj_cfg.build_root, r"vcd", self.vcd_name)


