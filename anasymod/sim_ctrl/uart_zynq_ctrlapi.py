import serial, os
import serial.tools.list_ports as ports
from .console_print import cprint_block
from pathlib import Path
from anasymod.base_config import BaseConfig
from anasymod.sim_ctrl.ctrlapi import CtrlApi
from anasymod.enums import ConfigSections
from anasymod.config import EmuConfig
from anasymod.structures.structure_config import StructureConfig
from anasymod.emu.xsct_emu import XSCTEmulation
from anasymod.generators.gen_api import CodeGenerator
from anasymod.templates.launch_ILA_tcl import TemplLAUNCH_ILA_TCL
from anasymod.enums import TraceUnitOperators
from anasymod.sim_ctrl.datatypes import AnalogProbe, DigitalSignal
from anasymod.util import expand_path
from anasymod.wave import ConvertWaveform
from anasymod.files import mkdir_p


class UARTCtrlApi(CtrlApi):
    """
    Start an interactive control interface to HW target for running regression tests or design exploration/debug.
    For FPGA/Emulators, as a pre-requisit, bitstream must have been created and programmed. Additionally any eSW
    necessary in the targeted system must have already been programmed.
    """
    def __init__(self, result_path_raw, result_type_raw, result_path, prj_cfg: EmuConfig, scfg: StructureConfig,
                 content, project_root, ltxfile_path, top_module, cwd=None, err_strs=None, debug=False,
                 float_type=False, prompt='Vivado% '):
        super().__init__(cwd=cwd, pcfg=prj_cfg, scfg=scfg, prompt=prompt, debug=debug)
        # set defaults
        if err_strs is None:
            err_strs = ['ERROR', 'FATAL']

        self.content = content
        self.project_root = project_root
        self.top_module = top_module

        self.result_path_raw = result_path_raw
        self.result_type_raw = result_type_raw
        self.result_path = result_path
        self.float_type = float_type

        self.debug = debug
        self.err_strs = err_strs

        self.tcl_console_running = False
        self.server_addr = None
        self.ltxfile_path = ltxfile_path

        # Initialize control config
        self.cfg = Config(cfg_file=prj_cfg.cfg_file)

        vid = self.pcfg.board.uart_zynq_vid
        if isinstance(vid, list):
            self.vid_list = vid
        else:
            self.vid_list = [vid]

        pid = self.pcfg.board.uart_zynq_pid
        if isinstance(pid, list):
            self.pid_list = pid
        else:
            self.pid_list = [pid]

        self.port_list = []
    ### User Functions

    def sendline(self, line, timeout=float('inf')):
        """
        Send a single line in target shell specific language e.g. in tcl for tcl shell.
        :param line: Line that shall be send to/processed by shell
        :param timeout: Maximum time granted for operation to finish
        :return: Return string from Vivado TCL interpreter
        """
        if self.debug:
            cprint_block([line], title='SEND', color='magenta')

        self.proc.sendline(line)
        before = self._expect_prompt(timeout=timeout)

        # make sure that there were no errors
        for err_str in self.err_strs:
            if err_str in before:
                raise Exception(f'Found {err_str} in output from Vivado.')

    def source(self, script, timeout=float('inf')):
        """
        Source a script written language for targeted shell.
        :param script: Name/Path to script that shall be sourced
        :param timeout: Maximum time granted for operation to finish
        """
        script = Path(script).resolve()
        res = self.sendline(f'source {script.as_posix()}', timeout=timeout)

    def setup_trace_unit(self, trigger_name, trigger_operator, trigger_value, sample_decimation=None, sample_count=None):
        """
        Setup the trace unit. This involves defining the signal, that shall be used to start tracing and defining the
        comparison operator, which is used to monitor the trigger signal. Also arm the trace unit at the end.

        Note: In case the trigger value is set too high and an overflow occurs, the simulation will hang, as the trigger
        condition will never be met.

        :param trigger_name:        Probe signal to be used as trigger signal.
        :param trigger_operator:    Comparison operator that is used when monitoring the trigger signal to detect,
                                    when a trigger shall be fired. Available oerators are:
                                        eq (equal),
                                        neq (not equal),
                                        gt (greater than),
                                        gteq (greater or equal than),
                                        lt (lesser than),
                                        lteq (lesser or equal than)
        :param trigger_value:       Value, the probe signal is compared to.
        :param sample_decimation:   Number of samples to be skipped during recording. By default, every sample will
                                    stored in the results file, adding a sample_decimation will allow to only record
                                    every x sample.
        :param sample_count:        Number of samples to be recorded. This number shall not exceed that maximum ILA
                                    depth defined during project setup AND needs to be a multiple of 2.
        """

        # Start vivado TCL interpreter, if it is not already running
        if not self.tcl_console_running:
            super()._initialize_vivado_tcl()
            self._setup_ila_ctrl(server_addr=self.server_addr)
            self.tcl_console_running = True

        # Compute timeout, that needs to be set for ila recording. Due to a bug in the ILA core, recording does not
        # return, unless a timeout is specified, for recordings exceeding 0.26 s
        self.record_timeout = 0.0

        trigger_obj = None

        if sample_count:
            # This solution I got from https://stackoverflow.com/questions/57025836/check-if-a-given-number-is-power-of-two-in-python
            # and is checking if sample_count is a power of two using bit manipulations
            if (sample_count & (sample_count-1) == 0) and sample_count != 0:
                depth = sample_count
            else:
                raise Exception(f'ERROR: Sample count needs to be a power of 2, but is set to: {sample_count}')
        else:
            depth = self.pcfg.ila_depth

        # Check, if provided trigger_signal is a valid signal connected to the ILA
        for probe in [self.scfg.time_probe] + self.scfg.analog_probes + self.scfg.digital_probes:
            if trigger_name == probe.name:
                trigger_obj = probe
            elif trigger_name == 'time':
                trigger_obj = self.scfg.time_probe
            else:
                raise Exception(f'ERROR: Provided trigger_signal:{trigger_name} is not a valid probe in the existing project!')

        # Check if operator set is legal
        if not trigger_operator in TraceUnitOperators.__dict__.values():
            raise Exception(f'ERROR: Provided operator:{trigger_operator} is not legal! Supported operators are:{TraceUnitOperators.__dict__.values()}')

        # Convert compare value depending on signal type
        if isinstance(trigger_obj, AnalogProbe):
            if not isinstance(trigger_value, float):
                raise Exception(
                    f'ERROR: trigger_value type for an analog trigger signal shall ne float, it is instead:{type(trigger_value)}')
            value_int = int(round(trigger_value * (2 ** (int(-trigger_obj.exponent)))))
            trigger_value_as_bin = f"{int(trigger_obj.width)}'u{value_int}"
        elif isinstance(trigger_obj, DigitalSignal):
            # For the time signal, conversion from float to int is necessary
            if trigger_name in ['time', self.scfg.time_probe.name]:
                # Convert trigger value to integer considering dt_scale
                trigger_value_as_int = int(float(trigger_value) / float(self.pcfg.cfg.dt_scale))
                # Represent as binary and expand to time_width
                trigger_value_as_bin = f"{trigger_obj.width}'b{bin(trigger_value_as_int).replace('b', '').zfill(self.pcfg.cfg.time_width)}"
                # Extend record_timeout according to time trigger
                self.record_timeout += float(trigger_value)
            elif isinstance(trigger_value, int):
                trigger_value_as_bin = f"{trigger_obj.width}'u{trigger_value}"
            else:
                p = set(trigger_value)
                s = {'0', '1'}

                if s == p or p == {'0'} or p == {'1'}:
                    trigger_value_as_bin = f"{trigger_obj.width}'b{trigger_value}"
                else:
                    raise Exception(f'ERROR: Provided trigger value:{trigger_value} is not valid for a digital trigger '
                                    f'signal, either provide and interger or binary string!')
        else:
            raise Exception(f'ERROR: No valid signal type for provided trigger signal:{trigger_name} Type:{type(trigger_obj)}')

        self.sendline(f'set_property CONTROL.CAPTURE_MODE BASIC $ila_0_i')
        self.sendline(f'set_property CONTROL.TRIGGER_POSITION 0 $ila_0_i')
        self.sendline(f"set_property TRIGGER_COMPARE_VALUE {trigger_operator}{trigger_value_as_bin} [get_hw_probes trace_port_gen_i/{trigger_obj.name} -of_objects $ila_0_i]")

        # Data depth is set to 2, as 1 is not supported by Vivado's ILA Core
        self.sendline(f'set_property CONTROL.DATA_DEPTH {depth} $ila_0_i')

        # Window count is set to half of the selected ILA depth
        #self.sendline(f'set_property CONTROL.WINDOW_COUNT {int(window_count)} $ila_0_i')
        self.sendline(f'set_property CONTROL.WINDOW_COUNT 1 $ila_0_i')
        self.sendline(f"set_property CAPTURE_COMPARE_VALUE eq1'b1 [get_hw_probes trace_port_gen_i/emu_dec_cmp -of_objects $ila_0_i]")

        # Set decimation threshold signal to value defined in sample_decimation if set
        if sample_decimation:
            if isinstance(sample_decimation, int): # Check if sample_decimation is an integer
                self.set_param(name=self.scfg.dec_thr_ctrl.name, value=sample_decimation, timeout=30)
            else:
                raise Exception(f'Provided sample_decimation value is of wrong type, expecting integer and got:{type(sample_decimation)}')
        else:
            sample_decimation = 0

        self.arm_trace_unit()

        # conclude calculation of record_timeout by considering time needed to collect samples and representing
        # over minutes

        self.record_timeout += float(self.pcfg.cfg.dt) * depth * sample_decimation
        self.record_timeout = self.record_timeout / 60

    def arm_trace_unit(self):
        """
        Arm the trace unit, this will delete the buffer and arm the trigger.
        """
        self.sendline('run_hw_ila $ila_0_i')

    def wait_on_and_dump_trace(self, result_file=None):
        """
        Wait until the trace unit stopped recording data. Transmit this data to the host PC, store by default to the raw
        result file path, or a custom path provided by the user, and convert analog values from fixed-point to float.
        Finally store it to a .vcd file in the default location.

        :param result_file: Optionally, it is possible to provide a custom result file path.
        """

        if result_file is not None:
            # Expand provided path, paths relative to project root are also supported
            result_path = expand_path(result_file, rel_path_reference=self.pcfg.root)

            # Create raw result path by adding _raw to the filename
            result_path_raw = os.path.join(os.path.dirname(result_path),
                                           os.path.basename(os.path.splitext(result_path)[0]) + '_raw' +
                                           os.path.splitext(result_path)[1])
            print(f'Simulation results will be stored in:{result_path}')
        else:
            result_path = self.result_path
            result_path_raw = self.result_path_raw

        if not result_path:
            raise Exception(f'ERROR: provided result_file:{result_file} is not valid!')

        # wait until trace buffer is full
        self.sendline(f'wait_on_hw_ila -timeout {self.record_timeout} $ila_0_i')

        # transmit and dump trace buffer data to a CSV file
        self.sendline('current_hw_ila_data [upload_hw_ila_data $ila_0_i]')

        if not os.path.isdir(os.path.dirname(result_path_raw)):
            mkdir_p(os.path.dirname(result_path_raw))

        self.sendline(f'write_hw_ila_data -csv_file -force {{{result_path_raw}}} [current_hw_ila_data]')

        # Convert to .vcd and from fixed-point to float
        ConvertWaveform(result_path_raw=result_path_raw,
                        result_type_raw=self.result_type_raw,
                        result_path=result_path,
                        str_cfg=self.scfg,
                        float_type=self.float_type,
                        dt_scale=self.pcfg.cfg.dt_scale)

    def get_param(self, name, timeout=30):
        """
        Read value of a control parameter in design.
        :param name: Name of control parameter to be read
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        self._write(name=self.cfg.get_operation_prefix+name)
        return self._read()

    def set_param(self, name, value, timeout=30):
        """
        Set value of a control parameter in design.
        :param name: Name of control parameter to be set
        :param value: Value of control parameter sto be set
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        self._write(name=self.cfg.set_operation_prefix+name, value=value)
        if self._read():
            raise Exception(f"ERROR: Couldn't properly write: {self.cfg.set_operation_prefix+name}={value} command to FPGA.")

    def set_reset(self, value, timeout=30):
        """
        Control the 'emu_rst' signal, in order to put the system running on the FPGA into or out of reset state.
        :param value: Value of reset signal, 1 will set it to reset and 0 will release reset.
        :param timeout: Maximum time granted for operation to finish
        """
        self.set_param(name= self.scfg.reset_ctrl.name, value=value, timeout=timeout)

    def get_emu_time_int(self, timeout=30):
        """
        Get current time of the FPGA simulation as an unscaled integer value.
        :param timeout: Maximum time granted for operation to finish
        """
        emu_time_vio = self.get_param(name=self.scfg.emu_time_vio.name, timeout=timeout)
        return int(emu_time_vio)

    def set_ctrl_mode(self, value, timeout=30):
        """
        Set the control mode that shall be applied to stall the FPGA simulation.
        :param value: Integer value setting the currently active control mode:
                        0:  FPGA simulation is not stalled
                        1:  FPGA simulation is immediately stalled
                        2:  FPGA simulation is stalled, after time stored in *ctrl_data* has passed, starting from
                            the point in time this mode has been selected.
                        3:  FPGA simulation is stalled, once time value stored in *ctrl_data* has been reached
        :param timeout: Maximum time granted for operation to finish
        """
        self.set_param(name=self.scfg.emu_ctrl_mode.name, value=value, timeout=timeout)

    ### Utility Functions

    def _initialize(self):
        """
        Initialize the control interface, this is usually done after the bitstream was programmed successfully on the FPGA.
        :return:
        """
        if self.cfg.comport is None:  # run auto search for finding the correct COM port
            # find all available COM ports
            comports = [port for port in ports.comports(include_links=True)]
            # check if any COM port is compliant to known vids and pids and if so store the device_id
            for port in comports:
                if ((port.vid in self.vid_list) and (port.pid in self.pid_list)):
                    self.port_list.append(port.device)

            for port in self.port_list:
                try:
                    self.ctrl_handler = serial.Serial(port, int(self.cfg.baud_rate), timeout=self.cfg.timeout,
                                                      parity=self.cfg.parity, stopbits=self.cfg.stopbits,
                                                      bytesize=self.cfg.bytesize)
                    self.cfg.comport = port
                except:
                    pass
            if self.cfg.comport is None:
                raise Exception(
                    f"ERROR: No COM port could be opened to enable connection to FPGA, found ports were: {self.port_list}.")

        else:
            try:
                self.ctrl_handler = serial.Serial(self.cfg.comport, int(self.cfg.baud_rate), timeout=self.cfg.timeout,
                                                  parity=self.cfg.parity, stopbits=self.cfg.stopbits,
                                                  bytesize=self.cfg.bytesize)
            except:
                raise Exception(f"ERROR: Provided COM port: {self.cfg.comport} could not ne opened for communication.")

    def _setup_ctrl(self, server_addr, *args, **kwargs):
        """
        Prepare instrumentation on the FPGA to allow interactive control.
        :param server_addr: Address of remote hardware server
        :return:
        """

        self.server_addr = server_addr

        # program the firmware
        XSCTEmulation(pcfg=self.pcfg,
                      content=self.content,
                      project_root=self.project_root,
                      top_module=self.top_module
                      ).program(server_addr=server_addr, *args, **kwargs)

    def _write(self, name, value=None):
        # check is space is in any of the give input strings
        if ' ' in [name, value]:
            raise Exception(f"Blanks in any of the provided argument strings;{name}, {value}; sent via control interface are not allowed!")
        if value is not None:
            self.ctrl_handler.write((f'{str(name)} {str(value)}\n'.encode('utf-8')))
        else:
            self.ctrl_handler.write((f'{str(name)}\n'.encode('utf-8')))
        self.ctrl_handler.flush()

    def _read(self, count=1):
        for idx in range(count):
            result = self.ctrl_handler.readline().decode('utf-8').rstrip()

            if result not in ['', None]:
                return int(result)
        raise Exception(f"ERROR: Couldn't read from FPGA after:{count} attempts.")

    def _setup_ila_ctrl(self, server_addr):
        """
        Prepare ILA instrumentation on the FPGA to allow interactive control.
        :param server_addr: Address of remote hardware server
        :return:
        """
        launch_script = os.path.join(os.path.dirname(os.path.dirname(self.result_path_raw)), r"launch_FPGA.tcl")
        codegen = CodeGenerator()
        codegen.use_templ(TemplLAUNCH_ILA_TCL(pcfg=self.pcfg, scfg=self.scfg,
                                               ltxfile_path=self.ltxfile_path, server_addr=server_addr))
        codegen.write_to_file(launch_script)
        self.source(script=launch_script)

    def __del__(self):
        """
        Close connection to shell.
        :return:
        """
        pass

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """
    def __init__(self, cfg_file):
        super().__init__(cfg_file=cfg_file, section=ConfigSections.FPGASIM)

        self.comport = None
        """ type(str) : Name of the COM port, that is attached to FPGA """

        self.baud_rate = 115200
        """ type(int): Baudrate used for communication with UART on FPGA """

        self.timeout = None
        """ type(int): Timeout in seconds used when waiting for a response during data transmission """

        self.parity = serial.PARITY_NONE
        """ type(str): Parity mode used for UART communication """

        self.stopbits=1
        """ type(int): Number of stop bits used when transmitting a package """

        self.bytesize=serial.EIGHTBITS
        """ type(int): Number of bits per transmitted package """

        self.set_operation_prefix='SET_'
        """ type(str): Default operator prefix added to every set operation."""

        self.get_operation_prefix = 'GET_'
        """ type(str): Default operator prefix added to every get operation."""

def main():
   ctrl = UARTCtrlApi(prj_cfg=EmuConfig(root='',cfg_file=''))
   ctrl.set_param(name=0, value=3)
   ctrl.set_param(name=1, value=4)
   print(ctrl.get_param(name=0))
   print(ctrl.get_param(name=1))

if __name__ == "__main__":
   main()