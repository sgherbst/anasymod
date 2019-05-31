/******************************************************************************
*
* Copyright (C) 2009 - 2014 Xilinx, Inc.  All rights reserved.
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in
* all copies or substantial portions of the Software.
*
* Use of the Software is limited solely to applications:
* (a) running on a Xilinx device, or
* (b) that interact with a Xilinx device through a bus or interconnect.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
* XILINX  BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
* WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
* OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
*
* Except as contained in this notice, the name of the Xilinx shall not be used
* in advertising or otherwise to promote the sale, use or other dealings in
* this Software without prior written authorization from Xilinx.
*
******************************************************************************/

/*
 * helloworld.c: simple test application
 *
 * This application configures UART 16550 to baud rate 9600.
 * PS7 UART (Zynq) is not initialized by this application, since
 * bootrom/bsp configures it to baud rate 115200
 *
 * ------------------------------------------------
 * | UART TYPE   BAUD RATE                        |
 * ------------------------------------------------
 *   uartns550   9600
 *   uartlite    Configurable only in HW design
 *   ps7_uart    115200 (configured by bootrom/bsp)
 */

#include <stdio.h>
#include <stdlib.h>
#include "platform.h"
#include "xil_printf.h"
#include "xparameters.h"
#include <xgpio.h>

#define MAX_CHAR_LEN 10000

// global variable
XGpio gpio_i;
XGpio gpio_o;

void initialize(){
	/*
	 * Initialization required prior to using I/O routines.
	 */

	XGpio_Initialize(&gpio_i, XPAR_AXI_GPIO_0_DEVICE_ID);
	XGpio_Initialize(&gpio_o, XPAR_AXI_GPIO_1_DEVICE_ID);
	init_platform();
}

void get_input( char *cmd_string){
	int len = 0;
	char ch;
	while ((ch = getchar()) != '\r'){
		cmd_string[len] = ch;
		len ++;
	}
	cmd_string[len] = '\0';
}

int main()
{
	initialize();

    //print("Hello World\n\r");

    char cmd_string[MAX_CHAR_LEN] = "";
    int cmd = 42;
    char name[50] = "";
    char value[50] = "";

    do{
    	//printf("Provide command \n");
    	get_input(cmd_string);
    	//printf("read line:%s\n", cmd_string);

    	sscanf( cmd_string, "%d %s %s", &cmd, name, value);
    	//printf("Cmd:%d, Name:%s, Value:%s.\n", cmd, name, value);

    	//interpreter
    	switch (cmd) {

    	   case 0  :
    		   printf("Writing... value:%s to parameters:%s.", value, name);
    		   putchar('\n');
    		   break;

    	   case 1  :
    		   printf("Reading... parameter:%s.", name);
    		   putchar('\n');
    		   break;

    	   default :
    		   printf("Default.");
    		   putchar('\n');
    	}
    }while(TRUE);

    cleanup_platform();
    return 0;
}
