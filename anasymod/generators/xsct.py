from pathlib import Path

from anasymod.util import call
from anasymod.generators.codegen import CodeGenerator
from anasymod.targets import FPGATarget

class XSCTTCLGenerator(CodeGenerator):
    """
    Class for generating TCL scripts for XSCT
    """

    def __init__(self, target: FPGATarget):
        super().__init__()
        self.target = target

    def run(self, filename=r'run.tcl', err_str=None):
        # write the TCL script
        tcl_script = Path(self.target.prj_cfg.build_root).resolve() / filename
        self.write_to_file(tcl_script)

        # assemble the command
        cmd = ['xsct', str(tcl_script)]

        # run the script
        call(args=cmd, err_str=err_str)
