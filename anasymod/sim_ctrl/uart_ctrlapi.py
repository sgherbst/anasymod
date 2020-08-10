import serial
import serial.tools.list_ports as ports
from anasymod.enums import CtrlOps
from anasymod.base_config import BaseConfig
from anasymod.sim_ctrl.ctrlapi import CtrlApi
from anasymod.enums import ConfigSections
from anasymod.config import EmuConfig


class UARTCtrlApi(CtrlApi):
    """
    Start an interactive control interface to HW target for running regression tests or design exploration/debug.
    For FPGA/Emulators, as a pre-requisit, bitstream must have been created and programmed. Additionally any eSW
    necessary in the targeted system must have already been programmed.
    """
    def __init__(self, prj_cfg: EmuConfig):
        super().__init__()

        # Initialize control config
        self.cfg = Config(cfg_file=prj_cfg.cfg_file)

        # Save UART identification settings
        self.uart_vid = prj_cfg.board.uart_vid
        self.uart_pid = prj_cfg.board.uart_pid
        self.uart_suffix = prj_cfg.board.uart_suffix

        # Initialize port_list
        self.port_list = []

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
        self._write(operation=CtrlOps.READ_PARAMETER, name=name)
        return self._read()

    def set_param(self, name, value, timeout=30):
        """
        Set value of a control parameter in design.
        :param name: Name of control parameter to be set
        :param value: Value of control parameter sto be set
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        self._write(operation=CtrlOps.WRITE_PARAMETER, name=name, value=value)
        if self._read():
            raise Exception(f"ERROR: Couldn't properly write: {name}={value} command to FPGA.")

    def set_var(self, name, value):
        """
        Define a variable in target shell environment.
        :param name: Name of variable that shall be set
        :param value: Value of variable that shall be set
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    ### Utility Functions

    def _initialize(self):
        """
        Initialize the control interface, this is usually done after the bitstream was
        programmed successfully on the FPGA.
        :return:
        """

        if self.cfg.comport is None:  # run auto search for finding the correct COM port
            # find all available COM ports
            comports = [port for port in ports.comports(include_links=True)]

            # check if any COM port is compliant to known vids and pids and if so store the device_id
            for port in comports:
                # filter out ports not matching VID (if provided)
                if (self.uart_vid is not None) and (port.vid != self.uart_vid):
                    continue
                # filter out ports not matching PID (if provided)
                if (self.uart_pid is not None) and (port.pid != self.uart_pid):
                    continue
                # filter out ports not matching location (if provided)
                if (self.uart_suffix is not None) and (not port.location.endswith(self.uart_suffix)):
                    continue
                # if we get to this point, then all of the provided tests passed,
                # so we can add the port to the port_list
                self.port_list.append(port.device)

            # indicate the specific error condition of no matching ports,
            # to better communicate the problem to the user
            if len(self.port_list) == 0:
                raise Exception('Did not find any matching COM ports.')

            # print a warning if multiple matching COM ports are detected,
            # since it's possible that the wrong one will be selected if
            # more than one can connect through PySerial
            if len(self.port_list) > 1:
                print('WARNING: Multiple COM ports matched search criteria, '
                      'will use the first one that can successfully connect.')

            # iterate through the matching ports, printing out each attempt
            for port in self.port_list:
                try:
                    print(f'Trying to open {port} ... ', end='')
                    self.ctrl_handler = self._open_serial_connection(port)
                    self.cfg.comport = port
                    print('success.')
                    break
                except:
                    print('failed.')
            else:
                raise Exception('ERROR: None of the matching COM ports could be opened.')
        else:
            try:
                self.ctrl_handler = self._open_serial_connection(self.cfg.comport)
            except:
                raise Exception(f"ERROR: Provided COM port: {self.cfg.comport} could not be "
                                f"opened for communication.")

    def _open_serial_connection(self, port):
        return serial.Serial(port, int(self.cfg.baud_rate), timeout=self.cfg.timeout,
                             parity=self.cfg.parity, stopbits=self.cfg.stopbits,
                             bytesize=self.cfg.bytesize)

    def _setup_ctrl(self, server_addr):
        """
        Prepare instrumentation on the FPGA to allow interactive control.  Does not currently
        do anything for the UART controller.
        :param server_addr: Address of remote hardware server
        :return:
        """
        pass

    def _expect_prompt(self, timeout=float('inf')):
        """
        Wait for the shell used to transmit commands to provide a response.
        :param timeout: Maximum time granted for shell to open
        :return:
        """
        raise NotImplementedError("Base class was called to execute function")

    def _write(self, operation, name, value=None):
        # check is space is in any of the give input strings
        if ' ' in [operation, name, value]:
            raise Exception(f"Blanks in any of the provided argument strings;{operation}, "
                            f"{name}, {value}; sent via control interface are not allowed!")

        self.ctrl_handler.write((' '.join([str(operation), str(name), str(value) + '\r']).encode('utf-8')))
        self.ctrl_handler.flush()

    def _read(self, count=1):
        for idx in range(count):
            result = self.ctrl_handler.readline()

            if result not in ['', None]:
                return int(result.decode("utf-8").rstrip())
        raise Exception(f"ERROR: Couldn't read from FPGA after:{count} attempts.")


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

        self.timeout = 30
        """ type(int): Timeout in seconds used when waiting for a response during data transmission """

        self.parity = serial.PARITY_NONE
        """ type(str): Parity mode used for UART communication """

        self.stopbits=1
        """ type(int): Number of stop bits used when transmitting a package """

        self.bytesize=serial.EIGHTBITS
        """ type(int): Number of bits per transmitted package """

def main():
   ctrl = UARTCtrlApi(prj_cfg=EmuConfig(root='',cfg_file=''))
   ctrl.set_param(name=0, value=3)
   ctrl.set_param(name=1, value=4)
   print(ctrl.get_param(name=0))
   print(ctrl.get_param(name=1))

if __name__ == "__main__":
   main()