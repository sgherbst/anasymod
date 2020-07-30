import numpy as np
import scipy.interpolate

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
