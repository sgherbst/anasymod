import serial
import io
import serial.tools.list_ports as ports
from anasymod.enums import CtrlOps

class UARTControl():
    def __init__(self, comport=None, baud_rate=None, timeout=None, parity=None, stopbits=None, bytesize=None):
        self.comport = None

        # Initialize internal variables
        vid_list = [1027]
        pid_list = [24592]
        port_list = []

        # Initialize parameters
        self.baud_rate = 115200 if baud_rate is None else baud_rate
        self.timeout = None if timeout is None else timeout
        self.parity = serial.PARITY_NONE if parity is None else parity
        self.stopbits = 1 if stopbits is None else stopbits
        self.bytesize = serial.EIGHTBITS if bytesize is None else bytesize

        if comport is None: # run auto search for finding the correct COM port
            # find all available COM ports
            comports = [port for port in ports.comports(include_links=True)]
            # check if any COM port is compliant to known vids and pids and if so store the device_id
            for port in comports:
                if ((port.vid in vid_list) and (port.pid in pid_list)):
                    port_list.append(port.device)

            for port in port_list:
                try:
                    self._init_handler(comport=port)
                except:
                    pass
            if self.comport is None:
                raise Exception(f"ERROR: No COM port could be opened to enable connection to FPGA, found ports were: {port_list}.")

        else:
            try:
                self._init_handler(comport=comport)
            except:
                raise Exception(f"ERROR: Provided COM port: {comport} could not ne opened for communication.")

    def _init_handler(self, comport):
        self.ctrl_handler = serial.Serial(comport, int(self.baud_rate), timeout=self.timeout, parity=self.parity, stopbits=self.stopbits,
                                         bytesize=self.bytesize)
        self.comport = comport

    def _write(self, operation, addr, data=None):
        # check is space is in any of the give input strings
        if ' ' in [operation, addr, data]:
            raise Exception(f"Blanks in any of the provided argument strings;{operation}, {addr}, {data}; sent via control interface are not allowed!")

        self.ctrl_handler.write((' '.join([str(operation), str(addr), str(data) + '\r']).encode('utf-8')))
        self.ctrl_handler.flush()

    def _read(self, count=1):
        for idx in range(count):
            result = self.ctrl_handler.readline()

            if result not in ['', None]:
                return int(result.decode("utf-8").rstrip())
        raise Exception(f"ERROR: Couldn't read from FPGA after:{count} attempts.")


    def write_parameter(self, addr, data):
        self._write(operation=CtrlOps.WRITE_PARAMETER, addr=addr, data=data)
        if self._read():
            raise Exception(f"ERROR: Couldn't properly write: {addr}={data} command to FPGA.")


    def read_parameter(self, addr):
        self._write(operation=CtrlOps.READ_PARAMETER, addr=addr)
        return self._read()

ctrl = UARTControl()
ctrl.write_parameter(addr=0, data=3)
ctrl.write_parameter(addr=1, data=4)
print(ctrl.read_parameter(addr=0))
print(ctrl.read_parameter(addr=1))
print('hier weiter')