
# Server Configuration

## Telemetrix4RpiPico2w-BLE

### BLE Default Advertising String
Both BLE server's use the default advertising string of "**Tmx4Pico2W**". 
It is defined near the top of the sketch for both BLE servers.

To modify the advertising string, search the server sketch for:

```aiignore
#define PICO2W_ID "TmxPico2W"
```

Place the new string between the quotation marks.

![](images/ble_server.png)

!!! warning

    If you change the advertising string on the server, you must inform
    the BLE client of the new string.
    The client is made aware of the new string, by using the ble_device_name
    parameter when instantiating the client class.
    

### Setting The Advertising String In The Telemetrix4RpiPico2w-BLE Class

**TelemetrixRpiPico2Ble**
```aiignore
class TelemetrixRpiPico2Ble (ble_device_name='Tmx4Pico2W',
                             sleep_tune=1e-06,
                             autostart=True,
                             shutdown_on_exception=True,
                             reset_on_shutdown=True) 
```



### Setting The Advertising String In The TelemetrixRpiPico2wBleAio Class
```aiignore
class TelemetrixRpiPico2wBleAio (ble_device_name='Tmx4Pico2W',
                                 sleep_tune=1e-06,
                                 autostart=True,
                                 loop=None,
                                 shutdown_on_exception=True,
                                 reset_on_shutdown=True,
                                 close_loop_on_shutdown=True) 
```
<br>

### Enable The Bluetooth Stack Before Compiling The BLE Server 



Before compiling a BLE server, you must configure the Arduino IDE 
to include the
BLE stack. To do so, in the Arduion IDE, select **Tools/IP/Bluetooth Stack** 
and then **IPV4 + Bluetooth**.

<br>
![](images/ble_server_2.png)

<br>









## Telemetrix4RpiPico2w-Serial

The serial server requires no configuration.

## Telemetrix4RpiPico2w-WiFi


![](images/config_wifi_server.png)

#### Required Configuration

##### SSID
Edit the sketch and place your router's SSID between the quotes.

##### PASSWORD

Edit the sketch and place your router's PASSWORD between the quotes.

Save your changes.

## Upload The Server To The Pico

Select the board and port on the Arduino IDE.




![](images/select_board_1.png)

Next, plug your Pico into a USB port and upload the server by pressing the upload
button on the Arduino IDE.

![](images/select_board_2.png)

## Getting The Assigned Router IP Address
If you selected the WiFi server, open the Arduino IDE's serial monitor by
clicking the serial monitor button.

![](images/serial_monitor.png)

Repower the Pico, and the router's assigned IP address will 
appear in the Arduino IDE's serial monitor window.


![](images/ip_address.png)

