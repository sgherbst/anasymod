# anasymod

## Requirements
1. Python
2. Vivado
3. GTKwave

## Installation
1. Open a terminal and navigate to a convenient directory.
```shell
> git clone ssh://git@bitbucket.vih.infineon.com:7999/inicio/anasymod.git --recursive
```
2. Install all of the Python packages in the project:
```shell
> cd ip_core_gen
> pip install -e .
> cd ..
> cd msdsl
> pip install -e .
> cd ..
> cd svreal
> pip install -e .
> cd ..
```
3. Have a look at anasymod/test_project/build_system/includes.mk.  In particular, update the paths to Python, Vivado, and GTKwave as necessary.

## Running the Example
1. Make sure that your Pynq board is set up correctly:
    1. Jumper JP4 should be set for "JTAG"
    2. Jumper "JP5" should be set for "USB"
2. Plug the Pynq board into your computer using a micro USB cable.
3. Move the Pynq board power switch to "ON"
4. Go to the test_project directory and run **make**.  This will generate the analog model(s), then run synthesis, place and route, and ultimately generate a bitstream file.
```shell
> cd test_project
> make
```
5. Run **make emulation** to configure the FPGA with the generated bitstream, run the emulation, and save the resulting waveforms to a VCD file.
```shell
> make emulation
```
6. Run **make view** to view the results from the VCD file using GTKwave.
```shell
> make view
```