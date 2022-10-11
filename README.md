# Thimble
A tiny web framework for MicroPython.

## What is it?
Thimble is similar in spirit to Flask, but scaled way back to fit on a microcontroller. Basically, you can create a web application using functions and routes. It's more robust than the typical MicroPython web server example code. But, there's a lot of features it lacks when compared to a full-featured web application fromework. Still, for something that runs on a $15 microcontroller, it's pretty sweet.

## How can I use it?
Copy thimble.py to your MicroPython powered microcontroller. Use main.py to test. Customize with your own functions and routes.

Timble is a class with a route() method and a run() method. You add routes similar to the way you would with Flask and then call a run() method to start listening.

```
from thimble import Thimble

app = Thimble() 

@app.route('/')
def hello():
    return 'Hello World'

app.run()
```

Now, point your web browser to the IP of your microcontroller on the default port of 80 and you should see 'Hello World'.

## What pitfalls do I need to be aware of?
Using the example main.py assumes that networking is already configured by a boot.py that you supply. Thimble won't work without it. If you need help with wifi connections, see my example under [lolin32oled](https://github.com/DavesCodeMusings/esp/tree/main/lolin32oled)

Thimble is in the beginning phases of development and really only supports HTTP GET. You can do POST and PUT or whatever, but currently they're all treated like a GET. There's also nothing to handle things like query parameters, URL encoding of special characters, etc.

## Will it run on Microcontroller X?
Code was developed and tested using an ESP32 with MicroPython 1.19.1. It may or may not work with other devices.
