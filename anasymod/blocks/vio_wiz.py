from anasymod.blocks.generic_ip import TemplGenericIp
from anasymod.targets import FPGATarget
from anasymod.config import EmuConfig
from anasymod.structures.structure_config import StructureConfig
from anasymod.structures.port_base import PortOUT, PortIN
from typing import Union

class TemplVIO(TemplGenericIp):
    def __init__(self, target: FPGATarget):
        # set defaults
        self.target = target

        ####################################################
        # Generate ip core config for clk wizard
        ####################################################

        props = {}

        # handle input ports
        for k, port in enumerate(self.target.str_cfg.vio_i_ports):
            props[f'CONFIG.C_PROBE_IN{k+1}_WIDTH'] = str(port.width)

        # handle input ports
        for k, port in enumerate(self.target.str_cfg.vio_r_ports + self.target.str_cfg.vio_s_ports + self.target.str_cfg.vio_o_ports):
                props[f'CONFIG.C_PROBE_OUT{k+1}_WIDTH'] = str(port.width)
                if port.init_value is not None:
                    props[f'CONFIG.C_PROBE_OUT{k+1}_INIT_VAL'] = str(port.init_value)

        props['CONFIG.C_NUM_PROBE_IN'] = str(len(self.target.str_cfg.vio_i_ports))
        props['CONFIG.C_NUM_PROBE_OUT'] = str(len(self.target.str_cfg.vio_r_ports + self.target.str_cfg.vio_s_ports + self.target.str_cfg.vio_o_ports))

        ####################################################
        # Prepare Template substitutions
        ####################################################

        super().__init__(ip_name='vio', target=self.target, props=props)



    def add_ports(self):
        """
        Add ports to module that are created in the module.
        """
        pass

def main():
    print(TemplVIO(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()