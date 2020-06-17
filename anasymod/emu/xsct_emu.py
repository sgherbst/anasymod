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

    @property
    def impl_dir(self):
        return (
            Path(self.target.project_root) /
            f'{self.target.prj_cfg.vivado_config.project_name}.runs' /
            'impl_1'
        )

    @property
    def bit_path(self):
        return self.impl_dir / f'{self.target.cfg.top_module}.bit'

    @property
    def tcl_path(self):
        return self.impl_dir / 'ps7_init.tcl'

    @property
    def hw_path(self):
        if self.version_year < 2020:
            return self.impl_dir / f'{self.target.cfg.top_module}.sysdef'
        else:
            return self.impl_dir / f'{self.target.cfg.top_module}.xsa'

    def build(self, create=True, copy_files=True, build=True):
        # determine SDK path
        sdk_path = (Path(self.target.project_root) /
                    f'{self.target.prj_cfg.vivado_config.project_name}.sdk')

        # clear the SDK directory
        if create:
            shutil.rmtree(sdk_path, ignore_errors=True)
            sdk_path.mkdir(exist_ok=True, parents=True)

        # copy over the firmware sources
        if copy_files:
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
                hw_path=self.hw_path,
                version_year=self.version_year,
                version_number=self.version_number,
                create=create,
                build=build
            ).text
        )

        # run the build script
        self.run('sdk.tcl')

    def program(self, program_fpga=True, reset_system=True):
        # determine SDK path
        sdk_path = (Path(self.target.project_root) /
                    f'{self.target.prj_cfg.vivado_config.project_name}.sdk')

        # generate the build script
        self.write(
            TemplXSCTProgram(
                sdk_path=sdk_path,
                bit_path=self.bit_path,
                hw_path=self.hw_path,
                tcl_path=self.tcl_path,
                program_fpga=program_fpga,
                reset_system=reset_system
            ).text
        )

        # run the programming script
        self.run('program.tcl')
