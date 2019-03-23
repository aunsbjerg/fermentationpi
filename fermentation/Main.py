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
import time
import click
import ptvsd
from gpiozero import DigitalOutputDevice
from Drivers.SolidStateRelay import SolidStateRelay
from Drivers.MAX31865 import MAX31865

def debug_server(debug_port):
    print('Waiting for remote debugging ...')
    ptvsd.enable_attach(address=('192.168.0.19', debug_port), redirect_output=True)
    ptvsd.wait_for_attach()

@click.command()
@click.option('--debug', is_flag=True, help='enable remote debugging')
@click.option('--debug-port', default=3000, show_default=True, help='remote debugging port')
def main(debug, debug_port):

    if debug:
        debug_server(debug_port)

    print("hello")
    pt100 = MAX31865(wires=2, port=0, device=0)

    while True:
        time.sleep(1.0)
        print("rtd         {}".format(pt100._read_rtd()))
        print("resistance  {}".format(pt100._read_resistance()))
        print("temperature {}".format(pt100.temperature))


if __name__ == '__main__':
    main()
