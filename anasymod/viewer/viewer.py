from abc import ABC, abstractmethod

from anasymod.config import EmuConfig
from anasymod.targets import Target

class Viewer(ABC):
    def __init__(self, cfg: EmuConfig, target: Target):
        self.cfg = cfg
        self.target = target

    @abstractmethod
    def view(self):
        pass