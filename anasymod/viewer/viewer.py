from abc import ABC, abstractmethod

from anasymod.config import EmuConfig

class Viewer(ABC):
    def __init__(self, cfg: EmuConfig):
        self.cfg = cfg

    @abstractmethod
    def view(self):
        pass