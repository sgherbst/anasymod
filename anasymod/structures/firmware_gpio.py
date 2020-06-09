class FirmwareGPIO:
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

        self.hdr_text = self.gen_hdr_text()
        self.src_text = self.gen_src_text()

    def gen_hdr_text(self):
        retval = '''
#include "xgpio.h"

int init_GPIO();
'''

        # add setter declarations
        for k, v in self.setter_dict.items():
            retval += f'''
void set_{v}(u32 val);
'''

        # add setter declarations
        for k, v in self.getter_dict.items():
            retval += f'''
u32 get_{v}();
'''

        # return the code
        return retval

    def gen_src_text(self):
        retval = '''
#include "xparameters.h"
#include "xgpio.h"
#include "sleep.h"

XGpio Gpio0; // chan 1: o_ctrl, chan 2: o_data
XGpio Gpio1; // chan 1: i_ctrl, chan 2: i_data

int init_GPIO(){
    int status0, status1;
    status0 = XGpio_Initialize(&Gpio0, XPAR_GPIO_0_DEVICE_ID);
    status1 = XGpio_Initialize(&Gpio1, XPAR_GPIO_1_DEVICE_ID);
    if ((status0 == XST_SUCCESS) && (status1 == XST_SUCCESS)) {
        return 0;
    } else {
        return 1;
    }
}

u32 get_value(u32 addr){
    XGpio_DiscreteWrite(&Gpio0, 1, addr);
    usleep(1);
    return XGpio_DiscreteRead(&Gpio0, 2);
}

void set_value(u32 addr, u32 val){
    // set address and data
    XGpio_DiscreteWrite(&Gpio1, 1, addr);
    XGpio_DiscreteWrite(&Gpio1, 2, val);
    usleep(1);

    // assert "valid"
    XGpio_DiscreteWrite(&Gpio1, 1, addr | (1UL << 30));
    usleep(1);

    // de-assert "valid"
    XGpio_DiscreteWrite(&Gpio1, 1, addr);
    usleep(1);
}
'''

        # add setter definitions
        for k, v in self.setter_dict.items():
            retval += f'''
void set_{v}(u32 val){{
    set_value({k}, val);
}}
'''

        # add setter definitions
        for k, v in self.getter_dict.items():
            retval += f'''
u32 get_{v}(){{
    return get_value({k});
}}
'''
        # return the code
        return retval