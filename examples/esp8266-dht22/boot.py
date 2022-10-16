from config import AP_NAME, AP_PASS, CONNECT_TIMEOUT, WEBREPL_PASS
from network import WLAN, AP_IF, STA_IF
from time import ticks_ms, ticks_diff
from webrepl import start

# On 8266, shutdown access point, which is active by default.
ap_if = WLAN(AP_IF)
ap_if.active(False)

wlan = WLAN(STA_IF)
wlan.active(True)
print(f'\nConnecting to {AP_NAME}...')
if not wlan.isconnected():
    start_time = ticks_ms()
    wlan.connect(AP_NAME, AP_PASS)
    while not wlan.isconnected():
        if ticks_diff(ticks_ms(), start_time) > CONNECT_TIMEOUT * 1000:
            print('Connection timeout.')
            break

if wlan.isconnected():
    print(wlan.ifconfig()[0])
    if (WEBREPL_PASS):
        start(password=WEBREPL_PASS)
