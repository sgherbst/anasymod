import os

from glob import glob

from anasymod.sim.sim import Simulator
from anasymod.util import call

class XceliumSimulator(Simulator):
    def simulate(self):
        # build up the simulation command
        cmd = [self.cfg.xcelium_config.xrun, '-sv', '-top', self.cfg.top_module, '-input', self.cfg.xcelium_config.tcl_input_path]

        # add defines
        for define in self.cfg.sim_verilog_defines:
            cmd.append(f'+define+{define}')

        # add include directories
        inc_dirs = set()
        for header in self.cfg.sim_verilog_headers:
            for file in glob(header):
                inc_dirs.add(os.path.dirname(file))

        for inc_dir in inc_dirs:
            cmd.extend(['-incdir', inc_dir])

        # add source files
        for src in self.cfg.sim_verilog_sources:
            cmd.extend(glob(src))

        # write TCL file
        with open(self.cfg.xcelium_config.tcl_input_path, 'w') as f:
            f.write('run\n')
            f.write('exit\n')

        # run xrun
        print(cmd)
        call(cmd, cwd=self.cfg.build_root)
