import os

from anasymod.sources import Sources, VerilogHeader, VerilogSource, VHDLSource
from anasymod.defines import Define
from anasymod.enums import ConfigSections
from anasymod.base_config import BaseConfig

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

        # List of includes that need to be added to source files generated via ANASYMOD
        self.cfg = Config(cfg_file=self._cfg_file)

        self.include_statements = []

    def _dump_defines(self):
        return self._defines

    def _dump_verilog_sources(self):
        return self._verilog_sources

    def _dump_verilog_headers(self):
        return self._verilog_headers

    def _dump_vhdl_sources(self):
        return self._vhdl_sources

    def _setup_sources(self):
        """
        Add Source objects that are specific to MSDSL
        """
        raise NotImplementedError()

    def _setup_defines(self):
        """
        Add Define objects that are specific to MSDSL
        """
        raise NotImplementedError()

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

    #def _update_config(self, cfg, config_section):
    #    return self.cfg.update_config(cfg=cfg, config_section=config_section)

    #def _read_config(self, cfg_file, section, subsection=None):
    #    return read_config(cfg_file=cfg_file, section=section, subsection=subsection)

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """

    def __init__(self, cfg_file):
        super().__init__(cfg_file=cfg_file, section=ConfigSections.PLUGIN)