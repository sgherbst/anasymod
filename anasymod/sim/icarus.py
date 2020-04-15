import os
import re

from anasymod.sim.sim import Simulator
from anasymod.util import call

class IcarusSimulator(Simulator):
    def compile(self):
        # build up the simulation command
        cmd = [self.cfg.icarus_config.iverilog, '-g2012', '-o', self.cfg.icarus_config.output_file_path, '-s',
               self.target.cfg.top_module]

        # if desired, only preprocess
        if self.cfg.cfg.preprocess_only:
            cmd.append('-E')

        # add defines
        for define in self.target.content.defines:
            for k, v in define.define.items():
                if v is not None:
                    cmd.extend(['-D', f"{k}={v}"])
                else:
                    cmd.extend(['-D', f"{k}"])

        # add include directories, remove filename from paths and create a list of inc dirs removing duplicates
        inc_dirs = set()
        for sources in self.target.content.verilog_headers:
            for src in sources.files:
                inc_dirs.add(os.path.dirname(src))

        for inc_dir in inc_dirs:
            cmd.extend(['-I', inc_dir])

        # add verilog source files
        for sources in self.target.content.verilog_sources:
            for src in sources.files:
                cmd.append(src)

        # add HDL files for functional models
        for sources in self.target.content.functional_models:
            for src in sources.gen_files:
                cmd.append(src)

        # run iverilog
        call(cmd, cwd=self.cfg.build_root)

    def run(self):
        args = [self.cfg.icarus_config.vvp, self.cfg.icarus_config.output_file_path]
        cwd = self.cfg.build_root
        err_str = re.compile('^(ERROR|FATAL):')
        call(args, cwd=cwd, err_str=err_str)

    def simulate(self):
        self.compile()

        if not self.cfg.cfg.preprocess_only:
            self.run()