import os
import platform

from collections import OrderedDict

from anasymod.sim.sim import Simulator
from anasymod.util import call
from anasymod.targets import SimulationTarget
from anasymod.config import EmuConfig

class XceliumSimulator(Simulator):
    def __init__(self, cfg: EmuConfig, target: SimulationTarget):
        super().__init__(cfg=cfg, target=target)

    def simulate(self, licqueue=True, smartorder=True):
        # build up the simulation command
        cmd = []
        cmd += [self.cfg.xcelium_config.xrun]
        cmd += ['-top', self.target.cfg['top_module']]
        cmd += ['-input', self.cfg.xcelium_config.tcl_input_path]

        # order independent compilation for VHDL
        if smartorder:
            cmd += ['-smartorder']

        # wait to get a license
        if licqueue:
            cmd += ['-licqueue']

        # 64-bit or 32-bit mode
        # TODO: is this actually necessary?  the problem is that sometimes xrun is submitted through a bsub command,
        # so the remote machine architecture isn't necessarily the same as that of the local machine that submits
        # the job.
        if '64bit' in platform.architecture():
            cmd += ['-64bit']

        # add defines
        for define in self.target.content['defines']:
            for k, v in define.define.items():
                if v is not None:
                    cmd.append(f"+define+{k}={v}")
                else:
                    cmd.append(f"+define+{k}")

        # add include directories, remove filename from paths and create a list of inc dirs removing duplicates
        inc_dirs = set()
        for sources in self.target.content['verilog_headers']:
            for src in sources.files:
                inc_dirs.add(os.path.dirname(src))

        for inc_dir in inc_dirs:
            cmd.extend(['-incdir', inc_dir])

        # add Verilog source files
        for sources in self.target.content['verilog_sources']:
            for src in sources.files:
                cmd.append(src)

        # add VHDL source files
        # TODO: is it actually necessary to consolidate makelib commands together?  if subsequent makelib commands
        # append rather than replace files, then it should be OK (and simpler) to have a separate makelib for
        # each file in each library.
        libraries = OrderedDict()
        for sources in self.target.content['vhdl_sources']:
            library = sources.library

            if library not in libraries:
                libraries[library] = []

            files = sources.files
            libraries[library] += files

        for library, sources in libraries.items():
            cmd += ['-makelib', library]
            cmd += sources
            cmd += ['-endlib']

        # write TCL file
        with open(self.cfg.xcelium_config.tcl_input_path, 'w') as f:
            f.write('run\n')
            f.write('exit\n')

        # run xrun
        print(cmd)
        call(cmd, cwd=self.cfg.build_root)
