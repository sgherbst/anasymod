from abc import ABC, abstractmethod

from anasymod.config import EmuConfig

class Simulator(ABC):
    def __init__(self, cfg: EmuConfig, source_fileset=None, header_fileset=None):
        self.cfg = cfg

        # Set source paths
        if source_fileset is None:
            self.sources = self.cfg.sim_verilog_sources
        else:
            self.sources = source_fileset

        # Set header paths
        if header_fileset is None:
            self.headers = self.cfg.sim_verilog_headers
        else:
            self.headers = header_fileset


    @abstractmethod
    def simulate(self):
        pass