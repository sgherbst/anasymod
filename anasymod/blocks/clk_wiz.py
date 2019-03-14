from anasymod.blocks.generic_ip import TemplGenericIp
from anasymod.targets import FPGATarget
from anasymod.config import EmuConfig
from anasymod.util import read_config, update_config
from anasymod.enums import ConfigSections, PortDirections
from anasymod.structures.port_base import PortBase

class TemplClkWiz(TemplGenericIp):
    def __init__(self, cfg: EmuConfig, target: FPGATarget, num_out_clks=1):

        self.target = target
        self.num_out_clks = num_out_clks
        self.prj_cfg = cfg

        # add some default enums
        single_ended = 'Single_ended_clock_capable_pin'
        differential = 'Differential_clock_capable_pin'

        ####################################################
        # Initialize config
        ####################################################
        self.cfg = {}
        self.cfg['input_freq'] = self.prj_cfg.board.cfg['clk_freq']
        self.cfg['input_source'] = single_ended
        self.cfg['output_freq'] = target.cfg['emu_clk_freq']
        self.cfg['dbg_hub_clk_freq'] = self.prj_cfg.board.cfg['dbg_hub_clk_freq']
        self.cfg['num_out_clks'] = num_out_clks

        # Update config options by reading from config file
        self.cfg = update_config(cfg=self.cfg, config_section=read_config(cfg_file=self.prj_cfg._cfg_file, section=ConfigSections.CLK))

        ####################################################
        # Add module ports
        ####################################################
        self.ports = {}
        """ type : {PortBase}"""

        self.gen_ports()

        ####################################################
        # Generate ip core config for clk wizard
        ####################################################
        props = {}
        # Add input clks
        props['CONFIG.PRIM_IN_FREQ'] = str(self.cfg['input_freq'] * 1e-6)
        props['CONFIG.PRIM_SOURCE'] = self.cfg['input_source']

        # Add master output clk (emu_clk)
        props['CONFIG.CLKOUT1_REQUESTED_OUT_FREQ'] = (self.cfg['output_freq'] * 1e-6)

        # Add debug clk
        props[f'CONFIG.CLKOUT2_USED'] = 'true'
        props[f'CONFIG.CLKOUT2_REQUESTED_OUT_FREQ'] = (self.cfg['dbg_hub_clk_freq'] * 1e-6)

        # Add additional output clks
        if self.num_out_clks > 1:
            props['CONFIG.FEEDBACK_SOURCE'] = 'FDBK_AUTO'

            for k in range(1, self.num_out_clks):
                props[f'CONFIG.CLKOUT{k+2}_USED'] = 'true'
                props[f'CONFIG.CLKOUT{k+2}_REQUESTED_OUT_FREQ'] = (self.cfg['output_freq'] * 1e-6)
                props[f'CONFIG.CLKOUT{k+2}_DRIVES'] = 'BUFGCE'

        super().__init__(ip_name='clk_wiz', target=self.target, props=props)

    def gen_ports(self):

        # Add signals for input clk
        if isinstance(self.target.prj_cfg.board.cfg['clk_pin'], list):
            if len(self.target.prj_cfg.board.cfg['clk_pin'])==2:
                clk_in_ports = ['clk_in1_p', 'clk_in1_n']
            elif len(self.target.prj_cfg.board.cfg['clk_pin'])==1:
                clk_in_ports = ['clk_in1']
            else:
                raise ValueError(f"Wrong number of pins provided for boards parameter 'clk_pin', expecting 1 or 2, provided:{len(self.target.prj_cfg.board.cfg['clk_pin'])}")
        else:
            raise ValueError(f"Wrong type for boards parameter 'clk_pin', expecting list, provided:{type(self.target.prj_cfg.board.cfg['clk_pin'])}")
        for port in clk_in_ports:
            self.ports[port] = PortBase(name=port, direction=PortDirections.IN)

        #self.ports += [PortBase(name=port, direction=PortDirections.IN) for port in clk_in_ports]

        # Add signals for first output clk
        self.ports['clk_out1'] = PortBase(name='clk_out1', direction=PortDirections.OUT)

        # Add signals for debug clk
        self.ports['clk_out2'] = PortBase(name='clk_out2', direction=PortDirections.OUT)

        # Add signals for additional output clks
        for k in range(1, self.num_out_clks):
            self.ports[f'clk_out{k+2}_ce'] = PortBase(name=f'clk_out{k+2}_ce', direction=PortDirections.IN)
            self.ports[f'clk_out{k+2}'] = PortBase(name=f'clk_out{k+2}', direction=PortDirections.OUT)

def main():
    pass

if __name__ == "__main__":
    main()
