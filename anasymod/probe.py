# general imports
import numpy as np
import os
import csv
from typing import Union

# anasymod imports
from anasymod.targets import CPUTarget, FPGATarget
from anasymod.utils.VCD_parser import ParseVCD


class Probe():
    """
    Base class for simulation data access API
    """
    def __init__(self, target: Union[CPUTarget, FPGATarget]):
        """
        Constructor
        """
        self.handle = None
        self.target = target

        #self.__ref_analysis = weakref.proxy(ref_analysis)
        #if False:
        #    from ...exported.analysis import Analysis
        #    self.__ref_analysis = Analysis()

        #self.simOpts = self.__ref_analysis.getSimOptions()
        #""":type: _Options_Base"""

        #if self.simOpts.idnum is not None:
        #    self.ident_num = self.simOpts.idnum
        #else:
        #    self.ident_num = 0

        self._data_valid = False

        #self.simulatorSimetrix = self.__ref_analysis.simulatorSimetrix
        #""":type: Simetrix"""

    def __del__(self):
        self.discardloadedsimdatafiles()

    def _probe(self, name, emu_time, cache=True):
        """
        Access probed waveform trace(s)

        :param name: name of probe whose waveform is require.
            (None = timebase reference trace)
        :type name: string
        :param cache: Cache probe data so subsequent calls for same data don't create
            more copies or trigger a SIMetrix data group load
        :type cache: bool

        :return: probed data for specified probe.
        :rtype: numpy.array
        """

        raise NotImplementedError()

    def _probes(self):
        """
        Get list of names probe waveforms for data group/ run
        :rtype: list[str]
        """

        raise NotImplementedError()

    def init_rundata(self):
        raise NotImplementedError()

    def discardloadedsimdatafile(self, run_num, check_loaded=True):
        """
        Discard probe data group from SIMetrix

        Normally a probed Data group accessed via probe is kept loaded in SIMetrix
        memory to avoid having to (expensively) reload it if further probed data vectors
        are accessed.  Calling this forces it to be unloaded from SIMetrix free-ing up
        memory.  Of course a follow-in accesses will be slow/expensive as data group
        needs to be reloaded.

        :param run_num: Run number in sweep, None for last run
        :type run_num: int
        :param check_loaded: Check group is actually loaded in SIMetrix, do nothing if it is not
        :type check_loaded: bool
        """
        raise NotImplementedError()

    def discardloadedsimdatafiles(self):
        """
        discard all   data groups currently loaded into SIMetrix
        """
        # print("DISCARD...")
        raise NotImplementedError()

    def refreshLoadedDataGroups(self):
        """
        Update local view of probe data groups currently loaded in SIMetrix

        Refresh  table of data groups loaded into SIMetrix from
        SIMetrix internal list.  Used to re-sync if
        activity in SIMetrox may have caused data groups loaded to change.
        """
        raise NotImplementedError()

    def _compress(self, wave=np.ndarray):
        """Compresses redundant data from 2d numpy array"""
        raise NotImplementedError()

    def parse_emu_time(self, data, emu_time):
        """

        :param data:
        :param emu_time:
        :return:
        """
        raise NotImplementedError()

