from anasymod.anasymod.structures.module_base import ModuleBase
from anasymod.anasymod.blocks.ext_clk import TemplExtClk
from anasymod.anasymod.structures.module_clk_manager import ModuleClkManager
from anasymod.anasymod.targets import FPGATarget
from anasymod.anasymod.config import EmuConfig

class ModuleTop(ModuleBase):
    """
    This is the generator for top.sv.
    """
    def __init__(self, cfg: EmuConfig, target: FPGATarget):
        ext_clk_name = 'ext_clk'

        # Instantiate all modules in toplevel
        self.ext_clk = TemplExtClk(ext_clk_name=ext_clk_name, cfg=cfg)
        self.clk_manager = ModuleClkManager(cfg=cfg, target=target)