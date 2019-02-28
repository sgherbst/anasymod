import os

from glob import glob

from anasymod.sim.sim import Simulator
from anasymod.util import call
from anasymod.sources import VerilogSource, VerilogHeader, VHDLSource, Sources

class XceliumSimulator(Simulator):
    def simulate(self):
        # build up the simulation command
        cmd = [self.cfg.xcelium_config.xrun, '-sv', '-top', self.target.cfg['top_module'], '-input', self.cfg.xcelium_config.tcl_input_path]

        # Preprocess Define and Source obj
        defines_dict = {}
        for define in self.target._defines:
            defines_dict.update(define.define)

        headers_dict = {}
        sources_dict = []
        for source in self.target._sources:
            if isinstance(source, VerilogSource):
                sources_dict += source.files
            elif isinstance(source, VerilogHeader):
                headers_dict += source.files

        # add defines
        for k, v in defines_dict.items():
            if v is not None:
                cmd.append(f"+define+{k}={v}")
            else:
                cmd.append(f"+define+{k}")


        # add include directories
        for header in headers_dict:
            cmd.extend(['-incdir', header])

        # add source files
        for source in sources_dict:
            cmd.extend(source)

        # write TCL file
        with open(self.cfg.xcelium_config.tcl_input_path, 'w') as f:
            f.write('run\n')
            f.write('exit\n')

        # run xrun
        print(cmd)
        call(cmd, cwd=self.cfg.build_root)
