class Define():
    def __init__(self, name, value=None, fileset=r"default"):
        self.name = name
        """ type(str) : mandatory setting; name of define. """

        self.value = value
        """ type(str) : value of define. """

        self.define = {self.name: self.value}

        self.fileset = fileset
        """ type(str) : Fileset, the source shall be associsted with. """