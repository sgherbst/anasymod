#include "gpio_funcs.h"
#include <stdio.h>
#include <string.h>
#include "sleep.h"

#define SET_A 1
#define SET_B 2
#define SET_MODE 3
#define GET_C 4

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
                    } else if (strcmp(buf, "SET_A") == 0) {
                        cmd = SET_A;
                        nargs++;
                    } else if (strcmp(buf, "SET_B") == 0) {
                        cmd = SET_B;
                        nargs++;
                    } else if (strcmp(buf, "SET_MODE") == 0) {
                        cmd = SET_MODE;
                        nargs++;
                    } else if (strcmp(buf, "GET_C") == 0) {
                        xil_printf("%0d\r\n", get_c_out());
                        nargs = 0;
                    } else {
	                    xil_printf("ERROR: Unknown command\r\n");
                    }
                } else if (nargs == 1) {
                    sscanf(buf, "%lu", &arg1);
                    if (cmd == SET_A) {
                        set_a_in(arg1);
                    } else if (cmd == SET_B) {
                        set_b_in(arg1);
                    } else if (cmd == SET_MODE) {
                        set_mode_in(arg1);
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
