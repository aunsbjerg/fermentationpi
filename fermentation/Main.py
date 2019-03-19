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
supply = SolidStateRelay(pin='GPIO4', active_high=True, initial_value=False)
pt100 = MAX31865(channel=0)

@app.route('/')
def hello():
    return "hello world"

@app.route('/<relay>')
def read_relay(relay):
    if relay == 'chiller':
        return "on" if ssr.value == 1 else "off"

    elif relay == 'supply':
        return "on" if supply.value == 1 else "off"

    return "invalid"

@app.route('/<relay>/<operation>')
def set_relay(relay, operation):
    if relay == 'chiller':
        ssr.value = 1 if operation == "on" else 0
        return "ok - {}".format(ssr.value)

    elif relay == 'supply':
        supply.value = 1 if operation == "on" else 0
        return "ok - {}".format(supply.value)

    return "invalid"

@app.route('/temperature/<sensor>')
def read_temperature(sensor):
    return pt100.temperature

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

   
