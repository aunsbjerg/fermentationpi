"""
wip

todo:
 - wrap app object in class if possible to avoid global nastynesss
 - find appropriate way to access temp control vars in thread safe manner
 - consider if twisted/tornado/trio/whatever is better alternative
 - consider lightweight db for data logging
 - consider adding temperateue graphs
"""
import logging
from threading import Thread
from flask import Flask, render_template, request


logger = logging.getLogger(__name__)
app = Flask(__name__)
_temp_control = None


def start_webview(temp_control, host='0.0.0.0', port=8080):
    """

    """
    global _temp_control

    logger.info(f"starting webview server at {host}:{port}")

    kwargs = {
        'debug': True,
        'use_reloader': False,
        'host': host,
        'port': port
    }

    _temp_control = temp_control
    _thread = Thread(target=app.run, kwargs=kwargs, daemon=True)
    _thread.start()


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    global _temp_control

    if request.method == 'POST':
        new_sp = float(request.form['beer_setpoint'])
        _temp_control.set_temperature_setpoint(new_sp)

    data = {
        'beer_setpoint': round(_temp_control._beer_setpoint, ndigits=2),
        'fridge_setpoint': round(_temp_control._fridge_setpoint, ndigits=2),
        'beer_temperature': round(_temp_control._beer_temperature, ndigits=2),
        'fridge_temperature': round(_temp_control._fridge_temperature, ndigits=2),
        'gravity': round(_temp_control._gravity, ndigits=1),
    }

    return render_template('index.html', data=data)


