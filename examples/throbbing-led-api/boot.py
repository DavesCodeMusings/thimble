from machine import Pin, PWM
from network import WLAN, AP_IF, AUTH_WPA2_PSK
from config import AP_NAME, AP_PASS, GPIO

led = PWM(Pin(GPIO), freq=1000)
led.duty(512)  # Half bright

print('\nStarting in wifi access point mode...')
wlan = WLAN(AP_IF)
wlan.active(True)
wlan.config(authmode=AUTH_WPA2_PSK, essid=AP_NAME, password=AP_PASS)
print(f'SSID: {AP_NAME}')
print(f'Password: {AP_PASS}')
print(f'IP: {wlan.ifconfig()[0]}')  # This is the device's IP address
