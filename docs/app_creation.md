## A Quick Start To Developing Applications

### Examples
Examples are provided for each of the APIs and are a good source for
gaining an understanding how applications are implemented using Telemetrix.

* [Serial Threaded](https://github.com/MrYsLab/telemetrix-rpi-pico-2w/tree/master/examples/Serial/threaded)

* [WiFi Threaded](https://github.com/MrYsLab/telemetrix-rpi-pico-2w/tree/master/examples/WIFI/threaded)

* [Serial Asyncio](https://github.com/MrYsLab/telemetrix-rpi-pico-2w/tree/master/examples/Serial/asyncio)

* [WiFi Asyncio](https://github.com/MrYsLab/telemetrix-rpi-pico-2w/tree/master/examples/WIFI/asyncio)

## Downloading And Running The Examples

Go to the [telemetrix-rpi-pico-2w](https://github.com/MrYsLab/telemetrix-rpi-pico-2w) GitHub repository. Click on 
the green button in the upper right corner and download the zip file.

![](./images/examples.png)

Next, expand the zip file and go to the examples directory. Select any of the examples that you wish to run. 

## Application Templates
Below are a set of application templates to help get you started.
The templates show how to instantiate each API. For asyncio, the templates

### Serial Threaded

Import the API and instantiate its class.

```angular2html
import sys
import time

# IMPORT THE API
from telemetrix_rpi_pico_2w_serial import telemetrix_rpi_pico_2w_serial
"""

# INSTANTIATE THE API CLASS
board = telemetrix_rpi_pico_2w_serial.TelemetrixRpiPico2wSerial()

try:
    # WRITE YOUR APPLICATION HERE
except:
    board.shutdown()

```

### WiFi Threaded
Here, we need to instantiate the class passing in the IP address assigned by your 
router. This parameter enables the WIFI transport.

```angular2html
import sys
import time

# IMPORT THE API
from telemetrix_rpi_pico_2w_wifi import telemetrix_rpi_pico_2w_wifi

# INSTANTIATE THE API CLASS
# Make sure to edit the transport address assigned by your router.

board = telemetrix_rpi_pico_2w_wifi.TelemetrixRpiPico2WiFi(ip_address='192.168.2.212')

try:
    # WRITE YOUR APPLICATION HERE
except:
    board.shutdown()

```


### Serial Asyncio

For asyncio, im addition to importing the API, we implement the application
in an asyncio function.

After obtaining an asyncio loop, we instantiate the API, passing in the loop we
obtained.

We run the application by calling loop.run_until_complete(my_app(board)), and 
end by gracefully shutting the application.

```angular2html

import sys
import asyncio

# IMPORT THE API
from telemetrix_rpi_pico_2w_serial_aio import telemetrix_rpi_pico_2w_serial_aio

# An async method for running your application.
# We pass in the instance of the API created below .
async def my_app(the_board):
    # Your Application code

# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    board = telemetrix_rpi_pico_2w_serial_aio.TelemetrixRpiPico2WSerialAIO(loop=loop)
except KeyboardInterrupt:
    sys.exit()

try:
    # start the main function
    loop.run_until_complete(my_app(board))
except KeyboardInterrupt:
    try:
        loop.run_until_complete(board.shutdown())
    except:
        pass
    sys.exit(0)

```



### WiFi Asyncio

For asyncio, im addition to importing the API, we implement the application
in an asyncio function.

After obtaining an asyncio loop, we instantiate the API, passing in the loop we
obtained, and the IP address assigned by our router.

We run the application by calling loop.run_until_complete(my_app(board)), and 
end by gracefully shutting the application.

```angular2html

import sys
import asyncio

# IMPORT THE API
from telemetrix_rpi_pico_2w_wifi_aio import telemetrix_rpi_pico_2w_wifi_aio

# An async method for running your application.
# We pass in the instance of the API created below .
async def my_app(the_board):
    # Your Application code

# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix_aio
# Make sure to edit the transport address assigned by your router.
board = telemetrix_rpi_pico_2w_wifi_aio.TelemetrixRpiPico2WiFiAio(
    ip_address='192.168.2.212', loop=loop)

try:
    # start the main function
    loop.run_until_complete(my_app(board))
except KeyboardInterrupt:
    try:
        loop.run_until_complete(board.shutdown())
    except:
        pass
    sys.exit(0)

```


