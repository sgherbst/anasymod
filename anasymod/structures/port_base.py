from anasymod.structures.signal_base import Signal
from anasymod.enums import PortDir

class Port():
    """
    This is the base class for port generation.
    """
    def __init__(self, name, width, direction=None, **kwargs):
        self.name = name
        self.width = width
        self.connection = None
        self.direction = direction
        self.__init_value = kwargs['init_value'] if 'init_value' in kwargs else None

    @property
    def init_value(self):
        if self.direction == PortDir.OUT:
            return self.__init_value

    def connect(self, signal: Signal):
        """
        Connects a signal to the port.
        """
        self.connection = signal.name

class PortIN(Port):
    def __init__(self, name, width=1):
        super().__init__(name=name, width=width, direction=PortDir.IN)

class PortOUT(Port):
    def __init__(self, name, width=1, direction=PortDir.OUT, init_value=None):
        super().__init__(name=name, width=width)