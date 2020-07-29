import os
import numpy as np
import scipy.interpolate
from argparse import ArgumentParser
from anasymod.analysis import Analysis


DEFAULT_SIMULATOR = 'icarus' if 'FPGA_SERVER' not in os.environ else 'vivado'


def run_simulation(root, simulator_name):
    # create analysis object
    ana = Analysis(input=root,
                   simulator_name=simulator_name)

    # generate functional models
    ana.gen_sources()

    # run the simulation
    ana.simulate()

    # print string to indicate test is done
    print('Done.')


def run_emulation(root, gen_bitstream=False, emu_ctrl_fun=None, emulate=False):
    # create analysis object
    ana = Analysis(input=root)

    # generate functional models
    ana.gen_sources()
    ana.set_target(target_name='fpga')  # set the active target to 'fpga'

    # generate the bitstream if desired
    if gen_bitstream:
        ana.build()  # generate bitstream for project

    # run the specific emulation sequence if desired
    if emulate and (emu_ctrl_fun is not None):
        ctrl = ana.launch(debug=True)  # start interactive control
        emu_ctrl_fun(ctrl)

    # print string to indicate test is done
    print('Done.')


class CommonArgParser(ArgumentParser):
    def __init__(self, sim_fun, emu_fun, *args, **kwargs):
        # call the super constructor
        super().__init__(*args, **kwargs)

        # parse command-line arguments
        self.add_argument('--sim', action='store_true')
        self.add_argument('--emulate', action='store_true')
        self.add_argument('--gen_bitstream', action='store_true')
        self.add_argument('--simulator_name', type=str, default=DEFAULT_SIMULATOR)
        args = self.parse_args()

        # run actions as requested
        if args.sim:
            print('Running simulation...')
            sim_fun(simulator_name=args.simulator_name)
        if args.gen_bitstream or args.emulate:
            print('Running emulation...')
            emu_fun(gen_bitstream=args.gen_bitstream, emulate=args.emulate)


class Waveform:
    def __init__(self, data, time):
        self.data = np.array(data, dtype=float)
        self.time = np.array(time, dtype=float)
        self.interp = scipy.interpolate.interp1d(
            time, data,
            bounds_error=False, fill_value=(data[0], data[-1])
        )

        # attach measurement objects in a way that is compatible with pverify
        measurements = Measurements(self)
        self.Measurements_Base = measurements
        self.Measurements_NonPeriodic = measurements
        self.Measurements_Periodic = measurements

    def check_in_limits(self, wave_lo, wave_hi):
        # compute bounds
        lo_bnds = wave_lo.interp(self.time)
        hi_bnds = wave_hi.interp(self.time)

        # uncomment for graphical debugging
        # import matplotlib.pyplot as plt
        # plt.plot(self.time, lo_bnds)
        # plt.plot(self.time, hi_bnds)
        # plt.plot(self.time, self.data)
        # plt.legend(['lo_bnds', 'hi_bnds', 'data'])
        # plt.show()

        # find any point where the waveform is out of spec
        in_spec = np.logical_and(lo_bnds <= self.data, self.data <= hi_bnds)
        if np.all(in_spec):
            pass
        else:
            indices = np.where(np.logical_not(in_spec))
            times = self.time[indices]
            raise Exception(f'Waveform is out of spec.  Check times: {times}')

class Measurements:
    def __init__(self, wave: Waveform):
        self.wave = wave

    def min(self):
        return np.min(self.wave.data)

    def max(self):
        return np.max(self.wave.data)

    def peak_to_peak(self):
        return self.max() - self.min()

    def find_settled(self, lo, hi):
        # find first index where the waveform is in the settled range
        idx = np.argmax((lo <= self.wave.data) & (self.wave.data <= hi))

        # if there is no such value, idx will be zero, so we have to check
        # for that condition
        if not (lo <= self.wave.data[idx] <= hi):
            raise Exception('Waveform did not settle to the specified range.')

        return self.wave.time[idx]

    def frequency(self, level=0, slope='rise', hysteresis=0):
        # find the crossing times
        crossings = []
        armed = False
        for t, v in zip(self.wave.time, self.wave.data):
            if slope == 'rise':
                if armed and (v > (level + hysteresis)):
                    crossings.append(t)
                    armed = False
                elif v < (level - hysteresis):
                    armed = True
            elif slope == 'fall':
                if armed and (v < (level - hysteresis)):
                    crossings.append(t)
                    armed = False
                elif v > (level + hysteresis):
                    armed = True
            else:
                raise Exception(f"Unknown slope type: {slope}")

        # measure time from the first crossing to the last crossing,
        # as well as the number of periods
        dt = crossings[-1] - crossings[0]
        num = len(crossings) - 1

        # return the average frequency
        return num/dt

    def frequency_average(self, *args, **kwargs):
        # not sure what this function is supposed to do as compared to the previous
        # one, so I'm leaving this as an alias to "frequency" for now
        return self.frequency(*args, **kwargs)