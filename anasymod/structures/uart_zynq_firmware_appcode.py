class UartZynqFirmwareAppCode:
    def __init__(self, scfg):
        crtl_inputs = scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        ctrl_outputs = scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs

        self.getter_dict = {}
        for probe in ctrl_outputs:
            if probe.o_addr is not None:
                self.getter_dict[probe.o_addr] = probe.name

        self.setter_dict = {}
        for param in crtl_inputs:
            if param.i_addr is not None:
                self.setter_dict[param.i_addr] = param.name

        self.src_text = self.gen_src_text()

    def gen_src_text(self):
        retval = '''
#include "gpio_funcs.h"
#include <stdio.h>
#include <string.h>
#include "sleep.h"
'''

        idx = 0

        # add setter defines
        for k, v in self.setter_dict.items():
            retval += f'''
#define SET_{v} {idx}'''
            idx += 1

        # add getter defines
        for k, v in self.getter_dict.items():
            retval += f'''
#define GET_{v} {idx}'''
            idx += 1

        # add default body 1
        retval += r'''

int main() {
    // character buffering
    u32 idx = 0;
    char rcv;
    char buf [32];
    
    // command processing;
    u32 cmd;
    u32 arg1;
    u32 nargs = 0;

    if (init_GPIO() != 0) {
        xil_printf("GPIO Initialization Failed\r\n");
        return XST_FAILURE;
    }

    while (1) {
        rcv = inbyte();
        if ((rcv == ' ') || (rcv == '\t') || (rcv == '\r') || (rcv == '\n')) {
            // whitespace
            if (idx > 0) {
                buf[idx++] = '\0';
                if (nargs == 0) {
                    if (strcmp(buf, "HELLO") == 0) {
                        xil_printf("Hello World!\r\n");
                        nargs = 0;
                    } else if (strcmp(buf, "EXIT") == 0) {
                        return 0;
'''

        #add cmd interpreter for setters
        for k, v in self.setter_dict.items():
            retval += f'''
                    }} else if (strcmp(buf, "SET_{v}") == 0) {{
                        cmd = SET_{v};
                        nargs++;
'''

        # add cmd interpreter for getters
        for k, v in self.getter_dict.items():
            retval += f'''
                    }} else if (strcmp(buf, "GET_{v}") == 0) {{
                        xil_printf("%0d\\r\\n", get_{v}());
                        nargs = 0;
'''

        # add default body 2
        retval += r'''
                    } else {
                        xil_printf("ERROR: Unknown command\r\n");
                    }
                } else if (nargs == 1) {
                    sscanf(buf, "%lu", &arg1);
'''

        # add setter argument reader
        cond_str = 'if'
        for k, v in self.setter_dict.items():
            retval += f'''
                    {cond_str} (cmd == SET_{v}) {{
                        set_{v}(arg1)\n;
''' + \
r'''                      
                        xil_printf("0\r\n");
'''
            cond_str = '} else if'

        # add default body 3
        retval += '''
                    }
                    nargs = 0;
                }
            }
            idx = 0;
        } else {
            // load next character
            buf[idx++] = rcv;
        }
    }

    return 0;
}  
'''

        # return the code
        return retval