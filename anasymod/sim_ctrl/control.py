from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections
from anasymod.sim_ctrl.ctrlifc_datatypes import DigitalCtrlInput, DigitalCtrlOutput, AnalogCtrlInput, AnalogCtrlOutput
from anasymod.targets import Target

import serial, os

class Control():
    def __init__(self, prj_cfg):
        # Store project's simulation ctrl setting
        self.sim_ctrl = prj_cfg.board.sim_ctrl

        # Initialize target_config
        self.cfg = Config(cfg_file=prj_cfg.cfg_file)

        self._simctrlwrap_path = os.path.join(prj_cfg.build_root, 'gen_ctrlwrap.sv')

    def _build_ctrl_structure(self, target: Target):
        """
        Generate RTL design for control infrastructure, depending on the interface selected for communication.
        """
        raise NotImplementedError("This function cannot be called from the base control class itself and is overloaded "
                                  "in the inheriting classes.")

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """
    def __init__(self, cfg_file):
        super().__init__(cfg_file=cfg_file, section=ConfigSections.FPGASIM)
        self.comport = None
        self.baud_rate = 115200
        self.timeout = None
        self.parity = serial.PARITY_NONE
        self.stopbits=1
        self.bytesize=serial.EIGHTBITS