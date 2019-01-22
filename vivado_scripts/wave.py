
import numpy as np

import sys
from argparse import ArgumentParser
from vcd import VCDWriter

def main():
    parser = ArgumentParser()
    parser.add_argument('--csv', type=str, default='ila_values.csv', help='Path to the CSV file with waveforms')
    parser.add_argument('--probes', type=str, default='probes.txt', help='Path to file with probe information.')
    parser.add_argument('-o', '--output', type=str, default='example.vcd', help='Path where the VCD file will be written.')

    args = parser.parse_args()

    # build a lookup table that maps signals names to column numbers
    signal_lookup = {}
    with open(args.csv, 'r') as f:
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

    # build up a list of signals and exponents
    probe_signals = []
    with open(args.probes, 'r') as f:
        for line in f:
            contents = line.split(',')

            if len(contents) != 2:
                continue

            probe_signal = (contents[0].strip(), int(contents[1].strip()))
            probe_signals.append(probe_signal)

    # get the ILA data for each of the probed signals

    # probe_data = {probe_signal[0]: np.genfromtxt(args.probes, delimiter =',', usecols=signal_lookup[probe_signal[0]])
    #               for probe_signal in probe_signals}

    probe_data = {}
    for probe_signal in probe_signals:
        signal_name = probe_signal[0]
        signal_scale = 2**probe_signal[1]

        unscaled_data = np.genfromtxt(args.csv, delimiter =',', usecols=signal_lookup[signal_name])
        scaled_data = signal_scale*unscaled_data

        probe_data[signal_name] = scaled_data

    # write data to VCD file
    with open(args.output, "w")as vcd:
        with VCDWriter(vcd, timescale='1 ns', date='today') as writer:
            for signal_full_name, scaled_data in probe_data.items():
                signal_split = signal_full_name.split('/')
                reg = writer.register_var('.'.join(signal_split[:-1]), signal_split[-1], 'real')
                for timestamp, value in enumerate(scaled_data):
                    writer.change(reg, timestamp, value)

if __name__ == '__main__':
    main()


