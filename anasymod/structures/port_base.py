from anasymod.enums import PortDirections
from anasymod.structures.signal_base import SignalBase

class PortBase():
    """
    This is the base class for port generation.
    """
    def __init__(self, name, direction, num_bits=1):
        self.name = name

        if direction.upper() in PortDirections.__dict__.keys():
            self.direction = direction
        else:
            raise ValueError(f"No vaild port direction specified for port{self.name}: {direction}")

        self.num_bits = num_bits
        self.connection = None

    def render_mod_port(self):
        if self.direction.lower() == 'in':
            return f"input wire logic {self.name}"
        elif self.direction.lower() == 'out':
            return f"output wire logic {self.name}"
        else:
            raise ValueError(f"No vaild port direction ")

    def connect(self, signal: SignalBase):
        """
        Connects a signal to the port.
        """

        self.connection = signal.name