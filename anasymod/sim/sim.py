from abc import ABC, abstractmethod
from anasymod.targets import SimulationTarget
from anasymod.config import EmuConfig

class Simulator(ABC):
    def __init__(self, cfg: EmuConfig, target: SimulationTarget):
        self.cfg = cfg
        self.target = target

        # Set source paths
        # if source_fileset is None:
        #     self.sources = self.target._sources.sim_verilog_sources
        # else:
        #     self.sources = source_fileset
        #
        # # Set header paths
        # if header_fileset is None:
        #     self.headers = self.cfg.sim_verilog_headers
        # else:
        #     self.headers = header_fileset


    @abstractmethod
    def simulate(self):
        pass