import sys, os
import time
from numbers import Number
from pathlib import Path
from .console_print import cprint_block, cprint_block_start, cprint_block_end
from anasymod.sim_ctrl.ctrlapi import CtrlApi
from anasymod.generators.gen_api import CodeGenerator
from anasymod.templates.launch_FPGA_sim import TemplLAUNCH_FPGA_SIM
from anasymod.structures.structure_config import StructureConfig
from anasymod.config import EmuConfig
from anasymod.enums import TraceUnitOperators
from anasymod.sim_ctrl.datatypes import AnalogProbe, DigitalSignal
from anasymod.wave import ConvertWaveform

SERVER_PORT = 57937

class VIOCtrlApi(CtrlApi):
    """
    Start an interactive control interface to HW target for running regression tests or design exploration/debug.
    For FPGA/Emulators, as a pre-requisit, bitstream must have been created and programmed. Additionally any eSW
    necessary in the targeted system must have already been programmed.
    """
    def __init__(self, result_path_raw, result_type_raw, result_path, scfg: StructureConfig, pcfg: EmuConfig,
                 bitfile_path, ltxfile_path, cwd=None, prompt='Vivado% ', err_strs=None, debug=False, float_type=False):
        super().__init__()
        # set defaults
        if err_strs is None:
            err_strs = ['ERROR', 'FATAL']

        self.result_path_raw = result_path_raw
        self.result_type_raw = result_type_raw
        self.result_path = result_path
        self.pcfg = pcfg
        self.scfg = scfg
        self.float_type = float_type

        # save settings
        self.cwd = cwd
        self.prompt = prompt
        self.debug = debug
        self.err_strs = err_strs
        self.bitfile_path = bitfile_path
        self.ltxfile_path = ltxfile_path

        # create dictionary of analog control I/O
        # TODO: is there a better way to access this information?
        self.analog_ctrl_outputs = {elem.name: elem for elem in self.scfg.analog_ctrl_outputs}
        self.analog_ctrl_inputs = {elem.name: elem for elem in self.scfg.analog_ctrl_inputs}

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

        return before

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
                                    depth defined during project setup.
        """

        trigger_obj = None

        window_count = self.pcfg.ila_depth if sample_count is None else sample_count
        window_count = window_count / 2

        # Check, if provided tirgger_signal is a valid signal connected to the ILA
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
            trigger_value_int = f"{int(trigger_obj.width)}'u{value_int}"
        elif isinstance(trigger_obj, DigitalSignal):
            if isinstance(trigger_value, int):
                trigger_value_int = f"{trigger_obj.width}'u{trigger_value}"
            else:
                p = set(trigger_value)
                s = {'0', '1'}

                if s == p or p == {'0'} or p == {'1'}:
                    trigger_value_int = f"{trigger_obj.width}'b{trigger_value}"
                else:
                    raise Exception(f'ERROR: Provided trigger value:{trigger_value} is not valid for a digital trigger '
                                    f'signal, either provide and interger or binary string!')
        else:
            raise Exception(f'ERROR: No valid signal type for provided trigger signal:{trigger_name} Type:{type(trigger_obj)}')

        self.sendline(f'set_property CONTROL.CAPTURE_MODE BASIC $ila_0_i')
        self.sendline(f'set_property CONTROL.TRIGGER_POSITION 0 $ila_0_i')
        self.sendline(f"set_property TRIGGER_COMPARE_VALUE {trigger_operator}{trigger_value_int} [get_hw_probes trace_port_gen_i/{trigger_obj.name} -of_objects $ila_0_i]")

        # Data depth is set to 2, as 1 is not supported by Vivado's ILA Core
        self.sendline(f'set_property CONTROL.DATA_DEPTH 2 $ila_0_i')

        # Window count is set to half of the selected ILA depth
        self.sendline(f'set_property CONTROL.WINDOW_COUNT {int(window_count)} $ila_0_i')
        self.sendline(f"set_property CAPTURE_COMPARE_VALUE eq1'b1 [get_hw_probes trace_port_gen_i/emu_dec_cmp -of_objects $ila_0_i]")

        # Set decimation threshold signal to value defined in sample_decimation if set
        if sample_decimation:
            if isinstance(sample_decimation, int): # Check if sample_decimation is an integer
                self.set_param(name=self.scfg.dec_thr_ctrl.name, value=sample_decimation, timeout=30)
            else:
                raise Exception(f'Provided sample_decimation value is of wrong type, expecting integer and got:{type(sample_decimation)}')

        self.arm_trace_unit()

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

        # wait until trace buffer is full
        self.sendline('wait_on_hw_ila $ila_0_i')

        # transmit and dump trace buffer data to a CSV file
        self.sendline('current_hw_ila_data [upload_hw_ila_data $ila_0_i]')
        self.sendline(f'write_hw_ila_data -csv_file -force {{{self.result_path_raw if result_file is None else result_file}}} [current_hw_ila_data]')

        # Convert to .vcd and from fixed-point to float
        ConvertWaveform(result_path_raw=self.result_path_raw,
                        result_type_raw=self.result_type_raw,
                        result_path=self.result_path,
                        str_cfg=self.scfg,
                        float_type=self.float_type)

    def refresh_param(self, name, timeout=30):
        """
        Refresh selected control parameter.
        :param name: Name of control parameter
        :param timeout: Maximum time granted for operation to finish
        """
        self.sendline(f'refresh_hw_vio ${name}', timeout=timeout)

    def get_param(self, name, timeout=30):
        """
        Read value of a control parameter in design.
        :param name: Name of control parameter to be read
        :param timeout: Maximum time granted for operation to finish
        """
        # get output result as a string
        value = self.sendline(f'get_property INPUT_VALUE ${name}', timeout=timeout)
        value = value.splitlines()[-1] # get last line
        value = value.strip() # strip off whitespace

        # convert value to floating-point if needed
        if name in self.analog_ctrl_outputs:
            value = self.analog_ctrl_outputs[name].fixed_to_float(int(value))

        # return value
        return value

    def set_param(self, name, value, timeout=30):
        """
        Set value of a control parameter in design.
        :param name: Name of control parameter to be set
        :param value: Value of control parameter sto be set
        :param timeout: Maximum time granted for operation to finish
        """
        # convert value to fixed-point if needed
        if name in self.analog_ctrl_inputs:
            value = self.analog_ctrl_inputs[name].float_to_fixed(value)

        # send command
        self.sendline(f'set_property OUTPUT_VALUE {value} ${name}', timeout=timeout)
        self.sendline(f'commit_hw_vio ${name}')

    def set_var(self, name, value):
        """
        Define a variable in target shell environment.
        :param name: Name of variable that shall be set
        :param value: Value of variable that shall be set
        """
        self.sendline(f'set {name} {self._tcl_val(value)}')

    def set_reset(self, value, timeout=30):
        """
        Control the 'emu_rst' signal, in order to put the system running on the FPGA into or out of reset state.
        :param value: Value of reset signal, 1 will set it to reset and 0 will release reset.
        :param timeout: Maximum time granted for operation to finish
        """
        self.set_param(name=self.scfg.reset_ctrl.name, value=value, timeout=timeout)

    def set_ctrl_mode(self, value, timeout=30):
        self.set_param(name=self.scfg.emu_ctrl_mode.name, value=value, timeout=timeout)

    def set_ctrl_data(self, value, timeout=30):
        self.set_param(name=self.scfg.emu_ctrl_data.name, value=value, timeout=timeout)

    def stall_emu(self, timeout=30):
        self.set_ctrl_mode(1, timeout=timeout)

    def get_emu_time_int(self, timeout=30):
        self.refresh_param('vio_0_i')
        emu_time_vio = self.get_param(name=self.scfg.emu_time_vio.name, timeout=timeout)
        return int(emu_time_vio)

    def get_emu_time(self, timeout=30):
        return self.get_emu_time_int(timeout=timeout) * self.pcfg.cfg.dt_scale

    def sleep_emu(self, t, timeout=30):
        # stall
        self.stall_emu()

        # set up in sleep mode
        t_next = t + self.get_emu_time(timeout=timeout)
        t_next_int = int(round(t_next / self.pcfg.cfg.dt_scale))
        self.set_ctrl_data(t_next_int)
        self.set_ctrl_mode(2)

        # wait for enough time to pass
        while(self.get_emu_time_int() < t_next_int):
            pass

    ### Utility Functions

    @classmethod
    def _tcl_val(cls, value):
        if isinstance(value, (list, tuple)):
            return '[list ' + ' '.join(cls._tcl_val(elem) for elem in value) + ']'
        elif isinstance(value, str):
            return '"' + value + '"'
        elif isinstance(value, Path):
            return cls._tcl_val(str(value))
        elif isinstance(value, Number):
            return str(value)
        else:
            raise Exception(f"Don't know how to convert to a TCL literal: {value}.")

    def _initialize(self):
        """
        Initialize the control interface, this is usually done after the bitstream was programmed successfully on the FPGA.
        :return:
        """

        # log current status
        print('Starting Vivado TCL interpreter.')
        sys.stdout.flush()

        # construct the command to launch Vivado
        cmd = 'vivado '
        cmd += self.pcfg.vivado_config.lsf_opts_ls + ' '
        cmd += '-nolog -nojournal -notrace -mode tcl'

        # Use pexpect under linux for interactive vivado ctrl
        if os.name == 'posix':
            # Add Vivado to the path using the Windows PATH separator (semicolon)
            # A copy of the environment is made to avoid side effects outside this function
            # TODO: do this only if needed
            env = os.environ.copy()
            env['PATH'] += f':{os.path.dirname(self.pcfg.vivado_config.vivado)}'
            # Launch Vivado
            from pexpect import spawnu
            self.proc = spawnu(command=cmd, cwd=self.cwd, env=env)
        elif os.name == 'nt':
            # Add Vivado to the path using the Windows PATH separator (semicolon)
            # A copy of the environment is made to avoid side effects outside this function
            # TODO: do this only if needed
            env = os.environ.copy()
            env['PATH'] += f';{os.path.dirname(self.pcfg.vivado_config.vivado)}'
            os.environ['WEXPECT_SPAWN_CLASS'] = 'SpawnPipe'
            # Launch Vivado
            try:
                # import patched wexpect from Inicio installation
                from site_pip_packages.wexpect import spawn
            except:
                from wexpect import spawn
            self.proc = spawn(command=cmd, cwd=self.cwd, env=env)
        else:
            raise Exception(f'No supported OS was detected, supported OS for interactive control are windows and linux.')

        # wait for the prompt
        self._expect_prompt(timeout=300)

    def _setup_ctrl(self, server_addr):
        """
        Prepare instrumentation on the FPGA to allow interactive control.
        :param server_addr: Address of remote hardware server
        :return:
        """
        launch_script = os.path.join(os.path.dirname(os.path.dirname(self.result_path_raw)), r"launch_FPGA.tcl")
        codegen = CodeGenerator()
        codegen.use_templ(TemplLAUNCH_FPGA_SIM(pcfg=self.pcfg, scfg=self.scfg, bitfile_path=self.bitfile_path,
                                               ltxfile_path=self.ltxfile_path, server_addr=server_addr))
        codegen.write_to_file(launch_script)
        self.source(script=launch_script)

    def _expect_prompt(self, timeout=float('inf')):
        before = ''
        start_time = time.time()
        lines_recv = 0
        while (time.time() - start_time) < timeout:
            remaining = timeout - (time.time() - start_time)
            if remaining == float('inf'):
                remaining = None
            index = self.proc.expect(['\n', self.prompt], timeout=remaining)
            if index == 0:
                before += self.proc.before + '\n'
                lines_recv += 1
                if self.debug:
                    if lines_recv == 2:
                        cprint_block_start('RECV', 'cyan')
                    if lines_recv >= 2:
                        print(self.proc.before)
            else:
                break
        if self.debug and lines_recv >= 2:
            cprint_block_end('RECV', 'cyan')
        return before

    def __del__(self):
        try:
            print('Sending "exit" to Vivado TCL interpreter.')
            self.proc.sendline('exit')
        except:
            print('Could not send "exit" to Vivado TCL interpreter.')

def get_vivado_tcl_client():
    import xmlrpc.client
    return xmlrpc.client.ServerProxy(f'http://localhost:{SERVER_PORT}')

def main():
    # modified from https://docs.python.org/3.7/library/xmlrpc.server.html?highlight=xmlrpc
    print(f'Launching Vivado TCL server on port {SERVER_PORT}.')

    from xmlrpc.server import SimpleXMLRPCServer
    from xmlrpc.server import SimpleXMLRPCRequestHandler

    # Restrict to a particular path.
    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)

    # Instantiate TCL evaluator
    tcl = VIOCtrlApi()

    # Create server
    with SimpleXMLRPCServer(('localhost', SERVER_PORT),
                            requestHandler=RequestHandler,
                            allow_none=True) as server:
        server.register_introspection_functions()

        # list of functions available to the client
        server.register_function(tcl.sendline)
        server.register_function(tcl.source)
        server.register_function(tcl.refresh_param)
        server.register_function(tcl.set_param)
        server.register_function(tcl.get_param)

        # program not progress past this point unless
        # Ctrl-C or similar is pressed.
        server.serve_forever()

if __name__ == '__main__':
    main()
