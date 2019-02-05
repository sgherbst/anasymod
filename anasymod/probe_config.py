class ProbeConfig:
    def __init__(self, probe_cfg_path):
        # Read Probe Config file
        with (open(probe_cfg_path, "r")) as cf:
            config = cf.readlines()

        prefixes = [r"ANALOG:", r"ANALOG_EXPONENT:", r"ANALOG_WIDTH:", r"TIME:", r"TIME_EXPONENT:", r"TIME_WIDTH:", r"RESET:", r"SB:", r"MB:", r"MB_WIDTH:"]
        # clean and remove prefixes
        signals = []
        for signal, prefix in zip(config, prefixes):
            signals.append(signal.strip(prefix).strip().split())

        self.analog_signals = []
        for name, width, exponent in zip(signals[0], signals[2], signals[1]):
            self.analog_signals.append((name, width, exponent))

        self.time_signal = []
        for name,width, exponent in zip(signals[3], signals[5], signals[4]):
            self.time_signal.append((name, width, exponent))

        self.reset_signal = []
        for name,width, exponent in zip(signals[6], [r"1"], [None]):
            self.reset_signal.append((name, width, exponent))

        self.digital_signals = []
        for name in signals[7]:
            self.digital_signals.append((name, r"1", None))

        for name, width in zip(signals[8], signals[9]):
            self.digital_signals.append((name, width, None))

