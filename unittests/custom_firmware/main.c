
#include "gpio_funcs.h"
#include <stdio.h>
#include <string.h>
#include "sleep.h"

#define SET_emu_rst 0
#define SET_emu_dec_thr 1
#define SET_emu_ctrl_data 2
#define SET_emu_ctrl_mode 3
#define SET_a_in 4
#define SET_b_in 5
#define SET_mode_in 6
#define GET_c_out 7

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

                    } else if (strcmp(buf, "SET_emu_rst") == 0) {
                        cmd = SET_emu_rst;
                        nargs++;

                    } else if (strcmp(buf, "SET_emu_dec_thr") == 0) {
                        cmd = SET_emu_dec_thr;
                        nargs++;

                    } else if (strcmp(buf, "SET_emu_ctrl_data") == 0) {
                        cmd = SET_emu_ctrl_data;
                        nargs++;

                    } else if (strcmp(buf, "SET_emu_ctrl_mode") == 0) {
                        cmd = SET_emu_ctrl_mode;
                        nargs++;

                    } else if (strcmp(buf, "SET_a_in") == 0) {
                        cmd = SET_a_in;
                        nargs++;

                    } else if (strcmp(buf, "SET_b_in") == 0) {
                        cmd = SET_b_in;
                        nargs++;

                    } else if (strcmp(buf, "SET_mode_in") == 0) {
                        cmd = SET_mode_in;
                        nargs++;

                    } else if (strcmp(buf, "GET_c_out") == 0) {
                        xil_printf("%0d\r\n", get_c_out());
                        nargs = 0;

                    } else {
                        xil_printf("ERROR: Unknown command\r\n");
                    }
                } else if (nargs == 1) {
                    sscanf(buf, "%lu", &arg1);

                    if (cmd == SET_emu_rst) {
                        set_emu_rst(arg1)
;

                        xil_printf("0\r\n");

                    } else if (cmd == SET_emu_dec_thr) {
                        set_emu_dec_thr(arg1)
;

                        xil_printf("0\r\n");

                    } else if (cmd == SET_emu_ctrl_data) {
                        set_emu_ctrl_data(arg1)
;

                        xil_printf("0\r\n");

                    } else if (cmd == SET_emu_ctrl_mode) {
                        set_emu_ctrl_mode(arg1)
;

                        xil_printf("0\r\n");

                    } else if (cmd == SET_a_in) {
                        set_a_in(arg1)
;

                        xil_printf("0\r\n");

                    } else if (cmd == SET_b_in) {
                        set_b_in(arg1)
;

                        xil_printf("0\r\n");

                    } else if (cmd == SET_mode_in) {
                        set_mode_in(arg1)
;

                        xil_printf("0\r\n");

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
