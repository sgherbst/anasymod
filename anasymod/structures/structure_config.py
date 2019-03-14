from anasymod.enums import ConfigSections
from anasymod.base_config import BaseConfig

class StructureConfig():
    """
    In this configuration, all the toplevel information about the generated toplevel is included.
    It will be used for generation of the target specific top-level, as well as attached wrappers.

    There is also a specific interface to flow plugins that allows modification due to some needs
    from the plugin side, e.g. additional clks, resets, ios to the host application or resources on the FPGA board.
    """
    def __init__(self, cfg_file):
        self.cfg = Config(cfg_file=cfg_file)

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """

    def __init__(self, cfg_file):
        super().__init__(cfg_file=cfg_file, section=ConfigSections.STRUCTURE)
