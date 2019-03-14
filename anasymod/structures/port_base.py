from anasymod.structures.signal_base import SignalBase

class PortBase():
    """
    This is the base class for port generation.
    """
    def __init__(self, name, num_bits):
        self.name = name
        self.num_bits = num_bits
        self.connection = None

    def dump(self):
        """
        Dump string for module instantiation.

        :return: Module instantiation string for Port
        """
        raise NotImplementedError()

    def connect(self, signal: SignalBase):
        """
        Connects a signal to the port.
        """
        self.connection = signal.name

class PortIN(PortBase):
    def __init__(self, name, num_bits=1):
        super().__init__(name=name, num_bits=num_bits)

    def dump(self):
        """
        Dump string for module instantiation.

        :return: Module instantiation string for Port
        """
        return f"input wire logic {self.name}"

class PortOUT(PortBase):
    def __init__(self, name, num_bits=1, init=None):
        super().__init__(name=name, num_bits=num_bits)
        self.init = init

    def dump(self):
        """
        Dump string for module instantiation.

        :return: Module instantiation string for Port
        """
        return f"output wire logic {self.name}"
