class Define():
    def __init__(self, name, value=None, fileset=r"default"):
        self.define = {name: value}
        self.fileset = fileset