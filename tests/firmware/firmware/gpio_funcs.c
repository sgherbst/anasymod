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

void set_a_in(u32 val){
    set_value(4, val);
}

void set_b_in(u32 val){
    set_value(5, val);
}

void set_mode_in(u32 val){
    set_value(6, val);
}

u32 get_c_out(u32 val){
    return get_value(1);
}
