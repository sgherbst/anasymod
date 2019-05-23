from anasymod.structures.port_base import Port, PortIN, PortOUT
from anasymod.structures.signal_base import Signal
from anasymod.enums import PortDir
from typing import Union
from anasymod.codegen import CodeGenerator

#ToDo: think of a more convenient way to gen and assign to signal then using a Port object

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

    def gen_signal(self, port: Union[Port, PortIN, PortOUT]):
        """
        Generate a signal using the port object as input.
        :param port: Port object
        """
        raise NotImplementedError()

    def assign_to_signal(self, port: Union[Port, PortIN, PortOUT], signal: Signal):
        """
        Assign signal with name of 'port' to signal of 'signal'. By default the abs_path of 'signal' will be used.
        If it is None, signal name will be used.

        :param port: name of object port will be used to define the signal name, that abspath of 'signal' will be assigned to.
        :param signal: signal object, that will be used to assign.
        :return:
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

    def assign_to_signal(self, port: Union[Port, PortIN, PortOUT], signal: Signal):
        """
        Assign signal with name of 'port' to signal of 'signal'. By default the abs_path of 'signal' will be used.
        If it is None, signal name will be used.

        :param port: name of object port will be used to define the signal name, that abspath of 'signal' will be assigned to.
        :param signal: signal object, that will be used to assign.
        :return:
        """

        if signal.abs_path is None:
            # Directly assign the signal name
            self.println(f"assign {port.name} = {signal.name};")
        else:
            # Assign the abspath
            self.println(f"assign {port.name} = {signal.abs_path};")
