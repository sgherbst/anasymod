import os

from anasymod.enums import ConfigSections
from anasymod.sources import Sources, VerilogHeader, VerilogSource, VHDLSource
from anasymod.defines import Define
from anasymod.files import mkdir_p, rm_rf, get_from_module, which
from argparse import ArgumentParser
from anasymod.util import call

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

    def update_config(self, config_section: dict=None):
        if config_section is not None:
            for k, v in config_section.items():
                if k in self.cfg:
                    self.cfg[k] = v
                else:
                    print(f"Warning: During target config update; provided config key: {k} in target: {self._name} does not exist")

    def _read_config(self, cfg_file, section, subsection=None):
        """
        Return specified entries from config file, datatype is a dict. This dict will later be used to update flow configs.

        :param section: section to use from config file
        :param subsection: subsection to use from config file
        """
        if cfg_file is not None:
            if section in ConfigSections.__dict__.keys():
                if subsection is not None:
                    return cfg_file[section].get(subsection)
                else:
                    return cfg_file.get(section)
            else:
                raise KeyError(f"provided section key:{section} is not supported")

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
        self.update_config(self._read_config(cfg_file=self._cfg_file, section=ConfigSections.PLUGIN, subsection=self._name))

        # Add defines according to command line arguments
        if self.args.float:
            self.add_define(Define(name='FLOAT_REAL', fileset='sim'))
        if self.args.range_assertions:
            self.add_define(Define(name='RANGE_ASSERTIONS', fileset='sim'))
        if self.args.add_saturation:
            self.add_define(Define(name='ADD_SATURATION'))

        # Setup Defines; after this step, defines shall not be added anymore in MSDSL
        self._setup_defines()
        self._setup_sources()

        ###############################################################
        # Execute actions according to command line arguments
        ###############################################################

        # make models
        if self.args.models:
            # make model directory, removing the old one if necessary
            rm_rf(self.cfg['model_dir'])
            mkdir_p(self.cfg['model_dir'])

            # run generator script
            gen_script = os.path.join(self._prj_root, 'gen.py')
            call([which('python'), gen_script, '-o', self.cfg['model_dir']])


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
