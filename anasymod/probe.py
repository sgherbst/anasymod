import numpy as np
import os
import weakref
import csv

#from ..utils import enums
from anasymod.utils.VCD_parser import VCDparser

class Api(object):
    """
    Base class for simulation data access API
    """
    def __init__(self, ref_analysis, options):
        """
        Constructor
        """
        self.handle = None

        self.__ref_analysis = weakref.proxy(ref_analysis)
        if False:
            from ...exported.analysis import Analysis
            self.__ref_analysis = Analysis()

        self.simOpts = self.__ref_analysis.getSimOptions()
        """:type: _Options_Base"""

        if self.simOpts.idnum is not None:
            self.ident_num = self.simOpts.idnum
        else:
            self.ident_num = 0

        self._data_valid = False

        self.simulatorSimetrix = self.__ref_analysis.simulatorSimetrix
        """:type: Simetrix"""

    def __del__(self):
        self.discardloadedsimdatafiles()

    def _probe(self, name, run_num=None, cache=True, simulator=None, division_index=0):
        """
        Access probed waveform trace(s)

        :param run_num: run number in sweep, None for last run
        :type run_num: int
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

    def _probes(self, run_num=None, group_name=None, simulator=None):
        """
        Get list of names probe waveforms for data group/ run

        :param run_num: Run number in sweep, None for last run
        :type run_num: int
        :param group_name: Name of data-group loaded in SIMetrix
        :type group_name: string

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

