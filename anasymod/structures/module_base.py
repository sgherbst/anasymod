class ModuleBase():
    """
    This is the base class for module structure generation.
    """
    def __init__(self):

        # Stores all modules that need to be instantiated in this module
        self.child_modules =[]

        # Stores all io ports of module
        self.ports = []

        # Template for custom body
        self.template = ''

        #

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