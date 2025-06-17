import time
import board
import adafruit_vcnl4200
from config.constants import PROXIMITY_THRESHOLD, OFF_HOOK_REQUIRED_DURATION, ON_HOOK_REQUIRED_DURATION, POLL_INTERVAL

def init_proximity_sensor():
    """
    Initializes and returns the VCNL4200 sensor object.
    """
    i2c = board.I2C()
    sensor = adafruit_vcnl4200.Adafruit_VCNL4200(i2c)
    return sensor

def wait_for_off_hook(sensor):
    """
    Wait until proximity < PROXIMITY_THRESHOLD for OFF_HOOK_REQUIRED_DURATION.
    """
    start_time = None
    while True:
        prox = sensor.proximity
        print(f"\rProximity: {prox}", end="", flush=True)

        if prox < PROXIMITY_THRESHOLD:
            if start_time is None:
                start_time = time.time()
            elif time.time() - start_time >= OFF_HOOK_REQUIRED_DURATION:
                return True
        else:
            start_time = None
        time.sleep(POLL_INTERVAL)

def wait_for_on_hook(sensor):
    """
    Wait until proximity >= PROXIMITY_THRESHOLD for ON_HOOK_REQUIRED_DURATION.
    """
    start_time = None
    while True:
        prox = sensor.proximity
        if prox >= PROXIMITY_THRESHOLD:
            if start_time is None:
                start_time = time.time()
            elif time.time() - start_time >= ON_HOOK_REQUIRED_DURATION:
                return True
        else:
            start_time = None
        time.sleep(POLL_INTERVAL)

def is_on_hook(sensor):
    """
    Returns True if proximity sensor reads "on hook" (>= threshold).
    Pass in your sensor object.
    """
    return sensor.proximity >= PROXIMITY_THRESHOLD

