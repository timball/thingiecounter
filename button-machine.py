# button-machine.py
# Program that runs on an RPi that interacts w/ ThingieCounter.
# This takes a little bit of time to startup. Wait for the pulsing LED.
#
# depends: gpiozero
#
# --timball@gmail.com
# Tue Mar 27 20:56:18 EDT 2018

import local_settings as conf
from gpiozero import LED, PWMLED, Button
from signal import pause


def put_curry(endpt):
    """ put_curry -- curry function to make the .when_released even easier
    than a decorator that takes a mostly empty function

    endpt -- end point we want to inc in ThingieCounter
    """
    def curry():
        import urllib2
        import json

        url = conf.URL + endpt
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url)
        request.add_header('Content-Type', 'application/json')
        request.get_method = lambda: 'PUT'
        try:
            url = opener.open(request)
        except urllib.error.URLError as e:
            print("PUT %s URLError, reason: %s" % (url, e.reason))
        except urllib.error.HTTPError as e:
            print("HTTPError PUT %s == %s" % (url, e.code))
    return curry


if __name__ == "__main__":
    led = PWMLED(conf.LED_PIN)
    led.blink()

    # each item in conf.BTNS[] is an individual button setting
    for this in conf.BTNS:
        this.button = Button(this['PIN'])
        this.button.when_released = put_curry(this['LABEL'])

    print("ready!")
    led.pulse()

    pause()
