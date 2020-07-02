import pathlib
import re
import shutil
from pathlib import Path

from anasymod.util import call
from anasymod.generators.codegen import CodeGenerator
from anasymod.targets import FPGATarget

class XSCTTCLGenerator(CodeGenerator):
    """
    Class for generating TCL scripts for XSCT
    """

    def __init__(self, target: FPGATarget, xsct=None, version=None,
                 version_year=None, version_number=None):
        super().__init__()

        self._xsct = xsct
        self._version = version
        self._version_year = version_year
        self._version_number = version_number
        self.target = target

    def run(self, filename=r'run.tcl', err_str=None):
        # write the TCL script
        tcl_script = Path(self.target.prj_cfg.build_root).resolve() / filename
        self.write_to_file(tcl_script)

        # assemble the command
        cmd = [str(self.xsct), str(tcl_script)]

        # run the script
        call(args=cmd, err_str=err_str)

    @property
    def xsct(self):
        if self._xsct is None:
            self._xsct = shutil.which('xsct')
        return self._xsct

    @property
    def version(self):
        if self._version is None:
            self._version = pathlib.Path(self.xsct).parent.parent.name
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