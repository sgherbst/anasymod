from anasymod.structures.port_base import Port, PortIN, PortOUT
from anasymod.sim_ctrl.ctrlifc_datatypes import *
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

    def assign_to_signal(self, io_obj: Union[DigitalCtrlInput, DigitalCtrlOutput,AnalogCtrlInput, AnalogCtrlOutput]):
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

    def _gen_signal(self, io_obj: Union[DigitalCtrlInput, DigitalCtrlOutput,AnalogCtrlInput, AnalogCtrlOutput]):
        """
        Generate a signal using the io object as input.
        :param io_obj: io object
        """

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput)):
            self.println(f"`MAKE_REAL({io_obj.name}, {io_obj.range});")
        elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput)):
            if io_obj.width > 1:
                self.println(f"logic [{str(io_obj.width-1)}:0] {io_obj.name};")
            else:
                self.println(f"logic {io_obj.name};")

    def assign_to_signal(self, io_obj: Union[DigitalCtrlInput, DigitalCtrlOutput,AnalogCtrlInput, AnalogCtrlOutput]):
        """
        Assign 'exp' to signal 'io_obj.name'.

        :param io_obj: Signal to be assigned holds name of io_obj.name.
        :param exp: Expression to be assigned.
        :return:
        """

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput)):
            self.println(f"`ASSIGN_REAL({io_obj.abs_path}, {io_obj.name});")
        elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput)):
            self.println(f"assign {io_obj.name} = {io_obj.abs_path};")

    def gen_in_port(self, io_obj: Union[DigitalCtrlInput, DigitalCtrlOutput,AnalogCtrlInput, AnalogCtrlOutput]):
        """
        Generate an input port using the io_obj object as input.
        :param port: Port object
        """

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput)):
            self.println(f"``INPUT_REAL({io_obj.abs_path}, {io_obj.name})")
        elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput)):
            if io_obj.width > 1:
                self.println(f"input wire logic [{str(io_obj.width-1)}:0] {io_obj.name}")
            else:
                self.println(f"input wire logic {io_obj.name}")

                #HIER WEITER: neben port muss bei analog signalen auch ein parameter angelegt werden
