import pathlib
import re
import shutil
from pathlib import Path

from anasymod.util import call
from anasymod.generators.codegen import CodeGenerator
from anasymod.config import EmuConfig

class XSCTTCLGenerator(CodeGenerator):
    """
    Class for generating TCL scripts for XSCT
    """

    def __init__(self, pcfg: EmuConfig,xsct=None, version=None,
                 version_year=None, version_number=None,
                 xsct_install_dir=None):
        super().__init__()

        self.pcfg = pcfg
        self._xsct = self.pcfg.xsct_config.xsct

    def run(self, filename=r'run.tcl', err_str=None):
        # write the TCL script
        tcl_script = Path(self.pcfg.build_root).resolve() / filename
        self.write_to_file(tcl_script)

        # assemble the command
        cmd = [str(self.pcfg.xsct_config.xsct), str(tcl_script)]

        # run the script
        call(args=cmd, err_str=err_str)
