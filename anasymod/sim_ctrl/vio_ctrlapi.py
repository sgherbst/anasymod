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

SERVER_PORT = 57937

class VIOCtrlApi(CtrlApi):
    """
    Start an interactive control interface to HW target for running regression tests or design exploration/debug.
    For FPGA/Emulators, as a pre-requisit, bitstream must have been created and programmed. Additionally any eSW
    necessary in the targeted system must have already been programmed.
    """
    def __init__(self, scfg: StructureConfig, pcfg: EmuConfig, bitfile_path, ltxfile_path, cwd=None, prompt='Vivado% ', err_strs=None, debug=False):
        super().__init__()
        # set defaults
        if err_strs is None:
            err_strs = ['ERROR', 'FATAL']

        # save settings
        self.cwd = cwd
        self.prompt = prompt
        self.debug = debug
        self.err_strs = err_strs
        self.pcfg = pcfg
        self.scfg = scfg
        self.bitfile_path = bitfile_path
        self.ltxfile_path = ltxfile_path

    ### User Functions

    def sendline(self, line, timeout=float('inf')):
        """
        Send a single line in target shell specific language e.g. in tcl for tcl shell.
        :param line: Line that shall be send to/processed by shell
        :param timeout: Maximum time granted for operation to finish
        :return:
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
        :return:
        """
        script = Path(script).resolve()
        self.sendline(f'source {script}', timeout=timeout)
    
    def refresh_param(self, name, timeout=30):
        """
        Refresh selected control parameter.
        :param name: Name of control parameter
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        self.sendline(f'refresh_hw_vio {name}', timeout=timeout)

    def get_param(self, name, timeout=30):
        """
        Read value of a control parameter in design.
        :param name: Name of control parameter to be read
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        before = self.sendline(f'get_property INPUT_VALUE {name}', timeout=timeout)
        before = before.splitlines()[-1] # get last line
        before = before.strip() # strip off whitespace
        return before

    def set_param(self, name, value, timeout=30):
        """
        Set value of a control parameter in design.
        :param name: Name of control parameter to be set
        :param value: Value of control parameter sto be set
        :param timeout: Maximum time granted for operation to finish
        :return:
        """
        self.sendline(f'set_property OUTPUT_VALUE {value} {name}', timeout=timeout)
        self.sendline(f'commit_hw_vio {name}')

    def set_var(self, name, value):
        """
        Define a variable in target shell environment.
        :param name: Name of variable that shall be set
        :param value: Value of variable that shall be set
        :return:
        """
        self.sendline(f'set {name} {self._tcl_val(value)}')

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

        # Use pexpect under linux for interactive vivado ctrl
        if os.name == 'posix':
            from pexpect import spawn
        elif os.name == 'nt':
            from wexpect import spawn
        else:
            raise Exception(f'No supported OS was detected, supported OS for interactive control are windows and linux.')

        # start the interpreter
        print('Starting Vivado TCL interpreter.')
        sys.stdout.flush()
        cmd = 'vivado -nolog -nojournal -notrace -mode tcl'

        # Add vivado to PATH variable, in case of an inicio installation
        path = os.environ['PATH']
        #path = path + f';{self.pcfg.vivado_config.hints}'
        path = path + r';C:\Inicio\tools\64\Xilinx-18.2.0.3\Vivado\2018.2\bin'
        os.environ['PATH'] = path

        self.proc = spawn(command=cmd, cwd=self.cwd, env=os.environ)

        # wait for the prompt
        self._expect_prompt(timeout=300)

    def _setup_ctrl(self, server_addr):
        """
        Prepare instrumentation on the FPGA to allow interactive control.
        :param server_addr: Address of remote hardware server
        :return:
        """
        launch_script = r"launch_FPGA.tcl"
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
