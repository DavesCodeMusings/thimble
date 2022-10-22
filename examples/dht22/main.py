# DHT22 sensor with an API
# (Assumes network connection is already configured.)
from machine import Pin
from dht import DHT22
from thimble import Thimble
import uasyncio

dht22 = DHT22(Pin(14))
temp_c = 0
temp_f = 32
humidity = 0

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
        await uasyncio.sleep(5)

api = Thimble()

@api.route('/temperature/celsius')
def get_temp_c(req):
    return round(temp_c)

@api.route('/temperature/fahrenheit')
def get_temp_f(req):
    return round(temp_f)

@api.route('/humidity')
def get_humidity(req):
    return round(humidity)

loop = uasyncio.get_event_loop()
api.run(loop=loop)
uasyncio.create_task(read_dht())
loop.run_forever()
