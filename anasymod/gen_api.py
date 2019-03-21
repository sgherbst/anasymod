from anasymod.structures.port_base import Port, PortIN, PortOUT
from anasymod.enums import PortDir
from typing import Union
from anasymod.codegen import CodeGenerator

class GenAPI(CodeGenerator):
    """
    This is the general generator API custom tailored for generation of anasymod project files, e.g. top.
    """
    def __init__(self, line_ending='\n'):
        super().__init__(line_ending=line_ending)

    def gen_port(self, port: Union[Port, PortIN, PortOUT]):
        """
        Generate a port using the port object as input.
        :param port: Port object
        """
        raise NotImplementedError()

class SVAPI(GenAPI):
    """
    This is the SV specific generator API custom for generation of anasymod project files, e.g. top.sv.
    """
    def __init__(self, line_ending='\n'):
        super().__init__(line_ending=line_ending)

    def gen_port(self, port: Union[Port, PortIN, PortOUT]):
        """
        Generate a port using the port object as input.
        :param port: Port object
        """

        if port.width > 1:
            self.println(f"{'input' if port.direction == PortDir.IN else 'output'} wire logic [{str(port.width-1)}:0] {port.name}")
        else:
            self.println(f"{'input' if port.direction == PortDir.IN else 'output'} wire logic {port.name}")

    def gen_signal(self, port: Union[Port, PortIN, PortOUT]):
        """
        Generate a signal using the port object as input.
        :param port: Port object
        """

        if port.width > 1:
            self.println(f"logic [{str(port.width-1)}:0] {port.name};")
        else:
            self.println(f"logic {port.name};")

    #def map_port(self, port: Union[Port, PortIN, PortOUT]):
