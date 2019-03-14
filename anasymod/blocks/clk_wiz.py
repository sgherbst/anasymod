from anasymod.blocks.generic_ip import TemplGenericIp
from anasymod.targets import FPGATarget
from anasymod.structures.port_base import PortIN, PortOUT
from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections

class TemplClkWiz(TemplGenericIp):
    def __init__(self, target: FPGATarget, num_out_clks=1):

        self.target = target

        ####################################################
        # Initialize config
        ####################################################
        self.cfg = Config(target=self.target, num_out_clks=num_out_clks)

        # Update config options by reading from config file
        self.cfg.update_config()

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
        props['CONFIG.PRIM_IN_FREQ'] = str(self.cfg.input_freq * 1e-6)
        props['CONFIG.PRIM_SOURCE'] = self.cfg.input_source

        # Add master output clk (emu_clk)
        props['CONFIG.CLKOUT1_REQUESTED_OUT_FREQ'] = (self.cfg.output_freq * 1e-6)

        # Add debug clk
        props[f'CONFIG.CLKOUT2_USED'] = 'true'
        props[f'CONFIG.CLKOUT2_REQUESTED_OUT_FREQ'] = (self.cfg.dbg_hub_clk_freq * 1e-6)

        # Add additional output clks
        if self.cfg.num_out_clks > 1:
            props['CONFIG.FEEDBACK_SOURCE'] = 'FDBK_AUTO'

            for k in range(1, self.cfg.num_out_clks):
                props[f'CONFIG.CLKOUT{k+2}_USED'] = 'true'
                props[f'CONFIG.CLKOUT{k+2}_REQUESTED_OUT_FREQ'] = (self.cfg.output_freq * 1e-6)
                props[f'CONFIG.CLKOUT{k+2}_DRIVES'] = 'BUFGCE'

        ####################################################
        # Prepare Template substitutions
        ####################################################

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
            self.ports[port] = PortIN(name=port)

        #self.ports += [PortBase(name=port, direction=PortDirections.IN) for port in clk_in_ports]

        # Add signals for first output clk
        self.ports['clk_out1'] = PortOUT(name='clk_out1')

        # Add signals for debug clk
        self.ports['clk_out2'] = PortOUT(name='clk_out2')

        # Add signals for additional output clks
        for k in range(1, self.cfg.num_out_clks):
            self.ports[f'clk_out{k+2}_ce'] = PortIN(name=f'clk_out{k+2}_ce')
            self.ports[f'clk_out{k+2}'] = PortOUT(name=f'clk_out{k+2}')

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """

    def __init__(self, target: FPGATarget, num_out_clks):
        super().__init__(cfg_file=target.prj_cfg.cfg_file, section=ConfigSections.CLK)

        # add some default enums
        single_ended = 'Single_ended_clock_capable_pin'
        differential = 'Differential_clock_capable_pin'

        self.input_freq = target.prj_cfg.board.cfg.clk_freq
        self.input_source = single_ended
        self.output_freq = target.cfg.emu_clk_freq
        self.dbg_hub_clk_freq = target.prj_cfg.board.cfg.dbg_hub_clk_freq
        self.num_out_clks = num_out_clks

def main():
    pass

if __name__ == "__main__":
    main()
