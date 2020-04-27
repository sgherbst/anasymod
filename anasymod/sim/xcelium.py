import os
import platform

from collections import OrderedDict

from anasymod.sim.sim import Simulator
from anasymod.util import call
from anasymod.targets import CPUTarget
from anasymod.config import EmuConfig

class XceliumSimulator(Simulator):
    def __init__(self, target: CPUTarget):
        super().__init__( target=target)
        self.unit = None
        self.id = None

    def simulate(self, licqueue=True, smartorder=True, timescale='1ns/1ps'):
        # prepare ifxxcelium makefile by adding inicio target
        self.prepare()

        # build up the simulation command
        cmd = []
        cmd += [self.cfg.xcelium_config.xrun]
        if "ifxxcelium" in self.cfg.xcelium_config.xrun:
            cmd += self.target.prj_cfg.xcelium_config.lsf_opts.split()
            cmd += ['inicio']
            if self.unit:
                cmd += ["-unit", self.unit]
            if self.id:
                cmd += ["-id", self.id]
            cmd += ['--']

        cmd += ['-top', self.target.cfg.top_module]
        cmd += ['-input', self.cfg.xcelium_config.tcl_input_path]

        # order independent compilation for VHDL
        if smartorder:
            cmd += ['-smartorder']

        # wait to get a license
        if licqueue:
            cmd += ['-licqueue']

        # specify the default timescale
        if timescale is not None:
            cmd += ['-timescale', f'{timescale}']

        # 64-bit or 32-bit mode
        # TODO: is this actually necessary?  the problem is that sometimes xrun is submitted through a bsub command,
        # so the remote machine architecture isn't necessarily the same as that of the local machine that submits
        # the job.
        if '64bit' in platform.architecture():
            cmd += ['-64bit']

        # add defines
        for define in self.target.content.defines:
            for k, v in define.define.items():
                if v is not None:
                    cmd.append(f"+define+{k}={v}")
                else:
                    cmd.append(f"+define+{k}")

        # add include directories, remove filename from paths and create a list of inc dirs removing duplicates
        inc_dirs = set()
        for sources in self.target.content.verilog_headers:
            for src in sources.files:
                inc_dirs.add(os.path.dirname(src))

        for inc_dir in inc_dirs:
            cmd.extend(['-incdir', inc_dir])

        # add Verilog source files
        for sources in self.target.content.verilog_sources:
            for src in sources.files:
                cmd.append(src)

        # add HDL sources for functional models
        for sources in self.target.content.functional_models:
            for src in sources.gen_files:
                cmd.append(src)

        # add VHDL source files
        # TODO: is it actually necessary to consolidate makelib commands together?  if subsequent makelib commands
        # append rather than replace files, then it should be OK (and simpler) to have a separate makelib for
        # each file in each library.
        libraries = OrderedDict()
        for sources in self.target.content.vhdl_sources:
            library = sources.library

            if library not in libraries:
                libraries[library] = []

            files = sources.files
            libraries[library] += files

        for library, sources in libraries.items():
            if library is not None:
                cmd += ['-makelib', library]
            else:
                cmd += ['-makelib']
            cmd += sources
            cmd += ['-endlib']

        # write TCL file
        with open(self.cfg.xcelium_config.tcl_input_path, 'w') as f:
            f.write('run\n')
            f.write('exit\n')

        # run xrun
        print(cmd)
        call(cmd, cwd=self.cfg.build_root)

    def prepare(self):
        """ Preparation of ifxxcelium Camino wrapper script"""
        if "ifxxcelium" in self.cfg.xcelium_config.xrun:
            cmd = []
            cmd += ['ifxxcelium', 'prepare', '-uc', 'rtl']
            if self.unit:
                cmd += ["-unit", self.unit ]
            if self.id:
                cmd += ["-id", self.id ]
            else:
                self.id = "xcelium"

            print(cmd)
            call(cmd, cwd=self.cfg.build_root)

            makefile = os.environ["WORKAREA"] + "/units/" + self.unit + "/simulation/" + self.id + "/Makefile"
            if "PHONY: inicio" not in open(makefile, 'r').read():
                self.patch_makefile(makefile)
            else:
                print("inicio make target already in Makefile, will not patch it")

        else:
            print("No ifxxcelium script detected, nothing to prepare..")

    def patch_makefile(self, file):
        """ patch content of generated Makefile and append inicio target
        :type file: str
        """

        inicio_target = open( os.path.dirname(__file__) + "/xcelium.make_target", 'r')

        print(f"Patching content of Makefile: {file}")
        with open(file, 'a+') as f:
            f.write(inicio_target.read())
            f.close()
