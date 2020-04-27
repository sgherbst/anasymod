from anasymod.sim_ctrl.datatypes import *
from anasymod.enums import PortDir
from typing import Union
from anasymod.generators.codegen import CodeGenerator

io_obj_types = DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal, AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal, AnalogProbe
io_obj_types_union = Union[DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal, AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal, AnalogProbe]
io_obj_types_str_union = Union[DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal, AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal, AnalogProbe, str]

class GenAPI(CodeGenerator):
    """
    This is the general generator API custom tailored for generation of anasymod project files, e.g. top.
    """

    def __init__(self, line_ending='\n'):
        super().__init__(line_ending=line_ending)

    def gen_signal(self, io_obj: io_obj_types_union):
        """
        Generate a signal using the io object as input.
        :param io_obj: io object
        """
        raise NotImplementedError()

    def gen_port(self, io_obj: io_obj_types_union, direction: PortDir):
        """
        Generate an input port using the io_obj object as input.
        :param port: Port object
        """
        raise NotImplementedError()

    def gen_parameter(self, param_obj: io_obj_types_union):
        """
        Generate a parameter using the param_obj as input.

        :param param_obj: Object that includes a parameter
        """
        raise NotImplementedError()

    def gen_connection(self, io_objs: [io_obj_types_union]):
        """
        Connect an io_obj from upwards the hierarchy "upper_io_obj" to an io_obj further down the hierarchy "lower_io_obj".

        :param upper_io_obj:
        :param lower_io_obj:
        :return:
        """
        raise NotImplementedError()

    def assign_to(self, io_obj: io_obj_types_union, exp):
        """
        Assign 'exp' to signal 'io_obj.name'.
        NOTE: If the io_obj is of the AnalogSignal type, it is only possible to assign another signal of the same type
        or a constant value.

        :param io_obj: Signal to be assigned holds name of io_obj.name.
        :param exp: Expression to be assigned.
        """
        raise NotImplementedError()

    def decl_analog_port(self, io_obj: Union[AnalogCtrlInput, AnalogCtrlOutput]):
        """
        Generate a declaration for an analog signal. Necessary towork with SVREAL.

        :param io_obj:
        """
        raise NotImplementedError()

    def pass_analog_port_format(self, io_obj: io_obj_types_union, io_obj_format: io_obj_types_union):
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

    def gen_signal(self, io_obj: io_obj_types_union):
        """
        Generate a signal using the io object as input.
        :param io_obj: io object
        """

        if isinstance(io_obj, AnalogProbe):
            self.writeln(f"`MAKE_GENERIC_REAL({io_obj.name}, {io_obj.range}, {io_obj.width});")
        elif isinstance(io_obj, AnalogSignal):
            self.writeln(f"`MAKE_REAL({io_obj.name}, {io_obj.range});")
        elif isinstance(io_obj, DigitalSignal):
            if io_obj.width > 1:
                self.writeln(f'logic [{str(io_obj.width)}  - 1:0] {io_obj.name};')
            else:
                self.writeln(f"logic {io_obj.name};")

    def gen_port(self, io_obj: io_obj_types_union, direction: PortDir):
        """
        Generate an input port using the io_obj object as input.
        :param port: Port object
        :rtype str: generated SV for port.
        """

        if direction in [PortDir.IN]:
            if isinstance(io_obj, AnalogSignal):
                return f"`INPUT_REAL({io_obj.name})"
            elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal)):
                width = f'[{str(io_obj.width - 1)}:0] ' if io_obj.width > 1 else ''
                return f"input wire logic {'signed ' if io_obj.signed else ''}{width}{io_obj.name}"
        elif direction in [PortDir.OUT]:
            if isinstance(io_obj, AnalogSignal):
                return f"`OUTPUT_REAL({io_obj.name})"
            elif isinstance(io_obj, (DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal)):
                width = f'[{str(io_obj.width - 1)}:0] ' if io_obj.width > 1 else ''
                return f"output wire logic {'signed ' if io_obj.signed else ''}{width}{io_obj.name}"
        else:
            raise Exception(f"No valid direction provided: {direction}")

    def gen_parameter(self, param_obj):
        """
        Generate a parameter using the param_obj as input.

        :param param_obj: Object that includes a parameter
        :rtype str: returns generated parameter statement
        """

        return f"parameter {param_obj.type} {param_obj.name}={param_obj.value}"

    def gen_connection(self, io_objs: [io_obj_types_str_union]):
        """
        Connect an io_obj from upwards the hierarchy "upper_io_obj" to an io_obj further down the hierarchy "lower_io_obj".
        :rtype str: returns generated string for the connection
        """
        if len(io_objs) == 2:
            if isinstance(io_objs[1], (io_obj_types)): # Connect two signal type objects
                return f".{io_objs[0].name}({io_objs[1].name})"
            elif isinstance(io_objs[1], str): # Connect a signal type object with a fixed value
                return f".{io_objs[0].name}({io_objs[1]})"
            else:
                raise Exception(f'Wrong type passed for connection:{type(io_objs[1])}')
        else:
            raise Exception(
                f"Wrong number of io_objects provided in list, exactly two are requrend, provided were: {len(io_objs)}")

    def assign_to(self, io_obj: io_obj_types_str_union, exp):
        """
        Assign 'exp' to signal 'io_obj.name'.
        NOTE: If the io_obj is of the AnalogSignal type, it is only possible to assign another signal of the same type
        or a constant value.

        :param io_obj: Signal to be assigned holds name of io_obj.name.
        :param exp: Expression to be assigned.
        """
        if isinstance(io_obj, AnalogSignal) and not isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput, AnalogProbe)):
            if isinstance(exp, AnalogSignal):
                self.writeln(f"`ASSIGN_REAL({exp}, {io_obj.name});")
            if isinstance(exp, str):
                self.writeln(f"`ASSIGN_REAL({exp}, {io_obj.name});")
            else:
                try:
                    exp = str(float(exp))
                    self.writeln(f"`ASSIGN_CONST_REAL({exp}, {io_obj.name});")
                except:
                    raise Exception(f"The provided expression is not supported for Analog Signals, only assignment of another"
                                    f"AnalogSignal object or a constant value is supported; given: '{exp}'")
        elif isinstance(io_obj, (DigitalSignal, AnalogCtrlInput, AnalogCtrlOutput, AnalogProbe)):
            self.writeln(f"assign {io_obj.name} = {exp};")
        elif isinstance(io_obj, str):
            self.writeln(f"assign {io_obj} = {exp};")
        else:
            raise Exception(f'Not supported signal type provided:{type(io_obj)}')

    def decl_analog_port(self, io_obj: Union[AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal]):
        """
        Generate a declaration for an analog signal. Necessary towork with SVREAL.

        :param io_obj:
        :rtype str: returns generated analog port
        """

        if isinstance(io_obj, (AnalogCtrlInput, AnalogCtrlOutput, AnalogSignal)):
            return f"`DECL_REAL({io_obj.name})"

    def pass_analog_port_format(self, io_obj: io_obj_types_union, io_obj_format: io_obj_types_union):
        """
        Pass formatting information into instantiated module for the connected analog signal.

        :param io_objs: List of two IO objects that are connected to each other.
        :rtype str: returns generated code for passing analog port format
        """

        if isinstance(io_obj, AnalogSignal):
            return f"`PASS_REAL({io_obj.name}, {io_obj_format.name})"
        else:
            raise Exception(f"ERROR: Wrong io type; supported only: "
                            f"{type(AnalogCtrlOutput), type(AnalogCtrlInput), type(AnalogSignal)}"
                            f"provided: {type(io_obj), type(io_obj_format)}")