class ProbeCSV(Probe):
    """
    API for CSV remote data access
    """

    def __init__(self, target: Union[CPUTarget, FPGATarget]):
        """
        Constructor
        """
        super().__init__(self, target=target)

        # List of dictionaries containing probename-probevalue pairs for each simulation run (one dict per sweep point)
        self.probe_caches = []
        """:type : list[dict[str, list[]]]"""

    def __del__(self):
        """
        Destructor

        Remote Data interface is automatically closed when Api is destructed
        """

    def init_rundata(self):
        self.probe_caches = [None] * 1 # As of now no sweeps are planned, later the value shall be set to the number of runs
        self._data_valid = True

    def path_for_sim_result_file(self):
        return os.path.join(self.target.cfg['result_path_raw'])

    def _probe(self, name, emu_time, cache=True):
        """
        Access csv logfile data for specified run number simulation parameter

        :param name: Column name in csv log, omit/None for all
        :type name: str

        :return: dict for `run_num`only or specified,
            list  for `name`  only specified,
            numpy.array for specified `run_num` and `name`,
            list of dict for run_num='all' specified
        :rtype: numpy.array | list[numpy.array] | dict[ string : numpy.array]
        """

        if not self._data_valid:
            raise LookupError("No data available (no succesful simulation run / dataset reload)")

        run_num = 0

        if run_num == 'all':
            for r in range(len(self.probe_caches)):
                if self.probe_caches[r] is None:
                    self.probe_caches[r] = self.fetch_simdata(self.path_for_sim_result_file())
        else:
            if self.probe_caches[run_num] is None:
                self.probe_caches[run_num] = self.fetch_simdata(self.path_for_sim_result_file())

        if run_num == 'all' and name is None:
            return self.probe_caches

        if run_num != 'all' and run_num >= len(self.probe_caches):
            raise ValueError("Run number must be in range [0 .. %d]" % len(self.probe_caches))

        if name is not None and run_num != 'all' and name not in self.probe_caches[run_num]:
            print("No such  name in simulation log: ", name)
            print("Available names: ", self.probe_caches[run_num].keys())
            raise LookupError("Bad probe name " + name)

        if name is None:
            return self.probe_caches[run_num]

        if run_num == 'all':
            if name not in self.probe_caches[0]:
                print("No such  name in simulation log: ", name)
                print("Available names: ", self.probe_caches[0].keys())
                raise ValueError("Bad probe name " + name)
            res = [log[name] for log in self.probe_caches]
            return res

        if name not in self.probe_caches[run_num]:
            print("No such  name in simulation log: ", name)
            print("Available names: ", self.probe_caches[run_num].keys())
            raise ValueError("Bad probe name " + name)

        return self.probe_caches[run_num][name]

    def fetch_simdata(self, csv_logfile):
        """
        Load simdata file as dictionary

        :return: Dict of numpy arrays (keys are column titles, values are column values)
        :rtype: dict[numpy.array]
        """

        with open(csv_logfile, "r") as csvfile:
            csvstrm = csv.DictReader(csvfile, delimiter=';', quotechar='\"')

            rowdict = next(csvstrm)
            csvdict = {name: [float(value)] for name, value in rowdict.items()}

            for rowdict in csvstrm:
                for name, value in rowdict.items():
                    csvdict[name].append(float(value))
        return {name: np.array(value) for name, value in csvdict.items()}

    def _probes(self):
        """
        Get list of names probe waveforms for specified run

        :rtype:list[str]
        """

        if not self._data_valid:
            raise LookupError("No data available (no succesful simulation run / dataset open)")

        run_num = 0

        if self.probe_caches[run_num] is None:
            self.probe_caches[run_num] = self.fetch_simdata(self.path_for_sim_result_file())

        return self.probe_caches[run_num].keys()

