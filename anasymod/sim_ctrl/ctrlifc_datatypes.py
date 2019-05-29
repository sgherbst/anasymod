class _CtrlIO():
    """
    Container for an IOs to the simulation, this could on the one hand be a control parameter, such as an input voltage,
    or a model parameter such as a capacitor or resistor value, or a probe, such a register value or an output signal.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Parameter name
    """

    def __init__(self, abspath, name, delimiter):
        self.delimiter = delimiter

        self.name = name
        self.abs_path = abspath

class _CtrlInput(_CtrlIO):
    """
    Container for an Input to the simulation, this could be a control parameters, such as an input voltage or a model
    parameter such as a capacitor or resistor value.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Parameter name
    :param i_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    :param init_value:  Initial value that will be transmitted via this input
    """

    def __init__(self, abspath, name, init_value, delimiter):
        super().__init__(abspath=abspath, name=name, delimiter=delimiter)
        self.i_addr = None
        self.init_value = init_value

class _CtrlOutput(_CtrlIO):
    """
    Container for an Output to the simulation, this could be a probe, such a register value or an output signal.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name         Parameter name
    :param o_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    """

    def __init__(self, abspath, name, delimiter):
        super().__init__(abspath=abspath, name=name, delimiter=delimiter)
        self.o_addr = None

class DigitalCtrlInput(_CtrlInput):
    """
    Container for a digital control input to the simulation.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Parameter name
    :param i_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    :param init_value:  Initial value that will be transmitted via this input
    :param width:       Number of bits
    """

    def __init__(self, abspath, name, width, init_value=0, delimiter='.'):
        super().__init__(abspath=abspath, name=name, init_value=init_value, delimiter=delimiter)
        self.width = width

class AnalogCtrlInput(_CtrlInput):
    """
    Container for an analog control input to the simulation.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Parameter name
    :param i_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    :param init_value:  Initial value that will be transmitted via this input
    :param range:       Range for analog fixed-point datatype
    """

    def __init__(self, abspath, name, range, init_value=0.0, delimiter='.'):
        super().__init__(abspath=abspath, name=name, init_value=init_value, delimiter=delimiter)
        self.range = range

class DigitalCtrlOutput(_CtrlOutput):
    """
    Container for a digital control output to the simulation.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Parameter name
    :param i_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    :param width:       Number of bits
    """

    def __init__(self, abspath, name, width, delimiter='.'):
        super().__init__(abspath=abspath, name=name, delimiter=delimiter)
        self.width = width


class AnalogCtrlOutput(_CtrlOutput):
    """
    Container for an analog control output to the simulation.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Parameter name
    :param o_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    :param range:       Range for analog fixed-point datatype
    """

    def __init__(self, abspath, name, range, delimiter='.'):
        super().__init__(abspath=abspath, name=name, delimiter=delimiter)
        self.range = range
