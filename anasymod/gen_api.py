from anasymod.structures.port_base import Port, PortIN, PortOUT
from anasymod.sim_ctrl.ctrlifc_datatypes import *
from anasymod.structures.signal_base import Signal
from anasymod.enums import PortDir
from typing import Union
from anasymod.codegen import CodeGenerator

# ToDo: think of a more convenient way to gen and assign to signal then using a Port object

io_obj_types = Union[DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal, AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal]


class GenAPI(CodeGenerator):
    """
    This is the general generator API custom tailored for generation of anasymod project files, e.g. top.
    """

    def __init__(self, line_ending='\n'):
        super().__init__(line_ending=line_ending)

    def indentation(self):
        self.print("    ")

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

    def assign_to(self, io_obj: io_obj_types, exp):
        """
        Assign 'exp' to signal 'io_obj.name'.
        NOTE: If the io_obj is of the AnalogSignal type, it is only possible to assign another signal of the same type
        or a constant value.

        :param io_obj: Signal to be assigned holds name of io_obj.name.
        :param exp: Expression to be assigned.
        """
        raise NotImplementedError()

    def _gen_port(self, io_obj: Union[DigitalCtrlInput, DigitalCtrlOutput, AnalogCtrlInput, AnalogCtrlOutput],
                  direction: PortDir):
        """
        Generate an input port using the io_obj object as input.
        :param port: Port object
        """
        raise NotImplementedError()

    def gen_parameter(self, param_obj: Union[DigitalCtrlInput, DigitalCtrlOutput, AnalogCtrlInput, AnalogCtrlOutput]):
        """
        Generate a parameter using the param_obj as input.

        :param param_obj: Object that includes a parameter
        """
        raise NotImplementedError()

    def gen_connection(self, io_objs: [io_obj_types]):
        """
        Connect an io_obj from upwards the hierarchy "upper_io_obj" to an io_obj further down the hierarchy "lower_io_obj".

        :param upper_io_obj:
        :param lower_io_obj:
        :return:
        """
        raise NotImplementedError()

    def decl_analog_port(self, io_obj: Union[AnalogCtrlInput, AnalogCtrlOutput]):
        """
        Generate a declaration for an analog signal. Necessary towork with SVREAL.

        :param io_obj:
        """
        raise NotImplementedError()

    def pass_analog_port_format(self, io_objs: [io_obj_types]):
        """
        Pass formatting information into instantiated module for the connected analog signal.

        :param io_connection: List of two IO objects that are connected to each other.
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
            self.println(f"{'input' if port.direction == PortDir.IN else 'output'} wire logic [{str(port.width - 1)}:0] {port.name}")
        else:
            self.println(f"{'input' if port.direction == PortDir.IN else 'output'} wire logic {port.name}")

    def gen_signal(self, port: Union[Port, PortIN, PortOUT]):
        """
        Generate a signal using the port object as input.
        :param port: Port object
        """

        if port.width > 1:
            self.println(f"logic [{str(port.width - 1)}:0] {port.name};")
        else:
            self.println(f"logic {port.name};")

    def _gen_signal(self, io_obj: io_obj_types):
        """
        Generate a signal using the io object as input.
        :param io_obj: io object
        """

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal)):
            self.println(f"`MAKE_REAL({io_obj.name}, {io_obj.range});")
        elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal)):
            if io_obj.width > 1:
                self.println(f"logic [{str(io_obj.width - 1)}:0] {io_obj.name};")
            else:
                self.println(f"logic {io_obj.name};")

    def assign_to(self, io_obj: io_obj_types, exp):
        """
        Assign 'exp' to signal 'io_obj.name'.
        NOTE: If the io_obj is of the AnalogSignal type, it is only possible to assign another signal of the same type
        or a constant value.

        :param io_obj: Signal to be assigned holds name of io_obj.name.
        :param exp: Expression to be assigned.
        """

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal)):
            if isinstance(exp, (AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal)):
                self.println(f"`ASSIGN_REAL({exp}, {io_obj.name});")
            else:
                try:
                    exp = str(float(exp))
                    self.println(f"`ASSIGN_CONST_REAL({exp}, {io_obj.name});")
                except:
                    raise Exception(f"The provided expression is not supported for Analog Signals, only assignment of another"
                                    f"AnalogSignal object or a cosntant value is supported; given: {exp}")
        elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal)):
            self.println(f"assign {io_obj.name} = {exp};")

    def _gen_port(self, io_obj: io_obj_types, direction: PortDir):
        """
        Generate an input port using the io_obj object as input.
        :param port: Port object
        """

        if direction in [PortDir.IN]:
            if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput)):
                self.println(f"`INPUT_REAL({io_obj.abs_path}, {io_obj.name})")
            elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput)):
                if io_obj.width > 1:
                    self.println(f"input wire logic [{str(io_obj.width - 1)}:0] {io_obj.name}")
                else:
                    self.println(f"input wire logic {io_obj.name}")
        elif direction in [PortDir.OUT]:
            if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput)):
                self.println(f"`OUTPUT_REAL({io_obj.abs_path}, {io_obj.name})")
            elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput)):
                if io_obj.width > 1:
                    self.println(f"output wire logic [{str(io_obj.width - 1)}:0] {io_obj.name}")
                else:
                    self.println(f"output wire logic {io_obj.name}")
        else:
            raise Exception(f"No valid direction provided: {direction}")

    def gen_parameter(self, param_obj):
        """
        Generate a parameter using the param_obj as input.

        :param param_obj: Object that includes a parameter
        """

        self.print(f"parameter {param_obj.type} {param_obj.name}={param_obj.value}")

    def gen_connection(self, io_objs: [io_obj_types]):

        """
        Connect an io_obj from upwards the hierarchy "upper_io_obj" to an io_obj further down the hierarchy "lower_io_obj".
        """
        if len(io_objs) == 2:
            self.print(f".{io_objs[0].name}({io_objs[1].name})")
        else:
            raise Exception(
                f"Wrong number of io_objects provided in list, exactly two are requrend, provided were: {len(io_objs)}")

    def decl_analog_port(self, io_obj: Union[AnalogCtrlInput, AnalogCtrlOutput]):
        """
        Generate a declaration for an analog signal. Necessary towork with SVREAL.

        :param io_obj:
        """

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput)):
            self.print(f"`DECL_REAL({io_obj.name})")

    def pass_analog_port_format(self, io_objs: [io_obj_types]):
        """
        Pass formatting information into instantiated module for the connected analog signal.

        :param io_objs: List of two IO objects that are connected to each other.
        """

        if len(io_objs) == 2:
            self.print(f".{io_objs[0].name}({io_objs[1].name})")
            if isinstance(io_objs[0], (AnalogCtrlInput, AnalogCtrlOutput)):
                self.print(f"`PASS_REAL({io_objs[0].name}, {io_objs[1].name})")
            else:
                raise Exception(f"ERROR: Wrong io type; supported only: {type(AnalogCtrlOutput), type(AnalogCtrlInput)}"
                                f"provided: {type(io_objs[0])}")
        else:
            raise Exception(
                f"Wrong number of io_objects provided in list, exactly two are requrend, provided were: {len(io_objs)}")


class ModuleInst():
    """
    Container for Module Structure.
    """

    def __init__(self, api: GenAPI, name):
        self.api = api

        self.name = name
        self.analog_inputs = []
        self.analog_outputs = []
        self.digital_inputs = []
        self.digital_outputs = []
        self.parameters = []

        self.connections = []

    def add_inputs(self, io_objs: [io_obj_types], connections=None):
        if connections:
            if len(io_objs) != len(connections):
                raise Exception(f"ERROR: Each provided port object needs to have a connection counterpart! "
                                f"io_objs:{io_objs}, connections: {connections}")
            for io_obj, connection in zip(io_objs, connections):
                self.add_input(io_obj=io_obj, connection=connection)
        else:
            for io_obj in io_objs:
                self.add_input(io_obj=io_obj)

    def add_input(self, io_obj: io_obj_types, connection=None):
        if connection:
            if isinstance(connection, (AnalogCtrlInput, AnalogCtrlOutput, DigitalCtrlInput, DigitalCtrlOutput)):
                self.connect(io_obj=io_obj, io_obj_con=connection)
            else:
                raise Exception(f"Unsupported connection type was provided, supported types are. {io_obj_types}, "
                                f"provided: {type(connection)}")

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput)):
            self.analog_inputs += io_obj
        else:
            self.digital_inputs += io_obj

    def add_outputs(self, io_objs: [io_obj_types], connections=None):
        if connections:
            if len(io_objs) != len(connections):
                raise Exception(f"ERROR: Each provided port object needs to have a connection counterpart! "
                                f"io_objs:{io_objs}, connections: {connections}")
            for io_obj, connection in zip(io_objs, connections):
                self.add_output(io_obj=io_obj, connection=connection)
        else:
            for io_obj in io_objs:
                self.add_output(io_obj=io_obj)

    def add_output(self, io_obj: io_obj_types, connection=None):
        if connection:
            if isinstance(connection, (AnalogCtrlInput, AnalogCtrlOutput, DigitalCtrlInput, DigitalCtrlOutput)):
                self.connect(io_obj=io_obj, io_obj_con=connection)
            else:
                raise Exception(f"Unsupported connection type was provided, supported types "
                                f"are. {io_obj_types}, provided: {type(connection)}")

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput)):
            self.analog_outputs += io_obj
        else:
            self.digital_outputs += io_obj

    def add_parameters(self, io_objs: [io_obj_types]):
        for io_obj in io_objs:
            self.add_parameter(io_obj=io_obj)

    def add_parameter(self, io_obj: io_obj_types):
        self.parameters += io_obj

    def connect(self, io_obj: io_obj_types, io_obj_con: io_obj_types):
        """
        Connect io_obj to io_obj_con. This is important for later module instantiations.

        :param io_obj:
        :param io_obj_con:
        """

        # ToDo: Improve type checkers to prevent multiple drivers.
        if (io_obj in [AnalogCtrlOutput, AnalogCtrlInput] and io_obj_con in [AnalogCtrlOutput, AnalogCtrlInput]) or (
                io_obj in [DigitalCtrlOutput, DigitalCtrlInput] and io_obj_con in [DigitalCtrlOutput, DigitalCtrlInput]):
            self.connections += [io_obj, io_obj_con]
        else:
            raise Exception(f"IO types of objects to be connected do not match:"
                            f"io_obj: {type(io_obj)}, io_obj_con: {type(io_obj_con)}")

    def generate_header(self):
        """
        Generate full module header.
        """
        self.api.println(f"module {self.name} #(")
        self.api.indentation()

        ## Add parameter section
        analog_ports = self.analog_inputs + self.analog_outputs
        if analog_ports:
            for analog_port in analog_ports[:-1]:
                self.api.indentation()
                self.api.decl_analog_port(analog_port)
                self.api.println(",")
            self.api.indentation()
            self.api.decl_analog_port(analog_ports[-1])

            if self.parameters:
                self.api.println(",")
            else:
                self.api.println("")

        if self.parameters:
            for parameter in self.parameters[:-1]:
                self.api.indentation()
                self.api.gen_parameter(param_obj=parameter)
                self.api.println(",")
            self.api.indentation()
            self.api.gen_parameter(param_obj=self.parameters[-1])
            self.api.println("")

        self.api.println(f") (")

        #### Add port section
        inputs = self.analog_inputs + self.digital_inputs
        if inputs:
            for input in inputs[:-1]:
                self.api.indentation()
                self.api._gen_port(io_obj=input, direction=PortDir.IN)
                self.api.println(",")
            self.api.indentation()
            self.api._gen_port(io_obj=inputs[-1], direction=PortDir.IN)
            self.api.println("")

        outputs = self.analog_outputs + self.digital_outputs
        if outputs:
            for output in outputs[:-1]:
                self.api.indentation()
                self.api._gen_port(io_obj=output, direction=PortDir.OUT)
                self.api.println(",")
            self.api.indentation()
            self.api._gen_port(io_obj=outputs[-1], direction=PortDir.OUT)
            self.api.println("")

        self.api.println(f");")

    def generate_instantiation(self):
        """
        Generate instantiation for module.
        """
        self.api.indentation()
        self.api.println(f"{self.name} #(")

        ## Add parameter section
        analog_connections = []
        for connection in self.connections:
            if connection[0] in [AnalogCtrlInput, AnalogCtrlOutput]:
                analog_connections += connection
        if analog_connections:
            for analog_connection in analog_connections[:-1]:
                self.api.indentation()
                self.api.indentation()
                self.api.pass_analog_port_format(io_objs=analog_connection)
                self.api.println(f",")
            self.api.indentation()
            self.api.indentation()
            self.api.pass_analog_port_format(analog_connections[-1])
            if self.parameters:
                self.api.println(",")
            else:
                self.api.println("")

        if self.parameters:
            for parameter in self.parameters[:-1]:
                self.api.indentation()
                self.api.indentation()
                self.api.gen_parameter(param_obj=parameter)
                self.api.println(",")
            self.api.indentation()
            self.api.indentation()
            self.api.gen_parameter(param_obj=self.parameters[-1])
            self.api.println("")

        self.api.indentation()
        self.api.println(f") {self.name}_i (")

        ## Add port section
        if self.connections:
            for connection in self.connections[:-1]:
                self.api.indentation()
                self.api.indentation()
                self.api.gen_connection(connection)
                self.api.println(f",")
            self.api.indentation()
            self.api.indentation()
            self.api.gen_connection(self.connections[-1])
            self.api.println("")

        self.api.indentation()
        self.api.println(f");")