class ApiCSV(Api):
    """
    API for CSV remote data access
    """

    def __init__(self, ref_analysis, options):
        """
        Constructor
        """
        Api.__init__(self, ref_analysis, options)

        # List of dictionaries containing probename-probevalue pairs for each simulation run (one dict per sweep point)
        self.probe_caches = []
        """:type : list[dict[str, list[]]]"""

    def __del__(self):
        """
        Destructor

        Remote Data interface is automatically closed when Api is destructed
        """

    def init_rundata(self):
        self.probe_caches = [None] * self.simOpts.runs
        self._data_valid = True

    def path_for_sim_result_file(self, run_num):
        return os.path.join(self.simOpts.workingdir, "{0}_{1:04d}.csv".format(self.simOpts.fileprefix, run_num))

    def _probe(self, name, run_num=None, cache=True, simulator=None, division_index=0):
        """
        Access csv logfile data for specified run number simulation parameter

        :param run_num: Run number in sweep, omit/None for last run, 'all' for all runs
        :type run_num: int
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

        run_num = self.simOpts._default_run_num(run_num)

        if run_num == 'all':
            for r in range(len(self.probe_caches)):
                if self.probe_caches[r] is None:
                    self.probe_caches[r] = self.self.fetch_simdata(self.path_for_sim_result_file(r))
        else:
            if self.probe_caches[run_num] is None:
                self.probe_caches[run_num] = self.self.fetch_simdata(self.path_for_sim_result_file(run_num))

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

    def _probes(self, run_num=None, group_name=None, simulator=None):
        """
        Get list of names probe waveforms for specified run

        :param run_num: Run number in sweep, omit/None for last run, 'all' for all runs
        :type run_num: int

        :rtype:list[str]
        """

        if not self._data_valid:
            raise LookupError("No data available (no succesful simulation run / dataset open)")

        run_num = self.simOpts._default_run_num(run_num)

        if self.probe_caches[run_num] is None:
            self.probe_caches[run_num] = self.self.fetch_simdata(self.path_for_sim_result_file(run_num))

        return self.probe_caches[run_num].keys()

class ApiVCD(Api):
    def __init__(self, ref_analysis, options):
        """
        Constructor for VCD reader.
        """
        Api.__init__(self, ref_analysis, options)

        # List of dictionaries containing probename-probevalue pairs for each simulation run (one dict per sweep point)
        self.probe_caches = []
        """:type : list[dict[str, list[]]]"""

        # VCD file handle
        self.vcd_handle = dict()
        """:type: dict[str,vcd.VCDparser]"""

    def __del__(self):
        """
        Destructor

        Remote Data interface is automatically closed when Api is destructed
        """
        pass

    def init_rundata(self):
        self.probe_caches = [{} for _ in list(self.simOpts.sim_params.items())[0][1]]
        self._data_valid = True

    def _probe(self, name, run_num=None, cache=True, simulator=None, division_index=0):
        """
        Access vcd data for specified run number simulation parameter

        :param run_num: Run number in sweep, omit/None for last run, 'all' for all runs
        :type run_num: int
        :param name: Column name in csv log, omit/None for all
        :type name: str

        :return: dict for `run_num`only or specified,
            list  for `name`  only specified,
            numpy.array for specified `run_num` and `name`,
            list of dict for run_num='all' specified
        :rtype: numpy.array | list[numpy.array] | dict[ string : numpy.array]

        """
        run_num = self.simOpts._default_run_num(run_num)
        vcd_handle = self.setup_data_access(run_num, simulator)
        try:
            run_cache = self.probe_caches[run_num]
        except IndexError:  # If PyVerify single run: run_num may be bigger than len(self.probe_caches)
            run_cache = []
            cache = False

        if name not in run_cache:
            data = self.fetch_simdata(vcd_handle, name)
            if cache:
                # Cached - make it read-only to prevent nasty overwriting bugs
                data.setflags(write=False)
                run_cache[name] = data

        else:
            data = run_cache[name]
        return data

    def _probes(self, run_num=None, group_name=None, simulator=None):
        """
        Get list of names probe waveforms for specified run

        :param run_num: Run number in sweep, omit/None for last run, 'all' for all runs
        :type run_num: int

        :rtype:list[str]
        """
        run_num = self.simOpts._default_run_num(run_num)
        vcd_handle = self.setup_data_access(run_num, simulator)
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

    def setup_data_access(self, run_num, simulator):
        """

        :param run_num:
        :param simulator:
        :rtype: VCDparser
        """
        if not self._data_valid:
            raise ValueError("No data available (no succesful simulation run / dataset reload)")

        if simulator is None:
            simulator = self.simOpts._opts_container['simulator']

        #if simulator not in enums.SimulatorType.__dict__.keys():
        #    raise ValueError(
        #        "Specified Simulator is not valid. Valid simulators are: {0}; given simulator was: {1}".format(
        #            enums.SimulatorType, simulator))

        vcd_handle = "_".join([simulator, str(run_num)])
        vcd_file_name = self.path_for_sim_result_file(run_num, simulator)
        if vcd_handle not in self.vcd_handle.keys():
            self.vcd_handle[vcd_handle] = VCDparser(vcd_file_name)
        vcd_handle = self.vcd_handle[vcd_handle]

        return vcd_handle

    def path_for_sim_result_file(self, run_num, simulator):
        # Setup Simulation Result file names
        return os.path.join(self.simulatorSimetrix.simdir, "{0}_{1:04d}{2}".format(self.simOpts.fileprefix, run_num, ".vcd"))

    def fetch_simdata(self, file_handle, name):
        """
        Load VCD signals and store values as dictionary

        :return: Dict of numpy arrays (keys are column titles, values are column values)
        :rtype: dict[numpy.array]
        """

        signal = r""
        if name.lower() == r"time":
            signals = file_handle.list_sigs()
            signal_dict = file_handle.parse_vcd(siglist=[signals[0]])
            """ :type : dict()"""

            for key in signal_dict.keys():
                signal = [i[0] for i in signal_dict[key]['tv']]
        elif r"_sig_time" in name:
            signal_dict = file_handle.parse_vcd(siglist=[name])
            """ :type : dict()"""

            for key in signal_dict.keys():
                signal = [i[0] for i in signal_dict[key]['tv']]
        else:
            signal_dict = file_handle.parse_vcd(siglist=[name])
            """ :type : dict()"""

            for key in signal_dict.keys():
                signal = [i[1] for i in signal_dict[key]['tv']]

        if signal in [""]:
            raise ValueError("No data found for signal:{0}".format(name))
        return np.array(signal)
