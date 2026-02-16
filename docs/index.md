<div style="text-align:center;color:#990033; font-family:times, serif;
font-size:3em"><i>Telemetrix User's Guide For The</i></div>
<div style="text-align:center;color:#990033; font-family:times, serif;
font-size:3em"><i>Raspberry Pi Pico 2W</i></div>
"
![](./images/tmx3.png)
<br>

# Introduction

## What is Telemetrix?

*Telemetry* is a system for collecting data from a remote device and automatically 
transmitting it to a local receiving device for processing.

Telemetrix is a telemetry system that allows you to remotely 
interact with the GPIO pins on your Raspberry Pi Pico 2W. 
If you set up a GPIO pin as a digital or analog input, Telemetrix will 
autonomously send reports for all detected data changes.  
It also allows you to interact with your favorite i2c device, 
control stepper and servo motors, control NeoPixel strips, monitor DHT 
temperature sensors, and monitor HC-SR04 SONAR distance sensors.

How does this all work? Telemetrix for the Raspberry Pi Pico 2W 
consists of two main software components. A resident Pico 2W server and a 
client that is written using a Python API, running on a 
Windows, Linux, or macOS computer. 
The client and server communicate over 
a BLE, WiFi, or a Serial/USB transport. The choice is up to you!

The server is implemented using the 
[Arduino Pico Core,](https://github.com/earlephilhower/arduino-pico?tab=readme-ov-file){: target="_blank" rel="noopener"}
providing full access to all Pico processor features. Choose the BLE, 
Serial/USB, or WiFi server you wish to use and install it on the Pico 2W 
using the Arduino IDE.

Clients are created using one of the Python APIs.
For each transport type, you may choose to use a threaded 
synchronous model or a Python asyncio model.


## Summary Of Major Features

* Applications are written in conventional Python 3.10 or later.
* All Data change events are reported asynchronously via user-registered callback functions. 
* Each data change event is time-stamped.
* Online API Reference Documentation is provided for all four API's.:

    * For the [Threaded WiFi Python Client.](https://htmlpreview.github.io/?https://github.com/MrYsLab/telemetrix-rpi-pico-2w/blob/master/html/telemetrix_rpi_pico_2w_wifi/index.html){: target="_blank" rel="noopener"}
    * For the [Asyncio WiFi Python Client.](https://htmlpreview.github.io/?https://github.com/MrYsLab/telemetrix-rpi-pico-2w/blob/master/html/telemetrix_rpi_pico_2w_wifi_aio/index.html){: target="_blank" rel="noopener"}
    * For the [Threaded BLE Python Client](https://htmlpreview.github.io/?https://github.com/MrYsLab/telemetrix-rpi-pico-2w/blob/master/html/telemetrix_rpi_pico_2w_ble/index.html){: target="_blank" rel="noopener"}
    * For the [Asyncio BLE Python Client](https://htmlpreview.github.io/?https://github.com/MrYsLab/telemetrix-rpi-pico-2w/blob/master/html/telemetrix_rpi_pico_2w_ble_aio/index.html){: target="_blank" rel="noopener"}
    * For the [Threaded Serial Python Client.](https://htmlpreview.github.io/?https://github.com/MrYsLab/telemetrix-rpi-pico-2w/blob/master/html/telemetrix_rpi_pico_2w_serial/index.html){: target="_blank" rel="noopener"}
    * For the [Asyncio Serial Python Client.](https://htmlpreview.github.io/?https://github.com/MrYsLab/telemetrix-rpi-pico-2w/blob/master/html/telemetrix_rpi_pico_2w_serial_aio/index.html){: target="_blank" rel="noopener"}
* A complete [set of working examples](https://github.
  com/MrYsLab/telemetrix-rpi-pico-2w/tree/master/examples){: target="_blank"rel="noopener"} is provided for each of the six client APIs.
* Integrated debugging methods are included in the Pico Server source code to aid in adding new features.

## Intuitive And Easy To Use APIs

For example, to receive asynchronous digital pin state data change notifications using 
traditional Python, you do the following:

### Typical API Steps For Input Pins

#### 1. Set a pin mode for the pin and register an associated callback function for the pin. 

The example below illustrates how this is done.

**Callbacks**

All callbacks are written to accept a single parameter. In the example below, this 
parameter is named _data_. 


```python
        def the_callback(data):
     
            # Your code here.
```
Upon receiving a data change report message from the Pico, 
the client creates a list containing the data describing the change 
event and calls the associated callback function, passing the list as a parameter.

For a digital data change, the list would contain the following:
    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**[report_type=digital input, pin_number, 
pin_value, time stamp]**

Each input report returns a unique list, as described in the API.

The first element in the list is the report type. Knowing the report type, you may 
optionally have a single callback function handle multiple event types using the 
report type to identify the callback source.

Report types are defined [here](https://github.com/MrYsLab/telemetrix-rpi-pico-2w/blob/a998a6eb3b3f265ad23d14bbc43319ad773c2ae3/telemetrix_rpi_pico_2w_common/private_constants.py#L90){: target="_blank" rel="noopener"}.

#### 2. Have your application sit in a loop, waiting for notifications.

### Typical API Steps For Output Pins

#### 1. Set a pin mode for the pin. 

#### 2. Set the pin's value.

 
## A Working Example   

Here is a Telemetrix example that monitors several digital input pins:

```python
import sys
import time

from telemetrix_rpi_pico_2w_serial import telemetrix_rpi_pico_2w_serial

"""
Monitor 4 digital input pins with pull-up enabled for each
"""


# Callback data indices
# When the callback function is called, the client fills in
# the data parameter. Data is a list of values, and the following are
# indexes into the list to retrieve report information

CB_REPORT_TYPE = 0 # The mode of the reporting pin (input, output, PWM, etc.)
CB_PIN = 1      # The GPIO pin number associated with this report
CB_VALUE = 2    # The data value reported
CB_TIME = 3     # A time stamp when the data change occurred


def the_callback(data):
    """
    A callback function to report data changes.
    This will print the pin number, its reported value and
    the date and time when the change occurred
    :param data: [pin mode, pin, current reported value, pin_mode, timestamp]
    """
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[CB_TIME]))
    print(f'Report Type: {data[CB_REPORT_TYPE]} Pin: {data[CB_PIN]} '
          f'Value: {data[CB_VALUE]} Time Stamp: {date}')


board = telemetrix_rpi_pico_2w_serial.TelemetrixRpiPico2wSerial()
board.set_pin_mode_digital_input_pullup(12, the_callback)
board.set_pin_mode_digital_input_pullup(13, the_callback)
board.set_pin_mode_digital_input_pullup(14, the_callback)
board.set_pin_mode_digital_input_pullup(15, the_callback)

try:
    while True:
        time.sleep(.0001)
except KeyboardInterrupt:
    board.shutdown()
    sys.exit(0)

```

And here is some sample output:

```python
TelemetrixRpiPicoW2:  Version 0.0.9

Copyright (c) 2020-2025 Alan Yorinks All Rights Reserved.

Opening all potential serial ports...
	/dev/ttyACM0
Serial compatible device found and connected to /dev/ttyACM0
Retrieving pico ID...
Pico Unique ID: [87, 237, 12, 180, 171, 71, 154, 172]

Retrieving Telemetrix4pico2W firmware ID...
Telemetrix4pico2W firmware version: 1.0
Report Type: 2 Pin: 12 Value: 1 Time Stamp: 2025-12-16 14:45:36
Report Type: 2 Pin: 13 Value: 1 Time Stamp: 2025-12-16 14:45:36
Report Type: 2 Pin: 14 Value: 1 Time Stamp: 2025-12-16 14:45:36
Report Type: 2 Pin: 15 Value: 1 Time Stamp: 2025-12-16 14:45:36
Report Type: 2 Pin: 12 Value: 0 Time Stamp: 2025-12-16 14:45:43
Report Type: 2 Pin: 12 Value: 1 Time Stamp: 2025-12-16 14:45:44
Report Type: 2 Pin: 12 Value: 0 Time Stamp: 2025-12-16 14:45:44
Report Type: 2 Pin: 12 Value: 1 Time Stamp: 2025-12-16 14:45:44
Report Type: 2 Pin: 14 Value: 0 Time Stamp: 2025-12-16 14:45:46
Report Type: 2 Pin: 14 Value: 1 Time Stamp: 2025-12-16 14:45:47
Report Type: 2 Pin: 13 Value: 0 Time Stamp: 2025-12-16 14:45:49
Report Type: 2 Pin: 13 Value: 1 Time Stamp: 2025-12-16 14:45:50


```

The following section explains how to install both the server and client APIs on your
system.