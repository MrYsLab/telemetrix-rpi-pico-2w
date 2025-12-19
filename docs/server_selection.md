## Choose A Server

Select File from the Arduino IDE main menu and then select Examples.

Next, choose _Telemetrix4RpiPico2w_ from the example selections.

![](images/select_server.png)

There are two servers to choose from:

* _Telemetrix4RpiPico2w-Serial_

    This server implements a serial transport via the USB port.
  
* _Telemetrix4RpiPico2w-WiFi_

    This server implements a WiFi transport.

## Configure The Server

### Telemetrix4RpiPico2w-Serial

The serial server requires no configuration.

### Telemetrix4RpiPico2w-WiFi


![](images/config_wifi_server.png)

#### Required Configuration

##### SSID
Edit the sketch and place your router's SSID between the quotes.

##### PASSWORD

Edit the sketch and place your router's PASSWORD between the quotes.

Save your changes

## Upload The Server To The Pico

Configure the Arduino IDE for the 


Allow 15 seconds for connection to complete......................................................
Connected to WiFi. IP Address: 192.168.2.212  IP Port: 31335