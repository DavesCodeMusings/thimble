# Example of controlling built-in LED with an API
# (Assumes networking is already configured.)
from machine import Pin
from thimble import Thimble

gpio_2 = Pin(2, Pin.OUT)

app = Thimble()

@app.route('/gpio/2', methods=['GET'])
def get_gpio_2(req):
    return gpio_2.value()

@app.route('/gpio/2', methods=['PUT'])
def set_gpio_2(req):
    if (req['body'] == '1' or erq['body'] == 'on'):
        gpio_2.on()
    elif (req['body'] == '0' or req['body'] == 'off'):
        gpio_2.off()
    return gpio_2.value()

app.run(debug=True)  # Listens on 0.0.0.0:80 by default.
