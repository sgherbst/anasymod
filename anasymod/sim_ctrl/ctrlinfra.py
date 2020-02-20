from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections
from anasymod.sim_ctrl.datatypes import DigitalCtrlInput, DigitalCtrlOutput, AnalogCtrlInput, AnalogCtrlOutput
from anasymod.structures.structure_config import StructureConfig

import serial, os

class ControlInfrastructure():
    def __init__(self, prj_cfg):

        self._simctrlwrap_path = os.path.join(prj_cfg.build_root, 'gen_ctrlwrap.sv')

    def gen_ctrlwrapper(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for base control infrastructure, depending on the interface selected for communication.
        """
        raise NotImplementedError("This function cannot be called from the base control class itself and is overloaded "
                                  "in the inheriting classes.")

    def gen_ctrl_infrastructure(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for FPGA specific control infrastructure, depending on the interface selected for communication.
        """
        raise NotImplementedError("This function cannot be called from the base control class itself and is overloaded "
                                  "in the inheriting classes.")

    def add_ip_cores(self, scfg, ip_dir):
        """
        Configures and adds IP cores that are necessary for selected IP cores.
        """
        raise NotImplementedError("This function cannot be called from the base control class itself and is overloaded "
                                  "in the inheriting classes.")