class ModuleInst():
    """
    Container for Module Structure.
    """

    def __init__(self, api: GenAPI, name, inst_name=None):
        self.api = api

        self.name = name
        self.inst_name = inst_name if inst_name else f'{name}_i'
        self.analog_inputs = []
        self.analog_outputs = []
        self.digital_inputs = []
        self.digital_outputs = []
        self.parameters = []

        self.connections = []

    def add_inputs(self, io_objs: [io_obj_types_union], connections=None):
        if connections:
            if len(io_objs) != len(connections):
                raise Exception(f"ERROR: Each provided port object needs to have a connection counterpart! "
                                f"io_objs:{io_objs}, connections: {connections}")
            for io_obj, connection in zip(io_objs, connections):
                self.add_input(io_obj=io_obj, connection=connection)
        else:
            for io_obj in io_objs:
                self.add_input(io_obj=io_obj)

    def add_input(self, io_obj: io_obj_types_union, connection=None):
        if connection:
            if isinstance(connection, (AnalogSignal, DigitalSignal, str)):
                self.connect(io_obj=io_obj, io_obj_con=connection)
            else:
                raise Exception(f"Unsupported connection type was provided, supported types are. {io_obj_types_str_union}, "
                                f"provided: {type(connection)}")

        if isinstance(io_obj, (AnalogSignal)):
            self.analog_inputs.append(io_obj)
        else:
            self.digital_inputs.append(io_obj)

    def add_outputs(self, io_objs: [io_obj_types_union], connections=None):
        if connections:
            if len(io_objs) != len(connections):
                raise Exception(f"ERROR: Each provided port object needs to have a connection counterpart! "
                                f"io_objs:{io_objs}, connections: {connections}")
            for io_obj, connection in zip(io_objs, connections):
                self.add_output(io_obj=io_obj, connection=connection)
        else:
            for io_obj in io_objs:
                self.add_output(io_obj=io_obj)

    def add_output(self, io_obj: io_obj_types_union, connection=None):
        if connection:
            if isinstance(connection, (AnalogSignal, DigitalSignal, str)):
                self.connect(io_obj=io_obj, io_obj_con=connection)
            else:
                raise Exception(f"Unsupported connection type was provided, supported types "
                                f"are. {io_obj_types_union}, provided: {type(connection)}")

        if isinstance(io_obj, (AnalogSignal)):
            self.analog_outputs.append(io_obj)
        else:
            self.digital_outputs.append(io_obj)

    def add_parameters(self, io_objs: [io_obj_types_union]):
        for io_obj in io_objs:
            self.add_parameter(io_obj=io_obj)

    def add_parameter(self, io_obj: io_obj_types_union):
        self.parameters.append(io_obj)

    def connect(self, io_obj: io_obj_types_union, io_obj_con: io_obj_types_union):
        """
        Connect io_obj to io_obj_con. This is important for later module instantiations.

        :param io_obj:
        :param io_obj_con:
        """

        # ToDo: Improve type checkers to prevent multiple drivers.
        # Allow connections only of both signals are of type AnalogSignal, or both are of type DigitalSignal,
        # or signal is of type DigitalSignal and connecting signal is of type AnalogCtrlOutput/AnalogCtrlOutput; this is needed for
        # streaming Analog signals, or strings to account for constant values
        if (isinstance(io_obj, AnalogSignal) and isinstance(io_obj_con, AnalogSignal)) or \
                (isinstance(io_obj, DigitalSignal) and isinstance(io_obj_con, DigitalSignal)) or \
                (isinstance(io_obj, DigitalSignal) and isinstance(io_obj_con, (AnalogCtrlInput, AnalogCtrlOutput, AnalogProbe))) or \
                (isinstance(io_obj_con, str)):
            self.connections.append([io_obj, io_obj_con])
        else:
            raise Exception(f"IO types of objects to be connected do not match:"
                            f"io_obj: {type(io_obj)}, io_obj_con: {type(io_obj_con)}")

    def generate_header(self):
        """
        Generate full module header.
        """

        ### Check if module includes analog ports or parameters
        analog_ports = self.analog_inputs + self.analog_outputs

        if (analog_ports or self.parameters):
            self.api.writeln(f"module {self.name} #(")
            self.api.indent()
            ## Add parameter section
            if analog_ports:
                for analog_port in analog_ports[:-1]:
                    self.api.writeln(self.api.decl_analog_port(analog_port) + ",")
                self.api.writeln(self.api.decl_analog_port(analog_ports[-1]) + ("," if self.parameters else ""))
            if self.parameters:
                for parameter in self.parameters[:-1]:
                    self.api.writeln(self.api.gen_parameter(param_obj=parameter) + ",")
                self.api.writeln(self.api.gen_parameter(param_obj=self.parameters[-1]))
            self.api.dedent()
            self.api.writeln(f") (")
        else:
            self.api.writeln(f"module {self.name} (")

        #### Add port section
        inputs = self.analog_inputs + self.digital_inputs
        outputs = self.analog_outputs + self.digital_outputs

        self.api.indent()
        if inputs:
            for input in inputs[:-1]:
                self.api.writeln(line=self.api.gen_port(io_obj=input, direction=PortDir.IN) + ",")
            self.api.writeln(self.api.gen_port(io_obj=inputs[-1], direction=PortDir.IN) + ("," if outputs else ""))
        if outputs:
            for output in outputs[:-1]:
                self.api.writeln(self.api.gen_port(io_obj=output, direction=PortDir.OUT) + ",")
            self.api.writeln(self.api.gen_port(io_obj=outputs[-1], direction=PortDir.OUT))

        self.api.dedent()
        self.api.writeln(f");")

    def generate_instantiation(self):
        """
        Generate instantiation for module.
        """

        ## Add parameter section
        analog_connections = []
        for connection in self.connections:
            # Remove analog control signals as for those signals no parameters will be transmitted
            if isinstance(connection[0], AnalogSignal):
                analog_connections.append(connection)

        if (analog_connections or self.parameters):
            self.api.indent()
            self.api.writeln(f"{self.name} #(")

            self.api.indent()
            if analog_connections:
                for analog_connection in analog_connections[:-1]:
                    self.api.writeln(self.api.pass_analog_port_format(io_obj=analog_connection[0], io_obj_format=analog_connection[1]) + ",")
                self.api.writeln(self.api.pass_analog_port_format(io_obj=analog_connections[-1][0], io_obj_format=analog_connections[-1][1]) + ("," if self.parameters else ""))

            if self.parameters:
                for parameter in self.parameters[:-1]:
                    self.api.writeln(self.api.gen_parameter(param_obj=parameter) + ",")
                self.api.writeln(self.api.gen_parameter(param_obj=self.parameters[-1]))

            self.api.dedent()
            self.api.writeln(f") {self.inst_name} (")
        else:
            self.api.indent()
            self.api.writeln(f"{self.name} {self.inst_name} (")

        ## Add port section
        self.api.indent()
        if self.connections:
            for connection in self.connections[:-1]:
                self.api.writeln(self.api.gen_connection(connection) + ",")
            self.api.writeln(self.api.gen_connection(self.connections[-1]))

        self.api.dedent()
        self.api.writeln(f");")