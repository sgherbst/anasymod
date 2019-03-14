from anasymod.sim.sim import Simulator
from anasymod.util import call
from anasymod.targets import SimulationTarget
from anasymod.config import EmuConfig

class XceliumSimulator(Simulator):
    def __init__(self, cfg: EmuConfig, target: SimulationTarget):
        super().__init__(cfg=cfg, target=target)

    def simulate(self):
        # build up the simulation command
        cmd = [self.cfg.xcelium_config.xrun, '-sv', '-top', self.target.cfg.top_module, '-input', self.cfg.xcelium_config.tcl_input_path]

        # add defines
        for define in self.target.content['defines']:
            for k, v in define.define.items():
                if v is not None:
                    cmd.append(f"+define+{k}={v}")
                else:
                    cmd.append(f"+define+{k}")


        # add verilog headers
        for header_obj in self.target.content['verilog_headers']:
            for file in header_obj.files:
                cmd.extend(['-incdir', file])

        # add verilog source files
        for source_obj in self.target.content['verilog_sources']:
            for file in source_obj.files:
                cmd.extend(file)

        #ToDo add source option for vhdl sources, will be necessary for NFC

        # write TCL file
        with open(self.cfg.xcelium_config.tcl_input_path, 'w') as f:
            f.write('run\n')
            f.write('exit\n')

        # run xrun
        print(cmd)
        call(cmd, cwd=self.cfg.build_root)
