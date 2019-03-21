import os

from anasymod.defines import Define
from anasymod.util import back2fwd
from anasymod.config import EmuConfig
from anasymod.sources import Sources, VerilogSource, VerilogHeader, VHDLSource
from anasymod.util import read_config
from anasymod.probe import Probe

class Target():
    """
    This class inherits all source and define objects necessary in order to run actions for a specific target.

    Attributes:
        _name               Target name
        content    Dict of Lists of source and define objects associated with target
    """
    def __init__(self, prj_cfg: EmuConfig, name):
        self.prj_cfg = prj_cfg
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
        self.cfg = {}
        self.cfg['tstop'] = 1e-05
        self.cfg['top_module'] = 'top'
        self.cfg['custom_top'] = False
        self.cfg['vcd_name'] = f"{self.cfg['top_module']}_{self._name}.vcd"
        self.cfg['vcd_path'] = os.path.join(self.prj_cfg.build_root, r"vcd", self.cfg['vcd_name'])

    def set_tstop(self):
        """
        Add define statement to specify tstop
        """
        self.content['defines'].append(Define(name='TSTOP_MSDSL', value=self.cfg['tstop']))

    def assign_fileset(self, fileset: dict):
        """
        Add a fileset to the target by adding defines and sources to the according attributes

        :param fileset: fileset that shall be added to target
        :type fileset: dict
        """

        for k in fileset.keys():
            self.content[k] += fileset[k]

    @property
    def project_root(self):
        return os.path.join(self.prj_cfg.build_root, self.prj_cfg.vivado_config.project_name)

class SimulationTarget(Target):
    def __init__(self, prj_cfg: EmuConfig, name=r"sim"):
        super().__init__(prj_cfg=prj_cfg, name=name)

    def setup_vcd(self):
        self.content['defines'].append(Define(name='VCD_FILE_MSDSL', value=back2fwd(self.cfg['vcd_path'])))

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
                            f"{self.cfg['top_module']}.bit")

    @property
    def ltxfile_path(self):
        return os.path.join(self.project_root, f'{self.prj_cfg.vivado_config.project_name}.runs', 'impl_1',
                            f"{self.cfg['top_module']}.ltx")

    @property
    def ip_dir(self):
        return os.path.join(self.project_root, f'{self.prj_cfg.vivado_config.project_name}.srcs', 'sources_1', 'ip')

