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
    Wait until proximity > PROXIMITY_THRESHOLD for OFF_HOOK_REQUIRED_DURATION.
    """
    start_time = None
    while True:
        prox = sensor.proximity
        print(f"\rProximity: {prox}", end="", flush=True)

        if prox > PROXIMITY_THRESHOLD:
            if start_time is None:
                start_time = time.time()
            elif time.time() - start_time >= OFF_HOOK_REQUIRED_DURATION:
                return True
        else:
            start_time = None
        time.sleep(POLL_INTERVAL)

def wait_for_on_hook(sensor):
    """
    Wait until proximity <= PROXIMITY_THRESHOLD for ON_HOOK_REQUIRED_DURATION.
    """
    start_time = None
    while True:
        prox = sensor.proximity
        if prox <= PROXIMITY_THRESHOLD:
            if start_time is None:
                start_time = time.time()
            elif time.time() - start_time >= ON_HOOK_REQUIRED_DURATION:
                return True
        else:
            start_time = None
        time.sleep(POLL_INTERVAL)

def wait_for_on_hook_with_dialtone(sensor, dialtone_filename, audio_dir):
    """
    Wait until proximity <= PROXIMITY_THRESHOLD for ON_HOOK_REQUIRED_DURATION,
    while playing a dialtone loop.
    """
    import threading
    from audio import play_audio_loop
    
    # Shared state for on-hook detection
    on_hook_detected = threading.Event()
    start_time = None
    
    def check_on_hook():
        nonlocal start_time
        while not on_hook_detected.is_set():
            prox = sensor.proximity
            if prox <= PROXIMITY_THRESHOLD:
                if start_time is None:
                    start_time = time.time()
                elif time.time() - start_time >= ON_HOOK_REQUIRED_DURATION:
                    on_hook_detected.set()
                    return
            else:
                start_time = None
            time.sleep(POLL_INTERVAL)
    
    # Start proximity monitoring in background thread
    proximity_thread = threading.Thread(target=check_on_hook, daemon=True)
    proximity_thread.start()
    
    # Play dialtone until on-hook is detected
    play_audio_loop(dialtone_filename, audio_dir, lambda: on_hook_detected.is_set())
    
    # Wait for proximity thread to complete
    proximity_thread.join(timeout=1.0)
    
    return True

def is_on_hook(sensor):
    """
    Returns True if proximity sensor reads "on hook" (<= threshold).
    Pass in your sensor object.
    """
    return sensor.proximity <= PROXIMITY_THRESHOLD