class ProbeVCD(Probe):
    def __init__(self, target: Union[CPUTarget, FPGATarget]):
        """
        Constructor for VCD reader.
        """
        super().__init__(target=target)

        # List of dictionaries containing probename-probevalue pairs for each simulation run (one dict per sweep point)
        self.probe_caches = []
        """:type : list[dict[str, list[]]]"""

        # VCD file handle
        self.vcd_handle = dict()
        """:type: dict[str,vcd.VCDparser]"""

        self.init_rundata()

    def __del__(self):
        """
        Destructor

        Remote Data interface is automatically closed when Api is destructed
        """
        self.probe_caches = []
        pass

    def init_rundata(self):
        self.probe_caches = [{} for _ in range(10)] # this needs a fix later, shall be depenent on number of signals that were stored during simulation
        self._data_valid = True

    def parse_emu_time(self, data, emu_time):
        """
        Parse Emu_time end returns new vector with emu_time instead of cycle count
        :param data:
        :return:
        """
        emutime_data = data.copy()
        emutime_data.setflags(write=True)

        # emu_time vector index
        t = 0
        for i in range(int(len(emutime_data[0]))):
            while emutime_data[0][i] > emu_time[0][t]:
                t += 1
                # break while loop, if it reaches the end of the array of emu_time
                if t >= len(emu_time[0]):
                    break
            # break for loop because whole emu_time vector was parsed
            if t >= len(emu_time[0]):
                break
            # if there is a data point with no coresponding emu_time cyclecount, take the last common cycle count value
            if emutime_data[0][i] < emu_time[0][t]:
                emutime_data[0][i] = emu_time[1][t]
            # if cycle count of data and emu_time vector is the same, take the time value
            else:
                emutime_data[0][i] = emu_time[1][t]

        emutime_data.setflags(write=False)
        return emutime_data

    def _probe(self, name, emu_time, cache=True):
        """
        Access VCD data for specified run number simulation parameter
        :param name: Column name in csv log, omit/None for all
        :type name: str
        :param emu_time: Use emu_time as time basis or cycle_count
        :type emu_time: bool
        :param cache:
        :return:
        """
        """
                Access vcd data for specified run number simulation parameter

                :param name: Column name in csv log, omit/None for all
                :type name: str

                :return: dict for `run_num`only or specified,
                    list  for `name`  only specified,
                    numpy.array for specified `run_num` and `name`,
                    list of dict for run_num='all' specified
                :rtype: numpy.array | list[numpy.array] | dict[ string : numpy.array]

                """
        run_num = 0
        vcd_handle = self.setup_data_access()
        try:
            run_cache = self.probe_caches[run_num]
        except IndexError:  # If PyVerify single run: run_num may be bigger than len(self.probe_caches)
            run_cache = []
            cache = False

        # check if empty run_cache and parse all signals and store in run_cache
        if len(run_cache) == 0 and cache:
            run_cache = self.fetch_simdata(vcd_handle, update_data=False)
            self.probe_caches[run_num] = run_cache

        #check complete name of emu_time_probe
        matching = [s for s in self._probes() if self.target.str_cfg.time_probe.name in s]
        if len(matching) == 1:
            emu_time_probe = matching[0]
        else:
            raise Exception(f'No Time probe was found in vcd file')

        if emu_time_probe not in run_cache:
            data = self.fetch_simdata(vcd_handle, name=emu_time_probe, update_data=True)
            print("Emu_time not in cache: " + name)
            if cache:
                # Cached - make it read-only to prevent nasty overwriting bugs
                data.setflags(write=False)
                run_cache[emu_time_probe] = data

        if name not in run_cache:
            data = self.fetch_simdata(vcd_handle, name=name)
            print("Data not in cache: " + name)
            if cache:
                # Cached - make it read-only to prevent nasty overwriting bugs
                data.setflags(write=False)
                run_cache[name] = data
        else:
            data = run_cache[name]
            print("Data already in cache: " + name)

        if emu_time and name != emu_time_probe:
            print("Using emulation time")
            emutime_data = self.parse_emu_time(data=data, emu_time=run_cache[emu_time_probe])
            return emutime_data
        else:
            print("Using cycle counts as time basis")
            return data

    def _probes(self):
        """
        Get list of names probe waveforms for specified run

        :param run_num: Run number in sweep, omit/None for last run, 'all' for all runs
        :type run_num: int

        :rtype:list[str]
        """
        vcd_handle = self.setup_data_access()
        return vcd_handle.list_sigs()

    def discardloadedsimdatafiles(self):
        """

        """
        for key in self.vcd_handle.keys():
            vcd_handle = self.vcd_handle[key]
            try:
                del vcd_handle
                del self.probe_caches
            except:
                pass
        self.vcd_handle = dict()

    def setup_data_access(self):
        """
        :rtype: ParseVCD
        """
        if not self._data_valid:
            raise ValueError("No data available (no succesful simulation run / dataset reload)")

        #if simulator is None:
        #    simulator = self.simOpts._opts_container['simulator']

        #if simulator not in enums.SimulatorType.__dict__.keys():
        #    raise ValueError(
        #        "Specified Simulator is not valid. Valid simulators are: {0}; given simulator was: {1}".format(
        #            enums.SimulatorType, simulator))

        vcd_handle = "_".join([self.target._name])
        vcd_file_name = self.path_for_sim_result_file()
        if vcd_handle not in self.vcd_handle.keys():
            self.vcd_handle[vcd_handle] = ParseVCD(vcd_file_name)
        vcd_handle = self.vcd_handle[vcd_handle]

        return vcd_handle

    def path_for_sim_result_file(self):
        # Setup Simulation Result file names
        if os.path.isfile(self.target.cfg.vcd_path):
            return self.target.cfg.vcd_path
        else:
            raise Exception(f'ERROR: Result file: self.target.cfg.vcd_path does not exist; cannot read results!')

    def fetch_simdata(self, file_handle, name="", update_data=False):
        """
        Load VCD signals and store values as dictionary

        :return: Dict of numpy arrays (keys are column titles, values are column values)
        :rtype: dict[numpy.array]
        """
        signal = ''
        cycle_cnt = ''
        if name is not "":
            # parse only single signal name
            signal_dict = file_handle.parse_vcd(update_data=update_data)
            """ :type : dict()"""

            for key in signal_dict.keys():
                signal = [i[1] for i in signal_dict[key]['cv']]
                cycle_cnt = [i[0] for i in signal_dict[key]['cv']]

            if signal in [""]:
                raise ValueError("No data found for signal:{0}".format(name))

            if signal == self.target.str_cfg.time_probe.name:
                return np.array([cycle_cnt, signal], dtype='O')
            else:
                return np.array([cycle_cnt, signal], dtype='O')

        else:
            # parse all signals into run_cache
            signal_dict = file_handle.parse_vcd(sigs=name, update_data=update_data)
            """ :type : dict()"""
            data = {}
            for key in signal_dict.keys():
                signal = [i[1] for i in signal_dict[key]['cv']]
                cycle_cnt = [i[0] for i in signal_dict[key]['cv']]
                net = signal_dict[key]['nets'][0]
                name = net['hier'] + '.' + net['name']
                if signal_dict[key]['nets'][0]['name'] == self.target.str_cfg.time_probe.name:
                    #convert binary representation on time signal to integer and scale according to precision set in prj
                    dt_scale = self.target.prj_cfg.cfg.dt_scale
                    signal_scaled = [int(x, 2) * dt_scale for x in signal]
                    data[name] = np.array([cycle_cnt, signal_scaled], dtype='O')
                else:
                    data[name] = np.array([cycle_cnt, signal], dtype='O')
                data[name].setflags(write=False)

            if signal in [""]:
                raise ValueError("No data found for signal:{0}".format(name))

            return data

