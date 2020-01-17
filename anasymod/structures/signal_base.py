class Signal():
    def __init__(self, abs_path: str, delimiter='.'):
        """
        Class for storing signal information, that will be later used to generate HDL code related to signals.
        :param abs_path:    Absolute path to the defined signal, this can also only be the name itself, in case it will
                            not be used for a connection via abs path later
        :param delimiter:   Delimiter to separate the signal's abs path
        """
        self.delimiter = delimiter
        # Separate the signal's abs path
        signal_hier = abs_path.split(self.delimiter)

        # Check if an abs path was actually provided or only the signal name
        if len(signal_hier) == 1:
            # Only signal name was given
            self.name = ''.join(signal_hier)
            self.abs_path = None
        elif len(signal_hier) > 1:
            # Abs path to signal was provided
            self.name = signal_hier[-1]
            self.abs_path = abs_path