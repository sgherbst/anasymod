from anasymod.blocks.generic_ip import TemplGenericIp
from anasymod.targets import FPGATarget
from anasymod.config import EmuConfig
from anasymod.structures.port_base import PortOUT, PortIN
from typing import Union

class TemplVIO(TemplGenericIp):
    def __init__(self, target: FPGATarget, ports: dict(list(Union[PortIN, PortOUT]))):
        # set defaults
        self.target = target

        ####################################################
        # Add module ports
        ####################################################
        self.ports = ports
        """ type : {[PortBase]}"""

        # Invert direction
        for port in self.ports['vio_ports']:
            port.invert_direction()

        # Add ports that are created in this module
        self.add_ports()

        ####################################################
        # Generate ip core config for clk wizard
        ####################################################

        props = {}
        num_inputs = 0
        num_outputs = 0

        for port in self.ports['vio_ports']:
            # handle input ports
            if isinstance(port, PortIN):
                num_inputs += 1
                props[f'CONFIG.C_PROBE_IN{num_inputs}_WIDTH'] = str(port.num_bits)

            # handle input ports
            elif isinstance(port, PortOUT):
                num_outputs += 1
                props[f'CONFIG.C_PROBE_OUT{num_outputs}_INIT_VAL'] = str(port.num_bits)
                if port.init is not None:
                    props[f'CONFIG.C_PROBE_OUT{num_outputs}_INIT_VAL'] = str(port.init)

        props['CONFIG.C_NUM_PROBE_IN'] = str(num_inputs)
        props['CONFIG.C_NUM_PROBE_OUT'] = str(num_outputs)

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
    print(TemplVIO(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file='')), ports={'vio_ports' : []}).render())

if __name__ == "__main__":
    main()