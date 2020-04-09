class CtrlApi:
    """
    Start an interactive control interface to HW target for running regression tests or design exploration/debug.
    For FPGA/Emulators, as a pre-requisit, bitstream must have been created and programmed. Additionally any eSW
    necessary in the targeted system must have already been programmed.
    """
    def __init__(self):
        pass

    ### User Functions

    def sendline(self, line, timeout=float('inf')):
        """
        Send a single line in target shell specific language e.g. in tcl for tcl shell.
        :param line: Line that shall be send to/processed by shell
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def source(self, script, timeout=float('inf')):
        """
        Source a script written language for targeted shell.
        :param script: Name/Path to script that shall be sourced
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def setup_trace_unit(self, trigger_name, trigger_operator, trigger_value, sample_decimation=None, sample_count=None):
        """
        Setup the trace unit. This involves defining the signal, that shall be used to start tracing and defining the
        comparison operator, which is used to monitor the trigger signal.

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
        raise NotImplementedError("Base class was called to execute function")

    def arm_trace_unit(self):
        """
        Arm the trace unit, this will delete the buffer and arm the trigger.
        """
        raise NotImplementedError("Base class was called to execute function")

    def wait_on_and_dump_trace(self, result_file=None):
        """
        Wait until the trace unit stopped recording data. Transmit this data to the host PC, store by default to the raw
        result file path, or a custom path provided by the user, and convert analog values from fixed-point to float.
        Finally store it to a .vcd file in the default location.

        :param result_file: Optionally, it is possible to provide a custom result file path.
        """
        raise NotImplementedError("Base class was called to execute function")

    def refresh_param(self, name, timeout=30):
        """
        Refresh selected control parameter.
        :param name: Name of control parameter
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def get_param(self, name, timeout=30):
        """
        Read value of a control parameter in design.
        :param name: Name of control parameter to be read
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def set_param(self, name, value, timeout=30):
        """
        Set value of a control parameter in design.
        :param name: Name of control parameter to be set
        :param value: Value of control parameter sto be set
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def set_var(self, name, value):
        """
        Define a variable in target shell environment.
        :param name: Name of variable that shall be set
        :param value: Value of variable that shall be set
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def set_reset(self, value, timeout=30):
        """
        Control the 'emu_rst' signal, in order to put the system running on the FPGA into or out of reset state.
        :param value: Value of reset signal, 1 will set it to reset and 0 will release reset.
        :param timeout: Maximum time granted for operation to finish
        """
        raise NotImplementedError("Base class was called to execute function")

    ### Utility Functions

    def _initialize(self):
        """
        Initialize the control interface, this is usually done after the bitstream was programmed successfully on the FPGA.
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def _setup_ctrl(self, server_addr):
        """
        Prepare instrumentation on the FPGA to allow interactive control.
        :param server_addr: Address of remote hardware server
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def _expect_prompt(self, timeout=float('inf')):
        """
        Wait for the shell used to transmit commands to provide a response.
        :param timeout: Maximum time granted for shell to open
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")


    def __del__(self):
        """
        Close connection to shell.
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")