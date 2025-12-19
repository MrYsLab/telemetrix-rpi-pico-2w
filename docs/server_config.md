
## Server Configuration

### Telemetrix4RpiPico2w-Serial

The serial server requires no configuration.

### Telemetrix4RpiPico2w-WiFi


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

