
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

## Upload The Server To The Pico

Once you have selected the desired server and configured it and saved it, 
select the board and port on the Arduino IDE.




![](images/select_board_1.png)

Next, plug your Pico into a USB port and upload the server by pressing the upload
button on the Arduino IDE.

![](images/select_board_1.png)

## Getting The Assigned Router IP Address
If you selected the WiFi server, open the Arduino IDE's serial monitor by
clicking the serial monitor button.

![](images/serial_monitor.png)

Repower the Pico, and the router's assigned IP address will appear
in the serial monitor windows of the Arduino IDE.

![](images/ip_address.png)

