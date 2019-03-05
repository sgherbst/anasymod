from abc import ABC, abstractmethod
from anasymod.targets import SimulationTarget
from anasymod.config import EmuConfig

class Simulator(ABC):
    def __init__(self, cfg: EmuConfig, target: SimulationTarget):
        self.cfg = cfg
        self.target = target

    @abstractmethod
    def simulate(self):
        pass