"""
Simple little application for getting/setting chiller and temperature over
http. 

Todo:
    - implement MAX31865 driver
    - implement temperature control loop
    - integrate with tilt device (see: tiltpi implementation)
    - async implementation using twisted/tornado
    - add web based ui
    - integrate with brewersfriend api
"""
from flask import Flask
from gpiozero import DigitalOutputDevice

from Drivers.SolidStateRelay import SolidStateRelay
from Drivers.MAX31865 import MAX31865

app = Flask(__name__)
ssr = SolidStateRelay(pin='GPIO18', active_high=True, initial_value=False)
# adc = MAX31865(bits=15, max_voltage=3.3, channel=0)

@app.route('/')
def hello():
    return "hello world"

@app.route('/chiller')
def read_chiller():
    return "on" if ssr.value == 1 else "off"

@app.route('/chiller/<operation>')
def set_chiller(operation):
    ssr.value = 1 if operation == "on" else 0
    return "ok - {}".format(ssr.value)

@app.route('/temperature/<sensor>')
def read_temperature(sensor):
    return "0.0"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

   
