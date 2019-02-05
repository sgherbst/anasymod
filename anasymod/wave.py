import numpy as np

from anasymod.probe_config import ProbeConfig
from anasymod.config import EmuConfig
from vcd import VCDWriter

class ConvertWaveform():
    def __init__(self, cfg: EmuConfig):

        signal_lookup = {}
        with open(cfg.csv_path, 'r') as f:
            first_line = f.readline()
            # split up the first line into comma-delimeted names
            signals = first_line.split(',')
            # account for whitespace
            signals = [signal.strip() for signal in signals]
            # strip off the signal indices
            for k, signal in enumerate(signals):
                if '[' in signal:
                    signal = signal[:signal.index('[')]
                signal_lookup[signal] = k
        # TODO: make formatting less fragile
        print(f"Keys:{signal_lookup.keys()}")

        signals = ProbeConfig(probe_cfg_path=cfg.vivado_config.probe_cfg_path)

        # Scale analog signals using the exponent
        probe_data = {}
        for name, _, exponent in signals.analog_signals:
            unscaled_data = np.genfromtxt(cfg.csv_path, delimiter=',', usecols=signal_lookup[name], skip_header=1)
            scaled_data = (2 ** int(exponent)) * unscaled_data
            probe_data[name] = scaled_data

        # Add reset signal to probe_data
        for name, _, _ in signals.reset_signal:
            unscaled_data = np.genfromtxt(cfg.csv_path, delimiter=',', usecols=signal_lookup[name], skip_header=1)
            probe_data[name] = unscaled_data

        # Add digital signals to probe_data
        for name, _, _ in signals.digital_signals:
            try:
                unscaled_data = np.genfromtxt(cfg.csv_path, delimiter=',', usecols=signal_lookup[name], skip_header=1)
                probe_data[name] = unscaled_data
            except:
                pass

        # Scale time signal using exponent
        name, _, exponent = signals.time_signal[0]
        unscaled_data = np.genfromtxt(cfg.csv_path, delimiter=',', usecols=signal_lookup[name], skip_header=1)
        scaled_data = (2 ** int(exponent)) * unscaled_data
        time_signal = scaled_data

        # write data to VCD file
        with open(cfg.vcd_path, "w")as vcd:
            with VCDWriter(vcd, timescale='1 ns', date='today') as writer:
                # for signal_full_name, scaled_data in probe_data.items():
                #     signal_split = signal_full_name.split('/')
                #     reg = writer.register_var('.'.join(signal_split[:-1]), signal_split[-1], 'real')
                #     print(reg)
                #     for timestamp, value in zip(time_signal, scaled_data):
                #         #print(timestamp)
                #         #print(value)
                #         if timestamp >= 0:
                #             writer.change(reg, 1e9 * timestamp, value)
                #         else:
                #             break

                reg = {}
                for signal_full_name, scaled_data in probe_data.items():
                    signal_split = signal_full_name.split('/')
                    reg[signal_full_name] = writer.register_var('.'.join(signal_split[:-1]), signal_split[-1], 'real')

                for k, timestamp in enumerate(time_signal):
                    if timestamp >= 0:
                        for signal_full_name, scaled_data in probe_data.items():
                            writer.change(reg[signal_full_name], 1e9 * timestamp, scaled_data[k])
                    else:
                        break