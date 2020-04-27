from anasymod.sim_ctrl.ctrlinfra import ControlInfrastructure
from anasymod.structures.module_viosimctrl import ModuleVIOSimCtrl
from anasymod.sources import VerilogSource
from anasymod.structures.structure_config import StructureConfig
from anasymod.templates.vio_wiz import TemplVIO

class VIOControlInfrastructure(ControlInfrastructure):
    def __init__(self, prj_cfg):
        super().__init__(prj_cfg=prj_cfg)

        # Initialize internal variables

    def gen_ctrlwrapper(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for base control infrastructure. This will generate the sim ctrl wrapper for VIO control.
        """

        # Generate simulation control wrapper and add to target sources
        with (open(self._simctrlwrap_path, 'w')) as ctrl_file:
           ctrl_file.write(ModuleVIOSimCtrl(scfg=str_cfg).render())

        content.verilog_sources += [VerilogSource(files=self._simctrlwrap_path, name='simctrlwrap')]

    def gen_ctrl_infrastructure(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for FPGA specific control infrastructure, depending on the interface selected for communication.
        For VIO control, no additional RTL sources need to be generated.

        """
        pass

    def add_ip_cores(self, scfg, ip_dir):
        """
        Configures and adds IP cores that are necessary for selected IP cores. VIO IP core is configured and added.
        :return rendered template for configuring a vio IP core
        """
        return [TemplVIO(scfg=scfg, ip_dir=ip_dir)]


def main():
    ctrl = VIOControlInfrastructure(prj_cfg=EmuConfig(root='test', cfg_file=''))
    ctrl.gen_ctrlwrapper(str_cfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file='')), content='')

if __name__ == "__main__":
    main()