from abc import ABC, abstractmethod
from anasymod.targets import SimulationTarget
from anasymod.config import EmuConfig

class Simulator(ABC):
    def __init__(self, target: SimulationTarget):
        self.cfg = target.prj_cfg
        self.target = target

    @abstractmethod
    def simulate(self):
        pass