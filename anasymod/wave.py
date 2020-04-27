import numpy as np

try:
    from si_prefix import si_format
except:
    print('ERROR: Could not load si-prefix package!')

try:
    from vcd import VCDWriter
except:
    print('ERROR: Could not load pyvcd package!')

import datetime

from anasymod.utils.VCD_parser import ParseVCD
from anasymod.enums import ResultFileTypes

class ConvertWaveform():
    """
    Convert raw result files to vcd and also make sure fixed-point datatypes are properly converted to a floating point
    representation. Currently supported raw result datatypes are vcd and csv.
    """
    def __init__(self, str_cfg, result_type_raw, result_path_raw, result_path, float_type=True, emu_time_scaled=True,
                 debug=False, dt_scale=1e-15):
        """

        :param str_cfg: structure config object used in current project.
        :param result_type_raw: filetype of result file to be converted
        :param result_path_raw: path to raw result file
        :param result_path: path to converted result file
        :param float_type: flag to indicate if real signal's data type is fixed-point or floating point
        :param emu_time_scaled: flag to indicate, if signals shall be displayed over cycle count or time
        :param debug: if debug flag is set to true, all signals from result file will be kept, even if they are not a
                        specified probe; keep in mind, that for those signals no fixed to float conversion can be done
        """

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

            for analog_signal in scfg.analog_probes:
                name = 'trace_port_gen_i/' + analog_signal.name
                if (name) in self.signal_lookup:
                    # add to set of probes with "real" data type
                    real_signals.add(name)

                    # get unscaled data and apply scaling factor
                    probe_data[name] = (2 ** int(analog_signal.exponent)) * self.get_csv_col(name)

                    # convert data to native Python float type (rather than numpy float)
                    # this is required for PyVCD
                    probe_data[name] = [float(x) for x in probe_data[name]]

            for digital_signal in scfg.digital_probes + [scfg.dec_cmp] + [scfg.time_probe]:
                name = 'trace_port_gen_i/' + digital_signal.name
                if name in self.signal_lookup:
                    # define width for this probe
                    reg_widths[name] = int(digital_signal.width)

                    # get unscaled data
                    probe_data[name] = self.get_csv_col(name)

                    # convert data to native Python int type (rather than numpy int)
                    # this is required for PyVCD
                    try:
                        probe_data[name] = [int(x) for x in probe_data[name]]
                    except ValueError:
                        print(f'ValueError encountered when converting probe_data[{name}].')
                        print(f'Contents of probe_data[{name}]:')
                        print(f'{probe_data}')
                        print(f'Contents of CSV file {self.result_path_raw}:')
                        print(open(self.result_path_raw, 'r').read())
                        raise

            # Write data to VCD file
            with open(result_path, 'w') as vcd:
                timescale = self.get_pyvcd_timescale(dt_scale)
                with VCDWriter(vcd, timescale=timescale, date=str(datetime.datetime.today())) as writer:
                    # register all of the signals that will be written to VCD
                    reg = {}
                    for sig, scaled_data in probe_data.items():
                        # determine signal scope and name
                        signal_split = sig.split('/')
                        vcd_scope = '.'.join(signal_split[:-1])
                        vcd_name = signal_split[-1]

                        # determine signal type and size
                        if sig in real_signals:
                            vcd_var_type = 'real'
                            vcd_size = None
                        elif sig in reg_widths:
                            vcd_var_type = 'reg'
                            vcd_size = reg_widths[sig]
                        else:
                            raise Exception('Unknown signal type.')

                        # register the signal
                        reg[sig] = writer.register_var(scope=vcd_scope, name=vcd_name,
                                                                    var_type=vcd_var_type,
                                                                    size=vcd_size)

                    # iterate over all timesteps
                    prev_timestep = float('-inf')
                    for k, timestamp in enumerate(probe_data['trace_port_gen_i/' + scfg.time_probe.name]):
                        # break if the current timestep is less than the previous one, since that means
                        # wrapping has occurred
                        if timestamp < prev_timestep:
                            break
                        prev_timestep = timestamp

                        # iterate over all signals and log their change at this timestamp
                        for sig, scaled_data in probe_data.items():
                            writer.change(reg[sig], timestamp, scaled_data[k])

        elif result_type_raw == ResultFileTypes.VCD:
            vcd_file_name = result_path_raw
            vcd_handle = ParseVCD(vcd_file_name)
            signal_dict = vcd_handle.parse_vcd(update_data=False)

            # print signal names
            signal_names = [(signal_dict[key]["nets"][0]["hier"] + '.' + signal_dict[key]["nets"][0]["name"], key) for key in signal_dict.keys()]
            print(f'Signals in result file: {[sig_name[0] for sig_name in signal_names]}')

            for analog_signal in scfg.analog_probes:
                analog_signal_path = 'top.trace_port_gen_i' + '.' + analog_signal.name
                if analog_signal_path in [sig[0] for sig in signal_names]:
                    # add to set of probes with "real" data type
                    real_signals.add(analog_signal_path)

                    probe_data[analog_signal_path] = {}
                    probe_data[analog_signal_path]['index'] = 0

                    # get the signal identifier from analog_signal used in VCD file
                    signal_identifier = signal_names[[y[0] for y in signal_names].index(analog_signal_path)][1]
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
                    probe_data[analog_signal_path]['data'] = np.asarray(data)

                    # convert data to native Python float type (rather than numpy float) this is required for PyVCD
                    probe_data[analog_signal_path]['data'] = [(int(c), float(v)) for c, v in probe_data[analog_signal_path]['data']]

            for digital_signal in scfg.digital_probes + [scfg.dec_cmp] + [scfg.time_probe]:
                digital_signal_path = 'top.trace_port_gen_i' + '.' + digital_signal.name
                if digital_signal_path in [sig[0] for sig in signal_names]:
                    # define width for this probe
                    reg_widths[digital_signal_path] = int(digital_signal.width)

                    probe_data[digital_signal_path] = {}
                    probe_data[digital_signal_path]['index'] = 0

                    # get unscaled data
                    probe_data[digital_signal_path]['data'] = np.asarray([(c, v) for c,v in signal_dict[signal_names[[y[0] for y in signal_names].index(digital_signal_path)][1]]['cv']])

                    # convert data to native Python int type (rather than numpy int) this is required for PyVCD
                    data = []
                    for c, v in probe_data[digital_signal_path]['data']:
                        try:
                            data.append((int(c), int(v, 2)))
                        except: # In case of an x or z value, a 0 will be added; this is necessary for PYVCD
                            data.append((int(c), int(0)))

                    probe_data[digital_signal_path]['data'] = data

            # Write data to VCD file

            with open(result_path, 'w') as vcd:
                timescale = self.get_pyvcd_timescale(dt_scale)
                with VCDWriter(vcd, timescale=timescale, date=str(datetime.datetime.today())) as writer:
                    # register all of the signals that will be written to VCD
                    reg = {}
                    for sig, scaled_data in probe_data.items():
                        # determine signal scope and name
                        signal_split = sig.split('.')
                        vcd_scope = '.'.join(signal_split[:-1])
                        vcd_name = signal_split[-1]

                        # determine signal type and size
                        if sig in real_signals:
                            vcd_var_type = 'real'
                            vcd_size = None
                        elif sig in reg_widths:
                            vcd_var_type = 'reg'
                            vcd_size = reg_widths[sig]
                        else:
                            raise Exception('Unknown signal type.')

                        # register the signal
                        reg[sig] = writer.register_var(scope=vcd_scope, name=vcd_name,
                                                                    var_type=vcd_var_type,
                                                                    size=vcd_size)

                    prev_timestep = float('-inf')
                    # Add all other signals in case debug flag is set
                    if debug:
                        for signal in signal_names:
                            if not signal[0] in probe_data.keys(): # signal was not listed yet
                                var_type = signal_dict[signal[1]]['nets'][0]['type']
                                if var_type != 'parameter':
                                    name = signal_dict[signal[1]]['nets'][0]['name']
                                    scope = signal_dict[signal[1]]['nets'][0]['hier']
                                    path = scope + '.' + name
                                    size = signal_dict[signal[1]]['nets'][0]['size']

                                    # register the signal
                                    reg[path] = writer.register_var(scope=scope, name=name, var_type=var_type, size=int(size))

                    # time probe path
                    time_path = 'top.trace_port_gen_i' + '.' + scfg.time_probe.name

                    # calculate emu_time offset
                    offset = 0
                    for idx, (cycle_count, timestamp) in enumerate(probe_data[time_path]['data']):
                        # break if the current timestep is less than the previous one, since that means
                        # wrapping has occurred
                        if timestamp < prev_timestep:
                            break
                        prev_timestep = timestamp

                        if timestamp > 0:
                            break

                        offset = cycle_count

                    #############################
                    # Represent signals over time
                    #############################

                    if emu_time_scaled:
                        # Add an index to all signals in signal dict, in case debug option was selected:
                        if debug:
                            for sig in signal_dict.keys():
                                signal_dict[sig]['index'] = 0

                        for idx, (cycle_count, timestamp) in enumerate(probe_data[time_path]['data']):
                            # break if timestamp is less than zero since it means that wrapping has occurred
                            if timestamp < 0:
                                break

                            # store all available signals in list, any signal, that is no longer in the list will be skipped
                            # signals, where the cycle_count is nop longer between current and next cycle count of the time
                            # signal will be removed from the list
                            sigs_in_interval = []
                            for sig in probe_data.keys():
                                sigs_in_interval.append((sig, None))

                            # Add all other signals in case debug flag is set
                            if debug:
                                for signal in signal_names:
                                    if not signal[0] in probe_data.keys() and not signal_dict[signal[1]]['nets'][0]['type'] == 'parameter':  # signal was not listed yet
                                        sigs_in_interval.append((signal[0], signal[1]))

                            # list of all activities within time interval
                            timestep_events = []

                            # As soon as all signals are no longer in the interval, timestep will advance
                            while sigs_in_interval:
                                for sig in sigs_in_interval:
                                    if sig[0] in probe_data.keys():
                                        sig_tuple = probe_data[sig[0]]['data'][probe_data[sig[0]]['index']]
                                    else: # debug signals
                                        sig_tuple = signal_dict[sig[1]]['cv'][signal_dict[sig[1]]['index']]

                                    if cycle_count == sig_tuple[0]:
                                        timestep_events.append([sig, timestamp, sig_tuple[1]])

                                        if sig[0] in probe_data.keys():
                                            probe_data[sig[0]]['index'] += 1
                                        else:
                                            signal_dict[sig[1]]['index'] += 1

                                        # This signal no longer needs to be observed
                                        sigs_in_interval.remove(sig)
                                    else:
                                        try: # Check if time signal is already at the end
                                            next_timestamp = probe_data[time_path]['data'][idx + 1][0]
                                        except: # Time signal has finished the end, finish conversion
                                            sigs_in_interval = []
                                            break
                                        if round(next_timestamp - offset) > sig_tuple[0]:
                                            # Note: There is always an offset between cycle count and timestamp  -> substract offset
                                            # The cycle count from data signal does not have a match with emu_time signal's cycle count
                                            # -> we need to apply interpolation in order to assign the timestamp properly
                                            cycles_in_dt = probe_data[time_path]['data'][idx+1][0] - cycle_count
                                            dt = probe_data[time_path]['data'][idx+1][1] - timestamp
                                            interp_timestamp = int(dt/cycles_in_dt * (sig_tuple[0] - cycle_count + offset) + timestamp)

                                            timestep_events.append([sig, interp_timestamp, sig_tuple[1]])

                                            if sig[0] in probe_data.keys():
                                                probe_data[sig[0]]['index'] += 1
                                            else:
                                                signal_dict[sig[1]]['index'] += 1
                                        else:
                                            # This signal no longer needs to be observed
                                            sigs_in_interval.remove(sig)

                            # Register events in time interval in chronological order
                            timestep_events = sorted(timestep_events, key=self.sort_timestamp)
                            for [name, timestamp, value] in timestep_events:
                                writer.change(reg[name[0]], timestamp, value)

                    ####################################
                    # Represent signals over cycle count
                    ####################################

                    else:
                        time_events = []  # store all events from result file
                        for signal in probe_data.keys():
                            for sig_tuple in probe_data[signal]['data']:
                                time_events.append([signal, sig_tuple[0], sig_tuple[1]])

                        # Add all other signals in case debug flag is set
                        if debug:
                            for signal in signal_names:
                                if not signal[0] in probe_data.keys() and not signal_dict[signal[1]]['nets'][0]['type'] == 'parameter':  # signal was not listed yet
                                    name = signal_dict[signal[1]]['nets'][0]['name']
                                    hier = signal_dict[signal[1]]['nets'][0]['hier']
                                    path = hier + '.' + name
                                    for sig_tuple in signal_dict[signal[1]]['cv']:
                                        time_events.append([path, sig_tuple[0], sig_tuple[1]])

                        # Register events in chronological order
                        time_events = sorted(time_events, key=self.sort_timestamp)
                        for [sig_name, timestamp, value] in time_events:
                            writer.change(reg[sig_name], timestamp, value)



        else:
            raise Exception(f'ERROR: No supported Result file format selected:{result_type_raw}')

    def get_csv_col(self, name):
        """
        Getting unscaled data from csv file column
        :return:
        """
        # have to preview the first few lines
        with open(self.result_path_raw, 'r') as f:
            first_line = f.readline()
            second_line = f.readline()

        # determine how many lines to skip
        if second_line.startswith('Radix'):
            skip_header=2
        else:
            skip_header=1

        # call a NumPy routine to read from the CSV file
        return np.genfromtxt(
            self.result_path_raw,
            delimiter=',',
            usecols=self.signal_lookup[name],
            skip_header=skip_header
        )

    def sort_timestamp(self, element):
        return element[1]
    def get_pyvcd_timescale(self, val):
        return si_format(val, precision=0) + 's'