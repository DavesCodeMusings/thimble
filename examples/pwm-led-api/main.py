# Control LED brightness via API.
# (Assumes network connection is already configured.)

from machine import Pin, PWM
from thimble import Thimble

pwm_2 = PWM(Pin(2))
pwm_2.duty(512) # Start with half brightness.

api = Thimble()


# Convert between percent value and PWM duty cycle for active-low LED.
# (e.g. 0% is 1023 duty cycle and 100% is 0)
def pwm_from_percent(percent):
    return round((100 - percent) * 1023 / 100)

def percent_from_pwm(duty_cycle):
    return round((1023 - duty_cycle) * 100 / 1023)
    

# Various HTTP methods allow control of the built-in LED.
@api.route('/nightlight', methods=['GET'])
def get_nightlight(req):
    return percent_from_pwm(pwm_2.duty())

@api.route('/nightlight', methods=['PUT'])
def set_nightlight(req):
    brightness = int(req['body'])
    if (brightness < 0 or brightness > 100):
        return "Value out of range", 400
    else:
        pwm_2.duty(pwm_from_percent(brightness))
        return percent_from_pwm(pwm_2.duty())

@api.route('/nightlight', methods=['DELETE'])
def set_nightlight_off(req):
    pwm_2.duty(pwm_from_percent(0))
    return percent_from_pwm(pwm_2.duty())


api.run(debug=True)

