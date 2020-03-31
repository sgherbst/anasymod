from math import ceil, log2


class _Signal():
    """
    Container for signals that can be used to describe connectivity within the design.
    :param abs_path:    Absolute path to the defined signal, this can also only be the
                        name itself, in case it will not be used for a connection via
                        an absolute path later
    :param delimiter:   Delimiter to separate the signal's abs path
    :param name:        Port name
    """

    def __init__(self, abspath, name, delimiter='.'):
        self.delimiter = delimiter
        self.name = name
        self.abs_path = abspath

    @classmethod
    def from_dict(cls, name, dict):
        return cls(name=name, **dict)

# Digital Signal Classes


class DigitalSignal(_Signal):
    """
    Container for digital signals that can be used to describe connectivity within the design.
    Same instantiation arguments as _Signal, plus:
    :param width:       Number of bits
    _param signed:      If true, signal is of type signed
    """

    def __init__(self, *args, width=1, signed=False, **kwargs):
        # call the super constructor
        super().__init__(*args, **kwargs)
        # save settings
        self.width = width
        self.signed = signed


class DigitalCtrlInput(DigitalSignal):
    """
    Container for a digital control input to the simulation.
    Same instantiation arguments as DigitalSignal, plus:
    :param i_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    :param init_value:  Initial value that will be transmitted via this input
    """

    def __init__(self, *args, init_value=0, i_addr=None, **kwargs):
        # call the super constructor
        super().__init__(*args, **kwargs)
        # save settings
        self.i_addr = i_addr
        self.init_value = init_value


class DigitalCtrlOutput(DigitalSignal):
    """
    Container for a digital control output to the simulation.
    Same instantiation arguments as DigitalSignal, plus:
    :param o_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    """

    def __init__(self, *args, o_addr=None, **kwargs):
        # call the super constructor
        super().__init__(*args, **kwargs)
        # save settings
        self.o_addr = o_addr


# Analog Signal Classes


class AnalogSignal(_Signal):
    """
    Container for analog signals that can be used to describe connectivity within the design.
    Same instantiation arguments as _Signal, plus
    :param range:       Range for analog fixed-point datatype
    :param width:       Width for analog fixed-point datatype
    :param exponent:    Exponent for analog fixed-point datatype
    """

    def __init__(self, *args, range=None, width=25, exponent=None, **kwargs):
        # call the super constructor
        super().__init__(*args, **kwargs)

        # Set defaults for fixed-point formatting in case only two of the
        # three arguments have been specified.  Note that in order to cause
        # the width to be inferred, a user must explicity set width=None,
        # since the default value is "25"
        if (width is None) and ((range is not None) and (exponent is not None)):
            width = self.calc_width(range=range, exponent=exponent)
        elif (exponent is None) and ((range is not None) and (width is not None)):
            exponent = self.calc_exponent(range=range, width=width)
        elif (range is None) and ((width is not None) and (exponent is not None)):
            range = self.calc_range(width=width, exponent=exponent)

        # make sure the width and exponent are defined
        # (range is not strictly needed to interpret fixed-point types)
        assert width is not None, 'Width is not defined.'
        assert exponent is not None, 'Exponent is not defined.'
        assert range is not None, 'Range is not defined.'

        # save settings
        self.width = width
        self.exponent = exponent
        self.range = range

    @staticmethod
    def calc_exponent(range, width):
        if range == 0:
            return 0
        else:
            return int(ceil(log2(range/(2**(width-1)-1))))

    @staticmethod
    def calc_width(range, exponent):
        if range == 0:
            return 1
        else:
            return int(ceil(1+log2((range/(2**exponent))+1)))

    @staticmethod
    def calc_range(width, exponent):
        # should be defined such that the following expressions are true
        # e == calc_exponent(calc_range(w, e), w)
        # w == calc_width(calc_range(w, e), e)
        return ((2**(width-1))-1)*(2**exponent)

    def float_to_fixed(self, val):
        return int(round(val*(2**(-self.exponent))))

    def fixed_to_float(self, val):
        return float(val*(2**(self.exponent)))


class AnalogCtrlInput(AnalogSignal):
    """
    Container for an analog control input to the simulation.
    Same instantiation arguments as AnalogSignal, plus
    :param i_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    :param init_value:  Initial value that will be transmitted via this input
    """

    def __init__(self, *args, init_value=0.0, i_addr=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.i_addr = i_addr
        self.init_value = init_value


class AnalogCtrlOutput(AnalogSignal):
    """
    Container for an analog control output to the simulation.
    Same instantiation arguments as AnalogSignal, plus
    :param o_addr:      Address, which the control interface uses to access the corresponding entry in reg map
    """

    def __init__(self, *args, o_addr=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.o_addr = o_addr


class AnalogProbe(AnalogSignal):
    """
    Container for an analog probe signals.
    Same instantiation arguments as AnalogSignal.
    """

    pass


class ProbeSignal():
    """
    Temporary container to store all the information necessary for generating ILA probe signals.
    """

    def __init__(self, name, abspath, width, exponent, type):
        self.name = name
        self.abspath = abspath
        self.width = width
        self.exponent = exponent
        self.type = type