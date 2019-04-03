import numpy as np
import os
import csv

from typing import Union

from anasymod.utils.VCD_parser import VCDparser
from anasymod.config import EmuConfig

#from anasymod.targets import SimulationTarget, FPGATarget

class Probe():
    """
    Base class for simulation data access API
    """
    def __init__(self, prj_config: EmuConfig, target):
        """
        Constructor
        """
        self.handle = None
        self.prj_config = prj_config
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

    def _probe(self, name, emu_time, compress, preserve, cache=True):
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


class ProbeCSV(Probe):
    """
    API for CSV remote data access
    """

    def __init__(self, prj_config: EmuConfig, target):
        """
        Constructor
        """
        super().__init__(self, prj_config=prj_config, target=target)

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
        return os.path.join(self.target.cfg['csv_path'])

    def _probe(self, name, emu_time, compress, preserve, cache=True):
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
    def __init__(self, prj_config: EmuConfig, target):
        """
        Constructor for VCD reader.
        """
        super().__init__(prj_config=prj_config, target=target)

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
        pass

    def init_rundata(self):
        self.probe_caches = [{} for _ in range(10)] # this needs a fix later, shall be depenent on number of signals that were stored during simulation
        self._data_valid = True

    def _probe(self, name, emu_time, compress=True, preserve=False, cache=True):
        """
        Access VCD data for specified run number simulation parameter
        :param name: Column name in csv log, omit/None for all
        :type name: str
        :param emu_time: Use emu_time as time basis or cycle_count
        :type emu_time: bool
        :param mode: Probe data for all time steps, or only when value changed
        :type mode: str
        :param preserve: When probing value changed data
        :type preserve: bool
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

        # check complete name of emu_time_probe
        matching = [s for s in self._probes() if 'emu_time_probe' in s]
        if len(matching) == 1:
            emu_time_probe = matching[0]

        if emu_time_probe not in run_cache:
            data = self.fetch_simdata(vcd_handle, emu_time_probe)
            if cache:
                # Cached - make it read-only to prevent nasty overwriting bugs
                data.setflags(write=False)
                run_cache[emu_time_probe] = data

        if name not in run_cache:
            data = self.fetch_simdata(vcd_handle, name)
            if cache:
                # Cached - make it read-only to prevent nasty overwriting bugs
                data.setflags(write=False)
                run_cache[name] = data

        else:
            data = run_cache[name]

        if emu_time and name != emu_time_probe:
            print("Using emulation time")
            emu_data = np.array([run_cache[emu_time_probe][1], data[1]])
            if compress:
                return self._compress(emu_data, preserve)
            else:
                return emu_data
        else:
            print("Using cycle counts as time basis")
            if compress:
                return self._compress(data, preserve)
            else:
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
            except:
                pass
        self.vcd_handle = dict()

    def setup_data_access(self):
        """
        :rtype: VCDparser
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
            self.vcd_handle[vcd_handle] = VCDparser(vcd_file_name)
        vcd_handle = self.vcd_handle[vcd_handle]

        return vcd_handle

    def path_for_sim_result_file(self):
        # Setup Simulation Result file names
        return os.path.join(self.target.cfg['vcd_path'])

    def fetch_simdata(self, file_handle, name):
        """
        Load VCD signals and store values as dictionary

        :return: Dict of numpy arrays (keys are column titles, values are column values)
        :rtype: dict[numpy.array]
        """

        signal = r""

        signal_dict = file_handle.parse_vcd(siglist=[name], update_data=True)
        """ :type : dict()"""

        for key in signal_dict.keys():
            signal = [i[1] for i in signal_dict[key]['tv']]
            cycle_cnt = [i[0] for i in signal_dict[key]['tv']]

        if signal in [""]:
            raise ValueError("No data found for signal:{0}".format(name))

        return np.array([cycle_cnt,signal], dtype='O')

    def _compress(self, wave=np.ndarray, preserve=False):
        """
        This function compress the waveform wave and removes redundant values
        :param wave: 2d numpy.ndarray
        :return: 2d numpy.ndarray
        """
        temp_data = ""
        temp_time = ""
        compressed =[]

        for d in wave.transpose():
            #if d[0] == temp_time:
                # same time value should replace with latest data value
                #compressed.pop()
                #compressed.append(d)
            #else:
            if temp_data != "":
                if d[1] != temp_data:
                    if preserve:
                        compressed.append([d[0],temp_data]) #old value with same timestep to preserve stepping
                    compressed.append(d)
            else:
                compressed.append(d)
            temp_data = d[1]
            temp_time = d[0]
        # check if last value was taken otherwise append it
        if wave.transpose()[-1][0] != compressed[-1][0]:
            compressed.append(wave.transpose()[-1])
        try:
            return np.array(compressed, dtype='float').transpose()
        except:
            return np.array(compressed, dtype='O').transpose()

