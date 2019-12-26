from abc import ABC, abstractmethod
from anasymod.targets import CPUTarget
from anasymod.config import EmuConfig

class Simulator(ABC):
    def __init__(self, target: CPUTarget):
        self.cfg = target.prj_cfg
        self.target = target

    @abstractmethod
    def simulate(self):
        pass