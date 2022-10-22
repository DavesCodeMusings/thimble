# Example program using Thimble to create an API.
from machine import Pin
from dht import DHT22
from thimble import Thimble
import uasyncio

gpio_2 = Pin(2, Pin.OUT)  # Built-in LED is used as a nightlight.
gpio_2.value(1)  # Turn off the active-low device for now.

dht22 = DHT22(Pin(14))
temp_c = 0
temp_f = 32
humidity = 0

# Read values from DHT sensor periodically.
async def read_dht():
    global temp_c
    global temp_f
    global humidity

    while (True):
        dht22.measure()
        temp_c = dht22.temperature()
        temp_f = 1.8 * temp_c + 32
        humidity = dht22.humidity()
        print(f'Temp: {temp_c}C, {temp_f}F  Humidity: {humidity}%')
        await uasyncio.sleep(15)


# Instantiate the Thimble API object.
api = Thimble()

# Add routes for reading the DHT-provided values using the default HTTP method of GET.
@api.route('/temperature/celsius')
def get_temp_c(req):
    return round(temp_c)

@api.route('/temperature/fahrenheit')
def get_temp_f(req):
    return round(temp_f)

@api.route('/humidity')
def get_humidity(req):
    return round(humidity)

# Various HTTP methods allow control of the built-in LED.
@api.route('/nightlight', methods=['GET'])
def get_nightlight(req):
    return 'on' if gpio_2.value() == 0 else 'off'

@api.route('/nightlight', methods=['PUT'])
def set_nightlight(req):
    if (req['body'] == 'on'):
        gpio_2.value(0)  # Built-in LED is active-low, so 0 is on
    elif (req['body'] == 'off'):
        gpio_2.value(1)
    return 'on' if gpio_2.value() == 0 else 'off'

@api.route('/nightlight', methods=['POST'])
def set_nightlight_on(req):
    gpio_2.value(0)
    return 'on' if gpio_2.value() == 0 else 'off'

@api.route('/nightlight', methods=['DELETE'])
def set_nightlight_off(req):
    gpio_2.value(1)
    return 'on' if gpio_2.value() == 0 else 'off'


# Run the DHT reader and Thimble as asynchronous tasks.
loop = uasyncio.get_event_loop()
api.run(loop=loop)
uasyncio.create_task(read_dht())
loop.run_forever()

