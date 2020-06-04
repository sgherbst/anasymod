from pathlib import Path
import shutil
from anasymod.generators.xsct import XSCTTCLGenerator

from anasymod.templates.xsct_build import TemplXSCTBuild
from anasymod.templates.xsct_program import TemplXSCTProgram
from anasymod.targets import FPGATarget

class XSCTEmulation(XSCTTCLGenerator):
    """
    Generate and execute Vivado TCL scripts to generate a bitstream, run an emulation of FPGA for non-interactive mode,
    or launch an FPGA emulation for interactive mode and pass the handle for interactive control.
    """

    def __init__(self, target: FPGATarget):
        super().__init__(target=target)

    def build(self):
        # determine SDK path
        sdk_path = (Path(self.target.project_root) /
                    f'{self.target.prj_cfg.vivado_config.project_name}.sdk')
        hdf_path = sdk_path / f'{self.target.cfg.top_module}.hdf'

        # clear the SDK directory
        shutil.rmtree(sdk_path, ignore_errors=True)
        sdk_path.mkdir(exist_ok=True, parents=True)

        # export the hardware
        sysdef_path = (Path(self.target.project_root) /
                       f'{self.target.prj_cfg.vivado_config.project_name}.runs' /
                       'impl_1' /
                       f'{self.target.cfg.top_module}.sysdef')
        shutil.copy(str(sysdef_path), str(hdf_path))

        # copy over the firmware sources
        src_path = sdk_path / 'sw' / 'src'
        src_path.mkdir(exist_ok=True, parents=True)
        for src in self.target.content.firmware_files:
            if src.files is not None:
                for file_ in src.files:
                    shutil.copy(str(file_), str(src_path / Path(file_).name))

        # generate the build script
        self.write(
            TemplXSCTBuild(
                sdk_path=sdk_path,
                top_name=f'{self.target.cfg.top_module}'
            ).text
        )

        # run the build script
        self.run('sdk.tcl')

    def program(self):
        # determine SDK path
        sdk_path = (Path(self.target.project_root) /
                    f'{self.target.prj_cfg.vivado_config.project_name}.sdk')

        # generate the build script
        self.write(
            TemplXSCTProgram(
                sdk_path=sdk_path,
                top_name=f'{self.target.cfg.top_module}'
            ).text
        )

        # run the programming script
        self.run('program.tcl')
