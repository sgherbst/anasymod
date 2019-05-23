from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections
from anasymod.config import EmuConfig

import serial

class Control():
    def __init__(self, prj_cfg: EmuConfig):
        prj_cfg = prj_cfg

        # Initialize target_config
        self.cfg = Config(cfg_file=prj_cfg.cfg_file, prj_cfg=prj_cfg)

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """
    def __init__(self, cfg_file, prj_cfg):
        super().__init__(cfg_file=cfg_file, section=ConfigSections.FPGASIM)
        self.comport = None
        self.baud_rate = 115200
        self.timeout = None
        self.parity = serial.PARITY_NONE
        self.stopbits=1
        self.bytesize=serial.EIGHTBITS