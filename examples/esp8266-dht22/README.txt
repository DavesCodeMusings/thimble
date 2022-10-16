In here is a full example of using Thimble as an API.

Hardware you will need:
* An ESP8266 (D1 mini or nodemcu)
* A DHT22 sensor

Required Software:
* Thonny editor (https://thonny.org/)
* MicroPython flashed onto ESP8266 (https://micropython.org/)
* A copy of thimble.py from this repository
* A REST API client (or use the curl command)

How to set it up:
* Flash the ESP8266 with MicroPython using Thonny
* Upload a copy of thimble.py to the 8266's flash filesystem
* Upload the files in this example
* Edit config.py with the SSID and pasword for your wifi

How to use it:
* Find the IP address of the 8266 from the serial debug output
* Point your API client to the IP of the device and one of the route paths

Here are some examples of curl commands to interact with the API:

curl -X GET -i 'http://192.168.4.2/temperature/celsius'
curl -X GET -i 'http://192.168.4.2/temperature/fahrenheit'
curl -X GET -i 'http://192.168.4.2/nightlight/humidity'

curl -X GET -i 'http://192.168.4.2/nightlight'
curl -X PUT -i 'http://192.168.4.2/nightlight' --data on
curl -X PUT -i 'http://192.168.4.2/nightlight' --data off
curl -X POST -i 'http://192.168.4.2/nightlight'
curl -X DELETE -i 'http://192.168.4.2/nightlight'

