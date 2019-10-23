from anasymod.sim_ctrl.control import Control
from anasymod.structures.module_viosimctrl import ModuleVIOSimCtrl
from anasymod.sources import VerilogSource
from anasymod.structures.structure_config import StructureConfig

class VIOControl(Control):
    def __init__(self, prj_cfg):
        super().__init__(prj_cfg=prj_cfg)

        # Initialize internal variables

    def _build_base_ctrl_structure(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for base control infrastructure. This will generate the sim ctrl wrapper for VIO control.
        """

        # Generate simulation control wrapper and add to target sources
        with (open(self._simctrlwrap_path, 'w')) as ctrl_file:
           ctrl_file.write(ModuleVIOSimCtrl(scfg=str_cfg).render())

        content.verilog_sources += [VerilogSource(files=self._simctrlwrap_path)]

    def _build_FPGA_ctrl_structure(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for FPGA specific control infrastructure, depending on the interface selected for communication.
        For VIO control, no additional RTL sources need to be generated.

        """
        pass

def main():
    ctrl = VIOControl(prj_cfg=EmuConfig(root='test', cfg_file=''))
    ctrl._build_base_ctrl_structure(str_cfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file='')), content='')

if __name__ == "__main__":
    main()