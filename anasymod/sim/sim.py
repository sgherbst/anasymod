from abc import ABC, abstractmethod

from anasymod.config import EmuConfig

class Simulator(ABC):
    def __init__(self, cfg: EmuConfig):
        self.cfg = cfg

    @abstractmethod
    def simulate(self):
        pass