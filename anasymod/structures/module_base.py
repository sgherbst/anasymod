class ModuleBase():
    """
    This is the base class for module structure generation.
    """
    def gen_module(self):
        """
        Generates sv code for module body.
        :return: Generated code of module body.
        """
        pass

    def gen_instantiation(self):
        """
        Generates sv code for module instantiation.
        :return: Generated code of module instantiation.
        """
        pass

    #note: it shall be possible to cluster ports -> all analog clks, all dig clks, all ctrl signals