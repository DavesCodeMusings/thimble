# Thimble
A tiny web framework for MicroPython.

## What is it?
Thimble is similar in spirit to Flask, but scaled way back to fit on a microcontroller. Basically, you can create a web application using functions and routes. It's more robust than the typical MicroPython web server example code. But, there's a lot of features it lacks when compared to a full-featured web application fromework. Still, for something that runs on a $15 microcontroller, it's pretty sweet.

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
    if (body == 1 or body == 'on'):
        gpio_2.on()
    elif (body == 0 or body == 'off'):
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
def get_gpio(req, num):
    return f'and the number of the counting shall be {num}'
```

See [the wiki](https://github.com/DavesCodeMusings/thimble/wiki) for more examples in a step by step tutorial format.

## Can it serve static web pages?
As we say here in Wisconsin: "Oh ya, you betcha!" You can put your static files in `/static` on your flash filesystem and they will be served up just like any other web server, though a bit slower.

## What pitfalls do I need to be aware of?
Using the example main.py assumes that networking is already configured by a boot.py that you supply. Thimble won't work without it. If you need help with wifi connections, see my example under [lolin32oled](https://github.com/DavesCodeMusings/esp/tree/main/lolin32oled)

Thimble is in the early phases of development and may crash from time to time. If it does, add a Github issue and I'll see if I can fix it.

## Will it run on Microcontroller X?
Code is being developed and tested using a Wemos D1 Mini (ESP8266, 4M Flash) clone with MicroPython 1.19.1. Occasionally, I will run it on a Wemos LOLIN32 (ESP32) clone. It may or may not work with other devices.

## Show me the docs!
* [Documentation of the Thimble Class](https://davescodemusings.github.io/thimble/)
* [Coding Examples](https://github.com/DavesCodeMusings/thimble/tree/main/examples)
