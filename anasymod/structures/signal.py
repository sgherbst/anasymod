class Signal():
    def __init__(self, name):
        self.name = name

    def input(self):
        return f"input wire logic {self.name}"

    def output(self):
        return f"output wire logic {self.name}"