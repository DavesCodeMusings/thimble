# Thimble
A tiny web framework for MicroPython.

[![Build thimble](https://github.com/DavesCodeMusings/thimble/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/DavesCodeMusings/thimble/actions/workflows/build.yml)

## What is it?
Thimble is similar in spirit to Flask, but scaled way back to fit on a microcontroller. Basically, you can create a web application using functions and routes. It's more robust than the typical MicroPython web server example code. But, there's a lot of features it lacks when compared to a full-featured web application framework. Still, for something that runs on a five dollar microcontroller, it's pretty sweet.

## How can I use it?
Thimble is a class with a route() method and a run() method. You add routes similar to the way you would with Flask and then call a run() method to start listening.

Copy thimble.py to your MicroPython powered microcontroller (or install with MIP). Use main.py to test. Customize with your own functions and routes.

Contents of main.py:

```py
from thimble import Thimble

app = Thimble() 

@app.route("/")
def hello(req):
    return "Hello World"

@app.route("/gpio/<digit>")
def gpio(req, num):
    return f"Hello GPIO {num}"

app.run(debug=True)
```

Now, point your web browser to the IP of your device on the default port of 80 and you should see 'Hello World'. Using the URL path of _/gpio/2_ should return 'Hello GPIO 2'.

There are more complex examples in the [examples](https://github.com/DavesCodeMusings/thimble/examples) subdirectory.

See [the wiki](https://github.com/DavesCodeMusings/thimble/wiki) for examples in a step by step tutorial format.

## Can it serve static web pages?
As we say here in Wisconsin: "Oh yah, you betcha!" You can put your static files in `/static` on your flash filesystem and they will be served up just like any other web server, though a bit slower.

You can save space by compressing static files with GZIP and adding a `.gzip` extension. These files will be sent with a 'Content-Encoding: gzip' header that will tell the web browser to decompress upon receipt. For example, something like _script-library.js_ could be compressed and stored as _script-library.js.gzip_. Then, when a request is made for _script-library.js_, Thimble will send the contents of _script-library.js.gzip_ and add the Content-Encoding header.

## What pitfalls do I need to be aware of?
Using the example main.py assumes that networking is already configured by a boot.py that you supply. Thimble won't work without it. If you need help with wifi connections, see my example under [lolin32oled](https://github.com/DavesCodeMusings/esp/tree/main/lolin32oled)

Thimble has been around for a while, but may have a few bugs lurking. If you find one, add a Github issue and I'll see if I can fix it.

## Will it run on Microcontroller X?
Code is being developed and tested using an ESP32 Devkit V1 clone with MicroPython 1.24. Occasionally, I will run it on an ESP32-C3 or ESP8266. It may or may not work with other devices.

## How do I install it?
Using mpremote on Windows, do this:
```
py -m mpremote connect PORT mip install github:DavesCodeMusings/thimble
```

_where PORT is something like COM4 (or whatever shows up in Device Manager for your microcontroller.)_

For Linux mpremote, do this:
```
mpremote connect PORT mip install github:DavesCodeMusings/thimble
```

_where PORT is something like /dev/ttyUSB0 (or whatever shows up in your `dmesg` output when you plug the device in.)_

Or just download directly from https://raw.githubusercontent.com/DavesCodeMusings/thimble/main/thimble.py and place it in your device's /lib directory.

## Show me the docs!
* [Documentation of the Thimble Class](https://davescodemusings.github.io/thimble/)
* [Coding Examples](https://github.com/DavesCodeMusings/thimble/tree/main/examples)
