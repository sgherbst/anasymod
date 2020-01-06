from math import ceil, log2

class _Signal():
    """
    Container for signals that can be used to describe connectivity within the design.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Port name
    """

    def __init__(self, abspath, name, delimiter):
        self.delimiter = delimiter

        self.name = name
        self.abs_path = abspath

### Digital Signal Classes

class DigitalSignal(_Signal):
    """
    Container for digital signals that can be used to describe connectivity within the design.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Port name
    :param width:       Number of bits
    _param signed:      If true, signal is of type signed
    """

    def __init__(self, abspath, name, width, delimiter='.', signed=False):
        super().__init__(abspath=abspath, name=name, delimiter=delimiter)
        self.width = width
        self.signed = signed

class DigitalCtrlInput(DigitalSignal):
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
        super().__init__(abspath=abspath, name=name, width=width, delimiter=delimiter)
        self.i_addr = None
        self.init_value = init_value

class DigitalCtrlOutput(DigitalSignal):
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
        super().__init__(abspath=abspath, name=name, width=width, delimiter=delimiter)
        self.o_addr = None

### Analog Signal Classes

class AnalogSignal(_Signal):
    """
    Container for analog signals that can be used to describe connectivity within the design.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Port name
    :param range:       Range for analog fixed-point datatype
    """

    def __init__(self, abspath, name, range, delimiter='.'):
        super().__init__(abspath=abspath, name=name, delimiter=delimiter)
        self.range = range

class AnalogCtrlInput(AnalogSignal):
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
        super().__init__(abspath=abspath, name=name, range=range, delimiter=delimiter)
        self.i_addr = None
        self.init_value = init_value

class AnalogCtrlOutput(AnalogSignal):
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
        super().__init__(abspath=abspath, name=name, range=range, delimiter=delimiter)
        self.o_addr = None

class AnalogProbe(AnalogSignal):
    """
    Container for an analog probe signals. Opposed to an AnalogSignal class instantiation, this one also provides
    information about width and exponent.
    :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                        not be used for a connection via abs path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Parameter name
    :param o_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    :param range:       Range for analog fixed-point datatype
    :param width:       Number of bits, NOTE: This should be similar to default in SVREAL (LONG_WIDTH_REAL=25)
    """

    def __init__(self, abspath, name, range, width=25, delimiter='.'):
        super().__init__(abspath=abspath, name=name, delimiter=delimiter, range=range)

        # As of now, the number of bits for each analog signal shall not be changed without also changing the corresponding
        # value in SVREAL (LONG_WIDTH_REAL=25); in future, it shall be possible to change width for each signal
        self.width = width
        self.exponent = ceil(log2((self.range) / (2 ** (self.width - 1) - 1)))






class ProbeSignal():
    """
    Temporary container to store all the information necessary for generating ila probe signals.
    """

    def __init__(self, name, abspath, width, exponent, type):
        self.name = name
        self.abspath = abspath
        self.width = width
        self.exponent = exponent
        self.type = type