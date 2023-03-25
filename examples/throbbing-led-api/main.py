# A pulse-width modulated LED that fades in and out in sync with music with API controlled beats per minute.
from math import pi, cos
from config import BPM  # Beats per minute
from thimble import Thimble
import uasyncio

def pulse_led():
    a = 0  # Angle in radians.
    while (1):
        x = cos(a) * 511 + 512  # Cosine ranges from -1 to 1. PWM amplitude requires 0 to 1023.
        led.duty(int(x))  # LED brightness is controlled by duty cycle.
        a += increment    # Syncs the LED transition to every two beats.
        if (a > 2 * pi):  # 2pi radians is one full cycle of the cosine wave.
            a = 0
        await uasyncio.sleep_ms(1)  # The loop delay is 1 millisecond, which is why beats per ms is important.

def calculate_increment(BPM):
    if BPM <= 0:
        increment = 0
    else:
        bps = BPM / 60  # Dividing BPM by 60 seconds/minute gives beats per second.
        bpms = bps / 1000  # Dividing again by 1000 gives beats per millisecond.
        period = 1 / bpms  # Period is the time between beats (expressed in milliseconds.) 
        increment = pi / period  # Adding this to angle will get to 180 degrees (pi) in one beat.
    return increment

print(f'BPM: {BPM}')
increment = calculate_increment(BPM)

api = Thimble()
@api.route('/bpm', methods=['GET'])
def get_bpm(req):
    print(f'BPM: {BPM}')
    return BPM

@api.route('/bpm', methods=['PUT'])
def get_bpm(req):
    global BPM, increment
    BPM = int(req['body'])
    print(f'BPM: {BPM}')
    increment = calculate_increment(BPM)
    return BPM

@api.route('/bpm', methods=['DELETE'])
def del_bpm(req):
    global BPM, increment
    BPM = 0
    print(f'BPM: {BPM}')
    increment = calculate_increment(BPM)
    return BPM

loop = uasyncio.get_event_loop()
api.run(loop=loop)
uasyncio.create_task(pulse_led())
loop.run_forever()
