import os

from anasymod.enums import ConfigSections
from anasymod.sources import Sources, VerilogHeader, VerilogSource, VHDLSource
from anasymod.defines import Define
from anasymod.files import mkdir_p, rm_rf, get_from_module, which
from argparse import ArgumentParser
from anasymod.util import call, read_config, update_config

class Plugin():
    def __init__(self, cfg_file, prj_root, build_root, name):
        self._cfg_file = cfg_file
        self._prj_root = prj_root
        self._build_root = build_root
        self._srccfg_path = os.path.join(self._prj_root, r"source.config")
        self._name = name
        self._defines = []
        self._verilog_sources = []
        """:type : List[VerilogSource]"""

        self._verilog_headers = []
        """:type : List[VerilogHeader]"""

        self._vhdl_sources = []
        """:type : List[VHDLSource]"""

        self.cfg = {}

    def dump_defines(self):
        return self._defines

    def dump_verilog_sources(self):
        return self._verilog_sources

    def dump_verilog_headers(self):
        return self._verilog_headers

    def dump_vhdl_sources(self):
        return self._vhdl_sources

    def add_source(self, source: Sources):
        if isinstance(source, VerilogSource):
            self._verilog_sources.append(source)
        if isinstance(source, VerilogHeader):
            self._verilog_headers.append(source)
        if isinstance(source, VHDLSource):
            self._vhdl_sources.append(source)

    def add_define(self, define: Define):
        self._defines.append(define)

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        pass

class MSDSL_Plugin(Plugin):
    def __init__(self, cfg_file, prj_root, build_root):
        super().__init__(cfg_file=cfg_file, prj_root=prj_root, build_root=build_root, name='msdsl')

        # Parse command line arguments specific to MSDSL
        self.args = None
        self._parse_args()

        # Initialize msdsl config
        self.cfg['dt'] = 0.1e-6
        self.cfg['model_dir'] = os.path.join(self._build_root, 'models')

        # Update msdsl config with msdsl section in config file
        self.cfg = update_config(cfg=self.cfg, config_section=read_config(cfg_file=self._cfg_file, section=ConfigSections.PLUGIN, subsection=self._name))

        # Add defines according to command line arguments
        if self.args.float:
            self.add_define(Define(name='FLOAT_REAL', fileset='sim'))
        if self.args.range_assertions:
            self.add_define(Define(name='RANGE_ASSERTIONS', fileset='sim'))
        if self.args.add_saturation:
            self.add_define(Define(name='ADD_SATURATION'))

        ###############################################################
        # Execute actions according to command line arguments
        ###############################################################

        # make models
        if self.args.models:
            self.models()

        # Setup Defines; after this step, defines shall not be added anymore in MSDSL
        self._setup_defines()
        self._setup_sources()

##### Functions exposed for user to exercise on Analysis Object

    def models(self):
        """
        Call gen.py to generate analog models.
        """
        # make model directory, removing the old one if necessary
        rm_rf(self.cfg['model_dir'])
        mkdir_p(self.cfg['model_dir'])

        # run generator script
        gen_script = os.path.join(self._prj_root, 'gen.py')
        call([which('python'), gen_script, '-o', self.cfg['model_dir'], '--dt', str(self.cfg['dt'])])

##### Utility Functions

    def _setup_defines(self):
        """
        Add Define objects that are specific to MSDSL
        """
        self._set_dt()
        self.add_define(Define(name='SIMULATION_MODE_MSDSL', fileset='sim'))
        self.add_define(Define(name='DEC_BITS_MSDSL', value=24))
        self.add_define(Define(name='OFF_BITS_MSDSL', value=32))

    def _set_dt(self):
        self.add_define(Define(name='DT_MSDSL', value=self.cfg['dt']))

    def _setup_sources(self):
        """
        Add Source objects that are specific to MSDSL
        """

        # Add MSDSL and SVREAL sources
        self.add_source(source=VerilogSource(files=get_from_module('msdsl', 'src', '*.sv'), config_path=self._srccfg_path))
        self.add_source(source=VerilogHeader(files=get_from_module('msdsl', 'include', '*.sv'), config_path=self._srccfg_path))

        self.add_source(source=VerilogSource(files=get_from_module('svreal', 'src', '*.sv'), config_path=self._srccfg_path))
        self.add_source(source=VerilogHeader(files=get_from_module('svreal', 'include', '*.sv'), config_path=self._srccfg_path))

        # Add model sources
        self.add_source(source=VerilogSource(files=os.path.join(self.cfg['model_dir'], '*.sv'), config_path=self._srccfg_path))

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        parser = ArgumentParser()
        parser.add_argument('--range_assertions', action='store_true')
        parser.add_argument('--float', action='store_true')
        parser.add_argument('--add_saturation', action='store_true')
        parser.add_argument('--models', action='store_true')

        self.args, _ = parser.parse_known_args()


class NETEXPLORER_Plugin(Plugin):
    def __init__(self, cfg_file, prj_root, build_root):
        super().__init__(cfg_file=cfg_file, prj_root=prj_root, build_root=build_root, name='netexplorer')

        # Parse command line arguments specific to MSDSL
        self.args = None
        self._parse_args()

        # Initialize netexplorer config

        # Update netexplorer config with netexplorer section in config file
        self.cfg = update_config(cfg=self.cfg, config_section=read_config(cfg_file=self._cfg_file, section=ConfigSections.PLUGIN, subsection=self._name))

        # Add defines according to command line arguments

        ###############################################################
        # Execute actions according to command line arguments
        ###############################################################

        # explore
        if self.args.explore:
            self.explore()

        # Setup Defines; after this step, defines shall not be added anymore in MSDSL

##### Functions exposed for user to exercise on Analysis Object

    def explore(self):
        """
        Convert SV or Verilog netlist input replacing IFX specific types such as ANALOG_T and CURRENT_T to svreal
        compliant data types als taking into account additional functionalities that need to be expressed by additional
        svreal operations.
        """
        pass

##### Utility Functions

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        parser = ArgumentParser()
        parser.add_argument('--explore', action='store_true')

        self.args, _ = parser.parse_known_args()

class STARGAZER_Plugin(Plugin):
    def __init__(self, cfg_file, prj_root, build_root):
        super().__init__(cfg_file=cfg_file, prj_root=prj_root, build_root=build_root, name='stargazer')

        # Parse command line arguments specific to MSDSL
        self.args = None
        self._parse_args()

        # Initialize stargazer config

        # Update stargazer config with stargazer section in config file
        self.cfg = update_config(cfg=self.cfg, config_section=read_config(cfg_file=self._cfg_file, section=ConfigSections.PLUGIN, subsection=self._name))

        # Add defines according to command line arguments

        ###############################################################
        # Execute actions according to command line arguments
        ###############################################################

        # gaze
        if self.args.gaze:
            self.gaze()

        # Setup Defines; after this step, defines shall not be added anymore in MSDSL

##### Functions exposed for user to exercise on Analysis Object

    def gaze(self):
        """
        Convert primitives in starlib into a synthesizable form.
        """
        pass

##### Utility Functions

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        parser = ArgumentParser()
        parser.add_argument('--gaze', action='store_true')

        self.args, _ = parser.parse_known_args()