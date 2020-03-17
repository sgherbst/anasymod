import numpy as np

try:
    from vcd import VCDWriter
except:
    print('ERROR: Could not load pyvcd package!')

import datetime
from anasymod.utils.VCD_parser import ParseVCD
from anasymod.enums import ResultFileTypes

class ConvertWaveform():
    def __init__(self, str_cfg, result_type_raw, result_path_raw, result_path, float_type=True, emu_time_scaled=True):
        # defaults
        self.result_path_raw = result_path_raw
        scfg = str_cfg
        self.signal_lookup = {}

        # store data from FPGA in a dictionary
        probe_data = {}
        real_signals = set()
        reg_widths = {}

        if result_type_raw == ResultFileTypes.CSV:
            # read CSV file
            with open(self.result_path_raw, 'r') as f:
                first_line = f.readline()

            # split up the first line into comma-delimited names
            signals = first_line.split(',')

            # account for whitespace
            signals = [signal.strip() for signal in signals]

            # strip off the signal indices and add to a lookup table
            for k, signal in enumerate(signals):
                if '[' in signal:
                    signal = signal[:signal.index('[')]
                self.signal_lookup[signal] = k

            # print keys
            print(f'Signals in result file: {[key for key in self.signal_lookup.keys()]}')

            for analog_signal in scfg.analog_probes + [scfg.time_probe]:
                name = 'trace_port_gen_i/' + analog_signal.name
                if (name) in self.signal_lookup:
                    # add to set of probes with "real" data type
                    real_signals.add(name)

                    # get unscaled data and apply scaling factor
                    probe_data[name] = (2 ** int(analog_signal.exponent)) * self.get_csv_col(name)

                    # convert data to native Python float type (rather than numpy float) this is required for PyVCD
                    probe_data[name] = [float(x) for x in probe_data[name]]

            for digital_signal in scfg.digital_probes + [scfg.dec_cmp]:
                name = 'trace_port_gen_i/' + digital_signal.name
                if name in self.signal_lookup:
                    # define width for this probe
                    reg_widths[name] = int(digital_signal.width)

                    # get unscaled data
                    probe_data[name] = self.get_csv_col(name)

                    # convert data to native Python int type (rather than numpy int) this is required for PyVCD
                    probe_data[name] = [int(x) for x in probe_data[name]]

            # Write data to VCD file
            with open(result_path, 'w') as vcd:
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
                        reg[signal_full_name] = writer.register_var(scope=vcd_scope, name=vcd_name,
                                                                    var_type=vcd_var_type,
                                                                    size=vcd_size)

                    # iterate over all timesteps
                    for k, timestamp in enumerate(probe_data['trace_port_gen_i/' + scfg.time_probe.name]):
                        # break if timestamp is less than zero since it means that wrapping has occurred
                        if timestamp < 0:
                            break

                        # iterate over all signals and log their change at this timestamp
                        for signal_full_name, scaled_data in probe_data.items():
                            writer.change(reg[signal_full_name], round(1e9 * timestamp), scaled_data[k])

        elif result_type_raw == ResultFileTypes.VCD:
            vcd_file_name = result_path_raw
            vcd_handle = ParseVCD(vcd_file_name)
            signal_dict = vcd_handle.parse_vcd(update_data=False)

            # print signal names
            signal_names = [(signal_dict[key]["nets"][0]["name"], key) for key in signal_dict.keys()]
            print(f'Signals in result file: {[sig_name[0] for sig_name in signal_names]}')

            for analog_signal in scfg.analog_probes + [scfg.time_probe]:
                if analog_signal.name in [sig[0] for sig in signal_names]:
                    # add to set of probes with "real" data type
                    real_signals.add(analog_signal.name)

                    probe_data[analog_signal.name] = {}
                    probe_data[analog_signal.name]['index'] = 0

                    # get the signal identifier from analog_signal used in VCD file
                    signal_identifier = signal_names[[y[0] for y in signal_names].index(analog_signal.name)][1]
                    data = []
                    for c,v in signal_dict[signal_identifier]['cv']:
                        if not isinstance(v, float):
                            for k in range(analog_signal.width - len(v)): # extend binary to full width, some simulators don't do that by default and remove leading zeros in VCD file
                                v = '0' + v
                            if v[0] == '1': # check if number is negative and if so calculate the two's complement
                                v = -1 * (int((''.join('1' if x == '0' else '0' for x in v)), 2) + 1)
                            else:
                                v = int(v, 2)
                        if not float_type:
                            v = 2 ** int(analog_signal.exponent) * v
                        data.append((c, v))
                    probe_data[analog_signal.name]['data'] = np.asarray(data)

                    # convert data to native Python float type (rather than numpy float) this is required for PyVCD
                    probe_data[analog_signal.name]['data'] = [(int(c), float(v)) for c, v in probe_data[analog_signal.name]['data']]

            for digital_signal in scfg.digital_probes + [scfg.dec_cmp]:
                if digital_signal.name in [sig[0] for sig in signal_names]:
                    # define width for this probe
                    reg_widths[digital_signal.name] = int(digital_signal.width)

                    probe_data[digital_signal.name] = {}
                    probe_data[digital_signal.name]['index'] = 0

                    # get unscaled data
                    probe_data[digital_signal.name]['data'] = np.asarray([(c, v) for c,v in signal_dict[signal_names[[y[0] for y in signal_names].index(digital_signal.name)][1]]['cv']])

                    # convert data to native Python int type (rather than numpy int) this is required for PyVCD
                    data = []
                    for c, v in probe_data[digital_signal.name]['data']:
                        try:
                            data.append((int(c), int(v, 2)))
                        except: # In case of an x or z value, a 0 will be added; this is necessary for PYVCD
                            data.append((int(c), int(0)))

                    probe_data[digital_signal.name]['data'] = data

            # Write data to VCD file
            with open(result_path, 'w') as vcd:
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
                        reg[signal_full_name] = writer.register_var(scope=vcd_scope, name=vcd_name,
                                                                    var_type=vcd_var_type,
                                                                    size=vcd_size)

                    # iterate over all timesteps
                    for idx, (cycle_count, timestamp) in enumerate(probe_data[scfg.time_probe.name]['data']):
                        # break if timestamp is less than zero since it means that wrapping has occurred
                        if timestamp < 0:
                            break

                        # iterate over all signals and log their change at this timestamp
                        for signal_full_name in probe_data.keys():
                            current_signal = probe_data[signal_full_name]['data'][probe_data[signal_full_name]['index']]
                            # Check if registered signals shall be associated with timestamp of emu_time signal
                            if emu_time_scaled:
                                # Check if a value change has occured at this timestep
                                if cycle_count == current_signal[0]:
                                    print(f"{signal_full_name}:{round(1e9 * timestamp)}:{current_signal[1]}")
                                    writer.change(reg[signal_full_name], round(1e9 * timestamp), current_signal[1])
                                elif round(probe_data[scfg.time_probe.name]['data'][idx + 1][0] - 25000) > current_signal[0]:
                                    # Note: There is always a difference of 25000 between a data signal and a timestep event -> substract 25000
                                    # The cycle count from data signal does not have a match with emu_time signal's cycle count
                                    # -> we need to apply interpolation in order to assign the timestamp properly
                                    print(f"needer to interp: {signal_full_name}: {round(probe_data[scfg.time_probe.name]['data'][idx+1][1] * 1e12)}")
                                    cycles_in_dt = probe_data[scfg.time_probe.name]['data'][idx+1][0] - cycle_count
                                    dt = probe_data[scfg.time_probe.name]['data'][idx+1][1] - timestamp
                                    interp_timestamp = dt/cycles_in_dt * (current_signal[0] - cycle_count + 25000) + timestamp
                                    writer.change(reg[signal_full_name], round(1e9 * interp_timestamp), current_signal[1])
                                else:
                                    continue
                            else: # Registered signal are associated with original cycle count
                                writer.change(reg[signal_full_name], current_signal[0], current_signal[1])
                            probe_data[signal_full_name]['index'] += 1
        else:
            raise Exception(f'ERROR: No supported Result file format selected:{result_type_raw}')



    def get_csv_col(self, name):
        """
        Getting unscaled data from csv file column
        :return:
        """
        return np.genfromtxt(self.result_path_raw, delimiter=',', usecols=self.signal_lookup[name], skip_header=1)