from abc import ABC, abstractmethod
from anasymod.targets import CPUTarget
from anasymod.config import EmuConfig

class Simulator(ABC):
    def __init__(self, target: CPUTarget, flags=None):
        # set defaults
        if flags is None:
            flags = []

        # save settings
        self.cfg = target.prj_cfg
        self.target = target
        self.flags = flags

    @abstractmethod
    def simulate(self):
        pass
