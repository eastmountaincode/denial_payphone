import time
import board
import adafruit_vcnl4200

# ---- Constants ----
PROXIMITY_THRESHOLD = 223       # >= this is ON HOOK; < this is OFF HOOK
OFF_HOOK_REQUIRED_DURATION = 2.0  # seconds proximity must stay low to count as off-hook
ON_HOOK_REQUIRED_DURATION = 2.0   # seconds proximity must stay high to count as on-hook
POLL_INTERVAL = 0.1               # seconds between sensor polls

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

