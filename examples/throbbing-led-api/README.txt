This is an example that uses Thimble to add an API to a pulsing LED.
The LED pulsing code is calculation intensive and not well optimized,
yet it still works well and the API is responsive.

Here's how it works:

Booting the microcontroller will result in a WiFi access point (AP)
being created. Debug output will show the SSID and password along
with the IP address and starting beats per minute (BPM.)

config.py is where you can change things like SSID, password, and
initial BPM. The IP address of the AP is 192.168.4.1 by default.

Once you cannect to the access point, the API can be accessed like
this:

http://192.168.4.1/bpm

GET is used to retreive the current BPM.
PUT is used to set a new BPM with the value in the request body.
DELETE will set BPM to zero, stopping the pulsing.

The body media type is always text/plain
