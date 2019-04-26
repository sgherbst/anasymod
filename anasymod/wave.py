import numpy as np

try:
    from vcd import VCDWriter
except:
    print('ERROR: Could not load pyvcd package!')

import datetime

from anasymod.probe_config import ProbeConfig
from anasymod.targets import FPGATarget

class ConvertWaveform():
    def __init__(self, target: FPGATarget):

        # read CSV file
        with open(target.cfg.csv_path, 'r') as f:
            first_line = f.readline()

        # split up the first line into comma-delimited names
        signals = first_line.split(',')

        # account for whitespace
        signals = [signal.strip() for signal in signals]

        # strip off the signal indices and add to a lookup table
        signal_lookup = {}
        for k, signal in enumerate(signals):
            if '[' in signal:
                signal = signal[:signal.index('[')]
            signal_lookup[signal] = k

        # print keys
        print(f'CSV column names: {[key for key in signal_lookup.keys()]}')

        # define method for getting unscaled data
        def get_csv_col(name):
            return np.genfromtxt(target.cfg.csv_path, delimiter=',', usecols=signal_lookup[name], skip_header=1)

        # read probe signal information to find out what signals are analog, digital, reset, time, etc.
        signals = ProbeConfig(probe_cfg_path=target.probe_cfg_path)

        # store data from FPGA in a dictionary
        probe_data = {}
        real_signals = set()
        reg_widths = {}

        # Add analog signals to probe_data
        for name, _, exponent in signals.analog_signals + signals.time_signal:
            if name not in signal_lookup:
                continue

            # add to set of probes with "real" data type
            real_signals.add(name)

            # get unscaled data and apply scaling factor
            probe_data[name] = (2**int(exponent)) * get_csv_col(name)

            # convert data to native Python float type (rather than numpy float)
            # this is required for PyVCD
            probe_data[name] = [float(x) for x in probe_data[name]]

        # Add digital signals to probe_data
        for name, width, _ in signals.digital_signals + signals.reset_signal:
            if name not in signal_lookup:
                continue

            # define width for this probe
            reg_widths[name] = int(width)

            # get unscaled data
            probe_data[name] = get_csv_col(name)

            # convert data to native Python float type (rather than numpy int)
            # this is required for PyVCD
            probe_data[name] = [int(x) for x in probe_data[name]]

        # Extract the time signal from the probe data since it is needed to produce a VCD file
        time_signal_name, _, _ = signals.time_signal[0]
        time_signal = probe_data[time_signal_name]

        # Write data to VCD file
        with open(target.cfg.vcd_path, 'w') as vcd:
            with VCDWriter(vcd, timescale='1 ns', date=str(datetime.datetime.today())) as writer:
                # register all of the signals that will be written to VCD
                reg = {}
                for signal_full_name, scaled_data in probe_data.items():
                    # determine signal scope and name
                    signal_split = signal_full_name.split('/')
                    vcd_scope = '.'.join(signal_split[:-1])
                    vcd_name = signal_split[-1]

                    # determine signal type and size
                    if signal_full_name in real_signals:
                        vcd_var_type = 'real'
                        vcd_size = None
                    elif signal_full_name in reg_widths:
                        vcd_var_type = 'reg'
                        vcd_size = reg_widths[signal_full_name]
                    else:
                        raise Exception('Unknown signal type.')

                    # register the signal
                    reg[signal_full_name] = writer.register_var(scope=vcd_scope, name=vcd_name, var_type=vcd_var_type,
                                                                size=vcd_size)

                # iterate over all timesteps
                for k, timestamp in enumerate(time_signal):
                    # break if timestamp is less than zero since it means that wrapping has occurred
                    if timestamp < 0:
                        break

                    # iterate over all signals and log their change at this timestamp
                    for signal_full_name, scaled_data in probe_data.items():
                        writer.change(reg[signal_full_name], round(1e9 * timestamp), scaled_data[k])