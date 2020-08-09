import serial, os
import serial.tools.list_ports as ports
from anasymod.base_config import BaseConfig
from anasymod.sim_ctrl.ctrlapi import CtrlApi
from anasymod.enums import ConfigSections
from anasymod.config import EmuConfig
from anasymod.structures.structure_config import StructureConfig
from anasymod.emu.xsct_emu import XSCTEmulation


class UARTCtrlApi(CtrlApi):
    """
    Start an interactive control interface to HW target for running regression tests or design exploration/debug.
    For FPGA/Emulators, as a pre-requisit, bitstream must have been created and programmed. Additionally any eSW
    necessary in the targeted system must have already been programmed.
    """
    def __init__(self, prj_cfg: EmuConfig, scfg: StructureConfig, content, project_root, top_module):
        super().__init__(pcfg=prj_cfg, scfg=scfg)

        self.content = content
        self.project_root = project_root
        self.top_module = top_module

        # Initialize control config
        self.cfg = Config(cfg_file=prj_cfg.cfg_file)

        self.vid_list = self.pcfg.board.uart_zynq_vid
        self.pid_list = self.pcfg.board.uart_zynq_pid
        self.port_list = []
    ### User Functions

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
        self.set_param(name= self.cfg.set_operation_prefix+self.scfg.reset_ctrl.name, value=value, timeout=timeout)

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

        self.ctrl_handler.write((' '.join([str(name), str(value) + '\r']).encode('utf-8')))
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