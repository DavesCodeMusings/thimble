# Thimble

## What is it?
Thimble is tiny web framework for MicroPython. It is similar in spirit to Flask, but scaled way back to fit on a microcontroller.

Basically, you can create a web application using functions and routes.

## How can I use it?
Copy thimble.py to your MicroPython powered microcontroller. Use main.py to test. Customize with your own functions and routes.

## What pitfalls do I need to be aware of?
Using the example main.py assumes that networking is already configured by a boot.py that you supply. Thimble won't work without it. If you need help with wifi connections, see my example under [lolin32oled](https://github.com/DavesCodeMusings/esp/tree/main/lolin32oled)

Code was developed and tested using an ESP32 with MicroPython 1.19.1. It may or may not work with other devices.
