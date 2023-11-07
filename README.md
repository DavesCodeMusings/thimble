# Thimble
A tiny web framework for MicroPython.

## What is it?
Thimble is similar in spirit to Flask, but scaled way back to fit on a microcontroller. Basically, you can create a web application using functions and routes. It's more robust than the typical MicroPython web server example code. But, there's a lot of features it lacks when compared to a full-featured web application fromework. Still, for something that runs on an eight dollar microcontroller, it's pretty sweet.

## How can I use it?
Copy thimble.py to your MicroPython powered microcontroller. Use main.py to test. Customize with your own functions and routes.

Timble is a class with a route() method and a run() method. You add routes similar to the way you would with Flask and then call a run() method to start listening.

```py
from thimble import Thimble

app = Thimble() 

@app.route('/')
def hello(req):
    return 'Hello World'

app.run()
```

Now, point your web browser to the IP of your device on the default port of 80 and you should see 'Hello World'.

Beyond Hello World, here's a more useful example of exposing a GPIO pin via a REST API.

```py
from machine import Pin
from thimble import Thimble

gpio_2 = Pin(2, Pin.OUT)

app = Thimble()

@app.route('/gpio/2', methods=['GET'])
def get_gpio_2(req):
    return gpio_2.value()

@app.route('/gpio/2', methods=['PUT'])
def set_gpio_2(req):
    if (req['body'] == '1' or req['body'] == 'on'):
        gpio_2.on()
    elif (req['body'] == '0' or req['body'] == 'off'):
        gpio_2.off()
    return gpio_2.value()

app.run(debug=True)
```

Saving the code above as main.py will let you read the state of GPIO 2 using a GET method and the URL path of /gpio/2. The same path with a PUT method and `on` or `off` in the request body will change the state of GPIO 2.

Try it out with your favorite REST API client or use the following `curl` commands:

```
curl -X GET -i 'http://192.168.0.43/gpio/2'
curl -X PUT -i 'http://192.168.0.43/gpio/2' --data 0
curl -X PUT -i 'http://192.168.0.43/gpio/2' --data 1
```

You can even get fancier by importing the `json` package so your API can return data like this: `{"value": 125, "units": "millivolts"}` Just specify the content-type with your function's return value.

Like this: 

```py
@app.route('/adc/0')
def get_adc_0(req):
    return json.dumps({ "value": int(adc_0.read_uv() / 1000), "units": "millivolts" }), 200, 'application/json'
```

Wildcard routes are also possible, but limited to one matching parameter written as a regular expression.

For example, the regex in the route below will match any integer at the end of the URL and pass it as a function argument:

```py
@app.route('/grenade/antioch/holy/([0-9+])$', methods=['GET'])
def get_count(req, num):
    return f'and the number of the counting shall be {num}'
```

Any of the following URLs will match the route
* /grenade/antioch/holy/2
* /grenade/antioch/holy/3
* /grenade/antioch/holy/2048

The value for `num` passed to `get_count(req, num)` will be 2, 3, and 2048 respectively. `/grenade/antioch/holy/([0-9])$` could be used to limit the match to a single digit. But, since the [MicroPython re module](https://docs.micropython.org/en/latest/library/re.html) is a subset of CPython, `/grenade/antioch/holy/([0-9]{1,2})$` to match one or two digits is right out. Counted repetitions are not supported in MicroPython.

See [the wiki](https://github.com/DavesCodeMusings/thimble/wiki) for more examples in a step by step tutorial format.

## Can it serve static web pages?
As we say here in Wisconsin: "Oh yah, you betcha!" You can put your static files in `/static` on your flash filesystem and they will be served up just like any other web server, though a bit slower.

You can save space by compressing static files with GZIP and adding a `.gzip` extension. These files will be sent with a 'Content-Encoding: gzip' header that will tell the web browser to decompress upon receipt. For example, something like _script-library.js_ could be compressed and stored as _script-library.js.gzip_. Then, when a request is made for _script-library.js_, Thimble will send the contents of _script-library.js.gzip_ and add the Content-Encoding header.

## What pitfalls do I need to be aware of?
Using the example main.py assumes that networking is already configured by a boot.py that you supply. Thimble won't work without it. If you need help with wifi connections, see my example under [lolin32oled](https://github.com/DavesCodeMusings/esp/tree/main/lolin32oled)

Thimble is in the early phases of development and may have a few bugs lurking. If you find one, add a Github issue and I'll see if I can fix it.

## Will it run on Microcontroller X?
Code is being developed and tested using an ESP32-C3 devkit with MicroPython 1.21. Occasionally, I will run it on a Wemos LOLIN32 (ESP32) clone. It may or may not work with other devices.

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
